"""FastAPI router for billing endpoints."""
from __future__ import annotations

from uuid import UUID

import stripe
from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.billing.schemas import (
    BillingPortalResponse,
    ChangePlanRequest,
    CreateSubscriptionRequest,
    CreditBalanceResponse,
    CreditTransactionResponse,
    SubscriptionResponse,
    WebhookResponse,
)
from backend.app.billing.service import BillingService, InsufficientCreditsError
from backend.app.billing.stripe_client import construct_webhook_event

router = APIRouter(prefix="/billing", tags=["billing"])


# ---------------------------------------------------------------------------
# Dependency stubs – replace with your actual auth / DB dependencies
# ---------------------------------------------------------------------------

async def get_db() -> AsyncSession:  # pragma: no cover
    """Override or replace with the project's real DB session dependency."""
    raise NotImplementedError("get_db dependency must be configured")


async def get_current_org_id() -> UUID:  # pragma: no cover
    """Override or replace with the project's real auth dependency."""
    raise NotImplementedError("get_current_org_id dependency must be configured")


async def get_current_user_id() -> UUID:  # pragma: no cover
    """Override or replace with the project's real auth dependency."""
    raise NotImplementedError("get_current_user_id dependency must be configured")


async def require_admin(
    user_id: UUID = Depends(get_current_user_id),
) -> UUID:  # pragma: no cover
    """Enforce admin role. Replace with actual role-check logic."""
    return user_id


def get_billing_service() -> BillingService:
    return BillingService()


# ---------------------------------------------------------------------------
# Subscription endpoints
# ---------------------------------------------------------------------------


@router.get("/subscription", response_model=SubscriptionResponse)
async def get_subscription(
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    service: BillingService = Depends(get_billing_service),
):
    """Return the current subscription for the authenticated org."""
    subscription = await service.get_subscription(db, org_id)
    if not subscription:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="No subscription found for this organization.",
        )
    return subscription


@router.post("/subscription", response_model=SubscriptionResponse, status_code=status.HTTP_201_CREATED)
async def create_subscription(
    body: CreateSubscriptionRequest,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    service: BillingService = Depends(get_billing_service),
):
    """Create a new subscription for the authenticated org."""
    try:
        subscription = await service.create_subscription(
            db=db,
            org_id=org_id,
            # user_email and org_name should come from auth context in real usage;
            # callers can override these deps to supply real values.
            user_email="",
            org_name="",
            plan=body.plan,
            trial_days=body.trial_days,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return subscription


@router.patch("/subscription/plan", response_model=SubscriptionResponse)
async def change_plan(
    body: ChangePlanRequest,
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    service: BillingService = Depends(get_billing_service),
):
    """Upgrade or downgrade the subscription plan."""
    try:
        subscription = await service.change_plan(db, org_id, body.new_plan)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return subscription


@router.delete("/subscription", response_model=SubscriptionResponse)
async def cancel_subscription(
    at_period_end: bool = Query(default=True),
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    service: BillingService = Depends(get_billing_service),
):
    """Cancel the subscription, optionally at period end."""
    try:
        subscription = await service.cancel_subscription(db, org_id, at_period_end)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return subscription


# ---------------------------------------------------------------------------
# Credit endpoints
# ---------------------------------------------------------------------------


@router.get("/credits", response_model=CreditBalanceResponse)
async def get_credit_balance(
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    service: BillingService = Depends(get_billing_service),
):
    """Return the current credit balance for the authenticated org."""
    try:
        balance = await service.get_credit_balance(db, org_id)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(exc))
    return balance


@router.get("/credits/transactions", response_model=list[CreditTransactionResponse])
async def list_transactions(
    page: int = Query(default=1, ge=1),
    page_size: int = Query(default=25, ge=1, le=100),
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    service: BillingService = Depends(get_billing_service),
):
    """Return paginated credit transaction history for the authenticated org."""
    transactions, _total = await service.list_transactions(db, org_id, page, page_size)
    return transactions


@router.post("/credits/add", response_model=CreditTransactionResponse)
async def add_credits(
    amount: int = Query(..., ge=1),
    description: str = Query(...),
    org_id: UUID = Depends(get_current_org_id),
    user_id: UUID = Depends(require_admin),
    db: AsyncSession = Depends(get_db),
    service: BillingService = Depends(get_billing_service),
):
    """Admin-only: add credits to the org's subscription."""
    try:
        transaction = await service.add_credits(
            db=db,
            org_id=org_id,
            user_id=user_id,
            amount=amount,
            description=description,
        )
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return transaction


# ---------------------------------------------------------------------------
# Billing portal
# ---------------------------------------------------------------------------


@router.get("/portal", response_model=BillingPortalResponse)
async def get_billing_portal(
    return_url: str = Query(...),
    org_id: UUID = Depends(get_current_org_id),
    db: AsyncSession = Depends(get_db),
    service: BillingService = Depends(get_billing_service),
):
    """Return a Stripe Customer Portal URL for the authenticated org."""
    try:
        url = await service.get_billing_portal_url(db, org_id, return_url)
    except ValueError as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(exc))
    return BillingPortalResponse(url=url)


# ---------------------------------------------------------------------------
# Stripe webhook (no auth)
# ---------------------------------------------------------------------------


@router.post("/webhooks/stripe", response_model=WebhookResponse, include_in_schema=False)
async def stripe_webhook(
    request: Request,
    db: AsyncSession = Depends(get_db),
    service: BillingService = Depends(get_billing_service),
):
    """Receive and process Stripe webhook events."""
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = construct_webhook_event(payload, sig_header)
    except stripe.errors.SignatureVerificationError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid Stripe webhook signature.",
        )
    except Exception as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Webhook error: {exc}",
        )

    await service.handle_webhook(db, event)
    return WebhookResponse(received=True)
