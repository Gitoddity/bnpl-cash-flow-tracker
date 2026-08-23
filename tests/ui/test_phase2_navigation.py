from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


def test_navigation_moves_from_welcome_to_card_entry():
    app_path = Path(__file__).resolve().parents[2] / "src" / "bnpl_cashflow" / "ui" / "app.py"

    at = AppTest.from_file(str(app_path))
    at.run()

    assert any(button.label == "Get started" for button in at.button)

    at.button[0].click()
    at.run()

    at.segmented_control[0].set_value("Profiles")
    at.run()
    assert any(button.label == "Add profile" for button in at.button)
    assert any(button.label == "Back" for button in at.button)
