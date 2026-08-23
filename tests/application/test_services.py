from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from bnpl_cashflow.application import ApplicationService, run_application
from bnpl_cashflow.application.models import ApplicationResult, PlanProcessingResult
from bnpl_cashflow.domain import BNPLPlan, CreditCard, InstallmentFrequency, StatementCycle, DueDate, Installment, InstallmentProjection, CashFlowObligation
from bnpl_cashflow.input.validation import BNPLPlanInput, CreditCardInput, ValidatedPayload


def _validated_single_payload() -> ValidatedPayload:
    return ValidatedPayload(
        credit_cards=(
            CreditCardInput(
                id="card_tangerine_mastercard",
                name="Tangerine Mastercard",
                statement_end_day=17,
                payment_due_day=13,
                current_balance=Decimal("500.00"),
            ),
        ),
        bnpl_plans=(
            BNPLPlanInput(
                id="plan_klarna_laptop_sleeve",
                provider_name="Klarna",
                plan_name="Laptop Sleeve",
                purchase_amount=Decimal("120.00"),
                currency="CAD",
                purchase_date=date(2026, 6, 7),
                first_installment_date=date(2026, 6, 7),
                installment_count=4,
                installment_frequency="BIWEEKLY",
                credit_card_id="card_tangerine_mastercard",
            ),
        ),
        output_options={},
    )


def _validated_multi_payload() -> ValidatedPayload:
    return ValidatedPayload(
        credit_cards=(
            CreditCardInput(
                id="card_tangerine_mastercard",
                name="Tangerine Mastercard",
                statement_end_day=17,
                payment_due_day=13,
            ),
            CreditCardInput(
                id="card_rbc_mastercard",
                name="RBC Mastercard",
                statement_end_day=6,
                payment_due_day=27,
            ),
        ),
        bnpl_plans=(
            BNPLPlanInput(
                id="plan_tangerine_shared_date",
                provider_name="Klarna",
                plan_name="Tangerine Shared Date",
                purchase_amount=Decimal("40.00"),
                currency="CAD",
                purchase_date=date(2026, 6, 12),
                first_installment_date=date(2026, 6, 12),
                installment_count=1,
                installment_frequency="BIWEEKLY",
                credit_card_id="card_tangerine_mastercard",
            ),
            BNPLPlanInput(
                id="plan_rbc_shared_date",
                provider_name="PayPal",
                plan_name="RBC Shared Date",
                purchase_amount=Decimal("60.00"),
                currency="CAD",
                purchase_date=date(2026, 6, 12),
                first_installment_date=date(2026, 6, 12),
                installment_count=1,
                installment_frequency="BIWEEKLY",
                credit_card_id="card_rbc_mastercard",
            ),
        ),
        output_options={"sort_output": True},
    )


def test_valid_single_card_single_plan_orchestration():
    service = ApplicationService(today_provider=lambda: date(2026, 7, 25))

    result = service.run(_validated_single_payload())

    assert isinstance(result, ApplicationResult)
    assert len(result.credit_cards) == 1
    assert len(result.bnpl_plans) == 1
    assert len(result.plan_results) == 1
    assert result.credit_cards[0].current_balance == Decimal("500.00")
    assert result.plan_results[0].credit_card.id == "card_tangerine_mastercard"
    assert result.plan_results[0].plan.id == "plan_klarna_laptop_sleeve"
    assert [item.installment_date for item in result.installments] == [
        date(2026, 6, 7),
        date(2026, 6, 21),
        date(2026, 7, 5),
        date(2026, 7, 19),
    ]
    assert [item.cash_flow_period for item in result.cash_flow_obligations] == ["2026-07", "2026-08", "2026-09"]
    assert sum((item.total_amount for item in result.cash_flow_obligations), Decimal("0.00")) == Decimal("620.00")
    assert sum(
        (item.total_amount - item.current_balance_amount for item in result.cash_flow_obligations),
        Decimal("0.00"),
    ) == Decimal("120.00")
    assert all(isinstance(item, PlanProcessingResult) for item in result.plan_results)


def test_paid_installments_are_excluded_from_future_results():
    payload = _validated_single_payload()
    paid_plan = BNPLPlanInput(
        id=payload.bnpl_plans[0].id,
        provider_name=payload.bnpl_plans[0].provider_name,
        plan_name=payload.bnpl_plans[0].plan_name,
        purchase_amount=payload.bnpl_plans[0].purchase_amount,
        currency=payload.bnpl_plans[0].currency,
        purchase_date=payload.bnpl_plans[0].purchase_date,
        first_installment_date=payload.bnpl_plans[0].first_installment_date,
        installment_count=payload.bnpl_plans[0].installment_count,
        installment_frequency=payload.bnpl_plans[0].installment_frequency,
        credit_card_id=payload.bnpl_plans[0].credit_card_id,
        paid_installment_count=2,
    )

    result = run_application(
        ValidatedPayload(
            credit_cards=payload.credit_cards,
            bnpl_plans=(paid_plan,),
            output_options={},
        )
    )

    assert [item.installment_number for item in result.installments] == [3, 4]
    assert [item.installment_number for item in result.projections] == [3, 4]
    assert sum(
        (item.total_amount - item.current_balance_amount for item in result.cash_flow_obligations),
        Decimal("0.00"),
    ) == Decimal("60.00")


def test_exact_amount_paid_reconciles_provider_rounding():
    payload = _validated_single_payload()
    paid_plan = BNPLPlanInput(
        id=payload.bnpl_plans[0].id,
        provider_name=payload.bnpl_plans[0].provider_name,
        plan_name=payload.bnpl_plans[0].plan_name,
        purchase_amount=Decimal("229.38"),
        currency=payload.bnpl_plans[0].currency,
        purchase_date=payload.bnpl_plans[0].purchase_date,
        first_installment_date=payload.bnpl_plans[0].first_installment_date,
        installment_count=4,
        installment_frequency=payload.bnpl_plans[0].installment_frequency,
        credit_card_id=payload.bnpl_plans[0].credit_card_id,
        paid_installment_count=1,
        amount_paid=Decimal("57.35"),
    )

    result = run_application(
        ValidatedPayload(
            credit_cards=payload.credit_cards,
            bnpl_plans=(paid_plan,),
            output_options={},
        )
    )

    assert result.installments[0].installment_amount == Decimal("57.34")
    assert sum((item.installment_amount for item in result.installments), Decimal("0.00")) == Decimal("172.03")


def test_valid_multiple_card_multiple_plan_orchestration():
    result = run_application(_validated_multi_payload())

    assert [card.id for card in result.credit_cards] == [
        "card_tangerine_mastercard",
        "card_rbc_mastercard",
    ]
    assert [plan.id for plan in result.bnpl_plans] == [
        "plan_tangerine_shared_date",
        "plan_rbc_shared_date",
    ]
    assert [plan_result.plan.id for plan_result in result.plan_results] == [
        "plan_tangerine_shared_date",
        "plan_rbc_shared_date",
    ]
    assert [plan_result.credit_card.id for plan_result in result.plan_results] == [
        "card_tangerine_mastercard",
        "card_rbc_mastercard",
    ]
    assert [item.due_date for item in result.cash_flow_obligations] == [
        date(2026, 7, 13),
        date(2026, 7, 27),
    ]


def test_plan_to_card_matching():
    result = run_application(_validated_multi_payload())

    tangerine_result = result.plan_results[0]
    rbc_result = result.plan_results[1]

    assert tangerine_result.credit_card.name == "Tangerine Mastercard"
    assert rbc_result.credit_card.name == "RBC Mastercard"
    assert all(plan.credit_card_id == plan_result.credit_card.id for plan, plan_result in zip(result.bnpl_plans, result.plan_results))


def test_preserves_mvp1_calculation_behavior_through_service():
    result = run_application(_validated_single_payload())

    assert [item.installment_amount for item in result.installments] == [
        Decimal("30.00"),
        Decimal("30.00"),
        Decimal("30.00"),
        Decimal("30.00"),
    ]
    assert [item.cycle_end_date for item in result.statement_cycles] == [
        date(2026, 6, 17),
        date(2026, 7, 17),
        date(2026, 7, 17),
        date(2026, 8, 17),
    ]
    assert [item.cash_flow_due_date for item in result.projections] == [
        date(2026, 7, 13),
        date(2026, 8, 13),
        date(2026, 8, 13),
        date(2026, 9, 13),
    ]


def test_current_balance_does_not_change_installment_calculations():
    baseline = run_application(
        ValidatedPayload(
            credit_cards=(
                CreditCardInput(
                    id="card_tangerine_mastercard",
                    name="Tangerine Mastercard",
                    statement_end_day=17,
                    payment_due_day=13,
                ),
            ),
            bnpl_plans=_validated_single_payload().bnpl_plans,
            output_options={},
        )
    )
    with_balance = run_application(_validated_single_payload())

    assert baseline.installments == with_balance.installments
    assert baseline.statement_cycles == with_balance.statement_cycles
    assert baseline.due_dates == with_balance.due_dates
    assert baseline.projections == with_balance.projections
    assert sum(
        (item.total_amount - item.current_balance_amount for item in with_balance.cash_flow_obligations),
        Decimal("0.00"),
    ) == sum(
        (item.total_amount for item in baseline.cash_flow_obligations),
        Decimal("0.00"),
    )


def test_dated_current_balance_becomes_cash_flow_obligation():
    payload = _validated_single_payload()
    card = CreditCardInput(
        id=payload.credit_cards[0].id,
        name=payload.credit_cards[0].name,
        statement_end_day=payload.credit_cards[0].statement_end_day,
        payment_due_day=payload.credit_cards[0].payment_due_day,
        current_balance=Decimal("500.00"),
        current_balance_due_date=date(2026, 8, 13),
    )

    result = run_application(
        ValidatedPayload(
            credit_cards=(card,),
            bnpl_plans=payload.bnpl_plans,
            output_options={},
        )
    )

    august = next(item for item in result.cash_flow_obligations if item.due_date == date(2026, 8, 13))
    assert august.total_amount == Decimal("560.00")
    assert august.current_balance_amount == Decimal("500.00")
    assert sum((item.installment_amount for item in august.installments), Decimal("0.00")) == Decimal("60.00")


def test_as_of_date_derives_current_balance_due_date():
    payload = _validated_single_payload()

    result = ApplicationService(today_provider=lambda: date(2026, 7, 25)).run(
        ValidatedPayload(
            credit_cards=payload.credit_cards,
            bnpl_plans=payload.bnpl_plans,
            output_options={},
        )
    )

    september = next(item for item in result.cash_flow_obligations if item.due_date == date(2026, 9, 13))
    assert september.current_balance_amount == Decimal("500.00")
    assert result.as_of_date == date(2026, 7, 25)


def test_deterministic_output_ordering():
    result_one = run_application(_validated_multi_payload())
    result_two = run_application(_validated_multi_payload())

    assert result_one == result_two
    assert [plan_result.plan.id for plan_result in result_one.plan_results] == [
        "plan_tangerine_shared_date",
        "plan_rbc_shared_date",
    ]
    assert [obligation.due_date for obligation in result_one.cash_flow_obligations] == [
        date(2026, 7, 13),
        date(2026, 7, 27),
    ]


def test_application_layer_does_not_duplicate_json_parsing_or_validation(monkeypatch):
    import bnpl_cashflow.input.json_parser as json_parser_module
    import bnpl_cashflow.input.validation as validation_module
    from bnpl_cashflow.application.services import ApplicationService as ServiceUnderTest

    monkeypatch.setattr(
        json_parser_module,
        "parse_json_payload",
        lambda *_args, **_kwargs: pytest.fail("application service should not parse JSON"),
    )
    monkeypatch.setattr(
        validation_module,
        "validate_payload",
        lambda *_args, **_kwargs: pytest.fail("application service should not validate JSON"),
    )

    result = ServiceUnderTest().run(_validated_single_payload())

    assert result.plan_results[0].plan.id == "plan_klarna_laptop_sleeve"


def test_application_layer_does_not_implement_business_rule_calculations(monkeypatch):
    from bnpl_cashflow.application import services as services_module
    from bnpl_cashflow.application.services import ApplicationService as ServiceUnderTest

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
    fabricated_installments = (
        Installment(
            plan_id=plan.id,
            credit_card_id=card.id,
            installment_number=1,
            installment_date=date(2099, 1, 1),
            installment_amount=Decimal("1.00"),
            currency="CAD",
        ),
    )
    fabricated_cycle = StatementCycle(
        credit_card_id=card.id,
        cycle_start_date=date(2099, 1, 1),
        cycle_end_date=date(2099, 1, 2),
    )
    fabricated_due_date = DueDate(
        credit_card_id=card.id,
        statement_cycle_end_date=fabricated_cycle.cycle_end_date,
        payment_due_date=date(2099, 2, 1),
    )
    fabricated_projection = InstallmentProjection(
        provider_name=plan.provider_name,
        plan_name=plan.plan_name,
        installment_number=1,
        installment_date=fabricated_installments[0].installment_date,
        installment_amount=fabricated_installments[0].installment_amount,
        currency="CAD",
        credit_card_name=card.name,
        statement_cycle_start_date=fabricated_cycle.cycle_start_date,
        statement_cycle_end_date=fabricated_cycle.cycle_end_date,
        cash_flow_due_date=fabricated_due_date.payment_due_date,
        cash_flow_period="2099-02",
    )
    fabricated_obligation = CashFlowObligation(
        due_date=fabricated_due_date.payment_due_date,
        credit_card_id=card.id,
        statement_cycle_end_date=fabricated_cycle.cycle_end_date,
        cash_flow_year=2099,
        cash_flow_month=2,
        cash_flow_period="2099-02",
        currency="CAD",
        total_amount=Decimal("1.00"),
        installments=fabricated_installments,
    )

    monkeypatch.setattr(services_module, "generate_installments", lambda *_args, **_kwargs: list(fabricated_installments))
    monkeypatch.setattr(services_module, "map_statement_cycle", lambda *_args, **_kwargs: fabricated_cycle)
    monkeypatch.setattr(services_module, "map_due_date", lambda *_args, **_kwargs: fabricated_due_date)
    monkeypatch.setattr(
        services_module,
        "build_installment_projections",
        lambda *_args, **_kwargs: [fabricated_projection],
    )
    monkeypatch.setattr(
        services_module,
        "aggregate_cash_flow",
        lambda installments, due_dates: [fabricated_obligation]
        if len(installments) == len(due_dates) == 1
        else pytest.fail("unexpected aggregation inputs"),
    )

    result = ServiceUnderTest().run(
        ValidatedPayload(
            credit_cards=(
                CreditCardInput(
                    id=card.id,
                    name=card.name,
                    statement_end_day=card.statement_end_day,
                    payment_due_day=card.payment_due_day,
                ),
            ),
            bnpl_plans=(
                BNPLPlanInput(
                    id=plan.id,
                    provider_name=plan.provider_name,
                    plan_name=plan.plan_name,
                    purchase_amount=plan.purchase_amount,
                    currency=plan.currency,
                    purchase_date=plan.purchase_date,
                    first_installment_date=plan.first_installment_date,
                    installment_count=plan.installment_count,
                    installment_frequency="BIWEEKLY",
                    credit_card_id=plan.credit_card_id,
                ),
            ),
            output_options={},
        )
    )

    assert result.installments == fabricated_installments
    assert result.statement_cycles == (fabricated_cycle,)
    assert result.due_dates == (fabricated_due_date,)
    assert result.projections == (fabricated_projection,)
    assert result.cash_flow_obligations == (fabricated_obligation,)
