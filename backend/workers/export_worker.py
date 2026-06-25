import asyncio
import csv
import io
import logging
from workers.celery_app import celery_app

logger = logging.getLogger(__name__)


@celery_app.task(name="workers.export_worker.export_contacts", bind=True, max_retries=2)
def export_contacts(self, export_id: str, org_id: str):
    try:
        asyncio.run(_export_contacts(export_id, org_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)


async def _export_contacts(export_id: str, org_id: str):
    from app.core.database import AsyncSessionLocal
    from app.models.system import Export
    from app.models.contacts import Contact
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        export = await db.get(Export, export_id)
        if not export:
            return
        export.status = "processing"
        await db.flush()

        contacts = (await db.execute(
            select(Contact).where(Contact.organization_id == org_id, Contact.is_deleted == False)
        )).scalars().all()

        output = io.StringIO()
        fieldnames = ["id", "first_name", "last_name", "email", "designation", "department", "phone", "email_status"]
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        for c in contacts:
            writer.writerow({
                "id": str(c.id), "first_name": c.first_name, "last_name": c.last_name,
                "email": c.email, "designation": c.designation,
                "department": c.department, "phone": c.phone, "email_status": c.email_status,
            })

        export.status = "completed"
        export.record_count = len(contacts)
        export.file_path = f"/exports/{export_id}.csv"
        await db.commit()
        logger.info("Export %s completed: %d records", export_id, len(contacts))


@celery_app.task(name="workers.export_worker.export_companies", bind=True, max_retries=2)
def export_companies(self, export_id: str, org_id: str):
    try:
        asyncio.run(_export_companies(export_id, org_id))
    except Exception as exc:
        raise self.retry(exc=exc, countdown=10)


async def _export_companies(export_id: str, org_id: str):
    from app.core.database import AsyncSessionLocal
    from app.models.system import Export
    from app.models.companies import Company
    from sqlalchemy import select

    async with AsyncSessionLocal() as db:
        export = await db.get(Export, export_id)
        if not export:
            return
        export.status = "processing"
        await db.flush()

        companies = (await db.execute(
            select(Company).where(Company.organization_id == org_id, Company.is_deleted == False)
        )).scalars().all()

        export.status = "completed"
        export.record_count = len(companies)
        export.file_path = f"/exports/{export_id}.csv"
        await db.commit()
