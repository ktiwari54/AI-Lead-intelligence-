from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.core.database import get_db
from app.common.dependencies import get_current_user
from app.enrichment import service
from app.enrichment.schemas import EmailVerifyRequest, EmailVerifyResponse

router = APIRouter()


@router.post("/email/verify", response_model=EmailVerifyResponse)
async def verify_email(
    data: EmailVerifyRequest,
    db: AsyncSession = Depends(get_db),
    user=Depends(get_current_user),
):
    return await service.verify_email(data, db)
