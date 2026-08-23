from __future__ import annotations

from datetime import date
from decimal import Decimal

import pandas as pd
import streamlit as st

from bnpl_cashflow.input import InputValidationError
from bnpl_cashflow.ui.drafts import discard_draft, draft_exists, load_draft, save_draft
from bnpl_cashflow.ui.state import (
    WORKSPACE_STEP,
    mark_data_changed,
    replace_financial_data,
    reset_financial_data,
    reset_to_welcome,
    set_current_step,
)
from bnpl_cashflow.ui.workflow import build_payload, calculate_from_entries


def render_welcome_screen() -> None:
    st.title("BNPL Cash Flow Tracker")
    st.write("See how your BNPL plans affect upcoming card statements and payment dates.")

    with st.container(border=True):
        st.subheader("What you'll add")
        st.write("Credit cards, current balances, statement dates, and remaining BNPL plans.")
        st.caption("Use Save draft to keep your entries locally on this device.")

    if st.button("Get started", type="primary", icon=":material/arrow_forward:"):
        set_current_step(WORKSPACE_STEP)
        st.rerun()

    if draft_exists() and st.button("Load saved draft", icon=":material/folder_open:"):
        try:
            cards, plans = load_draft()
            replace_financial_data(cards, plans)
            set_current_step(WORKSPACE_STEP)
            st.rerun()
        except (OSError, ValueError, InputValidationError, KeyError) as exc:
            st.error(f"The saved draft could not be loaded: {exc}")


def render_workspace_screen() -> None:
    st.title("BNPL Cash Flow Tracker")
    st.caption(f"Calculations use the system date: {date.today().isoformat()}")

    view = st.segmented_control(
        "Input step",
        ["Profiles", "Cards", "BNPL plans", "Review & calculate"],
        default=st.session_state.workspace_view,
        key="workspace_navigation",
        required=True,
        width="stretch",
    )
    st.session_state.workspace_view = view

    if view == "Profiles":
        _render_profiles()
    elif view == "Cards":
        _render_cards()
    elif view == "BNPL plans":
        _render_plans()
    else:
        _render_review_and_results()

    st.divider()
    with st.container(horizontal=True):
        if st.button("Back", icon=":material/arrow_back:"):
            reset_to_welcome()
            st.rerun()
        if st.button("Save draft", icon=":material/save:"):
            try:
                save_draft(st.session_state.credit_cards, st.session_state.bnpl_plans)
                st.toast("Draft saved locally.")
            except (OSError, InputValidationError) as exc:
                st.error(f"Draft could not be saved: {exc}")
        if st.button("Clear session data", icon=":material/delete:"):
            reset_financial_data()
            st.rerun()
        if draft_exists() and st.button("Discard saved draft", icon=":material/delete_forever:"):
            discard_draft()
            st.toast("Saved draft discarded.")
            st.rerun()


def _render_cards() -> None:
    st.header("Credit cards")
    profiles = st.session_state.profiles
    if not profiles:
        st.warning("Create a profile first. Cards and plans are grouped under a profile.")
        return
    st.write("Add every card used by a BNPL plan. Do not enter card numbers or security codes.")

    with st.form("add_card", clear_on_submit=True):
        name = st.text_input("Card name", placeholder="Tangerine Mastercard")
        profile_name = st.selectbox("Profile", profiles)
        current_balance = st.number_input("Current balance", min_value=0.0, step=0.01, format="%.2f")
        statement_end_day = st.number_input("Statement closing day", min_value=1, max_value=31, value=13, step=1)
        payment_due_day = st.number_input("Payment due day", min_value=1, max_value=31, value=13, step=1)
        submitted = st.form_submit_button("Add card", type="primary", icon=":material/add_card:")

    if submitted:
        if not name.strip():
            st.error("Enter a card name.")
        else:
            card_id = f"card_{st.session_state.next_card_number}"
            st.session_state.credit_cards.append(
                {
                    "id": card_id,
                    "name": name.strip(),
                    "profile_name": profile_name,
                    "statement_end_day": int(statement_end_day),
                    "payment_due_day": int(payment_due_day),
                    "current_balance": f"{Decimal(str(current_balance)):.2f}",
                }
            )
            st.session_state.next_card_number += 1
            mark_data_changed()
            st.rerun()

    _render_card_list()


def _render_profiles() -> None:
    st.header("Profiles")
    st.write("Create a profile to group cards and the BNPL plans charged to those cards.")
    with st.form("add_profile", clear_on_submit=True):
        name = st.text_input("Profile name", placeholder="Personal or Household")
        submitted = st.form_submit_button("Add profile", type="primary", icon=":material/person_add:")
    if submitted:
        normalized_name = name.strip()
        if not normalized_name:
            st.error("Enter a profile name.")
        elif normalized_name.casefold() in {profile.casefold() for profile in st.session_state.profiles}:
            st.error("A profile with that name already exists.")
        else:
            st.session_state.profiles.append(normalized_name)
            st.toast("Profile added. You can now add cards to it.")
            st.rerun()

    if not st.session_state.profiles:
        st.info("No profiles added yet.")
        return
    st.subheader("Profiles added")
    for profile in st.session_state.profiles:
        card_count = sum(card.get("profile_name", "Default profile") == profile for card in st.session_state.credit_cards)
        st.write(f"**{profile}** — {card_count} card{'s' if card_count != 1 else ''}")


def _render_card_list() -> None:
    cards = st.session_state.credit_cards
    if not cards:
        st.info("No cards added yet.")
        return

    st.subheader(f"Cards added ({len(cards)})")
    for card in cards:
        with st.container(border=True):
            st.markdown(f"**{card['name']}**")
            st.caption(
                f"Current balance ${card['current_balance']} · closes day {card['statement_end_day']} · "
                f"due day {card['payment_due_day']}"
            )
            if st.button("Remove", key=f"remove_{card['id']}", icon=":material/delete:"):
                st.session_state.credit_cards = [item for item in cards if item["id"] != card["id"]]
                st.session_state.bnpl_plans = [
                    plan for plan in st.session_state.bnpl_plans if plan["credit_card_id"] != card["id"]
                ]
                mark_data_changed()
                st.rerun()


def _render_plans() -> None:
    st.header("BNPL plans")
    cards = st.session_state.credit_cards
    if not cards:
        st.warning("Add at least one credit card before adding a BNPL plan.")
        return

    card_names = {card["id"]: f"{card.get('profile_name', 'Default profile')} — {card['name']}" for card in cards}
    with st.form("add_plan", clear_on_submit=True):
        provider_name = st.text_input("Provider", placeholder="PayPal")
        plan_name = st.text_input("Purchase or plan name", placeholder="Coffee equipment")
        purchase_amount = st.number_input("Original purchase amount", min_value=0.01, value=100.0, step=0.01, format="%.2f")
        currency = st.selectbox("Currency", ["CAD", "USD"])
        purchase_date = st.date_input("Purchase date", value=date.today())
        first_installment_date = st.date_input("First installment date", value=date.today())
        installment_count = st.number_input("Total installments", min_value=1, value=4, step=1)
        paid_installment_count = st.number_input(
            "Installments already paid", min_value=0, max_value=int(installment_count), value=0, step=1
        )
        amount_paid = st.number_input("Exact amount already paid", min_value=0.0, step=0.01, format="%.2f")
        credit_card_id = st.selectbox("Card used", list(card_names), format_func=card_names.get)
        submitted = st.form_submit_button("Add BNPL plan", type="primary", icon=":material/add:")

    if submitted:
        error = _plan_form_error(provider_name, plan_name, purchase_amount, paid_installment_count, amount_paid)
        if error:
            st.error(error)
        else:
            plan_id = f"plan_{st.session_state.next_plan_number}"
            st.session_state.bnpl_plans.append(
                {
                    "id": plan_id,
                    "provider_name": provider_name.strip(),
                    "plan_name": plan_name.strip(),
                    "purchase_amount": f"{Decimal(str(purchase_amount)):.2f}",
                    "currency": currency,
                    "purchase_date": purchase_date.isoformat(),
                    "first_installment_date": first_installment_date.isoformat(),
                    "installment_count": int(installment_count),
                    "paid_installment_count": int(paid_installment_count),
                    "amount_paid": f"{Decimal(str(amount_paid)):.2f}",
                    "installment_frequency": "BIWEEKLY",
                    "credit_card_id": credit_card_id,
                }
            )
            st.session_state.next_plan_number += 1
            mark_data_changed()
            st.rerun()

    _render_plan_list(card_names)


def _plan_form_error(provider: str, name: str, purchase_amount: float, paid_count: int, amount_paid: float) -> str | None:
    if not provider.strip() or not name.strip():
        return "Enter both a provider and a purchase name."
    if amount_paid > purchase_amount:
        return "Amount paid cannot exceed the original purchase amount."
    if paid_count == 0 and amount_paid > 0:
        return "Set the number of paid installments when an amount has already been paid."
    return None


def _render_plan_list(card_names: dict[str, str]) -> None:
    plans = st.session_state.bnpl_plans
    if not plans:
        st.info("No BNPL plans added yet.")
        return

    st.subheader(f"Plans added ({len(plans)})")
    for plan in plans:
        with st.container(border=True):
            st.markdown(f"**{plan['plan_name']}** · {plan['provider_name']}")
            st.caption(
                f"${plan['purchase_amount']} {plan['currency']} · {plan['paid_installment_count']} of "
                f"{plan['installment_count']} paid · {card_names[plan['credit_card_id']]}"
            )
            if st.button("Remove", key=f"remove_{plan['id']}", icon=":material/delete:"):
                st.session_state.bnpl_plans = [item for item in plans if item["id"] != plan["id"]]
                mark_data_changed()
                st.rerun()


def _render_review_and_results() -> None:
    st.header("Review and calculate")
    cards = st.session_state.credit_cards
    plans = st.session_state.bnpl_plans
    if not cards or not plans:
        st.warning("Add at least one card and one BNPL plan before calculating.")
        return

    card_names = {card["id"]: card["name"] for card in cards}
    st.write("Each profile is an independent cash-flow calculation. Correct any entry below, then select **Apply review changes** before calculating.")
    _render_profile_summary(cards, plans)
    st.subheader("Edit entries")
    editor_version = st.session_state.review_editor_version
    card_labels = {card["id"]: f"{card['name']} ({card['id']})" for card in cards}
    label_to_card_id = {label: card_id for card_id, label in card_labels.items()}

    with st.form("review_editor"):
        st.subheader("Cards")
        edited_cards = st.data_editor(
            pd.DataFrame(
                [
                    {
                        "Card ID": card["id"],
                        "Card": card["name"],
                        "Profile": card.get("profile_name", "Default profile"),
                        "Current balance": float(card["current_balance"]),
                        "Statement closes": card["statement_end_day"],
                        "Payment due": card["payment_due_day"],
                    }
                    for card in cards
                ]
            ),
            hide_index=True,
            disabled=["Card ID"],
            key=f"review_cards_editor_{editor_version}",
            column_config={
                "Current balance": st.column_config.NumberColumn(min_value=0.0, format="$%.2f"),
                "Statement closes": st.column_config.NumberColumn(min_value=1, max_value=31, step=1),
                "Payment due": st.column_config.NumberColumn(min_value=1, max_value=31, step=1),
                "Profile": st.column_config.SelectboxColumn(options=st.session_state.profiles),
            },
        )
        st.subheader("BNPL plans")
        edited_plans = st.data_editor(
            pd.DataFrame(
                [
                    {
                        "Plan ID": plan["id"],
                        "Plan": plan["plan_name"],
                        "Provider": plan["provider_name"],
                        "Card": card_labels[plan["credit_card_id"]],
                        "Purchase amount": float(plan["purchase_amount"]),
                        "Currency": plan["currency"],
                        "Purchase date": date.fromisoformat(plan["purchase_date"]),
                        "First installment": date.fromisoformat(plan["first_installment_date"]),
                        "Installments": plan["installment_count"],
                        "Already paid": plan["paid_installment_count"],
                        "Amount paid": float(plan["amount_paid"]),
                    }
                    for plan in plans
                ]
            ),
            hide_index=True,
            disabled=["Plan ID"],
            key=f"review_plans_editor_{editor_version}",
            column_config={
                "Card": st.column_config.SelectboxColumn(options=list(label_to_card_id)),
                "Purchase amount": st.column_config.NumberColumn(min_value=0.01, format="$%.2f"),
                "Currency": st.column_config.SelectboxColumn(options=["CAD", "USD"]),
                "Purchase date": st.column_config.DateColumn(format="MMM D, YYYY"),
                "First installment": st.column_config.DateColumn(format="MMM D, YYYY"),
                "Installments": st.column_config.NumberColumn(min_value=1, step=1),
                "Already paid": st.column_config.NumberColumn(min_value=0, step=1),
                "Amount paid": st.column_config.NumberColumn(min_value=0.0, format="$%.2f"),
            },
        )
        apply_changes = st.form_submit_button("Apply review changes", icon=":material/check:")

    if apply_changes:
        try:
            updated_cards, updated_plans = _entries_from_review(edited_cards, edited_plans, label_to_card_id)
            # Validate before modifying session state, so an invalid edit is not lost.
            from bnpl_cashflow.input import parse_json_payload

            parse_json_payload(build_payload(updated_cards, updated_plans))
            replace_financial_data(updated_cards, updated_plans)
            st.toast("Review changes applied.")
            st.rerun()
        except (InputValidationError, ValueError, KeyError) as exc:
            st.error(f"Please correct the review entries: {exc}")

    st.subheader("Calculate by profile")
    for profile_name in st.session_state.profiles:
        profile_cards = [card for card in cards if card.get("profile_name", "Default profile") == profile_name]
        card_ids = {card["id"] for card in profile_cards}
        profile_plans = [plan for plan in plans if plan["credit_card_id"] in card_ids]
        if not profile_cards:
            continue
        if not profile_plans:
            st.info(f"{profile_name}: add a BNPL plan before calculating.")
            continue
        if st.button(f"Calculate cash flow — {profile_name}", key=f"calculate_profile_{profile_name}", type="primary", icon=":material/calculate:"):
            try:
                st.session_state.calculation_results_by_profile[profile_name] = calculate_from_entries(profile_cards, profile_plans)
            except InputValidationError as exc:
                st.error(f"{profile_name}: please fix the following input issues:")
                for issue in exc.issues:
                    st.write(f"- {issue.format()}")
            except Exception:
                st.error(f"{profile_name}: the calculation could not be completed. Review the entries and try again.")

    for profile_name, result in st.session_state.calculation_results_by_profile.items():
        st.divider()
        st.header(f"Cash flow obligations — {profile_name}")
        _render_results(result, card_names, show_heading=False)


def _entries_from_review(
    card_frame: pd.DataFrame, plan_frame: pd.DataFrame, label_to_card_id: dict[str, str]
) -> tuple[list[dict[str, object]], list[dict[str, object]]]:
    cards = [
        {
            "id": str(row["Card ID"]),
            "name": str(row["Card"]).strip(),
            "profile_name": str(row["Profile"]).strip(),
            "current_balance": _money_text(row["Current balance"]),
            "statement_end_day": int(row["Statement closes"]),
            "payment_due_day": int(row["Payment due"]),
        }
        for _, row in card_frame.iterrows()
    ]
    plans = [
        {
            "id": str(row["Plan ID"]),
            "provider_name": str(row["Provider"]).strip(),
            "plan_name": str(row["Plan"]).strip(),
            "credit_card_id": label_to_card_id[str(row["Card"])],
            "purchase_amount": _money_text(row["Purchase amount"]),
            "currency": str(row["Currency"]),
            "purchase_date": _iso_date(row["Purchase date"]),
            "first_installment_date": _iso_date(row["First installment"]),
            "installment_count": int(row["Installments"]),
            "paid_installment_count": int(row["Already paid"]),
            "amount_paid": _money_text(row["Amount paid"]),
            "installment_frequency": "BIWEEKLY",
        }
        for _, row in plan_frame.iterrows()
    ]
    return cards, plans


def _render_profile_summary(cards: list[dict], plans: list[dict]) -> None:
    st.subheader("1. Profiles, cards, and plans")
    for profile_name in st.session_state.profiles:
        profile_cards = [card for card in cards if card.get("profile_name", "Default profile") == profile_name]
        if not profile_cards:
            continue
        card_ids = {card["id"] for card in profile_cards}
        profile_plans = [plan for plan in plans if plan["credit_card_id"] in card_ids]
        with st.container(border=True):
            st.markdown(f"**{profile_name}**")
            st.caption(f"{len(profile_cards)} card(s) · {len(profile_plans)} BNPL plan(s)")
            st.dataframe(
                [{"Card name": card["name"], "Current balance": float(card["current_balance"])} for card in profile_cards],
                hide_index=True,
                column_config={"Current balance": st.column_config.NumberColumn(format="$%.2f")},
            )
            st.dataframe(
                [
                    {
                        "Plan": plan["plan_name"],
                        "Provider": plan["provider_name"],
                        "Card": next(card["name"] for card in profile_cards if card["id"] == plan["credit_card_id"]),
                        "Purchase amount": float(plan["purchase_amount"]),
                    }
                    for plan in profile_plans
                ],
                hide_index=True,
                column_config={"Purchase amount": st.column_config.NumberColumn(format="$%.2f")},
            )


def _money_text(value: object) -> str:
    return f"{Decimal(str(value)):.2f}"


def _iso_date(value: object) -> str:
    if isinstance(value, pd.Timestamp):
        return value.date().isoformat()
    if isinstance(value, date):
        return value.isoformat()
    return date.fromisoformat(str(value)).isoformat()


def _render_results(result, card_names: dict[str, str], *, show_heading: bool = True) -> None:
    st.success(f"Calculated as of {result.as_of_date.isoformat()}")
    cards_by_id = {card.id: card for card in result.credit_cards}
    total = sum((item.total_amount for item in result.cash_flow_obligations), Decimal("0.00"))
    with st.container(horizontal=True):
        st.metric("Cards", len(result.credit_cards))
        st.metric("Active plans", len(result.bnpl_plans))
        st.metric("Total upcoming cash flow", f"${total:,.2f}")

    if show_heading:
        st.subheader("Cash flow obligations")
    st.dataframe(
        [
            {
                "Profile name": cards_by_id[item.credit_card_id].profile_name,
                "Card name": cards_by_id[item.credit_card_id].name,
                "Statement end date": item.statement_cycle_end_date,
                "Payment due date": item.due_date,
                "Statement period": _statement_period_text(item.statement_cycle_start_date, item.statement_cycle_end_date),
                "Amount": float(item.total_amount),
            }
            for item in result.cash_flow_obligations
        ],
        hide_index=True,
        column_config={
            "Statement end date": st.column_config.DateColumn(format="MMM D, YYYY"),
            "Payment due date": st.column_config.DateColumn(format="MMM D, YYYY"),
            "Amount": st.column_config.NumberColumn(format="$%.2f"),
        },
    )
    st.subheader("Upcoming installments")
    st.dataframe(
        [
            {
                "Date": projection.installment_date,
                "Plan": projection.plan_name,
                "Card": projection.credit_card_name,
                "Installment": projection.installment_number,
                "Amount": float(projection.installment_amount),
                "Payment due": projection.cash_flow_due_date,
            }
            for projection in result.projections
        ],
        hide_index=True,
        column_config={
            "Date": st.column_config.DateColumn(format="MMM D, YYYY"),
            "Payment due": st.column_config.DateColumn(format="MMM D, YYYY"),
            "Amount": st.column_config.NumberColumn(format="$%.2f"),
        },
    )


def _statement_period_text(start_date: date | None, end_date: date) -> str:
    if start_date is None:
        return f"Statement ending {end_date.strftime('%b %d, %Y')}"
    return f"Statement period {start_date.strftime('%b %d')} to {end_date.strftime('%b %d, %Y')}"
