from __future__ import annotations

import streamlit as st

from bnpl_cashflow.ui.screens import render_welcome_screen, render_workspace_screen
from bnpl_cashflow.ui.state import WELCOME_STEP, get_current_step, initialize_session_state

st.set_page_config(
    page_title="BNPL Cash Flow Tracker",
    page_icon=":material/account_balance_wallet:",
    layout="centered",
)
initialize_session_state()

if get_current_step() == WELCOME_STEP:
    render_welcome_screen()
else:
    render_workspace_screen()
