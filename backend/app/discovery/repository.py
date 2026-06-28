from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.discovery.models import DiscoveryJob, DiscoveryJobHit
from backend.app.discovery.schemas import (
    DiscoveryJobResponse,
    DiscoveryRequest,
    DiscoveryResultHit,
    DiscoveryResultResponse,
)


def _job_to_response(job: DiscoveryJob) -> DiscoveryJobResponse:
    return DiscoveryJobResponse(
        id=job.id,
        status=job.status,  # type: ignore[arg-type]
        query=job.query,
        entity_type=job.entity_type,
        connectors_used=job.connectors_used or [],
        result_count=job.result_count,
        credits_used=job.credits_used or 0,
        started_at=job.started_at,
        completed_at=job.completed_at,
        error_message=job.error_message,
        stages=job.stages or {},
        progress_pct=_progress_from_stages(job.stages or {}, job.status),
    )


def _progress_from_stages(stages: dict[str, str], status: str) -> int:
    if status == "completed":
        return 100
    if status == "failed":
        return 0
    order = [
        "connector_execution",
        "normalization",
        "entity_resolution",
        "enrichment",
        "confidence",
    ]
    completed = sum(1 for s in order if stages.get(s) == "completed")
    current = sum(1 for s in order if stages.get(s) == "in_progress")
    return min(95, int((completed / len(order)) * 100) + (10 if current else 0))


async def create_job(
    db: AsyncSession,
    *,
    job_id: uuid.UUID,
    org_id: uuid.UUID,
    user_id: uuid.UUID | None,
    request: DiscoveryRequest,
) -> DiscoveryJob:
    job = DiscoveryJob(
        id=job_id,
        organization_id=org_id,
        user_id=user_id,
        status="pending",
        query=request.query,
        entity_type=request.entity_type,
        filters=request.filters,
        connectors_used=request.connectors or [],
        stages={
            "connector_execution": "pending",
            "normalization": "pending",
            "entity_resolution": "pending",
            "enrichment": "pending",
            "confidence": "pending",
        },
    )
    db.add(job)
    await db.flush()
    return job


async def get_job(db: AsyncSession, job_id: uuid.UUID, org_id: uuid.UUID) -> DiscoveryJob | None:
    result = await db.execute(
        select(DiscoveryJob).where(
            DiscoveryJob.id == job_id,
            DiscoveryJob.organization_id == org_id,
            DiscoveryJob.deleted_at.is_(None),
        )
    )
    return result.scalar_one_or_none()


async def update_job_status(
    db: AsyncSession,
    job: DiscoveryJob,
    *,
    status: str | None = None,
    stages: dict[str, str] | None = None,
    connectors_used: list[str] | None = None,
    error_message: str | None = None,
    started_at: datetime | None = None,
    completed_at: datetime | None = None,
) -> DiscoveryJob:
    if status:
        job.status = status
    if stages:
        job.stages = {**(job.stages or {}), **stages}
    if connectors_used is not None:
        job.connectors_used = connectors_used
    if error_message is not None:
        job.error_message = error_message
    if started_at:
        job.started_at = started_at
    if completed_at:
        job.completed_at = completed_at
    await db.flush()
    return job


async def save_job_results(
    db: AsyncSession,
    job: DiscoveryJob,
    result: DiscoveryResultResponse,
    *,
    status: Literal["completed", "failed", "partial"] = "completed",
) -> None:
    job.status = status
    job.result_count = result.total
    job.took_ms = result.took_ms
    job.credits_used = sum(c.get("credits_used", 0) for c in result.connectors)
    job.connectors_used = [c.get("name", "") for c in result.connectors if c.get("name")]
    job.completed_at = datetime.now(timezone.utc)
    job.stages = {
        **(job.stages or {}),
        "connector_execution": "completed",
        "normalization": "completed",
        "entity_resolution": "completed",
        "enrichment": "completed",
        "confidence": "completed",
    }

    for hit in result.hits:
        db.add(
            DiscoveryJobHit(
                id=hit.id,
                job_id=job.id,
                entity_type=hit.entity_type,
                confidence=hit.confidence,
                source_trust=hit.source_trust,
                field_completeness=hit.field_completeness,
                verification_status=hit.verification_status,
                data=hit.data,
                provenance=hit.provenance,
                explanation=hit.explanation,
            )
        )
    await db.flush()


async def get_job_results(db: AsyncSession, job_id: uuid.UUID, org_id: uuid.UUID) -> DiscoveryResultResponse | None:
    job = await get_job(db, job_id, org_id)
    if not job:
        return None

    result = await db.execute(
        select(DiscoveryJobHit)
        .where(DiscoveryJobHit.job_id == job_id, DiscoveryJobHit.deleted_at.is_(None))
        .order_by(DiscoveryJobHit.confidence.desc())
    )
    hit_rows = result.scalars().all()
    if not hit_rows and job.status not in ("completed", "partial"):
        return None

    hits = [
        DiscoveryResultHit(
            id=row.id,
            entity_type=row.entity_type,  # type: ignore[arg-type]
            confidence=float(row.confidence),
            source_trust=float(row.source_trust),
            field_completeness=float(row.field_completeness),
            verification_status=row.verification_status,
            data=row.data or {},
            provenance=row.provenance or [],
            explanation=row.explanation or {},
        )
        for row in hit_rows
    ]
    return DiscoveryResultResponse(
        job_id=job.id,
        total=job.result_count or len(hits),
        hits=hits,
        took_ms=job.took_ms or 0,
        connectors=[{"name": n, "success": True} for n in (job.connectors_used or [])],
    )


async def list_jobs(
    db: AsyncSession,
    org_id: uuid.UUID,
    *,
    status: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[DiscoveryJobResponse], int]:
    stmt = select(DiscoveryJob).where(
        DiscoveryJob.organization_id == org_id,
        DiscoveryJob.deleted_at.is_(None),
    )
    if status:
        stmt = stmt.where(DiscoveryJob.status == status)

    count_stmt = select(func.count()).select_from(stmt.subquery())
    total = (await db.execute(count_stmt)).scalar() or 0

    stmt = stmt.order_by(DiscoveryJob.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = (await db.execute(stmt)).scalars().all()
    return [_job_to_response(j) for j in rows], total