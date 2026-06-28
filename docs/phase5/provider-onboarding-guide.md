# Provider Onboarding Guide

**Version 2.0** | AI Lead Intelligence Platform — Phase 5

---

## Table of Contents

1. [Onboarding Overview](#1-onboarding-overview)
2. [Pre-Onboarding Checklist](#2-pre-onboarding-checklist)
3. [Legal & Compliance Review](#3-legal--compliance-review)
4. [Technical Onboarding](#4-technical-onboarding)
5. [Configuration & Credentials](#5-configuration--credentials)
6. [Testing & Validation](#6-testing--validation)
7. [Production Rollout](#7-production-rollout)
8. [Provider Catalog](#8-provider-catalog)
9. [Offboarding](#9-offboarding)

---

## 1. Onboarding Overview

Provider onboarding brings a new data source into the Discovery Platform through a governed 6-stage process:

```text
1. Intake → 2. Legal Review → 3. SDK Implementation → 4. QA → 5. Staging → 6. Production
```

**Roles:**

| Role | Responsibility |
|------|----------------|
| Product | Business case, priority, credit pricing |
| Legal | ToS, DPA, data classification |
| Engineering | Connector implementation |
| Security | Credential handling, SSRF review |
| Ops | Monitoring, runbook, alerting |

---

## 2. Pre-Onboarding Checklist

| Item | Owner | Status |
|------|-------|--------|
| Provider has official REST/GraphQL API | Engineering | ☐ |
| API documentation is current | Engineering | ☐ |
| Sandbox/test environment available | Engineering | ☐ |
| Business contract or API license signed | Legal | ☐ |
| DPA executed (if processing EU data) | Legal | ☐ |
| Credit/pricing model defined | Product | ☐ |
| `source_type` classification determined | Legal + Engineering | ☐ |
| Rate limits documented | Engineering | ☐ |
| Data fields mapped to canonical model | Engineering | ☐ |

---

## 3. Legal & Compliance Review

### 3.1 Source Type Assignment

| Question | Classification |
|----------|---------------|
| Is data from an official provider API with a license? | `licensed_provider` |
| Is data from government open data? | `government_open_data` |
| Is data from a public company registry? | `public_registry` |
| Is data user-imported? | `user_import` |
| Is data from user OAuth CRM? | `user_authorized` |

### 3.2 Prohibited Sources

- Login-gated social media scraping
- Personal data without lawful basis
- Sources explicitly prohibiting resale in ToS
- Unofficial reverse-engineered APIs

### 3.3 Documentation Required

- Provider ToS summary
- DPA (Data Processing Agreement)
- Data retention policy alignment
- Sub-processor notification (if applicable)

---

## 4. Technical Onboarding

### 4.1 Implementation Steps

1. Create connector module: `backend/connectors/{provider}.py`
2. Implement `ConnectorSDKBase` contract
3. Assign `ConnectorCategory` and `ConnectorCapability` set
4. Register with `@ConnectorRegistry.register`
5. Add contract tests
6. Add mock provider for CI
7. Document in connector developer guide

### 4.2 Capability Declaration

```python
capabilities = frozenset({
    ConnectorCapability.SEARCH,
    ConnectorCapability.LOOKUP,
    ConnectorCapability.ENRICH,
})
```

Only declare capabilities the connector actually implements.

### 4.3 Provider Selection Rules

Add to `provider_selection_rules.yaml`:

```yaml
apollo:
  priority: 1
  entity_types: [company, contact]
  capabilities: [search, enrich]
  regions: [US, EU, global]
  fallback: clearbit

clearbit:
  priority: 2
  entity_types: [company]
  capabilities: [enrich, lookup]
  fallback: apollo
```

---

## 5. Configuration & Credentials

### 5.1 Tenant Configuration

Tenants configure via Admin UI or API:

```http
PUT /api/v1/discovery/providers/apollo/config
{
  "enabled": true,
  "credentials": {"api_key": "..."},
  "settings": {"priority": 1}
}
```

### 5.2 Platform-Level Secrets

For shared/platform API keys (if applicable):

- Store in HashiCorp Vault or AWS Secrets Manager
- Reference via `CONNECTOR_APOLLO_API_KEY` env var
- Rotate quarterly

### 5.3 Configuration Schema

Each connector exposes a JSON Schema for settings:

```json
{
  "type": "object",
  "properties": {
    "api_key": {"type": "string", "format": "password"},
    "default_page_size": {"type": "integer", "default": 25, "maximum": 100}
  },
  "required": ["api_key"]
}
```

---

## 6. Testing & Validation

### 6.1 Test Gates

| Gate | Criteria |
|------|----------|
| Contract tests | All SDK methods implemented |
| Unit tests | > 80% coverage on connector module |
| Mock integration | CI passes without live API |
| Live integration | Search, lookup, enrich succeed in staging |
| Load test | 50 concurrent requests without error spike |
| Security review | No SSRF, credentials encrypted |
| Normalization QA | Sample of 100 records manually verified |

### 6.2 Staging Validation

1. Configure staging tenant with test API key
2. Run discovery: 10 company + 10 contact searches
3. Verify normalization, confidence scores, provenance
4. Verify credit accounting
5. Verify health check in dashboard
6. Run 24h soak test

---

## 7. Production Rollout

### 7.1 Rollout Strategy

| Phase | Scope | Duration |
|-------|-------|----------|
| Canary | Internal org only | 3 days |
| Beta | 5 pilot tenants (opt-in) | 1 week |
| GA | All tenants | — |

### 7.2 Feature Flag

```python
FEATURE_FLAGS = {
    "connector.apollo.enabled": True,  # GA
    "connector.new_provider.enabled": False,  # Canary
}
```

### 7.3 Production Checklist

| Item | Status |
|------|--------|
| Monitoring dashboards live | ☐ |
| Alerting rules configured | ☐ |
| Runbook updated | ☐ |
| Credit pricing in billing system | ☐ |
| Admin UI shows connector | ☐ |
| Documentation published | ☐ |
| On-call briefed | ☐ |

---

## 8. Provider Catalog

### 8.1 Current Providers

| Provider | Category | Capabilities | Source Type | Status |
|----------|----------|-------------|-------------|--------|
| Apollo.io | Enrichment | search, lookup, enrich | licensed_provider | Production |
| Clearbit | Enrichment | lookup, enrich | licensed_provider | Production |
| Hunter.io | Verification | enrich, verify_email | licensed_provider | Production |

### 8.2 Planned Providers

| Provider | Category | Capabilities | Priority |
|----------|----------|-------------|----------|
| BuiltWith | Tech Detection | detect_tech | P1 |
| Google Places | Geolocation | geocode, search | P2 |
| Companies House (UK) | Company Registry | lookup, search | P2 |
| Salesforce | CRM | crm_sync | P1 |
| HubSpot | CRM | crm_sync | P1 |
| OpenCorporates | Company Registry | lookup, search | P3 |

### 8.3 Import Sources

| Source | Category | Capabilities |
|--------|----------|-------------|
| CSV Upload | Import | import |
| XLSX Upload | Import | import |
| Google Sheets | Import | import (user_authorized) |
| Webhook | Webhook | webhook |

---

## 9. Offboarding

When removing a provider:

1. Disable feature flag
2. Notify affected tenants (30-day notice)
3. Stop scheduling new jobs using provider
4. Drain in-flight jobs
5. Archive connector configs (encrypted backup)
6. Remove from Provider Selection Engine
7. Retain audit logs per retention policy
8. Update documentation and catalog