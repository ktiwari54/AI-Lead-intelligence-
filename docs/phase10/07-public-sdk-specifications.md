# 07 — Public SDK Specifications

**Version 4.0** | Phase 10 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [SDK Design Principles](#2-sdk-design-principles)
3. [Python SDK](#3-python-sdk)
4. [TypeScript SDK](#4-typescript-sdk)
5. [CLI Tool](#5-cli-tool)
6. [Authentication](#6-authentication)
7. [Error Handling](#7-error-handling)
8. [Pagination](#8-pagination)
9. [Idempotency](#9-idempotency)
10. [Publishing & Versioning](#10-publishing--versioning)

---

## 1. Overview

Public SDKs provide **typed, ergonomic clients** for all platform APIs. They wrap REST endpoints with auto-retry, pagination helpers, and webhook verification utilities.

| SDK | Package | Path |
|-----|---------|------|
| Python | `ali-sdk` | `backend/sdk/ali/` |
| TypeScript | `@ali/sdk` | `frontend/packages/@ali/sdk/` |
| CLI | `ali` | `backend/sdk/ali/cli/` |

All SDKs target API version `v1` with semver independent of platform version.

---

## 2. SDK Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Typed** | Pydantic models (Python), Zod schemas (TypeScript) |
| **Gateway-aware** | Default base URL through Traefik/Kong |
| **Retry-safe** | Exponential backoff on 429/503; respect `Retry-After` |
| **Idempotent** | Auto-generate `Idempotency-Key` for write ops |
| **Observable** | Pass `X-Request-Id` / `X-Correlation-Id` |
| **Minimal deps** | `httpx` (Python), native `fetch` (TypeScript) |

---

## 3. Python SDK

### Installation

```bash
pip install ali-sdk
# Monorepo development:
pip install -e backend/sdk/ali
```

### Quick Start

```python
from ali import Client

client = Client(
    api_key="ali_live_a1b2c3d4e5f6g7h8i9j0k1l2m3n4o5p6",
    base_url="https://api.example.com/api/v1",
)

# List contacts
contacts = client.crm.contacts.list(search="acme", per_page=50)
for contact in contacts:
    print(contact.email, contact.lead_score)

# Create webhook subscription
webhook = client.platform.webhooks.create(
    url="https://myapp.example.com/hooks",
    events=["contact.created", "lead.scored"],
)
print(f"Secret: {webhook.secret}")  # shown once

# Execute workflow
execution = client.workflows.execute(
    workflow_id="019f0c1f-...",
    entity_type="contact",
    entity_id="019f0c1f-...",
    async_mode=True,
)
status = client.workflows.executions.wait(execution.id, timeout=120)
```

### Client Architecture

```python
# backend/sdk/ali/client.py

class Client:
    def __init__(
        self,
        api_key: str | None = None,
        access_token: str | None = None,
        base_url: str = "http://localhost/api/v1",
        timeout: float = 30.0,
        max_retries: int = 3,
    ):
        self._http = HttpClient(base_url, api_key, access_token, timeout, max_retries)
        self.crm = CRMResource(self._http)
        self.search = SearchResource(self._http)
        self.workflows = WorkflowsResource(self._http)
        self.platform = PlatformResource(self._http)
        self.analytics = AnalyticsResource(self._http)
```

### Resource Modules

| Module | Class | Key Methods |
|--------|-------|-------------|
| `crm.contacts` | `ContactsResource` | `list`, `get`, `create`, `update`, `delete` |
| `crm.companies` | `CompaniesResource` | `list`, `get`, `create`, `update` |
| `crm.deals` | `DealsResource` | `list`, `get`, `create`, `update` |
| `search` | `SearchResource` | `execute`, `get_results` |
| `workflows` | `WorkflowsResource` | `list`, `get`, `execute`, `executions` |
| `platform.webhooks` | `WebhooksResource` | `create`, `list`, `get`, `update`, `delete`, `test` |
| `platform.oauth` | `OAuthResource` | `create_app`, `list_apps` |
| `platform.usage` | `UsageResource` | `get`, `by_key` |
| `analytics` | `AnalyticsResource` | `dashboard`, `lead_velocity` |

### Webhook Verification Helper

```python
from ali.webhooks import verify_signature

@app.post("/hooks/ali")
async def handle_webhook(request: Request):
    body = await request.body()
    signature = request.headers["X-Webhook-Signature"]
    timestamp = request.headers["X-Webhook-Timestamp"]

    if not verify_signature(body, signature, timestamp, WEBHOOK_SECRET):
        raise HTTPException(401)

    event = json.loads(body)
    if event["type"] == "contact.created":
        process_contact(event["data"])
    return {"status": "ok"}
```

---

## 4. TypeScript SDK

### Installation

```bash
npm install @ali/sdk
# Monorepo:
npm install -w @ali/sdk
```

### Quick Start

```typescript
import { Client } from '@ali/sdk';

const client = new Client({
  apiKey: process.env.ALI_API_KEY,
  baseUrl: 'https://api.example.com/api/v1',
});

// List contacts with auto-pagination
const contacts = await client.crm.contacts.listAll({ search: 'acme' });

// Create webhook
const webhook = await client.platform.webhooks.create({
  url: 'https://myapp.example.com/hooks',
  events: ['contact.created', 'lead.scored'],
});

// Workflow execution with polling
const execution = await client.workflows.execute(workflowId, {
  entityType: 'contact',
  entityId: contactId,
  asyncMode: true,
});
const result = await client.workflows.executions.waitFor(execution.id, {
  timeoutMs: 120_000,
});
```

### Type Definitions

```typescript
// frontend/packages/@ali/sdk/src/types/contact.ts

export interface Contact {
  id: string;
  firstName: string | null;
  lastName: string | null;
  email: string | null;
  phone: string | null;
  title: string | null;
  leadScore: number | null;
  companyId: string | null;
  tags: Tag[];
  createdAt: string;
  updatedAt: string;
}

export interface ContactListParams {
  search?: string;
  tags?: string[];
  minScore?: number;
  updatedSince?: string;
  page?: number;
  perPage?: number;
}

export interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  perPage: number;
  pages: number;
}
```

### React Hook (Optional)

```typescript
import { useAliClient, useContacts } from '@ali/sdk/react';

function ContactList() {
  const client = useAliClient();
  const { data, isLoading } = useContacts(client, { search: 'acme' });

  if (isLoading) return <Spinner />;
  return data.map(c => <ContactCard key={c.id} contact={c} />);
}
```

---

## 5. CLI Tool

### Installation

```bash
pip install ali-sdk[cli]
```

### Commands

```bash
# Configure credentials
ali config set --api-key ali_live_... --base-url https://api.example.com/api/v1

# Test connection
ali ping

# List contacts
ali crm contacts list --search acme --format table

# Create webhook
ali webhooks create \
  --url https://myapp.example.com/hooks \
  --events contact.created,lead.scored

# Test webhook delivery
ali webhooks test <webhook-id> --event contact.created

# View API usage
ali usage --period 7d

# Verify incoming webhook (local testing)
ali webhooks verify --secret whsec_... --payload payload.json

# Generate API key (requires JWT auth)
ali keys create --name "CI Pipeline" --scopes crm:read,contacts:read
```

### Output Formats

| Flag | Format |
|------|--------|
| `--format json` | JSON (default) |
| `--format table` | ASCII table |
| `--format csv` | CSV export |

---

## 6. Authentication

### Priority Order

1. Explicit `api_key` parameter
2. Explicit `access_token` parameter
3. Environment variable `ALI_API_KEY`
4. Environment variable `ALI_ACCESS_TOKEN`
5. Config file `~/.ali/config.json`

### Header Format

```python
# API Key
headers["Authorization"] = f"ApiKey {api_key}"

# JWT / OAuth
headers["Authorization"] = f"Bearer {access_token}"
```

### OAuth Helper (Python)

```python
from ali.oauth import OAuthFlow

flow = OAuthFlow(
    client_id="ali_app_...",
    client_secret="ali_sec_...",
    redirect_uri="http://localhost:8080/callback",
    scopes=["crm:read", "contacts:read"],
)

# Authorization Code flow
auth_url = flow.get_authorization_url()
# ... user visits auth_url ...
token = flow.exchange_code(code="auth_code_here")
client = Client(access_token=token.access_token)
```

---

## 7. Error Handling

### Exception Hierarchy (Python)

```python
class AliError(Exception):
    """Base SDK error."""

class AliAPIError(AliError):
    def __init__(self, status_code: int, code: str, message: str, data: dict = None):
        self.status_code = status_code
        self.code = code
        self.message = message
        self.data = data or {}

class RateLimitError(AliAPIError): ...
class AuthenticationError(AliAPIError): ...
class NotFoundError(AliAPIError): ...
class ValidationError(AliAPIError): ...
class ScopeError(AliAPIError): ...
```

### Usage

```python
from ali import Client
from ali.exceptions import RateLimitError, NotFoundError

client = Client(api_key="...")

try:
    contact = client.crm.contacts.get("nonexistent-id")
except NotFoundError:
    print("Contact not found")
except RateLimitError as e:
    print(f"Rate limited, retry after {e.data.get('retry_after_seconds')}s")
```

### TypeScript

```typescript
import { AliAPIError, isRateLimitError } from '@ali/sdk';

try {
  await client.crm.contacts.get('nonexistent-id');
} catch (error) {
  if (error instanceof AliAPIError && error.code === 'NOT_FOUND') {
    console.log('Contact not found');
  }
  if (isRateLimitError(error)) {
    await sleep(error.retryAfterSeconds * 1000);
  }
}
```

---

## 8. Pagination

### Auto-Pagination (Python)

```python
# Iterates all pages automatically
for contact in client.crm.contacts.iter(search="acme"):
    process(contact)

# Manual pagination
page = client.crm.contacts.list(page=1, per_page=100)
while page.page < page.pages:
    page = client.crm.contacts.list(page=page.page + 1, per_page=100)
    for contact in page.data:
        process(contact)
```

### TypeScript

```typescript
// Async iterator
for await (const contact of client.crm.contacts.iterate({ search: 'acme' })) {
  process(contact);
}

// Manual
let page = 1;
let result = await client.crm.contacts.list({ page, perPage: 100 });
while (page < result.pages) {
  result.data.forEach(process);
  page++;
  result = await client.crm.contacts.list({ page, perPage: 100 });
}
```

---

## 9. Idempotency

Write operations automatically include `Idempotency-Key` unless overridden:

```python
# Auto-generated key
contact = client.crm.contacts.create(first_name="Jane", email="jane@acme.com")

# Explicit key (safe retry)
contact = client.crm.contacts.create(
    first_name="Jane",
    email="jane@acme.com",
    idempotency_key="create-jane-acme-001",
)
```

Duplicate requests with the same key return the original response (HTTP 200, not 409).

---

## 10. Publishing & Versioning

### Version Alignment

| Component | Versioning |
|-----------|------------|
| Platform API | URL path (`/api/v1/`) |
| Python SDK | PyPI semver (`ali-sdk==1.2.0`) |
| TypeScript SDK | npm semver (`@ali/sdk@1.2.0`) |
| CLI | Bundled with Python SDK |

### Release Cadence

- SDK patch: bug fixes, no API changes
- SDK minor: new endpoints, backward-compatible
- SDK major: breaking client API (rare; platform API version handles breaking server changes)

### CI Publishing

```yaml
# .github/workflows/sdk-release.yml
on:
  push:
    tags: ['sdk-v*']
jobs:
  publish-python:
    runs-on: ubuntu-latest
    steps:
      - run: pip build backend/sdk/ali && twine upload dist/*
  publish-typescript:
    runs-on: ubuntu-latest
    steps:
      - run: npm publish -w @ali/sdk
```

---

## Related Documents

- [02-rest-api-specification.md](./02-rest-api-specification.md)
- [09-developer-portal-design.md](./09-developer-portal-design.md)
- [17-developer-experience-guide.md](./17-developer-experience-guide.md)