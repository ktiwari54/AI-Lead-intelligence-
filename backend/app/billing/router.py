from __future__ import annotations
from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.billing.schemas import (
    AddCreditsRequest, BillingPortalResponse, ChangePlanRequest,
    CreditBalanceResponse, CreditTransactionResponse, CreateSubscriptionRequest,
    SubscriptionResponse, WebhookResponse,
)
from backend.app.billing.service import BillingService
from backend.app.billing.stripe_client import construct_webhook_event
from backend.app.common.deps import get_current_user, get_db
from backend.app.common.exceptions import ForbiddenError
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.users.models import User

router = APIRouter(prefix="/billing", tags=["Billing"])
service = BillingService()


@router.get("/subscription", response_model=APIResponse[SubscriptionResponse])
async def get_subscription(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await service.get_subscription(db, current_user.organization_id)
    if not sub:
        raise HTTPException(status_code=404, detail="No subscription found")
    return APIResponse(data=SubscriptionResponse.model_validate(sub))


@router.post("/subscription", response_model=APIResponse[SubscriptionResponse], status_code=201)
async def create_subscription(
    body: CreateSubscriptionRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await service.create_subscription(
        db, current_user.organization_id,
        current_user.email, current_user.email,
        body.plan,
    )
    return APIResponse(data=SubscriptionResponse.model_validate(sub))


@router.patch("/subscription/plan", response_model=APIResponse[SubscriptionResponse])
async def change_plan(
    body: ChangePlanRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await service.change_plan(db, current_user.organization_id, body.new_plan)
    return APIResponse(data=SubscriptionResponse.model_validate(sub))


@router.delete("/subscription", response_model=APIResponse[SubscriptionResponse])
async def cancel_subscription(
    at_period_end: bool = Query(True),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    sub = await service.cancel_subscription(db, current_user.organization_id, at_period_end)
    return APIResponse(data=SubscriptionResponse.model_validate(sub))


@router.get("/credits", response_model=APIResponse[CreditBalanceResponse])
async def get_credit_balance(
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    balance = await service.get_credit_balance(db, current_user.organization_id)
    return APIResponse(data=CreditBalanceResponse(**balance))


@router.get("/credits/transactions", response_model=PaginatedResponse[CreditTransactionResponse])
async def list_transactions(
    page: int = Query(1, ge=1),
    page_size: int = Query(25, ge=1, le=100),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    txs, total = await service.list_transactions(db, current_user.organization_id, page, page_size)
    items = [CreditTransactionResponse.model_validate(t) for t in txs]
    return PaginatedResponse.create(items=items, total=total, page=page, page_size=page_size)


@router.post("/credits/add", response_model=APIResponse[CreditTransactionResponse])
async def add_credits(
    body: AddCreditsRequest,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    tx = await service.add_credits(
        db, current_user.organization_id, current_user.id,
        body.amount, body.description,
    )
    return APIResponse(data=CreditTransactionResponse.model_validate(tx))


@router.get("/portal", response_model=APIResponse[BillingPortalResponse])
async def get_billing_portal(
    return_url: str = Query(...),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    url = await service.get_billing_portal_url(db, current_user.organization_id, return_url)
    return APIResponse(data=BillingPortalResponse(url=url))


@router.post("/webhooks/stripe", response_model=WebhookResponse)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
):
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")
    try:
        event = construct_webhook_event(payload, sig_header)
    except (stripe.SignatureVerificationError, ValueError):
        raise HTTPException(status_code=400, detail="Invalid webhook signature")

    await service.handle_webhook(db, event)
    return WebhookResponse(received=True)
