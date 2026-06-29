# 05 — Event Bus Architecture

**Version 1.0** | Phase 8 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [Architecture](#2-architecture)
3. [Publish Flow](#3-publish-flow)
4. [Subscribe Flow](#4-subscribe-flow)
5. [Workflow Event Matching](#5-workflow-event-matching)
6. [Dead Letter Queue](#6-dead-letter-queue)
7. [Event Replay](#7-event-replay)
8. [RabbitMQ Topology](#8-rabbitmq-topology)
9. [Migration from Redis](#9-migration-from-redis)
10. [Monitoring](#10-monitoring)

---

## 1. Overview

Phase 8 upgrades the event bus from Redis-only Celery dispatch to **RabbitMQ-backed pub/sub** while preserving the transactional outbox pattern in `backend/infrastructure/messaging/event_bus.py`.

The workflow platform is the **largest consumer** of domain events — every `contact.created`, `lead.scored`, etc. may trigger one or more workflow executions.

### Design Goals

| Goal | Implementation |
|------|----------------|
| At-least-once delivery | Outbox + RabbitMQ acks |
| Ordering per aggregate | Partition key = `aggregate_id` |
| Tenant isolation | `organization_id` in envelope + consumer filter |
| Recoverability | DLQ + replay API |
| Backpressure | Queue depth monitoring + HPA |

---

## 2. Architecture

```mermaid
flowchart TB
    subgraph Producers
        CS[Company Service]
        CTS[Contact Service]
        AI[AI Scoring]
        CRM[CRM Service]
        WF[Workflow Executor]
    end

    subgraph Event Bus Core
        EB[EventBus<br/>event_bus.py]
        OUTBOX[(event_store<br/>PostgreSQL)]
    end

    subgraph RabbitMQ
        EX[domain.events<br/>Topic Exchange]
        Q_WF[workflows.events]
        Q_AI[ai.events]
        Q_CRM[crm.events]
        DLQ[workflows.dlq]
    end

    subgraph Consumers
        W1[workflows.process_event]
        W2[ai.subscriber]
        W3[crm.subscriber]
        DLQW[workflows.dlq_processor]
    end

    CS --> EB
    CTS --> EB
    AI --> EB
    CRM --> EB
    WF --> EB
    EB --> OUTBOX
    EB --> EX
    EX --> Q_WF --> W1
    EX --> Q_AI --> W2
    EX --> Q_CRM --> W3
    Q_WF -.->|nack/reject| DLQ --> DLQW
```

---

## 3. Publish Flow

### Event Envelope (Unchanged from Phase 3)

```python
@dataclass
class EventEnvelope:
    event_id: UUID
    event_type: DomainEvent
    aggregate_type: str
    aggregate_id: UUID
    organization_id: UUID
    actor_id: UUID | None
    payload: dict[str, Any]
    metadata: dict[str, Any]
    version: int = 1
    timestamp: datetime
```

### Phase 8 Extended Events

```python
class DomainEvent(str, Enum):
    # ... existing events ...
    WORKFLOW_STARTED = "workflow.started"
    WORKFLOW_EXECUTED = "workflow.executed"
    WORKFLOW_FAILED = "workflow.failed"
    WORKFLOW_APPROVAL_REQUESTED = "workflow.approval_requested"
    WORKFLOW_APPROVAL_DECIDED = "workflow.approval_decided"
    WORKFLOW_STEP_COMPLETED = "workflow.step_completed"
```

### Publish Sequence

```mermaid
sequenceDiagram
    participant S as Service
    participant EB as EventBus
    participant DB as PostgreSQL
    participant RMQ as RabbitMQ

    S->>EB: publish(envelope)
    EB->>DB: BEGIN
    EB->>DB: INSERT event_store
    EB->>DB: business writes (same TX)
    EB->>DB: COMMIT
    EB->>RMQ: basic.publish(exchange, routing_key, body)
    Note over RMQ: routing_key = event_type e.g. contact.created
```

### Outbox Poller (Fallback)

If direct RabbitMQ publish fails post-commit:

```python
@celery_app.task(name="messaging.outbox_poll", queue="system")
def outbox_poll():
    """Poll unpublished events every 5s; publish to RabbitMQ."""
```

Ensures **zero event loss** even during broker outages.

---

## 4. Subscribe Flow

### Subscription Registry

```python
# backend/infrastructure/messaging/subscriptions.py
SUBSCRIPTIONS: dict[str, list[SubscriberConfig]] = {
    "contact.created": [
        SubscriberConfig(queue="workflows.events", task="workflows.process_event"),
        SubscriberConfig(queue="ai.events", task="ai.on_contact_created"),
    ],
    "lead.scored": [
        SubscriberConfig(queue="workflows.events", task="workflows.process_event"),
        SubscriberConfig(queue="crm.events", task="crm.on_lead_scored"),
    ],
}
```

### Consumer Task

```python
@celery_app.task(
    name="workflows.process_event",
    queue="workflows",
    bind=True,
    acks_late=True,
    max_retries=3,
)
def process_event(self, event_type: str, event_id: str) -> None:
    envelope = load_event(event_id)
    matching = find_matching_workflows(
        org_id=envelope.organization_id,
        event_type=event_type,
        payload=envelope.payload,
    )
    for workflow in matching:
        start_execution.delay(workflow.id, envelope.to_trigger_data())
```

### Idempotent Consumption

```python
def consume_once(event_id: UUID, consumer: str) -> bool:
    """INSERT INTO event_consumption_log; return False if duplicate."""
```

---

## 5. Workflow Event Matching

### Matching Algorithm

```python
async def find_matching_workflows(
    org_id: UUID,
    event_type: str,
    payload: dict,
) -> list[Workflow]:
    """
    1. SELECT active workflows WHERE organization_id = org_id
    2. Filter: trigger.event == event_type
    3. Filter: evaluate trigger.filter expression (if present)
    4. Sort by priority (desc), created_at (asc)
    """
```

### Trigger Index

Materialized in Redis for hot path:

```
wf:triggers:{org_id}:{event_type} → Set[workflow_id]
```

Rebuilt on workflow activate/deactivate via `workflows.rebuild_trigger_index` task.

### Fan-Out Limits

| Limit | Default |
|-------|---------|
| Max workflows per event per org | 50 |
| Max executions spawned per event | 20 |
| Excess | Log warning, skip lowest priority |

---

## 6. Dead Letter Queue

### DLQ Triggers

| Condition | Action |
|-----------|--------|
| Max retries exceeded (3) | Route to `workflows.dlq` |
| Deserialization error | Route to `workflows.dlq` |
| Unknown event type | Log + ack (no DLQ) |
| Sandbox violation in trigger filter | Route to `workflows.dlq` |

### DLQ Message Schema

```json
{
  "original_event_id": "uuid",
  "original_queue": "workflows.events",
  "failure_reason": "MaxRetriesExceeded",
  "failure_count": 3,
  "last_error": "ConnectionError: RabbitMQ timeout",
  "failed_at": "2026-06-29T10:00:00Z",
  "payload": { "...": "original envelope" }
}
```

### DLQ Processing

```python
@celery_app.task(name="workflows.dlq_processor", queue="workflows.dlq")
def dlq_processor(message: dict) -> None:
    """
    1. Classify: transient vs permanent
    2. Transient → requeue to workflows.events (with delay)
    3. Permanent → store in audit.event_dlq, alert ops
    4. Notify org admin if tenant-specific
    """
```

### DLQ Retention

| Storage | Retention |
|---------|-----------|
| RabbitMQ DLQ queue | 7 days (TTL) |
| `audit.event_dlq` table | 90 days |
| S3 archive | 1 year |

---

## 7. Event Replay

### Replay Use Cases

| Scenario | Replay Scope |
|----------|--------------|
| Bug fix in workflow logic | Re-execute workflows for event range |
| DLQ recovery | Replay DLQ messages |
| Disaster recovery | Replay from `event_store` |
| Testing | Replay to staging environment |

### Replay API

```
POST /api/v1/admin/events/replay
```

**Permission:** `admin:events:replay`

```json
{
  "event_types": ["contact.created"],
  "organization_id": "uuid",
  "from": "2026-06-01T00:00:00Z",
  "to": "2026-06-29T00:00:00Z",
  "target": "workflows",
  "dry_run": true,
  "rate_limit_per_second": 10
}
```

### Replay Safeguards

1. **Dry run** mode counts affected events without dispatching
2. **Idempotency** — replays tagged with `metadata.replay_id`; consumers deduplicate
3. **Rate limiting** — default 10 events/sec, max 100
4. **Audit** — all replays logged to `audit.event_replay_jobs`

### Replay Job States

```mermaid
stateDiagram-v2
    [*] --> queued
    queued --> running
    running --> completed
    running --> failed
    running --> cancelled
    completed --> [*]
    failed --> [*]
    cancelled --> [*]
```

---

## 8. RabbitMQ Topology

### Exchanges

| Exchange | Type | Durable |
|----------|------|---------|
| `domain.events` | topic | yes |
| `domain.events.dlx` | fanout | yes |
| `workflows.internal` | direct | yes |

### Queues

| Queue | Binding | Consumers | Prefetch |
|-------|---------|-----------|----------|
| `workflows.events` | `domain.events` / `#` | `worker-workflows` | 10 |
| `workflows.priority` | `workflows.internal` / `priority` | `worker-workflows-priority` | 5 |
| `workflows.dlq` | `domain.events.dlx` / — | `worker-dlq` | 1 |
| `workflows.schedule` | `workflows.internal` / `schedule` | `worker-workflows` | 5 |

### Routing Keys

```
contact.created
contact.updated
company.created
lead.scored
deal.stage_changed
workflow.executed
workflow.failed
```

### Message Properties

```python
properties = {
    "delivery_mode": 2,  # persistent
    "content_type": "application/json",
    "headers": {
        "x-organization-id": str(org_id),
        "x-correlation-id": correlation_id,
        "x-event-version": 1,
    },
}
```

### Celery Broker Configuration

```python
# backend/infrastructure/workers/celery_app.py
broker_url = "amqp://guest:guest@rabbitmq:5672//"
broker_transport_options = {
    "queue_order_strategy": "priority",
    "priority_steps": list(range(10)),
}
task_routes = {
    "workflows.*": {"queue": "workflows"},
    "workflows.resume": {"queue": "workflows.priority"},
}
```

---

## 9. Migration from Redis

Phase 3 used Redis as Celery broker. Phase 8 migration path:

| Phase | Broker | Notes |
|-------|--------|-------|
| 8.0 | Redis (dev) | Default in `docker-compose.yml` |
| 8.1 | Dual-write | Events to both Redis + RabbitMQ |
| 8.2 | RabbitMQ primary | Redis as Celery result backend only |
| 8.3 | RabbitMQ only | Remove Redis broker config |

### Feature Flag

`event_bus_rabbitmq_enabled` — per-environment toggle.

### Rollback

If RabbitMQ fails health check, auto-fallback to Redis publish (logged as `WARN`).

---

## 10. Monitoring

### Key Metrics

| Metric | Type | Alert Threshold |
|--------|------|-----------------|
| `event_bus_publish_total` | Counter | — |
| `event_bus_publish_errors_total` | Counter | > 5/min |
| `rabbitmq_queue_depth{queue="workflows.events"}` | Gauge | > 10,000 |
| `rabbitmq_consumer_lag_seconds` | Gauge | > 60s |
| `workflow_event_match_duration_seconds` | Histogram | p95 > 500ms |
| `event_dlq_depth` | Gauge | > 100 |
| `outbox_unpublished_count` | Gauge | > 50 for 5min |

### Health Checks

```python
# GET /health/rabbitmq
{
  "status": "healthy",
  "connections": 12,
  "queues": {
    "workflows.events": { "depth": 42, "consumers": 4 }
  }
}
```

### Grafana Dashboard

See [12-analytics-dashboard.md](./12-analytics-dashboard.md) and `infra/monitoring/grafana/dashboards/workflows.json`.

---

## Related Documents

- [01-workflow-platform-architecture.md](./01-workflow-platform-architecture.md) — System context
- [03-workflow-engine-design.md](./03-workflow-engine-design.md) — Execution triggered by events
- [19-operational-runbook.md](./19-operational-runbook.md) — DLQ recovery procedures