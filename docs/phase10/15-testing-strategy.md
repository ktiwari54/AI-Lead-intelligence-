# 15 — Testing Strategy

**Version 4.0** | Phase 10 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [Test Pyramid](#2-test-pyramid)
3. [Unit Tests](#3-unit-tests)
4. [Integration Tests](#4-integration-tests)
5. [Contract Tests](#5-contract-tests)
6. [Gateway Tests](#6-gateway-tests)
7. [Webhook Tests](#7-webhook-tests)
8. [OAuth Tests](#8-oauth-tests)
9. [Plugin Tests](#9-plugin-tests)
10. [E2E Tests](#10-e2e-tests)
11. [Load Tests](#11-load-tests)
12. [CI Pipeline](#12-ci-pipeline)

---

## 1. Overview

Phase 10 testing extends the platform-wide strategy from Phase 8 (`docs/phase8/15-testing-strategy.md`) and Phase 9 (`docs/phase9/15-testing-strategy.md`) with integration-specific test suites for gateway routing, API contracts, webhooks, OAuth flows, and plugin sandboxing.

**Target coverage:** 85% for `backend/app/platform/`, 80% for SDK packages.

---

## 2. Test Pyramid

```
                    ┌─────────┐
                    │  E2E    │  5%  — Full integration flows
                   ┌┴─────────┴┐
                   │  Contract  │  15% — OpenAPI, GraphQL schema
                  ┌┴───────────┴┐
                  │ Integration  │  30% — Gateway, webhooks, OAuth
                 ┌┴─────────────┴┐
                 │     Unit       │  50% — Services, validators, SDK
                 └───────────────┘
```

---

## 3. Unit Tests

### Test Locations

| Module | Path | Focus |
|--------|------|-------|
| Webhook service | `tests/platform/test_webhook_service.py` | Subscription CRUD, payload building |
| Signature | `tests/platform/test_webhook_signature.py` | HMAC generation/verification |
| OAuth service | `tests/platform/test_oauth_service.py` | Token generation, scope validation |
| Plugin runtime | `tests/platform/test_plugin_runtime.py` | Hook dispatch, permission checks |
| Usage service | `tests/platform/test_usage_service.py` | Quota checks, aggregation |
| API key scopes | `tests/platform/test_scope_enforcement.py` | Scope-to-endpoint mapping |
| Python SDK | `backend/sdk/ali/tests/` | Client, pagination, error handling |
| Connector SDK | `backend/sdk/connectors/tests/` | BaseConnector, schema mapping |

### Example: Webhook Signature

```python
# tests/platform/test_webhook_signature.py

import pytest
from backend.app.platform.webhooks.signature import sign_payload, verify_signature

def test_sign_and_verify_roundtrip():
    secret = "whsec_test_secret_key_32chars_long!"
    payload = b'{"type":"contact.created","data":{}}'
    timestamp = "1719662400"

    signature = sign_payload(payload, timestamp, secret)
    assert verify_signature(payload, signature, timestamp, secret)

def test_reject_tampered_payload():
    secret = "whsec_test_secret_key_32chars_long!"
    payload = b'{"type":"contact.created"}'
    timestamp = "1719662400"
    signature = sign_payload(payload, timestamp, secret)

    tampered = b'{"type":"contact.updated"}'
    assert not verify_signature(tampered, signature, timestamp, secret)

def test_reject_stale_timestamp():
    secret = "whsec_test_secret_key_32chars_long!"
    payload = b'{"type":"contact.created"}'
    stale_timestamp = "1600000000"  # years ago
    signature = sign_payload(payload, stale_timestamp, secret)
    assert not verify_signature(payload, signature, stale_timestamp, secret)
```

### Example: Scope Enforcement

```python
@pytest.mark.parametrize("scopes,endpoint,expected", [
    (["crm:read"], "GET /api/v1/crm/contacts", True),
    (["contacts:read"], "GET /api/v1/crm/contacts", True),
    (["crm:read"], "POST /api/v1/crm/contacts", False),
    (["webhooks:manage"], "POST /api/v1/platform/webhooks", True),
    (["crm:read"], "POST /api/v1/platform/webhooks", False),
])
def test_scope_enforcement(scopes, endpoint, expected):
    assert check_scope(scopes, endpoint) == expected
```

---

## 4. Integration Tests

### Test Infrastructure

```python
# tests/conftest.py (platform fixtures)

@pytest.fixture
async def platform_client(test_app, test_org, admin_user):
    """Authenticated client with integration_platform_v4 enabled."""
    await enable_feature_flag(test_org.id, "integration_platform_v4")
    token = await create_test_token(admin_user)
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        client.headers["Authorization"] = f"Bearer {token}"
        yield client

@pytest.fixture
async def api_key_client(test_app, test_org, test_user):
    """Client authenticated with API key."""
    raw_key, api_key = await create_test_api_key(
        test_user, test_org, scopes=["crm:read", "contacts:read"]
    )
    async with AsyncClient(app=test_app, base_url="http://test") as client:
        client.headers["Authorization"] = f"ApiKey {raw_key}"
        yield client, raw_key
```

### Integration Test Cases

| Test | Validates |
|------|-----------|
| `test_create_webhook_subscription` | CRUD + secret generation |
| `test_webhook_delivery_end_to_end` | Event → match → deliver → verify |
| `test_oauth_authorization_code_flow` | Full OAuth flow with PKCE |
| `test_oauth_client_credentials` | M2M token grant |
| `test_api_key_scope_rejection` | 422 on insufficient scope |
| `test_rate_limit_enforcement` | 429 after quota exceeded |
| `test_tenant_isolation` | Cross-org data inaccessible |
| `test_plugin_install_and_invoke` | Install → configure → test hook |
| `test_usage_tracking` | API call logged in usage_logs |

---

## 5. Contract Tests

### OpenAPI Contract Validation

```python
# tests/contract/test_openapi_spec.py

import schemathesis

schema = schemathesis.from_uri("http://localhost:8000/api/v1/openapi.json")

@schema.parametrize()
def test_api_contract(case):
    case.call_and_validate()
```

### Breaking Change Detection

```bash
# CI: Compare OpenAPI spec against baseline
oasdiff breaking openapi-baseline.json openapi-current.json
```

### GraphQL Schema Validation

```python
# tests/contract/test_graphql_schema.py

def test_graphql_schema_matches_snapshot():
    schema_sdl = export_graphql_schema()
    assert schema_sdl == load_snapshot("graphql-schema-v1.graphql")
```

### SDK Contract Tests

```python
# Verify SDK models match OpenAPI schemas
def test_contact_model_matches_openapi():
    openapi_contact = load_openapi_schema("Contact")
    sdk_fields = Contact.model_fields.keys()
    api_fields = set(openapi_contact["properties"].keys())
    assert api_fields.issubset(sdk_fields)
```

---

## 6. Gateway Tests

### Kong Configuration Validation

```python
# tests/gateway/test_kong_config.py

def test_kong_config_valid():
    config = yaml.safe_load(open("infra/gateway/kong/kong.yml"))
    assert config["_format_version"] == "3.0"
    assert len(config["services"]) >= 1
    for service in config["services"]:
        assert "plugins" in service
        plugin_names = [p["name"] for p in service["plugins"]]
        assert "rate-limiting" in plugin_names
        assert "cors" in plugin_names
```

### Gateway Routing Tests (Docker)

```python
# tests/gateway/test_routing.py
# Requires: docker compose --profile gateway up

@pytest.mark.gateway
async def test_traefik_routes_api_to_kong():
    resp = await httpx.get("http://localhost/api/v1/health")
    assert resp.status_code == 200
    assert "X-Request-Id" in resp.headers

@pytest.mark.gateway
async def test_kong_rate_limiting():
    for _ in range(301):
        resp = await httpx.get("http://localhost/api/v1/health")
    assert resp.status_code == 429
```

---

## 7. Webhook Tests

### Mock Webhook Server

```python
# tests/platform/webhook_mock_server.py

from aiohttp import web

received_payloads = []

async def webhook_handler(request):
    body = await request.read()
    signature = request.headers.get("X-Webhook-Signature")
    timestamp = request.headers.get("X-Webhook-Timestamp")

    assert verify_signature(body, signature, timestamp, TEST_SECRET)
    received_payloads.append(json.loads(body))
    return web.Response(status=200)

@pytest.fixture
async def webhook_server():
    app = web.Application()
    app.router.add_post("/hooks/test", webhook_handler)
    runner = web.AppRunner(app)
    await runner.setup()
    site = web.TCPSite(runner, "localhost", 9876)
    await site.start()
    yield "http://localhost:9876/hooks/test"
    await runner.cleanup()
```

### Delivery Test

```python
async def test_webhook_delivery_with_retry(platform_client, webhook_server):
    sub = await platform_client.post("/api/v1/platform/webhooks", json={
        "url": webhook_server,
        "events": ["contact.created"],
    })
    # Trigger event
    await create_contact(test_org)
    await wait_for_delivery(sub.data["id"], timeout=30)
    assert len(received_payloads) == 1
    assert received_payloads[0]["type"] == "contact.created"
```

---

## 8. OAuth Tests

```python
async def test_authorization_code_flow_with_pkce(platform_client):
    # Register app
    app = await platform_client.post("/api/v1/platform/oauth/apps", json={
        "name": "Test App",
        "redirect_uris": ["http://localhost:9999/callback"],
        "scopes": ["crm:read"],
        "grant_types": ["authorization_code"],
    })

    # Generate PKCE challenge
    verifier, challenge = generate_pkce()

    # Authorize (simulated user consent)
    auth_resp = await platform_client.get(
        f"/api/v1/oauth/authorize?response_type=code"
        f"&client_id={app.data['client_id']}"
        f"&redirect_uri=http://localhost:9999/callback"
        f"&scope=crm:read"
        f"&code_challenge={challenge}"
        f"&code_challenge_method=S256"
    )
    code = extract_code_from_redirect(auth_resp)

    # Exchange code for token
    token_resp = await httpx.post("/api/v1/oauth/token", data={
        "grant_type": "authorization_code",
        "code": code,
        "client_id": app.data["client_id"],
        "client_secret": app.data["client_secret"],
        "redirect_uri": "http://localhost:9999/callback",
        "code_verifier": verifier,
    })
    assert token_resp.status_code == 200
    assert "access_token" in token_resp.json()
```

---

## 9. Plugin Tests

```python
async def test_plugin_install_and_test_connection(platform_client):
    # Install from marketplace
    install = await platform_client.post("/api/v1/platform/plugins/install", json={
        "plugin_id": "conn:hubspot-test",
        "version": "1.0.0",
        "config": {"api_key": "test_key"},
    })
    assert install.data["status"] == "active"

    # Test connection hook
    test = await platform_client.post(
        f"/api/v1/platform/plugins/{install.data['id']}/test"
    )
    assert test.data["success"] is True

async def test_plugin_permission_enforcement(platform_client):
    # Plugin requesting crm:write but key only has crm:read
    with pytest.raises(PluginPermissionError):
        await invoke_hook("connector.sync", "conn:test", {}, limited_context)
```

---

## 10. E2E Tests

### Developer Journey E2E

```python
# tests/e2e/test_developer_journey.py

async def test_first_api_call_journey():
    """Developer: signup → create key → list contacts → create webhook."""
    # 1. Login
    token = await login("developer@test.com", "password")

    # 2. Create API key
    key_resp = await api_post("/api/v1/users/me/api-keys", token=token, json={
        "name": "E2E Test Key",
        "scopes": ["crm:read", "contacts:read", "webhooks:manage"],
    })
    api_key = key_resp["data"]["key"]

    # 3. List contacts via API key
    contacts = await api_get("/api/v1/crm/contacts", api_key=api_key)
    assert contacts["success"] is True

    # 4. Create webhook
    webhook = await api_post("/api/v1/platform/webhooks", api_key=api_key, json={
        "url": "https://webhook.site/test",
        "events": ["contact.created"],
    })
    assert webhook["data"]["secret"].startswith("whsec_")
```

---

## 11. Load Tests

### k6 Scenarios

```javascript
// tests/load/api-gateway.js
import http from 'k6/http';
import { check, sleep } from 'k6';

export const options = {
  stages: [
    { duration: '2m', target: 100 },
    { duration: '5m', target: 500 },
    { duration: '2m', target: 0 },
  ],
  thresholds: {
    http_req_duration: ['p(99)<500'],
    http_req_failed: ['rate<0.01'],
  },
};

export default function () {
  const res = http.get('http://localhost/api/v1/crm/contacts', {
    headers: { Authorization: `ApiKey ${__ENV.API_KEY}` },
  });
  check(res, { 'status is 200': (r) => r.status === 200 });
  sleep(0.1);
}
```

### Load Test Targets

| Scenario | RPS Target | Duration | Pass Criteria |
|----------|-----------|----------|---------------|
| API read (contacts) | 500 | 10 min | p99 < 500 ms, error < 1% |
| Webhook dispatch | 200 events/s | 5 min | delivery < 5 s p99 |
| OAuth token grant | 50 | 5 min | p99 < 200 ms |
| GraphQL queries | 100 | 5 min | p99 < 1 s |

---

## 12. CI Pipeline

```yaml
# .github/workflows/platform-tests.yml
name: Phase 10 Platform Tests

on:
  push:
    paths: ['backend/app/platform/**', 'backend/sdk/**', 'infra/gateway/**']

jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - run: pytest tests/platform/ backend/sdk/ali/tests/ -v --cov=backend/app/platform

  contract:
    runs-on: ubuntu-latest
    services:
      postgres: { image: postgres:16 }
      redis: { image: redis:7 }
    steps:
      - run: pytest tests/contract/ -v
      - run: oasdiff breaking openapi-baseline.json <(curl -s localhost:8000/api/v1/openapi.json)

  integration:
    runs-on: ubuntu-latest
    services:
      postgres: { image: postgres:16 }
      redis: { image: redis:7 }
      rabbitmq: { image: rabbitmq:3.13-alpine }
    steps:
      - run: pytest tests/platform/ -v -m integration

  gateway:
    runs-on: ubuntu-latest
    steps:
      - run: docker compose -f docker-compose.yml -f docker-compose.gateway.yml --profile gateway up -d
      - run: pytest tests/gateway/ -v -m gateway

  load:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    steps:
      - run: k6 run tests/load/api-gateway.js
```

---

## Related Documents

- [02-rest-api-specification.md](./02-rest-api-specification.md)
- [04-webhook-platform-design.md](./04-webhook-platform-design.md)
- [16-api-governance-guide.md](./16-api-governance-guide.md)