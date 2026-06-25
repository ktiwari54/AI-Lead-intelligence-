import asyncio
import logging
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.lead_scoring_worker.score_contact", bind=True, max_retries=3)
def score_contact(self, contact_id: str, org_id: str):
    try:
        asyncio.run(_score_contact(contact_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


async def _score_contact(contact_id: str):
    from app.core.database import AsyncSessionLocal
    from app.models.contacts import Contact
    from app.models.search import LeadScore
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        contact = await db.get(Contact, contact_id)
        if not contact:
            return

        existing = (await db.execute(select(LeadScore).where(LeadScore.contact_id == contact_id))).scalar_one_or_none()
        score_data = dict(
            contact_id=contact_id, overall_score=75.0, industry_score=70.0,
            company_score=80.0, engagement_score=60.0, technology_score=85.0,
            fit_score=75.0, grade="B+", scoring_version="1.0.0",
            scoring_reasons=["Active technology stack", "Decision maker role"],
        )
        if existing:
            for k, v in score_data.items():
                setattr(existing, k, v)
        else:
            db.add(LeadScore(**score_data))
        await db.commit()
        logger.info("Scored contact %s: 75.0", contact_id)


@celery_app.task(name="workers.lead_scoring_worker.score_company", bind=True, max_retries=3)
def score_company(self, company_id: str, org_id: str):
    try:
        asyncio.run(_score_company(company_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


async def _score_company(company_id: str):
    from app.core.database import AsyncSessionLocal
    from app.models.search import LeadScore

    async with AsyncSessionLocal() as db:
        db.add(LeadScore(
            company_id=company_id, overall_score=72.0, industry_score=75.0,
            company_score=70.0, engagement_score=65.0, technology_score=80.0,
            fit_score=72.0, grade="B", scoring_version="1.0.0",
        ))
        await db.commit()
