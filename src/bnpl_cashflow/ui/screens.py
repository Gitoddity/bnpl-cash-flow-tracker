from __future__ import annotations

import streamlit as st


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
        st.info("The guided workflow will be implemented in the next phase.")
