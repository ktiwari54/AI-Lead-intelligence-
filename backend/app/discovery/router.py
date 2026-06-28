from __future__ import annotations

from typing import Any
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, status
from pydantic import BaseModel
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.deps import get_current_user
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.discovery import service
from backend.app.discovery.schemas import DiscoveryJobResponse, DiscoveryRequest, DiscoveryResultResponse
from backend.database import get_db

router = APIRouter(prefix="/discovery", tags=["discovery"])


class ExecuteDiscoveryBody(DiscoveryRequest):
    async_mode: bool = True


class PreviewRequest(BaseModel):
    query: str


@router.post("/execute", response_model=APIResponse)
async def execute_discovery(
    body: ExecuteDiscoveryBody,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    result = await service.execute_discovery(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        request=body,
        async_mode=body.async_mode,
    )
    if isinstance(result, DiscoveryResultResponse):
        return APIResponse(data=result.model_dump())
    return APIResponse(
        data={**result.model_dump(), "poll_url": f"/api/v1/discovery/jobs/{result.id}"},
        message="Discovery job queued",
    )


@router.get("/jobs", response_model=PaginatedResponse)
async def list_jobs(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    status: str | None = None,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    jobs, total = await service.list_jobs(
        db, current_user.organization_id, status=status, page=page, page_size=page_size
    )
    return PaginatedResponse.create(
        data=[j.model_dump() for j in jobs], total=total, page=page, per_page=page_size
    )


@router.get("/jobs/{job_id}", response_model=APIResponse)
async def get_job(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    job = await service.get_job(db, job_id, current_user.organization_id)
    if not job:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
    return APIResponse(data=job.model_dump())


@router.get("/jobs/{job_id}/results", response_model=APIResponse)
async def get_job_results(
    job_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    results = await service.get_job_results(db, job_id, current_user.organization_id)
    if results is None:
        job = await service.get_job(db, job_id, current_user.organization_id)
        if not job:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Job not found")
        if job.status in ("pending", "running"):
            return APIResponse(
                data={"status": job.status, "stages": job.stages, "progress_pct": job.progress_pct},
                message="Job still in progress",
            )
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Results not found")
    return APIResponse(data=results.model_dump())


@router.get("/connectors", response_model=APIResponse)
async def list_connectors(current_user=Depends(get_current_user)):
    return APIResponse(data=service.list_connectors(current_user.organization_id))


@router.get("/connectors/{name}/health", response_model=APIResponse)
async def get_connector_health(name: str, current_user=Depends(get_current_user)):
    return APIResponse(data=service.connector_health(name))


@router.post("/preview", response_model=APIResponse)
async def preview_query(body: PreviewRequest, current_user=Depends(get_current_user)):
    lower = body.query.lower()
    entity_type = "contact" if any(k in lower for k in ("cto", "vp ", "director", "contact")) else "company"
    if "compan" in lower or "startup" in lower:
        entity_type = "company" if entity_type != "contact" else "both"

    intent: dict[str, Any] = {
        "entity_type": entity_type,
        "filters": {"q": body.query},
        "suggested_connectors": ["apollo", "clearbit"],
        "estimated_credits": 3,
        "raw_query": body.query,
    }
    return APIResponse(data={"intent": intent, "query": body.query})