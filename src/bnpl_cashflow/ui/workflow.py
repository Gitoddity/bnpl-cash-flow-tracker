from __future__ import annotations

from collections.abc import Sequence
from typing import Any

from bnpl_cashflow.application import ApplicationResult, run_application
from bnpl_cashflow.input import parse_json_payload


def build_payload(
    credit_cards: Sequence[dict[str, Any]],
    bnpl_plans: Sequence[dict[str, Any]],
) -> dict[str, object]:
    return {
        "credit_cards": [dict(card) for card in credit_cards],
        "bnpl_plans": [dict(plan) for plan in bnpl_plans],
    }


def calculate_from_entries(
    credit_cards: Sequence[dict[str, Any]],
    bnpl_plans: Sequence[dict[str, Any]],
) -> ApplicationResult:
    return run_application(parse_json_payload(build_payload(credit_cards, bnpl_plans)))
