from __future__ import annotations

import calendar
from datetime import date

from bnpl_cashflow.domain import CreditCard, DueDate, StatementCycle


def map_due_date(credit_card: CreditCard, statement_cycle: StatementCycle) -> DueDate:
    if not isinstance(credit_card, CreditCard):
        raise TypeError("credit_card must be a CreditCard instance")
    if not isinstance(statement_cycle, StatementCycle):
        raise TypeError("statement_cycle must be a StatementCycle instance")

    payment_due_date = _first_due_date_after(statement_cycle.cycle_end_date, credit_card.payment_due_day)

    return DueDate(
        credit_card_id=credit_card.id,
        statement_cycle_end_date=statement_cycle.cycle_end_date,
        payment_due_date=payment_due_date,
        statement_cycle_start_date=statement_cycle.cycle_start_date,
    )


def _first_due_date_after(statement_cycle_end_date: date, payment_due_day: int) -> date:
    year = statement_cycle_end_date.year
    month = statement_cycle_end_date.month

    while True:
        last_day = calendar.monthrange(year, month)[1]
        if payment_due_day <= last_day:
            candidate = date(year, month, payment_due_day)
            if candidate > statement_cycle_end_date:
                return candidate

        year, month = _add_months(year, month, 1)


def _add_months(year: int, month: int, delta: int) -> tuple[int, int]:
    month_index = (year * 12) + (month - 1) + delta
    new_year, new_month_index = divmod(month_index, 12)
    return new_year, new_month_index + 1
