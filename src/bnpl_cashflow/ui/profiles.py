"""Compatibility imports for the existing Streamlit profile workflow."""

from bnpl_cashflow.application.profiles import (
    cards_for_profile,
    create_profile,
    delete_profile,
    plans_for_profile,
    rename_profile,
    resolve_active_profile,
)

__all__ = [
    "cards_for_profile", "create_profile", "delete_profile",
    "plans_for_profile", "rename_profile", "resolve_active_profile",
]
