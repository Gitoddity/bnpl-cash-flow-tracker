from __future__ import annotations

from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation
from typing import Any


SUPPORTED_CURRENCIES = {"CAD", "USD"}
SUPPORTED_PROVIDERS = {"paypal", "klarna", "afterpay", "sezzle", "affirm"}
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
    current_balance: Decimal = Decimal("0.00")
    current_balance_due_date: date | None = None
    profile_id: str = "profile_1"
    upcoming_statement_close_date: date | None = None
    upcoming_statement_due_date: date | None = None
    currency: str | None = None


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
    paid_installment_count: int = 0
    amount_paid: Decimal = Decimal("0.00")


@dataclass(frozen=True, slots=True)
class ValidatedPayload:
    credit_cards: tuple[CreditCardInput, ...]
    bnpl_plans: tuple[BNPLPlanInput, ...]
    output_options: Mapping[str, Any]


def validate_payload(payload: Mapping[str, Any]) -> ValidatedPayload:
    return _validate_payload(payload, allow_empty=False)


def validate_profile_payload(payload: Mapping[str, Any], *, allow_mixed_currencies: bool = False) -> ValidatedPayload:
    """Validate portable profile contents, including empty setup-stage profiles."""
    return _validate_payload(payload, allow_empty=True, allow_mixed_currencies=allow_mixed_currencies)


def _validate_payload(payload: Mapping[str, Any], *, allow_empty: bool, allow_mixed_currencies: bool = False) -> ValidatedPayload:
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
        normalized_credit_cards = _validate_credit_cards(raw_credit_cards, issues, allow_empty=allow_empty)

    if "bnpl_plans" in payload:
        normalized_bnpl_plans = _validate_bnpl_plans(raw_bnpl_plans, issues, allow_empty=allow_empty)

    if normalized_bnpl_plans and (normalized_credit_cards or allow_empty):
        _validate_references(normalized_bnpl_plans, normalized_credit_cards, issues)
        if not allow_mixed_currencies:
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


def _validate_credit_cards(value: Any, issues: list[ValidationIssue], *, allow_empty: bool = False) -> list[CreditCardInput]:
    if not isinstance(value, list):
        issues.append(ValidationIssue(path="credit_cards", message="must be an array", value=value))
        return []
    if not value and not allow_empty:
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
        card_currency = item.get("currency")
        if card_currency is not None:
            if isinstance(card_currency, str) and card_currency.strip().upper() in SUPPORTED_CURRENCIES:
                card_currency = card_currency.strip().upper()
            else:
                issues.append(ValidationIssue(f"{path}.currency", "choose CAD or USD"))
                card_currency = None
        exact_close = exact_due = None
        if "upcoming_statement_close_date" in item or "upcoming_statement_due_date" in item:
            exact_close = _require_date_field(item, "upcoming_statement_close_date", path, issues)
            exact_due = _require_date_field(item, "upcoming_statement_due_date", path, issues)
            if exact_close and exact_due:
                if exact_due <= exact_close:
                    issues.append(ValidationIssue(f"{path}.upcoming_statement_due_date", "must be after the statement closing date"))
                item = {**item, "statement_end_day": exact_close.day, "payment_due_day": exact_due.day}
        statement_end_day = _require_day_of_month(item, "statement_end_day", path, issues)
        payment_due_day = _require_day_of_month(item, "payment_due_day", path, issues)
        current_balance = _resolve_current_balance(item, path, issues)
        current_balance_due_date = _resolve_current_balance_due_date(item, path, issues)
        profile_id = _optional_profile_id(item, path, issues)

        if (
            card_id is None
            or name is None
            or statement_end_day is None
            or payment_due_day is None
            or current_balance is None
            or profile_id is None
        ):
            continue

        if (
            "current_balance_due_date" in item
            or "existing_balance_due_date" in item
        ) and current_balance_due_date is None:
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
                current_balance=current_balance,
                current_balance_due_date=current_balance_due_date,
                profile_id=profile_id,
                upcoming_statement_close_date=exact_close,
                upcoming_statement_due_date=exact_due,
                currency=card_currency,
            )
        )

    return cards


def _validate_bnpl_plans(value: Any, issues: list[ValidationIssue], *, allow_empty: bool = False) -> list[BNPLPlanInput]:
    if not isinstance(value, list):
        issues.append(ValidationIssue(path="bnpl_plans", message="must be an array", value=value))
        return []
    if not value and not allow_empty:
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
        if provider_name is not None:
            provider_name = provider_name.lower()
            if provider_name not in SUPPORTED_PROVIDERS:
                issues.append(ValidationIssue(f"{path}.provider_name", "Select PayPal, Klarna, Afterpay, Sezzle, or Affirm."))
                provider_name = None
        plan_name = _require_string_field(item, "plan_name", path, issues)
        purchase_amount = _require_decimal_field(item, "purchase_amount", path, issues)
        currency = _require_currency_field(item, "currency", path, issues)
        purchase_date = _require_date_field(item, "purchase_date", path, issues)
        first_installment_date = _require_date_field(item, "first_installment_date", path, issues)
        installment_count = _require_positive_int_field(item, "installment_count", path, issues)
        installment_frequency = _require_installment_frequency_field(item, "installment_frequency", path, issues)
        credit_card_id = _require_string_field(item, "credit_card_id", path, issues)
        paid_installment_count = _optional_non_negative_int_field(item, "paid_installment_count", path, issues)
        amount_paid = _require_non_negative_decimal_field(item, "amount_paid", path, issues)

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
            or paid_installment_count is None
            or amount_paid is None
        ):
            continue

        if paid_installment_count > installment_count:
            issues.append(
                ValidationIssue(
                    path=f"{path}.paid_installment_count",
                    message="must not exceed installment_count",
                    value=paid_installment_count,
                )
            )
            continue

        if amount_paid > purchase_amount:
            issues.append(
                ValidationIssue(
                    path=f"{path}.amount_paid",
                    message="must not exceed purchase_amount",
                    value=str(amount_paid),
                )
            )
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
                paid_installment_count=paid_installment_count,
                amount_paid=amount_paid,
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


def _optional_non_negative_int_field(
    item: Mapping[str, Any],
    field_name: str,
    path: str,
    issues: list[ValidationIssue],
) -> int | None:
    if field_name not in item:
        return 0

    value = item[field_name]
    if isinstance(value, bool) or not isinstance(value, int):
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be an integer", value=value))
        return None
    if value < 0:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be zero or greater", value=value))
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

    if not decimal_value.is_finite():
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be finite"))
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

    if not decimal_value.is_finite():
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be finite"))
        return None
    if decimal_value < 0:
        issues.append(ValidationIssue(path=f"{path}.{field_name}", message="must be zero or greater", value=value))
        return None

    return decimal_value


def _resolve_current_balance(
    item: Mapping[str, Any],
    path: str,
    issues: list[ValidationIssue],
) -> Decimal | None:
    if "current_balance" in item and "existing_balance" in item:
        issues.append(
            ValidationIssue(
                path=f"{path}.current_balance",
                message="must not be provided together with legacy existing_balance",
            )
        )
        return None
    field_name = "current_balance" if "current_balance" in item else "existing_balance"
    return _require_non_negative_decimal_field(item, field_name, path, issues)


def _resolve_current_balance_due_date(
    item: Mapping[str, Any],
    path: str,
    issues: list[ValidationIssue],
) -> date | None:
    if "current_balance_due_date" in item and "existing_balance_due_date" in item:
        issues.append(
            ValidationIssue(
                path=f"{path}.current_balance_due_date",
                message="must not be provided together with legacy existing_balance_due_date",
            )
        )
        return None
    field_name = (
        "current_balance_due_date"
        if "current_balance_due_date" in item
        else "existing_balance_due_date"
    )
    return _optional_date_field(item, field_name, path, issues)


def _optional_profile_id(item: Mapping[str, Any], path: str, issues: list[ValidationIssue]) -> str | None:
    if "profile_id" in item:
        return _require_string_field(item, "profile_id", path, issues)
    # Legacy calculation payloads identified the implicit profile by name.
    # Keep that compatibility at this boundary only.
    if "profile_name" in item:
        return "profile_1"
    return "profile_1"


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


def _optional_date_field(
    item: Mapping[str, Any],
    field_name: str,
    path: str,
    issues: list[ValidationIssue],
) -> date | None:
    if field_name not in item:
        return None
    return _require_date_field(item, field_name, path, issues)


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
