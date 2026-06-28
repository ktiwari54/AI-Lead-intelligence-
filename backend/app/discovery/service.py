from __future__ import annotations

import uuid
from datetime import datetime, timezone
from typing import Any, Literal

from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.discovery import repository as repo
from backend.app.discovery.orchestrator import DiscoveryOrchestrator
from backend.app.discovery.schemas import (
    DiscoveryJobResponse,
    DiscoveryRequest,
    DiscoveryResultResponse,
)
from backend.connectors.registry import ConnectorRegistry
from backend.connectors.sdk.registry import SDKConnectorRegistry

_orchestrator = DiscoveryOrchestrator()

# In-memory fallback when DB unavailable (dev/tests)
_MEMORY_JOBS: dict[uuid.UUID, dict[str, Any]] = {}
_MEMORY_RESULTS: dict[uuid.UUID, DiscoveryResultResponse] = {}


def list_connectors(org_id: uuid.UUID) -> list[dict[str, Any]]:
    v2 = SDKConnectorRegistry.list_available()
    seen = {c["name"] for c in v2}
    merged = list(v2)
    for connector in ConnectorRegistry.list_available():
        if connector["name"] not in seen:
            merged.append({**connector, "sdk_version": "1.0"})
    return merged


async def execute_discovery(
    db: AsyncSession | None,
    org_id: uuid.UUID,
    user_id: uuid.UUID,
    request: DiscoveryRequest,
    *,
    async_mode: bool = True,
) -> DiscoveryJobResponse | DiscoveryResultResponse:
    job_id = uuid.uuid4()
    now = datetime.now(timezone.utc)

    if db:
        job = await repo.create_job(db, job_id=job_id, org_id=org_id, user_id=user_id, request=request)
        await db.commit()
    else:
        _MEMORY_JOBS[job_id] = {
            "id": job_id,
            "organization_id": org_id,
            "status": "pending",
            "query": request.query,
            "entity_type": request.entity_type,
            "stages": {},
            "created_at": now,
        }

    if async_mode:
        from backend.workers.tasks.discovery import run_discovery_job

        run_discovery_job.delay(str(job_id), str(org_id), request.model_dump())
        return DiscoveryJobResponse(
            id=job_id,
            status="pending",
            query=request.query,
            entity_type=request.entity_type,
            connectors_used=request.connectors or [],
            stages={
                "connector_execution": "pending",
                "normalization": "pending",
                "entity_resolution": "pending",
                "enrichment": "pending",
                "confidence": "pending",
            },
            progress_pct=0,
        )

    result = await _run_job(db, job_id, org_id, request)
    return result


async def _run_job(
    db: AsyncSession | None,
    job_id: uuid.UUID,
    org_id: uuid.UUID,
    request: DiscoveryRequest,
) -> DiscoveryResultResponse:
    now = datetime.now(timezone.utc)

    async def on_stage(stage: str, status: str) -> None:
        if db:
            job = await repo.get_job(db, job_id, org_id)
            if job:
                await repo.update_job_status(db, job, stages={stage: status}, status="running" if status == "in_progress" else job.status)
                if status == "in_progress" and not job.started_at:
                    job.started_at = now
                await db.commit()

    if db:
        job = await repo.get_job(db, job_id, org_id)
        if job:
            await repo.update_job_status(db, job, status="running", started_at=now)
            await db.commit()

    try:
        result = await _orchestrator.execute(org_id, request, job_id=job_id, on_stage=on_stage)
        if db:
            job = await repo.get_job(db, job_id, org_id)
            if job:
                failed_connectors = [c for c in result.connectors if not c.get("success")]
                status: Literal["completed", "partial", "failed"] = "completed"
                if failed_connectors and result.total > 0:
                    status = "partial"
                await repo.save_job_results(db, job, result, status=status)
                await db.commit()
        else:
            _MEMORY_JOBS[job_id].update({"status": "completed", "result_count": result.total})
            _MEMORY_RESULTS[job_id] = result
        return result
    except Exception as exc:
        if db:
            job = await repo.get_job(db, job_id, org_id)
            if job:
                await repo.update_job_status(db, job, status="failed", error_message=str(exc), completed_at=datetime.now(timezone.utc))
                await db.commit()
        else:
            _MEMORY_JOBS[job_id].update({"status": "failed", "error_message": str(exc)})
        raise


async def get_job(db: AsyncSession | None, job_id: uuid.UUID, org_id: uuid.UUID) -> DiscoveryJobResponse | None:
    if db:
        job = await repo.get_job(db, job_id, org_id)
        return repo._job_to_response(job) if job else None
    mem = _MEMORY_JOBS.get(job_id)
    if not mem or mem.get("organization_id") != org_id:
        return None
    return DiscoveryJobResponse(
        id=job_id,
        status=mem.get("status", "pending"),
        query=mem.get("query"),
        entity_type=mem.get("entity_type", "both"),
        connectors_used=mem.get("connectors_used", []),
        result_count=mem.get("result_count"),
        stages=mem.get("stages", {}),
        progress_pct=mem.get("progress_pct", 0),
    )


async def get_job_results(db: AsyncSession | None, job_id: uuid.UUID, org_id: uuid.UUID) -> DiscoveryResultResponse | None:
    if db:
        return await repo.get_job_results(db, job_id, org_id)
    if _MEMORY_JOBS.get(job_id, {}).get("organization_id") != org_id:
        return None
    return _MEMORY_RESULTS.get(job_id)


async def list_jobs(
    db: AsyncSession | None,
    org_id: uuid.UUID,
    *,
    status: str | None = None,
    page: int = 1,
    page_size: int = 25,
) -> tuple[list[DiscoveryJobResponse], int]:
    if db:
        return await repo.list_jobs(db, org_id, status=status, page=page, page_size=page_size)
    items = [j for j in _MEMORY_JOBS.values() if j.get("organization_id") == org_id]
    if status:
        items = [j for j in items if j.get("status") == status]
    total = len(items)
    start = (page - 1) * page_size
    page_items = items[start : start + page_size]
    return [
        DiscoveryJobResponse(
            id=j["id"],
            status=j.get("status", "pending"),
            query=j.get("query"),
            entity_type=j.get("entity_type", "both"),
            connectors_used=j.get("connectors_used", []),
            result_count=j.get("result_count"),
            stages=j.get("stages", {}),
        )
        for j in page_items
    ], total


def connector_health(name: str, config: dict[str, Any] | None = None) -> dict[str, Any]:
    sdk = SDKConnectorRegistry.get(name, config)
    if sdk:
        health = sdk.health_check()
        return {"name": name, "healthy": health.healthy, "latency_ms": health.latency_ms, "message": health.message, "sdk_version": "2.0"}
    connector = ConnectorRegistry.get(name, config)
    if not connector:
        return {"name": name, "healthy": False, "message": "Connector not registered"}
    return {"name": name, **connector.health_check(), "sdk_version": "1.0"}