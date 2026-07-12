from __future__ import annotations

from bnpl_cashflow.application.models import ApplicationResult, PlanProcessingResult
from bnpl_cashflow.domain import BNPLPlan, CreditCard, InstallmentFrequency
from bnpl_cashflow.input.validation import BNPLPlanInput, CreditCardInput, ValidatedPayload
from bnpl_cashflow.reporting import build_installment_projections
from bnpl_cashflow.rules import aggregate_cash_flow, generate_installments, map_due_date, map_statement_cycle


class ApplicationService:
    def run(self, payload: ValidatedPayload) -> ApplicationResult:
        if not isinstance(payload, ValidatedPayload):
            raise TypeError("payload must be a ValidatedPayload instance")

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

            plan_installments = tuple(generate_installments(plan))
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

        cash_flow_obligations = tuple(aggregate_cash_flow(installments, due_dates))

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
        )


def run_application(payload: ValidatedPayload) -> ApplicationResult:
    return ApplicationService().run(payload)


def _build_credit_card(card_input: CreditCardInput) -> CreditCard:
    return CreditCard(
        id=card_input.id,
        name=card_input.name,
        statement_end_day=card_input.statement_end_day,
        payment_due_day=card_input.payment_due_day,
        existing_balance=card_input.existing_balance,
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
    )
