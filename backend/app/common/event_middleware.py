"""
FastAPI middleware that automatically publishes events for key operations.

Wraps service calls to emit domain events without polluting business logic.
Also provides a router for the event store API.
"""
from __future__ import annotations
import uuid
from datetime import datetime, timezone
from typing import Any

from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.deps import get_current_user, get_db
from backend.app.common.event_store import get_org_events, get_aggregate_events, get_event_timeline
from backend.app.common.events import DomainEvent
from backend.app.common.response import APIResponse, PaginatedResponse
from backend.app.users.models import User

# ─── Event Store API router ─────────────────────────────────────────────────

router = APIRouter(prefix="/events", tags=["Event Store"])


@router.get("/")
async def list_events(
    event_type: list[str] | None = Query(None),
    aggregate_type: str | None = Query(None),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """List events for the current organization."""
    events, total = await get_org_events(
        db,
        org_id=str(current_user.organization_id),
        event_types=event_type,
        aggregate_type=aggregate_type,
        limit=page_size,
        offset=(page - 1) * page_size,
    )
    return PaginatedResponse.create(items=events, total=total, page=page, page_size=page_size)


@router.get("/timeline/{entity_type}/{entity_id}")
async def entity_timeline(
    entity_type: str,
    entity_id: uuid.UUID,
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get the complete event timeline for a company or contact."""
    events = await get_event_timeline(
        db,
        org_id=str(current_user.organization_id),
        entity_type=entity_type,
        entity_id=str(entity_id),
    )
    return APIResponse(data={"events": events, "total": len(events)})


@router.get("/aggregate/{aggregate_type}/{aggregate_id}")
async def aggregate_events(
    aggregate_type: str,
    aggregate_id: str,
    from_sequence: int = Query(1, ge=1),
    limit: int = Query(100, ge=1, le=1000),
    current_user: User = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
):
    """Get events for a specific aggregate in sequence order (for replay)."""
    events = await get_aggregate_events(
        db,
        aggregate_type=aggregate_type,
        aggregate_id=aggregate_id,
        from_sequence=from_sequence,
        limit=limit,
    )
    return APIResponse(data={"events": events, "total": len(events), "from_sequence": from_sequence})


@router.get("/types")
async def list_event_types(current_user: User = Depends(get_current_user)):
    """List all registered event types."""
    return APIResponse(data={"event_types": [e.value for e in DomainEvent]})


# ─── Event publishing helpers ─────────────────────────────────────────────────

async def emit_company_created(db: AsyncSession, company: Any, actor_id: str, org_id: str) -> None:
    from backend.app.common.event_store import publish_event
    await publish_event(
        db=db,
        event_type=DomainEvent.COMPANY_CREATED,
        aggregate_type="Company",
        aggregate_id=str(company.id),
        data={"name": company.name, "domain": getattr(company, "domain", None), "industry": getattr(company, "industry", None)},
        actor_id=actor_id,
        org_id=org_id,
    )


async def emit_contact_created(db: AsyncSession, contact: Any, actor_id: str, org_id: str) -> None:
    from backend.app.common.event_store import publish_event
    await publish_event(
        db=db,
        event_type=DomainEvent.CONTACT_CREATED,
        aggregate_type="Contact",
        aggregate_id=str(contact.id),
        data={"first_name": contact.first_name, "last_name": contact.last_name, "email": contact.email, "designation": getattr(contact, "designation", None)},
        actor_id=actor_id,
        org_id=org_id,
    )


async def emit_deal_stage_changed(db: AsyncSession, deal: Any, from_stage: str, to_stage: str, actor_id: str, org_id: str) -> None:
    from backend.app.common.event_store import publish_event
    await publish_event(
        db=db,
        event_type=DomainEvent.DEAL_STAGE_CHANGED,
        aggregate_type="Deal",
        aggregate_id=str(deal.id),
        data={"deal_name": deal.name, "from_stage": from_stage, "to_stage": to_stage, "value": float(deal.value or 0)},
        actor_id=actor_id,
        org_id=org_id,
    )


async def emit_lead_scored(db: AsyncSession, score: Any, entity_type: str, entity_id: str, org_id: str) -> None:
    from backend.app.common.event_store import publish_event
    await publish_event(
        db=db,
        event_type=DomainEvent.LEAD_SCORED,
        aggregate_type=entity_type.capitalize(),
        aggregate_id=entity_id,
        data={"overall_score": score.overall_score, "model_used": score.model_used, "recommendation": score.score_breakdown.get("recommendation") if isinstance(score.score_breakdown, dict) else None},
        org_id=org_id,
    )


async def emit_credits_deducted(db: AsyncSession, tx: Any, org_id: str, actor_id: str) -> None:
    from backend.app.common.event_store import publish_event
    await publish_event(
        db=db,
        event_type=DomainEvent.CREDITS_DEDUCTED,
        aggregate_type="Subscription",
        aggregate_id=org_id,
        data={"amount": abs(tx.amount), "balance_after": tx.balance_after, "description": tx.description},
        actor_id=actor_id,
        org_id=org_id,
    )
