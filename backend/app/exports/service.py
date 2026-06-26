from __future__ import annotations
import csv
import io
import json
from datetime import datetime, timedelta, timezone
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.exports.models import Export, ImportJob
from backend.app.exports.schemas import ExportCreate, ImportJobCreate
from backend.app.companies.models import Company
from backend.app.contacts.models import Contact
from backend.app.common.exceptions import NotFoundError


class ExportService:

    async def create_export(
        self, db: AsyncSession, org_id: UUID, user_id: UUID, data: ExportCreate
    ) -> Export:
        export = Export(
            organization_id=org_id,
            user_id=user_id,
            name=data.name,
            format=data.format,
            entity_type=data.entity_type,
            filters=data.filters,
            status="PENDING",
            expires_at=datetime.now(timezone.utc) + timedelta(days=7),
        )
        db.add(export)
        await db.flush()
        return export

    async def get_export(self, db: AsyncSession, org_id: UUID, export_id: UUID) -> Export:
        result = await db.execute(
            select(Export).where(Export.id == export_id, Export.organization_id == org_id)
        )
        export = result.scalar_one_or_none()
        if not export:
            raise NotFoundError(f"Export {export_id} not found")
        return export

    async def list_exports(
        self, db: AsyncSession, org_id: UUID, page: int = 1, page_size: int = 25
    ) -> tuple[list[Export], int]:
        total = await db.scalar(
            select(func.count()).select_from(Export)
            .where(Export.organization_id == org_id)
        ) or 0
        result = await db.execute(
            select(Export).where(Export.organization_id == org_id)
            .order_by(Export.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
        return result.scalars().all(), total

    async def generate_csv_export(
        self, db: AsyncSession, org_id: UUID, export_id: UUID
    ) -> bytes:
        """Generate export in-memory and return bytes. For small datasets only."""
        export = await self.get_export(db, org_id, export_id)

        if export.entity_type == "companies":
            result = await db.execute(
                select(Company).where(
                    Company.organization_id == org_id,
                    Company.deleted_at.is_(None),
                ).limit(10000)
            )
            rows = result.scalars().all()
            fieldnames = ["id", "name", "domain", "industry", "country", "city", "employee_count", "annual_revenue", "created_at"]
            data = [{f: str(getattr(r, f, "") or "") for f in fieldnames} for r in rows]
        else:
            result = await db.execute(
                select(Contact).where(
                    Contact.organization_id == org_id,
                    Contact.deleted_at.is_(None),
                ).limit(10000)
            )
            rows = result.scalars().all()
            fieldnames = ["id", "first_name", "last_name", "email", "designation", "department", "seniority", "country", "created_at"]
            data = [{f: str(getattr(r, f, "") or "") for f in fieldnames} for r in rows]

        output = io.StringIO()
        writer = csv.DictWriter(output, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(data)

        export.status = "COMPLETED"
        export.row_count = len(data)
        await db.flush()

        return output.getvalue().encode("utf-8")

    async def generate_json_export(
        self, db: AsyncSession, org_id: UUID, export_id: UUID
    ) -> bytes:
        export = await self.get_export(db, org_id, export_id)

        if export.entity_type == "companies":
            result = await db.execute(
                select(Company).where(
                    Company.organization_id == org_id,
                    Company.deleted_at.is_(None),
                ).limit(10000)
            )
            rows = [r.to_dict() for r in result.scalars().all()]
        else:
            result = await db.execute(
                select(Contact).where(
                    Contact.organization_id == org_id,
                    Contact.deleted_at.is_(None),
                ).limit(10000)
            )
            rows = [r.to_dict() for r in result.scalars().all()]

        export.status = "COMPLETED"
        export.row_count = len(rows)
        await db.flush()

        def default_serializer(obj):
            if isinstance(obj, (datetime, UUID)):
                return str(obj)
            raise TypeError(f"Object of type {type(obj)} is not JSON serializable")

        return json.dumps(rows, default=default_serializer, indent=2).encode("utf-8")

    async def create_import_job(
        self, db: AsyncSession, org_id: UUID, user_id: UUID, data: ImportJobCreate
    ) -> ImportJob:
        job = ImportJob(
            organization_id=org_id,
            user_id=user_id,
            name=data.name,
            entity_type=data.entity_type,
            status="PENDING",
            mapping=data.mapping,
            errors=[],
        )
        db.add(job)
        await db.flush()
        return job

    async def get_import_job(self, db: AsyncSession, org_id: UUID, job_id: UUID) -> ImportJob:
        result = await db.execute(
            select(ImportJob).where(ImportJob.id == job_id, ImportJob.organization_id == org_id)
        )
        job = result.scalar_one_or_none()
        if not job:
            raise NotFoundError(f"Import job {job_id} not found")
        return job
