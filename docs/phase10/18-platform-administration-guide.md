# 18 — Platform Administration Guide

**Version 4.0** | Phase 10 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [Initial Setup](#2-initial-setup)
3. [Feature Flags](#3-feature-flags)
4. [Gateway Administration](#4-gateway-administration)
5. [Quota Management](#5-quota-management)
6. [API Key Administration](#6-api-key-administration)
7. [OAuth Administration](#7-oauth-administration)
8. [Webhook Administration](#8-webhook-administration)
9. [Marketplace Moderation](#9-marketplace-moderation)
10. [Security Operations](#10-security-operations)
11. [Troubleshooting](#11-troubleshooting)

---

## 1. Overview

This guide is for **Platform Administrators** and **Tenant Admins** who configure, manage, and maintain the integration platform.

**Required permissions:** `platform:admin` (platform-wide) or `admin` role (tenant-scoped)

---

## 2. Initial Setup

### Enable Integration Platform

```powershell
# Run migration
cd C:\path\to\AI-Lead-intelligence-\backend
alembic upgrade head  # Applies 016_phase10_integration_platform

# Enable feature flag (global)
curl -X POST http://localhost/api/v1/admin/feature-flags `
  -H "Authorization: Bearer $ADMIN_TOKEN" `
  -H "Content-Type: application/json" `
  -d '{ "key": "integration_platform_v4", "is_enabled": true }'

# Enable GraphQL (optional, per org)
curl -X POST http://localhost/api/v1/admin/feature-flags `
  -H "Authorization: Bearer $ADMIN_TOKEN" `
  -d '{ "key": "graphql_enabled", "is_enabled": true, "organization_id": "org-uuid" }'

# Start gateway overlay
docker compose -f docker-compose.yml -f docker-compose.gateway.yml --profile gateway up -d

# Verify
curl http://localhost/api/v1/platform/health
```

### Post-Setup Verification

| Check | Command | Expected |
|-------|---------|----------|
| Gateway routing | `curl http://localhost/api/v1/health` | 200 OK |
| Platform health | `curl http://localhost/api/v1/platform/health` | All subsystems healthy |
| Kong admin | `curl http://localhost:8080/api/overview` | Kong running |
| RabbitMQ | `curl http://localhost:15672` | Management UI accessible |
| MinIO | `curl http://localhost:9001` | Console accessible |

---

## 3. Feature Flags

| Flag | Scope | Purpose |
|------|-------|---------|
| `integration_platform_v4` | Global/Org | Enable all Phase 10 features |
| `graphql_enabled` | Global/Org | Enable GraphQL endpoint |
| `marketplace_enabled` | Global | Enable marketplace browsing |
| `oauth_enabled` | Global/Org | Enable OAuth 2.0 flows |
| `partner_streams_enabled` | Org | Enable SSE/AMQP event streams |
| `plugin_sandbox_disabled` | Dev only | Disable sandbox (local dev) |

### Per-Organization Enablement

```http
POST /api/v1/admin/feature-flags
{
  "key": "integration_platform_v4",
  "is_enabled": true,
  "organization_id": "019f0c1f-org-uuid"
}
```

---

## 4. Gateway Administration

### Kong Configuration Updates

1. Edit `infra/gateway/kong/kong.yml`
2. Validate: `docker exec kong kong config parse /kong/kong.yml`
3. Reload: `docker exec kong kong reload`
4. Verify: `curl http://localhost/api/v1/platform/health`

### Rate Limit Tuning

```yaml
# infra/gateway/kong/kong.yml
plugins:
  - name: rate-limiting
    config:
      minute: 300        # Adjust per environment
      policy: redis      # Use redis in staging/prod
      redis_host: redis
      fault_tolerant: true
```

### IP Allowlists (Enterprise)

```yaml
plugins:
  - name: ip-restriction
    config:
      allow:
        - "203.0.113.0/24"    # Customer office
        - "198.51.100.42"      # Customer VPN
```

### Traefik Dashboard

Access at `http://localhost:8080/dashboard/` (development only).

---

## 5. Quota Management

### Tier Configuration

```http
PATCH /api/v1/platform/admin/quotas/{organization_id}
Authorization: Bearer {admin_token}

{
  "tier": "enterprise",
  "requests_per_minute": 1000,
  "webhooks_per_day": 100000,
  "graphql_complexity_limit": 10000,
  "max_api_keys": 50,
  "max_webhooks": 100,
  "max_oauth_apps": 20
}
```

### Tier Defaults

| Setting | Free | Pro | Enterprise | Partner |
|---------|------|-----|------------|---------|
| `requests_per_minute` | 60 | 300 | 1,000 | 2,000 |
| `webhooks_per_day` | 1,000 | 10,000 | 100,000 | Unlimited |
| `max_api_keys` | 5 | 20 | 50 | 100 |
| `max_webhooks` | 10 | 50 | 100 | Unlimited |
| `max_oauth_apps` | 3 | 10 | 20 | 50 |

### Monitor Quota Usage

```http
GET /api/v1/platform/admin/usage/overview?period=7d
```

Returns top organizations by request volume, rate limit hits, and quota utilization.

---

## 6. API Key Administration

### View Organization Keys

```http
GET /api/v1/admin/organizations/{org_id}/api-keys
Authorization: Bearer {admin_token}
```

### Revoke Key

```http
DELETE /api/v1/admin/organizations/{org_id}/api-keys/{key_id}
```

### Key Audit

```http
GET /api/v1/admin/audit-logs?module=auth&action=api_key&organization_id={org_id}
```

### Security Recommendations

| Policy | Recommendation |
|--------|----------------|
| Key rotation | Rotate every 90 days |
| Scope minimum | Grant least-privilege scopes |
| Expiry | Set `expires_at` for CI/CD keys |
| Monitoring | Alert on keys unused > 30 days then suddenly active |
| Revocation | Immediate on employee departure |

---

## 7. OAuth Administration

### View Registered Applications

```http
GET /api/v1/platform/admin/oauth/apps?organization_id={org_id}
```

### Revoke Application

```http
DELETE /api/v1/platform/admin/oauth/apps/{client_id}
```

Revokes application and all issued tokens immediately.

### Token Audit

```http
GET /api/v1/admin/audit-logs?module=platform&action=oauth_token_granted
```

### Security Monitoring

| Alert | Condition |
|-------|-----------|
| Excessive token grants | > 100/hour per client |
| Failed auth attempts | > 50/hour per client |
| Scope escalation attempt | Requested scopes > registered scopes |

---

## 8. Webhook Administration

### View All Subscriptions (Admin)

```http
GET /api/v1/platform/admin/webhooks?organization_id={org_id}
```

### Force-Disable Failing Subscription

```http
PATCH /api/v1/platform/admin/webhooks/{id}
{ "is_active": false, "reason": "50 failures in 24h" }
```

### DLQ Management

```http
# View DLQ entries
GET /api/v1/platform/admin/webhooks/dlq?status=pending&page=1

# Bulk replay
POST /api/v1/platform/admin/webhooks/dlq/replay
{ "delivery_ids": ["...", "..."] }

# Purge old DLQ entries (> 30 days)
DELETE /api/v1/platform/admin/webhooks/dlq?older_than=30d
```

### Webhook Health Dashboard

Grafana: `infra/monitoring/grafana/dashboards/platform-webhooks.json`

Key panels:
- Delivery success rate (target: > 99%)
- DLQ size
- P99 delivery latency
- Top failing endpoints

---

## 9. Marketplace Moderation

### Review Queue

```http
GET /api/v1/platform/admin/marketplace/reviews?status=in_review
```

### Approve Listing

```http
POST /api/v1/platform/admin/marketplace/reviews/{review_id}/approve
{ "notes": "All checks passed" }
```

### Reject Listing

```http
POST /api/v1/platform/admin/marketplace/reviews/{review_id}/reject
{
  "reason": "SECURITY_ISSUE",
  "notes": "Dependency scan found critical vulnerability in requests 2.28.0"
}
```

### Feature Listing

```http
POST /api/v1/platform/admin/marketplace/listings/{id}/feature
{ "featured": true, "position": 1 }
```

---

## 10. Security Operations

### Incident Response

| Incident | Action |
|----------|--------|
| Compromised API key | Revoke key → audit usage logs → notify org admin |
| Compromised OAuth app | Revoke app + all tokens → notify publisher |
| Webhook SSRF attempt | Block subscription → alert security team |
| Plugin sandbox violation | Disable plugin → quarantine artifact → review |
| Rate limit abuse | Throttle org → investigate → adjust tier |

### Audit Log Queries

```sql
-- Recent platform admin actions
SELECT * FROM audit.audit_logs
WHERE module = 'platform'
  AND created_at > NOW() - INTERVAL '24 hours'
ORDER BY created_at DESC;

-- API key usage for investigation
SELECT * FROM platform.api_usage_logs
WHERE api_key_id = 'suspect-key-uuid'
  AND created_at > NOW() - INTERVAL '7 days'
ORDER BY created_at DESC;
```

### Secret Rotation

| Secret | Rotation Cadence | Procedure |
|--------|------------------|-----------|
| JWT signing keys | Quarterly | JWKS endpoint update, dual-key period |
| Webhook secrets | On compromise | Generate new, 24h grace period |
| OAuth client secrets | On compromise | Regenerate, notify app owner |
| Plugin secrets | On config change | Re-encrypt in `platform.plugin_secrets` |

---

## 11. Troubleshooting

### Common Issues

| Issue | Diagnosis | Resolution |
|-------|-----------|------------|
| Gateway 503 | `docker logs kong` | Restart Kong, check API upstream |
| Webhooks stuck in pending | Check `webhooks` Celery queue | Scale workers, check RabbitMQ |
| OAuth token errors | Check `platform.oauth_tokens` | Verify client_secret, check expiry |
| Plugin install fails | Check MinIO connectivity | Verify artifact URL, signature |
| Rate limits too aggressive | Check `platform.usage_quotas` | Adjust tier or per-org override |
| GraphQL complexity errors | Check query in logs | Increase org limit or optimize query |

### Health Check Commands

```powershell
# Platform subsystem health
curl http://localhost/api/v1/platform/health | jq .

# Celery queue depths
curl http://localhost:5555/api/queues  # Flower (if enabled)

# RabbitMQ queue status
curl -u ali:ali_dev_pass http://localhost:15672/api/queues

# Kong status
curl http://localhost:8080/status
```

### Log Locations

| Component | Location |
|-----------|----------|
| Kong | `docker logs kong` |
| Traefik | `docker logs traefik` |
| Platform API | Application structured logs |
| Webhook workers | `docker logs worker` (filter: `webhooks`) |
| Plugin runtime | `audit.audit_logs` (module=platform) |

---

## Related Documents

- [01-api-gateway-architecture.md](./01-api-gateway-architecture.md)
- [13-security-architecture.md](./13-security-architecture.md)
- [14-observability-strategy.md](./14-observability-strategy.md)
- [20-production-deployment-guide.md](./20-production-deployment-guide.md)