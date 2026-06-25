from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.models.search import LeadScore
from app.ai.schemas import ScoreRequest, ScoreResponse


async def score_lead(data: ScoreRequest, db: AsyncSession) -> ScoreResponse:
    score_data = {
        "contact_id": data.contact_id,
        "company_id": data.company_id,
        "overall_score": 75.0,
        "industry_score": 70.0,
        "company_score": 80.0,
        "engagement_score": 60.0,
        "technology_score": 85.0,
        "fit_score": 75.0,
        "grade": "B+",
        "scoring_version": "1.0.0",
        "scoring_reasons": ["Active technology stack", "Company size matches ICP", "Decision maker role"],
    }

    # Upsert lead score
    existing = None
    if data.contact_id:
        existing = (await db.execute(select(LeadScore).where(LeadScore.contact_id == data.contact_id))).scalar_one_or_none()
    elif data.company_id:
        existing = (await db.execute(select(LeadScore).where(LeadScore.company_id == data.company_id))).scalar_one_or_none()

    if existing:
        for k, v in score_data.items():
            setattr(existing, k, v)
    else:
        db.add(LeadScore(**score_data))
    await db.flush()

    return ScoreResponse(
        overall_score=75.0, industry_score=70.0, company_score=80.0,
        engagement_score=60.0, technology_score=85.0, fit_score=75.0,
        grade="B+", scoring_reasons=score_data["scoring_reasons"],
    )


async def process_nl_query(query: str) -> dict:
    # Placeholder: integrate Anthropic Claude for NL-to-filter parsing
    return {
        "interpreted_filters": {"industry": "SaaS", "employee_range": "50-500"},
        "suggested_query": query,
        "confidence": 0.85,
    }
