from __future__ import annotations

from datetime import datetime
from typing import Any, Literal
from uuid import UUID

from pydantic import BaseModel, Field

from backend.app.workflows.constants import OrchestrationMode


class WorkflowNodeSchema(BaseModel):
    key: str
    type: str
    label: str | None = None
    config: dict[str, Any] = Field(default_factory=dict)
    position: dict[str, float] = Field(default_factory=dict)


class WorkflowEdgeSchema(BaseModel):
    source: str
    target: str
    condition: dict[str, Any] | None = None
    label: str | None = None


class WorkflowCanvasSchema(BaseModel):
    nodes: list[WorkflowNodeSchema] = Field(default_factory=list)
    edges: list[WorkflowEdgeSchema] = Field(default_factory=list)
    variables: dict[str, Any] = Field(default_factory=dict)


class WorkflowTriggerSchema(BaseModel):
    type: str
    config: dict[str, Any] = Field(default_factory=dict)


class OrchestrationModeInfo(BaseModel):
    mode: str
    display_name: str
    purpose: str
    example: str
    dispatcher: str


class WorkflowCreateRequest(BaseModel):
    name: str
    description: str | None = None
    orchestration_mode: OrchestrationMode | None = None
    trigger: WorkflowTriggerSchema
    canvas: WorkflowCanvasSchema | None = None
    steps: list[dict[str, Any]] | None = None
    is_active: bool = True
    template_slug: str | None = None


class WorkflowUpdateRequest(BaseModel):
    name: str | None = None
    description: str | None = None
    orchestration_mode: OrchestrationMode | None = None
    trigger: WorkflowTriggerSchema | None = None
    canvas: WorkflowCanvasSchema | None = None
    steps: list[dict[str, Any]] | None = None
    is_active: bool | None = None


class WorkflowResponse(BaseModel):
    id: UUID
    organization_id: UUID
    name: str
    description: str | None
    orchestration_mode: str
    orchestration_mode_label: str | None = None
    trigger_type: str
    trigger_config: dict[str, Any]
    steps: list[dict[str, Any]]
    is_active: bool
    run_count: int
    status: str = "draft"
    current_version: int | None = None
    created_at: datetime
    updated_at: datetime

    model_config = {"from_attributes": True}


class WorkflowVersionResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    version_number: int
    status: str
    canvas: dict[str, Any]
    changelog: str | None
    published_at: datetime | None
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowExecuteRequest(BaseModel):
    entity_type: str | None = None
    entity_id: UUID | None = None
    payload: dict[str, Any] = Field(default_factory=dict)
    async_mode: bool = True
    idempotency_key: str | None = None


class WorkflowExecutionResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    status: str
    trigger_data: dict[str, Any]
    step_results: list[dict[str, Any]]
    error_message: str | None
    started_at: datetime | None = None
    completed_at: datetime | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class WorkflowApprovalRequest(BaseModel):
    comment: str | None = None


class WorkflowApprovalResponse(BaseModel):
    id: UUID
    execution_id: UUID
    node_key: str
    status: str
    approver_id: UUID | None
    comment: str | None
    due_at: datetime | None
    decided_at: datetime | None

    model_config = {"from_attributes": True}


class WorkflowScheduleRequest(BaseModel):
    schedule_type: Literal["cron", "once", "daily", "weekly", "monthly"]
    cron_expression: str | None = None
    timezone: str = "UTC"
    config: dict[str, Any] = Field(default_factory=dict)
    is_active: bool = True


class WorkflowScheduleResponse(BaseModel):
    id: UUID
    workflow_id: UUID
    schedule_type: str
    cron_expression: str | None
    timezone: str
    next_run_at: datetime | None
    last_run_at: datetime | None
    is_active: bool

    model_config = {"from_attributes": True}


class WorkflowTemplateResponse(BaseModel):
    id: UUID
    slug: str
    name: str
    description: str | None
    category: str
    trigger_type: str
    orchestration_mode: str = "event_driven"
    is_system: bool
    usage_count: int
    canvas: dict[str, Any]

    model_config = {"from_attributes": True}


class WorkflowAnalyticsResponse(BaseModel):
    runs_total: int
    runs_success: int
    runs_failed: int
    success_rate: float
    avg_duration_ms: float | None
    most_used_templates: list[dict[str, Any]]
    approval_metrics: dict[str, int]
    ai_node_usage: int
    period_days: int = 30


class WorkflowValidateResponse(BaseModel):
    valid: bool
    errors: list[str] = Field(default_factory=list)
    warnings: list[str] = Field(default_factory=list)
    compiled_plan: dict[str, Any] | None = None