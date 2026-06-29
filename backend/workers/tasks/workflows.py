from __future__ import annotations

import asyncio
import uuid

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(bind=True, max_retries=3, name="workflows.run_execution")
def run_workflow_execution(self, execution_id: str, org_id: str, orchestration_mode: str | None = None):
    """Execute a workflow asynchronously via Celery."""
    logger.info(
        "Running workflow execution %s for org %s mode=%s",
        execution_id,
        org_id,
        orchestration_mode or "auto",
    )

    async def _execute():
        from backend.database import AsyncSessionLocal
        from backend.app.workflows import service
        from backend.app.workflows.constants import OrchestrationMode

        mode = OrchestrationMode(orchestration_mode) if orchestration_mode else None
        async with AsyncSessionLocal() as db:
            await service._run_execution(
                db,
                uuid.UUID(execution_id),
                uuid.UUID(org_id),
                user_id=None,
                mode=mode,
            )

    try:
        _run_async(_execute())
        return {"status": "completed", "execution_id": execution_id}
    except Exception as exc:
        logger.exception("Workflow execution failed: %s", exc)
        raise self.retry(exc=exc)


@shared_task(name="workflows.run_scheduled")
def run_scheduled_workflows():
    """Poll workflow_schedules and trigger due workflows."""
    logger.info("Checking scheduled workflows")

    async def _poll():
        from datetime import datetime, timezone
        from sqlalchemy import select
        from backend.database import AsyncSessionLocal
        from backend.app.workflows.models import WorkflowSchedule
        from backend.app.workflows import service
        from backend.app.workflows.schemas import WorkflowExecuteRequest

        now = datetime.now(timezone.utc)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(WorkflowSchedule).where(
                    WorkflowSchedule.is_active == True,  # noqa: E712
                    WorkflowSchedule.next_run_at <= now,
                    WorkflowSchedule.deleted_at.is_(None),
                )
            )
            schedules = result.scalars().all()
            for sched in schedules:
                from backend.app.workflows import repository as repo
                from backend.app.workflows.constants import OrchestrationMode

                wf = await repo.get_workflow(db, sched.workflow_id, sched.organization_id)
                if not wf or wf.orchestration_mode != OrchestrationMode.SCHEDULED.value:
                    continue
                await service.execute_workflow(
                    db,
                    sched.workflow_id,
                    sched.organization_id,
                    None,
                    WorkflowExecuteRequest(payload={"scheduled": True}, async_mode=True),
                )
                sched.last_run_at = now
            await db.commit()

    try:
        _run_async(_poll())
    except Exception as exc:
        logger.exception("Scheduled workflow poll failed: %s", exc)
        raise


@shared_task(name="workflows.process_domain_event")
def process_domain_event(org_id: str, event_type: str, payload: dict):
    """Trigger workflows matching a domain event."""

    async def _handle():
        from backend.database import AsyncSessionLocal
        from backend.app.workflows import service

        async with AsyncSessionLocal() as db:
            await service.handle_domain_event(db, uuid.UUID(org_id), event_type, payload)

    try:
        _run_async(_handle())
    except Exception as exc:
        logger.exception("Domain event workflow trigger failed: %s", exc)
        raise