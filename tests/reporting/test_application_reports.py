from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from bnpl_cashflow.application import run_application
from bnpl_cashflow.input.validation import BNPLPlanInput, CreditCardInput, ValidatedPayload
from bnpl_cashflow.reporting import render_application_report


def _single_payload() -> ValidatedPayload:
    return ValidatedPayload(
        credit_cards=(
            CreditCardInput(
                id="card_tangerine_mastercard",
                name="Tangerine Mastercard",
                statement_end_day=17,
                payment_due_day=13,
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


def _multi_payload() -> ValidatedPayload:
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
        output_options={"include_installment_schedule": True, "include_installment_projections": True, "include_cash_flow_obligations": True},
    )


def test_rendering_single_card_single_plan_application_result():
    result = run_application(_single_payload())

    rendered = render_application_report(result)

    assert rendered.startswith("BNPL Cash Flow Report")
    assert "Installment Schedule" in rendered
    assert "Installment Projections" in rendered
    assert "Cash Flow Obligations" in rendered
    assert "2026-06-07" in rendered
    assert "2026-07-13" in rendered


def test_rendering_multiple_cards_multiple_plans_is_deterministic():
    first = render_application_report(run_application(_multi_payload()))
    second = render_application_report(run_application(_multi_payload()))

    assert first == second
    assert "plan_tangerine_shared_date" not in first
    assert "Installment Schedule" in first
    assert "Installment Projections" in first
    assert "Cash Flow Obligations" in first


def test_output_options_affect_presentation_only():
    result = run_application(_single_payload())
    hidden = type(result)(
        credit_cards=result.credit_cards,
        bnpl_plans=result.bnpl_plans,
        plan_results=result.plan_results,
        installments=result.installments,
        statement_cycles=result.statement_cycles,
        due_dates=result.due_dates,
        cash_flow_obligations=result.cash_flow_obligations,
        projections=result.projections,
        output_options={
            "include_installment_schedule": False,
            "include_installment_projections": True,
            "include_cash_flow_obligations": False,
        },
    )

    rendered = render_application_report(hidden)

    assert "Installment Schedule" not in rendered
    assert "Installment Projections" in rendered
    assert "Cash Flow Obligations" not in rendered


def test_reporting_does_not_parse_json_or_validate_contract(monkeypatch):
    import bnpl_cashflow.input.json_parser as json_parser_module
    import bnpl_cashflow.input.validation as validation_module

    monkeypatch.setattr(
        json_parser_module,
        "parse_json_payload",
        lambda *_args, **_kwargs: pytest.fail("reporting should not parse JSON"),
    )
    monkeypatch.setattr(
        validation_module,
        "validate_payload",
        lambda *_args, **_kwargs: pytest.fail("reporting should not validate JSON"),
    )

    rendered = render_application_report(run_application(_single_payload()))

    assert rendered.startswith("BNPL Cash Flow Report")


def test_reporting_does_not_call_rules_for_calculations(monkeypatch):
    import bnpl_cashflow.rules as rules_module

    monkeypatch.setattr(
        rules_module,
        "generate_installments",
        lambda *_args, **_kwargs: pytest.fail("reporting should not generate installments"),
    )
    monkeypatch.setattr(
        rules_module,
        "map_statement_cycle",
        lambda *_args, **_kwargs: pytest.fail("reporting should not map statement cycles"),
    )
    monkeypatch.setattr(
        rules_module,
        "map_due_date",
        lambda *_args, **_kwargs: pytest.fail("reporting should not map due dates"),
    )
    monkeypatch.setattr(
        rules_module,
        "aggregate_cash_flow",
        lambda *_args, **_kwargs: pytest.fail("reporting should not aggregate cash flow"),
    )

    rendered = render_application_report(run_application(_single_payload()))

    assert "Cash Flow Obligations" in rendered


def test_reporting_preserves_existing_mvp1_report_behavior():
    result = run_application(_single_payload())
    rendered = render_application_report(result)

    assert "2026-07-13 | card_tangerine_mastercard | 2026-07 | 30.00 CAD" in rendered
    assert "2026-08-13 | card_tangerine_mastercard | 2026-08 | 60.00 CAD" in rendered
    assert "4. 2026-07-19 - 30.00 CAD" in rendered

