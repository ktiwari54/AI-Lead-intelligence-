"""
Immutable event store for event sourcing.

The event_store table is:
- Append-only (no UPDATE or DELETE ever)
- Partitioned by month for query performance
- The permanent audit trail of everything that happened

Design principles:
1. Events are facts - they describe what happened, not what to do
2. Events are immutable - once written, never changed
3. Events are ordered by (aggregate_id, sequence_number) for replay
4. Projections (regular DB tables) are rebuilt from events

Usage:
    await publish_event(
        db=db,
        event_type=DomainEvent.DEAL_STAGE_CHANGED,
        aggregate_type="Deal",
        aggregate_id=str(deal_id),
        data={"from_stage": "Prospect", "to_stage": "Qualified", "deal_name": "Acme Corp"},
        actor_id=str(user_id),
        org_id=str(org_id),
    )
"""
from __future__ import annotations
import json
import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import text, select, func
from sqlalchemy.ext.asyncio import AsyncSession

from backend.app.common.events import DomainEvent
from backend.app.common.uuid7 import uuid7


async def publish_event(
    db: AsyncSession,
    event_type: DomainEvent | str,
    aggregate_type: str,
    aggregate_id: str,
    data: dict[str, Any],
    actor_id: str | None = None,
    org_id: str | None = None,
    correlation_id: str | None = None,
    causation_id: str | None = None,
    metadata: dict | None = None,
) -> uuid.UUID:
    """
    Append an event to the event store.

    Returns the event_id (UUID v7, time-ordered).

    The correlation_id links events from the same user action.
    The causation_id references the event that triggered this one (for event chains).
    """
    event_id = uuid7()

    # Get next sequence number for this aggregate
    seq_result = await db.execute(
        text("""
            SELECT COALESCE(MAX(sequence_number), 0) + 1
            FROM audit.event_store
            WHERE aggregate_type = :agg_type AND aggregate_id = :agg_id
        """),
        {"agg_type": aggregate_type, "agg_id": aggregate_id},
    )
    sequence_number = seq_result.scalar() or 1

    await db.execute(
        text("""
            INSERT INTO audit.event_store (
                id, event_type, aggregate_type, aggregate_id,
                sequence_number, data, actor_id, organization_id,
                correlation_id, causation_id, metadata, occurred_at
            ) VALUES (
                :id, :event_type, :aggregate_type, :aggregate_id,
                :seq, :data, :actor_id, :org_id,
                :corr_id, :caus_id, :metadata, :occurred_at
            )
        """),
        {
            "id": str(event_id),
            "event_type": str(event_type),
            "aggregate_type": aggregate_type,
            "aggregate_id": aggregate_id,
            "seq": sequence_number,
            "data": json.dumps(data),
            "actor_id": actor_id,
            "org_id": org_id,
            "corr_id": correlation_id or str(event_id),
            "caus_id": causation_id,
            "metadata": json.dumps(metadata or {}),
            "occurred_at": datetime.now(timezone.utc).isoformat(),
        },
    )

    return event_id


async def get_aggregate_events(
    db: AsyncSession,
    aggregate_type: str,
    aggregate_id: str,
    from_sequence: int = 1,
    limit: int = 1000,
) -> list[dict]:
    """
    Get all events for a specific aggregate in order.
    Use for event replay / aggregate reconstruction.
    """
    result = await db.execute(
        text("""
            SELECT id, event_type, aggregate_type, aggregate_id,
                   sequence_number, data, actor_id, organization_id,
                   correlation_id, causation_id, metadata, occurred_at
            FROM audit.event_store
            WHERE aggregate_type = :agg_type
              AND aggregate_id = :agg_id
              AND sequence_number >= :from_seq
            ORDER BY sequence_number ASC
            LIMIT :limit
        """),
        {
            "agg_type": aggregate_type,
            "agg_id": aggregate_id,
            "from_seq": from_sequence,
            "limit": limit,
        },
    )
    rows = result.mappings().all()
    return [
        {
            "id": str(row["id"]),
            "event_type": row["event_type"],
            "aggregate_type": row["aggregate_type"],
            "aggregate_id": row["aggregate_id"],
            "sequence_number": row["sequence_number"],
            "data": json.loads(row["data"]) if isinstance(row["data"], str) else row["data"],
            "actor_id": row["actor_id"],
            "organization_id": row["organization_id"],
            "correlation_id": row["correlation_id"],
            "causation_id": row["causation_id"],
            "metadata": json.loads(row["metadata"]) if isinstance(row["metadata"], str) else (row["metadata"] or {}),
            "occurred_at": row["occurred_at"].isoformat() if hasattr(row["occurred_at"], "isoformat") else row["occurred_at"],
        }
        for row in rows
    ]


async def get_org_events(
    db: AsyncSession,
    org_id: str,
    event_types: list[str] | None = None,
    aggregate_type: str | None = None,
    from_occurred_at: datetime | None = None,
    limit: int = 100,
    offset: int = 0,
) -> tuple[list[dict], int]:
    """
    Get events for an organization with optional filters.
    Used for activity feeds and compliance reporting.
    """
    filters = ["organization_id = :org_id"]
    params: dict = {"org_id": org_id, "limit": limit, "offset": offset}

    if event_types:
        filters.append("event_type = ANY(:event_types)")
        params["event_types"] = event_types

    if aggregate_type:
        filters.append("aggregate_type = :agg_type")
        params["agg_type"] = aggregate_type

    if from_occurred_at:
        filters.append("occurred_at >= :from_dt")
        params["from_dt"] = from_occurred_at.isoformat()

    where = " AND ".join(filters)

    total = await db.scalar(
        text(f"SELECT COUNT(*) FROM audit.event_store WHERE {where}"),
        params,
    ) or 0

    result = await db.execute(
        text(f"""
            SELECT id, event_type, aggregate_type, aggregate_id,
                   sequence_number, data, actor_id, occurred_at
            FROM audit.event_store
            WHERE {where}
            ORDER BY occurred_at DESC
            LIMIT :limit OFFSET :offset
        """),
        params,
    )
    rows = result.mappings().all()
    events = [
        {
            "id": str(row["id"]),
            "event_type": row["event_type"],
            "aggregate_type": row["aggregate_type"],
            "aggregate_id": row["aggregate_id"],
            "sequence_number": row["sequence_number"],
            "data": json.loads(row["data"]) if isinstance(row["data"], str) else row["data"],
            "actor_id": row["actor_id"],
            "occurred_at": row["occurred_at"].isoformat() if hasattr(row["occurred_at"], "isoformat") else row["occurred_at"],
        }
        for row in rows
    ]
    return events, total


async def get_event_timeline(
    db: AsyncSession,
    org_id: str,
    entity_type: str,
    entity_id: str,
) -> list[dict]:
    """
    Get the complete event timeline for a single entity (company or contact).
    Returns events sorted newest first for UI display.
    """
    aggregate_type = entity_type.capitalize()
    return await get_aggregate_events(db, aggregate_type, entity_id, limit=500)
