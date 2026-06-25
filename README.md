# AI Lead Intelligence Platform

Enterprise-grade SaaS platform for B2B lead discovery, contact enrichment, AI scoring, and CRM integration.

## Tech Stack

| Layer | Technology |
|---|---|
| API | FastAPI 0.115 (Python 3.12) |
| ORM | SQLAlchemy 2.0 (async) |
| Database | PostgreSQL 16 |
| Cache | Redis 7 |
| Task Queue | Celery 5 + Redis |
| Migrations | Alembic |
| Auth | JWT (HS256) + bcrypt |
| Connectors | Hunter.io · Clearbit · Apollo |
| Containers | Docker + Docker Compose |

## Quick Start

```bash
# 1. Clone and configure
cp .env.example .env          # edit SECRET_KEY and DB credentials

# 2. Start services
docker-compose up -d db redis

# 3. Install dependencies
cd backend && pip install -r requirements.txt

# 4. Apply schema
alembic upgrade head
psql $DATABASE_URL -f migrations/ddl/001_create_tables.sql
psql $DATABASE_URL -f migrations/ddl/002_indexes.sql
python scripts/seed_data.py

# 5. Run API
uvicorn main:app --reload --port 8000

# 6. Run worker (separate terminal)
celery -A workers.celery_app worker --loglevel=info
```

API docs: http://localhost:8000/docs

## Domain Modules

```
backend/
├── app/
│   ├── auth/              # JWT login + registration
│   ├── users/             # Profile management
│   ├── organizations/     # Multi-tenant org management
│   ├── companies/         # Company intelligence CRUD
│   ├── contacts/          # Contact intelligence CRUD
│   ├── search/            # NL + filter-based search
│   ├── enrichment/        # Email verification + enrichment
│   ├── ai/                # Lead scoring + NL query parsing
│   ├── crm/               # Activities, notes, tags, tasks
│   ├── billing/           # Subscriptions + credits
│   ├── notifications/     # In-app notifications
│   ├── admin/             # Platform stats
│   ├── core/              # Config, DB, security, middleware
│   └── common/            # Base models, shared deps
├── models/                # All SQLAlchemy models
├── connectors/            # Clearbit, Hunter, Apollo connectors
├── workers/               # Celery: scoring, enrichment, export
├── migrations/
│   ├── ddl/               # Production SQL DDL + indexes
│   └── seed/              # Reference data seeds
├── alembic/               # Alembic env + migration versions
├── scripts/               # seed_data.py, create_indexes.py
└── tests/                 # pytest-asyncio test suite
```

## API Endpoints

| Module | Base Path |
|---|---|
| Auth | `POST /api/v1/auth/login` `POST /api/v1/auth/register` |
| Users | `GET/PATCH /api/v1/users/me` |
| Organizations | `GET/PATCH /api/v1/organizations/me` |
| Companies | `CRUD /api/v1/companies` |
| Contacts | `CRUD /api/v1/contacts` |
| Search | `POST /api/v1/search` · `POST /api/v1/search/saved` |
| Enrichment | `POST /api/v1/enrichment/email/verify` |
| AI | `POST /api/v1/ai/score` · `POST /api/v1/ai/nl-query` |
| CRM | `/api/v1/crm/activities` `/crm/notes` `/crm/tags` `/crm/tasks` |
| Billing | `GET /api/v1/billing/subscription` |
| Notifications | `GET /api/v1/notifications` |
| Admin | `GET /api/v1/admin/stats` |

## Database

- 30+ normalized tables in 3NF
- UUID primary keys throughout
- Soft delete (`is_deleted`, `deleted_at`) on every table
- UTC timestamps (`created_at`, `updated_at`)
- Full-text search via `pg_trgm` GIN indexes
- JSONB for flexible metadata only

## Connector Framework

Every connector implements `BaseConnector`:

```python
authenticate() | search() | lookup() | enrich()
health_check() | get_rate_limit() | normalize() | retry()
```

Built-in connectors: **Hunter.io**, **Clearbit**, **Apollo**

## Background Workers (Celery)

| Queue | Worker | Purpose |
|---|---|---|
| `scoring` | `lead_scoring_worker` | Score contacts & companies |
| `enrichment` | `enrichment_worker` | Enrich companies, verify emails |
| `exports` | `export_worker` | Generate CSV/XLSX exports |
| `notifications` | `notification_worker` | Deliver in-app notifications |

## Phase 2 Deliverables

The next phase will produce:

1. Complete ER Diagram
2. Alembic auto-migration plan
3. Partitioning strategy (audit_logs, search_results by date)
4. Archiving & data retention policies
5. Backup & restore runbook
6. CRM connector integrations (Salesforce, HubSpot)
7. Frontend (Next.js) with search UI
8. Observability stack (Prometheus, Grafana, OpenTelemetry)
