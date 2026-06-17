from __future__ import annotations

import io
import json
from pathlib import Path

import pytest

from bnpl_cashflow import cli


def _valid_payload() -> dict[str, object]:
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


def test_successful_run_with_json_file_input(tmp_path: Path):
    input_file = tmp_path / "payload.json"
    input_file.write_text(json.dumps(_valid_payload()), encoding="utf-8")
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = cli.main([str(input_file)], stdout=stdout, stderr=stderr)

    assert exit_code == 0
    assert stderr.getvalue() == ""
    rendered = stdout.getvalue()
    assert "BNPL Cash Flow Report" in rendered
    assert "Installment Schedule" in rendered
    assert "Installment Projections" in rendered
    assert "Cash Flow Obligations" in rendered
    assert "2026-07-13 | card_tangerine_mastercard | 2026-07 | 30.00 CAD" in rendered


def test_successful_run_with_stdin_input():
    stdin = io.StringIO(json.dumps(_valid_payload()))
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = cli.main([], stdin=stdin, stdout=stdout, stderr=stderr)

    assert exit_code == 0
    assert stderr.getvalue() == ""
    assert "Tangerine Mastercard" in stdout.getvalue()


def test_validation_failure_returns_non_zero(monkeypatch):
    stdin = io.StringIO(
        json.dumps(
            {
                "credit_cards": [],
                "bnpl_plans": [],
            }
        )
    )
    stdout = io.StringIO()
    stderr = io.StringIO()

    monkeypatch.setattr(cli, "run_application", lambda *_args, **_kwargs: pytest.fail("application should not run when validation fails"))

    exit_code = cli.main([], stdin=stdin, stdout=stdout, stderr=stderr)

    assert exit_code != 0
    assert stdout.getvalue() == ""
    assert "Validation failed:" in stderr.getvalue()
    assert "credit_cards" in stderr.getvalue()
    assert "bnpl_plans" in stderr.getvalue()


def test_malformed_json_returns_non_zero():
    stdin = io.StringIO("{not-json")
    stdout = io.StringIO()
    stderr = io.StringIO()

    exit_code = cli.main([], stdin=stdin, stdout=stdout, stderr=stderr)

    assert exit_code != 0
    assert stdout.getvalue() == ""
    assert "Invalid JSON input." in stderr.getvalue()


def test_runtime_failure_returns_non_zero(monkeypatch):
    stdin = io.StringIO(json.dumps(_valid_payload()))
    stdout = io.StringIO()
    stderr = io.StringIO()

    monkeypatch.setattr(cli, "run_application", lambda *_args, **_kwargs: (_ for _ in ()).throw(RuntimeError("boom")))

    exit_code = cli.main([], stdin=stdin, stdout=stdout, stderr=stderr)

    assert exit_code != 0
    assert stdout.getvalue() == ""
    assert "An unexpected runtime error occurred." in stderr.getvalue()
    assert "boom" not in stderr.getvalue()


def test_cli_does_not_call_rules_functions_directly(monkeypatch):
    import bnpl_cashflow.rules as rules_module

    stdin = io.StringIO(json.dumps(_valid_payload()))
    stdout = io.StringIO()
    stderr = io.StringIO()

    monkeypatch.setattr(cli, "run_application", lambda *_args, **_kwargs: object())
    monkeypatch.setattr(cli, "render_application_report", lambda _result: "REPORT_FROM_APP_LAYER")
    monkeypatch.setattr(
        rules_module,
        "generate_installments",
        lambda *_args, **_kwargs: pytest.fail("cli should not call rules directly"),
    )
    monkeypatch.setattr(
        rules_module,
        "map_statement_cycle",
        lambda *_args, **_kwargs: pytest.fail("cli should not call rules directly"),
    )
    monkeypatch.setattr(
        rules_module,
        "map_due_date",
        lambda *_args, **_kwargs: pytest.fail("cli should not call rules directly"),
    )
    monkeypatch.setattr(
        rules_module,
        "aggregate_cash_flow",
        lambda *_args, **_kwargs: pytest.fail("cli should not call rules directly"),
    )

    exit_code = cli.main([], stdin=stdin, stdout=stdout, stderr=stderr)

    assert exit_code == 0
    assert stdout.getvalue().strip() == "REPORT_FROM_APP_LAYER"


def test_cli_does_not_duplicate_reporting_logic(monkeypatch):
    stdin = io.StringIO(json.dumps(_valid_payload()))
    stdout = io.StringIO()
    stderr = io.StringIO()

    monkeypatch.setattr(cli, "render_application_report", lambda result: "REPORT_FROM_ADAPTER")

    exit_code = cli.main([], stdin=stdin, stdout=stdout, stderr=stderr)

    assert exit_code == 0
    assert stdout.getvalue().strip() == "REPORT_FROM_ADAPTER"
    assert stderr.getvalue() == ""


def test_output_is_deterministic_enough_for_testing(tmp_path: Path):
    input_file = tmp_path / "payload.json"
    input_file.write_text(json.dumps(_valid_payload()), encoding="utf-8")

    first_stdout = io.StringIO()
    first_stderr = io.StringIO()
    second_stdout = io.StringIO()
    second_stderr = io.StringIO()

    first_exit = cli.main([str(input_file)], stdout=first_stdout, stderr=first_stderr)
    second_exit = cli.main([str(input_file)], stdout=second_stdout, stderr=second_stderr)

    assert first_exit == 0
    assert second_exit == 0
    assert first_stdout.getvalue() == second_stdout.getvalue()
    assert first_stderr.getvalue() == second_stderr.getvalue()
