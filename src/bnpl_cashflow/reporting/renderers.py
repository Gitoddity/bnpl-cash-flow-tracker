from __future__ import annotations

from collections.abc import Sequence

from bnpl_cashflow.domain import CashFlowObligation, Installment, InstallmentProjection


def render_installment_schedule(installments: Sequence[Installment]) -> str:
    lines = ["Installment Schedule"]
    for installment in installments:
        lines.append(
            f"{installment.installment_number}. {installment.installment_date.isoformat()} - "
            f"{installment.installment_amount:.2f} {installment.currency}"
        )
    return "\n".join(lines)


def render_installment_projections(projections: Sequence[InstallmentProjection]) -> str:
    lines = ["Installment Projections"]
    for projection in projections:
        lines.append(
            f"{projection.installment_number}. {projection.installment_date.isoformat()} | "
            f"{projection.installment_amount:.2f} {projection.currency} | "
            f"{projection.credit_card_name} | "
            f"{projection.statement_cycle_start_date.isoformat()} to {projection.statement_cycle_end_date.isoformat()} | "
            f"{projection.cash_flow_due_date.isoformat()} | "
            f"{projection.cash_flow_period}"
        )
    return "\n".join(lines)


def render_cash_flow_obligations(obligations: Sequence[CashFlowObligation]) -> str:
    lines = ["Cash Flow Obligations"]
    for obligation in obligations:
        lines.append(
            f"{obligation.due_date.isoformat()} | {obligation.credit_card_id} | "
            f"{obligation.cash_flow_period} | {obligation.total_amount:.2f} {obligation.currency}"
        )
    return "\n".join(lines)


def render_statement_cycle_assignments(lines_data: Sequence[tuple[str, str]]) -> str:
    lines = ["Statement Cycle Assignments"]
    for installment_date, cycle_range in lines_data:
        lines.append(f"{installment_date} -> {cycle_range}")
    return "\n".join(lines)


def render_due_date_assignments(lines_data: Sequence[tuple[str, str]]) -> str:
    lines = ["Due Date Assignments"]
    for installment_date, due_date in lines_data:
        lines.append(f"{installment_date} -> {due_date}")
    return "\n".join(lines)

