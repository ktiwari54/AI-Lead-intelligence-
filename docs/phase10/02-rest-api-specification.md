# 02 — REST API Specification

**Version 4.0** | Phase 10 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication & Permissions](#2-authentication--permissions)
3. [Platform Endpoints](#3-platform-endpoints)
4. [Public Resource APIs](#4-public-resource-apis)
5. [Webhook Management](#5-webhook-management)
6. [OAuth Application Management](#6-oauth-application-management)
7. [Usage & Quotas](#7-usage--quotas)
8. [Plugin & Connector APIs](#8-plugin--connector-apis)
9. [Error Codes](#9-error-codes)
10. [OpenAPI Tags](#10-openapi-tags)

---

## 1. Overview

Phase 10 publishes stable REST contracts under `/api/v1/*` served via Kong gateway. Platform-specific endpoints live at `/api/v1/platform/*` in `backend/app/platform/router.py`.

**Base URL (gateway):** `http://localhost/api/v1`  
**Base URL (direct dev):** `http://localhost:8000/api/v1`  
**Content-Type:** `application/json`  
**Response envelope:** `APIResponse[T]` from `backend/app/common/response.py`

```json
{
  "success": true,
  "data": { },
  "message": null
}
```

Paginated lists use `PaginatedResponse[T]`:

```json
{
  "success": true,
  "data": [],
  "total": 142,
  "page": 1,
  "per_page": 25,
  "pages": 6
}
```

All v4 platform endpoints are gated by feature flag `integration_platform_v4`.

---

## 2. Authentication & Permissions

### Auth Methods

| Method | Header | Use Case |
|--------|--------|----------|
| JWT | `Authorization: Bearer {token}` | User sessions, developer portal |
| API Key | `Authorization: ApiKey ali_live_...` | Server-to-server integrations |
| OAuth 2.0 | `Authorization: Bearer {access_token}` | Third-party applications |

### Permissions

| Permission | Scope | Roles |
|------------|-------|-------|
| `platform:read` | View apps, webhooks, usage | member, developer, admin |
| `platform:write` | Create/update integrations | developer, admin |
| `platform:admin` | Quotas, marketplace moderation, OAuth admin | admin |
| `integration:read` | Read CRM/search data via API key | scoped per key |
| `integration:write` | Write CRM/search data via API key | scoped per key |
| `webhooks:manage` | CRUD webhook subscriptions | developer, admin |

API key scopes are stored in `auth.api_keys.scopes` (JSONB) and validated per endpoint.

---

## 3. Platform Endpoints

### GET /platform/health

Gateway-aware health check including integration subsystems.

```http
GET /api/v1/platform/health
```

**Response:** `APIResponse[PlatformHealth]`

```json
{
  "data": {
    "status": "healthy",
    "gateway_version": "4.0",
    "subsystems": {
      "webhooks": "healthy",
      "oauth": "healthy",
      "plugins": "healthy",
      "event_bus": "healthy"
    },
    "timestamp": "2026-06-29T12:00:00Z"
  }
}
```

### GET /platform/capabilities

Returns enabled features and API versions for the organization.

```http
GET /api/v1/platform/capabilities
Authorization: Bearer {token}
```

**Response:**

```json
{
  "data": {
    "api_version": "v1",
    "feature_flags": ["integration_platform_v4", "graphql_enabled"],
    "auth_methods": ["jwt", "api_key", "oauth2"],
    "available_scopes": ["crm:read", "crm:write", "contacts:read", "webhooks:manage"],
    "rate_limit": { "limit": 300, "window_seconds": 60 }
  }
}
```

---

## 4. Public Resource APIs

Existing domain APIs are promoted to **public integration contracts** with stable schemas. No breaking changes to v3 endpoints.

### CRM — Contacts

```http
GET /api/v1/crm/contacts?page=1&per_page=25&search=acme
Authorization: ApiKey ali_live_...
```

| Param | Type | Default | Description |
|-------|------|---------|-------------|
| `page` | int | 1 | Page number |
| `per_page` | int | 25 | Items per page (max 100) |
| `search` | string | — | Full-text search |
| `tags` | string[] | — | Filter by tag slugs |
| `min_score` | float | — | Minimum lead score |
| `updated_since` | ISO8601 | — | Delta sync filter |

**Required scope:** `contacts:read` or `crm:read`

### CRM — Companies

```http
GET /api/v1/crm/companies/{company_id}
Authorization: ApiKey ali_live_...
```

**Required scope:** `crm:read`

### Search

```http
POST /api/v1/search
Authorization: ApiKey ali_live_...
Content-Type: application/json

{
  "query": "SaaS companies in Austin",
  "filters": { "industry": "software", "employee_min": 50 },
  "limit": 50
}
```

**Required scope:** `search:write`  
**Idempotency:** `Idempotency-Key` header recommended

### Workflows — Execute

```http
POST /api/v1/workflows/{workflow_id}/execute
Authorization: ApiKey ali_live_...
Idempotency-Key: exec-019f0c1f-...

{
  "entity_type": "contact",
  "entity_id": "019f0c1f-7a3b-7890-abcd-ef1234567890",
  "async_mode": true
}
```

**Required scope:** `workflows:execute`

### Analytics — Read (Phase 9)

```http
GET /api/v1/analytics/dashboard
Authorization: ApiKey ali_live_...
```

**Required scope:** `analytics:read`

---

## 5. Webhook Management

### POST /platform/webhooks

Create a webhook subscription.

```http
POST /api/v1/platform/webhooks
Authorization: Bearer {token}
Content-Type: application/json

{
  "url": "https://partner.example.com/hooks/ali",
  "events": ["contact.created", "lead.scored", "workflow.executed"],
  "description": "CRM sync webhook",
  "secret": null
}
```

**Response:** `APIResponse[WebhookSubscription]`

```json
{
  "data": {
    "id": "019f0c1f-7a3b-7890-abcd-ef1234567890",
    "url": "https://partner.example.com/hooks/ali",
    "events": ["contact.created", "lead.scored"],
    "secret": "whsec_8f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9",
    "is_active": true,
    "created_at": "2026-06-29T12:00:00Z"
  }
}
```

> **Note:** `secret` is returned only on creation. Store it securely.

### GET /platform/webhooks

```http
GET /api/v1/platform/webhooks?page=1&per_page=25
```

### GET /platform/webhooks/{id}

### PATCH /platform/webhooks/{id}

```json
{
  "events": ["contact.created"],
  "is_active": false
}
```

### DELETE /platform/webhooks/{id}

Soft-delete; deliveries stop immediately.

### POST /platform/webhooks/{id}/test

Send a test payload to verify endpoint reachability.

```json
{
  "event_type": "contact.created"
}
```

### GET /platform/webhooks/{id}/deliveries

```http
GET /api/v1/platform/webhooks/{id}/deliveries?status=failed&page=1
```

| Param | Values |
|-------|--------|
| `status` | `pending`, `delivered`, `failed`, `retrying` |

### POST /platform/webhooks/deliveries/{delivery_id}/replay

Replay a failed delivery (admin or owner).

---

## 6. OAuth Application Management

### POST /platform/oauth/apps

```http
POST /api/v1/platform/oauth/apps
Authorization: Bearer {token}

{
  "name": "My CRM Integration",
  "redirect_uris": ["https://app.example.com/oauth/callback"],
  "scopes": ["crm:read", "contacts:read"],
  "grant_types": ["authorization_code", "refresh_token"]
}
```

**Response:**

```json
{
  "data": {
    "client_id": "ali_app_7f3a2b1c0d9e",
    "client_secret": "ali_sec_8f3a2b1c0d9e8f7a6b5c4d3e2f1a0b9",
    "name": "My CRM Integration",
    "redirect_uris": ["https://app.example.com/oauth/callback"],
    "scopes": ["crm:read", "contacts:read"]
  }
}
```

### GET /platform/oauth/apps

List OAuth applications for the organization.

### DELETE /platform/oauth/apps/{client_id}

Revoke application and all issued tokens.

See [08-oauth-platform-design.md](./08-oauth-platform-design.md) for token endpoints.

---

## 7. Usage & Quotas

### GET /platform/usage

```http
GET /api/v1/platform/usage?period=30d&group_by=endpoint
Authorization: Bearer {token}
```

**Response:**

```json
{
  "data": {
    "period": "30d",
    "total_requests": 45230,
    "by_endpoint": [
      { "endpoint": "GET /api/v1/crm/contacts", "count": 12400 },
      { "endpoint": "POST /api/v1/platform/webhooks", "count": 12 }
    ],
    "webhook_deliveries": { "success": 8900, "failed": 23 },
    "quota": { "limit": 300, "window": "minute", "tier": "pro" }
  }
}
```

### GET /platform/usage/keys/{key_id}

Per API key usage breakdown.

---

## 8. Plugin & Connector APIs

### GET /platform/plugins

List installed plugins for the organization.

### POST /platform/plugins/install

```json
{
  "plugin_id": "marketplace:salesforce-sync-v2",
  "version": "2.1.0",
  "config": { "instance_url": "https://my.salesforce.com" }
}
```

### GET /platform/connectors

List connector configurations (extends `connector` schema).

### POST /platform/connectors/{connector_type}/sync

Trigger manual connector sync.

---

## 9. Error Codes

| HTTP | Code | Description |
|------|------|-------------|
| 400 | `VALIDATION_ERROR` | Request body/param validation failed |
| 401 | `UNAUTHORIZED` | Missing or invalid credentials |
| 403 | `FORBIDDEN` | Insufficient scope or permission |
| 403 | `FEATURE_NOT_ENABLED` | `integration_platform_v4` flag disabled |
| 404 | `NOT_FOUND` | Resource not found |
| 409 | `CONFLICT` | Duplicate webhook URL or idempotency conflict |
| 422 | `SCOPE_INSUFFICIENT` | API key missing required scope |
| 429 | `RATE_LIMIT_EXCEEDED` | Gateway or org quota exceeded |
| 500 | `INTERNAL_ERROR` | Unhandled server error |
| 503 | `SERVICE_UNAVAILABLE` | Gateway or subsystem unavailable |

### Error Response Format

```json
{
  "success": false,
  "message": "Insufficient scope for this endpoint",
  "data": {
    "code": "SCOPE_INSUFFICIENT",
    "required_scopes": ["crm:read"],
    "provided_scopes": ["contacts:read"]
  }
}
```

---

## 10. OpenAPI Tags

| Tag | Router Module | Description |
|-----|---------------|-------------|
| `platform` | `platform/router.py` | Integration platform management |
| `platform-webhooks` | `platform/webhooks/router.py` | Webhook subscriptions |
| `platform-oauth` | `platform/oauth/router.py` | OAuth applications |
| `platform-usage` | `platform/usage/router.py` | API usage analytics |
| `platform-plugins` | `platform/plugins/router.py` | Plugin management |
| `crm` | `crm/router.py` | CRM public API |
| `search` | `search/router.py` | Search public API |
| `workflows` | `workflows/router.py` | Workflow execution API |
| `analytics` | `analytics/router.py` | Analytics read API |

OpenAPI spec: `GET /api/v1/openapi.json`  
ReDoc: `GET /api/v1/redoc`  
Swagger UI: `GET /api/v1/docs`

---

## Related Documents

- [03-graphql-schema-design.md](./03-graphql-schema-design.md)
- [04-webhook-platform-design.md](./04-webhook-platform-design.md)
- [16-api-governance-guide.md](./16-api-governance-guide.md)