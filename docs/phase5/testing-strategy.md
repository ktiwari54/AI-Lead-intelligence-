# Testing Strategy — Discovery Platform

**Version 2.0** | AI Lead Intelligence Platform — Phase 5

---

## Table of Contents

1. [Testing Pyramid](#1-testing-pyramid)
2. [Unit Tests](#2-unit-tests)
3. [Connector Contract Tests](#3-connector-contract-tests)
4. [Mock Providers](#4-mock-providers)
5. [Integration Tests](#5-integration-tests)
6. [Load Tests](#6-load-tests)
7. [Failure Injection Tests](#7-failure-injection-tests)
8. [Security Tests](#8-security-tests)
9. [Performance Benchmarks](#9-performance-benchmarks)
10. [Chaos Testing](#10-chaos-testing)
11. [CI Pipeline](#11-ci-pipeline)

---

## 1. Testing Pyramid

```text
                    ┌─────────────┐
                    │   Chaos     │  ← Quarterly
                   ┌┴─────────────┴┐
                   │  Load / Perf  │  ← Weekly (staging)
                  ┌┴───────────────┴┐
                  │   Integration   │  ← Every PR
                 ┌┴─────────────────┴┐
                 │   Contract + Mock    │  ← Every PR
                ┌┴───────────────────────┴┐
                │        Unit Tests       │  ← Every commit
                └─────────────────────────┘
```

| Layer | Coverage Target | Run Frequency |
|-------|----------------|---------------|
| Unit | 85% on discovery module | Every commit |
| Contract | 100% registered connectors | Every PR |
| Integration | Critical paths | Every PR |
| Load | Baseline + regression | Weekly |
| Chaos | Failure scenarios | Quarterly |

---

## 2. Unit Tests

### 2.1 Scope

| Module | Test Focus |
|--------|-----------|
| `normalizers/*` | Input/output pairs, edge cases |
| `matchers/*` | Similarity thresholds, blocking |
| `confidence.py` | Score calculation, weights |
| `orchestrator.py` | Connector selection, aggregation |
| `schemas.py` | Pydantic validation |

### 2.2 Example

```python
def test_domain_normalizer_strips_www():
    assert DomainNormalizer.normalize("https://www.acme.com/about") == "acme.com"

def test_confidence_engine_single_source():
    score = ConfidenceEngine().calculate(record, sources=["apollo"])
    assert 0.4 <= score.overall <= 0.9
```

### 2.3 Fixtures

- `tests/fixtures/companies/` — normalized company DTOs
- `tests/fixtures/contacts/` — normalized contact DTOs
- `tests/fixtures/raw/apollo/` — raw API responses

---

## 3. Connector Contract Tests

### 3.1 Contract Test Suite

Every registered connector must pass:

```python
@pytest.mark.parametrize("connector_class", ConnectorRegistry.get_all_classes())
class TestConnectorContract:
    def test_required_methods(self, connector_class):
        ...

    def test_capabilities_declared(self, connector_class):
        assert len(connector_class.capabilities) > 0

    def test_source_type_valid(self, connector_class):
        assert connector_class.source_type in DataSourceType

    def test_normalize_returns_dto(self, connector_class):
        ...

    def test_validate_catches_missing_name(self, connector_class):
        ...
```

### 3.2 Compliance Tests

```python
def test_connector_not_scraping_based(connector_class):
    assert connector_class.source_type != "unauthorized_scrape"
    assert "scrape" not in connector_class.name
```

---

## 4. Mock Providers

### 4.1 Mock Server

`tests/connectors/mocks/mock_provider.py`:

```python
class MockProviderConnector(ConnectorSDKBase):
    name = "mock_provider"
    capabilities = frozenset({ConnectorCapability.SEARCH, ConnectorCapability.ENRICH})

    def search(self, request):
        return ConnectorSearchResult(
            success=True,
            records=[/* deterministic test data */],
            total=3,
            source="mock_provider",
        )
```

### 4.2 HTTP Mocking

```python
import httpx
import respx

@respx.mock
def test_apollo_search():
    respx.post("https://api.apollo.io/v1/mixed_people/search").respond(
        json={"people": [{"first_name": "Jane", "email": "jane@acme.com"}]}
    )
    ...
```

### 4.3 Scenario Mocks

| Scenario | Mock Behavior |
|----------|---------------|
| Rate limited | Return 429 with `Retry-After: 60` |
| Credits exhausted | Return 402 |
| Timeout | Delay 35s |
| Partial results | Return 10 of 25 with `total: 25` |
| Auth failure | Return 401 |

---

## 5. Integration Tests

### 5.1 Test Environment

- Docker Compose: PostgreSQL, Redis, OpenSearch
- `@pytest.mark.integration` marker
- Run on PR via GitHub Actions

### 5.2 Critical Paths

| Test | Description |
|------|-------------|
| `test_discovery_execute_async` | POST /discovery/execute → poll job → get results |
| `test_discovery_sync_small` | Sync execution returns hits |
| `test_multi_connector_aggregation` | Apollo + mock provider merge |
| `test_entity_resolution_merge` | Duplicate companies merged |
| `test_enrichment_pipeline` | Fields enriched post-discovery |
| `test_tenant_isolation` | Org A cannot see Org B jobs |
| `test_rate_limit_enforcement` | 429 after quota exceeded |

### 5.3 Live Provider Tests

```python
@pytest.mark.integration
@pytest.mark.live
@pytest.mark.skipif(not os.getenv("APOLLO_API_KEY"), reason="No API key")
def test_apollo_live_search():
    ...
```

Run nightly, not on every PR.

---

## 6. Load Tests

### 6.1 Tooling

k6 or Locust scripts in `tests/load/`.

### 6.2 Scenarios

| Scenario | Target |
|----------|--------|
| Steady state | 100 concurrent discovery jobs, 10 min |
| Burst | 500 jobs in 60s |
| Connector saturation | Single provider at rate limit |
| Index throughput | 10K records indexed in 5 min |

### 6.3 Acceptance Criteria

| Metric | Threshold |
|--------|-----------|
| p95 job completion | < 60s |
| Error rate | < 1% |
| Queue depth recovery | < 5 min after burst |
| No memory leaks | Stable RSS over 1h run |

---

## 7. Failure Injection Tests

### 7.1 Scenarios

| Injection | Expected Behavior |
|-----------|-------------------|
| Kill connector mid-request | Retry → partial result |
| Redis unavailable | Job fails gracefully, 503 |
| PostgreSQL slow (500ms latency) | Timeout with retry |
| OpenSearch down | Job completes, index queued |
| Provider returns malformed JSON | Record quarantined, job continues |
| All connectors circuit-open | 503 `CONNECTOR_UNAVAILABLE` |

### 7.2 Tooling

- Toxiproxy for network latency/partition
- `pytest-fault-injection` hooks
- Celery task failure simulation

---

## 8. Security Tests

| Test | Description |
|------|-------------|
| Cross-tenant access | User A cannot read User B's job |
| Credential leak scan | Grep logs for API key patterns |
| SSRF attempt | User-supplied URL blocked in connector |
| SQL injection | Fuzz discovery query/filters |
| JWT tampering | Modified org_id rejected |
| Rate limit bypass | Cannot exceed tenant quota |
| Webhook signature | Invalid HMAC rejected |

Run via OWASP ZAP in staging weekly.

---

## 9. Performance Benchmarks

### 9.1 Micro-Benchmarks

```bash
pytest tests/benchmarks/ --benchmark-only
```

| Function | Target |
|----------|--------|
| `NormalizationPipeline.process(100 records)` | < 200ms |
| `EntityResolutionEngine.resolve(50 candidates)` | < 500ms |
| `ConfidenceEngine.calculate(100 hits)` | < 100ms |

### 9.2 Regression Detection

Benchmark results stored in CI artifacts. Alert on > 20% regression.

---

## 10. Chaos Testing

### 10.1 Quarterly Exercises

| Experiment | Blast Radius |
|------------|-------------|
| Kill 50% of Celery workers | Staging |
| Partition Redis from workers | Staging |
| Rotate KMS key during active jobs | Staging |
| Provider API outage (mock) | Staging |

### 10.2 Game Days

- Document findings in post-mortem template
- Update runbook with discovered failure modes

---

## 11. CI Pipeline

```yaml
# .github/workflows/discovery-tests.yml
jobs:
  unit:
    runs-on: ubuntu-latest
    steps:
      - pytest tests/unit tests/connectors/contract -v --cov=backend/app/discovery

  integration:
    runs-on: ubuntu-latest
    services:
      postgres: ...
      redis: ...
    steps:
      - pytest tests/integration -m "integration and not live"

  load:
    runs-on: ubuntu-latest
    if: github.event_name == 'schedule'
    steps:
      - k6 run tests/load/discovery_steady.js
```

### PR Gates

| Gate | Required |
|------|----------|
| Unit + contract tests pass | Yes |
| Coverage ≥ 85% on discovery | Yes |
| Integration tests pass | Yes |
| No security scan criticals | Yes |
| Load test regression | Weekly |