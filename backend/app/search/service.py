from __future__ import annotations
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.search import search_engine
from backend.app.search.schemas import SearchRequest, SearchResponse, SavedSearchCreate, SearchHitResponse
from backend.app.search.search_engine import SearchFilters
from backend.app.search.models import Search, SearchResult, SavedSearch


def _request_to_filters(request: SearchRequest) -> SearchFilters:
    return SearchFilters(
        query=request.query,
        entity_type=request.entity_type,
        industries=request.industries,
        countries=request.countries,
        seniority_levels=request.seniority_levels,
        departments=request.departments,
        technologies=request.technologies,
        min_employees=request.min_employees,
        max_employees=request.max_employees,
        min_revenue=request.min_revenue,
        max_revenue=request.max_revenue,
        min_score=request.min_score,
        email_status=request.email_status,
        has_phone=request.has_phone,
        has_linkedin=request.has_linkedin,
        page=request.page,
        page_size=request.page_size,
        sort_by=request.sort_by,
        sort_order=request.sort_order,
    )


async def execute_search(
    db: AsyncSession,
    org_id: UUID,
    request: SearchRequest,
) -> tuple[SearchResponse, UUID]:
    filters = _request_to_filters(request)
    engine_response = await search_engine.execute_search(str(org_id), filters)

    # Persist search record
    search_record = Search(
        organization_id=org_id,
        filters=request.model_dump(),
        result_count=engine_response.total,
    )
    db.add(search_record)
    await db.flush()  # get search_record.id

    # Persist top results
    for rank, hit in enumerate(engine_response.hits, start=1):
        result = SearchResult(
            search_id=search_record.id,
            entity_id=hit.id,
            entity_type=hit.entity_type,
            rank=rank,
            score=hit.score,
        )
        db.add(result)

    await db.commit()

    hits = [
        SearchHitResponse(
            id=hit.id,
            entity_type=hit.entity_type,
            score=hit.score,
            data=hit.data,
            highlight=hit.highlight,
        )
        for hit in engine_response.hits
    ]

    response = SearchResponse(
        total=engine_response.total,
        page=engine_response.page,
        page_size=engine_response.page_size,
        hits=hits,
        took_ms=engine_response.took_ms,
        aggregations=engine_response.aggregations,
    )
    return response, search_record.id


async def get_search_history(
    db: AsyncSession,
    org_id: UUID,
    page: int = 1,
    page_size: int = 25,
) -> dict:
    offset = (page - 1) * page_size
    total_q = await db.execute(
        select(func.count()).select_from(Search).where(Search.organization_id == org_id)
    )
    total = total_q.scalar_one()

    result_q = await db.execute(
        select(Search)
        .where(Search.organization_id == org_id)
        .order_by(Search.created_at.desc())
        .offset(offset)
        .limit(page_size)
    )
    records = result_q.scalars().all()

    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "items": records,
    }


async def save_search(
    db: AsyncSession,
    org_id: UUID,
    user_id: UUID,
    create: SavedSearchCreate,
) -> SavedSearch:
    record = SavedSearch(
        organization_id=org_id,
        user_id=user_id,
        name=create.name,
        description=create.description,
        filters=create.filters,
    )
    db.add(record)
    await db.commit()
    await db.refresh(record)
    return record


async def list_saved_searches(
    db: AsyncSession,
    org_id: UUID,
) -> list[SavedSearch]:
    result_q = await db.execute(
        select(SavedSearch)
        .where(SavedSearch.organization_id == org_id)
        .order_by(SavedSearch.created_at.desc())
    )
    return result_q.scalars().all()
