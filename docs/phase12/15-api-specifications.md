# 15 — API Specifications

**Version 5.0** | Phase 12 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [Authentication & Permissions](#2-authentication--permissions)
3. [Health & Settings](#3-health--settings)
4. [Security Events & Incidents](#4-security-events--incidents)
5. [Risk & Access Logs](#5-risk--access-logs)
6. [IAM Endpoints](#6-iam-endpoints)
7. [Policy Management](#7-policy-management)
8. [Compliance & Privacy](#8-compliance--privacy)
9. [Vulnerability & Alerts](#9-vulnerability--alerts)
10. [Error Codes](#10-error-codes)

---

## 1. Overview

Phase 12 publishes security REST contracts under `/api/v1/security/*` served via Kong gateway. Routes are implemented in `backend/app/security/router.py`.

**Base URL (gateway):** `http://localhost/api/v1/security`  
**Base URL (direct dev):** `http://localhost:8000/api/v1/security`  
**Content-Type:** `application/json`  
**Response envelope:** `APIResponse[T]` from `backend/app/common/response.py`

All endpoints gated by feature flag `enterprise_security_v5`.

---

## 2. Authentication & Permissions

### Auth Methods

| Method | Header | Use Case |
|--------|--------|----------|
| JWT | `Authorization: Bearer {token}` | User sessions, security admin |
| API Key | `Authorization: ApiKey ali_live_...` | Automated compliance checks (scoped) |

### Security Permissions

| Permission | Scope | Roles |
|------------|-------|-------|
| `security:read` | View events, risk scores, policies | manager, admin |
| `security:write` | MFA, devices, sessions (self) | member+ |
| `security:investigate` | Incidents, alerts, auth logs | admin |
| `security:admin` | Policy CRUD, settings, session revoke | admin, owner |
| `security:compliance` | Compliance checks, privacy requests, audit export | admin |

---

## 3. Health & Settings

### GET /security/health

```http
GET /api/v1/security/health
```

**Response:** `APIResponse[SecurityHealth]`

```json
{
  "success": true,
  "data": {
    "status": "healthy",
    "version": "5.0",
    "subsystems": {
      "policy_engine": "healthy",
      "risk_scorer": "healthy",
      "soc_processor": "healthy",
      "compliance_runner": "healthy"
    },
    "feature_flag": "enterprise_security_v5"
  }
}
```

### GET /security/settings

```http
GET /api/v1/security/settings
Authorization: Bearer {token}
```

**Permission:** `security:read`

**Response:**

```json
{
  "data": {
    "mfa_required": true,
    "mfa_grace_days": 7,
    "ip_allowlist": ["203.0.113.0/24"],
    "session_max_concurrent": 5,
    "export_requires_approval": true,
    "ai_pii_redaction": true,
    "compliance_profile": "gdpr_strict"
  }
}
```

### PATCH /security/settings

```http
PATCH /api/v1/security/settings
Authorization: Bearer {token}
```

**Permission:** `security:admin`

**Request:**

```json
{
  "mfa_required": true,
  "ip_allowlist": ["203.0.113.0/24", "198.51.100.0/24"]
}
```

---

## 4. Security Events & Incidents

### GET /security/events

```http
GET /api/v1/security/events?severity=high&event_type=authz.denied&page=1&per_page=25
```

**Permission:** `security:read` (own org) | `security:investigate` (detailed metadata)

**Query Parameters:**

| Param | Type | Description |
|-------|------|-------------|
| `severity` | string | info, low, medium, high, critical |
| `event_type` | string | Dot-notation event type |
| `actor_id` | uuid | Filter by actor |
| `start_date` | date | ISO 8601 |
| `end_date` | date | ISO 8601 |
| `page` | int | Default 1 |
| `per_page` | int | Default 25, max 100 |

**Response:** `PaginatedResponse[SecurityEventResponse]`

### GET /security/events/{id}

**Permission:** `security:read`

### GET /security/incidents

```http
GET /api/v1/security/incidents?status=open&severity=P1
```

**Permission:** `security:investigate`

### POST /security/incidents

```http
POST /api/v1/security/incidents
```

**Permission:** `security:investigate`

**Request:**

```json
{
  "title": "Suspected API key compromise",
  "severity": "P2",
  "incident_type": "credential_compromise",
  "description": "API key found in public GitHub repo",
  "event_ids": ["uuid1", "uuid2"]
}
```

### GET /security/incidents/{id}

**Permission:** `security:investigate`

### PATCH /security/incidents/{id}

**Permission:** `security:investigate`

**Request:**

```json
{
  "status": "investigating",
  "assigned_to": "uuid",
  "severity": "P1"
}
```

### POST /security/incidents/{id}/timeline

**Permission:** `security:investigate`

**Request:**

```json
{
  "action": "contained",
  "notes": "Revoked compromised API key"
}
```

### POST /security/incidents/{id}/close

**Permission:** `security:admin`

**Request:**

```json
{
  "root_cause": "API key committed to public repository",
  "remediation": "Key rotated, gitleaks added to CI",
  "status": "closed"
}
```

---

## 5. Risk & Access Logs

### GET /security/risk-scores

```http
GET /api/v1/security/risk-scores?subject_type=user&subject_id={uuid}
```

**Permission:** `security:read` (own user) | `security:investigate` (any user in org)

### GET /security/risk-scores/me

Current user's risk score.

**Permission:** `security:write`

### GET /security/access-logs

```http
GET /api/v1/security/access-logs?decision=deny&page=1
```

**Permission:** `security:investigate`

### GET /security/authentication-logs

```http
GET /api/v1/security/authentication-logs?user_id={uuid}&success=false
```

**Permission:** `security:investigate`

### GET /security/authorization-logs

```http
GET /api/v1/security/authorization-logs?decision=deny
```

**Permission:** `security:investigate`

---

## 6. IAM Endpoints

### MFA Devices

#### GET /security/mfa/devices

**Permission:** `security:write` (own devices)

#### POST /security/mfa/devices

**Permission:** `security:write`

**Request:**

```json
{
  "type": "totp",
  "label": "Authenticator App"
}
```

**Response:**

```json
{
  "data": {
    "id": "uuid",
    "type": "totp",
    "provisioning_uri": "otpauth://totp/...",
    "secret_qr_base64": "data:image/png;base64,...",
    "is_verified": false
  }
}
```

#### POST /security/mfa/verify

**Permission:** `security:write`

**Request:**

```json
{
  "device_id": "uuid",
  "code": "123456"
}
```

#### DELETE /security/mfa/devices/{id}

**Permission:** `security:write` (own) | `security:admin` (any user in org)

### Trusted Devices

#### GET /security/devices

**Permission:** `security:write`

#### DELETE /security/devices/{id}

**Permission:** `security:write`

#### POST /security/devices/revoke-all

**Permission:** `security:admin`

**Request:**

```json
{ "user_id": "uuid" }
```

### Sessions

#### GET /security/sessions

List active sessions for current user.

**Permission:** `security:write`

#### POST /security/sessions/revoke

**Permission:** `security:write` (own session) | `security:admin` (any)

**Request:**

```json
{
  "session_id": "uuid",
  "revoke_all": false
}
```

#### POST /security/sessions/revoke-all

**Permission:** `security:admin`

---

## 7. Policy Management

### GET /security/policies

```http
GET /api/v1/security/policies?category=authentication&is_active=true
```

**Permission:** `security:read`

### POST /security/policies

**Permission:** `security:admin`

**Request:**

```json
{
  "name": "Require MFA for Admin",
  "category": "authentication",
  "priority": 200,
  "rules": {
    "conditions": [
      { "field": "role", "operator": "in", "value": ["admin", "owner"] },
      { "field": "mfa_verified", "operator": "eq", "value": false }
    ],
    "actions": [{ "type": "deny", "reason": "mfa_required" }]
  }
}
```

### GET /security/policies/{id}

**Permission:** `security:read`

### PATCH /security/policies/{id}

**Permission:** `security:admin`

### DELETE /security/policies/{id}

Soft-deactivate: `is_active = false`. **Permission:** `security:admin`

### POST /security/policies/{id}/assignments

**Permission:** `security:admin`

**Request:**

```json
{
  "target_type": "role",
  "target_id": "admin",
  "effective_from": "2026-07-01T00:00:00Z"
}
```

### GET /security/policies/{id}/assignments

**Permission:** `security:read`

---

## 8. Compliance & Privacy

### Compliance Checks

#### GET /security/compliance/checks

```http
GET /api/v1/security/compliance/checks?framework=gdpr&status=fail
```

**Permission:** `security:compliance`

#### POST /security/compliance/checks/run

**Permission:** `security:compliance`

**Request:**

```json
{
  "framework": "gdpr",
  "control_id": "gdpr.consent.tracking"
}
```

#### GET /security/compliance/report

```http
GET /api/v1/security/compliance/report?framework=soc2
```

**Permission:** `security:compliance`

#### GET /security/compliance/evidence/{check_id}

**Permission:** `security:compliance`

### Consent

#### GET /security/consent

```http
GET /api/v1/security/consent?subject_id={uuid}&purpose=ai_scoring
```

**Permission:** `security:read`

#### POST /security/consent

**Permission:** `security:admin`

**Request:**

```json
{
  "subject_type": "contact",
  "subject_id": "uuid",
  "purpose": "ai_scoring",
  "legal_basis": "consent",
  "evidence": { "form_version": "v2.1", "ip": "203.0.113.1" }
}
```

#### DELETE /security/consent/{id}

Withdraw consent. **Permission:** `security:admin`

### Privacy Requests

#### GET /security/privacy-requests

**Permission:** `security:compliance`

#### POST /security/privacy-requests

**Permission:** `security:compliance`

**Request:**

```json
{
  "request_type": "erasure",
  "subject_email": "contact@example.com",
  "details": "Support ticket #1234"
}
```

#### PATCH /security/privacy-requests/{id}

**Permission:** `security:compliance`

### Audit Export

#### POST /security/audit/export

**Permission:** `security:compliance`

**Request:**

```json
{
  "start_date": "2026-01-01",
  "end_date": "2026-06-30",
  "include": ["audit_logs", "security_events"],
  "format": "json"
}
```

**Response:** `APIResponse[ExportJobResponse]` with `job_id` for async download.

---

## 9. Vulnerability & Alerts

### GET /security/vulnerabilities

```http
GET /api/v1/security/vulnerabilities?status=open&severity=critical
```

**Permission:** `security:admin` (platform-wide) | `security:investigate` (org-scoped)

### POST /security/vulnerabilities

**Permission:** `security:admin`

### PATCH /security/vulnerabilities/{id}

**Permission:** `security:admin`

**Request:**

```json
{
  "status": "remediated",
  "remediation_notes": "Upgraded fastapi to 0.115.1"
}
```

### POST /security/vulnerabilities/import

CI scanner ingest endpoint.

**Permission:** `security:admin` (service account)

**Request:**

```json
{
  "source": "pip-audit",
  "findings": [
    {
      "cve": "CVE-2026-1234",
      "package": "requests",
      "version": "2.28.0",
      "fix_version": "2.32.0",
      "cvss": 7.5
    }
  ]
}
```

### GET /security/alerts

```http
GET /api/v1/security/alerts?status=active&severity=high
```

**Permission:** `security:investigate`

### PATCH /security/alerts/{id}/acknowledge

**Permission:** `security:investigate`

### PATCH /security/alerts/{id}/resolve

**Permission:** `security:investigate`

---

## 10. Error Codes

| Code | HTTP | Description |
|------|------|-------------|
| `SECURITY_DISABLED` | 503 | Feature flag `enterprise_security_v5` off |
| `STEP_UP_REQUIRED` | 403 | MFA verification needed |
| `RISK_TOO_HIGH` | 403 | Zero trust risk score exceeded threshold |
| `POLICY_DENIED` | 403 | Policy engine denied access |
| `MFA_REQUIRED` | 403 | MFA not enrolled but required by policy |
| `MFA_INVALID` | 401 | Invalid MFA code |
| `DEVICE_NOT_TRUSTED` | 403 | Action requires trusted device |
| `SESSION_REVOKED` | 401 | Session has been revoked |
| `CONSENT_REQUIRED` | 403 | Missing consent for data processing |
| `DLP_BLOCKED` | 403 | Data loss prevention rule triggered |
| `COMPLIANCE_CHECK_FAILED` | 422 | Compliance prerequisite not met |
| `PRIVACY_REQUEST_OVERDUE` | 409 | Cannot close overdue privacy request |
| `PROMPT_INJECTION` | 400 | AI input blocked by sanitizer |
| `FORBIDDEN` | 403 | Missing `security:*` permission |

### Error Response Format

```json
{
  "success": false,
  "code": "STEP_UP_REQUIRED",
  "message": "MFA verification required for this action",
  "data": {
    "mfa_challenge_url": "/api/v1/security/mfa/verify"
  }
}
```

### OpenAPI Tags

```python
# backend/app/security/router.py
router = APIRouter(prefix="/security", tags=["Security"])

# Sub-tags for OpenAPI grouping:
# Security - Health
# Security - Events & Incidents
# Security - IAM
# Security - Policies
# Security - Compliance
# Security - Vulnerabilities
```

### Cross-References

| Topic | Document |
|-------|----------|
| Database schema | [14-security-database-schema.md](./14-security-database-schema.md) |
| API security framework | [06-api-security-framework.md](./06-api-security-framework.md) |
| IAM design | [02-identity-access-management-design.md](./02-identity-access-management-design.md) |
| Phase 10 REST patterns | [../phase10/02-rest-api-specification.md](../phase10/02-rest-api-specification.md) |