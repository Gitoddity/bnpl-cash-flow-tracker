from __future__ import annotations

from collections.abc import Mapping, Sequence
from decimal import Decimal

from bnpl_cashflow.application.models import ApplicationResult
from bnpl_cashflow.domain import CashFlowObligation
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
    sections.append(_render_card_balance_summary(result))
    if _is_enabled(result.output_options, "include_installment_schedule", True):
        sections.append(render_installment_schedule(result.installments))
    if _is_enabled(result.output_options, "include_installment_projections", True):
        sections.append(render_installment_projections(result.projections))
    if _is_enabled(result.output_options, "include_cash_flow_obligations", True):
        sections.append(render_cash_flow_obligations(result.cash_flow_obligations))
    return sections


def _render_card_balance_summary(result: ApplicationResult) -> str:
    lines = ["Card Balances"]
    obligations_by_card = _group_obligations_by_card(result.cash_flow_obligations)
    default_currency = _default_currency(result.cash_flow_obligations)

    for card in result.credit_cards:
        scheduled_obligations = obligations_by_card.get(card.id, Decimal("0.00"))
        projected_balance = card.existing_balance + scheduled_obligations
        lines.append(
            f"{card.name} | Existing Balance | {card.existing_balance:.2f} {default_currency} | "
            f"BNPL Obligations | {scheduled_obligations:.2f} {default_currency} | "
            f"Projected Balance Impact | {projected_balance:.2f} {default_currency}"
        )

    return "\n".join(lines)


def _group_obligations_by_card(obligations: Sequence[CashFlowObligation]) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = {}
    for obligation in obligations:
        totals[obligation.credit_card_id] = totals.get(obligation.credit_card_id, Decimal("0.00")) + obligation.total_amount
    return totals


def _default_currency(obligations: Sequence[CashFlowObligation]) -> str:
    if not obligations:
        return ""
    return obligations[0].currency


def _is_enabled(options: Mapping[str, object], key: str, default: bool) -> bool:
    value = options.get(key, default)
    if isinstance(value, bool):
        return value
    return default
