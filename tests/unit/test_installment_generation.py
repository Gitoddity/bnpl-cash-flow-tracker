from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from bnpl_cashflow.domain import BNPLPlan, InstallmentFrequency
from bnpl_cashflow.rules import generate_installments


def _make_klarna_plan(*, purchase_amount: Decimal, installment_count: int, first_installment_date: date) -> BNPLPlan:
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


def test_standard_klarna_pay_in_4_installment_generation():
    plan = _make_klarna_plan(
        purchase_amount=Decimal("120.00"),
        installment_count=4,
        first_installment_date=date(2026, 6, 7),
    )

    installments = generate_installments(plan)

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
    assert sum((item.installment_amount for item in installments), Decimal("0.00")) == Decimal("120.00")


def test_tc_001_installment_generation_expectations():
    plan = _make_klarna_plan(
        purchase_amount=Decimal("120.00"),
        installment_count=4,
        first_installment_date=date(2026, 6, 7),
    )

    installments = generate_installments(plan)

    assert len(installments) == 4
    assert installments[0].installment_number == 1
    assert installments[-1].installment_number == 4
    assert installments[0].installment_date == date(2026, 6, 7)
    assert installments[1].installment_date == date(2026, 6, 21)
    assert installments[2].installment_date == date(2026, 7, 5)
    assert installments[3].installment_date == date(2026, 7, 19)
    assert [item.installment_amount for item in installments] == [
        Decimal("30.00"),
        Decimal("30.00"),
        Decimal("30.00"),
        Decimal("30.00"),
    ]


def test_tc_007_rounding_behavior():
    plan = _make_klarna_plan(
        purchase_amount=Decimal("100.00"),
        installment_count=3,
        first_installment_date=date(2026, 6, 7),
    )

    installments = generate_installments(plan)

    assert [item.installment_amount for item in installments] == [
        Decimal("33.33"),
        Decimal("33.33"),
        Decimal("33.34"),
    ]
    assert sum((item.installment_amount for item in installments), Decimal("0.00")) == Decimal("100.00")


def test_exact_installment_count_generation():
    plan = _make_klarna_plan(
        purchase_amount=Decimal("120.00"),
        installment_count=4,
        first_installment_date=date(2026, 6, 7),
    )

    installments = generate_installments(plan)

    assert len(installments) == plan.installment_count
    assert [item.installment_number for item in installments] == [1, 2, 3, 4]


def test_biweekly_date_increments():
    plan = _make_klarna_plan(
        purchase_amount=Decimal("120.00"),
        installment_count=4,
        first_installment_date=date(2026, 12, 10),
    )

    installments = generate_installments(plan)

    assert [item.installment_date for item in installments] == [
        date(2026, 12, 10),
        date(2026, 12, 24),
        date(2027, 1, 7),
        date(2027, 1, 21),
    ]
    assert installments[1].installment_date - installments[0].installment_date == installments[2].installment_date - installments[1].installment_date
    assert installments[2].installment_date - installments[1].installment_date == installments[3].installment_date - installments[2].installment_date


def test_final_installment_remainder_handling():
    plan = _make_klarna_plan(
        purchase_amount=Decimal("100.00"),
        installment_count=3,
        first_installment_date=date(2026, 6, 7),
    )

    installments = generate_installments(plan)

    assert installments[-1].installment_amount == Decimal("33.34")
    assert installments[0].installment_amount + installments[1].installment_amount + installments[2].installment_amount == Decimal("100.00")


@pytest.mark.parametrize(
    "purchase_amount, installment_count",
    [
        (Decimal("120.00"), 4),
        (Decimal("100.00"), 3),
        (Decimal("99.99"), 6),
    ],
)
def test_total_reconciliation(purchase_amount: Decimal, installment_count: int):
    plan = _make_klarna_plan(
        purchase_amount=purchase_amount,
        installment_count=installment_count,
        first_installment_date=date(2026, 6, 7),
    )

    installments = generate_installments(plan)

    assert sum((item.installment_amount for item in installments), Decimal("0.00")) == purchase_amount


def test_unsupported_frequency_raises():
    plan = BNPLPlan(
        id="plan",
        provider_name="Klarna",
        plan_name="Unsupported",
        purchase_amount=Decimal("120.00"),
        currency="CAD",
        purchase_date=date(2026, 6, 7),
        first_installment_date=date(2026, 6, 7),
        installment_count=4,
        installment_frequency=InstallmentFrequency.MONTHLY,
        credit_card_id="card_tangerine_mastercard",
    )

    with pytest.raises(ValueError):
        generate_installments(plan)

