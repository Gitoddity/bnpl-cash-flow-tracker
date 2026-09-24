from __future__ import annotations

from pathlib import Path

from streamlit.testing.v1 import AppTest


APP_PATH = Path(__file__).resolve().parents[2] / "src" / "bnpl_cashflow" / "ui" / "app.py"


def _widget(elements, label):
    return next(element for element in elements if element.label == label)


def test_user_can_add_card_plan_and_calculate():
    at = AppTest.from_file(str(APP_PATH)).run(timeout=10)
    _widget(at.button, "Get started").click().run(timeout=10)

    at.segmented_control[0].set_value("Profiles").run(timeout=10)
    _widget(at.text_input, "Profile name").set_value("Personal")
    _widget(at.button, "Add profile").click().run(timeout=10)
    at.segmented_control[0].set_value("Cards").run(timeout=10)

    _widget(at.text_input, "Card name").set_value("Tangerine")
    _widget(at.number_input, "Current balance").set_value(100.00)
    _widget(at.number_input, "Statement closing day").set_value(13)
    _widget(at.number_input, "Payment due day").set_value(13)
    _widget(at.button, "Add card").click().run(timeout=10)

    assert any("Tangerine" in item.value for item in at.markdown)

    # Returning to the welcome page must not discard the current session entries.
    _widget(at.button, "Back").click().run(timeout=10)
    _widget(at.button, "Get started").click().run(timeout=10)
    at.segmented_control[0].set_value("Cards").run(timeout=10)
    assert any("Tangerine" in item.value for item in at.markdown)

    at.segmented_control[0].set_value("BNPL plans").run(timeout=10)
    _widget(at.text_input, "Provider").set_value("PayPal")
    _widget(at.text_input, "Purchase or plan name").set_value("Test purchase")
    _widget(at.number_input, "Original purchase amount").set_value(120.00)
    _widget(at.button, "Add BNPL plan").click().run(timeout=10)

    assert any("Test purchase" in item.value for item in at.markdown)

    at.segmented_control[0].set_value("Review & calculate").run(timeout=10)
    _widget(at.button, "Calculate cash flow — Personal").click().run(timeout=10)

    assert any("Cash flow obligations — Personal" in item.value for item in at.header)
    assert any("Calculated as of" in item.value for item in at.success)
    assert len(at.dataframe) == 2
    assert at.dataframe[0].value.iloc[0]["Card"] == "Tangerine"
    assert at.dataframe[0].value.iloc[0]["Total due"] > 0
