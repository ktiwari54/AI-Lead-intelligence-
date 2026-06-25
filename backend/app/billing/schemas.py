from pydantic import BaseModel
from typing import Optional, List
from uuid import UUID
from datetime import datetime


class SubscriptionOut(BaseModel):
    id: UUID
    organization_id: UUID
    plan: str
    status: str
    credits_included: int
    credits_remaining: int
    renewal_date: Optional[datetime] = None
    trial_end_date: Optional[datetime] = None
    model_config = {"from_attributes": True}


class CreditTransactionOut(BaseModel):
    id: UUID
    transaction_type: str
    credits: int
    balance_after: int
    description: Optional[str] = None
    created_at: datetime
    model_config = {"from_attributes": True}
