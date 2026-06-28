# Connector Developer Guide

**Version 2.0** | AI Lead Intelligence Platform — Phase 5

---

## Table of Contents

1. [Getting Started](#1-getting-started)
2. [SDK Contract](#2-sdk-contract)
3. [Implementing a Connector](#3-implementing-a-connector)
4. [DTO Mapping](#4-dto-mapping)
5. [Rate Limiting & Retries](#5-rate-limiting--retries)
6. [Testing Your Connector](#6-testing-your-connector)
7. [Registration](#7-registration)
8. [Best Practices](#8-best-practices)
9. [Reference Implementation](#9-reference-implementation)

---

## 1. Getting Started

### 1.1 Prerequisites

- Python 3.11+
- Familiarity with the provider's official API documentation
- Valid API credentials for development/testing
- Review of provider Terms of Service and data usage rights

### 1.2 Project Layout

```text
backend/connectors/
├── sdk/
│   ├── base.py          # ConnectorSDKBase
│   └── dto.py           # Standard DTOs
├── registry.py          # ConnectorRegistry
├── apollo.py            # v1 (legacy)
├── apollo_v2.py         # v2 reference
└── your_provider.py     # Your connector
```

### 1.3 Quick Start

```python
from backend.connectors.sdk.base import ConnectorSDKBase, RetryPolicy
from backend.connectors.registry import ConnectorRegistry
from backend.app.discovery.capabilities import ConnectorCapability, ConnectorCategory, DataSourceType

@ConnectorRegistry.register
class YourProviderConnector(ConnectorSDKBase):
    name = "your_provider"
    display_name = "Your Provider"
    category = ConnectorCategory.ENRICHMENT
    source_type = DataSourceType.LICENSED_PROVIDER
    capabilities = frozenset({
        ConnectorCapability.SEARCH,
        ConnectorCapability.ENRICH,
    })
```

---

## 2. SDK Contract

Every connector must implement all methods on `ConnectorSDKBase`:

| Method | Purpose | Returns |
|--------|---------|---------|
| `authenticate()` | Validate credentials | `bool` |
| `health_check()` | Liveness + quota check | `ConnectorHealthDTO` |
| `search(request)` | Search by query/filters | `ConnectorSearchResult` |
| `lookup(id, type)` | Find by domain/email/etc. | `ConnectorSearchResult` |
| `fetch_details(external_id)` | Full record by provider ID | `ConnectorSearchResult` |
| `normalize(raw, entity_type)` | Raw → canonical DTO | `NormalizedCompanyDTO \| NormalizedContactDTO` |
| `validate(dto)` | Schema validation errors | `list[str]` |
| `transform(dto)` | DTO → internal dict | `dict` |
| `map_to_domain_model(dto)` | DTO → persistence model | `dict` |
| `get_rate_limit()` | Current quota | `RateLimitDTO` |
| `retry_policy()` | Retry configuration | `RetryPolicy` |
| `disconnect()` | Cleanup | `None` |

Optional helpers:

- `supports(capability)` — check capability membership
- `_ensure_authenticated()` — call before API requests

---

## 3. Implementing a Connector

### 3.1 Authentication

```python
def authenticate(self) -> bool:
    try:
        response = self._client.get("/v1/me")
        self._authenticated = response.status_code == 200
        return self._authenticated
    except Exception:
        self._authenticated = False
        return False
```

Never store credentials in instance variables beyond the session. Load from `self.config`.

### 3.2 Search

```python
def search(self, request: ConnectorSearchRequest) -> ConnectorSearchResult:
    self._ensure_authenticated()
    started = time.perf_counter()

    payload = self._build_search_payload(request)
    raw = self._post("/search", payload)

    records = []
    for item in raw.get("results", []):
        dto = self.normalize(item, entity_type=request.entity_type)
        records.append(ConnectorRecordDTO(
            entity_type="company",
            external_id=item.get("id"),
            company=dto,
            match_confidence=item.get("score", 0.7),
        ))

    return ConnectorSearchResult(
        success=True,
        records=records,
        total=raw.get("total", len(records)),
        source=self.name,
        credits_used=raw.get("credits_used", len(records)),
        latency_ms=int((time.perf_counter() - started) * 1000),
        raw_response=raw,
    )
```

### 3.3 Error Handling

Return `ConnectorSearchResult(success=False, errors=[...])` for:

- Validation errors (don't retry)
- Credits exhausted (don't retry)
- Rate limits (let orchestrator retry)

Raise exceptions only for unrecoverable programming errors.

### 3.4 Health Check

```python
def health_check(self) -> ConnectorHealthDTO:
    started = time.perf_counter()
    try:
        self._ensure_authenticated()
        quota = self._get("/quota")
        return ConnectorHealthDTO(
            healthy=True,
            latency_ms=int((time.perf_counter() - started) * 1000),
            credits_remaining=quota.get("remaining"),
        )
    except Exception as e:
        return ConnectorHealthDTO(
            healthy=False,
            latency_ms=int((time.perf_counter() - started) * 1000),
            message=str(e),
        )
```

---

## 4. DTO Mapping

### 4.1 Company Normalization

Map all provider fields to `NormalizedCompanyDTO`:

```python
def normalize(self, raw: dict, entity_type: str = "company") -> NormalizedCompanyDTO:
    return NormalizedCompanyDTO(
        external_id=str(raw.get("id", "")),
        name=raw.get("name", ""),
        domain=raw.get("website", "").replace("https://", "").split("/")[0],
        industry=raw.get("industry"),
        employee_count=raw.get("employees"),
        source=self.name,
        source_type=self.source_type.value,
        raw=raw,
    )
```

### 4.2 Provenance

Attach provenance for each populated field:

```python
from backend.connectors.sdk.dto import FieldProvenance
from datetime import datetime, timezone

provenance = [
    FieldProvenance("domain", self.name, self.source_type.value, datetime.now(timezone.utc))
]
```

### 4.3 Validation

```python
def validate(self, dto: NormalizedCompanyDTO | NormalizedContactDTO) -> list[str]:
    errors = []
    if isinstance(dto, NormalizedCompanyDTO) and not dto.name:
        errors.append("company.name is required")
    return errors
```

---

## 5. Rate Limiting & Retries

### 5.1 Rate Limit Reporting

```python
def get_rate_limit(self) -> RateLimitDTO:
    return RateLimitDTO(
        requests_remaining=self._remaining,
        requests_limit=self.REQUESTS_PER_MINUTE,
        reset_at=self._reset_at,
    )
```

### 5.2 Retry Policy

```python
def retry_policy(self) -> RetryPolicy:
    return RetryPolicy(
        max_attempts=4,
        backoff_base=2.0,
        max_backoff_seconds=60.0,
        retryable_status_codes=(429, 500, 502, 503, 504),
    )
```

### 5.3 HTTP Client

Use `httpx` with timeouts. Respect `Retry-After` headers on 429.

---

## 6. Testing Your Connector

### 6.1 Contract Tests

```python
# tests/connectors/test_your_provider_contract.py
import pytest
from backend.connectors.your_provider import YourProviderConnector

CONTRACT_METHODS = [
    "authenticate", "health_check", "search", "lookup",
    "fetch_details", "normalize", "validate", "transform",
    "map_to_domain_model", "get_rate_limit", "retry_policy", "disconnect",
]

def test_implements_contract():
    connector = YourProviderConnector({"api_key": "test"})
    for method in CONTRACT_METHODS:
        assert hasattr(connector, method) and callable(getattr(connector, method))
```

### 6.2 Mock Provider

Use `responses` or `httpx.MockTransport` for unit tests. See `tests/connectors/mocks/`.

### 6.3 Integration Tests

Mark with `@pytest.mark.integration`. Require `YOUR_PROVIDER_API_KEY` env var.

---

## 7. Registration

```python
@ConnectorRegistry.register
class YourProviderConnector(ConnectorSDKBase):
    ...
```

Registry auto-discovers on import. Ensure module is imported in `backend/connectors/__init__.py`.

Verify registration:

```python
from backend.connectors.registry import ConnectorRegistry
assert "your_provider" in [c["name"] for c in ConnectorRegistry.list_available()]
```

---

## 8. Best Practices

| Do | Don't |
|----|-------|
| Use official APIs only | Scrape HTML or bypass auth |
| Map to canonical DTOs | Return raw provider JSON to orchestrator |
| Declare `source_type` accurately | Misclassify data origin |
| Report `credits_used` | Hide quota consumption |
| Handle pagination in `search()` | Return partial results silently |
| Log errors without PII | Log API keys or emails |
| Use timeouts on all HTTP calls | Block workers indefinitely |
| Implement `disconnect()` | Leak HTTP connections |

---

## 9. Reference Implementation

See `backend/connectors/apollo_v2.py` for a complete SDK v2 implementation wrapping Apollo.io.

Key patterns demonstrated:

- v1→v2 bridge for gradual migration
- Company and contact normalization
- Rate limit error handling with tenacity
- `ConnectorSearchRequest` filter mapping
- Provenance attachment