# Phase 11 — Platform Operations & Free Cloud Stack

**Version 1.0** | AI Lead Intelligence Platform

Phase 11 documents how to run, deploy, observe, and operate the platform using **100% free and open-source tooling**. No paid Cloudflare plans, no AWS/Azure/GCP managed services required for development or small self-hosted deployments.

## Design Principles

| Principle | Implementation |
|-----------|----------------|
| **$0 dev stack** | Docker Compose for api, worker, postgres, redis, opensearch |
| **Free edge ingress** | Cloudflare Free + `cloudflared` quick tunnels or named tunnels |
| **Open observability** | Prometheus + Grafana via `docker-compose.monitoring.yml` |
| **Free CI/CD** | GitHub Actions (public repos unlimited; private repos 2,000 min/month) |
| **IaC without lock-in** | Terraform OSS CLI + Cloudflare free provider |
| **Local K8s practice** | k3d or minikube — not required for daily dev |

## Quick Start (Windows / PowerShell)

```powershell
# Clone and enter repo
cd C:\path\to\AI-Lead-intelligence-

# Copy environment template
Copy-Item .env.example .env

# Start full free stack (Docker + frontend dev server)
.\scripts\start-free-stack.ps1

# With monitoring (Prometheus :9090, Grafana :3001)
.\scripts\start-free-stack.ps1 -Monitoring

# With Cloudflare quick tunnel for API
.\scripts\start-free-stack.ps1 -Tunnel

# Or tunnel API + frontend separately
.\scripts\cloudflare\tunnel-dev.ps1 -Target both
```

### Service URLs (Local)

| Service | URL | Credentials |
|---------|-----|-------------|
| Frontend | http://localhost:3000 | `dev@example.com` / `DevPass123!` |
| API | http://localhost:8000 | — |
| API Docs | http://localhost:8000/api/docs | — |
| Health | http://localhost:8000/health | — |
| Metrics | http://localhost:8000/metrics | — |
| Prometheus | http://localhost:9090 | — |
| Grafana | http://localhost:3001 | `admin` / `admin` |
| PostgreSQL | localhost:5432 | `postgres` / `postgres` |
| Redis | localhost:6379 | — |
| OpenSearch | http://localhost:9200 | security disabled (dev) |

### Stop Stack

```powershell
docker compose down
# If monitoring was started:
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml --profile monitoring down
```

## Documentation Index

| # | Topic | Document |
|---|-------|----------|
| 1 | Cloud Architecture (Free Stack) | [01-cloud-architecture.md](./01-cloud-architecture.md) |
| 2 | Kubernetes Architecture (Local) | [02-kubernetes-architecture.md](./02-kubernetes-architecture.md) |
| 3 | Docker Standards | [03-docker-standards.md](./03-docker-standards.md) |
| 4 | CI/CD Pipeline | [04-cicd-pipeline.md](./04-cicd-pipeline.md) |
| 5 | GitOps Guide | [05-gitops-guide.md](./05-gitops-guide.md) |
| 6 | IaC Strategy | [06-iac-strategy.md](./06-iac-strategy.md) |
| 7 | Networking Design | [07-networking-design.md](./07-networking-design.md) |
| 8 | Security Architecture | [08-security-architecture.md](./08-security-architecture.md) |
| 9 | Observability Architecture | [09-observability-architecture.md](./09-observability-architecture.md) |
| 10 | Monitoring Dashboards | [10-monitoring-dashboards.md](./10-monitoring-dashboards.md) |
| 11 | Logging Standards | [11-logging-standards.md](./11-logging-standards.md) |
| 12 | Backup & Restore | [12-backup-restore.md](./12-backup-restore.md) |
| 13 | Disaster Recovery | [13-disaster-recovery.md](./13-disaster-recovery.md) |
| 14 | Scaling Strategy | [14-scaling-strategy.md](./14-scaling-strategy.md) |
| 15 | Cost Optimization | [15-cost-optimization.md](./15-cost-optimization.md) |
| 16 | Environment Configuration | [16-environment-configuration.md](./16-environment-configuration.md) |
| 17 | Release Management | [17-release-management.md](./17-release-management.md) |
| 18 | Operational Runbooks | [18-operational-runbooks.md](./18-operational-runbooks.md) |
| 19 | Incident Response | [19-incident-response.md](./19-incident-response.md) |
| 20 | Platform Handbook | [20-platform-handbook.md](./20-platform-handbook.md) |

## Key Repository Paths

| Component | Path |
|-----------|------|
| Core Compose | `docker-compose.yml` |
| Monitoring overlay | `docker-compose.monitoring.yml` |
| Dockerfile | `Dockerfile` |
| Start script | `scripts/start-free-stack.ps1` |
| Cloudflare tunnel script | `scripts/cloudflare/tunnel-dev.ps1` |
| Prometheus config | `infra/monitoring/prometheus/prometheus.yml` |
| Grafana dashboards | `infra/monitoring/grafana/dashboards/` |
| Terraform (Cloudflare DNS) | `infra/terraform/cloudflare/` |
| GitHub Actions CI | `.github/workflows/ci.yml` |
| Smoke test workflow | `.github/workflows/free-stack-smoke.yml` |
| CD workflow | `.github/workflows/cd.yml` |
| Backend health | `backend/app/common/health.py` |
| Structured logging | `backend/infrastructure/observability/logging.py` |
| Metrics | `backend/infrastructure/observability/metrics.py` |

## Relationship to Prior Phases

| Phase | Focus | Phase 11 Extends |
|-------|-------|------------------|
| Phase 3 | Backend architecture, API | Deployment targets, health probes |
| Phase 5 | Discovery, workers, observability | Production runbooks, scaling workers |
| Phase 4/frontend-v3 | Frontend | Tunnel exposure, env-specific API URLs |

## Prerequisites (All Free)

- [Docker Desktop](https://www.docker.com/products/docker-desktop/) (free for personal/small business)
- [Node.js 20 LTS](https://nodejs.org/) (frontend)
- [Python 3.12](https://www.python.org/) (local dev without Docker)
- [cloudflared](https://developers.cloudflare.com/cloudflare-one/connections/connect-networks/downloads/) — `winget install --id Cloudflare.cloudflared`
- [Terraform](https://developer.hashicorp.com/terraform/install) (optional, for DNS)
- [k3d](https://k3d.io/) or [minikube](https://minikube.sigs.k8s.io/) (optional, K8s practice)