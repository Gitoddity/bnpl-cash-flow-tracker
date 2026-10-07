from __future__ import annotations

from calendar import monthrange
from dataclasses import replace
from datetime import date, timedelta
from decimal import Decimal
from typing import Callable

from bnpl_cashflow.application.models import ApplicationResult, PlanProcessingResult
from bnpl_cashflow.domain import BNPLPlan, CashFlowObligation, CreditCard, Installment, InstallmentFrequency
from bnpl_cashflow.input.validation import BNPLPlanInput, CreditCardInput, ValidatedPayload
from bnpl_cashflow.reporting import build_installment_projections
from bnpl_cashflow.rules import aggregate_cash_flow, generate_installments, map_due_date, map_statement_cycle


class ApplicationService:
    def __init__(self, today_provider: Callable[[], date] = date.today) -> None:
        self._today_provider = today_provider

    def run(self, payload: ValidatedPayload) -> ApplicationResult:
        if not isinstance(payload, ValidatedPayload):
            raise TypeError("payload must be a ValidatedPayload instance")

        as_of_date = self._today_provider()
        if not isinstance(as_of_date, date):
            raise TypeError("today_provider must return a datetime.date instance")

        credit_cards = tuple(_build_credit_card(card_input) for card_input in payload.credit_cards)
        cards_by_id = {card.id: card for card in credit_cards}

        bnpl_plans = tuple(_build_bnpl_plan(plan_input) for plan_input in payload.bnpl_plans)
        plan_results: list[PlanProcessingResult] = []
        installments: list = []
        statement_cycles: list = []
        due_dates: list = []
        projections: list = []

        for plan_input, plan in zip(payload.bnpl_plans, bnpl_plans):
            credit_card = cards_by_id.get(plan_input.credit_card_id)
            if credit_card is None:
                raise ValueError(f"unknown credit_card_id referenced by plan {plan.id!r}")

            all_plan_installments = tuple(generate_installments(plan))
            plan_installments = _outstanding_installments(plan, all_plan_installments)
            plan_statement_cycles = tuple(map_statement_cycle(credit_card, installment) for installment in plan_installments)
            plan_due_dates = tuple(map_due_date(credit_card, statement_cycle) for statement_cycle in plan_statement_cycles)
            plan_projections = tuple(
                build_installment_projections(
                    plan,
                    credit_card,
                    list(plan_installments),
                    list(plan_statement_cycles),
                    list(plan_due_dates),
                )
            )

            plan_results.append(
                PlanProcessingResult(
                    credit_card=credit_card,
                    plan=plan,
                    installments=plan_installments,
                    statement_cycles=plan_statement_cycles,
                    due_dates=plan_due_dates,
                    projections=plan_projections,
                )
            )
            installments.extend(plan_installments)
            statement_cycles.extend(plan_statement_cycles)
            due_dates.extend(plan_due_dates)
            projections.extend(plan_projections)

        bnpl_cash_flow_obligations = tuple(aggregate_cash_flow(installments, due_dates))
        currency = bnpl_plans[0].currency if bnpl_plans else ""
        cash_flow_obligations = _include_current_balance_obligations(
            bnpl_cash_flow_obligations,
            credit_cards,
            currency,
            as_of_date,
        )

        return ApplicationResult(
            credit_cards=credit_cards,
            bnpl_plans=bnpl_plans,
            plan_results=tuple(plan_results),
            installments=tuple(installments),
            statement_cycles=tuple(statement_cycles),
            due_dates=tuple(due_dates),
            cash_flow_obligations=cash_flow_obligations,
            projections=tuple(projections),
            output_options=dict(payload.output_options),
            as_of_date=as_of_date,
        )


def run_application(payload: ValidatedPayload) -> ApplicationResult:
    return ApplicationService().run(payload)


def resolve_card_statement_dates(
    statement_end_day: int, payment_due_day: int, as_of_date: date,
) -> tuple[date, date, date, date]:
    """Pair the latest completed and upcoming closes with their scheduled dues.

    A statement closing today is upcoming until that calendar day has passed.
    Scheduled dues do not indicate whether a statement has been paid.
    """
    upcoming_close = _statement_end_on_or_after(as_of_date, statement_end_day)
    latest_close = _statement_end_before(upcoming_close, statement_end_day)
    return (latest_close, _payment_due_after(latest_close, payment_due_day),
            upcoming_close, _payment_due_after(upcoming_close, payment_due_day))


def resolve_upcoming_card_dates(
    statement_end_day: int, payment_due_day: int, as_of_date: date,
) -> tuple[date, date]:
    """Next schedule occurrences on/after as_of_date, including a prior cycle's due.

    Reuse the application's current-balance billing semantics, including clamping
    short months and requiring the payment date to be strictly after its close.
    These are scheduled dates, not evidence of a statement balance or amount owed.
    """
    next_close = _statement_end_on_or_after(as_of_date, statement_end_day)
    previous_close = _statement_end_before(next_close, statement_end_day)
    next_due = _payment_due_after(previous_close, payment_due_day)
    if next_due < as_of_date:
        next_due = _payment_due_after(next_close, payment_due_day)
    return next_close, next_due


def _build_credit_card(card_input: CreditCardInput) -> CreditCard:
    return CreditCard(
        id=card_input.id,
        name=card_input.name,
        statement_end_day=card_input.statement_end_day,
        payment_due_day=card_input.payment_due_day,
        current_balance=card_input.current_balance,
        current_balance_due_date=card_input.current_balance_due_date,
        profile_id=card_input.profile_id,
    )


def _build_bnpl_plan(plan_input: BNPLPlanInput) -> BNPLPlan:
    return BNPLPlan(
        id=plan_input.id,
        provider_name=plan_input.provider_name,
        plan_name=plan_input.plan_name,
        purchase_amount=plan_input.purchase_amount,
        currency=plan_input.currency,
        purchase_date=plan_input.purchase_date,
        first_installment_date=plan_input.first_installment_date,
        installment_count=plan_input.installment_count,
        installment_frequency=InstallmentFrequency[plan_input.installment_frequency],
        credit_card_id=plan_input.credit_card_id,
        paid_installment_count=plan_input.paid_installment_count,
        amount_paid=plan_input.amount_paid,
    )


def _outstanding_installments(
    plan: BNPLPlan,
    installments: tuple[Installment, ...],
) -> tuple[Installment, ...]:
    outstanding = installments[plan.paid_installment_count :]
    if not outstanding or plan.amount_paid == 0:
        return outstanding

    expected_remaining = plan.purchase_amount - plan.amount_paid
    actual_remaining = sum((item.installment_amount for item in outstanding), start=Decimal("0.00"))
    adjustment = expected_remaining - actual_remaining
    if adjustment == 0:
        return outstanding

    adjusted_last = replace(
        outstanding[-1],
        installment_amount=outstanding[-1].installment_amount + adjustment,
    )
    return (*outstanding[:-1], adjusted_last)


def _include_current_balance_obligations(
    obligations: tuple[CashFlowObligation, ...],
    credit_cards: tuple[CreditCard, ...],
    currency: str,
    as_of_date: date | None = None,
) -> tuple[CashFlowObligation, ...]:
    by_key = {(item.credit_card_id, item.due_date): item for item in obligations}

    for card in credit_cards:
        if card.current_balance == 0:
            continue

        balance_due_date = card.current_balance_due_date
        if balance_due_date is None and as_of_date is not None:
            statement_end = _statement_end_on_or_after(as_of_date, card.statement_end_day)
            balance_due_date = _payment_due_after(statement_end, card.payment_due_day)
        if balance_due_date is None:
            continue

        key = (card.id, balance_due_date)
        existing = by_key.get(key)
        if existing is not None:
            by_key[key] = replace(
                existing,
                total_amount=existing.total_amount + card.current_balance,
                current_balance_amount=existing.current_balance_amount + card.current_balance,
            )
            continue

        due_date = balance_due_date
        by_key[key] = CashFlowObligation(
            due_date=due_date,
            credit_card_id=card.id,
            statement_cycle_end_date=_statement_end_before(due_date, card.statement_end_day),
            statement_cycle_start_date=_previous_statement_end_before(due_date, card.statement_end_day) + timedelta(days=1),
            cash_flow_year=due_date.year,
            cash_flow_month=due_date.month,
            cash_flow_period=f"{due_date.year:04d}-{due_date.month:02d}",
            currency=currency,
            total_amount=card.current_balance,
            installments=(),
            current_balance_amount=card.current_balance,
        )

    return tuple(sorted(by_key.values(), key=lambda item: (item.due_date, item.credit_card_id)))


def _statement_end_before(due_date: date, statement_end_day: int) -> date:
    year = due_date.year
    month = due_date.month
    candidate = date(year, month, min(statement_end_day, monthrange(year, month)[1]))
    if candidate < due_date:
        return candidate

    if month == 1:
        year -= 1
        month = 12
    else:
        month -= 1
    return date(year, month, min(statement_end_day, monthrange(year, month)[1]))


def _previous_statement_end_before(due_date: date, statement_end_day: int) -> date:
    statement_end = _statement_end_before(due_date, statement_end_day)
    year = statement_end.year - (1 if statement_end.month == 1 else 0)
    month = 12 if statement_end.month == 1 else statement_end.month - 1
    return date(year, month, min(statement_end_day, monthrange(year, month)[1]))


def _statement_end_on_or_after(as_of_date: date, statement_end_day: int) -> date:
    candidate = date(
        as_of_date.year,
        as_of_date.month,
        min(statement_end_day, monthrange(as_of_date.year, as_of_date.month)[1]),
    )
    if candidate >= as_of_date:
        return candidate

    year = as_of_date.year + (1 if as_of_date.month == 12 else 0)
    month = 1 if as_of_date.month == 12 else as_of_date.month + 1
    return date(year, month, min(statement_end_day, monthrange(year, month)[1]))


def _payment_due_after(statement_end: date, payment_due_day: int) -> date:
    candidate = date(
        statement_end.year,
        statement_end.month,
        min(payment_due_day, monthrange(statement_end.year, statement_end.month)[1]),
    )
    if candidate > statement_end:
        return candidate

    year = statement_end.year + (1 if statement_end.month == 12 else 0)
    month = 1 if statement_end.month == 12 else statement_end.month + 1
    return date(year, month, min(payment_due_day, monthrange(year, month)[1]))
