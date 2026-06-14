from __future__ import annotations

from datetime import timedelta
from decimal import Decimal, ROUND_DOWN

from bnpl_cashflow.domain import BNPLPlan, Installment, InstallmentFrequency


_CENTS = Decimal("0.01")
_BIWEEKLY_DAYS = 14


def generate_installments(plan: BNPLPlan) -> list[Installment]:
    if not isinstance(plan, BNPLPlan):
        raise TypeError("plan must be a BNPLPlan instance")

    if plan.installment_count <= 0:
        raise ValueError("installment_count must be greater than zero")

    if plan.purchase_amount <= Decimal("0"):
        raise ValueError("purchase_amount must be positive")

    if plan.installment_frequency is not InstallmentFrequency.BIWEEKLY:
        raise ValueError("Only BIWEEKLY installment frequency is supported in MVP 1")

    base_amount = _round_to_cents(plan.purchase_amount / plan.installment_count)
    installments: list[Installment] = []
    running_total = Decimal("0.00")

    for installment_number in range(1, plan.installment_count + 1):
        installment_date = plan.first_installment_date + timedelta(days=_BIWEEKLY_DAYS * (installment_number - 1))
        if installment_number < plan.installment_count:
            installment_amount = base_amount
            running_total += installment_amount
        else:
            installment_amount = _round_to_cents(plan.purchase_amount - running_total)

        installments.append(
            Installment(
                plan_id=plan.id,
                credit_card_id=plan.credit_card_id,
                installment_number=installment_number,
                installment_date=installment_date,
                installment_amount=installment_amount,
                currency=plan.currency,
            )
        )

    return installments


def _round_to_cents(value: Decimal) -> Decimal:
    return value.quantize(_CENTS, rounding=ROUND_DOWN)

