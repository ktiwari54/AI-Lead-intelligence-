from __future__ import annotations

from enum import Enum


class WorkflowStatus(str, Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    ARCHIVED = "archived"


class ExecutionStatus(str, Enum):
    PENDING = "pending"
    RUNNING = "running"
    WAITING = "waiting"
    PAUSED = "paused"
    COMPLETED = "completed"
    FAILED = "failed"
    CANCELLED = "cancelled"
    TIMED_OUT = "timed_out"


class NodeType(str, Enum):
    TRIGGER = "trigger"
    ACTION = "action"
    CONDITION = "condition"
    DECISION = "decision"
    DELAY = "delay"
    TIMER = "timer"
    APPROVAL = "approval"
    AI = "ai"
    WEBHOOK = "webhook"
    SUB_WORKFLOW = "sub_workflow"
    PARALLEL = "parallel"
    MERGE = "merge"
    LOOP = "loop"
    END = "end"


class TriggerType(str, Enum):
    LEAD_CREATED = "lead.created"
    LEAD_UPDATED = "lead.updated"
    COMPANY_CREATED = "company.created"
    COMPANY_UPDATED = "company.updated"
    CONTACT_CREATED = "contact.created"
    TASK_CREATED = "task.created"
    DEAL_CREATED = "deal.created"
    DEAL_WON = "deal.won"
    DEAL_LOST = "deal.lost"
    ACTIVITY_COMPLETED = "activity.completed"
    EMAIL_RECEIVED = "email.received"
    WEBHOOK_RECEIVED = "webhook.received"
    SCHEDULED = "scheduled"
    CRON = "cron"
    API_CALL = "api.call"
    CSV_IMPORT_COMPLETED = "import.completed"
    CONNECTOR_COMPLETED = "connector.completed"
    AI_RECOMMENDATION = "ai.recommendation"
    USER_ACTION = "user.action"
    MANUAL = "manual"
    CUSTOM = "custom"


class ApprovalStatus(str, Enum):
    PENDING = "pending"
    APPROVED = "approved"
    REJECTED = "rejected"
    DELEGATED = "delegated"
    ESCALATED = "escalated"
    TIMED_OUT = "timed_out"


TRIGGER_EVENT_MAP: dict[str, TriggerType] = {
    "company.created": TriggerType.COMPANY_CREATED,
    "company.updated": TriggerType.COMPANY_UPDATED,
    "contact.created": TriggerType.CONTACT_CREATED,
    "lead.created": TriggerType.LEAD_CREATED,
    "lead.updated": TriggerType.LEAD_UPDATED,
    "deal.created": TriggerType.DEAL_CREATED,
    "deal.won": TriggerType.DEAL_WON,
    "deal.lost": TriggerType.DEAL_LOST,
    "import.completed": TriggerType.CSV_IMPORT_COMPLETED,
    "connector.finished": TriggerType.CONNECTOR_COMPLETED,
    "workflow.executed": TriggerType.CUSTOM,
}