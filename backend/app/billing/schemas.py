"""Pydantic schemas for billing endpoints."""
from datetime import datetime
from typing import Literal
from uuid import UUID

from pydantic import BaseModel


class SubscriptionResponse(BaseModel):
    id: UUID
    organization_id: UUID
    plan: str
    status: str
    credits_monthly: int
    credits_remaining: int
    features: dict
    period_start: datetime | None = None
    period_end: datetime | None = None
    trial_ends_at: datetime | None = None
    stripe_customer_id: str | None = None

    model_config = {"from_attributes": True}


class CreateSubscriptionRequest(BaseModel):
    plan: Literal["FREE", "STARTER", "PRO", "ENTERPRISE"] = "FREE"
    trial_days: int = 14


class ChangePlanRequest(BaseModel):
    new_plan: Literal["STARTER", "PRO", "ENTERPRISE"]


class CreditTransactionResponse(BaseModel):
    id: UUID
    amount: int
    transaction_type: str
    balance_before: int
    balance_after: int
    description: str | None = None
    entity_type: str | None = None
    created_at: datetime

    model_config = {"from_attributes": True}


class CreditBalanceResponse(BaseModel):
    credits_remaining: int
    credits_monthly: int
    plan: str


class BillingPortalResponse(BaseModel):
    url: str


class WebhookResponse(BaseModel):
    received: bool
