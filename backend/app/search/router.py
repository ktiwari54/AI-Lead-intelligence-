from __future__ import annotations
from uuid import UUID
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.search import service
from backend.app.search.schemas import (
    SearchRequest,
    SearchResponse,
    SavedSearchCreate,
    SavedSearchResponse,
    SearchHistoryResponse,
)
from backend.database import get_db
from backend.app.common.deps import get_current_user

router = APIRouter(prefix="/search", tags=["search"])


@router.post("/", response_model=SearchResponse)
async def execute_search(
    request: SearchRequest,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Execute a full-text search across companies and/or contacts."""
    response, _search_id = await service.execute_search(
        db=db,
        org_id=current_user.organization_id,
        request=request,
    )
    return response


@router.get("/history", response_model=dict)
async def get_search_history(
    page: int = 1,
    page_size: int = 25,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Return paginated search history for the current organization."""
    return await service.get_search_history(
        db=db,
        org_id=current_user.organization_id,
        page=page,
        page_size=page_size,
    )


@router.post("/saved", response_model=SavedSearchResponse, status_code=status.HTTP_201_CREATED)
async def save_search(
    create: SavedSearchCreate,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Save a search for later reuse."""
    record = await service.save_search(
        db=db,
        org_id=current_user.organization_id,
        user_id=current_user.id,
        create=create,
    )
    return record


@router.get("/saved", response_model=list[SavedSearchResponse])
async def list_saved_searches(
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """List all saved searches for the current organization."""
    return await service.list_saved_searches(
        db=db,
        org_id=current_user.organization_id,
    )


@router.delete("/saved/{saved_search_id}", status_code=status.HTTP_204_NO_CONTENT)
async def delete_saved_search(
    saved_search_id: UUID,
    db: AsyncSession = Depends(get_db),
    current_user=Depends(get_current_user),
):
    """Delete a saved search by ID."""
    from sqlalchemy import select, delete
    from backend.app.search.models import SavedSearch

    result = await db.execute(
        select(SavedSearch).where(
            SavedSearch.id == saved_search_id,
            SavedSearch.organization_id == current_user.organization_id,
        )
    )
    record = result.scalar_one_or_none()
    if record is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Saved search not found")

    await db.execute(
        delete(SavedSearch).where(SavedSearch.id == saved_search_id)
    )
    await db.commit()
