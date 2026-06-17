from __future__ import annotations

import json
from collections.abc import Mapping
from typing import Any

from bnpl_cashflow.input.validation import ValidatedPayload, validate_payload


def parse_json_payload(source: str | bytes | Mapping[str, Any]) -> ValidatedPayload:
    if isinstance(source, Mapping):
        payload = dict(source)
    elif isinstance(source, bytes):
        payload = json.loads(source.decode("utf-8"))
    elif isinstance(source, str):
        payload = json.loads(source)
    else:
        raise TypeError("source must be JSON text, bytes, or a mapping")

    if not isinstance(payload, Mapping):
        raise ValueError("JSON payload must decode to an object")

    return validate_payload(payload)

