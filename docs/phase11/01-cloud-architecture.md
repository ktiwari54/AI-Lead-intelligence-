# 01 — Cloud Architecture (Free Stack)

## Overview

The AI Lead Intelligence Platform runs on a **self-hosted, zero-cost development stack** with optional free Cloudflare edge services. There is no dependency on paid cloud compute for local development or small-team staging.

## Architecture Diagram

```
                    ┌─────────────────────────────────────┐
                    │     Cloudflare Free (Edge)          │
                    │  • DNS (if you own a domain)        │
                    │  • Basic WAF / DDoS (proxied DNS)   │
                    │  • cloudflared tunnel (ingress)     │
                    └──────────────┬──────────────────────┘
                                   │ HTTPS
                    ┌──────────────▼──────────────────────┐
                    │  Developer Machine / Self-Hosted VM │
                    │  ┌─────────────────────────────┐  │
                    │  │  Docker Compose Network     │  │
                    │  │                             │  │
                    │  │  api:8000 ──► FastAPI       │  │
                    │  │  worker ─────► Celery       │  │
                    │  │  beat ───────► Celery Beat  │  │
                    │  │  db:5432 ────► PostgreSQL   │  │
                    │  │  redis:6379 ─► Redis        │  │
                    │  │  opensearch ─► OpenSearch   │  │
                    │  └─────────────────────────────┘  │
                    │  ┌─────────────────────────────┐  │
                    │  │  Monitoring (profile)       │  │
                    │  │  prometheus:9090            │  │
                    │  │  grafana:3001               │  │
                    │  │  redis/postgres exporters   │  │
                    │  └─────────────────────────────┘  │
                    │  Frontend (host): localhost:3000    │
                    └───────────────────────────────────┘
```

## Service Topology

| Service | Image / Build | Port | Role |
|---------|---------------|------|------|
| `api` | `Dockerfile` | 8000 | FastAPI REST + `/health` + `/metrics` |
| `worker` | `Dockerfile` | — | Celery async tasks (discovery, scoring) |
| `beat` | `Dockerfile` | — | Scheduled Celery jobs |
| `db` | `pgvector/pgvector:pg16` | 5432 | Primary datastore + vectors |
| `redis` | `redis:7-alpine` | 6379 | Cache, Celery broker/backend |
| `opensearch` | `opensearchproject/opensearch:2.17.0` | 9200 | Full-text search index |
| `prometheus` | `prom/prometheus:v2.55.1` | 9090 | Metrics collection (profile) |
| `grafana` | `grafana/grafana:11.4.0` | 3001 | Dashboards (profile) |

Defined in `docker-compose.yml` and `docker-compose.monitoring.yml`.

## Ingress Options (All Free)

### Option A: Local Only (Default)

No external exposure. Use `http://localhost:8000` and `http://localhost:3000`.

```powershell
.\scripts\start-free-stack.ps1
```

### Option B: Cloudflare Quick Tunnel (No Domain)

Instant `*.trycloudflare.com` URLs — ideal for demos and webhook testing.

```powershell
.\scripts\cloudflare\tunnel-dev.ps1 -Target both
# Or bundled with stack start:
.\scripts\start-free-stack.ps1 -Tunnel
```

Install `cloudflared` if missing:

```powershell
winget install --id Cloudflare.cloudflared
```

### Option C: Named Tunnel + Free DNS

If you have a domain on Cloudflare Free:

1. Create a named tunnel in Cloudflare Zero Trust dashboard (free).
2. Point `api.yourdomain.com` and `app.yourdomain.com` CNAMEs to `{tunnel-id}.cfargotunnel.com`.
3. Manage DNS with Terraform: `infra/terraform/cloudflare/main.tf`.

```powershell
cd infra\terraform\cloudflare
$env:CLOUDFLARE_API_TOKEN = "your-token"
terraform init
terraform plan
terraform apply
```

## Data Flow

```
Browser → Frontend (Next.js :3000)
       → API (:8000/api/v1/*)
       → PostgreSQL (persistent)
       → Redis (cache + queue)
       → Celery Worker (background)
       → OpenSearch (search index)
       → External Connectors (Apollo, Clearbit — API keys in .env)
```

## Health & Readiness

| Endpoint | Purpose |
|----------|---------|
| `GET /health` | Full dependency check (db, redis, opensearch) |
| `GET /health/live` | Liveness — process is running |
| `GET /health/ready` | Readiness — can serve traffic |
| `GET /metrics` | Prometheus scrape target |

Implementation: `backend/app/common/health.py`, `backend/main.py`.

## Image Registry (Free)

GitHub Container Registry (GHCR) is used by `.github/workflows/cd.yml`:

```
ghcr.io/<org>/AI-Lead-intelligence-:sha-<commit>
ghcr.io/<org>/AI-Lead-intelligence-:v1.2.3
```

GHCR is free for public packages; private repos included in GitHub plan.

## Environment Tiers

| Tier | Hosting | Ingress | Cost |
|------|---------|---------|------|
| **Local** | Docker Desktop on Windows | localhost | $0 |
| **Dev tunnel** | Same + cloudflared | `*.trycloudflare.com` | $0 |
| **Staging** | Self-hosted VM or homelab | Named Cloudflare tunnel | $0 (+ hardware) |
| **Production (small)** | Self-hosted / VPS you already own | Cloudflare Free + tunnel | $0 software |

## What We Deliberately Avoid

- Paid Cloudflare plans (Workers paid tiers, advanced WAF rulesets)
- Managed Kubernetes (EKS, GKE, AKS)
- Managed databases (RDS, Cloud SQL)
- Paid observability SaaS

Use open-source equivalents running in Docker instead.

## Startup Checklist

```powershell
# 1. Environment
Copy-Item .env.example .env

# 2. Core stack
docker compose up -d

# 3. Verify
curl http://localhost:8000/health
curl http://localhost:8000/metrics

# 4. Optional monitoring
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml --profile monitoring up -d

# 5. Optional tunnel
.\scripts\cloudflare\tunnel-dev.ps1 -Target api
```

## Related Documents

- [07-networking-design.md](./07-networking-design.md) — Docker networks and tunnel config
- [08-security-architecture.md](./08-security-architecture.md) — Edge security on free tier
- [16-environment-configuration.md](./16-environment-configuration.md) — `.env` per environment