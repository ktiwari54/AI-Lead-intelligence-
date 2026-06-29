# Phase 8 — Developer SDK

**Version 3.0** | Workflow Automation Platform

---

## Overview

The Workflow SDK provides typed clients for creating, publishing, executing, and monitoring workflows from application code or CI pipelines.

## Python SDK

```python
from ali_workflows import WorkflowClient

client = WorkflowClient(
    base_url="https://api.example.com/api/v1",
    api_key="ali_...",
)

# Create from template
wf = client.workflows.create_from_template(
    slug="lead-qualification",
    name="My Lead Qualification",
)

# Execute manually
execution = client.workflows.execute(
    wf.id,
    entity_type="contact",
    entity_id="019f0c1f-...",
    async_mode=True,
)

# Poll status
status = client.executions.get(execution.execution_id)
```

Install (monorepo):

```bash
pip install -e backend/sdk/workflows
```

## TypeScript SDK

```typescript
import { WorkflowClient } from '@ali/workflows';

const client = new WorkflowClient({
  baseUrl: process.env.NEXT_PUBLIC_API_URL,
  getToken: () => localStorage.getItem('access_token'),
});

const workflows = await client.list({ is_active: true });
const execution = await client.execute(workflowId, {
  entity_type: 'company',
  entity_id: companyId,
});
```

## Webhook Trigger SDK

```bash
curl -X POST https://api.example.com/api/v1/workflows/hooks/{hook_id} \
  -H "X-Webhook-Secret: whsec_..." \
  -d '{"event":"custom","payload":{"score":85}}'
```

## Event Subscription

```python
@client.events.on("company.created")
def handle_company_created(event):
    client.workflows.trigger_by_event(event)
```

## Idempotency

Pass `Idempotency-Key` header on execute requests to prevent duplicate runs.

## Local Development

Point SDK at `http://localhost:8000/api/v1` with demo JWT from `/auth/login`.