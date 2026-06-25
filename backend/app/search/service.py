import time
from uuid import UUID
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select, or_
from app.models.search import Search, SearchResult, SavedSearch
from app.models.companies import Company
from app.models.contacts import Contact
from app.search.schemas import SearchRequest, SavedSearchCreate


async def run_search(data: SearchRequest, org_id: UUID, user_id: UUID, db: AsyncSession) -> Search:
    search = Search(
        organization_id=org_id,
        created_by=user_id,
        query=data.query,
        filters=data.filters,
        search_type=data.search_type,
        status="running",
    )
    db.add(search)
    await db.flush()

    start = time.monotonic()
    results = []

    if data.search_type in ("company", "mixed") and data.query:
        companies = (await db.execute(
            select(Company)
            .where(Company.organization_id == org_id, Company.is_deleted == False,
                   Company.company_name.ilike(f"%{data.query}%"))
            .limit(data.page_size)
        )).scalars().all()
        for rank, c in enumerate(companies):
            results.append(SearchResult(search_id=search.id, company_id=c.id, rank=rank + 1, source="database"))

    if data.search_type in ("contact", "mixed") and data.query:
        contacts = (await db.execute(
            select(Contact)
            .where(Contact.organization_id == org_id, Contact.is_deleted == False,
                   or_(Contact.full_name.ilike(f"%{data.query}%"),
                       Contact.email.ilike(f"%{data.query}%"),
                       Contact.designation.ilike(f"%{data.query}%")))
            .limit(data.page_size)
        )).scalars().all()
        for rank, c in enumerate(contacts):
            results.append(SearchResult(search_id=search.id, contact_id=c.id, rank=rank + 1, source="database"))

    for r in results:
        db.add(r)

    search.status = "completed"
    search.result_count = len(results)
    search.execution_time_ms = int((time.monotonic() - start) * 1000)
    return search


async def save_search(data: SavedSearchCreate, org_id: UUID, user_id: UUID, db: AsyncSession) -> SavedSearch:
    saved = SavedSearch(
        organization_id=org_id,
        created_by=user_id,
        **data.model_dump(),
    )
    db.add(saved)
    await db.flush()
    return saved
