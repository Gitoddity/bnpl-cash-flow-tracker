from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from bnpl_cashflow.application.services import _outstanding_installments
from bnpl_cashflow.domain import BNPLPlan, InstallmentFrequency
from bnpl_cashflow.rules import generate_installments


def _make_plan(
    *,
    purchase_amount: Decimal = Decimal("120.00"),
    paid_installment_count: int = 0,
    amount_paid: Decimal = Decimal("0.00"),
) -> BNPLPlan:
    return BNPLPlan(
        id="plan_paypal_test",
        provider_name="PayPal",
        plan_name="Test Purchase",
        purchase_amount=purchase_amount,
        currency="CAD",
        purchase_date=date(2026, 7, 1),
        first_installment_date=date(2026, 7, 2),
        installment_count=4,
        installment_frequency=InstallmentFrequency.BIWEEKLY,
        credit_card_id="card_tangerine",
        paid_installment_count=paid_installment_count,
        amount_paid=amount_paid,
    )


def test_paid_fields_default_to_no_completed_installments():
    plan = _make_plan()

    assert plan.paid_installment_count == 0
    assert plan.amount_paid == Decimal("0.00")


def test_completed_installments_are_removed_without_renumbering():
    plan = _make_plan(paid_installment_count=2, amount_paid=Decimal("60.00"))

    outstanding = _outstanding_installments(plan, tuple(generate_installments(plan)))

    assert [item.installment_number for item in outstanding] == [3, 4]
    assert [item.installment_amount for item in outstanding] == [
        Decimal("30.00"),
        Decimal("30.00"),
    ]


def test_exact_paid_amount_reconciles_paypal_rounding_difference():
    plan = _make_plan(
        purchase_amount=Decimal("229.38"),
        paid_installment_count=1,
        amount_paid=Decimal("57.35"),
    )

    outstanding = _outstanding_installments(plan, tuple(generate_installments(plan)))

    assert [item.installment_number for item in outstanding] == [2, 3, 4]
    assert outstanding[0].installment_amount == Decimal("57.34")
    assert outstanding[-1].installment_amount == Decimal("57.35")
    assert sum(
        (item.installment_amount for item in outstanding),
        Decimal("0.00"),
    ) == Decimal("172.03")


def test_fully_paid_plan_has_no_outstanding_installments():
    plan = _make_plan(
        paid_installment_count=4,
        amount_paid=Decimal("120.00"),
    )

    outstanding = _outstanding_installments(plan, tuple(generate_installments(plan)))

    assert outstanding == ()


@pytest.mark.parametrize(
    "paid_installment_count, amount_paid",
    [
        (-1, Decimal("0.00")),
        (5, Decimal("120.00")),
        (1, Decimal("-0.01")),
        (1, Decimal("120.01")),
    ],
)
def test_invalid_paid_values_are_rejected_by_domain_model(
    paid_installment_count: int,
    amount_paid: Decimal,
):
    with pytest.raises((TypeError, ValueError)):
        _make_plan(
            paid_installment_count=paid_installment_count,
            amount_paid=amount_paid,
        )
