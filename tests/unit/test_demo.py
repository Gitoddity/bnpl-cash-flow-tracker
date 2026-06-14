from __future__ import annotations

from bnpl_cashflow.demo import main, run_demo


def test_demo_runner_executes_without_error(capsys):
    main()
    captured = capsys.readouterr()

    assert captured.out


def test_demo_output_contains_tc001_fields():
    output = run_demo()

    assert "Tangerine Mastercard" in output
    assert "Klarna" in output
    assert "Laptop Sleeve" in output
    assert "2026-07-13" in output
    assert "2026-08-13" in output
    assert "2026-09-13" in output
    assert "2026-07" in output
    assert "2026-08" in output
    assert "2026-09" in output

