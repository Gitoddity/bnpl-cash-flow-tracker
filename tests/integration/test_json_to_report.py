from __future__ import annotations

import io
import json
from pathlib import Path

from bnpl_cashflow import cli


def _payload_t001() -> dict[str, object]:
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


def _payload_uneven_rounding() -> dict[str, object]:
    payload = _payload_t001()
    payload["bnpl_plans"][0]["purchase_amount"] = "100.00"
    payload["bnpl_plans"][0]["installment_count"] = 3
    return payload


def _payload_year_rollover() -> dict[str, object]:
    payload = _payload_t001()
    payload["bnpl_plans"][0]["purchase_amount"] = "120.00"
    payload["bnpl_plans"][0]["purchase_date"] = "2026-12-10"
    payload["bnpl_plans"][0]["first_installment_date"] = "2026-12-10"
    return payload


def _payload_leap_year() -> dict[str, object]:
    payload = _payload_t001()
    payload["bnpl_plans"][0]["purchase_date"] = "2028-02-15"
    payload["bnpl_plans"][0]["first_installment_date"] = "2028-02-15"
    return payload


def _run_cli_with_payload(payload: dict[str, object], *, use_file: bool) -> tuple[int, str, str]:
    stdout = io.StringIO()
    stderr = io.StringIO()
    serialized = json.dumps(payload)

    if use_file:
        from tempfile import NamedTemporaryFile

        with NamedTemporaryFile("w", suffix=".json", delete=False, encoding="utf-8") as handle:
            handle.write(serialized)
            file_path = handle.name
        try:
            exit_code = cli.main([file_path], stdout=stdout, stderr=stderr)
        finally:
            Path(file_path).unlink(missing_ok=True)
    else:
        stdin = io.StringIO(serialized)
        exit_code = cli.main([], stdin=stdin, stdout=stdout, stderr=stderr)

    return exit_code, stdout.getvalue(), stderr.getvalue()


def test_json_to_report_t001_file_and_stdin_are_deterministic():
    file_exit, file_stdout, file_stderr = _run_cli_with_payload(_payload_t001(), use_file=True)
    stdin_exit, stdin_stdout, stdin_stderr = _run_cli_with_payload(_payload_t001(), use_file=False)

    assert file_exit == 0
    assert stdin_exit == 0
    assert file_stderr == ""
    assert stdin_stderr == ""
    assert file_stdout == stdin_stdout
    assert "BNPL Cash Flow Report" in file_stdout
    assert "Installment Schedule" in file_stdout
    assert "Installment Projections" in file_stdout
    assert "Cash Flow Obligations" in file_stdout
    assert "2026-07-13 | card_tangerine_mastercard | 2026-07 | 30.00 CAD" in file_stdout
    assert "2026-08-13 | card_tangerine_mastercard | 2026-08 | 60.00 CAD" in file_stdout
    assert "2026-09-13 | card_tangerine_mastercard | 2026-09 | 30.00 CAD" in file_stdout


def test_json_to_report_uneven_rounding_preserves_approved_behavior():
    exit_code, stdout, stderr = _run_cli_with_payload(_payload_uneven_rounding(), use_file=False)

    assert exit_code == 0
    assert stderr == ""
    assert "33.33 CAD" in stdout
    assert "33.34 CAD" in stdout
    assert "2026-07-13 | card_tangerine_mastercard | 2026-07 | 33.33 CAD" in stdout
    assert "2026-08-13 | card_tangerine_mastercard | 2026-08 | 66.67 CAD" in stdout


def test_json_to_report_year_rollover_preserves_approved_behavior():
    exit_code, stdout, stderr = _run_cli_with_payload(_payload_year_rollover(), use_file=False)

    assert exit_code == 0
    assert stderr == ""
    assert "2027-01-13 | card_tangerine_mastercard | 2027-01 | 30.00 CAD" in stdout
    assert "2027-02-13 | card_tangerine_mastercard | 2027-02 | 60.00 CAD" in stdout
    assert "2027-03-13 | card_tangerine_mastercard | 2027-03 | 30.00 CAD" in stdout


def test_json_to_report_leap_year_preserves_approved_behavior():
    exit_code, stdout, stderr = _run_cli_with_payload(_payload_leap_year(), use_file=False)

    assert exit_code == 0
    assert stderr == ""
    assert "2028-03-13 | card_tangerine_mastercard | 2028-03 | 30.00 CAD" in stdout
    assert "2028-04-13 | card_tangerine_mastercard | 2028-04 | 60.00 CAD" in stdout
    assert "2028-05-13 | card_tangerine_mastercard | 2028-05 | 30.00 CAD" in stdout

