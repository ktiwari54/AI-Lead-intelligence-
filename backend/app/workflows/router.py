from __future__ import annotations

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.deps import get_current_user
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.workflows import service
from backend.app.workflows.schemas import (
    WorkflowAnalyticsResponse,
    WorkflowApprovalRequest,
    WorkflowCreateRequest,
    WorkflowExecuteRequest,
    WorkflowResponse,
    WorkflowScheduleRequest,
    WorkflowTemplateResponse,
    WorkflowUpdateRequest,
    WorkflowValidateResponse,
    WorkflowVersionResponse,
)
from backend.database import get_db

router = APIRouter(prefix="/workflows", tags=["Workflows"])


def _check_permission(user, permission: str) -> None:
    role_names = {r.name.lower() for r in (user.roles or [])}
    if "admin" in role_names or "owner" in role_names or "manager" in role_names:
        return
    if permission == "workflows:read":
        return
    raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail=f"Requires {permission}")


@router.get("", response_model=PaginatedResponse)
async def list_workflows(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    is_active: bool | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:read")
    workflows, total = await service.list_workflows(
        db, current_user.organization_id, page=page, page_size=page_size, is_active=is_active
    )
    return PaginatedResponse.create(
        data=[w.model_dump() for w in workflows], total=total, page=page, per_page=page_size
    )


@router.post("", response_model=APIResponse, status_code=status.HTTP_201_CREATED)
async def create_workflow(
    body: WorkflowCreateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:write")
    try:
        wf = await service.create_workflow(db, current_user.organization_id, current_user.id, body)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return APIResponse(data=wf.model_dump(), message="Workflow created")


@router.get("/templates", response_model=APIResponse)
async def list_templates(
    category: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:read")
    from backend.app.workflows import repository as repo

    templates = await repo.list_templates(db, current_user.organization_id, category=category)
    return APIResponse(data=[WorkflowTemplateResponse.model_validate(t).model_dump() for t in templates])


@router.get("/analytics", response_model=APIResponse)
async def workflow_analytics(
    days: int = Query(30, ge=1, le=365),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:read")
    analytics = await service.get_analytics(db, current_user.organization_id, days=days)
    return APIResponse(data=analytics.model_dump())


@router.get("/executions/{execution_id}", response_model=APIResponse)
async def get_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:read")
    from backend.app.workflows import repository as repo

    execution = await repo.get_execution(db, execution_id, current_user.organization_id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return APIResponse(
        data={
            "id": str(execution.id),
            "workflow_id": str(execution.workflow_id),
            "status": execution.status,
            "trigger_data": execution.trigger_data,
            "step_results": execution.step_results,
            "error_message": execution.error_message,
            "created_at": execution.created_at.isoformat(),
        }
    )


@router.post("/executions/{execution_id}/pause", response_model=APIResponse)
async def pause_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:execute")
    execution = await service.pause_execution(db, execution_id, current_user.organization_id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return APIResponse(data={"status": execution.status})


@router.post("/executions/{execution_id}/resume", response_model=APIResponse)
async def resume_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:execute")
    execution = await service.resume_execution(
        db, execution_id, current_user.organization_id, current_user.id
    )
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return APIResponse(data={"status": execution.status})


@router.post("/executions/{execution_id}/cancel", response_model=APIResponse)
async def cancel_execution(
    execution_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:execute")
    execution = await service.cancel_execution(db, execution_id, current_user.organization_id)
    if not execution:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Execution not found")
    return APIResponse(data={"status": execution.status})


@router.post("/executions/{execution_id}/approvals/{approval_id}/approve", response_model=APIResponse)
async def approve_step(
    execution_id: UUID,
    approval_id: UUID,
    body: WorkflowApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:execute")
    from datetime import datetime, timezone
    from backend.app.workflows import repository as repo

    approval = await repo.get_approval(db, approval_id)
    if not approval or str(approval.execution_id) != str(execution_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    approval.status = "approved"
    approval.comment = body.comment
    approval.decided_at = datetime.now(timezone.utc)
    approval.approver_id = current_user.id
    await db.commit()
    return APIResponse(data={"status": "approved"})


@router.post("/executions/{execution_id}/approvals/{approval_id}/reject", response_model=APIResponse)
async def reject_step(
    execution_id: UUID,
    approval_id: UUID,
    body: WorkflowApprovalRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:execute")
    from datetime import datetime, timezone
    from backend.app.workflows import repository as repo

    approval = await repo.get_approval(db, approval_id)
    if not approval or str(approval.execution_id) != str(execution_id):
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Approval not found")
    approval.status = "rejected"
    approval.comment = body.comment
    approval.decided_at = datetime.now(timezone.utc)
    approval.approver_id = current_user.id
    await db.commit()
    return APIResponse(data={"status": "rejected"})


@router.get("/{workflow_id}", response_model=APIResponse)
async def get_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:read")
    wf = await service.get_workflow(db, workflow_id, current_user.organization_id)
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return APIResponse(data=wf.model_dump())


@router.patch("/{workflow_id}", response_model=APIResponse)
async def update_workflow(
    workflow_id: UUID,
    body: WorkflowUpdateRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:write")
    try:
        wf = await service.update_workflow(
            db, workflow_id, current_user.organization_id, current_user.id, body
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return APIResponse(data=wf.model_dump(), message="Workflow updated")


@router.delete("/{workflow_id}", response_model=APIResponse)
async def delete_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:write")
    deleted = await service.delete_workflow(db, workflow_id, current_user.organization_id)
    if not deleted:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return APIResponse(message="Workflow deleted")


@router.post("/{workflow_id}/publish", response_model=APIResponse)
async def publish_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:write")
    try:
        wf = await service.publish_workflow(
            db, workflow_id, current_user.organization_id, current_user.id
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return APIResponse(data=wf.model_dump(), message="Workflow published")


@router.post("/{workflow_id}/validate", response_model=APIResponse)
async def validate_workflow(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:read")
    result = await service.validate_workflow(db, workflow_id, current_user.organization_id)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    return APIResponse(data=result.model_dump())


@router.get("/{workflow_id}/versions", response_model=APIResponse)
async def list_versions(
    workflow_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:read")
    versions = await service.list_versions(db, workflow_id, current_user.organization_id)
    return APIResponse(data=[v.model_dump() for v in versions])


@router.get("/{workflow_id}/executions", response_model=PaginatedResponse)
async def list_executions(
    workflow_id: UUID,
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status_filter: str | None = Query(None, alias="status"),
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:read")
    executions, total = await service.list_executions(
        db,
        workflow_id,
        current_user.organization_id,
        page=page,
        page_size=page_size,
        status=status_filter,
    )
    if total == 0:
        wf = await service.get_workflow(db, workflow_id, current_user.organization_id)
        if not wf:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    data = [
        {
            "id": str(e.id),
            "workflow_id": str(e.workflow_id),
            "status": e.status,
            "trigger_data": e.trigger_data,
            "step_results": e.step_results,
            "error_message": e.error_message,
            "created_at": e.created_at.isoformat(),
        }
        for e in executions
    ]
    return PaginatedResponse.create(data=data, total=total, page=page, per_page=page_size)


@router.post("/{workflow_id}/execute", response_model=APIResponse, status_code=status.HTTP_202_ACCEPTED)
async def execute_workflow(
    workflow_id: UUID,
    body: WorkflowExecuteRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:execute")
    try:
        execution = await service.execute_workflow(
            db,
            workflow_id,
            current_user.organization_id,
            current_user.id,
            body,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return APIResponse(
        data={
            "execution_id": str(execution.id),
            "status": execution.status,
            "poll_url": f"/api/v1/workflows/executions/{execution.id}",
        },
        message="Workflow execution started",
    )


@router.put("/{workflow_id}/schedule", response_model=APIResponse)
async def upsert_schedule(
    workflow_id: UUID,
    body: WorkflowScheduleRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    _check_permission(current_user, "workflows:write")
    from backend.app.workflows import repository as repo

    wf = await repo.get_workflow(db, workflow_id, current_user.organization_id)
    if not wf:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Workflow not found")
    sched = await repo.upsert_schedule(
        db,
        workflow_id,
        current_user.organization_id,
        schedule_type=body.schedule_type,
        cron_expression=body.cron_expression,
        timezone=body.timezone,
        config=body.config,
        is_active=body.is_active,
    )
    await db.commit()
    return APIResponse(data={"id": str(sched.id), "schedule_type": sched.schedule_type})