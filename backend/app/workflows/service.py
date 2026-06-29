from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.admin.models import Workflow, WorkflowExecution
from backend.app.workflows import repository as repo
from backend.app.workflows.constants import OrchestrationMode
from backend.app.workflows.engine import WorkflowCompiler, WorkflowExecutor, WorkflowValidator
from backend.app.workflows.engine.orchestrator import hybrid_orchestrator
from backend.app.workflows.orchestration import MODE_PROFILES, infer_orchestration_mode, list_mode_catalog
from backend.app.workflows.schemas import (
    WorkflowAnalyticsResponse,
    WorkflowCreateRequest,
    WorkflowExecuteRequest,
    WorkflowResponse,
    WorkflowUpdateRequest,
    WorkflowValidateResponse,
    WorkflowVersionResponse,
)
from backend.infrastructure.messaging.event_bus import DomainEvent, EventEnvelope, EventBus

_compiler = WorkflowCompiler()
_validator = WorkflowValidator()
_executor = WorkflowExecutor()


def _to_response(wf: Workflow, version_number: int | None = None) -> WorkflowResponse:
    status = "published" if wf.is_active else "draft"
    mode = getattr(wf, "orchestration_mode", OrchestrationMode.EVENT_DRIVEN.value)
    profile = MODE_PROFILES.get(OrchestrationMode(mode))
    return WorkflowResponse(
        id=wf.id,
        organization_id=wf.organization_id,
        name=wf.name,
        description=wf.description,
        orchestration_mode=mode,
        orchestration_mode_label=profile.display_name if profile else mode,
        trigger_type=wf.trigger_type,
        trigger_config=wf.trigger_config or {},
        steps=wf.steps or [],
        is_active=wf.is_active,
        run_count=wf.run_count,
        status=status,
        current_version=version_number,
        created_at=wf.created_at,
        updated_at=wf.updated_at,
    )


def _canvas_from_request(body: WorkflowCreateRequest | WorkflowUpdateRequest) -> dict[str, Any] | None:
    if body.canvas:
        return body.canvas.model_dump()
    return None


def get_orchestration_catalog() -> list[dict]:
    return list_mode_catalog()


async def list_workflows(
    db: AsyncSession,
    org_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 25,
    is_active: bool | None = None,
    orchestration_mode: str | None = None,
) -> tuple[list[WorkflowResponse], int]:
    workflows, total = await repo.list_workflows(
        db,
        org_id,
        page=page,
        page_size=page_size,
        is_active=is_active,
        orchestration_mode=orchestration_mode,
    )
    responses = []
    for wf in workflows:
        ver = await repo.get_latest_version(db, wf.id)
        responses.append(_to_response(wf, ver.version_number if ver else None))
    return responses, total


async def get_workflow(db: AsyncSession, workflow_id: uuid.UUID, org_id: uuid.UUID) -> WorkflowResponse | None:
    wf = await repo.get_workflow(db, workflow_id, org_id)
    if not wf:
        return None
    ver = await repo.get_latest_version(db, wf.id)
    return _to_response(wf, ver.version_number if ver else None)


async def create_workflow(
    db: AsyncSession,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    body: WorkflowCreateRequest,
) -> WorkflowResponse:
    canvas = _canvas_from_request(body)
    steps = body.steps or []

    orchestration_mode = body.orchestration_mode
    if body.template_slug:
        tmpl = await repo.get_template_by_slug(db, body.template_slug)
        if tmpl:
            canvas = tmpl.canvas
            steps = []
            if not orchestration_mode and getattr(tmpl, "orchestration_mode", None):
                orchestration_mode = OrchestrationMode(tmpl.orchestration_mode)

    mode = infer_orchestration_mode(
        trigger_type=body.trigger.type,
        canvas=canvas,
        steps=steps,
        explicit_mode=orchestration_mode.value if orchestration_mode else None,
    )

    validation = _validator.validate(
        canvas=canvas,
        steps=steps,
        trigger_type=body.trigger.type,
        orchestration_mode=mode,
    )
    if not validation["valid"]:
        raise ValueError("; ".join(validation["errors"]))

    plan = _compiler.compile(
        trigger_type=body.trigger.type,
        trigger_config=body.trigger.config,
        canvas=canvas,
        steps=steps,
    )

    wf = await repo.create_workflow(
        db,
        organization_id=org_id,
        created_by=user_id,
        name=body.name,
        description=body.description,
        trigger_type=body.trigger.type,
        trigger_config=body.trigger.config,
        steps=steps or plan.get("nodes", []),
        orchestration_mode=mode.value,
        is_active=body.is_active,
    )

    await repo.create_version(
        db,
        workflow_id=wf.id,
        version_number=1,
        status="published" if body.is_active else "draft",
        canvas=canvas or {"nodes": plan.get("nodes", []), "edges": plan.get("edges", [])},
        compiled_plan=plan,
        published_at=datetime.now(timezone.utc) if body.is_active else None,
        published_by=user_id if body.is_active else None,
    )

    await db.commit()
    return _to_response(wf, 1)


async def update_workflow(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    body: WorkflowUpdateRequest,
) -> WorkflowResponse | None:
    wf = await repo.get_workflow(db, workflow_id, org_id)
    if not wf:
        return None

    canvas = _canvas_from_request(body)
    steps = body.steps

    mode = (
        body.orchestration_mode
        or OrchestrationMode(getattr(wf, "orchestration_mode", OrchestrationMode.EVENT_DRIVEN.value))
    )
    if body.trigger or body.orchestration_mode or canvas or steps:
        mode = infer_orchestration_mode(
            trigger_type=body.trigger.type if body.trigger else wf.trigger_type,
            canvas=canvas,
            steps=steps or wf.steps,
            explicit_mode=mode.value if isinstance(mode, OrchestrationMode) else str(mode),
        )

    if canvas or steps or body.trigger or body.orchestration_mode:
        sched = await repo.get_schedule(db, wf.id)
        validation = _validator.validate(
            canvas=canvas,
            steps=steps or wf.steps,
            trigger_type=body.trigger.type if body.trigger else wf.trigger_type,
            orchestration_mode=mode,
            has_schedule=sched is not None and sched.is_active,
        )
        if not validation["valid"]:
            raise ValueError("; ".join(validation["errors"]))

    updates: dict[str, Any] = {}
    if body.name is not None:
        updates["name"] = body.name
    if body.description is not None:
        updates["description"] = body.description
    if body.is_active is not None:
        updates["is_active"] = body.is_active
    if body.trigger:
        updates["trigger_type"] = body.trigger.type
        updates["trigger_config"] = body.trigger.config
    if steps is not None:
        updates["steps"] = steps
    if body.orchestration_mode or body.trigger or canvas or steps:
        updates["orchestration_mode"] = mode.value if isinstance(mode, OrchestrationMode) else mode

    await repo.update_workflow(db, wf, **updates)

    if canvas or steps or body.trigger:
        latest = await repo.get_latest_version(db, wf.id)
        next_ver = (latest.version_number + 1) if latest else 1
        plan = _compiler.compile(
            trigger_type=body.trigger.type if body.trigger else wf.trigger_type,
            trigger_config=body.trigger.config if body.trigger else (wf.trigger_config or {}),
            canvas=canvas,
            steps=steps or wf.steps,
        )
        await repo.create_version(
            db,
            workflow_id=wf.id,
            version_number=next_ver,
            status="published" if wf.is_active else "draft",
            canvas=canvas or {"nodes": plan.get("nodes", []), "edges": plan.get("edges", [])},
            compiled_plan=plan,
        )

    await db.commit()
    ver = await repo.get_latest_version(db, wf.id)
    return _to_response(wf, ver.version_number if ver else None)


async def delete_workflow(db: AsyncSession, workflow_id: uuid.UUID, org_id: uuid.UUID) -> bool:
    wf = await repo.get_workflow(db, workflow_id, org_id)
    if not wf:
        return False
    await repo.soft_delete_workflow(db, wf)
    await db.commit()
    return True


async def validate_workflow(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    org_id: uuid.UUID,
) -> WorkflowValidateResponse | None:
    wf = await repo.get_workflow(db, workflow_id, org_id)
    if not wf:
        return None
    ver = await repo.get_latest_version(db, wf.id)
    canvas = ver.canvas if ver else None
    sched = await repo.get_schedule(db, wf.id)
    validation = _validator.validate(
        canvas=canvas,
        steps=wf.steps,
        trigger_type=wf.trigger_type,
        orchestration_mode=getattr(wf, "orchestration_mode", OrchestrationMode.EVENT_DRIVEN.value),
        has_schedule=sched is not None and sched.is_active,
    )
    plan = None
    if validation["valid"]:
        plan = _compiler.compile(
            trigger_type=wf.trigger_type,
            trigger_config=wf.trigger_config or {},
            canvas=canvas,
            steps=wf.steps,
        )
    return WorkflowValidateResponse(
        valid=validation["valid"],
        errors=validation["errors"],
        warnings=validation.get("warnings", []),
        compiled_plan=plan,
    )


async def publish_workflow(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
) -> WorkflowResponse | None:
    wf = await repo.get_workflow(db, workflow_id, org_id)
    if not wf:
        return None
    validation = await validate_workflow(db, workflow_id, org_id)
    if not validation or not validation.valid:
        raise ValueError("Workflow validation failed")

    await repo.update_workflow(db, wf, is_active=True)
    ver = await repo.get_latest_version(db, wf.id)
    if ver:
        ver.status = "published"
        ver.published_at = datetime.now(timezone.utc)
        ver.published_by = user_id
    await db.commit()
    return _to_response(wf, ver.version_number if ver else None)


async def execute_workflow(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    org_id: uuid.UUID,
    user_id: uuid.UUID | None,
    body: WorkflowExecuteRequest,
    event_bus: EventBus | None = None,
) -> WorkflowExecution:
    wf = await repo.get_workflow(db, workflow_id, org_id)
    if not wf:
        raise ValueError("Workflow not found")
    if not wf.is_active:
        raise ValueError("Workflow is not active")

    mode = OrchestrationMode(getattr(wf, "orchestration_mode", OrchestrationMode.EVENT_DRIVEN.value))
    trigger_data = {
        "entity_type": body.entity_type,
        "entity_id": str(body.entity_id) if body.entity_id else None,
        **body.payload,
        "triggered_by": str(user_id) if user_id else None,
        "trigger_type": "manual",
        "orchestration_mode": mode.value,
    }

    execution = await repo.create_execution(
        db,
        workflow_id=wf.id,
        status="pending",
        trigger_data=trigger_data,
        step_results=[],
    )
    await db.commit()

    if body.async_mode:
        await hybrid_orchestrator.dispatch(
            mode,
            workflow_id=wf.id,
            org_id=org_id,
            execution_id=execution.id,
            trigger_data=trigger_data,
            async_mode=True,
        )
        return execution

    result = await _run_execution(db, execution.id, org_id, user_id, event_bus=event_bus, mode=mode)
    return result


async def _run_execution(
    db: AsyncSession,
    execution_id: uuid.UUID,
    org_id: uuid.UUID,
    user_id: uuid.UUID | None,
    event_bus: EventBus | None = None,
    mode: OrchestrationMode | None = None,
) -> WorkflowExecution:
    execution = await repo.get_execution(db, execution_id, org_id)
    if not execution:
        raise ValueError("Execution not found")

    wf = execution.workflow
    mode = mode or OrchestrationMode(getattr(wf, "orchestration_mode", OrchestrationMode.EVENT_DRIVEN.value))
    ver = await repo.get_latest_version(db, wf.id)
    plan = (ver.compiled_plan if ver and ver.compiled_plan else None) or _compiler.compile(
        trigger_type=wf.trigger_type,
        trigger_config=wf.trigger_config or {},
        canvas=ver.canvas if ver else None,
        steps=wf.steps,
    )

    await repo.update_execution(db, execution, status="running")
    await db.commit()

    outcome = await _executor.execute(
        plan,
        org_id=org_id,
        user_id=user_id,
        trigger_data=execution.trigger_data or {},
        execution_id=execution.id,
        orchestration_mode=mode,
    )

    final_status = outcome["status"]
    if final_status == "waiting" and mode == OrchestrationMode.HUMAN_IN_THE_LOOP:
        final_status = hybrid_orchestrator.execution_status_on_approval_wait(mode)

    await repo.update_execution(
        db,
        execution,
        status=final_status,
        step_results=outcome["step_results"],
        error_message=outcome.get("error_message"),
    )
    await repo.increment_run_count(db, wf.id)
    await repo.add_execution_log(
        db,
        execution_id=execution.id,
        level="info" if outcome["status"] == "completed" else "error",
        message=f"Workflow execution {final_status} ({mode.value})",
        payload={"step_count": len(outcome["step_results"]), "orchestration_mode": mode.value},
    )
    await db.commit()

    if event_bus:
        await event_bus.publish(
            EventEnvelope.create(
                DomainEvent.WORKFLOW_EXECUTED,
                "workflow_execution",
                execution.id,
                org_id,
                {"workflow_id": str(wf.id), "status": outcome["status"]},
                actor_id=user_id,
            )
        )

    return execution


async def pause_execution(db: AsyncSession, execution_id: uuid.UUID, org_id: uuid.UUID) -> WorkflowExecution | None:
    execution = await repo.get_execution(db, execution_id, org_id)
    if not execution:
        return None
    await repo.update_execution(db, execution, status="paused")
    await db.commit()
    return execution


async def resume_execution(
    db: AsyncSession,
    execution_id: uuid.UUID,
    org_id: uuid.UUID,
    user_id: uuid.UUID | None,
) -> WorkflowExecution | None:
    execution = await repo.get_execution(db, execution_id, org_id)
    if not execution or execution.status not in ("paused", "waiting", "waiting_approval"):
        return None
    wf = execution.workflow
    mode = OrchestrationMode(getattr(wf, "orchestration_mode", OrchestrationMode.EVENT_DRIVEN.value))
    return await _run_execution(db, execution_id, org_id, user_id, mode=mode)


async def cancel_execution(db: AsyncSession, execution_id: uuid.UUID, org_id: uuid.UUID) -> WorkflowExecution | None:
    execution = await repo.get_execution(db, execution_id, org_id)
    if not execution:
        return None
    await repo.update_execution(db, execution, status="cancelled")
    await db.commit()
    return execution


async def list_versions(db: AsyncSession, workflow_id: uuid.UUID, org_id: uuid.UUID) -> list[WorkflowVersionResponse]:
    wf = await repo.get_workflow(db, workflow_id, org_id)
    if not wf:
        return []
    versions = await repo.list_versions(db, workflow_id)
    return [WorkflowVersionResponse.model_validate(v) for v in versions]


async def list_executions(
    db: AsyncSession,
    workflow_id: uuid.UUID,
    org_id: uuid.UUID,
    *,
    page: int = 1,
    page_size: int = 25,
    status: str | None = None,
):
    wf = await repo.get_workflow(db, workflow_id, org_id)
    if not wf:
        return [], 0
    return await repo.list_executions(db, workflow_id, page=page, page_size=page_size, status=status)


async def get_analytics(db: AsyncSession, org_id: uuid.UUID, days: int = 30) -> WorkflowAnalyticsResponse:
    data = await repo.get_analytics(db, org_id, days)
    return WorkflowAnalyticsResponse(**data)


async def handle_domain_event(
    db: AsyncSession,
    org_id: uuid.UUID,
    event_type: str,
    payload: dict[str, Any],
) -> list[uuid.UUID]:
    """Match active workflows to domain events and queue executions."""
    from backend.app.workflows.constants import TRIGGER_EVENT_MAP

    trigger = TRIGGER_EVENT_MAP.get(event_type)
    if not trigger:
        return []

    workflows = await repo.find_workflows_by_trigger(
        db,
        org_id,
        trigger.value,
        orchestration_modes=[
            OrchestrationMode.EVENT_DRIVEN.value,
            OrchestrationMode.HUMAN_IN_THE_LOOP.value,
        ],
    )
    execution_ids: list[uuid.UUID] = []
    for wf in workflows:
        mode = OrchestrationMode(getattr(wf, "orchestration_mode", OrchestrationMode.EVENT_DRIVEN.value))
        if not hybrid_orchestrator.should_process_event(mode):
            continue
        trigger_data = {"event_type": event_type, "orchestration_mode": mode.value, **payload}
        execution = await repo.create_execution(
            db,
            workflow_id=wf.id,
            status="pending",
            trigger_data=trigger_data,
            step_results=[],
        )
        execution_ids.append(execution.id)
        await hybrid_orchestrator.dispatch(
            mode,
            workflow_id=wf.id,
            org_id=org_id,
            execution_id=execution.id,
            trigger_data=trigger_data,
            async_mode=True,
        )

    if execution_ids:
        await db.commit()
    return execution_ids