import uuid
from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select

from backend.database import get_db
from backend.app.billing.models import Subscription, CreditTransaction
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.common.pagination import pagination_params, PaginationParams
from backend.app.common.deps import get_current_org_id

router = APIRouter()


@router.get("/subscription", response_model=APIResponse)
async def get_subscription(
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    result = await db.execute(
        select(Subscription)
        .where(Subscription.organization_id == org_id, Subscription.status == "active")
        .order_by(Subscription.created_at.desc())
        .limit(1)
    )
    sub = result.scalar_one_or_none()
    if not sub:
        return APIResponse(data=None, message="No active subscription")
    return APIResponse(data=sub.to_dict())


@router.get("/credits/history", response_model=PaginatedResponse)
async def get_credit_history(
    pagination: PaginationParams = Depends(pagination_params),
    org_id: uuid.UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
):
    stmt = select(CreditTransaction).where(
        CreditTransaction.organization_id == org_id
    ).order_by(CreditTransaction.created_at.desc())
    from sqlalchemy import func
    count = await db.execute(select(func.count()).select_from(stmt.subquery()))
    total = count.scalar()
    result = await db.execute(stmt.offset(pagination.offset).limit(pagination.per_page))
    txns = [t.to_dict() for t in result.scalars().all()]
    return PaginatedResponse.create(data=txns, total=total, page=pagination.page, per_page=pagination.per_page)
