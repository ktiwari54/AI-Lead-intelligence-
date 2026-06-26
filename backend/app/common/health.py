"""Detailed health check with dependency probing."""
from __future__ import annotations
import time
from datetime import datetime, timezone

import asyncpg
from fastapi import APIRouter
from pydantic import BaseModel

from backend.config import get_settings

router = APIRouter(tags=["Health"])
settings = get_settings()


class ComponentHealth(BaseModel):
    status: str  # "healthy" | "degraded" | "unhealthy"
    latency_ms: float | None = None
    error: str | None = None
    details: dict = {}


class HealthResponse(BaseModel):
    status: str
    timestamp: datetime
    version: str = "1.0.0"
    components: dict[str, ComponentHealth]


async def _check_postgres() -> ComponentHealth:
    start = time.perf_counter()
    try:
        conn = await asyncpg.connect(
            settings.DATABASE_URL.replace("+asyncpg", ""),
            timeout=3,
        )
        await conn.fetchval("SELECT 1")
        await conn.close()
        return ComponentHealth(
            status="healthy",
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
        )
    except Exception as e:
        return ComponentHealth(status="unhealthy", error=str(e)[:100])


async def _check_redis() -> ComponentHealth:
    start = time.perf_counter()
    try:
        import redis.asyncio as aioredis
        r = aioredis.from_url(settings.REDIS_URL, socket_timeout=2)
        await r.ping()
        await r.aclose()
        return ComponentHealth(
            status="healthy",
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
        )
    except Exception as e:
        return ComponentHealth(status="unhealthy", error=str(e)[:100])


async def _check_opensearch() -> ComponentHealth:
    start = time.perf_counter()
    try:
        import httpx
        async with httpx.AsyncClient(timeout=3) as client:
            resp = await client.get(f"{settings.OPENSEARCH_URL}/_cluster/health")
        data = resp.json()
        status = "healthy" if data.get("status") in ("green", "yellow") else "degraded"
        return ComponentHealth(
            status=status,
            latency_ms=round((time.perf_counter() - start) * 1000, 2),
            details={"cluster_status": data.get("status")},
        )
    except Exception as e:
        return ComponentHealth(status="degraded", error=str(e)[:100])


@router.get("/health", response_model=HealthResponse)
async def health_check():
    """Detailed health check probing all dependencies."""
    import asyncio
    postgres, redis_check, opensearch = await asyncio.gather(
        _check_postgres(),
        _check_redis(),
        _check_opensearch(),
        return_exceptions=False,
    )

    components = {
        "postgres": postgres,
        "redis": redis_check,
        "opensearch": opensearch,
    }

    overall = "healthy"
    if any(c.status == "unhealthy" for c in components.values()):
        overall = "unhealthy"
    elif any(c.status == "degraded" for c in components.values()):
        overall = "degraded"

    return HealthResponse(
        status=overall,
        timestamp=datetime.now(timezone.utc),
        components=components,
    )


@router.get("/health/live")
async def liveness():
    """Kubernetes liveness probe - returns 200 if process is alive."""
    return {"status": "ok"}


@router.get("/health/ready")
async def readiness():
    """Kubernetes readiness probe - returns 200 only when DB is reachable."""
    pg = await _check_postgres()
    if pg.status == "unhealthy":
        from fastapi import HTTPException
        raise HTTPException(status_code=503, detail="Database unavailable")
    return {"status": "ready"}
