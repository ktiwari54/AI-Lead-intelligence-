# Phase 3 — API Specification

**Version 3.0** | Base URL: `https://api.example.com/api/v1`

All endpoints return the standard envelope unless noted. Auth: `Authorization: Bearer <access_token>` or `X-API-Key: ali_...`.

---

## Table of Contents

1. [Conventions](#1-conventions)
2. [Authentication](#2-authentication)
3. [Users & Permissions](#3-users--permissions)
4. [Organizations](#4-organizations)
5. [Companies](#5-companies)
6. [Contacts](#6-contacts)
7. [Search](#7-search)
8. [AI Search & Scoring](#8-ai-search--scoring)
9. [Enrichment](#9-enrichment)
10. [Connectors](#10-connectors)
11. [CRM](#11-crm)
12. [Workflows](#12-workflows)
13. [Exports & Imports](#13-exports--imports)
14. [Analytics](#14-analytics)
15. [Notifications](#15-notifications)
16. [Billing](#16-billing)
17. [Admin](#17-admin)
18. [Developer API](#18-developer-api)
19. [Files](#19-files)
20. [Health & Observability](#20-health--observability)

---

## 1. Conventions

### Headers

| Header | Required | Description |
|--------|----------|-------------|
| `Authorization` | Yes* | Bearer JWT (*except public auth routes) |
| `X-API-Key` | Alt | Developer API key |
| `X-Request-ID` | No | Client-generated; echoed in response |
| `X-Correlation-ID` | No | Trace across services |
| `Idempotency-Key` | POST/PUT | Prevents duplicate mutations |

### Pagination Response

```json
{
  "pagination": {
    "page": 1,
    "page_size": 25,
    "total": 142,
    "total_pages": 6,
    "has_next": true,
    "has_prev": false
  }
}
```

### Common Error Responses

| Status | Code | Example |
|--------|------|---------|
| 401 | `UNAUTHORIZED` | Invalid or missing token |
| 403 | `FORBIDDEN` | Missing `companies:write` |
| 404 | `NOT_FOUND` | Resource not in tenant |
| 409 | `CONFLICT` | Duplicate domain |
| 402 | `INSUFFICIENT_CREDITS` | Need 5, have 2 |
| 429 | `RATE_LIMITED` | Retry after 60s |

---

## 2. Authentication

### POST `/auth/register`

Create account and organization.

| | |
|---|---|
| **Permission** | Public |
| **Idempotent** | No |

**Request:**
```json
{
  "email": "user@acme.com",
  "password": "SecureP@ss1",
  "full_name": "Jane Doe",
  "organization_name": "Acme Corp"
}
```

**Validation:**
- `email`: valid, unique
- `password`: min 8 chars, 1 upper, 1 lower, 1 digit
- `organization_name`: 2–100 chars

**Response (201):**
```json
{
  "success": true,
  "data": {
    "access_token": "eyJ...",
    "refresh_token": "rt_...",
    "token_type": "bearer",
    "expires_in": 3600
  }
}
```

**Errors:** `409 CONFLICT` (email exists), `422 VALIDATION_ERROR`

---

### POST `/auth/login`

| | |
|---|---|
| **Permission** | Public |
| **Content-Type** | `application/x-www-form-urlencoded` (OAuth2) or JSON |

**Request (JSON):**
```json
{ "email": "user@acme.com", "password": "SecureP@ss1" }
```

**Response (200):** Same as register token response.

**Errors:** `401 UNAUTHORIZED`, `429 RATE_LIMITED` (lockout)

---

### POST `/auth/refresh`

| | |
|---|---|
| **Permission** | Public (requires valid refresh token) |

**Request:**
```json
{ "refresh_token": "rt_..." }
```

**Response (200):** New access + refresh tokens (rotation).

**Errors:** `401 TOKEN_EXPIRED`, `401 UNAUTHORIZED` (revoked)

---

### POST `/auth/logout`

| | |
|---|---|
| **Permission** | Authenticated |

**Request:** `{ "refresh_token": "rt_..." }`

**Response (200):** `{ "success": true, "message": "Logged out" }`

---

### GET `/auth/oauth/google`

Redirect to Google OAuth consent screen.

**Query:** `redirect_uri` (optional, must be whitelisted)

---

### POST `/auth/oauth/google/callback`

**Request:**
```json
{ "code": "4/0A...", "redirect_uri": "https://app.example.com/callback" }
```

**Response (200):** Token response.

---

### GET `/auth/oauth/microsoft`

Redirect to Microsoft OAuth consent screen.

---

### POST `/auth/oauth/microsoft/callback`

Same structure as Google callback.

---

### POST `/auth/magic-link`

**Request:** `{ "email": "user@acme.com" }`

**Response (200):** `{ "success": true, "message": "Magic link sent" }`

---

### POST `/auth/magic-link/verify`

**Request:** `{ "token": "ml_..." }`

**Response (200):** Token response.

---

### POST `/auth/2fa/setup`

| | |
|---|---|
| **Permission** | Authenticated |

**Response (200):**
```json
{
  "data": {
    "secret": "BASE32SECRET",
    "qr_uri": "otpauth://totp/...",
    "backup_codes": ["12345678", "..."]
  }
}
```

---

### POST `/auth/2fa/verify`

**Request:** `{ "code": "123456" }`

**Response (200):** `{ "success": true, "message": "2FA enabled" }`

---

### POST `/auth/password/forgot`

**Request:** `{ "email": "user@acme.com" }`

**Response (200):** Always success (no email enumeration).

---

### POST `/auth/password/reset`

**Request:**
```json
{
  "token": "reset_...",
  "new_password": "NewSecureP@ss1"
}
```

---

### GET `/auth/sessions`

List active sessions for current user.

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "device": "Chrome on Windows",
      "ip_address": "203.0.113.1",
      "last_active_at": "2026-06-28T10:00:00Z",
      "is_current": true
    }
  ]
}
```

---

### DELETE `/auth/sessions/{session_id}`

Revoke a specific session. **Permission:** Authenticated (own sessions).

---

### DELETE `/auth/sessions`

Revoke all sessions except current.

---

## 3. Users & Permissions

### GET `/users/me`

**Permission:** Authenticated

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "email": "user@acme.com",
    "full_name": "Jane Doe",
    "role": "admin",
    "organization_id": "uuid",
    "is_verified": true,
    "created_at": "2026-01-01T00:00:00Z"
  }
}
```

---

### PATCH `/users/me`

**Request:**
```json
{ "full_name": "Jane Smith", "avatar_url": "https://..." }
```

---

### GET `/users`

**Permission:** `users:read`

**Query:** `page`, `page_size`, `role`, `q` (search name/email), `sort`

---

### POST `/users`

**Permission:** `users:write`

**Request:**
```json
{
  "email": "new@acme.com",
  "full_name": "Bob Lee",
  "role": "member",
  "password": "TempP@ss1"
}
```

---

### GET `/users/{user_id}`

**Permission:** `users:read`

---

### PATCH `/users/{user_id}`

**Permission:** `users:write`

**Request:** `{ "full_name": "...", "role": "manager", "is_active": true }`

---

### DELETE `/users/{user_id}`

**Permission:** `users:delete` — soft delete.

---

### GET `/users/roles`

**Permission:** `users:read`

**Response:** List of roles with permissions.

---

### POST `/users/roles`

**Permission:** `users:admin`

**Request:**
```json
{
  "name": "sales_rep",
  "display_name": "Sales Representative",
  "permissions": ["companies:read", "contacts:read", "contacts:write", "search:execute"]
}
```

---

### GET `/users/api-keys`

**Permission:** `api_keys:read`

---

### POST `/users/api-keys`

**Permission:** `api_keys:write`

**Request:**
```json
{
  "name": "Production Integration",
  "scopes": ["companies:read", "contacts:read", "search:execute"],
  "expires_at": "2027-01-01T00:00:00Z"
}
```

**Response (201):**
```json
{
  "data": {
    "id": "uuid",
    "name": "Production Integration",
    "key": "ali_live_abc123...",
    "key_prefix": "ali_live_abc",
    "scopes": ["companies:read"],
    "created_at": "2026-06-28T00:00:00Z"
  },
  "message": "Store this key securely. It will not be shown again."
}
```

---

### DELETE `/users/api-keys/{key_id}`

**Permission:** `api_keys:write` — revoke key.

---

## 4. Organizations

### GET `/organizations/current`

**Permission:** Authenticated

**Response (200):**
```json
{
  "data": {
    "id": "uuid",
    "name": "Acme Corp",
    "slug": "acme-corp",
    "plan": "pro",
    "monthly_credits": 5000,
    "credits_used": 1234,
    "credits_remaining": 3766,
    "settings": { "icp_industries": ["saas", "fintech"] }
  }
}
```

---

### PATCH `/organizations/current`

**Permission:** `organization:write`

**Request:**
```json
{
  "name": "Acme Corporation",
  "settings": { "icp_industries": ["saas"], "default_country": "US" }
}
```

---

### GET `/organizations/usage`

**Permission:** `organization:read`

**Response:** Credit usage breakdown by operation type.

---

## 5. Companies

### GET `/companies`

**Permission:** `companies:read`

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `page` | int | Page number (default 1) |
| `page_size` | int | 1–100 (default 25) |
| `q` | string | Full-text search |
| `industry` | string[] | Filter by industry |
| `country` | string[] | ISO country codes |
| `employee_min` | int | Min employee count |
| `employee_max` | int | Max employee count |
| `technologies` | string[] | Tech stack filter |
| `lead_score_min` | float | Min lead score |
| `sort` | string | e.g. `-lead_score`, `name` |

**Response (200):**
```json
{
  "data": [
    {
      "id": "uuid",
      "name": "Acme Inc",
      "domain": "acme.com",
      "industry": "saas",
      "country": "US",
      "employee_count": 250,
      "lead_score": 82.5,
      "technologies": ["react", "aws"]
    }
  ],
  "pagination": { "page": 1, "page_size": 25, "total": 142 }
}
```

---

### POST `/companies`

**Permission:** `companies:write`

**Request:**
```json
{
  "name": "Acme Inc",
  "domain": "acme.com",
  "industry": "saas",
  "country": "US",
  "city": "San Francisco",
  "employee_count": 250,
  "annual_revenue": 50000000,
  "description": "B2B SaaS platform",
  "technologies": ["react", "postgresql"],
  "social_links": { "linkedin": "https://linkedin.com/company/acme" }
}
```

**Validation:**
- `domain`: valid, unique within org
- `name`: 1–255 chars, required
- `employee_count`: >= 0

**Response (201):** Full `CompanyResponse`

**Errors:** `409 CONFLICT` (duplicate domain)

---

### GET `/companies/{company_id}`

**Permission:** `companies:read`

---

### PATCH `/companies/{company_id}`

**Permission:** `companies:write`

**Request:** Partial update — any create fields optional.

---

### DELETE `/companies/{company_id}`

**Permission:** `companies:delete` — soft delete.

---

### POST `/companies/merge`

**Permission:** `companies:merge`

**Request:**
```json
{
  "survivor_id": "uuid",
  "duplicate_ids": ["uuid1", "uuid2"],
  "strategy": "keep_highest_score"
}
```

**Response (200):** Merged `CompanyResponse`

**Business Rules:** Reassign contacts to survivor; union technologies; highest lead_score wins.

---

### GET `/companies/{company_id}/timeline`

**Permission:** `companies:read`

**Response:** Activity timeline from events + CRM activities.

---

### GET `/companies/{company_id}/intelligence`

**Permission:** `companies:read`

**Response:**
```json
{
  "data": {
    "company_id": "uuid",
    "technologies": [{ "name": "react", "category": "frontend", "detected_at": "..." }],
    "social_profiles": [{ "platform": "linkedin", "url": "...", "followers": 12000 }],
    "funding": { "total_raised": 25000000, "last_round": "Series B" },
    "growth_signals": ["hiring_engineers", "new_office"]
  }
}
```

---

### POST `/companies/{company_id}/detect-technology`

**Permission:** `companies:write` | **Credits:** 2

Triggers async technology detection worker.

---

### GET `/companies/{company_id}/summary`

**Permission:** `companies:read`

**Response:** AI-generated company summary narrative.

---

### POST `/companies/import`

**Permission:** `companies:write` | **Credits:** 1/row

**Request:** `{ "file_id": "uuid", "mapping": { "name": "Company Name", "domain": "Website" } }`

**Response (202):** `{ "data": { "job_id": "uuid", "status": "queued" } }`

---

### POST `/companies/export`

**Permission:** `companies:read`

**Request:** `{ "format": "csv", "filters": { "industry": ["saas"] } }`

**Response (202):** Export job created.

---

### GET `/companies/spatial/search`

**Permission:** `companies:read`

**Query:** `lat`, `lng`, `radius_km`, `page`, `page_size`

---

## 6. Contacts

### GET `/contacts`

**Permission:** `contacts:read`

**Query:** `page`, `page_size`, `q`, `company_id`, `seniority`, `department`, `lead_score_min`, `email_verified`, `sort`

---

### POST `/contacts`

**Permission:** `contacts:write`

**Request:**
```json
{
  "first_name": "John",
  "last_name": "Smith",
  "email": "john@acme.com",
  "phone": "+14155551234",
  "company_id": "uuid",
  "designation": "VP Engineering",
  "department": "engineering",
  "seniority": "vp",
  "linkedin_url": "https://linkedin.com/in/johnsmith"
}
```

**Validation:**
- `email`: valid format, unique within org
- `phone`: E.164 format

---

### GET `/contacts/{contact_id}`

**Permission:** `contacts:read`

---

### PATCH `/contacts/{contact_id}`

**Permission:** `contacts:write`

---

### DELETE `/contacts/{contact_id}`

**Permission:** `contacts:delete`

---

### POST `/contacts/merge`

**Permission:** `contacts:merge`

**Request:**
```json
{
  "survivor_id": "uuid",
  "duplicate_ids": ["uuid1"],
  "prefer_verified_email": true
}
```

---

### POST `/contacts/{contact_id}/verify-email`

**Permission:** `contacts:verify` | **Credits:** 1

**Response (202):** `{ "data": { "job_id": "uuid", "status": "queued" } }`

---

### POST `/contacts/{contact_id}/verify-phone`

**Permission:** `contacts:verify` | **Credits:** 1

---

### GET `/contacts/{contact_id}/intelligence`

**Permission:** `contacts:read`

---

### GET `/contacts/{contact_id}/timeline`

**Permission:** `contacts:read`

---

### GET `/contacts/{contact_id}/notes`

**Permission:** `contacts:read`

---

### POST `/contacts/{contact_id}/notes`

**Permission:** `contacts:write`

**Request:** `{ "content": "Follow up next week about demo." }`

---

### POST `/contacts/{contact_id}/tags`

**Permission:** `contacts:write`

**Request:** `{ "tag_ids": ["uuid1", "uuid2"] }`

---

### POST `/contacts/{contact_id}/crm-sync`

**Permission:** `crm:sync` | **Credits:** 0

**Request:** `{ "connector": "salesforce", "pipeline_id": "uuid" }`

**Response (202):** Sync job queued.

---

## 7. Search

### POST `/search`

**Permission:** `search:execute` | **Credits:** 5

Execute structured filter search.

**Request:**
```json
{
  "query": "saas companies in california",
  "filters": {
    "entity_type": "company",
    "industry": ["saas"],
    "country": ["US"],
    "state": ["CA"],
    "employee_min": 50,
    "employee_max": 500
  },
  "page": 1,
  "page_size": 25
}
```

**Response (200):**
```json
{
  "data": {
    "search_id": "uuid",
    "results": [ { "entity_type": "company", "entity_id": "uuid", "score": 0.95, "data": {} } ],
    "result_count": 42,
    "credits_used": 5,
    "execution_time_ms": 234
  }
}
```

---

### POST `/search/ai`

**Permission:** `search:execute` | **Credits:** 10

Natural language AI search.

**Request:**
```json
{
  "query": "Find VP of Engineering at Series B fintech companies in New York using AWS",
  "entity_type": "contact",
  "page": 1,
  "page_size": 25
}
```

**Response (202):**
```json
{
  "data": {
    "search_id": "uuid",
    "status": "processing",
    "parsed_intent": {
      "intent": "find_contacts",
      "entities": { "seniority": "vp", "department": "engineering", "industry": "fintech" },
      "connectors": ["apollo", "clearbit"]
    }
  }
}
```

Poll: `GET /search/{search_id}`

---

### GET `/search/{search_id}`

**Permission:** `search:read`

Returns search status and results when complete.

---

### GET `/search/history`

**Permission:** `search:read`

**Query:** `page`, `page_size`, `status`, `sort=-executed_at`

---

### POST `/search/saved`

**Permission:** `search:write`

**Request:**
```json
{
  "name": "West Coast SaaS",
  "filters": { "industry": ["saas"], "country": ["US"], "state": ["CA", "WA"] },
  "notify_on_new": true
}
```

---

### GET `/search/saved`

**Permission:** `search:read`

---

### DELETE `/search/saved/{saved_search_id}`

**Permission:** `search:write`

---

### GET `/search/suggest`

**Permission:** `search:read`

**Query:** `q` (min 2 chars), `entity_type` (company|contact)

**Response:**
```json
{ "data": [{ "text": "acme.com", "type": "domain" }, { "text": "Acme Inc", "type": "company" }] }
```

---

### GET `/search/filters`

**Permission:** `search:read`

Returns available filter values (industries, countries, technologies).

---

## 8. AI Search & Scoring

### POST `/ai/score/contact/{contact_id}`

**Permission:** `ai:score` | **Credits:** 1

---

### POST `/ai/score/company/{company_id}`

**Permission:** `ai:score` | **Credits:** 1

---

### POST `/ai/score/bulk`

**Permission:** `ai:score` | **Credits:** 1/entity

**Request:**
```json
{
  "entity_type": "contact",
  "entity_ids": ["uuid1", "uuid2"],
  "icp_config": { "industries": ["saas"], "min_employees": 50 }
}
```

**Response (202):** `{ "data": { "job_id": "uuid", "status": "queued", "entity_count": 2 } }`

---

### GET `/ai/scores/contact/{contact_id}`

**Permission:** `ai:read`

---

### GET `/ai/scores/company/{company_id}`

**Permission:** `ai:read`

---

### GET `/ai/search/companies`

**Permission:** `ai:read`

**Query:** `q` (semantic query), `limit` (default 10)

Vector similarity search over company embeddings.

---

### GET `/ai/search/contacts`

**Permission:** `ai:read`

---

### GET `/ai/similar/companies/{company_id}`

**Permission:** `ai:read`

**Query:** `limit` (default 10)

---

### GET `/ai/similar/contacts/{contact_id}`

**Permission:** `ai:read`

---

### GET `/ai/recommendations`

**Permission:** `ai:read`

**Query:** `entity_type`, `entity_id`, `limit`

**Response:**
```json
{
  "data": [
    {
      "type": "next_action",
      "action": "send_email",
      "reason": "Contact has high score but no activity in 30 days",
      "confidence": 0.87
    }
  ]
}
```

---

## 9. Enrichment

### POST `/enrichment/email/verify`

**Permission:** `enrichment:execute` | **Credits:** 1

**Request:** `{ "email": "john@acme.com" }`

---

### POST `/enrichment/email/bulk-verify`

**Permission:** `enrichment:execute` | **Credits:** 1/email

**Request:** `{ "emails": ["a@x.com", "b@y.com"] }`

**Response (202):** Job queued.

---

### GET `/enrichment/email/{email}`

**Permission:** `enrichment:read`

---

### POST `/enrichment/contact/enrich`

**Permission:** `enrichment:execute` | **Credits:** 3

**Request:** `{ "contact_id": "uuid", "connectors": ["apollo", "clearbit"] }`

---

### POST `/enrichment/company/enrich`

**Permission:** `enrichment:execute` | **Credits:** 3

---

### POST `/enrichment/phone/verify`

**Permission:** `enrichment:execute` | **Credits:** 1

**Request:** `{ "phone": "+14155551234" }`

---

### POST `/enrichment/technology/detect`

**Permission:** `enrichment:execute` | **Credits:** 2

**Request:** `{ "domain": "acme.com" }`

---

## 10. Connectors

### GET `/connectors`

**Permission:** `connectors:read`

**Response:**
```json
{
  "data": [
    {
      "name": "apollo",
      "display_name": "Apollo.io",
      "type": "search",
      "capabilities": ["search", "lookup", "enrich"],
      "status": "healthy"
    }
  ]
}
```

---

### GET `/connectors/configs`

**Permission:** `connectors:read`

---

### POST `/connectors/configs`

**Permission:** `connectors:write`

**Request:**
```json
{
  "connector_name": "apollo",
  "credentials": { "api_key": "..." },
  "settings": { "default_limit": 25 },
  "is_active": true
}
```

---

### PATCH `/connectors/configs/{config_id}`

**Permission:** `connectors:write`

---

### DELETE `/connectors/configs/{config_id}`

**Permission:** `connectors:write`

---

### POST `/connectors/configs/{config_id}/test`

**Permission:** `connectors:write`

**Response:** `{ "data": { "healthy": true, "latency_ms": 142 } }`

---

### GET `/connectors/jobs`

**Permission:** `connectors:read`

**Query:** `status`, `connector_name`, `page`, `page_size`

---

### GET `/connectors/jobs/{job_id}`

**Permission:** `connectors:read`

---

## 11. CRM

### Pipelines

| Method | Route | Permission | Description |
|--------|-------|------------|-------------|
| GET | `/crm/pipelines` | `crm:read` | List pipelines |
| POST | `/crm/pipelines` | `crm:write` | Create pipeline |
| GET | `/crm/pipelines/{id}` | `crm:read` | Get pipeline with stages |
| PATCH | `/crm/pipelines/{id}` | `crm:write` | Update pipeline |
| DELETE | `/crm/pipelines/{id}` | `crm:delete` | Delete pipeline |

### Deals

| Method | Route | Permission | Description |
|--------|-------|------------|-------------|
| GET | `/crm/deals` | `crm:read` | List deals |
| POST | `/crm/deals` | `crm:write` | Create deal |
| GET | `/crm/deals/{id}` | `crm:read` | Get deal |
| PATCH | `/crm/deals/{id}` | `crm:write` | Update deal / move stage |
| DELETE | `/crm/deals/{id}` | `crm:delete` | Delete deal |

**Create Deal Request:**
```json
{
  "title": "Acme Enterprise Deal",
  "company_id": "uuid",
  "contact_id": "uuid",
  "pipeline_id": "uuid",
  "stage_id": "uuid",
  "value": 50000,
  "currency": "USD",
  "expected_close_date": "2026-09-30"
}
```

### Tasks

| Method | Route | Permission |
|--------|-------|------------|
| GET | `/crm/tasks` | `crm:read` |
| POST | `/crm/tasks` | `crm:write` |
| PATCH | `/crm/tasks/{id}` | `crm:write` |
| DELETE | `/crm/tasks/{id}` | `crm:delete` |

### Tags

| Method | Route | Permission |
|--------|-------|------------|
| GET | `/crm/tags` | `crm:read` |
| POST | `/crm/tags` | `crm:write` |
| DELETE | `/crm/tags/{id}` | `crm:delete` |

### Lists

| Method | Route | Permission |
|--------|-------|------------|
| GET | `/crm/lists` | `crm:read` |
| POST | `/crm/lists` | `crm:write` |
| POST | `/crm/lists/{id}/contacts` | `crm:write` |
| DELETE | `/crm/lists/{id}/contacts/{contact_id}` | `crm:write` |

### Activities

| Method | Route | Permission |
|--------|-------|------------|
| GET | `/crm/activities` | `crm:read` |
| POST | `/crm/activities` | `crm:write` |

### CRM Sync

| Method | Route | Permission |
|--------|-------|------------|
| POST | `/crm/sync/push` | `crm:sync` |
| POST | `/crm/sync/pull` | `crm:sync` |
| GET | `/crm/sync/status` | `crm:read` |

---

## 12. Workflows

### GET `/workflows`

**Permission:** `workflows:read`

---

### POST `/workflows`

**Permission:** `workflows:write`

**Request:**
```json
{
  "name": "Auto-score new contacts",
  "trigger": { "event": "contact.created" },
  "conditions": [{ "field": "contact.seniority", "operator": "in", "value": ["vp", "c_level"] }],
  "actions": [
    { "type": "score_entity", "params": { "entity_type": "contact" } },
    { "type": "send_notification", "params": { "template": "high_value_contact" } }
  ],
  "is_active": true
}
```

---

### PATCH `/workflows/{workflow_id}`

**Permission:** `workflows:write`

---

### DELETE `/workflows/{workflow_id}`

**Permission:** `workflows:delete`

---

### GET `/workflows/{workflow_id}/executions`

**Permission:** `workflows:read`

---

### POST `/workflows/{workflow_id}/execute`

**Permission:** `workflows:execute` — manual trigger.

**Request:** `{ "entity_type": "contact", "entity_id": "uuid" }`

---

## 13. Exports & Imports

### POST `/exports`

**Permission:** `exports:create`

**Request:**
```json
{
  "entity_type": "contact",
  "format": "csv",
  "filters": { "lead_score_min": 70 },
  "columns": ["first_name", "last_name", "email", "company_name", "lead_score"]
}
```

**Response (202):**
```json
{ "data": { "export_id": "uuid", "status": "queued", "estimated_rows": 1250 } }
```

---

### GET `/exports`

**Permission:** `exports:read`

---

### GET `/exports/{export_id}`

**Permission:** `exports:read`

---

### GET `/exports/{export_id}/download`

**Permission:** `exports:read`

**Response:** Redirect to presigned S3 URL or stream file.

---

### DELETE `/exports/{export_id}`

**Permission:** `exports:delete`

---

### POST `/imports`

**Permission:** `imports:create`

**Request:**
```json
{
  "entity_type": "company",
  "format": "csv",
  "file_id": "uuid",
  "mapping": { "name": "Company", "domain": "Website" },
  "options": { "skip_duplicates": true, "update_existing": false }
}
```

---

### GET `/imports/{job_id}`

**Permission:** `imports:read`

**Response:**
```json
{
  "data": {
    "id": "uuid",
    "status": "processing",
    "total_rows": 5000,
    "processed_rows": 2300,
    "errors": [{ "row": 42, "field": "domain", "message": "Invalid domain" }],
    "created_count": 2100,
    "updated_count": 150,
    "skipped_count": 50
  }
}
```

---

## 14. Analytics

### GET `/analytics/dashboard`

**Permission:** `analytics:read`

**Response:**
```json
{
  "data": {
    "total_companies": 1250,
    "total_contacts": 8400,
    "avg_lead_score": 62.3,
    "credits_used_this_month": 1234,
    "searches_this_month": 89,
    "top_industries": [{ "industry": "saas", "count": 320 }]
  }
}
```

---

### GET `/analytics/lead-velocity`

**Query:** `period` (7d|30d|90d)

---

### GET `/analytics/score-distribution`

---

### GET `/analytics/industry`

---

### GET `/analytics/geography`

---

### GET `/analytics/seniority`

---

### GET `/analytics/search-activity`

---

### GET `/analytics/crm-funnel`

**Query:** `pipeline_id`

---

### GET `/analytics/credits`

---

### GET `/analytics/full`

Combined dashboard payload (cached 10 min).

---

## 15. Notifications

### GET `/notifications`

**Permission:** Authenticated

**Query:** `page`, `page_size`, `is_read`, `type`

---

### GET `/notifications/unread-count`

---

### POST `/notifications/mark-read`

**Request:** `{ "notification_ids": ["uuid1"] }`

---

### POST `/notifications/mark-all-read`

---

### DELETE `/notifications/{notification_id}`

---

### WS `/notifications/ws`

**Permission:** JWT via `?token=` query param

**Messages:**
```json
{ "type": "notification", "data": { "id": "uuid", "title": "...", "body": "..." } }
```

---

### POST `/notifications/preferences`

**Request:**
```json
{
  "email_enabled": true,
  "push_enabled": true,
  "categories": { "lead_scored": true, "export_completed": true }
}
```

---

## 16. Billing

### GET `/billing/subscription`

**Permission:** `billing:read`

---

### POST `/billing/subscription`

**Permission:** `billing:write`

**Request:** `{ "plan": "pro", "payment_method_id": "pm_..." }`

---

### PATCH `/billing/subscription/plan`

**Request:** `{ "plan": "enterprise" }`

---

### DELETE `/billing/subscription`

Cancel at period end.

---

### GET `/billing/credits`

---

### GET `/billing/credits/transactions`

**Query:** `page`, `page_size`, `type`, `sort=-created_at`

---

### POST `/billing/credits/add`

**Permission:** `billing:admin`

**Request:** `{ "amount": 1000, "reason": "Promotional credit" }`

---

### GET `/billing/portal`

Returns Stripe customer portal URL.

---

### POST `/billing/webhooks/stripe`

**Permission:** Stripe signature verification (no JWT).

---

## 17. Admin

### GET `/admin/stats`

**Permission:** `admin:read`

Platform-wide statistics (superadmin only).

---

### GET `/admin/audit-logs`

**Permission:** `admin:audit`

**Query:** `page`, `page_size`, `user_id`, `action`, `resource_type`, `from`, `to`

---

### GET `/admin/settings`

### PATCH `/admin/settings/{key}`

**Permission:** `admin:settings`

---

### GET `/admin/feature-flags`

### PATCH `/admin/feature-flags/{key}`

**Permission:** `admin:settings`

**Request:** `{ "enabled": true, "rollout_percentage": 50 }`

---

## 18. Developer API

Developer API uses `X-API-Key` header. Scopes enforced per key.

### Rate Limits by Tier

| Tier | Requests/min | Burst |
|------|-------------|-------|
| Free | 60 | 10 |
| Pro | 300 | 50 |
| Enterprise | 1000 | 200 |

### Available Scopes

All read/write endpoints for: `companies`, `contacts`, `search`, `ai:score`, `enrichment`, `exports`

Not available via API key: `admin:*`, `billing:write`, `users:delete`

### Webhook Subscriptions

| Method | Route | Permission |
|--------|-------|------------|
| GET | `/developer/webhooks` | `api_keys:read` |
| POST | `/developer/webhooks` | `api_keys:write` |
| DELETE | `/developer/webhooks/{id}` | `api_keys:write` |

**Webhook Payload:**
```json
{
  "event": "lead.scored",
  "data": { "contact_id": "uuid", "score": 85.2 },
  "timestamp": "2026-06-28T12:00:00Z"
}
```

---

## 19. Files

### POST `/files/upload-url`

**Permission:** Authenticated

**Request:**
```json
{
  "filename": "companies.csv",
  "content_type": "text/csv",
  "purpose": "import"
}
```

**Response:**
```json
{
  "data": {
    "file_id": "uuid",
    "upload_url": "https://s3.../presigned",
    "expires_at": "2026-06-28T12:15:00Z"
  }
}
```

---

## 20. Health & Observability

### GET `/health/live`

**Permission:** Public

**Response (200):** `{ "status": "alive" }`

---

### GET `/health/ready`

**Permission:** Public (internal network in prod)

**Response (200):**
```json
{
  "status": "ready",
  "checks": {
    "database": { "status": "up", "latency_ms": 2 },
    "redis": { "status": "up", "latency_ms": 1 },
    "opensearch": { "status": "up", "latency_ms": 5 }
  }
}
```

---

### GET `/health`

Detailed health with version info.

---

### GET `/metrics`

**Permission:** Internal (Prometheus scrape)

Returns Prometheus text format.

---

*End of Phase 3 API Specification*