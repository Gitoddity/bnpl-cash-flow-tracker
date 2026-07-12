from __future__ import annotations

import streamlit as st

WELCOME_STEP = 0
PLACEHOLDER_STEP = 1


def initialize_session_state() -> None:
    if "current_step" not in st.session_state:
        st.session_state.current_step = WELCOME_STEP


def get_current_step() -> int:
    initialize_session_state()
    return int(st.session_state.current_step)


def set_current_step(step: int) -> None:
    st.session_state.current_step = step


def reset_to_welcome() -> None:
    set_current_step(WELCOME_STEP)
