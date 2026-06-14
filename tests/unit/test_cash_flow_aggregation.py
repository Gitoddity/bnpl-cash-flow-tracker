from __future__ import annotations

from datetime import date
from decimal import Decimal

from bnpl_cashflow.domain import BNPLPlan, CreditCard, InstallmentFrequency, CashFlowObligation
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


def _pipeline(card: CreditCard, plan: BNPLPlan):
    installments = generate_installments(plan)
    statement_cycles = [map_statement_cycle(card, installment) for installment in installments]
    due_dates = [map_due_date(card, cycle) for cycle in statement_cycles]
    obligations = aggregate_cash_flow(installments, due_dates)
    return installments, statement_cycles, due_dates, obligations


def test_tc_001_aggregated_cash_flow():
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

    installments, statement_cycles, due_dates, obligations = _pipeline(card, plan)

    assert len(obligations) == 3
    assert [(item.due_date, item.credit_card_id, item.cash_flow_period, item.total_amount) for item in obligations] == [
        (date(2026, 7, 13), card.id, "2026-07", Decimal("30.00")),
        (date(2026, 8, 13), card.id, "2026-08", Decimal("60.00")),
        (date(2026, 9, 13), card.id, "2026-09", Decimal("30.00")),
    ]
    assert sum((obligation.total_amount for obligation in obligations), Decimal("0.00")) == Decimal("120.00")
    assert all(isinstance(item, CashFlowObligation) for item in obligations)
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
    assert sum((item.installment_amount for item in installments), Decimal("0.00")) == Decimal("120.00")


def test_tc_007_rounding_aggregation_reconciliation():
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

    installments, _statement_cycles, _due_dates, obligations = _pipeline(card, plan)

    assert [obligation.total_amount for obligation in obligations] == [Decimal("33.33"), Decimal("66.67")]
    assert sum((obligation.total_amount for obligation in obligations), Decimal("0.00")) == Decimal("100.00")
    assert sum((item.installment_amount for item in installments), Decimal("0.00")) == Decimal("100.00")


def test_tc_008_multiple_bnpl_plans_same_card_same_due_date():
    card = _make_card("card_tangerine_mastercard", "Tangerine Mastercard", 17, 13)
    plan_one = _make_plan(
        plan_id="plan_klarna_keyboard",
        provider_name="Klarna",
        plan_name="Keyboard",
        purchase_amount=Decimal("80.00"),
        purchase_date=date(2026, 6, 21),
        first_installment_date=date(2026, 6, 21),
        installment_count=1,
        credit_card_id=card.id,
    )
    plan_two = _make_plan(
        plan_id="plan_paypal_mouse",
        provider_name="PayPal",
        plan_name="Mouse",
        purchase_amount=Decimal("50.00"),
        purchase_date=date(2026, 7, 5),
        first_installment_date=date(2026, 7, 5),
        installment_count=1,
        credit_card_id=card.id,
    )

    installments_one, _cycles_one, due_dates_one, _obligations_one = _pipeline(card, plan_one)
    installments_two, _cycles_two, due_dates_two, _obligations_two = _pipeline(card, plan_two)

    obligations = aggregate_cash_flow(installments_one + installments_two, due_dates_one + due_dates_two)

    assert len(obligations) == 1
    assert obligations[0].due_date == date(2026, 8, 13)
    assert obligations[0].credit_card_id == card.id
    assert obligations[0].cash_flow_period == "2026-08"
    assert obligations[0].total_amount == Decimal("130.00")
    assert sum((obligation.total_amount for obligation in obligations), Decimal("0.00")) == Decimal("130.00")


def test_tc_009_multiple_cards_with_different_due_dates():
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

    installments_tangerine, _cycles_tangerine, due_dates_tangerine, _obligations_tangerine = _pipeline(tangerine, plan_tangerine)
    installments_rbc, _cycles_rbc, due_dates_rbc, _obligations_rbc = _pipeline(rbc, plan_rbc)

    obligations = aggregate_cash_flow(installments_tangerine + installments_rbc, due_dates_tangerine + due_dates_rbc)

    assert [(item.due_date, item.credit_card_id, item.cash_flow_period, item.total_amount) for item in obligations] == [
        (date(2026, 7, 13), tangerine.id, "2026-07", Decimal("40.00")),
        (date(2026, 7, 27), rbc.id, "2026-07", Decimal("60.00")),
    ]


def test_year_rollover_cash_flow_period_derivation():
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

    installments, _cycles, due_dates, obligations = _pipeline(card, plan)

    assert [item.cash_flow_period for item in obligations] == ["2027-01", "2027-02", "2027-03"]
    assert [item.due_date for item in obligations] == [date(2027, 1, 13), date(2027, 2, 13), date(2027, 3, 13)]
    assert sum((obligation.total_amount for obligation in obligations), Decimal("0.00")) == Decimal("120.00")
    assert sum((item.installment_amount for item in installments), Decimal("0.00")) == Decimal("120.00")
    assert [due_date.payment_due_date for due_date in due_dates] == [
        date(2027, 1, 13),
        date(2027, 2, 13),
        date(2027, 2, 13),
        date(2027, 3, 13),
    ]


def test_aggregation_key_and_total_reconciliation():
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

    installments, _cycles, due_dates, obligations = _pipeline(card, plan)

    assert all(obligation.credit_card_id == card.id for obligation in obligations)
    assert [obligation.due_date for obligation in obligations] == [date(2026, 7, 13), date(2026, 8, 13)]
    assert sum((item.installment_amount for item in installments), Decimal("0.00")) == Decimal("100.00")
    assert sum((obligation.total_amount for obligation in obligations), Decimal("0.00")) == Decimal("100.00")

