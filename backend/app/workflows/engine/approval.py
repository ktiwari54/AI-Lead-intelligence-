from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID


class ApprovalEngine:
    """Evaluates approval policies for workflow approval nodes."""

    def evaluate_policy(
        self,
        *,
        approval_type: str,
        approvals: list[dict[str, Any]],
        required_count: int | None = None,
    ) -> str:
        if not approvals:
            return "pending"

        statuses = [a.get("status") for a in approvals]
        if any(s == "rejected" for s in statuses):
            return "rejected"

        approved = sum(1 for s in statuses if s == "approved")

        if approval_type == "sequential":
            for a in approvals:
                if a.get("status") == "pending":
                    return "pending"
            return "approved" if approved == len(approvals) else "pending"

        if approval_type == "parallel":
            needed = required_count or len(approvals)
            return "approved" if approved >= needed else "pending"

        if approval_type == "majority":
            needed = (len(approvals) // 2) + 1
            return "approved" if approved >= needed else "pending"

        return "approved" if approved == len(approvals) else "pending"

    def check_timeouts(self, approvals: list[dict[str, Any]], now: datetime | None = None) -> list[UUID]:
        now = now or datetime.now(timezone.utc)
        timed_out: list[UUID] = []
        for a in approvals:
            due = a.get("due_at")
            if due and a.get("status") == "pending":
                due_dt = due if isinstance(due, datetime) else datetime.fromisoformat(str(due))
                if due_dt < now:
                    aid = a.get("id")
                    if aid:
                        timed_out.append(UUID(str(aid)))
        return timed_out