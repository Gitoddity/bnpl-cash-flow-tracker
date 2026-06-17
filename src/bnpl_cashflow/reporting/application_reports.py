from __future__ import annotations

from collections.abc import Mapping, Sequence

from bnpl_cashflow.application.models import ApplicationResult
from bnpl_cashflow.domain import CashFlowObligation, Installment, InstallmentProjection
from bnpl_cashflow.reporting.renderers import (
    render_cash_flow_obligations,
    render_installment_projections,
    render_installment_schedule,
)


def render_application_report(result: ApplicationResult) -> str:
    if not isinstance(result, ApplicationResult):
        raise TypeError("result must be an ApplicationResult instance")

    sections = ["BNPL Cash Flow Report"]
    sections.extend(_build_report_sections(result))
    return "\n\n".join(sections)


def _build_report_sections(result: ApplicationResult) -> list[str]:
    sections: list[str] = []
    if _is_enabled(result.output_options, "include_installment_schedule", True):
        sections.append(render_installment_schedule(result.installments))
    if _is_enabled(result.output_options, "include_installment_projections", True):
        sections.append(render_installment_projections(result.projections))
    if _is_enabled(result.output_options, "include_cash_flow_obligations", True):
        sections.append(render_cash_flow_obligations(result.cash_flow_obligations))
    return sections


def _is_enabled(options: Mapping[str, object], key: str, default: bool) -> bool:
    value = options.get(key, default)
    if isinstance(value, bool):
        return value
    return default

