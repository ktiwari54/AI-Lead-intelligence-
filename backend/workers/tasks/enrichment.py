"""Enrichment Celery tasks."""
from __future__ import annotations
import asyncio
import logging
from celery import shared_task

logger = logging.getLogger(__name__)


@shared_task(bind=True, max_retries=3, default_retry_delay=60, name="enrichment.verify_emails")
def verify_emails_task(self, email: str, contact_id: str | None = None):
    """Verify a single email address using Hunter connector."""
    from backend.database import AsyncSessionLocal
    from backend.app.enrichment.models import EmailVerification
    from sqlalchemy import select
    import uuid

    async def _run():
        try:
            from backend.connectors.hunter import HunterConnector
            from backend.config import get_settings
            settings = get_settings()

            connector = HunterConnector({"api_key": settings.HUNTER_API_KEY} if hasattr(settings, "HUNTER_API_KEY") else {})
            result = connector.enrich({"email": email})

            async with AsyncSessionLocal() as db:
                verification = await db.scalar(
                    select(EmailVerification)
                    .where(EmailVerification.email == email)
                    .order_by(EmailVerification.created_at.desc())
                    .limit(1)
                )
                if not verification:
                    verification = EmailVerification(email=email)
                    if contact_id:
                        verification.contact_id = uuid.UUID(contact_id)
                    db.add(verification)

                if result and result.success:
                    data = result.data
                    verification.is_deliverable = data.get("is_valid", data.get("result") == "deliverable")
                    verification.is_disposable = data.get("is_disposable", False)
                    verification.is_role_address = data.get("is_role_address", False)
                    verification.is_catch_all = data.get("is_catch_all", False)
                    verification.smtp_check = data.get("smtp_check", None)
                    verification.confidence = data.get("score", data.get("confidence", 0)) / 100.0
                    verification.provider = "hunter"
                    verification.raw_response = data
                else:
                    verification.provider = "hunter_error"

                await db.commit()
                return {"email": email, "status": "completed"}
        except Exception as e:
            logger.exception(f"Email verification failed for {email}: {e}")
            return {"email": email, "status": "failed", "error": str(e)}

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)


@shared_task(bind=True, max_retries=3, default_retry_delay=120, name="enrichment.enrich_contact")
def enrich_contact_task(self, contact_id: str, org_id: str, provider: str = "hunter"):
    """Enrich a contact using a connector."""
    from backend.database import AsyncSessionLocal
    from backend.app.contacts.models import Contact
    from sqlalchemy import select
    import uuid

    async def _run():
        async with AsyncSessionLocal() as db:
            contact = await db.scalar(
                select(Contact).where(
                    Contact.id == uuid.UUID(contact_id),
                    Contact.organization_id == uuid.UUID(org_id),
                )
            )
            if not contact:
                return {"status": "not_found", "contact_id": contact_id}

            try:
                if provider == "hunter" and contact.email:
                    from backend.connectors.hunter import HunterConnector
                    from backend.config import get_settings
                    settings = get_settings()
                    connector = HunterConnector({"api_key": getattr(settings, "HUNTER_API_KEY", "")})
                    result = connector.lookup(contact.email)
                    if result and result.success:
                        data = result.data
                        if not contact.designation and data.get("designation"):
                            contact.designation = data["designation"]
                        if not contact.department and data.get("department"):
                            contact.department = data["department"]
                        if not contact.linkedin_url and data.get("linkedin_url"):
                            contact.linkedin_url = data["linkedin_url"]
                        contact.enrichment_status = "ENRICHED"
                    else:
                        contact.enrichment_status = "FAILED"
                else:
                    contact.enrichment_status = "SKIPPED"

                await db.commit()
                return {"status": "completed", "contact_id": contact_id}
            except Exception as e:
                contact.enrichment_status = "FAILED"
                await db.commit()
                raise

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)


@shared_task(bind=True, max_retries=3, default_retry_delay=120, name="enrichment.enrich_company")
def enrich_company_task(self, company_id: str, org_id: str, provider: str = "clearbit"):
    """Enrich a company using a connector."""
    from backend.database import AsyncSessionLocal
    from backend.app.companies.models import Company
    from sqlalchemy import select
    import uuid

    async def _run():
        async with AsyncSessionLocal() as db:
            company = await db.scalar(
                select(Company).where(
                    Company.id == uuid.UUID(company_id),
                    Company.organization_id == uuid.UUID(org_id),
                )
            )
            if not company:
                return {"status": "not_found", "company_id": company_id}

            try:
                if provider == "clearbit" and company.domain:
                    from backend.connectors.clearbit import ClearbitConnector
                    from backend.config import get_settings
                    settings = get_settings()
                    connector = ClearbitConnector({"api_key": getattr(settings, "CLEARBIT_API_KEY", "")})
                    result = connector.lookup(company.domain)
                    if result and result.success:
                        data = result.data
                        if not company.description and data.get("description"):
                            company.description = data["description"]
                        if not company.employee_count and data.get("employee_count"):
                            company.employee_count = data["employee_count"]
                        if not company.annual_revenue and data.get("annual_revenue"):
                            company.annual_revenue = data["annual_revenue"]
                        company.enrichment_status = "ENRICHED"
                    else:
                        company.enrichment_status = "FAILED"
                else:
                    company.enrichment_status = "SKIPPED"

                await db.commit()
                return {"status": "completed", "company_id": company_id}
            except Exception as e:
                company.enrichment_status = "FAILED"
                await db.commit()
                raise

    try:
        return asyncio.run(_run())
    except Exception as exc:
        raise self.retry(exc=exc, countdown=2 ** self.request.retries * 30)


@shared_task(name="enrichment.check_connector_health")
def check_connector_health():
    """Beat task: check health of all registered connectors."""
    from backend.connectors.registry import connector_registry
    results = {}
    for name in connector_registry.list_available():
        try:
            connector = connector_registry.get(name)
            if connector:
                health = connector.health_check()
                results[name] = {"status": health.status, "latency_ms": health.latency_ms}
            else:
                results[name] = {"status": "not_instantiable"}
        except Exception as e:
            results[name] = {"status": "error", "error": str(e)}
    logger.info(f"Connector health check: {results}")
    return results


@shared_task(bind=True, max_retries=2, name="search.execute")
def execute_search_task(self, search_id: str):
    """Execute a saved search (preserved from original stub)."""
    logger.info(f"Executing search {search_id}")
    try:
        return {"status": "completed", "search_id": search_id}
    except Exception as exc:
        raise self.retry(exc=exc)
