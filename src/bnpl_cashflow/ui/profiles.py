from __future__ import annotations

from collections.abc import Sequence
from typing import Any


def create_profile(profiles: list[dict[str, str]], next_number: int, name: str) -> tuple[dict[str, str], int]:
    normalized = name.strip()
    if not normalized:
        raise ValueError("profile name must not be empty")
    if any(profile["name"].casefold() == normalized.casefold() for profile in profiles):
        raise ValueError("a profile with that name already exists")
    profile = {"id": f"profile_{next_number}", "name": normalized}
    profiles.append(profile)
    return profile, next_number + 1


def rename_profile(profiles: list[dict[str, str]], profile_id: str, name: str) -> None:
    normalized = name.strip()
    if not normalized:
        raise ValueError("profile name must not be empty")
    if any(profile["id"] != profile_id and profile["name"].casefold() == normalized.casefold() for profile in profiles):
        raise ValueError("a profile with that name already exists")
    profile = _profile(profiles, profile_id)
    profile["name"] = normalized


def cards_for_profile(cards: Sequence[dict[str, Any]], profile_id: str) -> list[dict[str, Any]]:
    return [card for card in cards if card.get("profile_id") == profile_id]


def plans_for_profile(
    cards: Sequence[dict[str, Any]], plans: Sequence[dict[str, Any]], profile_id: str
) -> list[dict[str, Any]]:
    card_ids = {card["id"] for card in cards_for_profile(cards, profile_id)}
    return [plan for plan in plans if plan.get("credit_card_id") in card_ids]


def delete_profile(
    profiles: list[dict[str, str]], cards: list[dict[str, Any]], plans: list[dict[str, Any]], active_profile_id: str | None, profile_id: str
) -> tuple[list[dict[str, str]], list[dict[str, Any]], list[dict[str, Any]], str | None]:
    _profile(profiles, profile_id)
    remaining_profiles = [profile for profile in profiles if profile["id"] != profile_id]
    removed_card_ids = {card["id"] for card in cards if card.get("profile_id") == profile_id}
    remaining_cards = [card for card in cards if card["id"] not in removed_card_ids]
    remaining_plans = [plan for plan in plans if plan.get("credit_card_id") not in removed_card_ids]
    if active_profile_id == profile_id:
        active_profile_id = remaining_profiles[0]["id"] if remaining_profiles else None
    return remaining_profiles, remaining_cards, remaining_plans, active_profile_id


def resolve_active_profile(profiles: Sequence[dict[str, str]], active_profile_id: str | None) -> str | None:
    if any(profile["id"] == active_profile_id for profile in profiles):
        return active_profile_id
    return profiles[0]["id"] if profiles else None


def _profile(profiles: Sequence[dict[str, str]], profile_id: str) -> dict[str, str]:
    for profile in profiles:
        if profile["id"] == profile_id:
            return profile
    raise ValueError("profile does not exist")
