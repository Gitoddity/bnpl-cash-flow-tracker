from __future__ import annotations

from datetime import date
from decimal import Decimal

from bnpl_cashflow.domain import BNPLPlan, CreditCard, InstallmentFrequency, StatementCycle, DueDate, InstallmentProjection
from bnpl_cashflow.rules import generate_installments, map_due_date, map_statement_cycle
from bnpl_cashflow.reporting import build_installment_projection, build_installment_projections


def _make_card(*, statement_end_day: int = 17, payment_due_day: int = 13, name: str = "Tangerine Mastercard") -> CreditCard:
    return CreditCard(
        id="card_tangerine_mastercard",
        name=name,
        statement_end_day=statement_end_day,
        payment_due_day=payment_due_day,
    )


def _make_plan(*, first_installment_date: date, installment_count: int, purchase_amount: Decimal = Decimal("120.00")) -> BNPLPlan:
    return BNPLPlan(
        id="plan_klarna_laptop_sleeve",
        provider_name="Klarna",
        plan_name="Laptop Sleeve",
        purchase_amount=purchase_amount,
        currency="CAD",
        purchase_date=date(2026, 6, 7),
        first_installment_date=first_installment_date,
        installment_count=installment_count,
        installment_frequency=InstallmentFrequency.BIWEEKLY,
        credit_card_id="card_tangerine_mastercard",
    )


def test_successful_installment_projection_construction():
    card = _make_card()
    plan = _make_plan(first_installment_date=date(2026, 6, 7), installment_count=4)
    installment = generate_installments(plan)[0]
    statement_cycle = map_statement_cycle(card, installment)
    due_date = map_due_date(card, statement_cycle)

    projection = build_installment_projection(plan, card, installment, statement_cycle, due_date)

    assert isinstance(projection, InstallmentProjection)
    assert projection.provider_name == "Klarna"
    assert projection.plan_name == "Laptop Sleeve"
    assert projection.installment_date == date(2026, 6, 7)
    assert projection.installment_amount == Decimal("30.00")
    assert projection.credit_card_name == "Tangerine Mastercard"
    assert projection.statement_cycle_start_date == date(2026, 5, 18)
    assert projection.statement_cycle_end_date == date(2026, 6, 17)
    assert projection.cash_flow_due_date == date(2026, 7, 13)
    assert projection.cash_flow_period == "2026-07"


def test_projection_field_mapping_from_source_objects():
    card = _make_card()
    plan = _make_plan(first_installment_date=date(2026, 6, 7), installment_count=4)
    installment = generate_installments(plan)[2]
    statement_cycle = map_statement_cycle(card, installment)
    due_date = map_due_date(card, statement_cycle)

    projection = build_installment_projection(plan, card, installment, statement_cycle, due_date)

    assert projection.installment_number == 3
    assert projection.installment_date == installment.installment_date
    assert projection.statement_cycle_start_date == statement_cycle.cycle_start_date
    assert projection.statement_cycle_end_date == statement_cycle.cycle_end_date
    assert projection.cash_flow_due_date == due_date.payment_due_date
    assert projection.cash_flow_period == "2026-08"


def test_tc_001_style_projection_values():
    card = _make_card()
    plan = _make_plan(first_installment_date=date(2026, 6, 7), installment_count=4)

    installments = generate_installments(plan)
    statement_cycles = [map_statement_cycle(card, installment) for installment in installments]
    due_dates = [map_due_date(card, statement_cycle) for statement_cycle in statement_cycles]
    projections = build_installment_projections(plan, card, installments, statement_cycles, due_dates)

    assert [projection.installment_date for projection in projections] == [
        date(2026, 6, 7),
        date(2026, 6, 21),
        date(2026, 7, 5),
        date(2026, 7, 19),
    ]
    assert [projection.cash_flow_due_date for projection in projections] == [
        date(2026, 7, 13),
        date(2026, 8, 13),
        date(2026, 8, 13),
        date(2026, 9, 13),
    ]
    assert [projection.cash_flow_period for projection in projections] == [
        "2026-07",
        "2026-08",
        "2026-08",
        "2026-09",
    ]


def test_leap_year_style_projection_values():
    card = _make_card()
    plan = _make_plan(first_installment_date=date(2028, 2, 15), installment_count=4)

    installments = generate_installments(plan)
    statement_cycles = [map_statement_cycle(card, installment) for installment in installments]
    due_dates = [map_due_date(card, statement_cycle) for statement_cycle in statement_cycles]
    projections = build_installment_projections(plan, card, installments, statement_cycles, due_dates)

    assert projections[1].installment_date == date(2028, 2, 29)
    assert projections[1].statement_cycle_start_date == date(2028, 2, 18)
    assert projections[1].statement_cycle_end_date == date(2028, 3, 17)
    assert projections[1].cash_flow_due_date == date(2028, 4, 13)
    assert projections[1].cash_flow_period == "2028-04"


def test_projection_construction_does_not_format_text():
    card = _make_card()
    plan = _make_plan(first_installment_date=date(2026, 6, 7), installment_count=1)
    installment = generate_installments(plan)[0]
    statement_cycle = map_statement_cycle(card, installment)
    due_date = map_due_date(card, statement_cycle)

    projection = build_installment_projection(plan, card, installment, statement_cycle, due_date)

    assert not isinstance(projection, str)

