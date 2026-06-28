"""Discovery Celery tasks — Phase 5 background workers."""

from __future__ import annotations

import logging
import uuid

from celery import shared_task

from backend.workers.async_runner import run_async_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, name="discovery.run_job")
def run_discovery_job(self, job_id: str, org_id: str, request_data: dict):
    """Execute a discovery job via the orchestrator with DB persistence."""

    async def _run():
        from backend.database import AsyncSessionLocal
        from backend.app.discovery.schemas import DiscoveryRequest
        from backend.app.discovery import service

        jid = uuid.UUID(job_id)
        oid = uuid.UUID(org_id)
        request = DiscoveryRequest(**request_data)

        async with AsyncSessionLocal() as db:
            try:
                result = await service._run_job(db, jid, oid, request)
                return {"job_id": job_id, "status": "completed", "total": result.total}
            except Exception as exc:
                logger.exception("Discovery job %s failed: %s", job_id, exc)
                raise

    try:
        return run_async_task(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)


@shared_task(name="discovery.run_scheduled")
def run_scheduled_searches():
    logger.info("Scheduled discovery scan — no saved searches configured yet")
    return {"scheduled": 0}


@shared_task(name="discovery.check_connector_health")
def check_connector_health():
    from backend.connectors.registry import ConnectorRegistry
    from backend.connectors.sdk.registry import SDKConnectorRegistry

    results = []
    for name in SDKConnectorRegistry.all():
        connector = SDKConnectorRegistry.get(name, {})
        if connector:
            health = connector.health_check()
            results.append({"name": name, "healthy": health.healthy, "sdk": "2.0"})

    for name in ConnectorRegistry.all():
        if name in SDKConnectorRegistry.all():
            continue
        connector = ConnectorRegistry.get(name, {})
        if connector:
            hc = connector.health_check()
            results.append({"name": name, "healthy": hc.get("healthy", False), "sdk": "1.0"})

    unhealthy = [r for r in results if not r["healthy"]]
    if unhealthy:
        logger.warning("Unhealthy connectors: %s", unhealthy)
    return {"checked": len(results), "unhealthy": len(unhealthy)}


@shared_task(name="discovery.process_dlq")
def process_dlq():
    logger.info("DLQ processing — no entries in MVP store")
    return {"processed": 0}