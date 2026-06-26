from __future__ import annotations

import asyncio
import uuid

from celery import shared_task

from backend.app.ai.scoring_engine import get_scorer


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def score_contact_task(self, contact_id: str, org_id: str, icp_profile: dict | None = None):
    """Score a contact using AI. Called async via Celery."""
    from backend.app.ai.service import AIService
    from backend.database import AsyncSessionLocal

    async def _run():
        async with AsyncSessionLocal() as db:
            service = AIService()
            return await service.score_contact(db, uuid.UUID(org_id), uuid.UUID(contact_id), icp_profile)

    try:
        result = asyncio.run(_run())
        return {"contact_id": contact_id, "overall_score": result.overall_score, "status": "completed"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)


@shared_task(bind=True, max_retries=3, default_retry_delay=60)
def score_company_task(self, company_id: str, org_id: str, icp_profile: dict | None = None):
    """Score a company using AI."""
    from backend.app.ai.service import AIService
    from backend.database import AsyncSessionLocal

    async def _run():
        async with AsyncSessionLocal() as db:
            service = AIService()
            return await service.score_company(db, uuid.UUID(org_id), uuid.UUID(company_id), icp_profile)

    try:
        result = asyncio.run(_run())
        return {"company_id": company_id, "overall_score": result.overall_score, "status": "completed"}
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)


@shared_task
def score_stale_leads(days_since_last_score: int = 7):
    """Beat task: re-score leads not scored in N days."""
    from backend.database import AsyncSessionLocal
    from backend.app.contacts.models import Contact
    from sqlalchemy import select
    from datetime import datetime, timedelta, timezone

    cutoff = datetime.now(timezone.utc) - timedelta(days=days_since_last_score)

    async def _run():
        async with AsyncSessionLocal() as db:
            result = await db.execute(
                select(Contact.id, Contact.organization_id)
                .where(Contact.deleted_at.is_(None))
                .limit(100)
            )
            contacts = result.all()

            for contact_id, org_id in contacts:
                score_contact_task.delay(str(contact_id), str(org_id))

            return len(contacts)

    count = asyncio.run(_run())
    return {"queued": count}
