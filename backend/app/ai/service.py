from __future__ import annotations

from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from backend.app.ai.scoring_engine import get_scorer
from backend.app.ai.models import LeadScore
from backend.app.contacts.models import Contact
from backend.app.companies.models import Company


class AIService:
    async def score_contact(
        self,
        db: AsyncSession,
        org_id: UUID,
        contact_id: UUID,
        icp_profile: dict | None = None,
    ) -> LeadScore:
        # Load contact with company
        result = await db.execute(
            select(Contact)
            .options(selectinload(Contact.company))
            .where(Contact.id == contact_id, Contact.organization_id == org_id)
        )
        contact = result.scalar_one()

        company = contact.company
        contact_data = {
            "first_name": contact.first_name,
            "last_name": contact.last_name,
            "email": contact.email,
            "designation": contact.designation,
            "department": contact.department,
            "seniority": contact.seniority,
            "email_verified": contact.email_verified,
            "linkedin_url": contact.linkedin_url,
            "phone": contact.phone,
            "company_name": company.name if company else None,
            "company_industry": company.industry if company else None,
            "company_size": company.employee_count if company else None,
            "technologies": company.technologies if company else [],
        }

        score_result = await get_scorer().score_contact(contact_data, icp_profile)

        # Upsert LeadScore
        existing = await db.execute(
            select(LeadScore).where(
                LeadScore.contact_id == contact_id,
                LeadScore.organization_id == org_id,
            )
        )
        lead_score = existing.scalar_one_or_none()

        if lead_score is None:
            lead_score = LeadScore(
                contact_id=contact_id,
                organization_id=org_id,
            )
            db.add(lead_score)

        lead_score.overall_score = score_result.overall_score
        lead_score.seniority_score = score_result.seniority_score
        lead_score.engagement_score = score_result.engagement_score
        lead_score.fit_score = score_result.fit_score
        lead_score.technology_score = score_result.technology_score
        lead_score.industry_score = score_result.industry_score
        lead_score.company_score = getattr(score_result, "company_score", 0)
        lead_score.score_breakdown = score_result.score_breakdown

        await db.commit()
        await db.refresh(lead_score)
        return lead_score

    async def score_company(
        self,
        db: AsyncSession,
        org_id: UUID,
        company_id: UUID,
        icp_profile: dict | None = None,
    ) -> LeadScore:
        result = await db.execute(
            select(Company).where(
                Company.id == company_id, Company.organization_id == org_id
            )
        )
        company = result.scalar_one()

        company_data = {
            "name": company.name,
            "domain": company.domain,
            "industry": company.industry,
            "employee_count": company.employee_count,
            "annual_revenue": company.annual_revenue,
            "technologies": company.technologies,
            "country": company.country,
            "description": company.description,
        }

        score_result = await get_scorer().score_company(company_data, icp_profile)

        existing = await db.execute(
            select(LeadScore).where(
                LeadScore.company_id == company_id,
                LeadScore.organization_id == org_id,
            )
        )
        lead_score = existing.scalar_one_or_none()

        if lead_score is None:
            lead_score = LeadScore(
                company_id=company_id,
                organization_id=org_id,
            )
            db.add(lead_score)

        lead_score.overall_score = score_result.overall_score
        lead_score.company_score = score_result.company_score
        lead_score.technology_score = score_result.technology_score
        lead_score.industry_score = score_result.industry_score
        lead_score.engagement_score = score_result.engagement_score
        lead_score.fit_score = score_result.fit_score
        lead_score.seniority_score = score_result.seniority_score
        lead_score.score_breakdown = score_result.score_breakdown

        await db.commit()
        await db.refresh(lead_score)
        return lead_score

    async def get_contact_scores(
        self, db: AsyncSession, org_id: UUID, contact_id: UUID
    ) -> list[LeadScore]:
        result = await db.execute(
            select(LeadScore).where(
                LeadScore.contact_id == contact_id,
                LeadScore.organization_id == org_id,
            )
        )
        return list(result.scalars().all())

    async def get_company_scores(
        self, db: AsyncSession, org_id: UUID, company_id: UUID
    ) -> list[LeadScore]:
        result = await db.execute(
            select(LeadScore).where(
                LeadScore.company_id == company_id,
                LeadScore.organization_id == org_id,
            )
        )
        return list(result.scalars().all())
