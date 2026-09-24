from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from bnpl_cashflow.ui.workflow import build_payload


def default_draft_path() -> Path:
    return Path(__file__).resolve().parents[3] / "user-data" / "bnpl-ui-draft.json"


def draft_exists(path: Path | None = None) -> bool:
    return (path or default_draft_path()).is_file()


def save_draft(
    profiles: Sequence[dict[str, Any]], credit_cards: Sequence[dict[str, Any]], bnpl_plans: Sequence[dict[str, Any]], path: Path | None = None
) -> Path:
    payload = build_payload(credit_cards, bnpl_plans)
    # Drafts preserve in-progress local state. Financial validation still runs
    # only when a calculation payload is submitted to the application service.
    envelope = {"profiles": [dict(profile) for profile in profiles], **payload}
    draft_path = path or default_draft_path()
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(json.dumps(envelope, indent=2) + "\n", encoding="utf-8")
    return draft_path


def load_draft(path: Path | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]], list[dict[str, Any]]]:
    draft_path = path or default_draft_path()
    payload = json.loads(draft_path.read_text(encoding="utf-8"))
    cards = [dict(card) for card in payload["credit_cards"]]
    plans = [dict(plan) for plan in payload["bnpl_plans"]]
    profiles = _load_profiles(payload, cards)
    return profiles, cards, plans


def _load_profiles(payload: dict[str, Any], cards: list[dict[str, Any]]) -> list[dict[str, Any]]:
    raw_profiles = payload.get("profiles")
    if isinstance(raw_profiles, list):
        profiles = [{"id": str(profile["id"]), "name": str(profile["name"])} for profile in raw_profiles]
        valid_ids = {profile["id"] for profile in profiles}
        if any(card.get("profile_id") not in valid_ids for card in cards):
            raise ValueError("draft card references an unknown profile")
        return profiles

    # Legacy draft: profile names live on cards. Materialize stable identities.
    by_name: dict[str, str] = {}
    profiles: list[dict[str, Any]] = []
    for card in cards:
        name = str(card.pop("profile_name", "Default profile")).strip() or "Default profile"
        key = name.casefold()
        if key not in by_name:
            profile_id = f"profile_{len(profiles) + 1}"
            by_name[key] = profile_id
            profiles.append({"id": profile_id, "name": name})
        card["profile_id"] = by_name[key]
    return profiles


def discard_draft(path: Path | None = None) -> None:
    draft_path = path or default_draft_path()
    if draft_path.exists():
        draft_path.unlink()
