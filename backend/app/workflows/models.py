from __future__ import annotations

import uuid
from datetime import datetime

from sqlalchemy import (
    Boolean,
    DateTime,
    ForeignKey,
    Index,
    Integer,
    Numeric,
    String,
    Text,
    UniqueConstraint,
    text,
)
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from backend.app.common.base import BaseModel


class WorkflowVersion(BaseModel):
    __tablename__ = "workflow_versions"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    version_number: Mapped[int] = mapped_column(Integer, nullable=False)
    status: Mapped[str] = mapped_column(String(20), server_default="draft", nullable=False)
    canvas: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    compiled_plan: Mapped[dict | None] = mapped_column(JSONB)
    changelog: Mapped[str | None] = mapped_column(Text)
    published_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    published_by: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )

    __table_args__ = (
        Index("ix_workflow_versions_workflow_id", "workflow_id"),
        UniqueConstraint("workflow_id", "version_number", name="uq_workflow_version"),
    )

    workflow: Mapped["Workflow"] = relationship("Workflow", back_populates="versions", foreign_keys=[workflow_id])


class WorkflowNode(BaseModel):
    __tablename__ = "workflow_nodes"

    workflow_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_versions.id", ondelete="CASCADE"), nullable=False
    )
    node_key: Mapped[str] = mapped_column(String(100), nullable=False)
    node_type: Mapped[str] = mapped_column(String(50), nullable=False)
    label: Mapped[str | None] = mapped_column(String(255))
    config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    position: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    __table_args__ = (
        Index("ix_workflow_nodes_version_id", "workflow_version_id"),
        UniqueConstraint("workflow_version_id", "node_key", name="uq_workflow_node_key"),
    )


class WorkflowEdge(BaseModel):
    __tablename__ = "workflow_edges"

    workflow_version_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_versions.id", ondelete="CASCADE"), nullable=False
    )
    source_node_key: Mapped[str] = mapped_column(String(100), nullable=False)
    target_node_key: Mapped[str] = mapped_column(String(100), nullable=False)
    condition: Mapped[dict | None] = mapped_column(JSONB)
    label: Mapped[str | None] = mapped_column(String(100))

    __table_args__ = (Index("ix_workflow_edges_version_id", "workflow_version_id"),)


class WorkflowVariable(BaseModel):
    __tablename__ = "workflow_variables"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    name: Mapped[str] = mapped_column(String(100), nullable=False)
    var_type: Mapped[str] = mapped_column(String(50), server_default="string", nullable=False)
    default_value: Mapped[dict | None] = mapped_column(JSONB)
    is_secret: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    scope: Mapped[str] = mapped_column(String(20), server_default="workflow", nullable=False)

    __table_args__ = (
        Index("ix_workflow_variables_workflow_id", "workflow_id"),
        UniqueConstraint("workflow_id", "name", name="uq_workflow_variable"),
    )


class WorkflowExecutionLog(BaseModel):
    __tablename__ = "workflow_execution_logs"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False
    )
    node_key: Mapped[str | None] = mapped_column(String(100))
    level: Mapped[str] = mapped_column(String(20), server_default="info", nullable=False)
    message: Mapped[str] = mapped_column(Text, nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    duration_ms: Mapped[int | None] = mapped_column(Integer)

    __table_args__ = (
        Index("ix_workflow_execution_logs_execution_id", "execution_id"),
        Index("ix_workflow_execution_logs_created_at", "created_at"),
    )


class WorkflowTemplate(BaseModel):
    __tablename__ = "workflow_templates"

    organization_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE")
    )
    slug: Mapped[str] = mapped_column(String(100), nullable=False)
    name: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str | None] = mapped_column(Text)
    category: Mapped[str] = mapped_column(String(50), server_default="general", nullable=False)
    canvas: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    trigger_type: Mapped[str] = mapped_column(String(50), nullable=False)
    orchestration_mode: Mapped[str] = mapped_column(
        String(30), server_default="event_driven", nullable=False
    )
    is_system: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)
    usage_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)

    __table_args__ = (
        Index("ix_workflow_templates_slug", "slug"),
        Index("ix_workflow_templates_category", "category"),
    )


class WorkflowSchedule(BaseModel):
    __tablename__ = "workflow_schedules"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    schedule_type: Mapped[str] = mapped_column(String(20), nullable=False)
    cron_expression: Mapped[str | None] = mapped_column(String(100))
    timezone: Mapped[str] = mapped_column(String(50), server_default="UTC", nullable=False)
    next_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_run_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    is_active: Mapped[bool] = mapped_column(Boolean, server_default="true", nullable=False)
    config: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)

    __table_args__ = (
        Index("ix_workflow_schedules_workflow_id", "workflow_id"),
        Index("ix_workflow_schedules_next_run", "next_run_at"),
    )


class WorkflowApproval(BaseModel):
    __tablename__ = "workflow_approvals"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False
    )
    node_key: Mapped[str] = mapped_column(String(100), nullable=False)
    approver_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("users.id", ondelete="SET NULL")
    )
    status: Mapped[str] = mapped_column(String(20), server_default="pending", nullable=False)
    approval_type: Mapped[str] = mapped_column(String(30), server_default="sequential", nullable=False)
    comment: Mapped[str | None] = mapped_column(Text)
    decided_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    due_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    metadata_: Mapped[dict] = mapped_column(
        "metadata", JSONB, server_default=text("'{}'::jsonb"), nullable=False
    )

    __table_args__ = (
        Index("ix_workflow_approvals_execution_id", "execution_id"),
        Index("ix_workflow_approvals_status", "status"),
    )


class WorkflowEvent(BaseModel):
    __tablename__ = "workflow_events"

    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    workflow_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="SET NULL")
    )
    execution_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="SET NULL")
    )
    event_type: Mapped[str] = mapped_column(String(100), nullable=False)
    payload: Mapped[dict] = mapped_column(JSONB, server_default=text("'{}'::jsonb"), nullable=False)
    correlation_id: Mapped[str | None] = mapped_column(String(100))
    idempotency_key: Mapped[str | None] = mapped_column(String(100))

    __table_args__ = (
        Index("ix_workflow_events_org_id", "organization_id"),
        Index("ix_workflow_events_event_type", "event_type"),
        Index("ix_workflow_events_correlation_id", "correlation_id"),
    )


class WorkflowPermission(BaseModel):
    __tablename__ = "workflow_permissions"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    principal_type: Mapped[str] = mapped_column(String(20), nullable=False)
    principal_id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), nullable=False)
    permission: Mapped[str] = mapped_column(String(50), nullable=False)

    __table_args__ = (
        Index("ix_workflow_permissions_workflow_id", "workflow_id"),
        UniqueConstraint("workflow_id", "principal_type", "principal_id", "permission", name="uq_workflow_perm"),
    )


class WorkflowMetric(BaseModel):
    __tablename__ = "workflow_metrics"

    workflow_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflows.id", ondelete="CASCADE"), nullable=False
    )
    organization_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("organizations.id", ondelete="CASCADE"), nullable=False
    )
    metric_date: Mapped[datetime] = mapped_column(DateTime(timezone=True), nullable=False)
    runs_total: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    runs_success: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    runs_failed: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    avg_duration_ms: Mapped[int | None] = mapped_column(Integer)
    ai_nodes_used: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)

    __table_args__ = (
        Index("ix_workflow_metrics_workflow_date", "workflow_id", "metric_date"),
        UniqueConstraint("workflow_id", "metric_date", name="uq_workflow_metric_date"),
    )


class WorkflowError(BaseModel):
    __tablename__ = "workflow_errors"

    execution_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True), ForeignKey("workflow_executions.id", ondelete="CASCADE"), nullable=False
    )
    node_key: Mapped[str | None] = mapped_column(String(100))
    error_code: Mapped[str] = mapped_column(String(50), nullable=False)
    error_message: Mapped[str] = mapped_column(Text, nullable=False)
    stack_trace: Mapped[str | None] = mapped_column(Text)
    retry_count: Mapped[int] = mapped_column(Integer, server_default="0", nullable=False)
    is_resolved: Mapped[bool] = mapped_column(Boolean, server_default="false", nullable=False)

    __table_args__ = (Index("ix_workflow_errors_execution_id", "execution_id"),)