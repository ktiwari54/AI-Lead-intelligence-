from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.common.dependencies import get_current_user, get_current_org
from app.search import service
from app.search.schemas import SearchRequest, SearchOut, SavedSearchCreate, SavedSearchOut

router = APIRouter()


@router.post("", response_model=SearchOut, status_code=201)
async def run_search(
    data: SearchRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    org=Depends(get_current_org),
):
    return await service.run_search(data, org.id, user.id, db)


@router.post("/saved", response_model=SavedSearchOut, status_code=201)
async def save_search(
    data: SavedSearchCreate,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
    org=Depends(get_current_org),
):
    return await service.save_search(data, org.id, user.id, db)
