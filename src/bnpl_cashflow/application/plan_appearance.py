"""Optional presentation metadata, independent of financial calculations."""
from bnpl_cashflow.input.validation import InputValidationError, ValidationIssue

PLAN_ICONS = {"shopping", "laptop", "home", "plane", "car", "gift", "heart", "book", "phone", "music", "coffee", "star"}
PLAN_COLORS = {"slate", "blue", "purple", "pink", "green", "orange"}


def plan_appearance(raw: dict, path: str) -> dict:
    result = {}
    for key, allowed in (("icon", PLAN_ICONS), ("icon_color", PLAN_COLORS)):
        value = raw.get(key)
        if value is None:
            continue
        if not isinstance(value, str) or value not in allowed:
            raise InputValidationError([ValidationIssue(f"{path}.{key}", "Choose one of the available plan icons or colors.")])
        result[key] = value
    return result
