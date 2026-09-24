from __future__ import annotations

from datetime import date
from decimal import Decimal

import streamlit as st

from bnpl_cashflow.input import InputValidationError
from bnpl_cashflow.ui.drafts import discard_draft, draft_exists, load_draft, save_draft
from bnpl_cashflow.ui.profiles import cards_for_profile, create_profile, delete_profile, plans_for_profile, resolve_active_profile
from bnpl_cashflow.ui.state import WORKSPACE_STEP, mark_data_changed, replace_financial_data, reset_financial_data, reset_to_welcome, set_current_step
from bnpl_cashflow.ui.workflow import calculate_from_entries


def render_welcome_screen() -> None:
    st.title("BNPL Cash Flow Tracker")
    st.write("See how BNPL plans affect upcoming card statements and payment dates.")
    profiles = st.session_state.profiles
    active_profile_id = resolve_active_profile(profiles, st.session_state.active_profile_id)
    st.session_state.active_profile_id = active_profile_id
    if len(profiles) > 1 and active_profile_id is not None:
        active_profile = next(profile for profile in profiles if profile["id"] == active_profile_id)
        st.caption(f"Active profile: {active_profile['name']}")
    if st.button("Get started", type="primary"):
        st.session_state.workspace_view = "Profiles"
        set_current_step(WORKSPACE_STEP); st.rerun()
    if draft_exists() and st.button("Load saved draft"):
        try:
            profiles, cards, plans = load_draft()
            replace_financial_data(profiles, cards, plans)
            set_current_step(WORKSPACE_STEP); st.rerun()
        except (OSError, ValueError, InputValidationError, KeyError) as exc:
            st.error(f"The saved draft could not be loaded: {exc}")


def render_workspace_screen() -> None:
    st.title("BNPL Cash Flow Tracker")
    st.caption(f"Calculations use system date: {date.today().isoformat()}")
    st.session_state.active_profile_id = resolve_active_profile(st.session_state.profiles, st.session_state.active_profile_id)
    view = st.segmented_control("Input step", ["Profiles", "Cards", "BNPL plans", "Review & calculate"], default=st.session_state.workspace_view, key="workspace_navigation", required=True, width="stretch")
    st.session_state.workspace_view = view
    if view == "Profiles": _render_profiles()
    elif not st.session_state.active_profile_id: st.warning("Create a profile first.")
    elif view == "Cards": _render_cards()
    elif view == "BNPL plans": _render_plans()
    else: _render_review()
    st.divider()
    if st.button("Back"): reset_to_welcome(); st.rerun()
    if st.button("Save draft"):
        try: save_draft(st.session_state.profiles, st.session_state.credit_cards, st.session_state.bnpl_plans); st.toast("Draft saved locally.")
        except (OSError, InputValidationError) as exc: st.error(f"Draft could not be saved: {exc}")
    if st.button("Clear session data"): reset_financial_data(); st.rerun()
    if draft_exists() and st.button("Discard saved draft"): discard_draft(); st.toast("Saved draft discarded."); st.rerun()


def _active_profile() -> dict[str, str]:
    return next(p for p in st.session_state.profiles if p["id"] == st.session_state.active_profile_id)


def _render_profiles() -> None:
    st.header("Profiles")
    if len(st.session_state.profiles) > 1 and st.session_state.active_profile_id:
        st.caption(f"Active profile: {_active_profile()['name']}")
    with st.form("add_profile", clear_on_submit=True):
        name = st.text_input("Profile name", placeholder="Personal or Household")
        submitted = st.form_submit_button("Add profile", type="primary")
    if submitted:
        try:
            profile, number = create_profile(st.session_state.profiles, st.session_state.next_profile_number, name)
            st.session_state.next_profile_number = number; st.session_state.active_profile_id = profile["id"]; st.rerun()
        except ValueError as exc: st.error(str(exc).capitalize() + ".")
    for profile in st.session_state.profiles:
        cards = cards_for_profile(st.session_state.credit_cards, profile["id"])
        plans = plans_for_profile(st.session_state.credit_cards, st.session_state.bnpl_plans, profile["id"])
        active = profile["id"] == st.session_state.active_profile_id
        st.write(f"**{profile['name']}**" + (" — Active profile" if active else "") + f" — {len(cards)} card(s) · {len(plans)} BNPL plan(s)")
        if not active and st.button("Use profile", key=f"use_{profile['id']}"): st.session_state.active_profile_id = profile["id"]; st.rerun()
        if st.button("Delete profile", key=f"delete_{profile['id']}"):
            result = delete_profile(st.session_state.profiles, st.session_state.credit_cards, st.session_state.bnpl_plans, st.session_state.active_profile_id, profile["id"])
            st.session_state.profiles, st.session_state.credit_cards, st.session_state.bnpl_plans, st.session_state.active_profile_id = result
            mark_data_changed(); st.rerun()


def _render_cards() -> None:
    profile = _active_profile(); st.header(f"Credit cards — {profile['name']}")
    with st.form("add_card", clear_on_submit=True):
        name = st.text_input("Card name"); balance = st.number_input("Current balance", min_value=0.0, step=0.01)
        closing = st.number_input("Statement closing day", min_value=1, max_value=31, value=13); due = st.number_input("Payment due day", min_value=1, max_value=31, value=13)
        submitted = st.form_submit_button("Add card", type="primary")
    if submitted and name.strip():
        st.session_state.credit_cards.append({"id": f"card_{st.session_state.next_card_number}", "name": name.strip(), "profile_id": profile["id"], "current_balance": f"{Decimal(str(balance)):.2f}", "statement_end_day": int(closing), "payment_due_day": int(due)})
        st.session_state.next_card_number += 1; mark_data_changed(); st.rerun()
    elif submitted: st.error("Enter a card name.")
    for card in cards_for_profile(st.session_state.credit_cards, profile["id"]): st.write(f"**{card['name']}**")


def _render_plans() -> None:
    profile = _active_profile(); cards = cards_for_profile(st.session_state.credit_cards, profile["id"]); st.header(f"BNPL plans — {profile['name']}")
    if not cards: st.warning("Add at least one credit card before adding a BNPL plan."); return
    labels = {c["id"]: c["name"] for c in cards}
    with st.form("add_plan", clear_on_submit=True):
        provider = st.text_input("Provider"); name = st.text_input("Purchase or plan name"); amount = st.number_input("Original purchase amount", min_value=0.01, value=100.0, step=0.01)
        currency = st.selectbox("Currency", ["CAD", "USD"]); purchase = st.date_input("Purchase date", value=date.today()); first = st.date_input("First installment date", value=date.today()); count = st.number_input("Total installments", min_value=1, value=4); card_id = st.selectbox("Card used", list(labels), format_func=labels.get)
        submitted = st.form_submit_button("Add BNPL plan", type="primary")
    if submitted and provider.strip() and name.strip():
        st.session_state.bnpl_plans.append({"id": f"plan_{st.session_state.next_plan_number}", "provider_name": provider.strip(), "plan_name": name.strip(), "purchase_amount": f"{Decimal(str(amount)):.2f}", "currency": currency, "purchase_date": purchase.isoformat(), "first_installment_date": first.isoformat(), "installment_count": int(count), "installment_frequency": "BIWEEKLY", "credit_card_id": card_id})
        st.session_state.next_plan_number += 1; mark_data_changed(); st.rerun()
    elif submitted: st.error("Enter provider and purchase name.")
    for plan in plans_for_profile(st.session_state.credit_cards, st.session_state.bnpl_plans, profile["id"]): st.write(f"**{plan['plan_name']}** · {plan['provider_name']}")


def _render_review() -> None:
    profile = _active_profile(); cards = cards_for_profile(st.session_state.credit_cards, profile["id"]); plans = plans_for_profile(st.session_state.credit_cards, st.session_state.bnpl_plans, profile["id"])
    st.header(f"Review and calculate — {profile['name']}")
    if not cards or not plans: st.warning("This profile is not ready: add at least one card and one BNPL plan before calculating."); return
    if st.button(f"Calculate cash flow — {profile['name']}", type="primary"):
        try: st.session_state.calculation_results_by_profile[profile["id"]] = calculate_from_entries(cards, plans)
        except InputValidationError as exc: st.error(str(exc))
    result = st.session_state.calculation_results_by_profile.get(profile["id"])
    if result:
        st.header(f"Cash flow obligations — {profile['name']}")
        st.success(f"Calculated as of {result.as_of_date.isoformat()}")
        card_names = {card.id: card.name for card in result.credit_cards}
        obligations = [
            {
                "Payment due": obligation.due_date.isoformat(),
                "Card": card_names[obligation.credit_card_id],
                "Statement closes": obligation.statement_cycle_end_date.isoformat(),
                "BNPL amount": float(obligation.total_amount - obligation.current_balance_amount),
                "Current balance": float(obligation.current_balance_amount),
                "Total due": float(obligation.total_amount),
                "Currency": obligation.currency,
            }
            for obligation in result.cash_flow_obligations
        ]
        st.dataframe(
            obligations,
            column_config={
                "BNPL amount": st.column_config.NumberColumn(format="%.2f"),
                "Current balance": st.column_config.NumberColumn(format="%.2f"),
                "Total due": st.column_config.NumberColumn(format="%.2f"),
            },
            hide_index=True,
        )

        with st.expander("Installment schedule"):
            st.dataframe(
                [
                    {
                        "Plan": projection.plan_name,
                        "Installment": projection.installment_number,
                        "Installment date": projection.installment_date.isoformat(),
                        "Amount": float(projection.installment_amount),
                        "Card": projection.credit_card_name,
                        "Payment due": projection.cash_flow_due_date.isoformat(),
                        "Currency": projection.currency,
                    }
                    for projection in result.projections
                ],
                column_config={"Amount": st.column_config.NumberColumn(format="%.2f")},
                hide_index=True,
            )
