from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from backend.app.workflows.constants import NodeType, OrchestrationMode, TriggerType


SCHEDULED_TRIGGERS = {TriggerType.SCHEDULED.value, TriggerType.CRON.value}

EVENT_TRIGGERS = {
    TriggerType.LEAD_CREATED.value,
    TriggerType.LEAD_UPDATED.value,
    TriggerType.COMPANY_CREATED.value,
    TriggerType.COMPANY_UPDATED.value,
    TriggerType.CONTACT_CREATED.value,
    TriggerType.TASK_CREATED.value,
    TriggerType.DEAL_CREATED.value,
    TriggerType.DEAL_WON.value,
    TriggerType.DEAL_LOST.value,
    TriggerType.ACTIVITY_COMPLETED.value,
    TriggerType.EMAIL_RECEIVED.value,
    TriggerType.WEBHOOK_RECEIVED.value,
    TriggerType.CSV_IMPORT_COMPLETED.value,
    TriggerType.CONNECTOR_COMPLETED.value,
    TriggerType.AI_RECOMMENDATION.value,
    TriggerType.USER_ACTION.value,
    TriggerType.CUSTOM.value,
}


@dataclass
class ModeProfile:
    """Runtime profile for a hybrid orchestration mode."""

    mode: OrchestrationMode
    display_name: str
    purpose: str
    example: str
    required_trigger_kinds: set[str] = field(default_factory=set)
    requires_approval_node: bool = False
    requires_schedule: bool = False
    dispatcher: str = ""
    supports_resume: bool = False
    supports_idempotency: bool = True


MODE_PROFILES: dict[OrchestrationMode, ModeProfile] = {
    OrchestrationMode.EVENT_DRIVEN: ModeProfile(
        mode=OrchestrationMode.EVENT_DRIVEN,
        display_name="Event-Driven",
        purpose="Reacts to system events",
        example="When a new lead is created, assign it and notify the sales manager.",
        required_trigger_kinds=EVENT_TRIGGERS,
        dispatcher="event_bus",
        supports_resume=False,
    ),
    OrchestrationMode.SCHEDULED: ModeProfile(
        mode=OrchestrationMode.SCHEDULED,
        display_name="Scheduled",
        purpose="Runs on a schedule",
        example="Every Monday at 8 AM, generate a pipeline report and email executives.",
        required_trigger_kinds=SCHEDULED_TRIGGERS,
        requires_schedule=True,
        dispatcher="celery_beat",
        supports_resume=False,
    ),
    OrchestrationMode.HUMAN_IN_THE_LOOP: ModeProfile(
        mode=OrchestrationMode.HUMAN_IN_THE_LOOP,
        display_name="Human-in-the-Loop",
        purpose="Requires user approval",
        example="If a lead score exceeds 90, send it for manager approval before creating an opportunity.",
        required_trigger_kinds=EVENT_TRIGGERS | {TriggerType.MANUAL.value},
        requires_approval_node=True,
        dispatcher="approval_engine",
        supports_resume=True,
    ),
}


def _nodes_from(canvas: dict[str, Any] | None, steps: list[dict] | None) -> list[dict]:
    if canvas and canvas.get("nodes"):
        return canvas["nodes"]
    return steps or []


def _has_approval_node(canvas: dict[str, Any] | None, steps: list[dict] | None) -> bool:
    for node in _nodes_from(canvas, steps):
        ntype = node.get("type", "")
        if ntype == NodeType.APPROVAL.value:
            return True
        if ntype == "action" and node.get("config", {}).get("action_type") == "wait_for_approval":
            return True
    return False


def infer_orchestration_mode(
    *,
    trigger_type: str,
    canvas: dict[str, Any] | None = None,
    steps: list[dict] | None = None,
    explicit_mode: str | None = None,
) -> OrchestrationMode:
    """Infer the best orchestration mode when not explicitly set."""
    if explicit_mode:
        return OrchestrationMode(explicit_mode)

    if _has_approval_node(canvas, steps):
        return OrchestrationMode.HUMAN_IN_THE_LOOP
    if trigger_type in SCHEDULED_TRIGGERS:
        return OrchestrationMode.SCHEDULED
    return OrchestrationMode.EVENT_DRIVEN


def validate_mode_constraints(
    mode: OrchestrationMode,
    *,
    trigger_type: str,
    canvas: dict[str, Any] | None = None,
    steps: list[dict] | None = None,
    has_schedule: bool = False,
) -> list[str]:
    """Validate workflow definition against orchestration mode requirements."""
    profile = MODE_PROFILES[mode]
    errors: list[str] = []

    if mode == OrchestrationMode.SCHEDULED:
        if trigger_type not in SCHEDULED_TRIGGERS and not has_schedule:
            errors.append(
                "Scheduled orchestrations require a cron/scheduled trigger or an active workflow schedule"
            )
    elif mode == OrchestrationMode.EVENT_DRIVEN:
        if trigger_type in SCHEDULED_TRIGGERS:
            errors.append("Event-driven orchestrations cannot use cron/scheduled triggers")
        if trigger_type == TriggerType.MANUAL.value:
            errors.append("Event-driven orchestrations require a domain event trigger (e.g. lead.created)")
    elif mode == OrchestrationMode.HUMAN_IN_THE_LOOP:
        if not _has_approval_node(canvas, steps):
            errors.append("Human-in-the-loop orchestrations must include at least one approval node")

    return errors


def mode_supports_trigger(mode: OrchestrationMode, trigger_type: str) -> bool:
    profile = MODE_PROFILES[mode]
    if mode == OrchestrationMode.SCHEDULED:
        return trigger_type in SCHEDULED_TRIGGERS
    if mode == OrchestrationMode.EVENT_DRIVEN:
        return trigger_type in EVENT_TRIGGERS
    return trigger_type in profile.required_trigger_kinds


def get_dispatcher_for_mode(mode: OrchestrationMode) -> str:
    return MODE_PROFILES[mode].dispatcher


def list_mode_catalog() -> list[dict[str, str]]:
    return [
        {
            "mode": p.mode.value,
            "display_name": p.display_name,
            "purpose": p.purpose,
            "example": p.example,
            "dispatcher": p.dispatcher,
        }
        for p in MODE_PROFILES.values()
    ]