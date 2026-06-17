from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from bnpl_cashflow.input import InputValidationError, parse_json_payload, validate_payload


def _single_plan_payload() -> dict[str, object]:
    return {
        "credit_cards": [
            {
                "id": "card_tangerine_mastercard",
                "name": "Tangerine Mastercard",
                "statement_end_day": 17,
                "payment_due_day": 13,
            }
        ],
        "bnpl_plans": [
            {
                "id": "plan_klarna_laptop_sleeve",
                "provider_name": "Klarna",
                "plan_name": "Laptop Sleeve",
                "purchase_amount": "120.00",
                "currency": "CAD",
                "purchase_date": "2026-06-07",
                "first_installment_date": "2026-06-07",
                "installment_count": 4,
                "installment_frequency": "BIWEEKLY",
                "credit_card_id": "card_tangerine_mastercard",
            }
        ],
    }


def _multi_plan_payload() -> dict[str, object]:
    return {
        "credit_cards": [
            {
                "id": "card_tangerine_mastercard",
                "name": "Tangerine Mastercard",
                "statement_end_day": 17,
                "payment_due_day": 13,
            },
            {
                "id": "card_rbc_mastercard",
                "name": "RBC Mastercard",
                "statement_end_day": 6,
                "payment_due_day": 27,
            },
        ],
        "bnpl_plans": [
            {
                "id": "plan_tangerine_shared_date",
                "provider_name": "Klarna",
                "plan_name": "Tangerine Shared Date",
                "purchase_amount": "40.00",
                "currency": "CAD",
                "purchase_date": "2026-06-12",
                "first_installment_date": "2026-06-12",
                "installment_count": 1,
                "installment_frequency": "BIWEEKLY",
                "credit_card_id": "card_tangerine_mastercard",
            },
            {
                "id": "plan_rbc_shared_date",
                "provider_name": "PayPal",
                "plan_name": "RBC Shared Date",
                "purchase_amount": "60.00",
                "currency": "CAD",
                "purchase_date": "2026-06-12",
                "first_installment_date": "2026-06-12",
                "installment_count": 1,
                "installment_frequency": "BIWEEKLY",
                "credit_card_id": "card_rbc_mastercard",
            },
        ],
    }


def test_valid_single_card_single_plan_payload():
    payload = _single_plan_payload()

    parsed = parse_json_payload(payload)

    assert len(parsed.credit_cards) == 1
    assert len(parsed.bnpl_plans) == 1
    assert parsed.credit_cards[0].id == "card_tangerine_mastercard"
    assert parsed.bnpl_plans[0].currency == "CAD"
    assert parsed.bnpl_plans[0].purchase_amount == Decimal("120.00")
    assert parsed.bnpl_plans[0].purchase_date == date(2026, 6, 7)


def test_valid_multiple_card_multiple_plan_payload():
    parsed = validate_payload(_multi_plan_payload())

    assert [card.id for card in parsed.credit_cards] == [
        "card_tangerine_mastercard",
        "card_rbc_mastercard",
    ]
    assert [plan.id for plan in parsed.bnpl_plans] == [
        "plan_tangerine_shared_date",
        "plan_rbc_shared_date",
    ]


@pytest.mark.parametrize(
    "payload, expected_path",
    [
        ({}, "credit_cards"),
        ({"bnpl_plans": []}, "credit_cards"),
        ({"credit_cards": []}, "credit_cards"),
        ({"credit_cards": [], "bnpl_plans": []}, "credit_cards"),
    ],
)
def test_missing_top_level_arrays(payload, expected_path):
    with pytest.raises(InputValidationError) as exc_info:
        validate_payload(payload)

    assert any(issue.path == expected_path for issue in exc_info.value.issues)


def test_empty_arrays_rejected():
    with pytest.raises(InputValidationError) as exc_info:
        validate_payload({"credit_cards": [], "bnpl_plans": []})

    paths = {issue.path for issue in exc_info.value.issues}
    assert "credit_cards" in paths
    assert "bnpl_plans" in paths


def test_duplicate_card_and_plan_ids_rejected():
    payload = {
        "credit_cards": [
            {
                "id": "card_shared",
                "name": "Card One",
                "statement_end_day": 17,
                "payment_due_day": 13,
            },
            {
                "id": "card_shared",
                "name": "Card Two",
                "statement_end_day": 6,
                "payment_due_day": 27,
            },
        ],
        "bnpl_plans": [
            {
                "id": "plan_shared",
                "provider_name": "Klarna",
                "plan_name": "One",
                "purchase_amount": "40.00",
                "currency": "CAD",
                "purchase_date": "2026-06-12",
                "first_installment_date": "2026-06-12",
                "installment_count": 1,
                "installment_frequency": "BIWEEKLY",
                "credit_card_id": "card_shared",
            },
            {
                "id": "plan_shared",
                "provider_name": "PayPal",
                "plan_name": "Two",
                "purchase_amount": "60.00",
                "currency": "CAD",
                "purchase_date": "2026-06-12",
                "first_installment_date": "2026-06-12",
                "installment_count": 1,
                "installment_frequency": "BIWEEKLY",
                "credit_card_id": "card_shared",
            },
        ],
    }

    with pytest.raises(InputValidationError) as exc_info:
        validate_payload(payload)

    assert any(issue.path == "credit_cards[1].id" for issue in exc_info.value.issues)
    assert any(issue.path == "bnpl_plans[1].id" for issue in exc_info.value.issues)


@pytest.mark.parametrize(
    "field, value",
    [
        ("purchase_date", "06/07/2026"),
        ("first_installment_date", "2026/06/07"),
    ],
)
def test_invalid_date_format(field, value):
    payload = _single_plan_payload()
    payload["bnpl_plans"][0][field] = value

    with pytest.raises(InputValidationError) as exc_info:
        validate_payload(payload)

    assert any(issue.path == f"bnpl_plans[0].{field}" for issue in exc_info.value.issues)


@pytest.mark.parametrize("purchase_amount", ["abc", "0", "-10.00"])
def test_invalid_money_values(purchase_amount):
    payload = _single_plan_payload()
    payload["bnpl_plans"][0]["purchase_amount"] = purchase_amount

    with pytest.raises(InputValidationError) as exc_info:
        validate_payload(payload)

    assert any(issue.path == "bnpl_plans[0].purchase_amount" for issue in exc_info.value.issues)


def test_negative_or_zero_amount_rejected():
    payload = _single_plan_payload()
    payload["bnpl_plans"][0]["purchase_amount"] = "0.00"

    with pytest.raises(InputValidationError) as exc_info:
        validate_payload(payload)

    assert any(issue.path == "bnpl_plans[0].purchase_amount" for issue in exc_info.value.issues)


def test_unsupported_currency_rejected():
    payload = _single_plan_payload()
    payload["bnpl_plans"][0]["currency"] = "EUR"

    with pytest.raises(InputValidationError) as exc_info:
        validate_payload(payload)

    assert any(issue.path == "bnpl_plans[0].currency" for issue in exc_info.value.issues)


def test_mixed_currency_payload_rejected():
    payload = _multi_plan_payload()
    payload["bnpl_plans"][1]["currency"] = "USD"

    with pytest.raises(InputValidationError) as exc_info:
        validate_payload(payload)

    assert any(issue.path == "bnpl_plans" for issue in exc_info.value.issues)


def test_unsupported_frequency_rejected():
    payload = _single_plan_payload()
    payload["bnpl_plans"][0]["installment_frequency"] = "DAILY"

    with pytest.raises(InputValidationError) as exc_info:
        validate_payload(payload)

    assert any(issue.path == "bnpl_plans[0].installment_frequency" for issue in exc_info.value.issues)


@pytest.mark.parametrize(
    "field, value",
    [
        ("statement_end_day", 0),
        ("payment_due_day", 32),
        ("installment_count", 0),
    ],
)
def test_invalid_day_values(field, value):
    payload = _single_plan_payload()
    if field in payload["credit_cards"][0]:
        payload["credit_cards"][0][field] = value
    else:
        payload["bnpl_plans"][0][field] = value

    with pytest.raises(InputValidationError) as exc_info:
        validate_payload(payload)

    assert any(issue.path.endswith(field) for issue in exc_info.value.issues)


def test_missing_card_reference():
    payload = _single_plan_payload()
    payload["bnpl_plans"][0]["credit_card_id"] = "card_missing"

    with pytest.raises(InputValidationError) as exc_info:
        validate_payload(payload)

    assert any(issue.path == "bnpl_plans[0].credit_card_id" for issue in exc_info.value.issues)


def test_normalization_of_currency_and_frequency():
    payload = _single_plan_payload()
    payload["bnpl_plans"][0]["currency"] = " cad "
    payload["bnpl_plans"][0]["installment_frequency"] = " biweekly "

    parsed = validate_payload(payload)

    assert parsed.bnpl_plans[0].currency == "CAD"
    assert parsed.bnpl_plans[0].installment_frequency == "BIWEEKLY"


def test_no_rules_engine_functions_invoked_during_validation(monkeypatch):
    import bnpl_cashflow.rules as rules_module

    monkeypatch.setattr(
        rules_module,
        "generate_installments",
        lambda *_args, **_kwargs: pytest.fail("rules engine should not be called during validation"),
    )
    monkeypatch.setattr(
        rules_module,
        "map_statement_cycle",
        lambda *_args, **_kwargs: pytest.fail("rules engine should not be called during validation"),
    )
    monkeypatch.setattr(
        rules_module,
        "map_due_date",
        lambda *_args, **_kwargs: pytest.fail("rules engine should not be called during validation"),
    )
    monkeypatch.setattr(
        rules_module,
        "aggregate_cash_flow",
        lambda *_args, **_kwargs: pytest.fail("rules engine should not be called during validation"),
    )

    parsed = validate_payload(_single_plan_payload())

    assert parsed.credit_cards[0].id == "card_tangerine_mastercard"

