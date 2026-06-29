# 13 — Security Model

**Version 1.0** | Phase 8 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [RBAC Permissions](#2-rbac-permissions)
3. [Tenant Isolation](#3-tenant-isolation)
4. [Expression Sandboxing](#4-expression-sandboxing)
5. [Webhook Security](#5-webhook-security)
6. [AI Node Security](#6-ai-node-security)
7. [Data Access Controls](#7-data-access-controls)
8. [Audit Logging](#8-audit-logging)
9. [Threat Model](#9-threat-model)

---

## 1. Overview

The workflow platform handles **cross-domain automation** with access to contacts, CRM data, AI providers, and external webhooks. Security is enforced at four layers:

1. **API** — JWT + RBAC via `backend/app/core/permissions.py`
2. **Tenant** — Row-level `organization_id` isolation
3. **Runtime** — Expression sandbox, node permission checks
4. **Audit** — All mutations logged to `audit.audit_logs`

---

## 2. RBAC Permissions

### Workflow Permissions

| Permission | Roles | Scope |
|------------|-------|-------|
| `workflows:read` | manager, admin, owner | View workflows, executions, analytics |
| `workflows:write` | manager, admin, owner | Create, edit, activate workflows |
| `workflows:execute` | manager, admin, owner | Manual trigger, test run, cancel |
| `workflows:delete` | manager, admin, owner | Soft delete workflows |
| `workflows:approve` | manager, admin, owner | Decide approval requests |
| `workflows:admin` | admin, owner | Templates, replay, quotas, org settings |

### Permission Enforcement

```python
# backend/app/workflows/router.py
@router.post("/workflows")
@require_permission("workflows:write")
async def create_workflow(ctx: RequestContext, body: CreateWorkflowRequest):
    return await workflow_service.create(ctx, body)
```

### Node-Level Permission Checks

Certain node types require additional permissions at **runtime**:

| Node Type | Required Permission |
|-----------|---------------------|
| `crm_sync` | `crm:sync` |
| `export_data` | `exports:create` |
| `ai_score` | `ai:score` |
| `http_request` (external) | `workflows:admin` |
| `sub_workflow` | Same as child workflow |

If triggering user lacks permission, step fails with `FORBIDDEN` (not workflow owner bypass).

---

## 3. Tenant Isolation

### Database Level

Every workflow table includes `organization_id` with FK to `core.organizations`:

```python
async def get_workflow(ctx: RequestContext, workflow_id: UUID) -> Workflow:
    return await repo.get_by_id(
        workflow_id,
        organization_id=ctx.organization_id,  # Always filtered
    )
```

### Cache Keys

All Redis keys prefixed with org ID:

```
wf:plan:{org_id}:{version_id}
wf:triggers:{org_id}:{event_type}
wf:ratelimit:{org_id}
wf:idempotency:{org_id}:{key}
```

### Cross-Tenant Prevention

| Vector | Mitigation |
|--------|------------|
| Workflow ID guessing | 404 if org mismatch (not 403, to prevent enumeration) |
| Entity ID in trigger | Validate entity belongs to org before execution |
| Sub-workflow call | Child workflow must be same org |
| Template instantiation | System templates only; org templates scoped |
| Event replay | `organization_id` required in replay request |

### Integration Tests

```python
async def test_cross_tenant_workflow_access_denied():
    workflow = await create_workflow(org_a, ...)
    with pytest.raises(NotFoundException):
        await get_workflow(org_b_ctx, workflow.id)
```

---

## 4. Expression Sandboxing

See [04-rule-engine-design.md](./04-rule-engine-design.md) for full sandbox spec.

### Summary

| Control | Implementation |
|---------|----------------|
| No `eval()` / `exec()` | Custom AST interpreter |
| No imports | Deny list at compile time |
| No file/network access | Sandboxed builtins only |
| CPU time limit | 100ms per evaluation |
| Memory limit | Max AST depth 32 |
| String length limit | 10,000 chars |

### Compile-Time vs Runtime

- **Compile-time:** Reject dangerous constructs before save
- **Runtime:** Timeout + resource limits as defense-in-depth

---

## 5. Webhook Security

### `webhook_trigger` Authentication

Webhooks use **HMAC-SHA256** signatures, not JWT:

```python
def verify_webhook_signature(
    payload: bytes,
    signature: str,
    timestamp: str,
    secret: str,
) -> bool:
    # Reject if timestamp > 5 minutes old (replay protection)
    if abs(time.time() - int(timestamp)) > 300:
        return False
    expected = hmac.new(
        secret.encode(),
        f"{timestamp}.{payload.decode()}".encode(),
        hashlib.sha256,
    ).hexdigest()
    return hmac.compare_digest(f"sha256={expected}", signature)
```

### Webhook Secrets

- Generated on workflow activation: `whsec_{random_32_bytes}`
- Stored as SHA-256 hash in `workflow_versions.definition` trigger config
- Rotatable via `POST /workflows/{id}/webhook/rotate-secret`

### Rate Limiting

| Limit | Value |
|-------|-------|
| Per webhook_id | 100 req/min |
| Per org | 1,000 req/min |
| Payload size | 1 MB max |

### IP Allowlist (Optional)

```json
{
  "webhook_config": {
    "allowed_ips": ["203.0.113.0/24"],
    "require_signature": true
  }
}
```

---

## 6. AI Node Security

### Prompt Injection Mitigation

```python
INJECTION_PATTERNS = [
    r"ignore\s+(previous|above)\s+instructions",
    r"system\s*:",
    r"<\|.*?\|>",  # Special tokens
]

def sanitize_ai_input(text: str, max_length: int = 8000) -> str:
    text = text[:max_length]
    for pattern in INJECTION_PATTERNS:
        text = re.sub(pattern, "[FILTERED]", text, flags=re.IGNORECASE)
    return text
```

### Output Validation

AI node outputs validated against expected schema before passing to downstream nodes. Unexpected fields stripped.

### PII Handling

| Data | Treatment |
|------|-----------|
| Email addresses | Logged as hashed in step output |
| Phone numbers | Masked in execution logs |
| AI prompts | Not stored in execution logs (only token counts) |
| AI responses | Stored in `step.output` (org-scoped, 90-day retention) |

### Credit Fraud Prevention

- Credit reservation before AI call (atomic)
- Per-org daily AI credit cap (configurable)
- Anomaly detection: >10x normal AI usage → alert + throttle

---

## 7. Data Access Controls

### Execution Log Access

| Role | Access |
|------|--------|
| viewer | No execution access |
| manager | Own org executions |
| admin | Own org + export |
| platform admin | Cross-tenant (audit only) |

### Sensitive Node Output Redaction

```python
REDACTED_FIELDS = {"password", "api_key", "secret", "token", "ssn"}

def redact_step_output(output: dict) -> dict:
    """Applied before API response for non-admin users."""
```

### `http_request` Node Restrictions

| Restriction | Value |
|-------------|-------|
| Allowed methods | GET, POST, PUT, PATCH |
| Blocked hosts | `localhost`, `127.0.0.1`, `10.*`, `172.16.*`, `192.168.*`, `metadata.google.internal` |
| Max response size | 1 MB |
| Timeout | 30s |
| Follow redirects | Max 3 |
| Custom headers | Blocked: `Authorization` injection from expressions |

---

## 8. Audit Logging

All workflow mutations logged to `audit.audit_logs`:

| Entity | Actions |
|--------|---------|
| `workflow` | `created`, `updated`, `activated`, `deactivated`, `deleted` |
| `workflow_execution` | `started`, `completed`, `failed`, `cancelled` |
| `workflow_approval` | `requested`, `approved`, `rejected`, `escalated`, `timed_out` |
| `workflow_template` | `instantiated`, `created` |
| `event_replay` | `started`, `completed` |

### Audit Entry Schema

```json
{
  "entity": "workflow",
  "entity_id": "uuid",
  "action": "activated",
  "user_id": "uuid",
  "organization_id": "uuid",
  "old_values": { "is_active": false, "status": "draft" },
  "new_values": { "is_active": true, "status": "active" },
  "ip_address": "203.0.113.50",
  "metadata": { "version_id": "uuid", "version_number": 3 }
}
```

---

## 9. Threat Model

### STRIDE Analysis

| Threat | Category | Mitigation |
|--------|----------|------------|
| Cross-tenant data access | Tampering | `organization_id` on all queries |
| Expression code injection | Elevation | Sandbox interpreter |
| Webhook replay | Spoofing | HMAC + timestamp validation |
| AI prompt injection | Tampering | Input sanitization |
| SSRF via http_request | Info Disclosure | Host blocklist |
| Workflow bombing | DoS | Rate limits, concurrent execution caps |
| Approval bypass | Elevation | Server-side approver validation |
| Secret leakage in logs | Info Disclosure | Output redaction |

### Security Testing Requirements

- [ ] Cross-tenant access tests for all API endpoints
- [ ] Sandbox escape attempts (100+ patterns)
- [ ] Webhook signature bypass attempts
- [ ] SSRF payload catalog for `http_request` node
- [ ] AI prompt injection test suite
- [ ] Rate limit validation under load

---

## Related Documents

- [04-rule-engine-design.md](./04-rule-engine-design.md) — Sandbox details
- [08-ai-node-specifications.md](./08-ai-node-specifications.md) — AI security
- [phase3/backend-architecture.md](../phase3/backend-architecture.md) — Platform security
- [15-testing-strategy.md](./15-testing-strategy.md) — Security test plan