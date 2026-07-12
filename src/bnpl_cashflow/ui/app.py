from __future__ import annotations

import streamlit as st

from bnpl_cashflow.ui.screens import render_welcome_screen


def main() -> None:
    st.set_page_config(page_title="BNPL Cash Flow Tracker", page_icon="💳", layout="centered")
    render_welcome_screen()


if __name__ == "__main__":
    main()
