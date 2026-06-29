from __future__ import annotations

import asyncio

from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def _run_async(coro):
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(name="security.run_compliance_checks")
def run_compliance_checks():
    """Run automated compliance checks for all organizations."""
    logger.info("Running security compliance checks")

    async def _run():
        from sqlalchemy import select
        from backend.database import AsyncSessionLocal
        from backend.app.organizations.models import Organization
        from backend.app.security import service

        async with AsyncSessionLocal() as db:
            orgs = (await db.execute(select(Organization.id))).scalars().all()
            total = 0
            for org_id in orgs:
                from backend.app.users.models import User
                admin = (await db.execute(
                    select(User).where(User.organization_id == org_id, User.is_superadmin == True).limit(1)  # noqa: E712
                )).scalar_one_or_none()
                if not admin:
                    continue
                try:
                    results = await service.run_compliance_checks(db, org_id, admin)
                    total += len(results)
                except Exception:
                    pass
            return total

    try:
        count = _run_async(_run())
        return {"status": "completed", "checks_run": count}
    except Exception as exc:
        logger.exception("Compliance check failed: %s", exc)
        raise


@shared_task(name="security.process_soc_alerts")
def process_soc_alerts():
    """Scan recent security events and create alerts for high-severity patterns."""
    logger.info("Processing SOC security alerts")

    async def _process():
        from datetime import datetime, timedelta, timezone
        from sqlalchemy import select, func
        from backend.database import AsyncSessionLocal
        from backend.app.security.models import SecurityAlert, SecurityEvent

        since = datetime.now(timezone.utc) - timedelta(hours=1)
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(
                    SecurityEvent.organization_id,
                    SecurityEvent.event_type,
                    func.count(),
                ).where(
                    SecurityEvent.severity.in_(["high", "critical"]),
                    SecurityEvent.created_at >= since,
                ).group_by(SecurityEvent.organization_id, SecurityEvent.event_type)
                .having(func.count() >= 5)
            )
            created = 0
            for org_id, event_type, count in result.all():
                db.add(SecurityAlert(
                    organization_id=org_id,
                    alert_type="event_spike",
                    severity="high",
                    title=f"Spike in {event_type} events",
                    description=f"{count} high/critical events in the last hour",
                    metadata_={"event_type": event_type, "count": count},
                ))
                created += 1
            if created:
                await db.commit()
            return created

    try:
        count = _run_async(_process())
        return {"status": "completed", "alerts_created": count}
    except Exception as exc:
        logger.exception("SOC alert processing failed: %s", exc)
        raise