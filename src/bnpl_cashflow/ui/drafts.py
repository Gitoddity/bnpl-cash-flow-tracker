from __future__ import annotations

import json
from collections.abc import Sequence
from pathlib import Path
from typing import Any

from bnpl_cashflow.input import parse_json_payload
from bnpl_cashflow.ui.workflow import build_payload


def default_draft_path() -> Path:
    return Path(__file__).resolve().parents[3] / "user-data" / "bnpl-ui-draft.json"


def draft_exists(path: Path | None = None) -> bool:
    return (path or default_draft_path()).is_file()


def save_draft(credit_cards: Sequence[dict[str, Any]], bnpl_plans: Sequence[dict[str, Any]], path: Path | None = None) -> Path:
    payload = build_payload(credit_cards, bnpl_plans)
    parse_json_payload(payload)
    draft_path = path or default_draft_path()
    draft_path.parent.mkdir(parents=True, exist_ok=True)
    draft_path.write_text(json.dumps(payload, indent=2) + "\n", encoding="utf-8")
    return draft_path


def load_draft(path: Path | None = None) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    draft_path = path or default_draft_path()
    payload = json.loads(draft_path.read_text(encoding="utf-8"))
    parse_json_payload(payload)
    return list(payload["credit_cards"]), list(payload["bnpl_plans"])


def discard_draft(path: Path | None = None) -> None:
    draft_path = path or default_draft_path()
    if draft_path.exists():
        draft_path.unlink()
