# Phase 5 — Data Discovery, Connector Framework & Intelligence Engine

**Version 2.0** | AI Lead Intelligence Platform

Phase 5 defines the **provider-agnostic discovery platform** that powers company/contact discovery, enrichment, verification, entity resolution, and confidence scoring — without dependence on unauthorized scraping.

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **Capability-based connectors** | Connectors implement capabilities (`search`, `lookup`, `enrich`, `verify`) — not provider-specific business logic |
| **Canonical data model** | All sources map to `Company`, `Contact`, `Address`, `Technology`, `DiscoveryResult` domain models |
| **Discovery pipeline** | Every search is a pipeline: parse → select → retrieve → normalize → resolve → enrich → score → persist |
| **Authorized data only** | Official APIs, public registries, user OAuth connections, licensed enrichment providers |
| **Replaceable providers** | Connector Registry + SDK; swap Apollo for Clearbit without changing orchestrator |

## Deliverables Index

| # | Deliverable | Document |
|---|-------------|----------|
| 1 | Discovery Platform Architecture | [discovery-platform-architecture.md](./discovery-platform-architecture.md) |
| 2 | Connector Framework Design | [connector-framework.md](./connector-framework.md) |
| 3 | Connector SDK Specification | [connector-sdk-specification.md](./connector-sdk-specification.md) |
| 4 | Discovery Orchestrator Design | [discovery-orchestrator.md](./discovery-orchestrator.md) |
| 5 | Standard DTO Models | [standard-dto-models.md](./standard-dto-models.md) |
| 6 | Query Processing Flow | [query-engine.md](./query-engine.md) |
| 7 | Normalization Pipeline | [data-pipelines.md §1](./data-pipelines.md#1-normalization-pipeline) |
| 8 | Entity Resolution Design | [data-pipelines.md §2](./data-pipelines.md#2-entity-resolution-engine) |
| 9 | Confidence Scoring Model | [data-pipelines.md §3](./data-pipelines.md#3-confidence-engine) |
| 10 | Enrichment Pipeline | [data-pipelines.md §4](./data-pipelines.md#4-enrichment-pipeline) |
| 11 | Background Job Architecture | [events-and-workers.md §1](./events-and-workers.md#1-background-workers) |
| 12 | Event-Driven Workflow | [events-and-workers.md §2](./events-and-workers.md#2-event-model) |
| 13 | API Specifications | [api-specification.md](./api-specification.md) |
| 14 | Security Architecture | [security-architecture.md](./security-architecture.md) |
| 15 | Monitoring & Observability | [observability.md](./observability.md) |
| 16 | Connector Developer Guide | [connector-developer-guide.md](./connector-developer-guide.md) |
| 17 | Provider Onboarding Guide | [provider-onboarding-guide.md](./provider-onboarding-guide.md) |
| 18 | Testing Strategy | [testing-strategy.md](./testing-strategy.md) |
| 19 | Operational Runbook | [operational-runbook.md](./operational-runbook.md) |
| 20 | Scalability & Performance Guide | [scalability-performance.md](./scalability-performance.md) |

## Skeleton Code

| Component | Path |
|-----------|------|
| Discovery orchestrator | `backend/app/discovery/orchestrator.py` |
| Normalization pipeline | `backend/app/discovery/pipelines/normalization.py` |
| Entity resolution | `backend/app/discovery/pipelines/entity_resolution.py` |
| Confidence engine | `backend/app/discovery/pipelines/confidence.py` |
| Enrichment pipeline | `backend/app/discovery/pipelines/enrichment.py` |
| Job persistence | `backend/app/discovery/models.py`, `repository.py` |
| Discovery API | `backend/app/discovery/router.py` |
| Discovery service | `backend/app/discovery/service.py` |
| Discovery workers | `backend/workers/tasks/discovery.py` |
| DB migration | `backend/migrations/versions/013_discovery_jobs.py` |
| Capability definitions | `backend/app/discovery/capabilities.py` |
| Discovery DTOs | `backend/app/discovery/schemas.py` |
| Connector SDK (v2) | `backend/connectors/sdk/` |
| SDK registry | `backend/connectors/sdk/registry.py` |
| Apollo v2 reference | `backend/connectors/apollo_v2.py` |
| Existing connectors | `backend/connectors/` (Apollo, Clearbit, Hunter) |
| v1 registry | `backend/connectors/registry.py` |

## Relationship to Prior Phases

| Phase | Focus | This Phase Extends |
|-------|-------|-------------------|
| Phase 1 | `BaseConnector`, event catalog | SDK v2, capability model |
| Phase 2 | Multi-schema DB, spatial, vectors | Discovery job tables, provenance |
| Phase 3 | Clean Architecture, API gaps | Orchestrator, worker contracts |
| Phase 4 | Lead Discovery UI | API bindings for discovery jobs |

## Implementation Roadmap

| Sprint | Scope |
|--------|-------|
| 1 | Connector SDK v2, capability registry, DTO models |
| 2 | Discovery Orchestrator MVP (parallel execution, aggregation) |
| 3 | Normalization + Entity Resolution pipelines |
| 4 | Confidence Engine + Enrichment pipeline |
| 5 | Discovery APIs, job workers, event bus integration |
| 6 | Observability, rate limiting, provider health dashboard |
| 7 | Contract tests, mock providers, load/security gates |
| 8 | Provider onboarding (Apollo, Clearbit, Hunter production) |

## Compliance & Data Ethics

- All connectors must declare **data source type** (`official_api`, `licensed_provider`, `public_registry`, `user_authorized`, `import`)
- Scraping of login-gated, ToS-prohibited, or personal data without consent is **explicitly forbidden**
- Audit trail records provider, license, and retrieval timestamp per field (field-level provenance)