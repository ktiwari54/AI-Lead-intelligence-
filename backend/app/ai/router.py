from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.common.dependencies import get_current_user
from app.ai import service
from app.ai.schemas import ScoreRequest, ScoreResponse, NLQueryRequest, NLQueryResponse

router = APIRouter()


@router.post("/score", response_model=ScoreResponse)
async def score_lead(data: ScoreRequest, db: AsyncSession = Depends(get_db), user=Depends(get_current_user)):
    return await service.score_lead(data, db)


@router.post("/nl-query", response_model=NLQueryResponse)
async def nl_query(data: NLQueryRequest, user=Depends(get_current_user)):
    result = await service.process_nl_query(data.query)
    return result
