from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from app.core.database import get_db
from app.common.dependencies import get_current_org
from app.models.billing import Subscription
from app.billing.schemas import SubscriptionOut
from app.core.exceptions import NotFoundError

router = APIRouter()


@router.get("/subscription", response_model=SubscriptionOut)
async def get_subscription(db: AsyncSession = Depends(get_db), org=Depends(get_current_org)):
    result = await db.execute(select(Subscription).where(Subscription.organization_id == org.id))
    sub = result.scalar_one_or_none()
    if not sub:
        raise NotFoundError("No subscription found")
    return sub
