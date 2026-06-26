"""Search endpoints."""
from fastapi import APIRouter, Query

from app.common.dependencies import DbDep, UserDep
from app.search.schemas import (
    AutocompleteRequest,
    NLSearchRequest,
    SavedSearchCreate,
    SavedSearchResponse,
    SearchRequest,
    SearchResponse,
)
from app.search.service import SearchService

router = APIRouter()


@router.post("", response_model=SearchResponse)
async def search(req: SearchRequest, user: UserDep, db: DbDep) -> SearchResponse:
    """Execute a structured search with filters."""
    user.require_permission("searches:read")
    return await SearchService(db).search(user.org_id, user.user_id, req)


@router.post("/nl", response_model=SearchResponse)
async def nl_search(req: NLSearchRequest, user: UserDep, db: DbDep) -> SearchResponse:
    """Natural language search — AI parses the query into filters."""
    user.require_permission("searches:read")
    return await SearchService(db).nl_search(user.org_id, user.user_id, req)


@router.get("/autocomplete")
async def autocomplete(
    user: UserDep,
    db: DbDep,
    q: str = Query(min_length=1, max_length=100),
    search_type: str = Query(default="company"),
    limit: int = Query(default=10, ge=1, le=20),
) -> list:
    """Autocomplete suggestions for search input."""
    return await SearchService(db).autocomplete(user.org_id, q, search_type, limit)


@router.post("/saved", response_model=SavedSearchResponse, status_code=201)
async def save_search(req: SavedSearchCreate, user: UserDep, db: DbDep) -> dict:
    """Save a search for later use or alerts."""
    user.require_permission("searches:create")
    return await SearchService(db).save_search(user.org_id, user.user_id, req)


@router.get("/saved", response_model=list[SavedSearchResponse])
async def list_saved_searches(user: UserDep, db: DbDep) -> list:
    """List saved searches."""
    user.require_permission("searches:read")
    return await SearchService(db).list_saved_searches(user.org_id, user.user_id)


@router.delete("/saved/{search_id}")
async def delete_saved_search(search_id: str, user: UserDep, db: DbDep) -> dict:
    """Delete a saved search."""
    user.require_permission("searches:delete")
    from sqlalchemy import text
    await db.execute(
        text("UPDATE search.saved_searches SET deleted_at = NOW() WHERE id = :id AND organization_id = :oid"),
        {"id": search_id, "oid": user.org_id},
    )
    return {"message": "Saved search deleted"}
