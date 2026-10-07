from __future__ import annotations

import json
import re
import sqlite3
from dataclasses import asdict, fields
from datetime import date
from decimal import Decimal, DecimalException
from pathlib import Path
from uuid import uuid4
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field, StrictInt

from bnpl_cashflow.input.validation import (
    BNPLPlanInput, CreditCardInput, InputValidationError, ValidationIssue,
    validate_profile_payload,
)
from bnpl_cashflow.application.profiles import create_profile
from bnpl_cashflow.application.plan_appearance import plan_appearance


class ProfileIdentity(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    id: str = Field(min_length=1, max_length=128)
    name: str = Field(min_length=1, max_length=120)


class PlanCreate(BaseModel):
    """Transport schema; financial constraints remain in the shared validator."""
    model_config = ConfigDict(extra="forbid", strict=True)
    plan_name: str
    provider_name: Literal["paypal", "klarna", "afterpay", "sezzle", "affirm"]
    credit_card_id: str
    purchase_amount: str
    currency: str
    purchase_date: str
    first_installment_date: str
    installment_count: StrictInt | str
    paid_installment_count: StrictInt | str = 0
    installment_frequency: Literal["BIWEEKLY"]
    amount_paid: str = "0.00"
    icon: str | None = None
    icon_color: str | None = None


class ProfileDocument(BaseModel):
    model_config = ConfigDict(extra="forbid", strict=True)
    format: str
    version: StrictInt
    profile: ProfileIdentity
    credit_cards: list[dict]
    bnpl_plans: list[dict]


class ProfileConflict(ValueError):
    pass


class ProfileNotFound(Exception):
    pass


class CardNotFound(Exception):
    pass


class PlanNotFound(Exception):
    pass


def validate_document(raw: object) -> dict:
    document = ProfileDocument.model_validate(raw)
    if document.format != "bnpl-profile" or document.version != 1:
        raise ValueError("Expected a bnpl-profile document with version 1. Legacy workspace drafts are not supported.")
    # Reuse the existing profile-name rules, including whitespace normalization.
    identity, _ = create_profile([], 1, document.profile.name)
    identity["id"] = document.profile.id
    if not identity["id"].strip() or identity["id"] != identity["id"].strip():
        raise ValueError("Profile ID must be non-empty and have no surrounding whitespace.")
    issues = []
    for collection, model in (("credit_cards", CreditCardInput), ("bnpl_plans", BNPLPlanInput)):
        allowed = {field.name for field in fields(model)}
        if collection == "bnpl_plans":
            allowed |= {"icon", "icon_color"}
        for index, entry in enumerate(getattr(document, collection)):
            if set(entry) - allowed:
                issues.append(ValidationIssue(f"{collection}[{index}]", "contains unsupported fields"))
            if collection == "credit_cards" and entry.get("profile_id") != identity["id"]:
                issues.append(ValidationIssue(f"{collection}[{index}].profile_id", "must match the imported profile ID"))
    if issues:
        raise InputValidationError(issues)
    validated = validate_profile_payload({
        "credit_cards": document.credit_cards, "bnpl_plans": document.bnpl_plans,
    }, allow_mixed_currencies=True)
    cards = []
    for card in validated.credit_cards:
        cards.append(_card_value(card))
    return json.loads(json.dumps({
        "format": "bnpl-profile", "version": 1, "profile": identity,
        "credit_cards": cards, "bnpl_plans": [{**asdict(plan), **plan_appearance(raw, f"bnpl_plans[{index}]")}
            for index, (plan, raw) in enumerate(zip(validated.bnpl_plans, document.bnpl_plans))],
    }, default=_json_value, allow_nan=False))


def _json_value(value: object) -> str:
    if isinstance(value, Decimal):
        return str(value)
    if isinstance(value, date):
        return value.isoformat()
    raise TypeError("Unsupported stored value")


def _card_value(card: CreditCardInput) -> dict:
    value = asdict(card)
    if value["current_balance_due_date"] is None:
        del value["current_balance_due_date"]
    for field in ("upcoming_statement_close_date", "upcoming_statement_due_date"):
        if value[field] is None:
            del value[field]
    return json.loads(json.dumps(value, default=_json_value, allow_nan=False))


def summary(document: dict) -> dict:
    return {**document["profile"], "card_count": len(document["credit_cards"]),
            "plan_count": len(document["bnpl_plans"])}


class ProfileStore:
    """Transactional, local-only persistence isolated from Streamlit drafts."""

    def __init__(self, path: Path):
        self.path = path

    def export(self, profile_id: str) -> dict:
        connection = self._connect()
        try:
            return self._document(connection, profile_id)
        finally:
            connection.close()

    def plans(self, profile_id: str) -> list[dict]:
        return self.export(profile_id)["bnpl_plans"]

    def add_plan(self, profile_id: str, raw: object) -> dict:
        return self._save_plan(profile_id, raw)

    def update_plan(self, profile_id: str, plan_id: str, raw: object) -> dict:
        return self._save_plan(profile_id, raw, plan_id)

    def delete_plan(self, profile_id: str, plan_id: str) -> None:
        connection = self._connect()
        try:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                document = self._document(connection, profile_id)
                plans = document["bnpl_plans"]
                if not any(plan["id"] == plan_id for plan in plans):
                    raise PlanNotFound()
                document["bnpl_plans"] = [plan for plan in plans if plan["id"] != plan_id]
                connection.execute("UPDATE profiles SET document = ? WHERE id = ?", (json.dumps(document), profile_id))
        finally:
            connection.close()

    def _save_plan(self, profile_id: str, raw: object, plan_id: str | None = None) -> dict:
        from bnpl_cashflow.application.services import run_application

        allowed = ({field.name for field in fields(BNPLPlanInput)} - {"id"}) | {"icon", "icon_color"}
        if not isinstance(raw, dict) or set(raw) - allowed:
            raise ValueError("Provide only payment plan fields.")
        plan = {"paid_installment_count": 0, "amount_paid": "0.00", **raw, "id": str(uuid4())}
        for field in ("installment_count", "paid_installment_count"):
            value = plan.get(field)
            if isinstance(value, str) and re.fullmatch(r"[+-]?[0-9]{1,10}", value.strip()):
                plan[field] = int(value)
        connection = self._connect()
        try:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                document = self._document(connection, profile_id)
                existing = next((item for item in document["bnpl_plans"] if item["id"] == plan_id), None)
                if plan_id is not None:
                    if existing is None:
                        raise PlanNotFound()
                    plan = {**existing, **raw, "id": plan_id}
                    for field in ("installment_count", "paid_installment_count"):
                        value = plan.get(field)
                        if isinstance(value, str) and re.fullmatch(r"[+-]?[0-9]{1,10}", value.strip()):
                            plan[field] = int(value)
                # Validate the candidate at index zero for stable field-error paths.
                appearance = plan_appearance(plan, "bnpl_plans[0]")
                payload = validate_profile_payload({"credit_cards": document["credit_cards"],
                    "bnpl_plans": [plan, *(item for item in document["bnpl_plans"] if item["id"] != plan_id)]}, allow_mixed_currencies=True)
                try:
                    run_application(validate_profile_payload({"credit_cards": document["credit_cards"], "bnpl_plans": [plan]}))
                except (ValueError, OverflowError, DecimalException) as exc:
                    raise InputValidationError([ValidationIssue("bnpl_plans", "The schedule could not be generated. Check the dates, amount, and installment count.")]) from exc
                saved = json.loads(json.dumps(asdict(payload.bnpl_plans[0]), default=_json_value))
                saved.update(appearance)
                if plan_id is None:
                    document["bnpl_plans"].append(saved)
                else:
                    document["bnpl_plans"] = [saved if item["id"] == plan_id else item for item in document["bnpl_plans"]]
                # Only inputs are stored: no stale projection survives a mutation.
                connection.execute("UPDATE profiles SET document = ? WHERE id = ?", (json.dumps(document), profile_id))
                return saved
        finally:
            connection.close()

    def _connect(self) -> sqlite3.Connection:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        connection = sqlite3.connect(self.path)
        connection.execute("CREATE TABLE IF NOT EXISTS profiles (id TEXT PRIMARY KEY, name_key TEXT UNIQUE NOT NULL, document TEXT NOT NULL)")
        return connection

    def list(self) -> list[dict]:
        connection = self._connect()
        try:
            return [summary(json.loads(row[0])) for row in connection.execute("SELECT document FROM profiles ORDER BY name_key")]
        finally:
            connection.close()

    def insert(self, document: dict) -> dict:
        connection = self._connect()
        try:
            with connection:
                connection.execute("INSERT INTO profiles (id, name_key, document) VALUES (?, ?, ?)",
                                   (document["profile"]["id"], document["profile"]["name"].casefold(), json.dumps(document)))
        except sqlite3.IntegrityError as exc:
            raise ProfileConflict("A profile with this ID or name already exists. Nothing was replaced.") from exc
        finally:
            connection.close()
        return summary(document)

    def create(self, name: str) -> dict:
        document = validate_document({"format": "bnpl-profile", "version": 1,
                                      "profile": {"id": str(uuid4()), "name": name},
                                      "credit_cards": [], "bnpl_plans": []})
        return self.insert(document)

    @staticmethod
    def _document(connection: sqlite3.Connection, profile_id: str) -> dict:
        row = connection.execute("SELECT document FROM profiles WHERE id = ?", (profile_id,)).fetchone()
        if row is None:
            raise ProfileNotFound()
        return json.loads(row[0])

    def cards(self, profile_id: str) -> list[dict]:
        connection = self._connect()
        try:
            return self._document(connection, profile_id)["credit_cards"]
        finally:
            connection.close()

    @staticmethod
    def _card_changes(raw: object) -> dict:
        allowed = {"name", "current_balance", "statement_end_day", "payment_due_day",
                   "upcoming_statement_close_date", "upcoming_statement_due_date"}
        if not isinstance(raw, dict) or set(raw) - allowed:
            raise ValueError("Provide only nickname, current balance, and statement schedule fields.")
        card = dict(raw)
        # Transport conversion only: ranges, balance, and name rules stay in Python's
        # existing financial validator. Never truncate fractional day values.
        for field in ("statement_end_day", "payment_due_day"):
            value = card.get(field)
            if isinstance(value, str) and re.fullmatch(r"[+-]?[0-9]{1,10}", value.strip()):
                card[field] = int(value)
        return card

    def add_card(self, profile_id: str, raw: object) -> dict:
        card = {**self._card_changes(raw), "id": str(uuid4()), "profile_id": profile_id}
        validated = _card_value(validate_profile_payload({
            "credit_cards": [card], "bnpl_plans": [],
        }).credit_cards[0])
        connection = self._connect()
        try:
            with connection:
                # Lock before reading to avoid losing another request's appended card.
                connection.execute("BEGIN IMMEDIATE")
                document = self._document(connection, profile_id)
                document["credit_cards"].append(validated)
                connection.execute("UPDATE profiles SET document = ? WHERE id = ?",
                                   (json.dumps(document), profile_id))
        finally:
            connection.close()
        return validated

    def update_card(self, profile_id: str, card_id: str, raw: object) -> dict:
        changes = self._card_changes(raw)
        connection = self._connect()
        try:
            with connection:
                connection.execute("BEGIN IMMEDIATE")
                document = self._document(connection, profile_id)
                index = next((i for i, card in enumerate(document["credit_cards"]) if card["id"] == card_id), None)
                if index is None:
                    raise CardNotFound()
                candidate = {**document["credit_cards"][index], **changes}
                validated = _card_value(validate_profile_payload({
                    "credit_cards": [candidate], "bnpl_plans": [],
                }).credit_cards[0])
                document["credit_cards"][index] = validated
                connection.execute("UPDATE profiles SET document = ? WHERE id = ?", (json.dumps(document), profile_id))
        finally:
            connection.close()
        return validated
