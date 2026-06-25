# AI Lead Intelligence Platform — Architecture Document

## Phase 1: Enterprise Software Architecture & Database Design

### 1. Architecture Goals

| Goal | Implementation |
|------|----------------|
| Multi-Tenant SaaS | Row-level `organization_id` on all tables |
| API First | FastAPI with OpenAPI 3.1 docs |
| AI Native | Celery scoring tasks + Anthropic/OpenAI integration |
| Cloud Native | Docker + Kubernetes, S3-compatible storage |
| Event Driven | Domain events via Celery tasks and message queue |
| Modular Design | Bounded contexts per domain module |
| High Availability | PostgreSQL pool, Redis cluster, worker autoscaling |
| Horizontal Scalability | Stateless API + worker pods |
| High Performance | <300ms cached reads, Redis cache layer |
| Secure by Design | JWT + bcrypt + API keys + soft deletes |

### 2. Layer Architecture

```
Presentation Layer   →  Next.js (Phase 2)
Application Layer    →  FastAPI routers + schemas
Domain Layer         →  Services (business logic)
Infrastructure Layer →  SQLAlchemy models + Redis + Celery
Persistence Layer    →  PostgreSQL 16 (pgvector)
```

### 3. Domain Modules

| Module | Tables | Key Responsibility |
|--------|--------|-----------------------|
| auth | users, refresh_tokens, api_keys | Authentication & authorization |
| organizations | organizations | Multi-tenant context |
| users | users, roles, permissions, role_permissions | User & RBAC management |
| companies | companies, company_social_profiles, company_technologies | Company intelligence |
| contacts | contacts, contact_social_profiles | Contact intelligence |
| search | searches, search_results, saved_searches | Search execution & history |
| ai | lead_scores | AI scoring & ranking |
| enrichment | email_verifications | Data enrichment pipelines |
| crm | pipelines, deals, tasks, tags, notes, activities, lists | CRM functionality |
| billing | subscriptions, credit_transactions | Credits & subscriptions |
| notifications | notifications | Multi-channel notifications |
| exports | exports, import_jobs | Data export/import |
| integrations | connector_configs, connector_jobs | External connector management |
| admin | audit_logs, system_settings, feature_flags, workflows | Platform administration |

### 4. Caching Strategy (Redis)

- Company & Contact profiles: TTL 1 hour
- Industry/Country/Technology reference data: TTL 24 hours
- Permission sets per user: TTL 15 minutes
- Popular search results: TTL 5 minutes
- Organization settings: TTL 1 hour

### 5. Event Catalog

| Event | Publisher | Subscribers |
|-------|-----------|-------------|
| company.created | Company service | Scoring, Search index |
| contact.created | Contact service | Scoring, Email verify |
| lead.scored | Scoring worker | Notifications |
| search.completed | Search worker | Analytics |
| export.generated | Export worker | Notifications |
| email.verified | Enrichment worker | Contact service |
| connector.finished | Connector engine | Analytics, Notifications |

### 6. Connector Framework

Every connector implements `BaseConnector`:
- `authenticate()` — OAuth/API key handshake
- `search(query, filters)` — discovery queries
- `lookup(id, type)` — single-record fetch
- `enrich(data)` — data augmentation
- `normalize(raw)` — canonical schema mapping
- `health_check()` — availability probe
- `get_rate_limit()` — quota introspection
- `retry(fn, ...)` — exponential backoff

Connectors are registered with `ConnectorRegistry` and resolved by name.

### 7. Database Design Principles

- Third Normal Form (3NF) throughout
- UUID v4 primary keys (`gen_random_uuid()`)
- UTC timestamps on all tables
- Soft deletes via `deleted_at` on all tables
- JSONB only for genuinely flexible metadata
- `pg_trgm` trigram indexes for full-text search
- Composite indexes for common filter combinations
- Foreign keys with appropriate `ondelete` behavior

### 8. Security Architecture

- Passwords: bcrypt with cost factor 12
- Access tokens: JWT RS256, 60-minute expiry
- Refresh tokens: stored as SHA-256 hash, rotated on use
- API keys: stored as SHA-256 hash, prefixed with `ali_`
- All secrets via environment variables (never in code)
- Row-level security enforced at application layer
- Audit log on all mutating operations
