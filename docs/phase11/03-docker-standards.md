# 03 — Docker Standards

## Overview

All backend services (`api`, `worker`, `beat`) share a single multi-purpose image built from the root `Dockerfile`. Standards emphasize reproducibility, security basics, and health verification — without paid registry or scanning services.

## Dockerfile Structure

Current `Dockerfile` at repo root:

| Stage / Section | Purpose |
|-----------------|---------|
| Base `python:3.12-slim` | Minimal attack surface |
| System deps | `build-essential`, `libpq-dev`, `curl` (health check) |
| `requirements.txt` | Pinned Python dependencies |
| `COPY . .` | Application code |
| `HEALTHCHECK` | `curl -f http://localhost:8000/health` |
| `CMD` | Production uvicorn (no `--reload`) |

### Production vs Development Command

`docker-compose.yml` overrides the CMD for dev:

```yaml
# api service — hot reload in development
command: uvicorn backend.main:app --host 0.0.0.0 --port 8000 --reload
volumes:
  - ./backend:/app/backend
```

Production deployments should use the Dockerfile default CMD without volume mounts.

## Multi-Stage Build (Recommended Enhancement)

For smaller production images, adopt a two-stage pattern:

```dockerfile
# Stage 1: builder
FROM python:3.12-slim AS builder
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends build-essential libpq-dev
COPY requirements.txt .
RUN pip install --no-cache-dir --prefix=/install -r requirements.txt

# Stage 2: runtime
FROM python:3.12-slim AS runtime
WORKDIR /app
RUN apt-get update && apt-get install -y --no-install-recommends libpq5 curl \
    && rm -rf /var/lib/apt/lists/* \
    && useradd --create-home --uid 10001 appuser
COPY --from=builder /install /usr/local
COPY . .
USER appuser
ENV PYTHONDONTWRITEBYTECODE=1 PYTHONUNBUFFERED=1 PYTHONPATH=/app
EXPOSE 8000
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
CMD ["uvicorn", "backend.main:app", "--host", "0.0.0.0", "--port", "8000"]
```

## Non-Root Container

| Rule | Implementation |
|------|----------------|
| Run as non-root | `USER appuser` (UID 10001) in Dockerfile |
| No root in Compose | Add `user: "10001:10001"` when not mounting host volumes |
| Read-only root FS | Optional in K8s: `securityContext.readOnlyRootFilesystem: true` |

**Note:** Dev Compose bind-mounts `./backend` — keep root for write access during local dev only.

## Health Checks

### Dockerfile HEALTHCHECK

```dockerfile
HEALTHCHECK --interval=30s --timeout=10s --start-period=5s --retries=3 \
    CMD curl -f http://localhost:8000/health || exit 1
```

### Compose Service Health (Data Stores)

From `docker-compose.yml`:

```yaml
db:
  healthcheck:
    test: ["CMD-SHELL", "pg_isready -U postgres"]
    interval: 5s
    timeout: 5s
    retries: 5

redis:
  healthcheck:
    test: ["CMD", "redis-cli", "ping"]
    interval: 5s
    timeout: 3s
    retries: 5

opensearch:
  healthcheck:
    test: ["CMD-SHELL", "curl -sf http://localhost:9200/_cluster/health || exit 1"]
    interval: 10s
    timeout: 5s
    retries: 12
    start_period: 30s
```

API depends on healthy `db` and `redis`:

```yaml
depends_on:
  db:
    condition: service_healthy
  redis:
    condition: service_healthy
```

## Image Tagging Convention

| Tag | When |
|-----|------|
| `ai-lead-intelligence:local` | Local builds |
| `ai-lead-intelligence:sha-<git-sha>` | CI build (`.github/workflows/ci.yml`) |
| `ghcr.io/<org>/repo:sha-<sha>` | CD push to GHCR |
| `ghcr.io/<org>/repo:v1.2.3` | Semver release tag |

## Build Commands

```powershell
# Local build
docker build -t ai-lead-intelligence:local .

# Build with BuildKit cache
$env:DOCKER_BUILDKIT = "1"
docker build --progress=plain -t ai-lead-intelligence:local .

# Verify health after run
docker run -d --name api-test -p 8000:8000 `
  -e DATABASE_URL=postgresql+asyncpg://postgres:postgres@host.docker.internal:5432/ai_lead_intel `
  -e REDIS_URL=redis://host.docker.internal:6379/0 `
  ai-lead-intelligence:local

curl http://localhost:8000/health
docker rm -f api-test
```

## Compose Profiles

| Profile | File | Services |
|---------|------|----------|
| `default` | `docker-compose.yml` | api, worker, beat, db, redis, opensearch |
| `monitoring` | `docker-compose.monitoring.yml` | prometheus, grafana, exporters |

```powershell
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml --profile monitoring up -d
```

## Volume Standards

| Volume | Service | Data |
|--------|---------|------|
| `pgdata` | db | PostgreSQL data |
| `redisdata` | redis | Redis persistence |
| `opensearch_data` | opensearch | Search indices |
| `prometheus_data` | prometheus | TSDB |
| `grafana_data` | grafana | Dashboard state |

Named volumes survive `docker compose down`. Use `docker compose down -v` only when intentionally wiping data.

## Security Scanning (Free)

CI runs free tools in `.github/workflows/ci.yml`:

- **pip-audit** — Python dependency CVEs
- **bandit** — Python SAST

```powershell
# Run locally
pip install pip-audit bandit
pip-audit -r requirements.txt
bandit -r backend/ -ll -x backend/tests/
```

## .dockerignore Recommendations

Ensure these are excluded (create `.dockerignore` if missing):

```
.git
.env
__pycache__
*.pyc
.pytest_cache
frontend/node_modules
.mypy_cache
coverage.xml
```

## Resource Limits (Compose)

Add for production-like Compose deployments:

```yaml
api:
  deploy:
    resources:
      limits:
        cpus: "1.0"
        memory: 512M
      reservations:
        cpus: "0.25"
        memory: 256M
```

## Related Documents

- [01-cloud-architecture.md](./01-cloud-architecture.md) — service topology
- [04-cicd-pipeline.md](./04-cicd-pipeline.md) — automated image builds
- [18-operational-runbooks.md](./18-operational-runbooks.md) — start/stop procedures