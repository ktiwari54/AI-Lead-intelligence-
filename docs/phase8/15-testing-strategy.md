# 15 — Testing Strategy

**Version 1.0** | Phase 8 | AI Lead Intelligence Platform

---

## Table of Contents

1. [Overview](#1-overview)
2. [Test Pyramid](#2-test-pyramid)
3. [Unit Tests](#3-unit-tests)
4. [Integration Tests](#4-integration-tests)
5. [End-to-End Tests](#5-end-to-end-tests)
6. [Chaos Tests](#6-chaos-tests)
7. [Performance Tests](#7-performance-tests)
8. [CI/CD Integration](#8-cicd-integration)
9. [Test Data & Fixtures](#9-test-data--fixtures)

---

## 1. Overview

Workflow platform testing ensures correctness of compilation, execution, tenant isolation, sandbox security, and resilience under failure. Tests live in `backend/tests/workflows/` and `frontend/src/features/workflows/__tests__/`.

---

## 2. Test Pyramid

```
                    ┌─────────┐
                    │  E2E    │  5%  — Playwright builder + execution
                   ┌┴─────────┴┐
                   │ Integration│  25% — API, DB, Celery, RabbitMQ
                  ┌┴───────────┴┐
                  │    Unit     │  70% — Compiler, rules, state machine
                  └─────────────┘
```

| Layer | Count Target | Runtime |
|-------|--------------|---------|
| Unit | 300+ | < 30s |
| Integration | 80+ | < 3min |
| E2E | 20+ | < 10min |
| Chaos | 10+ | < 15min (nightly) |
| Performance | 5+ | < 30min (weekly) |

---

## 3. Unit Tests

### Compiler Tests

```text
backend/tests/workflows/compiler/
├── test_schema_validation.py
├── test_graph_analysis.py
├── test_cycle_detection.py
├── test_type_checking.py
├── test_expression_parsing.py
├── test_plan_generation.py
└── fixtures/
    ├── valid_workflows/
    └── invalid_workflows/
```

| Test Case | Assertion |
|-----------|-----------|
| Single trigger node | Compiles successfully |
| No trigger node | `WF001` error |
| Cycle in graph | `WF002` error |
| Type mismatch on edge | `WF003` error |
| 101 nodes | `WF006` error |
| Valid condition expression | AST in plan |
| Invalid expression syntax | `WF004` error |

### State Machine Tests

```python
@pytest.mark.parametrize("from_status,event,to_status", [
    ("pending", "START", "running"),
    ("running", "STEP_WAITING", "waiting"),
    ("waiting", "RESUME", "running"),
    ("running", "ALL_STEPS_DONE", "completed"),
    ("running", "STEP_FAILED", "failed"),
    ("running", "CANCEL", "cancelled"),
])
def test_execution_transitions(from_status, event, to_status):
    sm = ExecutionStateMachine(from_status)
    sm.apply(event)
    assert sm.status == to_status
```

### Rule Engine Tests

See [04-rule-engine-design.md](./04-rule-engine-design.md) §9.

### Node Handler Tests

Each node handler tested with mocked dependencies:

```python
async def test_ai_score_node_success(mock_scoring_service):
    handler = AIScoreHandler(scoring=mock_scoring_service)
    result = await handler.execute(sample_input, sample_ctx)
    assert result.status == StepStatus.COMPLETED
    assert result.outputs["score"] == 85
```

---

## 4. Integration Tests

### API Integration

```text
backend/tests/workflows/integration/
├── test_workflow_crud.py
├── test_definition_compile.py
├── test_execution_lifecycle.py
├── test_approval_flow.py
├── test_schedule_trigger.py
├── test_template_instantiate.py
├── test_tenant_isolation.py
└── conftest.py
```

### Test Infrastructure

```python
# conftest.py
@pytest.fixture
async def workflow_client(test_app, auth_headers):
    async with AsyncClient(app=test_app, headers=auth_headers) as client:
        yield client

@pytest.fixture
async def celery_worker(celery_app):
    """Embedded Celery worker for integration tests."""
    with celery_app.purge():
        yield start_test_worker(queues=["workflows"])
```

### Key Integration Scenarios

| Scenario | Steps | Assertion |
|----------|-------|-----------|
| Create + compile + activate | POST workflow, PUT definition, PATCH active | `is_active: true`, trigger index built |
| Event-triggered execution | Publish `contact.created`, wait for worker | Execution `completed`, step outputs present |
| Approval pause + resume | Execute to approval, POST decide | Execution resumes, completes |
| Schedule trigger | Insert schedule with past `next_run_at`, run tick | Execution created |
| Template instantiate | POST instantiate with params | Workflow created with substituted values |
| Cross-tenant isolation | Org A creates, Org B accesses | 404 response |
| Concurrent executions | Start 15 executions (limit 10) | 10 run, 5 rate-limited (429) |
| Idempotent step | Execute same step twice | Second returns cached result |

### Database Tests

```python
async def test_execution_state_persisted(db_session):
    execution = await executor.start(workflow_id, trigger_data)
    await executor.run(execution.id)

    stored = await repo.get_execution(execution.id)
    assert stored.status == "completed"
    assert len(stored.steps) == expected_step_count
```

### RabbitMQ Tests

```python
async def test_event_triggers_workflow(rabbitmq_channel, celery_worker):
    publish_event("contact.created", payload=sample_contact)
    await wait_for_execution(status="completed", timeout=30)
```

---

## 5. End-to-End Tests

### Playwright Tests

```text
frontend/e2e/workflows/
├── builder-create-workflow.spec.ts
├── builder-add-nodes.spec.ts
├── builder-validate-and-save.spec.ts
├── execution-monitor.spec.ts
├── approval-inbox.spec.ts
└── template-gallery.spec.ts
```

### E2E Scenario: Full Workflow Lifecycle

```typescript
test('create, build, activate, and monitor workflow', async ({ page }) => {
  await page.goto('/workflows/new');
  await page.click('[data-testid="template-auto-score-contacts"]');
  await page.fill('[data-testid="workflow-name"]', 'E2E Test Workflow');
  await page.click('[data-testid="instantiate-template"]');

  // Builder
  await expect(page.locator('[data-testid="canvas"]')).toBeVisible();
  await page.click('[data-testid="save-workflow"]');
  await expect(page.locator('[data-testid="compile-success"]')).toBeVisible();

  // Activate
  await page.click('[data-testid="activate-workflow"]');

  // Trigger via API
  await triggerContactCreated(testContact);

  // Monitor
  await page.goto('/workflows/executions');
  await expect(page.locator('[data-testid="execution-completed"]')).toBeVisible({ timeout: 30000 });
});
```

---

## 6. Chaos Tests

**Schedule:** Nightly on staging environment.

### Chaos Scenarios

| Scenario | Injection | Expected Behavior |
|----------|-----------|-------------------|
| Worker crash mid-execution | `SIGKILL` worker during step 3 | Celery redelivery; execution resumes from step 3 |
| RabbitMQ restart | Restart broker during event publish | Outbox poller recovers; no event loss |
| PostgreSQL slow | 5s query delay injection | Timeout; step retry; eventual completion |
| Redis unavailable | Stop Redis | Plan loaded from DB; rate limit disabled (fail-open with alert) |
| AI provider 503 | Mock 503 responses | Step retry 3x; then fail with `PROVIDER_ERROR` |
| Duplicate event delivery | Publish same event twice | Idempotency prevents duplicate execution |
| Approval timeout | Don't decide within timeout | Escalation fires per config |
| Network partition | Isolate worker from DB | Execution fails; state consistent (no partial writes) |

### Chaos Tools

```bash
# Docker Compose chaos injection
docker kill --signal=SIGKILL ai-lead-intelligence-worker-1

# RabbitMQ management
rabbitmqctl stop_app && sleep 10 && rabbitmqctl start_app

# Toxiproxy for latency injection
toxiproxy-cli create postgres_latency -l 0.0.0.0:25432 -u postgres:5432
toxiproxy-cli toxic add postgres_latency -t latency -a latency=5000
```

---

## 7. Performance Tests

### Load Test Scenarios (k6)

```javascript
// tests/performance/workflow_load.js
export const options = {
  scenarios: {
    event_burst: {
      executor: 'ramping-vus',
      startVUs: 0,
      stages: [
        { duration: '2m', target: 100 },
        { duration: '5m', target: 100 },
        { duration: '2m', target: 0 },
      ],
    },
  },
  thresholds: {
    'workflow_start_latency_seconds{p(95)}': ['< 2'],
    'workflow_execution_duration_seconds{p(95)}': ['< 30'],
    'http_req_failed{endpoint:execute}': ['< 0.01'],
  },
};
```

### Benchmarks

| Scenario | Target |
|----------|--------|
| 100 concurrent event triggers | p95 start < 2s |
| 500 concurrent executions | No OOM; queue drains < 10min |
| Compiler (50-node workflow) | < 500ms |
| Rule evaluation (10 rules) | < 10ms |
| Trigger index lookup | < 5ms |

---

## 8. CI/CD Integration

### GitHub Actions

```yaml
# .github/workflows/workflow-tests.yml
name: Workflow Platform Tests

on:
  push:
    paths: ['backend/app/workflows/**', 'backend/tests/workflows/**']
  pull_request:
    paths: ['backend/app/workflows/**']

jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - run: pytest backend/tests/workflows/ -m "not integration and not chaos" --cov=app/workflows

  integration:
    runs-on: ubuntu-latest
    services:
      postgres: ...
      redis: ...
      rabbitmq: ...
    steps:
      - run: pytest backend/tests/workflows/ -m integration

  e2e:
    runs-on: ubuntu-latest
    steps:
      - run: npx playwright test frontend/e2e/workflows/
```

### Test Markers

```python
# pytest markers
@pytest.mark.unit
@pytest.mark.integration
@pytest.mark.chaos
@pytest.mark.performance
```

### Coverage Targets

| Module | Min Coverage |
|--------|--------------|
| `compiler/` | 95% |
| `executor/` | 90% |
| `rules/` | 95% |
| `approvals/` | 90% |
| `nodes/` | 85% |
| `router.py` | 80% |

---

## 9. Test Data & Fixtures

### Workflow Fixtures

```text
backend/tests/workflows/fixtures/
├── definitions/
│   ├── auto_score_contacts.json
│   ├── approval_crm_sync.json
│   ├── scheduled_export.json
│   └── complex_branching.json
├── trigger_payloads/
│   ├── contact_created.json
│   ├── lead_scored.json
│   └── deal_stage_changed.json
└── factories.py
```

### Factory Example

```python
class WorkflowFactory:
    @staticmethod
    async def create_with_definition(
        db, org_id, definition: dict, *, is_active: bool = False
    ) -> Workflow:
        workflow = await create_workflow(db, org_id, name="Test Workflow")
        version = await compile_and_save(db, workflow.id, definition)
        if is_active:
            await activate_workflow(db, workflow.id, version.id)
        return workflow
```

---

## Related Documents

- [04-rule-engine-design.md](./04-rule-engine-design.md) — Rule engine tests
- [13-security-model.md](./13-security-model.md) — Security test requirements
- [phase5/testing-strategy.md](../phase5/testing-strategy.md) — Platform testing standards
- [phase11/04-cicd-pipeline.md](../phase11/04-cicd-pipeline.md) — CI/CD pipeline