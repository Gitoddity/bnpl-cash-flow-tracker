from __future__ import annotations

import streamlit as st

WELCOME_STEP = 0
WORKSPACE_STEP = 1


def initialize_session_state() -> None:
    st.session_state.setdefault("current_step", WELCOME_STEP)
    st.session_state.setdefault("workspace_view", "Cards")
    st.session_state.setdefault("credit_cards", [])
    st.session_state.setdefault("profiles", [])
    st.session_state.setdefault("bnpl_plans", [])
    st.session_state.setdefault("calculation_result", None)
    st.session_state.setdefault("calculation_results_by_profile", {})
    st.session_state.setdefault("next_card_number", 1)
    st.session_state.setdefault("next_plan_number", 1)
    st.session_state.setdefault("review_editor_version", 1)


def get_current_step() -> int:
    initialize_session_state()
    return int(st.session_state.current_step)


def set_current_step(step: int) -> None:
    st.session_state.current_step = step


def reset_financial_data() -> None:
    st.session_state.credit_cards = []
    st.session_state.profiles = []
    st.session_state.bnpl_plans = []
    st.session_state.calculation_result = None
    st.session_state.calculation_results_by_profile = {}
    st.session_state.next_card_number = 1
    st.session_state.next_plan_number = 1
    st.session_state.workspace_view = "Cards"
    mark_data_changed()


def reset_to_welcome() -> None:
    set_current_step(WELCOME_STEP)


def mark_data_changed() -> None:
    """Invalidate calculated output and give review widgets fresh keys."""
    st.session_state.calculation_result = None
    st.session_state.calculation_results_by_profile = {}
    st.session_state.review_editor_version = int(st.session_state.get("review_editor_version", 1)) + 1


def replace_financial_data(credit_cards: list[dict], bnpl_plans: list[dict]) -> None:
    st.session_state.credit_cards = credit_cards
    st.session_state.bnpl_plans = bnpl_plans
    st.session_state.profiles = list(dict.fromkeys(card.get("profile_name", "Default profile") for card in credit_cards))
    st.session_state.next_card_number = _next_id_number(credit_cards, "card_")
    st.session_state.next_plan_number = _next_id_number(bnpl_plans, "plan_")
    st.session_state.workspace_view = "Review & calculate"
    mark_data_changed()


def _next_id_number(items: list[dict], prefix: str) -> int:
    numbers = [int(str(item.get("id", ""))[len(prefix) :]) for item in items if str(item.get("id", "")).startswith(prefix) and str(item.get("id", ""))[len(prefix) :].isdigit()]
    return max(numbers, default=0) + 1
