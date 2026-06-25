import uuid
import asyncio
from celery import shared_task
from celery.utils.log import get_task_logger

logger = get_task_logger(__name__)


def run_async(coro):
    """Run an async coroutine from a synchronous Celery task."""
    loop = asyncio.new_event_loop()
    try:
        return loop.run_until_complete(coro)
    finally:
        loop.close()


@shared_task(bind=True, max_retries=3, default_retry_delay=60, name="enrichment.verify_emails")
def verify_emails_task(self, emails: list[str], org_id: str, contact_id: str | None = None):
    logger.info(f"Verifying {len(emails)} emails for org {org_id}")
    try:
        from backend.connectors.registry import ConnectorRegistry
        connector = ConnectorRegistry.get("email_verifier")
        if connector:
            results = connector.enrich({"emails": emails})
            logger.info(f"Email verification complete: {results}")
        return {"status": "completed", "count": len(emails)}
    except Exception as exc:
        logger.error(f"Email verification failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120, name="enrichment.enrich_contact")
def enrich_contact_task(self, contact_id: str, org_id: str):
    logger.info(f"Enriching contact {contact_id} for org {org_id}")
    try:
        # Placeholder: invoke connectors, update contact record
        return {"status": "completed", "contact_id": contact_id}
    except Exception as exc:
        logger.error(f"Contact enrichment failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=3, default_retry_delay=120, name="enrichment.enrich_company")
def enrich_company_task(self, company_id: str, org_id: str):
    logger.info(f"Enriching company {company_id} for org {org_id}")
    try:
        return {"status": "completed", "company_id": company_id}
    except Exception as exc:
        logger.error(f"Company enrichment failed: {exc}")
        raise self.retry(exc=exc)


@shared_task(bind=True, max_retries=2, name="search.execute")
def execute_search_task(self, search_id: str):
    logger.info(f"Executing search {search_id}")
    try:
        return {"status": "completed", "search_id": search_id}
    except Exception as exc:
        raise self.retry(exc=exc)


@shared_task(name="connector.health_check")
def check_connector_health():
    logger.info("Running connector health checks")
    from backend.connectors.registry import ConnectorRegistry
    results = {}
    for name, connector in ConnectorRegistry.all().items():
        try:
            results[name] = connector.health_check()
        except Exception as e:
            results[name] = {"healthy": False, "error": str(e)}
    return results
