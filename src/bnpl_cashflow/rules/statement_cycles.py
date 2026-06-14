from __future__ import annotations

import calendar
from datetime import date, timedelta

from bnpl_cashflow.domain import CreditCard, Installment, StatementCycle


def map_statement_cycle(credit_card: CreditCard, installment: Installment) -> StatementCycle:
    if not isinstance(credit_card, CreditCard):
        raise TypeError("credit_card must be a CreditCard instance")
    if not isinstance(installment, Installment):
        raise TypeError("installment must be an Installment instance")

    cycle_end_date = _statement_cycle_end_date(installment.installment_date, credit_card.statement_end_day)
    cycle_start_date = _previous_cycle_end_date(cycle_end_date, credit_card.statement_end_day) + timedelta(days=1)

    return StatementCycle(
        credit_card_id=credit_card.id,
        cycle_start_date=cycle_start_date,
        cycle_end_date=cycle_end_date,
    )


def _statement_cycle_end_date(installment_date: date, statement_end_day: int) -> date:
    if installment_date.day <= statement_end_day:
        return _build_date(installment_date.year, installment_date.month, statement_end_day)

    year, month = _add_months(installment_date.year, installment_date.month, 1)
    return _build_date(year, month, statement_end_day)


def _previous_cycle_end_date(cycle_end_date: date, statement_end_day: int) -> date:
    year, month = _add_months(cycle_end_date.year, cycle_end_date.month, -1)
    return _build_date(year, month, statement_end_day)


def _add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    month_index = (year * 12) + (month - 1) + delta
    new_year, new_month_index = divmod(month_index, 12)
    return new_year, new_month_index + 1


def _build_date(year: int, month: int, day: int) -> date:
    last_day = calendar.monthrange(year, month)[1]
    if day < 1 or day > last_day:
        raise ValueError(f"day {day} is not valid for {year:04d}-{month:02d}")
    return date(year, month, day)
