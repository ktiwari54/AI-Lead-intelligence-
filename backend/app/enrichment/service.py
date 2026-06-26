from __future__ import annotations
from uuid import UUID

from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.enrichment.models import EmailVerification
from backend.app.enrichment.schemas import VerifyEmailRequest, EnrichContactRequest, EnrichCompanyRequest
from backend.app.contacts.models import Contact
from backend.app.companies.models import Company
from backend.app.common.exceptions import NotFoundError


class EnrichmentService:

    async def verify_email(
        self, db: AsyncSession, org_id: UUID, data: VerifyEmailRequest
    ) -> EmailVerification:
        # Return a recent cached verification if one exists
        existing = await db.scalar(
            select(EmailVerification)
            .where(EmailVerification.email == data.email)
            .order_by(EmailVerification.created_at.desc())
            .limit(1)
        )
        if existing:
            return existing

        # Create pending verification record
        verification = EmailVerification(
            contact_id=data.contact_id,
            email=data.email,
            provider="pending",
        )
        db.add(verification)
        await db.flush()
        return verification

    async def get_verification(self, db: AsyncSession, email: str) -> EmailVerification | None:
        return await db.scalar(
            select(EmailVerification)
            .where(EmailVerification.email == email)
            .order_by(EmailVerification.created_at.desc())
            .limit(1)
        )

    async def list_verifications(
        self, db: AsyncSession, contact_id: UUID, page: int = 1, page_size: int = 25
    ) -> tuple[list[EmailVerification], int]:
        total = await db.scalar(
            select(func.count()).select_from(EmailVerification)
            .where(EmailVerification.contact_id == contact_id)
        ) or 0
        result = await db.execute(
            select(EmailVerification)
            .where(EmailVerification.contact_id == contact_id)
            .order_by(EmailVerification.created_at.desc())
            .offset((page - 1) * page_size).limit(page_size)
        )
        return result.scalars().all(), total

    async def enrich_contact(self, db: AsyncSession, org_id: UUID, data: EnrichContactRequest) -> Contact:
        contact = await db.scalar(
            select(Contact).where(Contact.id == data.contact_id, Contact.organization_id == org_id)
        )
        if not contact:
            raise NotFoundError(f"Contact {data.contact_id} not found")
        # Mark as enrichment in progress
        contact.enrichment_status = "IN_PROGRESS"
        await db.flush()
        return contact

    async def enrich_company(self, db: AsyncSession, org_id: UUID, data: EnrichCompanyRequest) -> Company:
        company = await db.scalar(
            select(Company).where(Company.id == data.company_id, Company.organization_id == org_id)
        )
        if not company:
            raise NotFoundError(f"Company {data.company_id} not found")
        company.enrichment_status = "IN_PROGRESS"
        await db.flush()
        return company
