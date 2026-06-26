"""Stripe client wrapper."""
import stripe
from functools import lru_cache
from backend.config import get_settings

settings = get_settings()

PLAN_CREDITS = {
    "FREE": 100,
    "STARTER": 1000,
    "PRO": 5000,
    "ENTERPRISE": 25000,
}

PLAN_FEATURES = {
    "FREE": {"max_contacts": 100, "max_companies": 50, "ai_scoring": False, "bulk_export": False, "api_access": False, "connectors": []},
    "STARTER": {"max_contacts": 1000, "max_companies": 500, "ai_scoring": True, "bulk_export": False, "api_access": True, "connectors": ["hunter"]},
    "PRO": {"max_contacts": 10000, "max_companies": 5000, "ai_scoring": True, "bulk_export": True, "api_access": True, "connectors": ["hunter", "apollo", "clearbit"]},
    "ENTERPRISE": {"max_contacts": -1, "max_companies": -1, "ai_scoring": True, "bulk_export": True, "api_access": True, "connectors": ["hunter", "apollo", "clearbit", "custom"]},
}

def _plan_price_ids() -> dict:
    return {
        "STARTER": settings.STRIPE_PRICE_ID_STARTER,
        "PRO": settings.STRIPE_PRICE_ID_PRO,
        "ENTERPRISE": settings.STRIPE_PRICE_ID_ENTERPRISE,
    }


def get_stripe_client() -> stripe.StripeClient:
    return stripe.StripeClient(api_key=settings.STRIPE_SECRET_KEY)


async def create_customer(email: str, name: str, org_id: str) -> str:
    client = get_stripe_client()
    customer = client.customers.create(params={
        "email": email,
        "name": name,
        "metadata": {"organization_id": org_id},
    })
    return customer.id


async def create_subscription(customer_id: str, plan: str, trial_days: int = 14) -> dict:
    price_id = _plan_price_ids().get(plan)
    if not price_id:
        raise ValueError(f"No Stripe price ID configured for plan {plan}")
    client = get_stripe_client()
    sub = client.subscriptions.create(params={
        "customer": customer_id,
        "items": [{"price": price_id}],
        "trial_period_days": trial_days,
        "payment_behavior": "default_incomplete",
        "expand": ["latest_invoice.payment_intent"],
        "metadata": {"plan": plan},
    })
    client_secret = None
    if sub.latest_invoice and hasattr(sub.latest_invoice, "payment_intent") and sub.latest_invoice.payment_intent:
        client_secret = sub.latest_invoice.payment_intent.client_secret
    return {
        "subscription_id": sub.id,
        "status": sub.status,
        "current_period_end": sub.current_period_end,
        "trial_end": sub.trial_end,
        "client_secret": client_secret,
    }


async def cancel_subscription(subscription_id: str, at_period_end: bool = True) -> dict:
    client = get_stripe_client()
    if at_period_end:
        sub = client.subscriptions.update(subscription_id, params={"cancel_at_period_end": True})
    else:
        sub = client.subscriptions.cancel(subscription_id)
    return {"status": sub.status, "cancel_at_period_end": sub.cancel_at_period_end}


async def change_plan(subscription_id: str, new_plan: str) -> dict:
    price_id = _plan_price_ids().get(new_plan)
    if not price_id:
        raise ValueError(f"No Stripe price ID for plan {new_plan}")
    client = get_stripe_client()
    sub = client.subscriptions.retrieve(subscription_id)
    item_id = sub.items.data[0].id
    updated = client.subscriptions.update(subscription_id, params={
        "items": [{"id": item_id, "price": price_id}],
        "proration_behavior": "create_prorations",
        "metadata": {"plan": new_plan},
    })
    return {"subscription_id": updated.id, "status": updated.status, "plan": new_plan}


async def create_billing_portal_session(customer_id: str, return_url: str) -> str:
    client = get_stripe_client()
    session = client.billing_portal.sessions.create(params={
        "customer": customer_id,
        "return_url": return_url,
    })
    return session.url


def construct_webhook_event(payload: bytes, sig_header: str) -> stripe.Event:
    return stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
