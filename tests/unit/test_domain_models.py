from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from bnpl_cashflow.domain import (
    BNPLPlan,
    CashFlowObligation,
    CreditCard,
    DueDate,
    Installment,
    InstallmentFrequency,
    InstallmentProjection,
    StatementCycle,
)


def test_installment_frequency_enum_members():
    assert InstallmentFrequency.BIWEEKLY.value == "BIWEEKLY"
    assert InstallmentFrequency.WEEKLY.value == "WEEKLY"
    assert InstallmentFrequency.MONTHLY.value == "MONTHLY"


def test_credit_card_creation():
    card = CreditCard(
        id="card_tangerine_mastercard",
        name="Tangerine Mastercard",
        statement_end_day=17,
        payment_due_day=13,
    )

    assert card.id == "card_tangerine_mastercard"
    assert card.statement_end_day == 17
    assert card.payment_due_day == 13


def test_bnpl_plan_creation():
    plan = BNPLPlan(
        id="plan_klarna_laptop_sleeve",
        provider_name="Klarna",
        plan_name="Laptop Sleeve",
        purchase_amount=Decimal("120.00"),
        currency="CAD",
        purchase_date=date(2026, 6, 7),
        first_installment_date=date(2026, 6, 7),
        installment_count=4,
        installment_frequency=InstallmentFrequency.BIWEEKLY,
        credit_card_id="card_tangerine_mastercard",
    )

    assert plan.purchase_amount == Decimal("120.00")
    assert plan.purchase_date == date(2026, 6, 7)
    assert plan.installment_frequency is InstallmentFrequency.BIWEEKLY


def test_bnpl_plan_rejects_more_than_four_installments():
    with pytest.raises(ValueError, match='installment_count must not exceed 4'):
        BNPLPlan(
            id='plan', provider_name='Klarna', plan_name='Laptop',
            purchase_amount=Decimal('120.00'), currency='CAD',
            purchase_date=date(2026, 6, 7), first_installment_date=date(2026, 6, 7),
            installment_count=5, installment_frequency=InstallmentFrequency.BIWEEKLY,
            credit_card_id='card',
        )


def test_installment_creation():
    installment = Installment(
        plan_id="plan_klarna_laptop_sleeve",
        credit_card_id="card_tangerine_mastercard",
        installment_number=1,
        installment_date=date(2026, 6, 7),
        installment_amount=Decimal("30.00"),
        currency="CAD",
    )

    assert installment.installment_number == 1
    assert installment.installment_amount == Decimal("30.00")
    assert installment.installment_date == date(2026, 6, 7)


def test_statement_cycle_creation():
    cycle = StatementCycle(
        credit_card_id="card_tangerine_mastercard",
        cycle_start_date=date(2026, 5, 18),
        cycle_end_date=date(2026, 6, 17),
    )

    assert cycle.cycle_start_date == date(2026, 5, 18)
    assert cycle.cycle_end_date == date(2026, 6, 17)


def test_due_date_creation():
    due_date = DueDate(
        credit_card_id="card_tangerine_mastercard",
        statement_cycle_end_date=date(2026, 6, 17),
        payment_due_date=date(2026, 7, 13),
    )

    assert due_date.payment_due_date == date(2026, 7, 13)


def test_cash_flow_obligation_creation():
    installment = Installment(
        plan_id="plan_klarna_laptop_sleeve",
        credit_card_id="card_tangerine_mastercard",
        installment_number=1,
        installment_date=date(2026, 6, 7),
        installment_amount=Decimal("30.00"),
        currency="CAD",
    )
    obligation = CashFlowObligation(
        due_date=date(2026, 7, 13),
        credit_card_id="card_tangerine_mastercard",
        statement_cycle_end_date=date(2026, 6, 17),
        cash_flow_year=2026,
        cash_flow_month=7,
        cash_flow_period="2026-07",
        currency="CAD",
        total_amount=Decimal("30.00"),
        installments=(installment,),
    )

    assert obligation.total_amount == Decimal("30.00")
    assert obligation.installments == (installment,)


def test_installment_projection_creation():
    projection = InstallmentProjection(
        provider_name="Klarna",
        plan_name="Laptop Sleeve",
        installment_number=1,
        installment_date=date(2026, 6, 7),
        installment_amount=Decimal("30.00"),
        currency="CAD",
        credit_card_name="Tangerine Mastercard",
        statement_cycle_start_date=date(2026, 5, 18),
        statement_cycle_end_date=date(2026, 6, 17),
        cash_flow_due_date=date(2026, 7, 13),
        cash_flow_period="2026-07",
    )

    assert projection.credit_card_name == "Tangerine Mastercard"
    assert projection.cash_flow_period == "2026-07"


@pytest.mark.parametrize(
    "factory, expected_exception",
    [
        (
            lambda: CreditCard(
                id="",
                name="Tangerine Mastercard",
                statement_end_day=17,
                payment_due_day=13,
            ),
            ValueError,
        ),
        (
            lambda: BNPLPlan(
                id="plan",
                provider_name="Provider",
                plan_name="Plan",
                purchase_amount=Decimal("0.00"),
                currency="CAD",
                purchase_date=date(2026, 6, 7),
                first_installment_date=date(2026, 6, 7),
                installment_count=4,
                installment_frequency=InstallmentFrequency.BIWEEKLY,
                credit_card_id="card",
            ),
            ValueError,
        ),
        (
            lambda: Installment(
                plan_id="plan",
                credit_card_id="card",
                installment_number=0,
                installment_date=date(2026, 6, 7),
                installment_amount=Decimal("30.00"),
                currency="CAD",
            ),
            ValueError,
        ),
        (
            lambda: StatementCycle(
                credit_card_id="card",
                cycle_start_date=date(2026, 6, 17),
                cycle_end_date=date(2026, 6, 16),
            ),
            ValueError,
        ),
        (
            lambda: DueDate(
                credit_card_id="card",
                statement_cycle_end_date=date(2026, 6, 17),
                payment_due_date="2026-07-13",
            ),
            TypeError,
        ),
        (
            lambda: CashFlowObligation(
                due_date=date(2026, 7, 13),
                credit_card_id="card",
                statement_cycle_end_date=date(2026, 6, 17),
                cash_flow_year=2026,
                cash_flow_month=7,
                cash_flow_period="2026-07",
                currency="CAD",
                total_amount=Decimal("-1.00"),
                installments=(),
            ),
            ValueError,
        ),
    ],
)
def test_domain_validation_errors(factory, expected_exception):
    with pytest.raises(expected_exception):
        factory()


def test_decimal_and_date_field_handling():
    plan = BNPLPlan(
        id="plan",
        provider_name="Provider",
        plan_name="Plan",
        purchase_amount=Decimal("100.00"),
        currency="CAD",
        purchase_date=date(2026, 1, 2),
        first_installment_date=date(2026, 1, 16),
        installment_count=3,
        installment_frequency=InstallmentFrequency.MONTHLY,
        credit_card_id="card",
    )

    assert isinstance(plan.purchase_amount, Decimal)
    assert isinstance(plan.purchase_date, date)
    assert isinstance(plan.first_installment_date, date)
