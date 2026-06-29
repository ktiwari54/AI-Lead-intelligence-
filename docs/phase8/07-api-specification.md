# 07 — API Specification

**Version 1.0** | Phase 8 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication & Permissions](#2-authentication--permissions)
3. [Workflow CRUD](#3-workflow-crud)
4. [Definition & Versions](#4-definition--versions)
5. [Execution](#5-execution)
6. [Approvals](#6-approvals)
7. [Schedules](#7-schedules)
8. [Rule Sets](#8-rule-sets)
9. [Templates](#9-templates)
10. [Webhooks](#10-webhooks)
11. [Admin & Analytics](#11-admin--analytics)
12. [Error Codes](#12-error-codes)

**Base URL:** `/api/v1`  
**Router:** `backend/app/workflows/router.py`  
**OpenAPI Tag:** `workflows`

---

## 1. Overview

Phase 8 extends Phase 3 workflow endpoints with visual definition management, versioning, step-level execution detail, approvals, schedules, and templates.

### API Conventions

| Convention | Value |
|------------|-------|
| Content-Type | `application/json` |
| Pagination | Cursor-based (`?cursor=&limit=20`) |
| Idempotency | `Idempotency-Key` header on POST execute |
| Versioning | Workflow definitions versioned; API is `/api/v1` |

---

## 2. Authentication & Permissions

| Permission | Roles | Description |
|------------|-------|-------------|
| `workflows:read` | viewer+ (via manager) | List, view workflows and executions |
| `workflows:write` | manager+ | Create, update definitions |
| `workflows:execute` | manager+ | Manual trigger, test run |
| `workflows:delete` | manager+ | Soft delete workflows |
| `workflows:approve` | manager+ | Decide approval requests |
| `workflows:admin` | admin | Templates, replay, org quotas |

---

## 3. Workflow CRUD

### GET `/workflows`

**Permission:** `workflows:read`

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `status` | string | `draft`, `active`, `paused`, `archived` |
| `category` | string | Filter by category |
| `is_active` | boolean | Active toggle |
| `search` | string | Name/description search |
| `cursor` | string | Pagination cursor |
| `limit` | int | Max 100, default 20 |

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Auto-score new contacts",
      "description": "Scores VP+ contacts on creation",
      "status": "active",
      "is_active": true,
      "category": "lead_scoring",
      "tags": ["ai", "contacts"],
      "current_version_id": "uuid",
      "current_version_number": 3,
      "trigger_summary": "contact.created",
      "run_count": 1247,
      "last_run_at": "2026-06-29T09:00:00Z",
      "created_by": { "id": "uuid", "name": "Jane Doe" },
      "created_at": "2026-01-15T10:00:00Z",
      "updated_at": "2026-06-28T14:00:00Z"
    }
  ],
  "meta": { "next_cursor": "...", "has_more": true }
}
```

---

### POST `/workflows`

**Permission:** `workflows:write`

**Request (v2 — visual definition):**
```json
{
  "name": "Auto-score new contacts",
  "description": "Scores VP+ contacts on creation",
  "category": "lead_scoring",
  "tags": ["ai", "contacts"],
  "definition": {
    "schema_version": "2.0",
    "nodes": [...],
    "edges": [...],
    "settings": { "timeout_seconds": 300 }
  }
}
```

**Request (v1 — legacy, auto-converted):**
```json
{
  "name": "Auto-score new contacts",
  "trigger": { "event": "contact.created" },
  "conditions": [{ "field": "contact.seniority", "operator": "in", "value": ["vp", "c_level"] }],
  "actions": [
    { "type": "score_entity", "params": { "entity_type": "contact" } }
  ],
  "is_active": true
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "status": "draft",
    "current_version_id": "uuid",
    "current_version_number": 1,
    "compile_result": {
      "success": true,
      "warnings": []
    }
  }
}
```

---

### GET `/workflows/{workflow_id}`

**Permission:** `workflows:read`

Returns full workflow including current definition.

---

### PATCH `/workflows/{workflow_id}`

**Permission:** `workflows:write`

**Request (partial update):**
```json
{
  "name": "Updated name",
  "is_active": true,
  "status": "active",
  "priority": 10
}
```

**Note:** Setting `is_active: true` requires a valid compiled `current_version_id`.

---

### DELETE `/workflows/{workflow_id}`

**Permission:** `workflows:delete`

Soft delete — sets `deleted_at`, deactivates triggers.

**Response:** `204 No Content`

---

## 4. Definition & Versions

### PUT `/workflows/{workflow_id}/definition`

**Permission:** `workflows:write`

Save and compile new version.

**Request:**
```json
{
  "definition": {
    "schema_version": "2.0",
    "nodes": [...],
    "edges": [...],
    "settings": {}
  },
  "viewport": { "x": 0, "y": 0, "zoom": 1 },
  "change_summary": "Added approval gate before CRM sync"
}
```

**Response (200):**
```json
{
  "data": {
    "version_id": "uuid",
    "version_number": 4,
    "checksum": "sha256:abc...",
    "compiled_at": "2026-06-29T10:00:00Z",
    "warnings": [
      { "code": "WF010", "node_id": "node-5", "message": "Node has no outgoing edges" }
    ],
    "errors": []
  }
}
```

**Response (422):** Compile errors — definition not saved.

---

### POST `/workflows/{workflow_id}/validate`

**Permission:** `workflows:read`

Compile without persisting. Used by builder for real-time validation.

---

### GET `/workflows/{workflow_id}/versions`

**Permission:** `workflows:read`

List all versions (metadata only, no full definition).

---

### GET `/workflows/{workflow_id}/versions/{version_id}`

**Permission:** `workflows:read`

Full definition + execution plan for a specific version.

---

### POST `/workflows/{workflow_id}/versions/{version_id}/restore`

**Permission:** `workflows:write`

Create new version from historical snapshot.

---

## 5. Execution

### GET `/workflows/{workflow_id}/executions`

**Permission:** `workflows:read`

**Query:** `status`, `from`, `to`, `cursor`, `limit`

---

### GET `/workflows/executions/{execution_id}`

**Permission:** `workflows:read`

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "workflow_id": "uuid",
    "workflow_name": "Auto-score new contacts",
    "version_id": "uuid",
    "version_number": 3,
    "status": "completed",
    "trigger_type": "event",
    "trigger_data": { "event": "contact.created", "payload": {} },
    "variables": {},
    "started_at": "2026-06-29T09:00:01Z",
    "completed_at": "2026-06-29T09:00:05Z",
    "duration_ms": 4200,
    "steps": [
      {
        "node_id": "trigger-1",
        "node_type": "event_trigger",
        "status": "completed",
        "duration_ms": 0,
        "output": {}
      },
      {
        "node_id": "score-1",
        "node_type": "ai_score",
        "status": "completed",
        "duration_ms": 3800,
        "output": { "score": 85, "explanation": "..." }
      }
    ],
    "error": null
  }
}
```

---

### POST `/workflows/{workflow_id}/execute`

**Permission:** `workflows:execute`

Manual trigger.

**Headers:** `Idempotency-Key: optional-unique-key`

**Request:**
```json
{
  "entity_type": "contact",
  "entity_id": "uuid",
  "variables": { "custom_threshold": 80 },
  "version_id": null
}
```

**Response (202):**
```json
{
  "data": {
    "execution_id": "uuid",
    "status": "pending",
    "poll_url": "/api/v1/workflows/executions/uuid"
  }
}
```

---

### POST `/workflows/{workflow_id}/test-run`

**Permission:** `workflows:execute`

Dry-run with sample payload — does not trigger side effects (notifications, CRM writes).

**Request:**
```json
{
  "trigger_data": {
    "event": "contact.created",
    "payload": { "id": "uuid", "seniority": "vp", "email": "test@example.com" }
  }
}
```

---

### POST `/workflows/executions/{execution_id}/cancel`

**Permission:** `workflows:execute`

Cancel running or waiting execution.

---

### POST `/workflows/executions/{execution_id}/retry`

**Permission:** `workflows:execute`

Retry failed execution from failed step.

**Request:**
```json
{
  "step_id": "uuid",
  "reset_downstream": false
}
```

---

## 6. Approvals

### GET `/workflows/approvals`

**Permission:** `workflows:approve`

List pending approvals for current user.

**Query:** `status` (`pending`, `approved`, `rejected`), `cursor`, `limit`

---

### GET `/workflows/approvals/{approval_id}`

**Permission:** `workflows:approve`

Full approval context including workflow name, entity data, and message.

---

### POST `/workflows/approvals/{approval_id}/decide`

**Permission:** `workflows:approve`

**Request:**
```json
{
  "decision": "approved",
  "comment": "Looks good — high-value lead"
}
```

**Response (200):**
```json
{
  "data": {
    "approval_id": "uuid",
    "decision": "approved",
    "execution_status": "running",
    "message": "Workflow resumed"
  }
}
```

---

## 7. Schedules

### GET `/workflows/{workflow_id}/schedules`

**Permission:** `workflows:read`

---

### POST `/workflows/{workflow_id}/schedules`

**Permission:** `workflows:write`

**Request:**
```json
{
  "cron_expression": "0 9 * * 1-5",
  "timezone": "America/New_York",
  "holiday_calendar_id": "uuid",
  "config": {
    "skip_if_running": true,
    "variables": { "batch_mode": true }
  }
}
```

---

### PATCH `/workflows/schedules/{schedule_id}`

**Permission:** `workflows:write`

---

### DELETE `/workflows/schedules/{schedule_id}`

**Permission:** `workflows:write`

---

## 8. Rule Sets

### GET `/workflows/rule-sets`

**Permission:** `workflows:read`

---

### POST `/workflows/rule-sets`

**Permission:** `workflows:write`

**Request:**
```json
{
  "name": "High-Value Lead Criteria",
  "rules": [
    { "name": "Seniority", "expression": "{{ entity.seniority in ['vp','c_level'] }}", "priority": 10 }
  ],
  "combinator": "and"
}
```

---

### POST `/workflows/rule-sets/{rule_set_id}/evaluate`

**Permission:** `workflows:read`

Test rule set against sample entity.

---

## 9. Templates

### GET `/workflows/templates`

**Permission:** `workflows:read`

**Query:** `category`, `is_system`, `search`

---

### GET `/workflows/templates/{slug}`

**Permission:** `workflows:read`

---

### POST `/workflows/templates/{slug}/instantiate`

**Permission:** `workflows:write`

**Request:**
```json
{
  "name": "My Auto-Score Workflow",
  "parameters": {
    "score_threshold": 70,
    "notification_template": "high_value_contact"
  }
}
```

**Response (201):** New workflow in `draft` status with compiled definition.

---

## 10. Webhooks

### POST `/workflows/webhooks/{webhook_id}`

**Auth:** HMAC signature (`X-Workflow-Signature`)

Triggers `webhook_trigger` workflows. No JWT required.

**Headers:**
```
X-Workflow-Signature: sha256=abc...
X-Workflow-Timestamp: 1719669600
Content-Type: application/json
```

**Rate limit:** 100 req/min per webhook_id.

---

## 11. Admin & Analytics

### GET `/workflows/analytics/summary`

**Permission:** `workflows:read`

```json
{
  "data": {
    "total_workflows": 42,
    "active_workflows": 28,
    "executions_24h": 1523,
    "success_rate_24h": 0.974,
    "avg_duration_ms_24h": 3200,
    "pending_approvals": 5,
    "failed_executions_24h": 39
  }
}
```

---

### GET `/workflows/analytics/executions`

**Permission:** `workflows:read`

Time-series execution metrics.

**Query:** `from`, `to`, `granularity` (`hour`, `day`), `workflow_id`

---

### POST `/admin/events/replay`

**Permission:** `workflows:admin`

See [05-event-bus-architecture.md](./05-event-bus-architecture.md).

---

### GET `/admin/workflows/quotas`

**Permission:** `workflows:admin`

Org-level workflow quotas and current usage.

---

## 12. Error Codes

| HTTP | Code | Description |
|------|------|-------------|
| 400 | `INVALID_REQUEST` | Malformed request body |
| 401 | `UNAUTHORIZED` | Missing/invalid JWT |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 404 | `WORKFLOW_NOT_FOUND` | Workflow does not exist |
| 404 | `EXECUTION_NOT_FOUND` | Execution does not exist |
| 409 | `WORKFLOW_CONFLICT` | Optimistic lock conflict |
| 409 | `EXECUTION_ALREADY_RUNNING` | Duplicate execution |
| 422 | `COMPILE_ERROR` | Definition failed compilation |
| 422 | `VALIDATION_ERROR` | Pydantic validation failure |
| 429 | `RATE_LIMITED` | Org execution quota exceeded |
| 503 | `EXECUTOR_UNAVAILABLE` | Worker queue saturated |

### Error Response Format

```json
{
  "error": {
    "code": "COMPILE_ERROR",
    "message": "Workflow definition failed compilation",
    "details": [
      { "code": "WF002", "node_id": "node-3", "message": "Cycle detected" }
    ],
    "request_id": "req-abc123"
  }
}
```

---

## Related Documents

- [02-visual-workflow-builder-spec.md](./02-visual-workflow-builder-spec.md) — UI consumes these APIs
- [17-developer-sdk.md](./17-developer-sdk.md) — SDK wraps these endpoints
- [phase3/api-specification.md](../phase3/api-specification.md) — Base API conventions