# 20 — Platform Handbook

## Overview

Onboarding guide for engineers joining the AI Lead Intelligence Platform team. Covers tools, access, first-day setup, and where to find documentation — **100% free tooling**.

## Who This Is For

| Role | Focus Areas |
|------|-------------|
| Backend engineer | `backend/`, workers, connectors, API |
| Frontend engineer | `frontend/`, Next.js, API integration |
| Platform / DevOps | Docker, monitoring, tunnels, CI |
| QA | Smoke tests, health checks, test data |

## First-Day Setup (Windows)

### 1. Install Tools (All Free)

```powershell
# Package managers — use what you have
winget install Docker.DockerDesktop
winget install OpenJS.NodeJS.LTS
winget install Python.Python.3.12
winget install Git.Git
winget install Hashicorp.Terraform        # optional
winget install Cloudflare.cloudflared     # optional, for tunnels
```

### 2. Clone Repository

```powershell
git clone https://github.com/<org>/AI-Lead-intelligence-.git
cd AI-Lead-intelligence-
```

### 3. Configure Environment

```powershell
Copy-Item .env.example .env
Copy-Item frontend\.env.local.example frontend\.env.local
```

### 4. Start Platform

```powershell
.\scripts\start-free-stack.ps1 -Monitoring
```

### 5. Verify

```powershell
curl http://localhost:8000/health
Start-Process http://localhost:3000
Start-Process http://localhost:8000/api/docs
```

Login: `dev@example.com` / `DevPass123!`

### 6. Run Tests

```powershell
pip install -r requirements.txt
pytest backend/tests/ -v
cd frontend; npm ci; npm run build
```

## Tool Reference

| Tool | Purpose | Doc |
|------|---------|-----|
| Docker Compose | Local runtime | [03-docker-standards.md](./03-docker-standards.md) |
| `start-free-stack.ps1` | One-command startup | [18-operational-runbooks.md](./18-operational-runbooks.md) |
| `tunnel-dev.ps1` | Cloudflare quick tunnel | [07-networking-design.md](./07-networking-design.md) |
| Prometheus + Grafana | Metrics | [09-observability-architecture.md](./09-observability-architecture.md) |
| GitHub Actions | CI/CD | [04-cicd-pipeline.md](./04-cicd-pipeline.md) |
| Terraform | Cloudflare DNS | [06-iac-strategy.md](./06-iac-strategy.md) |
| k3d / minikube | K8s practice | [02-kubernetes-architecture.md](./02-kubernetes-architecture.md) |
| Alembic | DB migrations | `backend/migrations/` |
| Celery | Background jobs | `backend/workers/` |
| pytest | Backend tests | `backend/tests/` |

## Repository Map

```
AI-Lead-intelligence-/
├── backend/                 # FastAPI application
│   ├── app/                 # Domain modules (auth, discovery, crm, ...)
│   ├── connectors/          # External data connectors + SDK
│   ├── infrastructure/      # Cache, observability, repositories
│   ├── workers/             # Celery tasks
│   ├── migrations/          # Alembic
│   └── tests/
├── frontend/                # Next.js UI
├── scripts/                 # Ops and seed scripts
├── infra/
│   ├── monitoring/          # Prometheus, Grafana configs
│   └── terraform/cloudflare/
├── docs/                    # All phase documentation
├── docker-compose.yml
├── docker-compose.monitoring.yml
├── Dockerfile
└── .github/workflows/       # CI/CD
```

## Documentation Index by Phase

| Phase | Path | Topic |
|-------|------|-------|
| Architecture | `docs/architecture.md` | Enterprise architecture |
| Phase 2 | `docs/phase2/` | Database design |
| Phase 3 | `docs/phase3/` | Backend architecture |
| Phase 4 | `docs/phase4/` | Frontend architecture |
| Phase 5 | `docs/phase5/` | Discovery platform |
| Frontend v3 | `docs/frontend-v3/` | UI design system |
| **Phase 11** | `docs/phase11/` | **Platform ops (this handbook)** |

Start with [README.md](./README.md) in Phase 11 for ops quick start.

## Development Workflows

### Feature Development

```powershell
git checkout -b feat/my-feature main
# develop locally with hot reload (api volume mount)
pytest backend/tests/ -v
git push -u origin feat/my-feature
# Open PR — CI runs automatically
```

### API Exploration

- Swagger UI: http://localhost:8000/api/docs
- Health: http://localhost:8000/health
- Metrics: http://localhost:8000/metrics

### Discovery Local Test

```powershell
python backend\scripts\test_discovery_local.py
```

Uses mock connectors when `USE_MOCK_CONNECTORS=true`.

## Key Environment Variables

| Variable | Dev Default | Notes |
|----------|-------------|-------|
| `USE_MOCK_CONNECTORS` | `true` | Avoid paid API calls |
| `ENABLE_AI_SCORING` | `true` | Disable to skip LLM calls |
| `DEBUG` | `false` | Set `true` for verbose errors |
| `DATABASE_URL` | localhost / db | Host vs container |

Full list: `.env.example`

## Code Standards

| Area | Tool | CI Job |
|------|------|--------|
| Python lint | ruff | `lint-backend` |
| Python security | bandit, pip-audit | `security-scan` |
| TypeScript | tsc, ESLint | `lint-frontend` |
| Tests | pytest | `test-backend` |

## Getting Help

| Question | Where to Look |
|----------|---------------|
| How do I start the stack? | [18-operational-runbooks.md](./18-operational-runbooks.md) |
| API is down | [19-incident-response.md](./19-incident-response.md) |
| How do connectors work? | `docs/phase5/connector-developer-guide.md` |
| Database schema | `docs/phase2/database-design.md` |
| Release process | [17-release-management.md](./17-release-management.md) |
| Security expectations | [08-security-architecture.md](./08-security-architecture.md) |

## Access Checklist (Team Lead Provides)

- [ ] GitHub repo access
- [ ] GitHub Environment secrets (if deploying)
- [ ] Cloudflare account (if managing DNS/tunnels)
- [ ] Connector API keys (staging only, via secure channel)
- [ ] Staging VM SSH key (if applicable)
- [ ] Grafana credentials (change defaults on shared hosts)

**Never share secrets in Slack/email plaintext** — use team password manager.

## 30-Day Onboarding Goals

| Week | Goals |
|------|-------|
| 1 | Run stack locally, pass health checks, run tests |
| 2 | Ship small PR, understand CI pipeline |
| 3 | Trace discovery job end-to-end (API → worker → DB) |
| 4 | Shadow on-call: run backup, read Grafana dashboards |

## Contributing to Ops Docs

Phase 11 docs live in `docs/phase11/`. Update via PR when:

- Scripts change (`scripts/start-free-stack.ps1`)
- Compose services added/removed
- New monitoring dashboards
- Incident learnings

## Related Documents

- [README.md](./README.md) — Phase 11 index and quick start
- [01-cloud-architecture.md](./01-cloud-architecture.md) — architecture overview
- [15-cost-optimization.md](./15-cost-optimization.md) — $0 stack philosophy