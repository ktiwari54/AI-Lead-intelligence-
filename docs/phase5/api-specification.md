# API Specifications — Discovery Platform

**Version 2.0** | AI Lead Intelligence Platform — Phase 5

**Base URL:** `/api/v1/discovery`

All endpoints require `Authorization: Bearer <jwt>` and enforce tenant isolation via `organization_id` from token.

---

## Table of Contents

1. [Discovery Execution](#1-discovery-execution)
2. [Discovery Jobs](#2-discovery-jobs)
3. [Discovery Results](#3-discovery-results)
4. [Connector Management](#4-connector-management)
5. [Connector Health](#5-connector-health)
6. [Provider Configuration](#6-provider-configuration)
7. [Search Preview](#7-search-preview)
8. [Connector Metrics & Logs](#8-connector-metrics--logs)
9. [Retry Jobs](#9-retry-jobs)
10. [Error Responses](#10-error-responses)
11. [Webhooks](#11-webhooks)

---

## 1. Discovery Execution

### POST `/execute`

Execute a discovery search synchronously (small result sets) or enqueue async job (large/complex).

**Request:**

```json
{
  "query": "SaaS companies in Austin with 50-200 employees using React",
  "entity_type": "company",
  "filters": {
    "industry": "software",
    "employee_min": 50,
    "employee_max": 200,
    "technologies": ["react"],
    "location": {"city": "Austin", "state": "TX", "country": "US"}
  },
  "connectors": ["apollo", "clearbit"],
  "enrich": true,
  "verify_contacts": false,
  "async": true
}
```

**Response (async):**

```json
{
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "pending",
    "poll_url": "/api/v1/discovery/jobs/550e8400-e29b-41d4-a716-446655440000"
  },
  "message": "Discovery job queued"
}
```

**Response (sync, `async: false`, max 25 results):**

```json
{
  "data": {
    "job_id": "550e8400-e29b-41d4-a716-446655440000",
    "total": 12,
    "hits": [/* DiscoveryResultHit[] */],
    "took_ms": 2340,
    "connectors": [
      {"name": "apollo", "success": true, "latency_ms": 1200},
      {"name": "clearbit", "success": true, "latency_ms": 890}
    ]
  }
}
```

| Field | Type | Required | Description |
|-------|------|----------|-------------|
| `query` | string | No* | Natural language or keyword query |
| `entity_type` | enum | Yes | `company`, `contact`, `both` |
| `filters` | object | No | Structured filters (see Query Engine doc) |
| `connectors` | string[] | No | Override auto-selection |
| `enrich` | boolean | No | Default `true` |
| `verify_contacts` | boolean | No | Default `false` |
| `async` | boolean | No | Default `true` |

*Either `query` or non-empty `filters` required.

---

## 2. Discovery Jobs

### GET `/jobs`

List discovery jobs for the organization.

**Query params:** `page`, `page_size`, `status`, `from`, `to`

**Response:**

```json
{
  "data": [
    {
      "id": "550e8400-e29b-41d4-a716-446655440000",
      "status": "completed",
      "query": "SaaS companies in Austin",
      "entity_type": "company",
      "connectors_used": ["apollo", "clearbit"],
      "result_count": 47,
      "credits_used": 12,
      "started_at": "2026-06-28T10:00:00Z",
      "completed_at": "2026-06-28T10:00:05Z"
    }
  ],
  "total": 156,
  "page": 1,
  "per_page": 25
}
```

### GET `/jobs/{job_id}`

Get job status and stage progress.

```json
{
  "data": {
    "id": "550e8400-e29b-41d4-a716-446655440000",
    "status": "running",
    "stages": {
      "connector_execution": "completed",
      "normalization": "completed",
      "entity_resolution": "in_progress",
      "enrichment": "pending"
    },
    "progress_pct": 55
  }
}
```

### POST `/jobs/{job_id}/cancel`

Cancel a pending or running job.

### DELETE `/jobs/{job_id}`

Soft-delete job record (admin only).

---

## 3. Discovery Results

### GET `/jobs/{job_id}/results`

Paginated discovery results.

**Query params:** `page`, `page_size`, `min_confidence`, `entity_type`, `sort` (`confidence`, `recency`)

```json
{
  "data": {
    "hits": [
      {
        "id": "hit-uuid",
        "entity_type": "company",
        "confidence": 0.87,
        "source_trust": 0.85,
        "field_completeness": 0.78,
        "verification_status": null,
        "data": {
          "name": "Acme SaaS Inc",
          "domain": "acmesaas.com",
          "industry": "Computer Software",
          "employee_count": 120
        },
        "provenance": [
          {"field": "domain", "source": "clearbit", "retrieved_at": "2026-06-28T10:00:02Z"}
        ],
        "explanation": {
          "overall": 0.87,
          "factors": [{"field": "domain", "score": 1.0, "reason": "Exact match across 2 sources"}]
        }
      }
    ],
    "total": 47,
    "took_ms": 45
  }
}
```

### POST `/jobs/{job_id}/results/import`

Import selected hits into tenant companies/contacts tables.

```json
{
  "hit_ids": ["hit-uuid-1", "hit-uuid-2"],
  "target": "companies",
  "dedupe": true
}
```

---

## 4. Connector Management

### GET `/connectors`

List registered connectors and capabilities.

```json
{
  "data": [
    {
      "name": "apollo",
      "display_name": "Apollo.io",
      "version": "2.0",
      "category": "enrichment",
      "source_type": "licensed_provider",
      "capabilities": ["search", "lookup", "enrich"],
      "configured": true,
      "healthy": true
    }
  ]
}
```

### GET `/connectors/{name}`

Connector detail including rate limits and config schema.

### POST `/connectors/{name}/test`

Test connector authentication with stored or provided credentials.

```json
{
  "credentials": {"api_key": "test-key"}
}
```

---

## 5. Connector Health

### GET `/connectors/health`

Aggregate health for all configured connectors.

```json
{
  "data": {
    "overall": "healthy",
    "connectors": [
      {
        "name": "apollo",
        "healthy": true,
        "latency_ms": 145,
        "circuit_state": "closed",
        "last_check": "2026-06-28T09:55:00Z"
      }
    ]
  }
}
```

### GET `/connectors/{name}/health`

Single connector health with credit/quota info.

### POST `/connectors/health/check`

Trigger immediate health check for all connectors (admin).

---

## 6. Provider Configuration

Provider configs are stored encrypted per tenant. See also `/api/v1/integrations/configs`.

### GET `/providers`

List available providers with onboarding status.

### PUT `/providers/{name}/config`

Update provider credentials and settings.

```json
{
  "enabled": true,
  "credentials": {
    "api_key": "encrypted-at-rest"
  },
  "settings": {
    "default_page_size": 25,
    "priority": 1
  }
}
```

### GET `/providers/{name}/config`

Return config metadata (credentials masked).

---

## 7. Search Preview

### POST `/preview`

Parse query and return structured intent without executing connectors.

```json
{
  "query": "CTOs at fintech startups in London"
}
```

**Response:**

```json
{
  "data": {
    "intent": {
      "entity_type": "contact",
      "filters": {
        "title": "CTO",
        "industry": "fintech",
        "location": {"city": "London", "country": "GB"}
      },
      "suggested_connectors": ["apollo", "clearbit"],
      "estimated_credits": 5
    }
  }
}
```

### GET `/suggestions`

Autocomplete suggestions.

**Query params:** `q`, `type` (`company`, `contact`, `industry`, `technology`)

### GET `/saved`

List saved searches with schedule info.

### POST `/saved`

Create saved search with optional cron schedule.

---

## 8. Connector Metrics & Logs

### GET `/metrics`

Prometheus-compatible metrics endpoint (internal/service token).

### GET `/connectors/{name}/metrics`

Per-connector metrics for dashboard.

```json
{
  "data": {
    "requests_total": 15420,
    "success_rate": 0.97,
    "avg_latency_ms": 890,
    "p95_latency_ms": 2100,
    "rate_limit_denied": 12,
    "credits_used_24h": 340
  }
}
```

### GET `/connectors/{name}/logs`

Structured connector execution logs.

**Query params:** `page`, `level`, `from`, `to`, `job_id`

---

## 9. Retry Jobs

### POST `/jobs/{job_id}/retry`

Retry failed connectors for a partial/failed job.

```json
{
  "connectors": ["clearbit"],
  "retry_stage": "connector_execution"
}
```

### GET `/retry-queue`

List items in retry queue (admin).

### POST `/dlq/{entry_id}/replay`

Replay a dead-letter entry.

---

## 10. Error Responses

Standard error envelope:

```json
{
  "error": {
    "code": "RATE_LIMIT_EXCEEDED",
    "message": "Tenant daily discovery quota exceeded",
    "details": {"limit": 1000, "used": 1000, "resets_at": "2026-06-29T00:00:00Z"},
    "request_id": "req-uuid"
  }
}
```

| HTTP | Code | Description |
|------|------|-------------|
| 400 | `INVALID_QUERY` | Missing query/filters |
| 401 | `UNAUTHORIZED` | Invalid/expired token |
| 403 | `FORBIDDEN` | Insufficient permissions |
| 402 | `CREDITS_EXHAUSTED` | Tenant credits depleted |
| 429 | `RATE_LIMIT_EXCEEDED` | Tenant or provider limit |
| 404 | `JOB_NOT_FOUND` | Invalid job_id |
| 422 | `VALIDATION_ERROR` | Pydantic validation failure |
| 503 | `CONNECTOR_UNAVAILABLE` | All connectors circuit-open |

---

## 11. Webhooks

Tenants may register webhooks for discovery events.

### POST `/webhooks`

```json
{
  "url": "https://customer.app/hooks/discovery",
  "events": ["DiscoveryCompleted", "DiscoveryFailed"],
  "secret": "whsec_..."
}
```

Payload signed with `X-Signature: sha256=...` (HMAC-SHA256).