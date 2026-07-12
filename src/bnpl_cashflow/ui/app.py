from __future__ import annotations

import streamlit as st

from bnpl_cashflow.ui.screens import render_placeholder_step, render_welcome_screen
from bnpl_cashflow.ui.state import PLACEHOLDER_STEP, WELCOME_STEP, get_current_step, initialize_session_state, set_current_step


def main() -> None:
    st.set_page_config(page_title="BNPL Cash Flow Tracker", page_icon="💳", layout="centered")
    initialize_session_state()

    step = get_current_step()
    if step == WELCOME_STEP:
        render_welcome_screen()
        return

    if step == PLACEHOLDER_STEP:
        render_placeholder_step()
        return


if __name__ == "__main__":
    main()
