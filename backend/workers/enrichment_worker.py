import asyncio
import logging
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.enrichment_worker.enrich_company", bind=True, max_retries=3)
def enrich_company(self, company_id: str, connector_name: str = "clearbit"):
    try:
        asyncio.run(_enrich_company(company_id, connector_name))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


async def _enrich_company(company_id: str, connector_name: str):
    from app.core.database import AsyncSessionLocal
    from app.models.companies import Company
    from connectors.clearbit_connector import ClearbitConnector
    from app.core.config import settings

    async with AsyncSessionLocal() as db:
        company = await db.get(Company, company_id)
        if not company:
            return
        connector = ClearbitConnector(config={"api_key": settings.CLEARBIT_API_KEY})
        result = await connector.enrich({"domain": company.domain})
        if result.success and result.data:
            d = result.data
            if d.get("employee_count"):
                company.employee_count = d["employee_count"]
            if d.get("description"):
                company.description = d["description"]
            if d.get("founded_year"):
                company.founded_year = d["founded_year"]
            company.confidence_score = 0.9
        await db.commit()
        logger.info("Enriched company %s via %s", company_id, connector_name)


@celery_app.task(name="workers.enrichment_worker.verify_email", bind=True, max_retries=3)
def verify_email_task(self, contact_id: str, email: str):
    try:
        asyncio.run(_verify_email(contact_id, email))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries)


async def _verify_email(contact_id: str, email: str):
    from app.core.database import AsyncSessionLocal
    from app.models.enrichment import EmailVerification
    from app.models.contacts import Contact
    from connectors.hunter_connector import HunterConnector
    from app.core.config import settings
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        connector = HunterConnector(config={"api_key": settings.HUNTER_API_KEY})
        result = await connector.enrich({"email": email})
        # Update the pending verification record
        existing = (await db.execute(
            select(EmailVerification).where(EmailVerification.contact_id == contact_id, EmailVerification.email == email)
        )).scalar_one_or_none()
        status = result.data.get("status", "unknown") if result.success and result.data else "error"
        confidence = (result.data.get("score", 0) / 100) if result.success and result.data else 0
        if existing:
            existing.status = status
            existing.confidence = confidence
            existing.provider = "hunter"
        else:
            db.add(EmailVerification(contact_id=contact_id, email=email, status=status, provider="hunter", confidence=confidence))
        # Sync status to contact
        contact = await db.get(Contact, contact_id)
        if contact:
            contact.email_status = status
        await db.commit()
        logger.info("Verified email %s: %s", email, status)
