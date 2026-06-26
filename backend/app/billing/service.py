from __future__ import annotations
import uuid
from datetime import datetime, timezone
from uuid import UUID

import stripe
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.billing.models import Subscription, CreditTransaction
from backend.app.billing import stripe_client as sc
from backend.app.common.exceptions import NotFoundError, InsufficientCreditsError


class BillingService:

    async def get_subscription(self, db: AsyncSession, org_id: UUID) -> Subscription | None:
        result = await db.execute(
            select(Subscription).where(Subscription.organization_id == org_id)
        )
        return result.scalar_one_or_none()

    async def create_subscription(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_email: str,
        org_name: str,
        plan: str = "FREE",
    ) -> Subscription:
        existing = await self.get_subscription(db, org_id)

        stripe_customer_id = None
        stripe_subscription_id = None
        status = "active"
        trial_ends_at = None

        if plan != "FREE":
            try:
                stripe_customer_id = await sc.create_customer(user_email, org_name, str(org_id))
                sub_data = await sc.create_subscription(stripe_customer_id, plan)
                stripe_subscription_id = sub_data["subscription_id"]
                status = sub_data["status"]
                if sub_data.get("trial_end"):
                    trial_ends_at = datetime.fromtimestamp(sub_data["trial_end"], tz=timezone.utc)
            except Exception:
                pass  # Fall through to create DB record without Stripe if keys not configured

        credits_monthly = sc.PLAN_CREDITS.get(plan, 100)
        features = sc.PLAN_FEATURES.get(plan, sc.PLAN_FEATURES["FREE"])

        if existing:
            existing.plan = plan
            existing.status = status
            existing.stripe_customer_id = stripe_customer_id or existing.stripe_customer_id
            existing.stripe_subscription_id = stripe_subscription_id or existing.stripe_subscription_id
            existing.credits_monthly = credits_monthly
            existing.credits_remaining = credits_monthly
            existing.features = features
            existing.trial_ends_at = trial_ends_at
            await db.flush()
            return existing

        subscription = Subscription(
            organization_id=org_id,
            plan=plan,
            status=status,
            stripe_customer_id=stripe_customer_id,
            stripe_subscription_id=stripe_subscription_id,
            credits_monthly=credits_monthly,
            credits_remaining=credits_monthly,
            features=features,
            trial_ends_at=trial_ends_at,
        )
        db.add(subscription)
        await db.flush()
        return subscription

    async def change_plan(self, db: AsyncSession, org_id: UUID, new_plan: str) -> Subscription:
        sub = await self.get_subscription(db, org_id)
        if not sub:
            raise NotFoundError("Subscription not found")

        if sub.stripe_subscription_id:
            try:
                await sc.change_plan(sub.stripe_subscription_id, new_plan)
            except Exception:
                pass

        old_credits = sub.credits_monthly
        new_credits = sc.PLAN_CREDITS.get(new_plan, old_credits)

        sub.plan = new_plan
        sub.credits_monthly = new_credits
        sub.features = sc.PLAN_FEATURES.get(new_plan, sub.features)

        if sub.credits_remaining < new_credits:
            sub.credits_remaining = new_credits

        await db.flush()
        return sub

    async def cancel_subscription(self, db: AsyncSession, org_id: UUID, at_period_end: bool = True) -> Subscription:
        sub = await self.get_subscription(db, org_id)
        if not sub:
            raise NotFoundError("Subscription not found")

        if sub.stripe_subscription_id:
            try:
                result = await sc.cancel_subscription(sub.stripe_subscription_id, at_period_end)
                sub.status = result["status"]
            except Exception:
                sub.status = "canceled"
        else:
            sub.status = "canceled"

        await db.flush()
        return sub

    async def get_billing_portal_url(self, db: AsyncSession, org_id: UUID, return_url: str) -> str:
        sub = await self.get_subscription(db, org_id)
        if not sub or not sub.stripe_customer_id:
            raise NotFoundError("No Stripe customer found for this organization")
        return await sc.create_billing_portal_session(sub.stripe_customer_id, return_url)

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
        sub = await self.get_subscription(db, org_id)
        if not sub:
            raise NotFoundError("Subscription not found")
        if sub.credits_remaining < amount:
            raise InsufficientCreditsError(f"Insufficient credits: {sub.credits_remaining} available, {amount} required")

        balance_before = sub.credits_remaining
        sub.credits_remaining -= amount
        balance_after = sub.credits_remaining

        tx = CreditTransaction(
            organization_id=org_id,
            user_id=user_id,
            amount=-amount,
            transaction_type="DEDUCTION",
            balance_before=balance_before,
            balance_after=balance_after,
            description=description,
            entity_type=entity_type,
            entity_id=entity_id,
        )
        db.add(tx)
        await db.flush()
        return tx

    async def add_credits(
        self,
        db: AsyncSession,
        org_id: UUID,
        user_id: UUID,
        amount: int,
        description: str,
        transaction_type: str = "MANUAL_ADJUSTMENT",
    ) -> CreditTransaction:
        sub = await self.get_subscription(db, org_id)
        if not sub:
            raise NotFoundError("Subscription not found")

        balance_before = sub.credits_remaining
        sub.credits_remaining += amount

        tx = CreditTransaction(
            organization_id=org_id,
            user_id=user_id,
            amount=amount,
            transaction_type=transaction_type,
            balance_before=balance_before,
            balance_after=sub.credits_remaining,
            description=description,
        )
        db.add(tx)
        await db.flush()
        return tx

    async def get_credit_balance(self, db: AsyncSession, org_id: UUID) -> dict:
        sub = await self.get_subscription(db, org_id)
        if not sub:
            return {"credits_remaining": 0, "credits_monthly": 0, "plan": "FREE"}
        return {
            "credits_remaining": sub.credits_remaining,
            "credits_monthly": sub.credits_monthly,
            "plan": sub.plan,
        }

    async def list_transactions(
        self, db: AsyncSession, org_id: UUID, page: int = 1, page_size: int = 25
    ) -> tuple[list[CreditTransaction], int]:
        from sqlalchemy import func as sqlfunc
        total = await db.scalar(
            select(sqlfunc.count()).select_from(CreditTransaction)
            .where(CreditTransaction.organization_id == org_id)
        ) or 0
        result = await db.execute(
            select(CreditTransaction)
            .where(CreditTransaction.organization_id == org_id)
            .order_by(CreditTransaction.created_at.desc())
            .offset((page - 1) * page_size)
            .limit(page_size)
        )
        return result.scalars().all(), total

    async def handle_webhook(self, db: AsyncSession, event: stripe.Event) -> None:
        if event.type == "customer.subscription.updated":
            stripe_sub = event.data.object
            result = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == stripe_sub.id
                )
            )
            sub = result.scalar_one_or_none()
            if sub:
                sub.status = stripe_sub.status
                if stripe_sub.current_period_start:
                    sub.period_start = datetime.fromtimestamp(stripe_sub.current_period_start, tz=timezone.utc)
                if stripe_sub.current_period_end:
                    sub.period_end = datetime.fromtimestamp(stripe_sub.current_period_end, tz=timezone.utc)
                new_plan = stripe_sub.metadata.get("plan")
                if new_plan and new_plan in sc.PLAN_CREDITS:
                    sub.plan = new_plan
                    sub.credits_monthly = sc.PLAN_CREDITS[new_plan]
                    sub.features = sc.PLAN_FEATURES[new_plan]
                await db.flush()

        elif event.type == "customer.subscription.deleted":
            stripe_sub = event.data.object
            result = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == stripe_sub.id
                )
            )
            sub = result.scalar_one_or_none()
            if sub:
                sub.status = "canceled"
                await db.flush()

        elif event.type == "invoice.payment_succeeded":
            invoice = event.data.object
            if not invoice.subscription:
                return
            result = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == invoice.subscription
                )
            )
            sub = result.scalar_one_or_none()
            if sub:
                balance_before = sub.credits_remaining
                sub.credits_remaining = sub.credits_monthly
                tx = CreditTransaction(
                    organization_id=sub.organization_id,
                    user_id=None,
                    amount=sub.credits_monthly - balance_before,
                    transaction_type="RENEWAL",
                    balance_before=balance_before,
                    balance_after=sub.credits_monthly,
                    description=f"Monthly credit renewal - {sub.plan}",
                    stripe_invoice_id=invoice.id,
                )
                db.add(tx)
                await db.flush()

        elif event.type == "invoice.payment_failed":
            invoice = event.data.object
            if not invoice.subscription:
                return
            result = await db.execute(
                select(Subscription).where(
                    Subscription.stripe_subscription_id == invoice.subscription
                )
            )
            sub = result.scalar_one_or_none()
            if sub:
                sub.status = "past_due"
                await db.flush()
