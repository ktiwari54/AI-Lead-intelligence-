# 16 — Environment Configuration

## Overview

Environments are differentiated by **`.env` files**, Compose overrides, and frontend env — not by paid multi-account cloud infrastructure. Three tiers: **local**, **dev/staging**, and **production (self-hosted)**.

## Environment Matrix

| Setting | Local | Staging | Production |
|---------|-------|---------|------------|
| Hosting | Docker Desktop | Self-hosted VM | Self-hosted VM |
| `ENVIRONMENT` | `development` | `staging` | `production` |
| `DEBUG` | `true` | `false` | `false` |
| `USE_MOCK_CONNECTORS` | `true` | `false` | `false` |
| DB host port | Published `5432` | Internal only | Internal only |
| Ingress | localhost | Named CF tunnel | Named CF tunnel |
| Monitoring | Optional profile | Enabled | Enabled |
| Log format | Text | JSON | JSON |

## File Layout

```
AI-Lead-intelligence-/
├── .env.example          # Template — commit to git
├── .env                  # Local secrets — NEVER commit
├── docker-compose.yml    # Base stack
├── docker-compose.monitoring.yml
├── docker-compose.staging.yml   # Optional override (create as needed)
├── frontend/
│   ├── .env.local.example
│   └── .env.local        # Frontend local — NEVER commit
```

## Bootstrap Local Environment

```powershell
cd C:\Users\PC\AI-Lead-intelligence-
Copy-Item .env.example .env
Copy-Item frontend\.env.local.example frontend\.env.local
```

### Key Variables (`.env.example`)

```ini
ENVIRONMENT=development
DEBUG=false
SECRET_KEY=change-this-to-a-secure-random-string-in-production

DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/ai_lead_intel
REDIS_URL=redis://localhost:6379/0
CELERY_BROKER_URL=redis://localhost:6379/1
CELERY_RESULT_BACKEND=redis://localhost:6379/2
OPENSEARCH_URL=http://localhost:9200

USE_MOCK_CONNECTORS=true
ENABLE_AI_SCORING=true
```

Docker Compose overrides URLs for in-network services:

```yaml
environment:
  DATABASE_URL: postgresql+asyncpg://postgres:postgres@db:5432/ai_lead_intel
  REDIS_URL: redis://redis:6379/0
```

Host tools (`pytest`, `alembic`) use `localhost` from `.env`; containers use service names from Compose `environment` block.

## Frontend Environment

`frontend/.env.local`:

```ini
NEXT_PUBLIC_API_URL=http://localhost:8000/api/v1
```

Staging with tunnel:

```ini
NEXT_PUBLIC_API_URL=https://api.yourdomain.com/api/v1
```

Rebuild or restart `npm run dev` after changes.

## Staging Compose Override

Create `docker-compose.staging.yml`:

```yaml
services:
  api:
    image: ghcr.io/<org>/AI-Lead-intelligence-:sha-latest
    command: uvicorn backend.main:app --host 0.0.0.0 --port 8000
    volumes: []   # no bind mount
    environment:
      ENVIRONMENT: staging
      DEBUG: "false"
    ports: []     # tunnel only

  db:
    ports: []     # no public exposure

  redis:
    ports: []
```

Start staging:

```powershell
docker compose -f docker-compose.yml -f docker-compose.staging.yml `
  -f docker-compose.monitoring.yml --profile monitoring up -d
```

## Production Differences

| Variable | Production Value |
|----------|------------------|
| `SECRET_KEY` | 64+ char random string |
| `DEBUG` | `false` |
| `ALLOWED_HOSTS` | `["api.yourdomain.com"]` |
| `DATABASE_URL` | Strong password, no host port |
| `USE_MOCK_CONNECTORS` | `false` |
| OpenSearch | Enable security plugin |

Generate secret:

```powershell
python -c "import secrets; print(secrets.token_urlsafe(64))"
```

## GitHub Environments

Configure in repo → Settings → Environments:

| Environment | Secrets |
|-------------|---------|
| `staging` | `DEPLOY_SSH_KEY`, `DEPLOY_HOST` |
| `production` | Same + required reviewers |

Used by `.github/workflows/cd.yml` deploy jobs.

## Feature Flags

From `.env.example`:

```ini
ENABLE_AI_SCORING=true
ENABLE_EMAIL_VERIFICATION=true
ENABLE_PHONE_VALIDATION=true
```

CI disables AI for speed:

```yaml
ENABLE_AI_SCORING: "false"
```

## Database Migrations Per Environment

```powershell
# Local against Docker db
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_lead_intel"
alembic upgrade head

# Inside api container
docker compose exec api alembic upgrade head
```

## Seed Data

```powershell
# SQL init on first db start
# scripts/init_db.sql mounted in docker-compose.yml

# Python seed
python scripts/seed/seed_data.py
```

## Validation Script

```powershell
# Verify required env vars are set
$required = @("SECRET_KEY", "DATABASE_URL", "REDIS_URL")
foreach ($key in $required) {
    if (-not (Select-String -Path .env -Pattern "^$key=")) {
        Write-Warning "Missing $key in .env"
    }
}
curl http://localhost:8000/health
```

## Environment Promotion

```
.env.example (git) → developer .env (local)
                   → staging .env (VM, manual)
                   → production .env (VM, manual, stricter values)
```

Never promote `.env` via git. Document new keys in `.env.example` via PR.

## Related Documents

- [05-gitops-guide.md](./05-gitops-guide.md) — promotion workflow
- [08-security-architecture.md](./08-security-architecture.md) — secret handling
- [17-release-management.md](./17-release-management.md) — release to production