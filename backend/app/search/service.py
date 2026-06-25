import uuid
from datetime import datetime, timezone
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, func

from backend.app.search.models import Search, SearchResult, SavedSearch
from backend.app.search.schemas import SearchRequest, SavedSearchCreate
from backend.app.common.exceptions import NotFoundError
from backend.app.common.pagination import PaginationParams


class SearchService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def execute_search(
        self, org_id: uuid.UUID, user_id: uuid.UUID, request: SearchRequest
    ) -> Search:
        search = Search(
            organization_id=org_id,
            created_by=user_id,
            query=request.query,
            filters=request.filters,
            search_type=request.search_type,
            status="pending",
        )
        self.db.add(search)
        await self.db.flush()

        # Dispatch async task for actual search execution
        from backend.workers.tasks.enrichment import execute_search_task
        execute_search_task.delay(str(search.id))

        return search

    async def get_search_history(
        self, org_id: uuid.UUID, pagination: PaginationParams
    ) -> tuple[list[Search], int]:
        stmt = select(Search).where(
            Search.organization_id == org_id, Search.deleted_at.is_(None)
        ).order_by(Search.created_at.desc())
        count = await self.db.execute(select(func.count()).select_from(stmt.subquery()))
        total = count.scalar()
        result = await self.db.execute(stmt.offset(pagination.offset).limit(pagination.per_page))
        return result.scalars().all(), total

    async def save_search(
        self, org_id: uuid.UUID, user_id: uuid.UUID, data: SavedSearchCreate
    ) -> SavedSearch:
        saved = SavedSearch(
            organization_id=org_id,
            created_by=user_id,
            **data.model_dump(),
        )
        self.db.add(saved)
        await self.db.flush()
        return saved
