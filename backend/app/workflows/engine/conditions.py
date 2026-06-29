from __future__ import annotations

import re
from datetime import datetime
from typing import Any


def _resolve_path(context: dict[str, Any], path: str) -> Any:
    parts = path.split(".")
    current: Any = context
    for part in parts:
        if current is None:
            return None
        if isinstance(current, dict):
            current = current.get(part)
        else:
            return None
    return current


def _compare(left: Any, operator: str, right: Any) -> bool:
    if operator == "eq":
        return left == right
    if operator == "ne":
        return left != right
    if operator == "gt":
        return left is not None and right is not None and left > right
    if operator == "gte":
        return left is not None and right is not None and left >= right
    if operator == "lt":
        return left is not None and right is not None and left < right
    if operator == "lte":
        return left is not None and right is not None and left <= right
    if operator == "in":
        return left in (right or [])
    if operator == "not_in":
        return left not in (right or [])
    if operator == "contains":
        return right in str(left or "")
    if operator == "regex":
        return bool(re.search(str(right), str(left or "")))
    if operator == "exists":
        return left is not None
    if operator == "null":
        return left is None
    if operator == "not_null":
        return left is not None
    return False


def evaluate_condition(condition: dict[str, Any], context: dict[str, Any]) -> bool:
    """Evaluate a single condition or nested boolean group."""
    if not condition:
        return True

    if "and" in condition:
        return all(evaluate_condition(c, context) for c in condition["and"])
    if "or" in condition:
        return any(evaluate_condition(c, context) for c in condition["or"])
    if "not" in condition:
        return not evaluate_condition(condition["not"], context)

    if condition.get("type") == "switch":
        field_val = _resolve_path(context, condition.get("field", ""))
        cases = condition.get("cases", {})
        return cases.get(str(field_val), cases.get("default", False)) is True

    field = condition.get("field", "")
    operator = condition.get("operator", "eq")
    value = condition.get("value")
    left = _resolve_path(context, field) if field else condition.get("left")

    if operator in ("date_before", "date_after"):
        try:
            left_dt = datetime.fromisoformat(str(left).replace("Z", "+00:00"))
            right_dt = datetime.fromisoformat(str(value).replace("Z", "+00:00"))
            return left_dt < right_dt if operator == "date_before" else left_dt > right_dt
        except (ValueError, TypeError):
            return False

    return _compare(left, operator, value)


def evaluate_conditions(conditions: list[dict[str, Any]], context: dict[str, Any]) -> bool:
    if not conditions:
        return True
    return all(evaluate_condition(c, context) for c in conditions)