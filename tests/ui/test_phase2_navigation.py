from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_phase2_navigation_moves_from_welcome_to_placeholder_step():
    app_path = Path(__file__).resolve().parents[2] / "src" / "bnpl_cashflow" / "ui" / "app.py"

    at = AppTest.from_file(str(app_path))
    at.run()

    assert any(button.label == "Get started" for button in at.button)

    at.button[0].click()
    at.run()

    assert any(button.label == "Back" for button in at.button)
