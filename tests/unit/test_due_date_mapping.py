from __future__ import annotations

from datetime import date
from decimal import Decimal

from bnpl_cashflow.domain import BNPLPlan, CreditCard, InstallmentFrequency, StatementCycle, DueDate
from bnpl_cashflow.rules import generate_installments, map_due_date, map_statement_cycle


def _make_card(*, statement_end_day: int = 17, payment_due_day: int = 13, name: str = "Tangerine Mastercard") -> CreditCard:
    return CreditCard(
        id="card_tangerine_mastercard",
        name=name,
        statement_end_day=statement_end_day,
        payment_due_day=payment_due_day,
    )


def _make_statement_cycle(statement_end_day: int, installment_date: date) -> StatementCycle:
    card = _make_card(statement_end_day=statement_end_day)
    plan = BNPLPlan(
        id="plan",
        provider_name="Klarna",
        plan_name="Plan",
        purchase_amount=Decimal("40.00"),
        currency="CAD",
        purchase_date=installment_date,
        first_installment_date=installment_date,
        installment_count=1,
        installment_frequency=InstallmentFrequency.BIWEEKLY,
        credit_card_id=card.id,
    )
    installment = generate_installments(plan)[0]
    return map_statement_cycle(card, installment)


def test_tc_005_due_date_in_same_calendar_month():
    card = _make_card(statement_end_day=10, payment_due_day=25, name="Same Month Mastercard")
    statement_cycle = _make_statement_cycle(statement_end_day=10, installment_date=date(2026, 6, 10))

    due_date = map_due_date(card, statement_cycle)

    assert isinstance(due_date, DueDate)
    assert due_date.statement_cycle_end_date == date(2026, 6, 10)
    assert due_date.payment_due_date == date(2026, 6, 25)


def test_tc_006_due_date_in_following_calendar_month():
    card = _make_card(statement_end_day=17, payment_due_day=13)
    statement_cycle = _make_statement_cycle(statement_end_day=17, installment_date=date(2026, 6, 17))

    due_date = map_due_date(card, statement_cycle)

    assert isinstance(due_date, DueDate)
    assert due_date.statement_cycle_end_date == date(2026, 6, 17)
    assert due_date.payment_due_date == date(2026, 7, 13)


def test_tangerine_mastercard_statement_close_maps_to_july_thirteenth():
    card = _make_card(statement_end_day=17, payment_due_day=13)
    statement_cycle = StatementCycle(
        credit_card_id=card.id,
        cycle_start_date=date(2026, 5, 18),
        cycle_end_date=date(2026, 6, 17),
    )

    due_date = map_due_date(card, statement_cycle)

    assert due_date.payment_due_date == date(2026, 7, 13)


def test_same_month_mastercard_statement_close_maps_to_june_twenty_fifth():
    card = _make_card(statement_end_day=10, payment_due_day=25, name="Same Month Mastercard")
    statement_cycle = StatementCycle(
        credit_card_id=card.id,
        cycle_start_date=date(2026, 5, 11),
        cycle_end_date=date(2026, 6, 10),
    )

    due_date = map_due_date(card, statement_cycle)

    assert due_date.payment_due_date == date(2026, 6, 25)


def test_year_rollover_due_date():
    card = _make_card(statement_end_day=17, payment_due_day=13)
    statement_cycle = StatementCycle(
        credit_card_id=card.id,
        cycle_start_date=date(2026, 12, 18),
        cycle_end_date=date(2027, 1, 17),
    )

    due_date = map_due_date(card, statement_cycle)

    assert due_date.payment_due_date == date(2027, 2, 13)
    assert due_date.statement_cycle_end_date == date(2027, 1, 17)


def test_leap_year_safe_due_date():
    card = _make_card(statement_end_day=17, payment_due_day=29)
    statement_cycle = StatementCycle(
        credit_card_id=card.id,
        cycle_start_date=date(2028, 2, 18),
        cycle_end_date=date(2028, 3, 17),
    )

    due_date = map_due_date(card, statement_cycle)

    assert due_date.payment_due_date == date(2028, 3, 29)


def test_due_day_31_uses_november_end_instead_of_skipping_a_statement():
    card = _make_card(statement_end_day=28, payment_due_day=31)
    cycle = StatementCycle(card.id, date(2026, 10, 29), date(2026, 11, 28))
    assert map_due_date(card, cycle).payment_due_date == date(2026, 11, 30)


def test_short_month_due_date_respects_leap_year_and_strictly_follows_close():
    card = _make_card(statement_end_day=17, payment_due_day=31)
    for year, last_day in ((2026, 28), (2028, 29)):
        cycle = StatementCycle(card.id, date(year, 1, 18), date(year, 2, 17))
        assert map_due_date(card, cycle).payment_due_date == date(year, 2, last_day)
    # Clamping must not place the payment on the closing date itself.
    cycle = StatementCycle(card.id, date(2026, 11, 1), date(2026, 11, 30))
    assert map_due_date(card, cycle).payment_due_date == date(2026, 12, 31)
