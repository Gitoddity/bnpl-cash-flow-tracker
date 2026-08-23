from __future__ import annotations

from dataclasses import dataclass
from datetime import date
from decimal import Decimal

from bnpl_cashflow.domain.frequency import InstallmentFrequency


def _require_non_empty_text(value: str, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"{field_name} must be a non-empty string")
    return value


def _require_date(value: date, field_name: str) -> date:
    if not isinstance(value, date):
        raise TypeError(f"{field_name} must be a datetime.date instance")
    return value


def _require_decimal(value: Decimal, field_name: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be a decimal.Decimal instance")
    if value <= Decimal("0"):
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_non_negative_decimal(value: Decimal, field_name: str) -> Decimal:
    if not isinstance(value, Decimal):
        raise TypeError(f"{field_name} must be a decimal.Decimal instance")
    if value < Decimal("0"):
        raise ValueError(f"{field_name} must be zero or greater")
    return value


def _require_positive_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value <= 0:
        raise ValueError(f"{field_name} must be positive")
    return value


def _require_non_negative_int(value: int, field_name: str) -> int:
    if isinstance(value, bool) or not isinstance(value, int):
        raise TypeError(f"{field_name} must be an integer")
    if value < 0:
        raise ValueError(f"{field_name} must be zero or greater")
    return value


def _require_day_of_month(value: int, field_name: str) -> int:
    value = _require_positive_int(value, field_name)
    if value > 31:
        raise ValueError(f"{field_name} must be between 1 and 31")
    return value


def _require_frequency(value: InstallmentFrequency, field_name: str) -> InstallmentFrequency:
    if not isinstance(value, InstallmentFrequency):
        raise TypeError(f"{field_name} must be an InstallmentFrequency value")
    return value


@dataclass(frozen=True, slots=True)
class CreditCard:
    id: str
    name: str
    statement_end_day: int
    payment_due_day: int
    current_balance: Decimal = Decimal("0.00")
    current_balance_due_date: date | None = None
    profile_name: str = "Default profile"

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _require_non_empty_text(self.id, "id"))
        object.__setattr__(self, "name", _require_non_empty_text(self.name, "name"))
        object.__setattr__(self, "profile_name", _require_non_empty_text(self.profile_name, "profile_name"))
        object.__setattr__(self, "statement_end_day", _require_day_of_month(self.statement_end_day, "statement_end_day"))
        object.__setattr__(self, "payment_due_day", _require_day_of_month(self.payment_due_day, "payment_due_day"))
        object.__setattr__(self, "current_balance", _require_non_negative_decimal(self.current_balance, "current_balance"))
        if self.current_balance_due_date is not None:
            object.__setattr__(
                self,
                "current_balance_due_date",
                _require_date(self.current_balance_due_date, "current_balance_due_date"),
            )


@dataclass(frozen=True, slots=True)
class BNPLPlan:
    id: str
    provider_name: str
    plan_name: str
    purchase_amount: Decimal
    currency: str
    purchase_date: date
    first_installment_date: date
    installment_count: int
    installment_frequency: InstallmentFrequency
    credit_card_id: str
    paid_installment_count: int = 0
    amount_paid: Decimal = Decimal("0.00")

    def __post_init__(self) -> None:
        object.__setattr__(self, "id", _require_non_empty_text(self.id, "id"))
        object.__setattr__(self, "provider_name", _require_non_empty_text(self.provider_name, "provider_name"))
        object.__setattr__(self, "plan_name", _require_non_empty_text(self.plan_name, "plan_name"))
        object.__setattr__(self, "purchase_amount", _require_decimal(self.purchase_amount, "purchase_amount"))
        object.__setattr__(self, "currency", _require_non_empty_text(self.currency, "currency"))
        object.__setattr__(self, "purchase_date", _require_date(self.purchase_date, "purchase_date"))
        object.__setattr__(self, "first_installment_date", _require_date(self.first_installment_date, "first_installment_date"))
        object.__setattr__(self, "installment_count", _require_positive_int(self.installment_count, "installment_count"))
        object.__setattr__(self, "installment_frequency", _require_frequency(self.installment_frequency, "installment_frequency"))
        object.__setattr__(self, "credit_card_id", _require_non_empty_text(self.credit_card_id, "credit_card_id"))
        object.__setattr__(
            self,
            "paid_installment_count",
            _require_non_negative_int(self.paid_installment_count, "paid_installment_count"),
        )
        if self.paid_installment_count > self.installment_count:
            raise ValueError("paid_installment_count must not exceed installment_count")
        object.__setattr__(self, "amount_paid", _require_non_negative_decimal(self.amount_paid, "amount_paid"))
        if self.amount_paid > self.purchase_amount:
            raise ValueError("amount_paid must not exceed purchase_amount")


@dataclass(frozen=True, slots=True)
class Installment:
    plan_id: str
    credit_card_id: str
    installment_number: int
    installment_date: date
    installment_amount: Decimal
    currency: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "plan_id", _require_non_empty_text(self.plan_id, "plan_id"))
        object.__setattr__(self, "credit_card_id", _require_non_empty_text(self.credit_card_id, "credit_card_id"))
        object.__setattr__(self, "installment_number", _require_positive_int(self.installment_number, "installment_number"))
        object.__setattr__(self, "installment_date", _require_date(self.installment_date, "installment_date"))
        object.__setattr__(self, "installment_amount", _require_decimal(self.installment_amount, "installment_amount"))
        object.__setattr__(self, "currency", _require_non_empty_text(self.currency, "currency"))


@dataclass(frozen=True, slots=True)
class StatementCycle:
    credit_card_id: str
    cycle_start_date: date
    cycle_end_date: date

    def __post_init__(self) -> None:
        object.__setattr__(self, "credit_card_id", _require_non_empty_text(self.credit_card_id, "credit_card_id"))
        object.__setattr__(self, "cycle_start_date", _require_date(self.cycle_start_date, "cycle_start_date"))
        object.__setattr__(self, "cycle_end_date", _require_date(self.cycle_end_date, "cycle_end_date"))
        if self.cycle_end_date < self.cycle_start_date:
            raise ValueError("cycle_end_date must be on or after cycle_start_date")


@dataclass(frozen=True, slots=True)
class DueDate:
    credit_card_id: str
    statement_cycle_end_date: date
    payment_due_date: date
    statement_cycle_start_date: date | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "credit_card_id", _require_non_empty_text(self.credit_card_id, "credit_card_id"))
        object.__setattr__(self, "statement_cycle_end_date", _require_date(self.statement_cycle_end_date, "statement_cycle_end_date"))
        object.__setattr__(self, "payment_due_date", _require_date(self.payment_due_date, "payment_due_date"))
        if self.statement_cycle_start_date is not None:
            object.__setattr__(self, "statement_cycle_start_date", _require_date(self.statement_cycle_start_date, "statement_cycle_start_date"))


@dataclass(frozen=True, slots=True)
class CashFlowObligation:
    due_date: date
    credit_card_id: str
    statement_cycle_end_date: date
    cash_flow_year: int
    cash_flow_month: int
    cash_flow_period: str
    currency: str
    total_amount: Decimal
    installments: tuple[Installment, ...]
    current_balance_amount: Decimal = Decimal("0.00")
    statement_cycle_start_date: date | None = None

    def __post_init__(self) -> None:
        object.__setattr__(self, "due_date", _require_date(self.due_date, "due_date"))
        object.__setattr__(self, "credit_card_id", _require_non_empty_text(self.credit_card_id, "credit_card_id"))
        object.__setattr__(self, "statement_cycle_end_date", _require_date(self.statement_cycle_end_date, "statement_cycle_end_date"))
        if self.statement_cycle_start_date is not None:
            object.__setattr__(self, "statement_cycle_start_date", _require_date(self.statement_cycle_start_date, "statement_cycle_start_date"))
        object.__setattr__(self, "cash_flow_year", _require_positive_int(self.cash_flow_year, "cash_flow_year"))
        object.__setattr__(self, "cash_flow_month", _require_positive_int(self.cash_flow_month, "cash_flow_month"))
        object.__setattr__(self, "cash_flow_period", _require_non_empty_text(self.cash_flow_period, "cash_flow_period"))
        object.__setattr__(self, "currency", _require_non_empty_text(self.currency, "currency"))
        object.__setattr__(self, "total_amount", _require_decimal(self.total_amount, "total_amount"))
        object.__setattr__(
            self,
            "current_balance_amount",
            _require_non_negative_decimal(self.current_balance_amount, "current_balance_amount"),
        )
        if self.current_balance_amount > self.total_amount:
            raise ValueError("current_balance_amount must not exceed total_amount")
        if not isinstance(self.installments, tuple):
            raise TypeError("installments must be a tuple of Installment instances")
        for installment in self.installments:
            if not isinstance(installment, Installment):
                raise TypeError("installments must contain only Installment instances")


@dataclass(frozen=True, slots=True)
class InstallmentProjection:
    provider_name: str
    plan_name: str
    installment_number: int
    installment_date: date
    installment_amount: Decimal
    currency: str
    credit_card_name: str
    statement_cycle_start_date: date
    statement_cycle_end_date: date
    cash_flow_due_date: date
    cash_flow_period: str

    def __post_init__(self) -> None:
        object.__setattr__(self, "provider_name", _require_non_empty_text(self.provider_name, "provider_name"))
        object.__setattr__(self, "plan_name", _require_non_empty_text(self.plan_name, "plan_name"))
        object.__setattr__(self, "installment_number", _require_positive_int(self.installment_number, "installment_number"))
        object.__setattr__(self, "installment_date", _require_date(self.installment_date, "installment_date"))
        object.__setattr__(self, "installment_amount", _require_decimal(self.installment_amount, "installment_amount"))
        object.__setattr__(self, "currency", _require_non_empty_text(self.currency, "currency"))
        object.__setattr__(self, "credit_card_name", _require_non_empty_text(self.credit_card_name, "credit_card_name"))
        object.__setattr__(self, "statement_cycle_start_date", _require_date(self.statement_cycle_start_date, "statement_cycle_start_date"))
        object.__setattr__(self, "statement_cycle_end_date", _require_date(self.statement_cycle_end_date, "statement_cycle_end_date"))
        object.__setattr__(self, "cash_flow_due_date", _require_date(self.cash_flow_due_date, "cash_flow_due_date"))
        object.__setattr__(self, "cash_flow_period", _require_non_empty_text(self.cash_flow_period, "cash_flow_period"))
