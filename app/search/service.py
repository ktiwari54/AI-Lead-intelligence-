"""Search service — keyword, FTS, semantic, NL, and connector-backed search."""
import hashlib
import time
from uuid import UUID, uuid4

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from app.common.base_service import BaseService
from app.core.events import SearchCompleted
from app.core.logging import get_logger
from app.core.redis import CacheService
from app.search.schemas import (
    NLSearchRequest,
    ParsedSearchIntent,
    SearchRequest,
    SearchResponse,
    SearchResultItem,
)

_cache = CacheService(prefix="search", ttl=1800)
logger = get_logger(__name__)


class SearchService(BaseService):
    def __init__(self, db: AsyncSession) -> None:
        super().__init__()
        self.db = db

    async def search(self, org_id: UUID, user_id: UUID, req: SearchRequest) -> SearchResponse:
        start = time.perf_counter()
        cache_key = self._cache_key(org_id, req)
        cached = await _cache.get(cache_key)
        if cached:
            resp = SearchResponse(**cached)
            resp.cache_hit = True
            return resp

        if req.use_semantic and req.query:
            results, total = await self._semantic_search(org_id, req)
        else:
            results, total = await self._fts_search(org_id, req)

        execution_ms = int((time.perf_counter() - start) * 1000)
        query_id = await self._log_search(org_id, user_id, req, total, execution_ms)

        resp = SearchResponse(
            items=results,
            total=total,
            page=req.page,
            page_size=req.page_size,
            pages=max(1, -(-total // req.page_size)),
            query_id=query_id,
            execution_ms=execution_ms,
        )
        await _cache.set(cache_key, resp.model_dump(mode="json"), ttl=1800)
        await self.publish(SearchCompleted(org_id=org_id, user_id=user_id, payload={"total": total}))
        return resp

    async def nl_search(self, org_id: UUID, user_id: UUID, req: NLSearchRequest) -> SearchResponse:
        """Parse natural language → structured filters → execute search."""
        intent = await self._parse_nl_query(req.query, req.search_type)
        search_req = SearchRequest(
            query=" ".join(intent.keywords) if intent.keywords else req.query,
            search_type=intent.search_type,
            filters=intent.filters,
            page=req.page,
            page_size=req.page_size,
        )
        result = await self.search(org_id, user_id, search_req)
        result.explanation = intent.explanation
        return result

    async def autocomplete(self, org_id: UUID, q: str, search_type: str, limit: int) -> list[dict]:
        table = "core.companies" if search_type == "company" else "core.contacts"
        name_col = "name" if search_type == "company" else "full_name"
        result = await self.db.execute(
            text(f"""
                SELECT id, {name_col} AS name, '{search_type}' AS entity_type
                FROM {table}
                WHERE organization_id = :oid AND deleted_at IS NULL
                  AND {name_col} ILIKE :q
                ORDER BY {name_col}
                LIMIT :limit
            """),
            {"oid": org_id, "q": f"{q}%", "limit": limit},
        )
        return [dict(r) for r in result.mappings().fetchall()]

    async def save_search(self, org_id: UUID, user_id: UUID, req) -> dict:
        result = await self.db.execute(
            text("""
                INSERT INTO search.saved_searches
                  (organization_id, user_id, name, search_type, query, filters, alert_enabled, alert_frequency, is_shared)
                VALUES (:oid, :uid, :name, :stype, :q, :f, :alert, :freq, :shared)
                RETURNING id, name, search_type, query, filters, alert_enabled, is_shared, use_count, created_at
            """),
            {
                "oid": org_id, "uid": user_id, "name": req.name,
                "stype": req.search_type, "q": req.query,
                "f": __import__('json').dumps(req.filters),
                "alert": req.alert_enabled, "freq": req.alert_frequency, "shared": req.is_shared,
            },
        )
        return dict(result.mappings().fetchone())

    async def list_saved_searches(self, org_id: UUID, user_id: UUID) -> list[dict]:
        result = await self.db.execute(
            text("""
                SELECT id, name, search_type, query, filters, alert_enabled, is_shared, use_count, created_at
                FROM search.saved_searches
                WHERE organization_id = :oid AND (user_id = :uid OR is_shared = TRUE)
                  AND deleted_at IS NULL ORDER BY use_count DESC
            """),
            {"oid": org_id, "uid": user_id},
        )
        return [dict(r) for r in result.mappings().fetchall()]

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------
    async def _fts_search(self, org_id: UUID, req: SearchRequest) -> tuple[list[SearchResultItem], int]:
        offset = (req.page - 1) * req.page_size
        if req.search_type in ("company", "all"):
            return await self._search_companies(org_id, req, offset)
        return await self._search_contacts(org_id, req, offset)

    async def _search_companies(self, org_id, req, offset) -> tuple[list, int]:
        conditions = ["c.organization_id = :oid", "c.deleted_at IS NULL"]
        p: dict = {"oid": org_id, "limit": req.page_size, "offset": offset}
        if req.query:
            conditions.append("c.fts @@ websearch_to_tsquery('english', :q)")
            p["q"] = req.query
        for k, v in req.filters.items():
            if k in {"country_code", "industry_name"} and v:
                conditions.append(f"c.{k} = :{k}")
                p[k] = v
        where = " AND ".join(conditions)
        count = (await self.db.execute(text(f"SELECT COUNT(*) FROM core.companies c WHERE {where}"), p)).scalar_one()
        rows = await self.db.execute(
            text(f"SELECT id, 'company' AS entity_type, name, 0.9 AS score, NULL AS domain FROM core.companies c WHERE {where} LIMIT :limit OFFSET :offset"),
            p,
        )
        items = [SearchResultItem(id=r["id"], entity_type="company", name=r["name"], score=r["score"]) for r in rows.mappings().fetchall()]
        return items, count

    async def _search_contacts(self, org_id, req, offset) -> tuple[list, int]:
        conditions = ["c.organization_id = :oid", "c.deleted_at IS NULL"]
        p: dict = {"oid": org_id, "limit": req.page_size, "offset": offset}
        if req.query:
            conditions.append("c.fts @@ websearch_to_tsquery('english', :q)")
            p["q"] = req.query
        where = " AND ".join(conditions)
        count = (await self.db.execute(text(f"SELECT COUNT(*) FROM core.contacts c WHERE {where}"), p)).scalar_one()
        rows = await self.db.execute(
            text(f"SELECT id, 'contact' AS entity_type, full_name AS name, 0.9 AS score FROM core.contacts c WHERE {where} LIMIT :limit OFFSET :offset"),
            p,
        )
        items = [SearchResultItem(id=r["id"], entity_type="contact", name=r["name"] or "", score=r["score"]) for r in rows.mappings().fetchall()]
        return items, count

    async def _semantic_search(self, org_id: UUID, req: SearchRequest) -> tuple[list, int]:
        from app.ai.embeddings import EmbeddingService
        embedding = await EmbeddingService().embed_text(req.query)
        result = await self.db.execute(
            text("""
                SELECT e.entity_id, e.entity_type,
                       1 - (e.embedding <=> :emb::vector) AS score
                FROM ai.embeddings e
                WHERE e.organization_id = :oid AND e.entity_type = :etype
                ORDER BY e.embedding <=> :emb::vector
                LIMIT :limit OFFSET :offset
            """),
            {
                "oid": org_id, "emb": str(embedding),
                "etype": req.search_type if req.search_type != "all" else "company",
                "limit": req.page_size, "offset": (req.page - 1) * req.page_size,
            },
        )
        rows = result.mappings().fetchall()
        items = [SearchResultItem(id=r["entity_id"], entity_type=r["entity_type"], name="", score=float(r["score"])) for r in rows]
        return items, len(items)

    async def _parse_nl_query(self, query: str, search_type: str) -> ParsedSearchIntent:
        """Use Anthropic to parse natural language into structured filters."""
        import json
        from anthropic import AsyncAnthropic
        from app.core.config import settings
        client = AsyncAnthropic(api_key=settings.ANTHROPIC_API_KEY)
        prompt = f"""Parse this search query for a B2B lead intelligence platform into JSON.
Query: "{query}"
Search type: {search_type}

Return JSON with keys: search_type, filters (object), keywords (array), explanation (string), confidence (0-1).
Filters may include: industry, country_code, employee_min, employee_max, technology, seniority_level, is_decision_maker.

Return only valid JSON."""
        msg = await client.messages.create(
            model=settings.ANTHROPIC_MODEL,
            max_tokens=512,
            messages=[{"role": "user", "content": prompt}],
        )
        try:
            parsed = json.loads(msg.content[0].text)
        except Exception:
            parsed = {"search_type": search_type, "filters": {}, "keywords": [query], "explanation": query, "confidence": 0.5}
        return ParsedSearchIntent(raw_query=query, **parsed)

    async def _log_search(self, org_id, user_id, req, total, execution_ms) -> UUID:
        import json
        qid = uuid4()
        try:
            await self.db.execute(
                text("""
                    INSERT INTO search.search_requests
                      (id, organization_id, user_id, search_type, query, filters, result_count, execution_ms)
                    VALUES (:id, :oid, :uid, :stype, :q, :f, :count, :ms)
                """),
                {"id": qid, "oid": org_id, "uid": user_id, "stype": req.search_type,
                 "q": req.query, "f": json.dumps(req.filters), "count": total, "ms": execution_ms},
            )
        except Exception:
            pass
        return qid

    def _cache_key(self, org_id: UUID, req: SearchRequest) -> str:
        import json
        raw = f"{org_id}:{req.search_type}:{req.query}:{json.dumps(req.filters, sort_keys=True)}:{req.page}:{req.page_size}"
        return hashlib.md5(raw.encode()).hexdigest()
