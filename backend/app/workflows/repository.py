from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.admin.models import Workflow, WorkflowExecution
from backend.app.workflows.models import (
    WorkflowApproval,
    WorkflowExecutionLog,
    WorkflowMetric,
    WorkflowSchedule,
    WorkflowTemplate,
    WorkflowVersion,
)


async def list_workflows(
    db: AsyncSession,
    org_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 25,
    is_active: bool | None = None,
    orchestration_mode: str | None = None,
) -> tuple[list[Workflow], int]:
    q = select(Workflow).where(
        Workflow.organization_id == org_id,
        Workflow.deleted_at.is_(None),
    )
    if is_active is not None:
        q = q.where(Workflow.is_active == is_active)
    if orchestration_mode:
        q = q.where(Workflow.orchestration_mode == orchestration_mode)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(Workflow.updated_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def get_workflow(db: AsyncSession, workflow_id: uuid.UUID, org_id: uuid.UUID) -> Workflow | None:
    result = await db.execute(
        select(Workflow).where(
            Workflow.id == workflow_id,
            Workflow.organization_id == org_id,
            Workflow.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def create_workflow(db: AsyncSession, **kwargs: Any) -> Workflow:
    wf = Workflow(**kwargs)
    db.add(wf)
    await db.flush()
    return wf


async def update_workflow(db: AsyncSession, workflow: Workflow, **kwargs: Any) -> Workflow:
    for key, val in kwargs.items():
        if val is not None and hasattr(workflow, key):
            setattr(workflow, key, val)
    await db.flush()
    return workflow


async def soft_delete_workflow(db: AsyncSession, workflow: Workflow) -> None:
    workflow.deleted_at = datetime.now(timezone.utc)
    workflow.is_active = False
    await db.flush()


async def create_version(db: AsyncSession, **kwargs: Any) -> WorkflowVersion:
    ver = WorkflowVersion(**kwargs)
    db.add(ver)
    await db.flush()
    return ver


async def get_latest_version(db: AsyncSession, workflow_id: uuid.UUID) -> WorkflowVersion | None:
    result = await db.execute(
        select(WorkflowVersion)
        .where(WorkflowVersion.workflow_id == workflow_id, WorkflowVersion.deleted_at.is_(None))
        .order_by(WorkflowVersion.version_number.desc())
        .limit(1)
    )
    return result.scalar_one_or_none()


async def list_versions(db: AsyncSession, workflow_id: uuid.UUID) -> list[WorkflowVersion]:
    result = await db.execute(
        select(WorkflowVersion)
        .where(WorkflowVersion.workflow_id == workflow_id, WorkflowVersion.deleted_at.is_(None))
        .order_by(WorkflowVersion.version_number.desc())
    )
    return list(result.scalars().all())


async def create_execution(db: AsyncSession, **kwargs: Any) -> WorkflowExecution:
    ex = WorkflowExecution(**kwargs)
    db.add(ex)
    await db.flush()
    return ex


async def get_execution(
    db: AsyncSession, execution_id: uuid.UUID, org_id: uuid.UUID | None = None
) -> WorkflowExecution | None:
    q = (
        select(WorkflowExecution)
        .join(Workflow)
        .where(WorkflowExecution.id == execution_id, WorkflowExecution.deleted_at.is_(None))
    )
    if org_id:
        q = q.where(Workflow.organization_id == org_id)
    result = await db.execute(q.options(selectinload(WorkflowExecution.workflow)))
    return result.scalar_one_or_none()


async def list_executions(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 25,
    status: str | None = None,
) -> tuple[list[WorkflowExecution], int]:
    q = select(WorkflowExecution).where(
        WorkflowExecution.workflow_id == workflow_id,
        WorkflowExecution.deleted_at.is_(None),
    )
    if status:
        q = q.where(WorkflowExecution.status == status)
    count_q = select(func.count()).select_from(q.subquery())
    total = (await db.execute(count_q)).scalar() or 0
    q = q.order_by(WorkflowExecution.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    result = await db.execute(q)
    return list(result.scalars().all()), total


async def update_execution(db: AsyncSession, execution: WorkflowExecution, **kwargs: Any) -> WorkflowExecution:
    for key, val in kwargs.items():
        if hasattr(execution, key):
            setattr(execution, key, val)
    await db.flush()
    return execution


async def add_execution_log(db: AsyncSession, **kwargs: Any) -> WorkflowExecutionLog:
    log = WorkflowExecutionLog(**kwargs)
    db.add(log)
    await db.flush()
    return log


async def list_templates(
    db: AsyncSession,
    org_id: uuid.UUID | None = None,
    category: str | None = None,
) -> list[WorkflowTemplate]:
    q = select(WorkflowTemplate).where(WorkflowTemplate.deleted_at.is_(None))
    if org_id:
        q = q.where((WorkflowTemplate.organization_id == org_id) | (WorkflowTemplate.is_system == True))  # noqa: E712
    if category:
        q = q.where(WorkflowTemplate.category == category)
    result = await db.execute(q.order_by(WorkflowTemplate.usage_count.desc()))
    return list(result.scalars().all())


async def get_template_by_slug(db: AsyncSession, slug: str) -> WorkflowTemplate | None:
    result = await db.execute(
        select(WorkflowTemplate).where(WorkflowTemplate.slug == slug, WorkflowTemplate.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def get_schedule(db: AsyncSession, workflow_id: uuid.UUID) -> WorkflowSchedule | None:
    result = await db.execute(
        select(WorkflowSchedule).where(
            WorkflowSchedule.workflow_id == workflow_id,
            WorkflowSchedule.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def upsert_schedule(db: AsyncSession, workflow_id: uuid.UUID, org_id: uuid.UUID, **kwargs: Any) -> WorkflowSchedule:
    existing = await get_schedule(db, workflow_id)
    if existing:
        for k, v in kwargs.items():
            setattr(existing, k, v)
        await db.flush()
        return existing
    sched = WorkflowSchedule(workflow_id=workflow_id, organization_id=org_id, **kwargs)
    db.add(sched)
    await db.flush()
    return sched


async def list_pending_approvals(db: AsyncSession, user_id: uuid.UUID) -> list[WorkflowApproval]:
    result = await db.execute(
        select(WorkflowApproval).where(
            WorkflowApproval.approver_id == user_id,
            WorkflowApproval.status == "pending",
            WorkflowApproval.deleted_at.is_(None),
        )
    )
    return list(result.scalars().all())


async def get_approval(db: AsyncSession, approval_id: uuid.UUID) -> WorkflowApproval | None:
    result = await db.execute(
        select(WorkflowApproval).where(WorkflowApproval.id == approval_id, WorkflowApproval.deleted_at.is_(None))
    )
    return result.scalar_one_or_none()


async def increment_run_count(db: AsyncSession, workflow_id: uuid.UUID) -> None:
    await db.execute(
        update(Workflow).where(Workflow.id == workflow_id).values(run_count=Workflow.run_count + 1)
    )


async def get_analytics(db: AsyncSession, org_id: uuid.UUID, days: int = 30) -> dict[str, Any]:
    since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    result = await db.execute(
        select(
            func.coalesce(func.sum(WorkflowMetric.runs_total), 0),
            func.coalesce(func.sum(WorkflowMetric.runs_success), 0),
            func.coalesce(func.sum(WorkflowMetric.runs_failed), 0),
            func.avg(WorkflowMetric.avg_duration_ms),
            func.coalesce(func.sum(WorkflowMetric.ai_nodes_used), 0),
        ).where(
            WorkflowMetric.organization_id == org_id,
            WorkflowMetric.metric_date >= since,
        )
    )
    row = result.one()
    runs_total, runs_success, runs_failed, avg_dur, ai_usage = row
    runs_total = int(runs_total or 0)
    runs_success = int(runs_success or 0)
    runs_failed = int(runs_failed or 0)
    success_rate = (runs_success / runs_total * 100) if runs_total else 0.0

    tmpl_result = await db.execute(
        select(WorkflowTemplate.slug, WorkflowTemplate.name, WorkflowTemplate.usage_count)
        .where(WorkflowTemplate.deleted_at.is_(None))
        .order_by(WorkflowTemplate.usage_count.desc())
        .limit(5)
    )
    templates = [{"slug": r[0], "name": r[1], "usage_count": r[2]} for r in tmpl_result.all()]

    return {
        "runs_total": runs_total,
        "runs_success": runs_success,
        "runs_failed": runs_failed,
        "success_rate": round(success_rate, 2),
        "avg_duration_ms": float(avg_dur) if avg_dur else None,
        "ai_node_usage": int(ai_usage or 0),
        "most_used_templates": templates,
        "approval_metrics": {"pending": 0, "approved": 0, "rejected": 0},
        "period_days": days,
    }


async def find_workflows_by_trigger(
    db: AsyncSession,
    org_id: uuid.UUID,
    trigger_type: str,
    *,
    orchestration_modes: list[str] | None = None,
) -> list[Workflow]:
    q = select(Workflow).where(
        Workflow.organization_id == org_id,
        Workflow.trigger_type == trigger_type,
        Workflow.is_active == True,  # noqa: E712
        Workflow.deleted_at.is_(None),
    )
    if orchestration_modes:
        q = q.where(Workflow.orchestration_mode.in_(orchestration_modes))
    result = await db.execute(q)
    return list(result.scalars().all())


async def find_scheduled_workflows(db: AsyncSession, org_id: uuid.UUID | None = None) -> list[Workflow]:
    q = select(Workflow).where(
        Workflow.orchestration_mode == "scheduled",
        Workflow.is_active == True,  # noqa: E712
        Workflow.deleted_at.is_(None),
    )
    if org_id:
        q = q.where(Workflow.organization_id == org_id)
    result = await db.execute(q)
    return list(result.scalars().all())