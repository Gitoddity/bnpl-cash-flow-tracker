from __future__ import annotations

import streamlit as st

from bnpl_cashflow.ui.state import PLACEHOLDER_STEP, set_current_step


def render_welcome_screen() -> None:
    st.title("BNPL Cash Flow Tracker")
    st.markdown(
        """
        See how Buy Now, Pay Later plans affect future credit-card statements and cash flow.
        """
    )

    st.markdown(
        """
        You'll eventually provide:

        - credit card names
        - statement closing days
        - payment due days
        - current card balances
        - BNPL plan details
        """
    )

    st.info("This app keeps information only for the active local session. It is not saved.")

    if st.button("Get started"):
        set_current_step(PLACEHOLDER_STEP)
        st.rerun()


def render_placeholder_step() -> None:
    st.title("BNPL Cash Flow Tracker")
    st.write("This is a placeholder step for the guided workflow.")

    if st.button("Back"):
        set_current_step(0)
        st.rerun()
