from __future__ import annotations

from collections.abc import Mapping
from dataclasses import dataclass

from bnpl_cashflow.domain import (
    BNPLPlan,
    CashFlowObligation,
    CreditCard,
    DueDate,
    Installment,
    InstallmentProjection,
    StatementCycle,
)


@dataclass(frozen=True, slots=True)
class PlanProcessingResult:
    credit_card: CreditCard
    plan: BNPLPlan
    installments: tuple[Installment, ...]
    statement_cycles: tuple[StatementCycle, ...]
    due_dates: tuple[DueDate, ...]
    projections: tuple[InstallmentProjection, ...]


@dataclass(frozen=True, slots=True)
class ApplicationResult:
    credit_cards: tuple[CreditCard, ...]
    bnpl_plans: tuple[BNPLPlan, ...]
    plan_results: tuple[PlanProcessingResult, ...]
    installments: tuple[Installment, ...]
    statement_cycles: tuple[StatementCycle, ...]
    due_dates: tuple[DueDate, ...]
    cash_flow_obligations: tuple[CashFlowObligation, ...]
    projections: tuple[InstallmentProjection, ...]
    output_options: Mapping[str, object]

