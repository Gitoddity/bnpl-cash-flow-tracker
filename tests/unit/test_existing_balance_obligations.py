from __future__ import annotations

from datetime import date
from decimal import Decimal

from bnpl_cashflow.application.services import (
    _include_current_balance_obligations,
    _payment_due_after,
    _statement_end_before,
    _statement_end_on_or_after,
)
from bnpl_cashflow.domain import CashFlowObligation, CreditCard


def _card(*, balance: Decimal, due_date: date | None) -> CreditCard:
    return CreditCard(
        id="card_tangerine",
        name="Tangerine",
        statement_end_day=17,
        payment_due_day=13,
        current_balance=balance,
        current_balance_due_date=due_date,
    )


def test_standalone_current_balance_creates_dated_obligation():
    obligations = _include_current_balance_obligations(
        (),
        (_card(balance=Decimal("626.52"), due_date=date(2026, 8, 13)),),
        "CAD",
    )

    assert len(obligations) == 1
    assert obligations[0].due_date == date(2026, 8, 13)
    assert obligations[0].statement_cycle_end_date == date(2026, 7, 17)
    assert obligations[0].total_amount == Decimal("626.52")
    assert obligations[0].current_balance_amount == Decimal("626.52")
    assert obligations[0].installments == ()


def test_zero_or_undated_balance_does_not_create_obligation():
    obligations = _include_current_balance_obligations(
        (),
        (
            _card(balance=Decimal("0.00"), due_date=date(2026, 8, 13)),
            _card(balance=Decimal("100.00"), due_date=None),
        ),
        "CAD",
    )

    assert obligations == ()


def test_current_balance_merges_with_same_card_and_due_date():
    bnpl = CashFlowObligation(
        due_date=date(2026, 8, 13),
        credit_card_id="card_tangerine",
        statement_cycle_end_date=date(2026, 7, 17),
        cash_flow_year=2026,
        cash_flow_month=8,
        cash_flow_period="2026-08",
        currency="CAD",
        total_amount=Decimal("40.00"),
        installments=(),
    )

    obligations = _include_current_balance_obligations(
        (bnpl,),
        (_card(balance=Decimal("626.52"), due_date=date(2026, 8, 13)),),
        "CAD",
    )

    assert len(obligations) == 1
    assert obligations[0].total_amount == Decimal("666.52")
    assert obligations[0].current_balance_amount == Decimal("626.52")


def test_statement_end_date_handles_month_end_and_year_rollover():
    assert _statement_end_before(date(2026, 3, 5), 31) == date(2026, 2, 28)
    assert _statement_end_before(date(2026, 1, 13), 17) == date(2025, 12, 17)


def test_as_of_date_derives_current_statement_and_payment_due_date():
    statement_end = _statement_end_on_or_after(date(2026, 7, 25), 13)
    payment_due = _payment_due_after(statement_end, 13)

    assert statement_end == date(2026, 8, 13)
    assert payment_due == date(2026, 9, 13)


def test_as_of_date_assigns_undated_current_balance():
    obligations = _include_current_balance_obligations(
        (),
        (_card(balance=Decimal("626.52"), due_date=None),),
        "CAD",
        as_of_date=date(2026, 7, 25),
    )

    assert obligations[0].due_date == date(2026, 9, 13)
    assert obligations[0].current_balance_amount == Decimal("626.52")
