# 17 — Developer Experience Guide

**Version 4.0** | Phase 10 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [10-Minute Quickstart](#2-10-minute-quickstart)
3. [Authentication Guide](#3-authentication-guide)
4. [Making API Calls](#4-making-api-calls)
5. [Webhook Integration](#5-webhook-integration)
6. [OAuth Integration](#6-oauth-integration)
7. [SDK Usage Patterns](#7-sdk-usage-patterns)
8. [Error Handling Best Practices](#8-error-handling-best-practices)
9. [Sandbox Development](#9-sandbox-development)
10. [Troubleshooting](#10-troubleshooting)

---

## 1. Overview

This guide helps developers integrate with the AI Lead Intelligence Platform efficiently. The CTO mandate is clear: **from signup to first successful API call in under 10 minutes**.

**Developer Portal:** http://localhost:3000/developers  
**API Base URL:** http://localhost/api/v1 (via gateway)

---

## 2. 10-Minute Quickstart

### Step 1: Get Credentials (2 min)

```powershell
# Login to get JWT
$response = Invoke-RestMethod -Uri "http://localhost/api/v1/auth/login" `
  -Method POST -ContentType "application/json" `
  -Body '{"email":"dev@example.com","password":"your_password"}'
$TOKEN = $response.data.access_token

# Create API key
$key = Invoke-RestMethod -Uri "http://localhost/api/v1/users/me/api-keys" `
  -Method POST -Headers @{Authorization="Bearer $TOKEN"} `
  -ContentType "application/json" `
  -Body '{"name":"Quickstart Key","scopes":["crm:read","contacts:read"]}'
$API_KEY = $key.data.key
Write-Host "API Key: $API_KEY"
# Save this key — it won't be shown again!
```

### Step 2: Make Your First Call (1 min)

```powershell
curl http://localhost/api/v1/crm/contacts `
  -H "Authorization: ApiKey $API_KEY"
```

### Step 3: Install SDK (2 min)

```bash
pip install ali-sdk
```

```python
from ali import Client

client = Client(api_key="ali_live_...", base_url="http://localhost/api/v1")
contacts = client.crm.contacts.list(per_page=5)
for c in contacts.data:
    print(f"{c.first_name} {c.last_name} — score: {c.lead_score}")
```

### Step 4: Set Up a Webhook (5 min)

```python
webhook = client.platform.webhooks.create(
    url="https://your-server.com/hooks/ali",
    events=["contact.created", "lead.scored"],
)
print(f"Webhook secret: {webhook.secret}")
```

**Done!** You're receiving real-time events.

---

## 3. Authentication Guide

### Choose Your Auth Method

| Method | Best For | Setup Time |
|--------|----------|------------|
| **API Key** | Server-to-server, scripts, CI/CD | 1 minute |
| **JWT** | User-facing apps, developer portal | Login required |
| **OAuth 2.0** | Third-party apps acting on behalf of users | 15 minutes |

### API Key Scopes

Request only the scopes you need:

| Scope | Access |
|-------|--------|
| `crm:read` | Read companies, deals, pipelines |
| `crm:write` | Create/update companies, deals |
| `contacts:read` | Read contacts |
| `contacts:write` | Create/update contacts |
| `search:write` | Execute searches |
| `workflows:execute` | Trigger workflows |
| `webhooks:manage` | Manage webhook subscriptions |
| `analytics:read` | Read analytics data |
| `platform:read` | Read usage, capabilities |

### Header Format

```bash
# API Key
curl -H "Authorization: ApiKey ali_live_a1b2c3d4..." http://localhost/api/v1/crm/contacts

# JWT
curl -H "Authorization: Bearer eyJhbGciOiJSUzI1NiIs..." http://localhost/api/v1/crm/contacts
```

---

## 4. Making API Calls

### Pagination

```python
# Auto-pagination (recommended)
for contact in client.crm.contacts.iter(per_page=100):
    process(contact)

# Manual pagination
page = 1
while True:
    result = client.crm.contacts.list(page=page, per_page=100)
    for contact in result.data:
        process(contact)
    if page >= result.pages:
        break
    page += 1
```

### Filtering & Delta Sync

```python
# Get contacts updated in the last 24 hours
from datetime import datetime, timedelta

since = (datetime.utcnow() - timedelta(hours=24)).isoformat() + "Z"
contacts = client.crm.contacts.list(updated_since=since)
```

### Idempotent Writes

```python
contact = client.crm.contacts.create(
    first_name="Jane",
    last_name="Smith",
    email="jane@acme.com",
    idempotency_key="create-jane-2026-06-29",
)
# Safe to retry — same key returns original response
```

### Rate Limits

| Tier | Limit | Header |
|------|-------|--------|
| Free | 60/min | `X-RateLimit-Limit: 60` |
| Pro | 300/min | `X-RateLimit-Limit: 300` |

When rate limited (HTTP 429), wait for `Retry-After` seconds before retrying.

---

## 5. Webhook Integration

### Setup

```python
webhook = client.platform.webhooks.create(
    url="https://your-server.com/hooks/ali",
    events=["contact.created", "lead.scored", "workflow.executed"],
)
WEBHOOK_SECRET = webhook.secret
```

### Verify Signatures (Python)

```python
from ali.webhooks import verify_signature

@app.post("/hooks/ali")
async def handle_webhook(request: Request):
    body = await request.body()
    if not verify_signature(
        body,
        request.headers["X-Webhook-Signature"],
        request.headers["X-Webhook-Timestamp"],
        WEBHOOK_SECRET,
    ):
        return Response(status_code=401)

    event = json.loads(body)
    match event["type"]:
        case "contact.created":
            await sync_contact(event["data"])
        case "lead.scored":
            if event["data"]["score"] >= 80:
                await alert_sales(event["data"])
    return {"status": "ok"}
```

### Verify Signatures (Node.js)

```typescript
import { verifyWebhookSignature } from '@ali/sdk';

app.post('/hooks/ali', express.raw({ type: 'application/json' }), (req, res) => {
  const valid = verifyWebhookSignature(
    req.body,
    req.headers['x-webhook-signature'] as string,
    req.headers['x-webhook-timestamp'] as string,
    process.env.WEBHOOK_SECRET!,
  );
  if (!valid) return res.status(401).send('Invalid signature');

  const event = JSON.parse(req.body);
  // Handle event...
  res.json({ status: 'ok' });
});
```

### Best Practices

| Practice | Why |
|----------|-----|
| Return 200 quickly | Process async; platform retries on non-2xx |
| Verify signatures | Prevent spoofed events |
| Handle duplicates | At-least-once delivery; use `event.id` for dedup |
| Log event IDs | Correlate with delivery log in developer portal |
| Test with `ali webhooks test` | Verify endpoint before going live |

---

## 6. OAuth Integration

### Authorization Code Flow (User-Delegated)

```python
from ali.oauth import OAuthFlow

flow = OAuthFlow(
    client_id="ali_app_...",
    client_secret="ali_sec_...",
    redirect_uri="http://localhost:8080/callback",
    scopes=["crm:read", "contacts:read"],
    base_url="http://localhost/api/v1",
)

# Step 1: Redirect user to authorization URL
print(flow.get_authorization_url(state="random_state"))

# Step 2: Exchange authorization code (in your callback handler)
token = flow.exchange_code(code="auth_code_from_callback")
client = Client(access_token=token.access_token)
contacts = client.crm.contacts.list()
```

### Client Credentials Flow (Server-to-Server)

```python
import httpx

resp = httpx.post("http://localhost/api/v1/oauth/token", data={
    "grant_type": "client_credentials",
    "client_id": "ali_app_...",
    "client_secret": "ali_sec_...",
    "scope": "crm:read",
})
token = resp.json()["access_token"]
client = Client(access_token=token)
```

---

## 7. SDK Usage Patterns

### Error Handling with Retry

```python
from ali import Client
from ali.exceptions import RateLimitError
import time

client = Client(api_key="...", max_retries=3)

def fetch_with_retry():
    try:
        return client.crm.contacts.list(per_page=100)
    except RateLimitError as e:
        time.sleep(e.data.get("retry_after_seconds", 60))
        return fetch_with_retry()
```

### Batch Processing

```python
# Process contacts in batches
for contact in client.crm.contacts.iter(per_page=100):
    try:
        score = calculate_custom_score(contact)
        client.crm.contacts.update(
            contact.id,
            custom_fields={"custom_score": score},
        )
    except Exception as e:
        logger.error(f"Failed to process {contact.id}: {e}")
        continue
```

### Webhook + API Pattern

```python
# Real-time sync: webhook triggers API fetch for full data
@client.events.on("contact.created")
async def on_contact_created(event):
    contact = client.crm.contacts.get(event.data["contact_id"])
    await external_crm.create_contact(contact)
```

---

## 8. Error Handling Best Practices

### Error Response Structure

```json
{
  "success": false,
  "message": "Insufficient scope for this endpoint",
  "data": {
    "code": "SCOPE_INSUFFICIENT",
    "required_scopes": ["crm:write"],
    "provided_scopes": ["crm:read"]
  }
}
```

### Common Errors

| Code | HTTP | Action |
|------|------|--------|
| `UNAUTHORIZED` | 401 | Check API key / token |
| `SCOPE_INSUFFICIENT` | 422 | Add required scope to API key |
| `RATE_LIMIT_EXCEEDED` | 429 | Wait `retry_after_seconds` |
| `VALIDATION_ERROR` | 400 | Fix request body per error details |
| `FEATURE_NOT_ENABLED` | 403 | Contact admin to enable `integration_platform_v4` |
| `NOT_FOUND` | 404 | Verify resource ID and organization |

### Retry Strategy

| Status | Retry? | Backoff |
|--------|--------|---------|
| 400 | No | Fix request |
| 401 | No | Refresh credentials |
| 403 | No | Check permissions |
| 404 | No | Check resource ID |
| 409 | No | Check idempotency key |
| 429 | Yes | `Retry-After` header |
| 500 | Yes | Exponential: 1s, 2s, 4s |
| 503 | Yes | Exponential: 2s, 4s, 8s |

---

## 9. Sandbox Development

### Sandbox vs Production

| Feature | Sandbox | Production |
|---------|---------|------------|
| API key prefix | `ali_test_` | `ali_live_` |
| Webhook URLs | HTTP allowed | HTTPS required |
| Rate limit | 60/min | Per plan tier |
| Data | Seeded demo data | Real data |
| OAuth redirect | `localhost` allowed | Registered URIs only |

### Local Webhook Testing

```bash
# Option 1: ngrok
ngrok http 3000
ali webhooks create --url https://abc123.ngrok.io/hooks/ali --events contact.created

# Option 2: webhook.site
ali webhooks create --url https://webhook.site/unique-id --events contact.created

# Option 3: CLI test (no server needed)
ali webhooks test <webhook-id> --event contact.created
```

### Postman Collection

Import from developer portal: `/developers/docs` → **Postman Collection** download.

Pre-configured with:
- Environment variables (`API_KEY`, `BASE_URL`)
- Auth helpers
- Example requests for all major endpoints

---

## 10. Troubleshooting

### Diagnostic Checklist

| Symptom | Check |
|---------|-------|
| 401 Unauthorized | Key active? Correct header format? Not expired? |
| 403 Forbidden | Feature flag enabled? Sufficient role? |
| 422 Scope error | API key has required scope? |
| 429 Rate limited | Check `X-RateLimit-Reset` header |
| Webhook not received | Subscription active? URL reachable? Check delivery log |
| Signature verification fails | Using raw body (not parsed JSON)? Clock sync? |
| Slow responses | Using gateway URL? Check `X-RateLimit-Remaining` |

### Debug Headers

```bash
curl -v http://localhost/api/v1/crm/contacts \
  -H "Authorization: ApiKey ali_live_..." \
  2>&1 | grep -E "X-Request-Id|X-RateLimit|X-Deprecation"
```

### Get Help

| Channel | URL |
|---------|-----|
| Documentation | `/developers/docs` |
| API Explorer | `/developers/explorer` |
| Delivery logs | `/developers/webhooks/{id}` |
| Usage analytics | `/developers/usage` |
| Support | support@example.com |

---

## Related Documents

- [02-rest-api-specification.md](./02-rest-api-specification.md)
- [07-public-sdk-specifications.md](./07-public-sdk-specifications.md)
- [09-developer-portal-design.md](./09-developer-portal-design.md)
- [19-integration-playbook.md](./19-integration-playbook.md)