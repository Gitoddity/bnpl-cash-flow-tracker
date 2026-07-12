from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


SUPPORTED_CURRENCIES = {"CAD", "USD"}
SUPPORTED_INSTALLMENT_FREQUENCIES = {"BIWEEKLY"}


@dataclass(frozen=True, slots=True)
class ValidationIssue:
    path: str
    message: str
    value: Any | None = None

    def format(self) -> str:
        if self.value is None:
            return f"{self.path}: {self.message}"
        return f"{self.path}: {self.message} (value={self.value!r})"


class InputValidationError(ValueError):
    def __init__(self, issues: Sequence[ValidationIssue]):
        if not issues:
            raise ValueError("issues must not be empty")
        self.issues = tuple(issues)
        super().__init__(self._build_message())

    def _build_message(self) -> str:
        if len(self.issues) == 1:
            return self.issues[0].format()
        return "; ".join(issue.format() for issue in self.issues)


@dataclass(frozen=True, slots=True)
class CreditCardInput:
    id: str
    name: str
    statement_end_day: int
    payment_due_day: int
    existing_balance: Decimal = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class BNPLPlanInput:
    id: str
    provider_name: str
    plan_name: str
    purchase_amount: Decimal
    currency: str
    purchase_date: date
    first_installment_date: date
    installment_count: int
    installment_frequency: str
    credit_card_id: str


@dataclass(frozen=True, slots=True)
class ValidatedPayload:
    credit_cards: tuple[CreditCardInput, ...]
    bnpl_plans: tuple[BNPLPlanInput, ...]
    output_options: Mapping[str, Any]


def validate_payload(payload: Mapping[str, Any]) -> ValidatedPayload:
    if not isinstance(payload, Mapping):
        raise InputValidationError([ValidationIssue(path="$", message="payload must be a mapping", value=payload)])

    issues: list[ValidationIssue] = []
    normalized_output_options = _validate_output_options(payload.get("output_options"), issues)

    raw_credit_cards = payload.get("credit_cards")
    raw_bnpl_plans = payload.get("bnpl_plans")

    if "credit_cards" not in payload:
        issues.append(ValidationIssue(path="credit_cards", message="is required"))
    if "bnpl_plans" not in payload:
        issues.append(ValidationIssue(path="bnpl_plans", message="is required"))

    normalized_credit_cards: list[CreditCardInput] = []
    normalized_bnpl_plans: list[BNPLPlanInput] = []

    if "credit_cards" in payload:
        normalized_credit_cards = _validate_credit_cards(raw_credit_cards, issues)

    if "bnpl_plans" in payload:
        normalized_bnpl_plans = _validate_bnpl_plans(raw_bnpl_plans, issues)

    if normalized_credit_cards and normalized_bnpl_plans:
        _validate_references(normalized_bnpl_plans, normalized_credit_cards, issues)
        _validate_currency_consistency(normalized_bnpl_plans, issues)

    if issues:
        raise InputValidationError(issues)

    return ValidatedPayload(
        credit_cards=tuple(normalized_credit_cards),
        bnpl_plans=tuple(normalized_bnpl_plans),
        output_options=normalized_output_options,
    )


def _validate_output_options(value: Any, issues: list[ValidationIssue]) -> Mapping[str, Any]:
    if value is None:
        return {}
    if not isinstance(value, Mapping):
        issues.append(ValidationIssue(path="output_options", message="must be an object", value=value))
        return {}
    return dict(value)


def _validate_credit_cards(value: Any, issues: list[ValidationIssue]) -> list[CreditCardInput]:
    if not isinstance(value, list):
        issues.append(ValidationIssue(path="credit_cards", message="must be an array", value=value))
        return []
    if not value:
        issues.append(ValidationIssue(path="credit_cards", message="must contain at least one item", value=value))
        return []

    cards: list[CreditCardInput] = []
    seen_ids: dict[str, int] = {}
    for index, item in enumerate(value):
        path = f"credit_cards[{index}]"
        if not isinstance(item, Mapping):
            issues.append(ValidationIssue(path=path, message="must be an object", value=item))
            continue

        card_id = _require_string_field(item, "id", path, issues)
        name = _require_string_field(item, "name", path, issues)
        statement_end_day = _require_day_of_month(item, "statement_end_day", path, issues)
        payment_due_day = _require_day_of_month(item, "payment_due_day", path, issues)
        existing_balance = _require_non_negative_decimal_field(item, "existing_balance", path, issues)

        if (
            card_id is None
            or name is None
            or statement_end_day is None
            or payment_due_day is None
            or existing_balance is None
        ):
            continue

        if card_id in seen_ids:
            issues.append(
                ValidationIssue(
                    path=f"{path}.id",
                    message=f"duplicates credit_cards[{seen_ids[card_id]}].id",
                    value=card_id,
                )
            )
        else:
            seen_ids[card_id] = index

        cards.append(
            CreditCardInput(
                id=card_id,
                name=name,
                statement_end_day=statement_end_day,
                payment_due_day=payment_due_day,
                existing_balance=existing_balance,
            )
        )

    return cards


def _validate_bnpl_plans(value: Any, issues: list[ValidationIssue]) -> list[BNPLPlanInput]:
    if not isinstance(value, list):
        issues.append(ValidationIssue(path="bnpl_plans", message="must be an array", value=value))
        return []
    if not value:
        issues.append(ValidationIssue(path="bnpl_plans", message="must contain at least one item", value=value))
        return []

    plans: list[BNPLPlanInput] = []
    seen_ids: dict[str, int] = {}
    for index, item in enumerate(value):
        path = f"bnpl_plans[{index}]"
        if not isinstance(item, Mapping):
            issues.append(ValidationIssue(path=path, message="must be an object", value=item))
            continue

        plan_id = _require_string_field(item, "id", path, issues)
        provider_name = _require_string_field(item, "provider_name", path, issues)
        plan_name = _require_string_field(item, "plan_name", path, issues)
        purchase_amount = _require_decimal_field(item, "purchase_amount", path, issues)
        currency = _require_currency_field(item, "currency", path, issues)
        purchase_date = _require_date_field(item, "purchase_date", path, issues)
        first_installment_date = _require_date_field(item, "first_installment_date", path, issues)
        installment_count = _require_positive_int_field(item, "installment_count", path, issues)
        installment_frequency = _require_installment_frequency_field(item, "installment_frequency", path, issues)
        credit_card_id = _require_string_field(item, "credit_card_id", path, issues)

        if (
            plan_id is None
            or provider_name is None
            or plan_name is None
            or purchase_amount is None
            or currency is None
            or purchase_date is None
            or first_installment_date is None
            or installment_count is None
            or installment_frequency is None
            or credit_card_id is None
        ):
            continue

        if plan_id in seen_ids:
            issues.append(
                ValidationIssue(
                    path=f"{path}.id",
                    message=f"duplicates bnpl_plans[{seen_ids[plan_id]}].id",
                    value=plan_id,
                )
            )
        else:
            seen_ids[plan_id] = index

        plans.append(
            BNPLPlanInput(
                id=plan_id,
                provider_name=provider_name,
                plan_name=plan_name,
                purchase_amount=purchase_amount,
                currency=currency,
                purchase_date=purchase_date,
                first_installment_date=first_installment_date,
                installment_count=installment_count,
                installment_frequency=installment_frequency,
                credit_card_id=credit_card_id,
            )
        )

    return plans


def _validate_references(
    plans: Sequence[BNPLPlanInput],
    credit_cards: Sequence[CreditCardInput],
    issues: list[ValidationIssue],
) -> None:
    valid_card_ids = {card.id for card in credit_cards}
    for index, plan in enumerate(plans):
        if plan.credit_card_id not in valid_card_ids:
            issues.append(
                ValidationIssue(
                    path=f"bnpl_plans[{index}].credit_card_id",
                    message="must reference an existing credit_cards[].id",
                    value=plan.credit_card_id,
                )
            )


def _validate_currency_consistency(plans: Sequence[BNPLPlanInput], issues: list[ValidationIssue]) -> None:
    currencies = {plan.currency for plan in plans}
    if len(currencies) > 1:
        issues.append(
            ValidationIssue(
                path="bnpl_plans",
                message="mixed-currency payloads are not supported in MVP 2",
                value=sorted(currencies),
            )
        )


def _require_string_field(
    item: Mapping[str, Any],
    field_name: str,
    path: str,
    issues: list[ValidationIssue],
) -> str | None:
    if field_name not in item:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="is required"))
        return None

    value = item[field_name]
    if not isinstance(value, str):
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be a string", value=value))
        return None

    normalized = value.strip()
    if not normalized:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must not be empty", value=value))
        return None

    return normalized


def _require_day_of_month(
    item: Mapping[str, Any],
    field_name: str,
    path: str,
    issues: list[ValidationIssue],
) -> int | None:
    if field_name not in item:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="is required"))
        return None

    value = item[field_name]
    if isinstance(value, bool) or not isinstance(value, int):
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be an integer", value=value))
        return None
    if value < 1 or value > 31:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be between 1 and 31", value=value))
        return None
    return value


def _require_positive_int_field(
    item: Mapping[str, Any],
    field_name: str,
    path: str,
    issues: list[ValidationIssue],
) -> int | None:
    if field_name not in item:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="is required"))
        return None

    value = item[field_name]
    if isinstance(value, bool) or not isinstance(value, int):
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be an integer", value=value))
        return None
    if value <= 0:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be greater than zero", value=value))
        return None
    return value


def _require_decimal_field(
    item: Mapping[str, Any],
    field_name: str,
    path: str,
    issues: list[ValidationIssue],
) -> Decimal | None:
    if field_name not in item:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="is required"))
        return None

    value = item[field_name]
    if not isinstance(value, str):
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be a string", value=value))
        return None

    normalized = value.strip()
    if not normalized:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must not be empty", value=value))
        return None

    try:
        decimal_value = Decimal(normalized)
    except (InvalidOperation, ValueError):
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be a valid decimal value", value=value))
        return None

    if decimal_value <= 0:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be greater than zero", value=value))
        return None

    return decimal_value


def _require_non_negative_decimal_field(
    item: Mapping[str, Any],
    field_name: str,
    path: str,
    issues: list[ValidationIssue],
) -> Decimal | None:
    if field_name not in item:
        return Decimal("0.00")

    value = item[field_name]
    if not isinstance(value, str):
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be a string", value=value))
        return None

    normalized = value.strip()
    if not normalized:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must not be empty", value=value))
        return None

    try:
        decimal_value = Decimal(normalized)
    except (InvalidOperation, ValueError):
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be a valid decimal value", value=value))
        return None

    if decimal_value < 0:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be zero or greater", value=value))
        return None

    return decimal_value


def _require_currency_field(
    item: Mapping[str, Any],
    field_name: str,
    path: str,
    issues: list[ValidationIssue],
) -> str | None:
    value = _require_string_field(item, field_name, path, issues)
    if value is None:
        return None

    currency = value.upper()
    if currency not in SUPPORTED_CURRENCIES:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="unsupported currency", value=value))
        return None
    return currency


def _require_date_field(
    item: Mapping[str, Any],
    field_name: str,
    path: str,
    issues: list[ValidationIssue],
) -> date | None:
    value = _require_string_field(item, field_name, path, issues)
    if value is None:
        return None

    try:
        return date.fromisoformat(value)
    except ValueError:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be a valid YYYY-MM-DD date", value=value))
        return None


def _require_installment_frequency_field(
    item: Mapping[str, Any],
    field_name: str,
    path: str,
    issues: list[ValidationIssue],
) -> str | None:
    value = _require_string_field(item, field_name, path, issues)
    if value is None:
        return None

    frequency = value.upper()
    if frequency not in SUPPORTED_INSTALLMENT_FREQUENCIES:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="unsupported installment frequency", value=value))
        return None
    return frequency
