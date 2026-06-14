from __future__ import annotations

from datetime import date
from decimal import Decimal

from bnpl_cashflow.domain import BNPLPlan, CreditCard, InstallmentFrequency
from bnpl_cashflow.reporting import build_installment_projections
from bnpl_cashflow.rules import aggregate_cash_flow, generate_installments, map_due_date, map_statement_cycle


def _make_card(card_id: str, name: str, statement_end_day: int, payment_due_day: int) -> CreditCard:
    return CreditCard(
        id=card_id,
        name=name,
        statement_end_day=statement_end_day,
        payment_due_day=payment_due_day,
    )


def _make_plan(
    *,
    plan_id: str,
    provider_name: str,
    plan_name: str,
    purchase_amount: Decimal,
    purchase_date: date,
    first_installment_date: date,
    installment_count: int,
    credit_card_id: str,
) -> BNPLPlan:
    return BNPLPlan(
        id=plan_id,
        provider_name=provider_name,
        plan_name=plan_name,
        purchase_amount=purchase_amount,
        currency="CAD",
        purchase_date=purchase_date,
        first_installment_date=first_installment_date,
        installment_count=installment_count,
        installment_frequency=InstallmentFrequency.BIWEEKLY,
        credit_card_id=credit_card_id,
    )


def _execute_plan(card: CreditCard, plan: BNPLPlan):
    installments = generate_installments(plan)
    statement_cycles = [map_statement_cycle(card, installment) for installment in installments]
    due_dates = [map_due_date(card, statement_cycle) for statement_cycle in statement_cycles]
    obligations = aggregate_cash_flow(installments, due_dates)
    projections = build_installment_projections(plan, card, installments, statement_cycles, due_dates)
    return installments, statement_cycles, due_dates, obligations, projections


def test_tc_001_standard_klarna_pay_in_4_using_tangerine_mastercard():
    card = _make_card("card_tangerine_mastercard", "Tangerine Mastercard", 17, 13)
    plan = _make_plan(
        plan_id="plan_klarna_laptop_sleeve",
        provider_name="Klarna",
        plan_name="Laptop Sleeve",
        purchase_amount=Decimal("120.00"),
        purchase_date=date(2026, 6, 7),
        first_installment_date=date(2026, 6, 7),
        installment_count=4,
        credit_card_id=card.id,
    )

    installments, statement_cycles, due_dates, obligations, projections = _execute_plan(card, plan)

    assert [item.installment_date for item in installments] == [
        date(2026, 6, 7),
        date(2026, 6, 21),
        date(2026, 7, 5),
        date(2026, 7, 19),
    ]
    assert [item.installment_amount for item in installments] == [
        Decimal("30.00"),
        Decimal("30.00"),
        Decimal("30.00"),
        Decimal("30.00"),
    ]
    assert [cycle.cycle_start_date for cycle in statement_cycles] == [
        date(2026, 5, 18),
        date(2026, 6, 18),
        date(2026, 6, 18),
        date(2026, 7, 18),
    ]
    assert [cycle.cycle_end_date for cycle in statement_cycles] == [
        date(2026, 6, 17),
        date(2026, 7, 17),
        date(2026, 7, 17),
        date(2026, 8, 17),
    ]
    assert [due_date.payment_due_date for due_date in due_dates] == [
        date(2026, 7, 13),
        date(2026, 8, 13),
        date(2026, 8, 13),
        date(2026, 9, 13),
    ]
    assert [(item.due_date, item.credit_card_id, item.cash_flow_period, item.total_amount) for item in obligations] == [
        (date(2026, 7, 13), card.id, "2026-07", Decimal("30.00")),
        (date(2026, 8, 13), card.id, "2026-08", Decimal("60.00")),
        (date(2026, 9, 13), card.id, "2026-09", Decimal("30.00")),
    ]
    assert [projection.cash_flow_period for projection in projections] == [
        "2026-07",
        "2026-08",
        "2026-08",
        "2026-09",
    ]
    assert sum((item.installment_amount for item in installments), Decimal("0.00")) == Decimal("120.00")
    assert sum((obligation.total_amount for obligation in obligations), Decimal("0.00")) == Decimal("120.00")


def test_tc_007_uneven_purchase_amount_rounding():
    card = _make_card("card_tangerine_mastercard", "Tangerine Mastercard", 17, 13)
    plan = _make_plan(
        plan_id="plan_uneven_rounding",
        provider_name="Klarna",
        plan_name="Uneven Rounding",
        purchase_amount=Decimal("100.00"),
        purchase_date=date(2026, 6, 7),
        first_installment_date=date(2026, 6, 7),
        installment_count=3,
        credit_card_id=card.id,
    )

    installments, _statement_cycles, due_dates, obligations, projections = _execute_plan(card, plan)

    assert [item.installment_amount for item in installments] == [
        Decimal("33.33"),
        Decimal("33.33"),
        Decimal("33.34"),
    ]
    assert [item.cash_flow_period for item in obligations] == ["2026-07", "2026-08"]
    assert [item.total_amount for item in obligations] == [Decimal("33.33"), Decimal("66.67")]
    assert [projection.cash_flow_due_date for projection in projections] == [
        date(2026, 7, 13),
        date(2026, 8, 13),
        date(2026, 8, 13),
    ]
    assert sum((item.installment_amount for item in installments), Decimal("0.00")) == Decimal("100.00")
    assert sum((obligation.total_amount for obligation in obligations), Decimal("0.00")) == Decimal("100.00")
    assert [due_date.payment_due_date for due_date in due_dates] == [
        date(2026, 7, 13),
        date(2026, 8, 13),
        date(2026, 8, 13),
    ]


def test_tc_008_multiple_bnpl_plans_same_card_same_due_date():
    card = _make_card("card_tangerine_mastercard", "Tangerine Mastercard", 17, 13)
    plan_keyboard = _make_plan(
        plan_id="plan_klarna_keyboard",
        provider_name="Klarna",
        plan_name="Keyboard",
        purchase_amount=Decimal("80.00"),
        purchase_date=date(2026, 6, 21),
        first_installment_date=date(2026, 6, 21),
        installment_count=1,
        credit_card_id=card.id,
    )
    plan_mouse = _make_plan(
        plan_id="plan_paypal_mouse",
        provider_name="PayPal",
        plan_name="Mouse",
        purchase_amount=Decimal("50.00"),
        purchase_date=date(2026, 7, 5),
        first_installment_date=date(2026, 7, 5),
        installment_count=1,
        credit_card_id=card.id,
    )

    installments_keyboard, _cycles_keyboard, due_dates_keyboard, _obligations_keyboard, _projections_keyboard = _execute_plan(card, plan_keyboard)
    installments_mouse, _cycles_mouse, due_dates_mouse, _obligations_mouse, _projections_mouse = _execute_plan(card, plan_mouse)

    obligations = aggregate_cash_flow(installments_keyboard + installments_mouse, due_dates_keyboard + due_dates_mouse)

    assert len(obligations) == 1
    assert obligations[0].due_date == date(2026, 8, 13)
    assert obligations[0].credit_card_id == card.id
    assert obligations[0].cash_flow_period == "2026-08"
    assert obligations[0].total_amount == Decimal("130.00")


def test_tc_009_multiple_cards_with_different_statement_and_due_days():
    tangerine = _make_card("card_tangerine_mastercard", "Tangerine Mastercard", 17, 13)
    rbc = _make_card("card_rbc_mastercard", "RBC Mastercard", 6, 27)

    plan_tangerine = _make_plan(
        plan_id="plan_tangerine_shared_date",
        provider_name="Klarna",
        plan_name="Tangerine Shared Date",
        purchase_amount=Decimal("40.00"),
        purchase_date=date(2026, 6, 12),
        first_installment_date=date(2026, 6, 12),
        installment_count=1,
        credit_card_id=tangerine.id,
    )
    plan_rbc = _make_plan(
        plan_id="plan_rbc_shared_date",
        provider_name="PayPal",
        plan_name="RBC Shared Date",
        purchase_amount=Decimal("60.00"),
        purchase_date=date(2026, 6, 12),
        first_installment_date=date(2026, 6, 12),
        installment_count=1,
        credit_card_id=rbc.id,
    )

    installments_tangerine, _cycles_tangerine, due_dates_tangerine, _obligations_tangerine, _projections_tangerine = _execute_plan(tangerine, plan_tangerine)
    installments_rbc, _cycles_rbc, due_dates_rbc, _obligations_rbc, _projections_rbc = _execute_plan(rbc, plan_rbc)

    obligations = aggregate_cash_flow(installments_tangerine + installments_rbc, due_dates_tangerine + due_dates_rbc)

    assert [(item.due_date, item.credit_card_id, item.cash_flow_period, item.total_amount) for item in obligations] == [
        (date(2026, 7, 13), tangerine.id, "2026-07", Decimal("40.00")),
        (date(2026, 7, 27), rbc.id, "2026-07", Decimal("60.00")),
    ]


def test_tc_010_december_to_january_year_rollover():
    card = _make_card("card_tangerine_mastercard", "Tangerine Mastercard", 17, 13)
    plan = _make_plan(
        plan_id="plan_year_rollover",
        provider_name="Klarna",
        plan_name="Year Rollover",
        purchase_amount=Decimal("120.00"),
        purchase_date=date(2026, 12, 10),
        first_installment_date=date(2026, 12, 10),
        installment_count=4,
        credit_card_id=card.id,
    )

    installments, statement_cycles, due_dates, obligations, projections = _execute_plan(card, plan)

    assert [item.installment_date for item in installments] == [
        date(2026, 12, 10),
        date(2026, 12, 24),
        date(2027, 1, 7),
        date(2027, 1, 21),
    ]
    assert [cycle.cycle_end_date for cycle in statement_cycles] == [
        date(2026, 12, 17),
        date(2027, 1, 17),
        date(2027, 1, 17),
        date(2027, 2, 17),
    ]
    assert [due_date.payment_due_date for due_date in due_dates] == [
        date(2027, 1, 13),
        date(2027, 2, 13),
        date(2027, 2, 13),
        date(2027, 3, 13),
    ]
    assert [obligation.cash_flow_period for obligation in obligations] == ["2027-01", "2027-02", "2027-03"]
    assert [projection.cash_flow_period for projection in projections] == [
        "2027-01",
        "2027-02",
        "2027-02",
        "2027-03",
    ]
    assert sum((item.installment_amount for item in installments), Decimal("0.00")) == Decimal("120.00")
    assert sum((obligation.total_amount for obligation in obligations), Decimal("0.00")) == Decimal("120.00")


def test_tc_011_leap_year_handling():
    card = _make_card("card_tangerine_mastercard", "Tangerine Mastercard", 17, 13)
    plan = _make_plan(
        plan_id="plan_klarna_leap_year_validation",
        provider_name="Klarna",
        plan_name="Leap Year Validation",
        purchase_amount=Decimal("120.00"),
        purchase_date=date(2028, 2, 15),
        first_installment_date=date(2028, 2, 15),
        installment_count=4,
        credit_card_id=card.id,
    )

    installments, statement_cycles, due_dates, obligations, projections = _execute_plan(card, plan)

    assert [item.installment_date for item in installments] == [
        date(2028, 2, 15),
        date(2028, 2, 29),
        date(2028, 3, 14),
        date(2028, 3, 28),
    ]
    assert [cycle.cycle_start_date for cycle in statement_cycles] == [
        date(2028, 1, 18),
        date(2028, 2, 18),
        date(2028, 2, 18),
        date(2028, 3, 18),
    ]
    assert [cycle.cycle_end_date for cycle in statement_cycles] == [
        date(2028, 2, 17),
        date(2028, 3, 17),
        date(2028, 3, 17),
        date(2028, 4, 17),
    ]
    assert [due_date.payment_due_date for due_date in due_dates] == [
        date(2028, 3, 13),
        date(2028, 4, 13),
        date(2028, 4, 13),
        date(2028, 5, 13),
    ]
    assert [obligation.cash_flow_period for obligation in obligations] == ["2028-03", "2028-04", "2028-05"]
    assert [projection.cash_flow_period for projection in projections] == [
        "2028-03",
        "2028-04",
        "2028-04",
        "2028-05",
    ]
    assert sum((item.installment_amount for item in installments), Decimal("0.00")) == Decimal("120.00")
    assert sum((obligation.total_amount for obligation in obligations), Decimal("0.00")) == Decimal("120.00")

