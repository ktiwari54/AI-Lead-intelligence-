from __future__ import annotations

from typing import Any


class PolicyEngine:
    """Evaluates JSON policy rules against a security context."""

    def evaluate(self, rules: dict[str, Any], context: dict[str, Any]) -> dict[str, Any]:
        conditions = rules.get("conditions", [])
        actions = rules.get("actions", [])

        if not conditions:
            return {"decision": "allow", "matched": True, "actions": []}

        matched = all(self._eval_condition(c, context) for c in conditions)
        if not matched:
            return {"decision": "allow", "matched": False, "actions": []}

        for action in actions:
            if action.get("type") == "deny":
                return {
                    "decision": "deny",
                    "matched": True,
                    "reason": action.get("reason", "policy_denied"),
                    "actions": actions,
                }
            if action.get("type") == "step_up":
                return {
                    "decision": "step_up",
                    "matched": True,
                    "reason": action.get("reason", "mfa_required"),
                    "actions": actions,
                }

        return {"decision": "allow", "matched": True, "actions": actions}

    def _eval_condition(self, cond: dict[str, Any], ctx: dict[str, Any]) -> bool:
        field = cond.get("field", "")
        op = cond.get("operator", "eq")
        expected = cond.get("value")
        actual = self._resolve_field(field, ctx)

        if op == "eq":
            return actual == expected
        if op == "neq":
            return actual != expected
        if op == "in":
            return actual in (expected or [])
        if op == "not_in":
            return actual not in (expected or [])
        if op == "gte":
            return actual is not None and actual >= expected
        if op == "lte":
            return actual is not None and actual <= expected
        return False

    def _resolve_field(self, field: str, ctx: dict[str, Any]) -> Any:
        parts = field.split(".")
        val: Any = ctx
        for p in parts:
            if isinstance(val, dict):
                val = val.get(p)
            else:
                return None
        return val