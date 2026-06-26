# AI Lead Intelligence Platform

Enterprise-grade SaaS platform for B2B lead discovery, enrichment, AI scoring, and CRM integration.

## Tech Stack

| Layer | Technology |
|---|---|
| Backend | FastAPI + Python 3.12 |
| ORM | SQLAlchemy 2.x (async) |
| Database | PostgreSQL 16+ (pgvector) |
| Cache | Redis 7 |
| Queue | Celery + Redis |
| Search | OpenSearch 2.x |
| Storage | S3-compatible |
| Auth | JWT + OAuth2 + Refresh Tokens |
| Deploy | Docker + Kubernetes |
| Observability | Prometheus + Grafana + OpenTelemetry |

## Quick Start

```bash
cp .env.example .env
# Edit .env with your values
docker-compose up -d
make migrate
make seed
make dev
```

## Development

```bash
make dev          # Run API server with hot reload
make worker       # Run Celery worker
make beat         # Run Celery beat scheduler
make test         # Run test suite
make lint         # Run ruff + mypy
make format       # Auto-format code
make migrate      # Apply migrations
make makemigrations message="your message"  # Create new migration
```

## Project Structure

```
backend/
├── app/
│   ├── auth/          # Authentication & authorization
│   ├── users/         # User management
│   ├── organizations/ # Multi-tenant organization management
│   ├── companies/     # Company intelligence
│   ├── contacts/      # Contact intelligence
│   ├── search/        # Natural language & filter search
│   ├── enrichment/    # Data enrichment pipelines
│   ├── ai/            # AI scoring & recommendations
│   ├── crm/           # CRM (leads, deals, pipelines)
│   ├── exports/       # Export & import jobs
│   ├── notifications/ # Multi-channel notifications
│   ├── integrations/  # Connector configs
│   ├── billing/       # Subscriptions & credits
│   ├── analytics/     # Usage analytics
│   ├── admin/         # Admin operations
│   └── common/        # Shared utilities
├── workers/           # Celery async workers
├── connectors/        # Data source connector framework
├── migrations/        # Alembic migrations
└── tests/             # Test suite
```

## Architecture

See [docs/architecture.md](docs/architecture.md) for the full architecture document.

## API Documentation

Once running, visit:
- Swagger UI: http://localhost:8000/api/docs
- ReDoc: http://localhost:8000/api/redoc
- OpenAPI JSON: http://localhost:8000/api/openapi.json
