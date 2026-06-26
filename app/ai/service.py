"""AI service — scoring, embeddings, recommendations, duplicate detection, summaries."""
from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.base_service import BaseService
from app.core.config import settings
from app.core.events import LeadScored
from app.core.logging import get_logger
from app.core.metrics import AI_SCORING_DURATION
from app.ai.embeddings import EmbeddingService
from app.ai.schemas import LeadScoreResponse, RecommendationResponse

logger = get_logger(__name__)


class AIService(BaseService):
    def __init__(self, db: AsyncSession | None = None) -> None:
        super().__init__()
        self.db = db
        self._embed = EmbeddingService()

    async def score_lead(
        self,
        org_id: UUID,
        entity_type: str,
        entity_id: UUID,
        force_refresh: bool = False,
    ) -> LeadScoreResponse:
        import time
        if not force_refresh and self.db:
            cached = await self._get_cached_score(org_id, entity_type, entity_id)
            if cached:
                return cached

        entity_data = await self._fetch_entity(org_id, entity_type, entity_id)
        start = time.perf_counter()
        score_data = await self._call_scoring_model(entity_type, entity_data)
        AI_SCORING_DURATION.observe(time.perf_counter() - start)

        if self.db:
            await self._upsert_score(org_id, entity_type, entity_id, score_data)
        await self.publish(LeadScored(org_id=org_id, payload={"entity_type": entity_type, "entity_id": str(entity_id), "score": score_data["overall_score"]}))
        return LeadScoreResponse(**score_data, entity_type=entity_type, entity_id=entity_id)

    async def generate_embeddings(self, org_id: UUID, entity_type: str, entity_id: UUID, text_content: str) -> None:
        embedding = await self._embed.embed_text(text_content)
        if self.db:
            await self.db.execute(
                text("""
                    INSERT INTO ai.embeddings (organization_id, entity_type, entity_id, embedding, model_id)
                    VALUES (:oid, :etype, :eid, :emb::vector, :model)
                    ON CONFLICT (organization_id, entity_type, entity_id)
                    DO UPDATE SET embedding = EXCLUDED.embedding, updated_at = NOW()
                """),
                {"oid": org_id, "etype": entity_type, "eid": entity_id,
                 "emb": str(embedding), "model": settings.OPENAI_EMBEDDING_MODEL},
            )

    async def find_duplicates(self, org_id: UUID, entity_type: str, entity_id: UUID, threshold: float = 0.85) -> list[dict]:
        entity_data = await self._fetch_entity(org_id, entity_type, entity_id)
        embedding = await self._embed.embed_text(str(entity_data))
        if not self.db:
            return []
        result = await self.db.execute(
            text("""
                SELECT e.entity_id, 1 - (e.embedding <=> :emb::vector) AS similarity
                FROM ai.embeddings e
                WHERE e.organization_id = :oid AND e.entity_type = :etype
                  AND e.entity_id != :eid
                  AND 1 - (e.embedding <=> :emb::vector) >= :threshold
                ORDER BY similarity DESC
                LIMIT 10
            """),
            {"oid": org_id, "etype": entity_type, "eid": entity_id,
             "emb": str(embedding), "threshold": threshold},
        )
        return [{"entity_id": r["entity_id"], "similarity": float(r["similarity"])} for r in result.mappings().fetchall()]

    async def get_recommendations(
        self, org_id: UUID, entity_type: str, seed_entity_id: UUID, limit: int = 10
    ) -> RecommendationResponse:
        if not self.db:
            return RecommendationResponse(seed_entity_id=seed_entity_id, recommendations=[], model_id=settings.ANTHROPIC_MODEL)
        seed_emb = await self.db.execute(
            text("SELECT embedding FROM ai.embeddings WHERE organization_id = :oid AND entity_type = :etype AND entity_id = :eid"),
            {"oid": org_id, "etype": entity_type, "eid": seed_entity_id},
        )
        row = seed_emb.fetchone()
        if not row:
            return RecommendationResponse(seed_entity_id=seed_entity_id, recommendations=[], model_id=settings.OPENAI_EMBEDDING_MODEL)
        result = await self.db.execute(
            text("""
                SELECT e.entity_id, 1 - (e.embedding <=> :emb::vector) AS score
                FROM ai.embeddings e
                WHERE e.organization_id = :oid AND e.entity_type = :etype
                  AND e.entity_id != :seed
                ORDER BY e.embedding <=> :emb::vector
                LIMIT :limit
            """),
            {"oid": org_id, "etype": entity_type, "seed": seed_entity_id, "emb": str(row[0]), "limit": limit},
        )
        recs = [{"entity_id": str(r["entity_id"]), "score": float(r["score"])} for r in result.mappings().fetchall()]
        return RecommendationResponse(seed_entity_id=seed_entity_id, recommendations=recs, model_id=settings.OPENAI_EMBEDDING_MODEL)

    async def generate_company_summary(self, company: dict) -> dict:
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = f"""Analyze this B2B company and provide a concise intelligence summary.

Company: {company.get('name')}
Industry: {company.get('industry_name', 'Unknown')}
Employees: {company.get('employee_count', 'Unknown')}
Revenue: {company.get('annual_revenue', 'Unknown')}
Country: {company.get('country_code', 'Unknown')}
Description: {company.get('description', 'No description')}

Provide JSON with keys: summary (string), key_facts (list), strengths (list), risks (list)."""
        msg = await client.messages.create(
            model=settings.ANTHROPIC_MODEL, max_tokens=1024,
            messages=[{"role": "user", "content": prompt}],
        )
        import json
        try:
            data = json.loads(msg.content[0].text)
        except Exception:
            data = {"summary": msg.content[0].text, "key_facts": [], "strengths": [], "risks": []}
        data.update({"company_id": company["id"], "generated_at": datetime.now(timezone.utc)})
        return data

    # ------------------------------------------------------------------
    # Internals
    # ------------------------------------------------------------------
    async def _call_scoring_model(self, entity_type: str, entity: dict) -> dict:
        import json
        from anthropic import AsyncAnthropic
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = f"""Score this {entity_type} as a B2B sales lead. Return JSON with:
overall_score (0-100), quality_score, fit_score, intent_score, engagement_score, timing_score (all 0-100),
recommendation (hot/warm/cold/not_a_fit), score_reasons (list of strings).

Data: {json.dumps(entity, default=str)[:2000]}"""
        msg = await client.messages.create(
            model=settings.ANTHROPIC_MODEL, max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            return json.loads(msg.content[0].text)
        except Exception:
            return {
                "overall_score": 50, "quality_score": 50, "fit_score": 50,
                "intent_score": 50, "engagement_score": 50, "timing_score": 50,
                "recommendation": "warm", "score_reasons": [],
                "model_id": settings.ANTHROPIC_MODEL,
                "scored_at": datetime.now(timezone.utc),
            }

    async def _fetch_entity(self, org_id: UUID, entity_type: str, entity_id: UUID) -> dict:
        if not self.db:
            return {}
        table = "core.companies" if entity_type == "company" else "core.contacts"
        result = await self.db.execute(
            text(f"SELECT * FROM {table} WHERE id = :id AND organization_id = :oid AND deleted_at IS NULL"),
            {"id": entity_id, "oid": org_id},
        )
        row = result.mappings().fetchone()
        return dict(row) if row else {}

    async def _get_cached_score(self, org_id, entity_type, entity_id) -> LeadScoreResponse | None:
        if not self.db:
            return None
        result = await self.db.execute(
            text("SELECT * FROM ai.lead_scores WHERE organization_id = :oid AND entity_type = :etype AND entity_id = :eid AND deleted_at IS NULL"),
            {"oid": org_id, "etype": entity_type, "eid": entity_id},
        )
        row = result.mappings().fetchone()
        if row:
            return LeadScoreResponse(**dict(row))
        return None

    async def _upsert_score(self, org_id, entity_type, entity_id, score_data) -> None:
        if not self.db:
            return
        await self.db.execute(
            text("""
                INSERT INTO ai.lead_scores
                  (organization_id, entity_type, entity_id, overall_score, quality_score,
                   fit_score, intent_score, engagement_score, timing_score, recommendation,
                   score_reasons, model_id, scored_at)
                VALUES (:oid, :etype, :eid, :overall, :quality, :fit, :intent, :engage, :timing,
                        :rec, :reasons::jsonb, :model, NOW())
                ON CONFLICT (organization_id, entity_type, entity_id)
                DO UPDATE SET
                  overall_score = EXCLUDED.overall_score,
                  recommendation = EXCLUDED.recommendation,
                  score_reasons = EXCLUDED.score_reasons,
                  scored_at = NOW(), updated_at = NOW()
            """),
            {
                "oid": org_id, "etype": entity_type, "eid": entity_id,
                "overall": score_data.get("overall_score", 50),
                "quality": score_data.get("quality_score"), "fit": score_data.get("fit_score"),
                "intent": score_data.get("intent_score"), "engage": score_data.get("engagement_score"),
                "timing": score_data.get("timing_score"),
                "rec": score_data.get("recommendation", "cold"),
                "reasons": __import__('json').dumps(score_data.get("score_reasons", [])),
                "model": settings.ANTHROPIC_MODEL,
            },
        )
