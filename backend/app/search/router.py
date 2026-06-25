import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession

from backend.database import get_db
from backend.app.search.schemas import SearchRequest, SavedSearchCreate, SearchResponse
from backend.app.search.service import SearchService
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.common.pagination import pagination_params, PaginationParams
from backend.app.common.deps import get_current_user_id, get_current_org_id

router = APIRouter()


@router.post("/", response_model=APIResponse[SearchResponse], status_code=202)
async def run_search(
    request: SearchRequest,
    user_id: uuid.UUID = Depends(get_current_user_id),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    search = await SearchService(db).execute_search(org_id, user_id, request)
    return APIResponse(data=SearchResponse.model_validate(search), message="Search queued")


@router.get("/history", response_model=PaginatedResponse[SearchResponse])
async def get_history(
    pagination: PaginationParams = Depends(pagination_params),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    searches, total = await SearchService(db).get_search_history(org_id, pagination)
    return PaginatedResponse.create(
        data=[SearchResponse.model_validate(s) for s in searches],
        total=total, page=pagination.page, per_page=pagination.per_page,
    )


@router.post("/saved", response_model=APIResponse, status_code=201)
async def save_search(
    data: SavedSearchCreate,
    user_id: uuid.UUID = Depends(get_current_user_id),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    saved = await SearchService(db).save_search(org_id, user_id, data)
    return APIResponse(message="Search saved", data={"id": str(saved.id)})
