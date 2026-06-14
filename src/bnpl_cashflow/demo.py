from __future__ import annotations

import sys
from datetime import date
from decimal import Decimal
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from bnpl_cashflow.domain import BNPLPlan, CreditCard, InstallmentFrequency
from bnpl_cashflow.reporting import build_installment_projections, render_cash_flow_obligations, render_installment_projections, render_installment_schedule
from bnpl_cashflow.rules import aggregate_cash_flow, generate_installments, map_due_date, map_statement_cycle


def _build_tc001_inputs() -> tuple[CreditCard, BNPLPlan]:
    card = CreditCard(
        id="card_tangerine_mastercard",
        name="Tangerine Mastercard",
        statement_end_day=17,
        payment_due_day=13,
    )
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
        credit_card_id=card.id,
    )
    return card, plan


def run_demo() -> str:
    card, plan = _build_tc001_inputs()
    installments = generate_installments(plan)
    statement_cycles = [map_statement_cycle(card, installment) for installment in installments]
    due_dates = [map_due_date(card, statement_cycle) for statement_cycle in statement_cycles]
    obligations = aggregate_cash_flow(installments, due_dates)
    projections = build_installment_projections(plan, card, installments, statement_cycles, due_dates)

    sections = [
        "TC-001 Demo",
        f"Provider: {plan.provider_name}",
        f"Plan: {plan.plan_name}",
        f"Credit Card: {card.name}",
        render_installment_schedule(installments),
        render_installment_projections(projections),
        render_cash_flow_obligations(obligations),
    ]
    return "\n\n".join(sections)


def main() -> None:
    print(run_demo())


if __name__ == "__main__":
    main()
