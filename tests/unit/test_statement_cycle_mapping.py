from __future__ import annotations

from datetime import date
from decimal import Decimal

from bnpl_cashflow.domain import BNPLPlan, CreditCard, InstallmentFrequency, StatementCycle
from bnpl_cashflow.rules import generate_installments, map_statement_cycle


def _make_card(statement_end_day: int = 17) -> CreditCard:
    return CreditCard(
        id="card_tangerine_mastercard",
        name="Tangerine Mastercard",
        statement_end_day=statement_end_day,
        payment_due_day=13,
    )


def _make_installment(installment_date: date):
    plan = BNPLPlan(
        id="plan_klarna_laptop_sleeve",
        provider_name="Klarna",
        plan_name="Laptop Sleeve",
        purchase_amount=Decimal("120.00"),
        currency="CAD",
        purchase_date=date(2026, 6, 7),
        first_installment_date=installment_date,
        installment_count=1,
        installment_frequency=InstallmentFrequency.BIWEEKLY,
        credit_card_id="card_tangerine_mastercard",
    )
    return generate_installments(plan)[0]


def test_tc_002_installment_before_statement_end_day():
    card = _make_card()
    installment = _make_installment(date(2026, 6, 16))

    cycle = map_statement_cycle(card, installment)

    assert isinstance(cycle, StatementCycle)
    assert cycle.cycle_start_date == date(2026, 5, 18)
    assert cycle.cycle_end_date == date(2026, 6, 17)
    assert cycle.cycle_start_date <= installment.installment_date <= cycle.cycle_end_date


def test_tc_003_installment_exactly_on_statement_end_day():
    card = _make_card()
    installment = _make_installment(date(2026, 6, 17))

    cycle = map_statement_cycle(card, installment)

    assert isinstance(cycle, StatementCycle)
    assert cycle.cycle_start_date == date(2026, 5, 18)
    assert cycle.cycle_end_date == date(2026, 6, 17)
    assert cycle.cycle_start_date <= installment.installment_date <= cycle.cycle_end_date


def test_tc_004_installment_after_statement_end_day():
    card = _make_card()
    installment = _make_installment(date(2026, 6, 18))

    cycle = map_statement_cycle(card, installment)

    assert isinstance(cycle, StatementCycle)
    assert cycle.cycle_start_date == date(2026, 6, 18)
    assert cycle.cycle_end_date == date(2026, 7, 17)
    assert cycle.cycle_start_date <= installment.installment_date <= cycle.cycle_end_date


def test_month_boundary_scenario():
    card = _make_card(statement_end_day=6)
    plan = BNPLPlan(
        id="plan",
        provider_name="PayPal",
        plan_name="Month Boundary",
        purchase_amount=Decimal("60.00"),
        currency="CAD",
        purchase_date=date(2026, 6, 12),
        first_installment_date=date(2026, 6, 12),
        installment_count=1,
        installment_frequency=InstallmentFrequency.BIWEEKLY,
        credit_card_id="card_tangerine_mastercard",
    )
    mapped_installment = generate_installments(plan)[0]

    cycle = map_statement_cycle(card, mapped_installment)

    assert cycle.cycle_start_date == date(2026, 6, 7)
    assert cycle.cycle_end_date == date(2026, 7, 6)
    assert cycle.cycle_start_date <= mapped_installment.installment_date <= cycle.cycle_end_date


def test_year_rollover_scenario():
    card = _make_card()
    plan = BNPLPlan(
        id="plan_year_rollover",
        provider_name="Klarna",
        plan_name="Year Rollover",
        purchase_amount=Decimal("120.00"),
        currency="CAD",
        purchase_date=date(2026, 12, 10),
        first_installment_date=date(2026, 12, 10),
        installment_count=4,
        installment_frequency=InstallmentFrequency.BIWEEKLY,
        credit_card_id="card_tangerine_mastercard",
    )
    installment = generate_installments(plan)[2]

    cycle = map_statement_cycle(card, installment)

    assert cycle.cycle_start_date == date(2026, 12, 18)
    assert cycle.cycle_end_date == date(2027, 1, 17)
    assert cycle.cycle_start_date <= installment.installment_date <= cycle.cycle_end_date


def test_leap_year_scenario():
    card = _make_card()
    plan = BNPLPlan(
        id="plan_leap_year",
        provider_name="Klarna",
        plan_name="Leap Year",
        purchase_amount=Decimal("120.00"),
        currency="CAD",
        purchase_date=date(2028, 2, 15),
        first_installment_date=date(2028, 2, 15),
        installment_count=4,
        installment_frequency=InstallmentFrequency.BIWEEKLY,
        credit_card_id="card_tangerine_mastercard",
    )
    installment = generate_installments(plan)[1]

    cycle = map_statement_cycle(card, installment)

    assert cycle.cycle_start_date == date(2028, 2, 18)
    assert cycle.cycle_end_date == date(2028, 3, 17)
    assert cycle.cycle_start_date <= installment.installment_date <= cycle.cycle_end_date
