"""Billing service: manages subscriptions and credits."""
from __future__ import annotations

from datetime import datetime, timezone
from typing import Any
from uuid import UUID

import stripe
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.billing.models import CreditTransaction, Subscription
from backend.app.billing.stripe_client import (
    PLAN_CREDITS,
    PLAN_FEATURES,
    cancel_subscription as stripe_cancel,
    change_plan as stripe_change_plan,
    construct_webhook_event,
    create_billing_portal_session,
    create_customer,
    create_subscription as stripe_create_subscription,
)


class InsufficientCreditsError(Exception):
    """Raised when an org does not have enough credits."""


class BillingService:
    # ------------------------------------------------------------------
    # Subscription helpers
    # ------------------------------------------------------------------

    async def get_subscription(self, db: AsyncSession, org_id: UUID) -> Subscription | None:
        """Return the subscription for an org, or None."""
        result = await db.execute(
            select(Subscription).where(Subscription.org_id == org_id)
        )
        return result.scalar_one_or_none()

    async def create_subscription(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_email: str,
        org_name: str,
        plan: str = "FREE",
        trial_days: int = 14,
    ) -> Subscription:
        """Create (or re-activate) a subscription for an org."""
        existing = await self.get_subscription(db, org_id)

        # Determine or create Stripe customer
        stripe_customer_id: str | None = None
        if existing and existing.stripe_customer_id:
            stripe_customer_id = existing.stripe_customer_id
        else:
            stripe_customer_id = await create_customer(
                email=user_email,
                name=org_name,
                org_id=str(org_id),
            )

        stripe_subscription_id: str | None = None
        status = "active"
        period_start: datetime | None = None
        period_end: datetime | None = None
        trial_ends_at: datetime | None = None

        if plan != "FREE":
            sub_data = await stripe_create_subscription(
                customer_id=stripe_customer_id,
                plan=plan,
                trial_days=trial_days,
            )
            stripe_subscription_id = sub_data["subscription_id"]
            status = sub_data["status"]
            if sub_data.get("current_period_end"):
                period_end = datetime.fromtimestamp(
                    sub_data["current_period_end"], tz=timezone.utc
                )
            if sub_data.get("trial_end"):
                trial_ends_at = datetime.fromtimestamp(
                    sub_data["trial_end"], tz=timezone.utc
                )
            period_start = datetime.now(tz=timezone.utc)

        credits_monthly = PLAN_CREDITS[plan]
        features = PLAN_FEATURES[plan]

        if existing:
            existing.plan = plan
            existing.status = status
            existing.stripe_customer_id = stripe_customer_id
            existing.stripe_subscription_id = stripe_subscription_id
            existing.credits_monthly = credits_monthly
            existing.credits_remaining = credits_monthly
            existing.features = features
            existing.period_start = period_start
            existing.period_end = period_end
            existing.trial_ends_at = trial_ends_at
            db.add(existing)
            await db.commit()
            await db.refresh(existing)
            return existing

        subscription = Subscription(
            org_id=org_id,
            plan=plan,
            status=status,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            credits_monthly=credits_monthly,
            credits_remaining=credits_monthly,
            features=features,
            period_start=period_start,
            period_end=period_end,
            trial_ends_at=trial_ends_at,
        )
        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        return subscription

    async def change_plan(
        self, db: AsyncSession, org_id: UUID, new_plan: str
    ) -> Subscription:
        """Upgrade or downgrade a subscription's plan."""
        subscription = await self._require_subscription(db, org_id)

        if subscription.stripe_subscription_id:
            await stripe_change_plan(
                subscription_id=subscription.stripe_subscription_id,
                new_plan=new_plan,
            )

        new_credits_monthly = PLAN_CREDITS[new_plan]
        new_features = PLAN_FEATURES[new_plan]

        subscription.plan = new_plan
        subscription.credits_monthly = new_credits_monthly
        subscription.features = new_features

        # Top up credits if upgrading to a higher allowance
        if subscription.credits_remaining < new_credits_monthly:
            subscription.credits_remaining = new_credits_monthly

        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        return subscription

    async def cancel_subscription(
        self, db: AsyncSession, org_id: UUID, at_period_end: bool = True
    ) -> Subscription:
        """Cancel a subscription."""
        subscription = await self._require_subscription(db, org_id)

        if subscription.stripe_subscription_id:
            result = await stripe_cancel(
                subscription_id=subscription.stripe_subscription_id,
                at_period_end=at_period_end,
            )
            subscription.status = result["status"]
        else:
            subscription.status = "canceled"

        db.add(subscription)
        await db.commit()
        await db.refresh(subscription)
        return subscription

    async def get_billing_portal_url(
        self, db: AsyncSession, org_id: UUID, return_url: str
    ) -> str:
        """Return a Stripe customer portal URL."""
        subscription = await self._require_subscription(db, org_id)
        if not subscription.stripe_customer_id:
            raise ValueError("No Stripe customer associated with this organization.")
        url = await create_billing_portal_session(
            customer_id=subscription.stripe_customer_id,
            return_url=return_url,
        )
        return url

    # ------------------------------------------------------------------
    # Credit helpers
    # ------------------------------------------------------------------

    async def deduct_credits(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        amount: int,
        description: str,
        entity_type: str | None = None,
        entity_id: str | None = None,
    ) -> CreditTransaction:
        """Deduct credits from an org subscription. Raises InsufficientCreditsError if balance is too low."""
        subscription = await self._require_subscription(db, org_id)

        if subscription.credits_remaining < amount:
            raise InsufficientCreditsError(
                f"Insufficient credits: need {amount}, have {subscription.credits_remaining}."
            )

        balance_before = subscription.credits_remaining
        subscription.credits_remaining -= amount
        balance_after = subscription.credits_remaining

        transaction = CreditTransaction(
            org_id=org_id,
            user_id=user_id,
            amount=-amount,
            transaction_type="USAGE",
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        db.add(subscription)
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction

    async def add_credits(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID | None,
        amount: int,
        description: str,
        transaction_type: str = "MANUAL_ADJUSTMENT",
        stripe_invoice_id: str | None = None,
    ) -> CreditTransaction:
        """Add credits to an org subscription."""
        subscription = await self._require_subscription(db, org_id)

        balance_before = subscription.credits_remaining
        subscription.credits_remaining += amount
        balance_after = subscription.credits_remaining

        transaction = CreditTransaction(
            org_id=org_id,
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            stripe_invoice_id=stripe_invoice_id,
        )
        db.add(subscription)
        db.add(transaction)
        await db.commit()
        await db.refresh(transaction)
        return transaction

    async def get_credit_balance(self, db: AsyncSession, org_id: UUID) -> dict:
        """Return current credit balance info for an org."""
        subscription = await self._require_subscription(db, org_id)
        return {
            "credits_remaining": subscription.credits_remaining,
            "credits_monthly": subscription.credits_monthly,
            "plan": subscription.plan,
        }

    async def list_transactions(
        self,
        db: AsyncSession,
        org_id: UUID,
        page: int = 1,
        page_size: int = 25,
    ) -> tuple[list[CreditTransaction], int]:
        """Return a paginated list of credit transactions for an org, newest first."""
        offset = (page - 1) * page_size

        count_result = await db.execute(
            select(func.count()).select_from(CreditTransaction).where(
                CreditTransaction.org_id == org_id
            )
        )
        total = count_result.scalar_one()

        rows_result = await db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.org_id == org_id)
            .order_by(CreditTransaction.created_at.desc())
            .offset(offset)
            .limit(page_size)
        )
        transactions = list(rows_result.scalars().all())
        return transactions, total

    # ------------------------------------------------------------------
    # Webhook handler
    # ------------------------------------------------------------------

    async def handle_webhook(self, db: AsyncSession, event: stripe.Event) -> None:
        """Process Stripe webhook events and update DB state."""
        event_type: str = event["type"]
        data_object: dict[str, Any] = event["data"]["object"]

        if event_type == "customer.subscription.updated":
            await self._sync_subscription_from_stripe(db, data_object)

        elif event_type == "customer.subscription.deleted":
            stripe_sub_id = data_object.get("id")
            subscription = await self._find_by_stripe_sub(db, stripe_sub_id)
            if subscription:
                subscription.status = "canceled"
                db.add(subscription)
                await db.commit()

        elif event_type == "invoice.payment_succeeded":
            stripe_sub_id = data_object.get("subscription")
            stripe_invoice_id = data_object.get("id")
            subscription = await self._find_by_stripe_sub(db, stripe_sub_id)
            if subscription:
                balance_before = subscription.credits_remaining
                subscription.credits_remaining = subscription.credits_monthly
                transaction = CreditTransaction(
                    org_id=subscription.org_id,
                    user_id=None,
                    amount=subscription.credits_monthly,
                    transaction_type="RENEWAL",
                    balance_before=balance_before,
                    balance_after=subscription.credits_monthly,
                    description="Monthly credit renewal",
                    stripe_invoice_id=stripe_invoice_id,
                )
                db.add(subscription)
                db.add(transaction)
                await db.commit()

        elif event_type == "invoice.payment_failed":
            stripe_sub_id = data_object.get("subscription")
            subscription = await self._find_by_stripe_sub(db, stripe_sub_id)
            if subscription:
                subscription.status = "past_due"
                db.add(subscription)
                await db.commit()

    # ------------------------------------------------------------------
    # Internal helpers
    # ------------------------------------------------------------------

    async def _require_subscription(
        self, db: AsyncSession, org_id: UUID
    ) -> Subscription:
        subscription = await self.get_subscription(db, org_id)
        if not subscription:
            raise ValueError(f"No subscription found for organization {org_id}.")
        return subscription

    async def _find_by_stripe_sub(
        self, db: AsyncSession, stripe_sub_id: str | None
    ) -> Subscription | None:
        if not stripe_sub_id:
            return None
        result = await db.execute(
            select(Subscription).where(
                Subscription.stripe_subscription_id == stripe_sub_id
            )
        )
        return result.scalar_one_or_none()

    async def _sync_subscription_from_stripe(
        self, db: AsyncSession, stripe_sub: dict[str, Any]
    ) -> None:
        """Update a DB subscription record from a Stripe subscription object."""
        stripe_sub_id = stripe_sub.get("id")
        subscription = await self._find_by_stripe_sub(db, stripe_sub_id)
        if not subscription:
            return

        subscription.status = stripe_sub.get("status", subscription.status)

        # Update plan from metadata if present
        new_plan = stripe_sub.get("metadata", {}).get("plan")
        if new_plan and new_plan in PLAN_CREDITS:
            subscription.plan = new_plan
            subscription.credits_monthly = PLAN_CREDITS[new_plan]
            subscription.features = PLAN_FEATURES[new_plan]

        period_start_ts = stripe_sub.get("current_period_start")
        period_end_ts = stripe_sub.get("current_period_end")
        trial_end_ts = stripe_sub.get("trial_end")

        if period_start_ts:
            subscription.period_start = datetime.fromtimestamp(
                period_start_ts, tz=timezone.utc
            )
        if period_end_ts:
            subscription.period_end = datetime.fromtimestamp(
                period_end_ts, tz=timezone.utc
            )
        if trial_end_ts:
            subscription.trial_ends_at = datetime.fromtimestamp(
                trial_end_ts, tz=timezone.utc
            )

        db.add(subscription)
        await db.commit()
