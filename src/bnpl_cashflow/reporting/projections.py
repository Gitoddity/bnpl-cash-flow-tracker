from __future__ import annotations

from collections.abc import Mapping

from bnpl_cashflow.domain import BNPLPlan, CreditCard, DueDate, Installment, InstallmentProjection, StatementCycle


def build_installment_projection(
    plan: BNPLPlan,
    credit_card: CreditCard,
    installment: Installment,
    statement_cycle: StatementCycle,
    due_date: DueDate,
) -> InstallmentProjection:
    if not isinstance(plan, BNPLPlan):
        raise TypeError("plan must be a BNPLPlan instance")
    if not isinstance(credit_card, CreditCard):
        raise TypeError("credit_card must be a CreditCard instance")
    if not isinstance(installment, Installment):
        raise TypeError("installment must be an Installment instance")
    if not isinstance(statement_cycle, StatementCycle):
        raise TypeError("statement_cycle must be a StatementCycle instance")
    if not isinstance(due_date, DueDate):
        raise TypeError("due_date must be a DueDate instance")

    _ensure_related_objects(plan, credit_card, installment, statement_cycle, due_date)

    return InstallmentProjection(
        provider_name=plan.provider_name,
        plan_name=plan.plan_name,
        installment_number=installment.installment_number,
        installment_date=installment.installment_date,
        installment_amount=installment.installment_amount,
        currency=installment.currency,
        credit_card_name=credit_card.name,
        statement_cycle_start_date=statement_cycle.cycle_start_date,
        statement_cycle_end_date=statement_cycle.cycle_end_date,
        cash_flow_due_date=due_date.payment_due_date,
        cash_flow_period=f"{due_date.payment_due_date.year:04d}-{due_date.payment_due_date.month:02d}",
    )


def build_installment_projections(
    plan: BNPLPlan,
    credit_card: CreditCard,
    installments: list[Installment],
    statement_cycles: list[StatementCycle],
    due_dates: list[DueDate],
) -> list[InstallmentProjection]:
    if not (len(installments) == len(statement_cycles) == len(due_dates)):
        raise ValueError("installments, statement_cycles, and due_dates must have the same length")

    projections = []
    for installment, statement_cycle, due_date in zip(installments, statement_cycles, due_dates):
        projections.append(build_installment_projection(plan, credit_card, installment, statement_cycle, due_date))
    return projections


def _ensure_related_objects(
    plan: BNPLPlan,
    credit_card: CreditCard,
    installment: Installment,
    statement_cycle: StatementCycle,
    due_date: DueDate,
) -> None:
    if installment.plan_id != plan.id:
        raise ValueError("installment plan_id must match plan.id")
    if installment.credit_card_id != credit_card.id:
        raise ValueError("installment credit_card_id must match credit_card.id")
    if statement_cycle.credit_card_id != credit_card.id:
        raise ValueError("statement_cycle credit_card_id must match credit_card.id")
    if due_date.credit_card_id != credit_card.id:
        raise ValueError("due_date credit_card_id must match credit_card.id")
    if statement_cycle.cycle_end_date != due_date.statement_cycle_end_date:
        raise ValueError("statement_cycle end date must match due_date statement cycle end date")

