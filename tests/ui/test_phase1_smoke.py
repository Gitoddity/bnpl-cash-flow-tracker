from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_phase1_welcome_screen_renders():
    app_path = Path(__file__).resolve().parents[2] / "src" / "bnpl_cashflow" / "ui" / "app.py"

    at = AppTest.from_file(str(app_path))
    at.run()

    assert at.title[0].value == "BNPL Cash Flow Tracker"
    assert any(button.label == "Get started" for button in at.button)
