from __future__ import annotations

from datetime import date
from decimal import Decimal

from bnpl_cashflow.domain import BNPLPlan, CreditCard, InstallmentFrequency
from bnpl_cashflow.reporting import (
    build_installment_projection,
    render_cash_flow_obligations,
    render_installment_projections,
    render_installment_schedule,
)
from bnpl_cashflow.rules import aggregate_cash_flow, generate_installments, map_due_date, map_statement_cycle


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


def test_render_installment_schedule():
    plan = _make_plan(first_installment_date=date(2026, 6, 7), installment_count=4)
    installments = generate_installments(plan)

    rendered = render_installment_schedule(installments)

    assert "Installment Schedule" in rendered
    assert "2026-06-07" in rendered
    assert "30.00 CAD" in rendered
    assert "4. 2026-07-19 - 30.00 CAD" in rendered


def test_render_installment_projections():
    card = _make_card()
    plan = _make_plan(first_installment_date=date(2026, 6, 7), installment_count=4)
    installment = generate_installments(plan)[0]
    statement_cycle = map_statement_cycle(card, installment)
    due_date = map_due_date(card, statement_cycle)
    projection = build_installment_projection(plan, card, installment, statement_cycle, due_date)

    rendered = render_installment_projections([projection])

    assert "Installment Projections" in rendered
    assert "2026-06-07" in rendered
    assert "30.00 CAD" in rendered
    assert "Tangerine Mastercard" in rendered
    assert "2026-05-18 to 2026-06-17" in rendered
    assert "2026-07-13" in rendered
    assert "2026-07" in rendered


def test_render_cash_flow_obligations():
    card = _make_card()
    plan = _make_plan(first_installment_date=date(2026, 6, 7), installment_count=4)
    installments = generate_installments(plan)
    statement_cycles = [map_statement_cycle(card, installment) for installment in installments]
    due_dates = [map_due_date(card, statement_cycle) for statement_cycle in statement_cycles]
    obligations = aggregate_cash_flow(installments, due_dates)

    rendered = render_cash_flow_obligations(obligations)

    assert "Cash Flow Obligations" in rendered
    assert "2026-07-13 | card_tangerine_mastercard | 2026-07 | 30.00 CAD" in rendered
    assert "2026-08-13 | card_tangerine_mastercard | 2026-08 | 60.00 CAD" in rendered


def test_reporting_output_is_deterministic():
    card = _make_card()
    plan = _make_plan(first_installment_date=date(2026, 6, 7), installment_count=1)
    installment = generate_installments(plan)[0]
    statement_cycle = map_statement_cycle(card, installment)
    due_date = map_due_date(card, statement_cycle)
    projection = build_installment_projection(plan, card, installment, statement_cycle, due_date)

    first = render_installment_schedule([installment])
    second = render_installment_schedule([installment])
    projection_first = render_installment_projections([projection])
    projection_second = render_installment_projections([projection])

    assert first == second
    assert projection_first == projection_second
