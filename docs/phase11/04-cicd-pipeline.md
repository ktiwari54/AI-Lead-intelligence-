# 04 — CI/CD Pipeline (GitHub Actions Free Tier)

## Overview

Continuous integration and delivery use **GitHub Actions** — free for public repositories and included minutes for private repos. No Jenkins, CircleCI, or paid CI services required.

## Workflow Inventory

| Workflow | File | Trigger | Purpose |
|----------|------|---------|---------|
| CI | `.github/workflows/ci.yml` | push/PR to main | Lint, test, build |
| PR Checks | `.github/workflows/pr-checks.yml` | pull_request | Additional PR gates |
| Free Stack Smoke | `.github/workflows/free-stack-smoke.yml` | push/PR, manual | Docker Compose health |
| CD | `.github/workflows/cd.yml` | main push, `v*` tags | Build + push GHCR |

## CI Pipeline (`ci.yml`)

```
┌─────────────┐  ┌─────────────┐
│ lint-backend│  │lint-frontend│  (parallel)
└──────┬──────┘  └──────┬──────┘
       │                │
       ▼                ▼
┌─────────────┐  ┌─────────────┐
│test-backend │  │build-frontend│
└──────┬──────┘  └─────────────┘
       │
       ▼
┌─────────────┐  ┌─────────────┐
│build-docker │  │security-scan│  (parallel)
└─────────────┘  └─────────────┘
```

### Backend Lint

```yaml
# Runs ruff check + format on backend/
ruff check backend/ --output-format=github
ruff format backend/ --check
```

### Backend Tests

Uses GitHub Actions **service containers** (free) for PostgreSQL and Redis:

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg16
  redis:
    image: redis:7-alpine
```

Runs `alembic upgrade head` then `pytest backend/tests/ -v --cov=backend`.

### Frontend

```yaml
npm ci --prefer-offline
npx tsc --noEmit
npx next lint
npm run build
```

### Docker Build (No Push)

```yaml
docker/build-push-action@v5
  push: false
  tags: ai-lead-intelligence:${{ github.sha }}
  cache-from: type=gha
  cache-to: type=gha,mode=max
```

Uses GitHub Actions cache — free, speeds up repeat builds.

### Security Scan (Free Tools)

- `pip-audit` for dependency vulnerabilities
- `bandit` for Python security linting

## Smoke Test (`free-stack-smoke.yml`)

Validates the real Compose stack:

```yaml
docker compose up -d db redis opensearch api
timeout 120 bash -c 'until curl -sf http://localhost:8000/health; do sleep 3; done'
curl -sf http://localhost:8000/health | grep -q healthy
curl -sf http://localhost:8000/metrics
docker compose down -v
```

Manual trigger:

```
GitHub → Actions → Free Stack Smoke Test → Run workflow
```

## CD Pipeline (`cd.yml`)

### Build & Push to GHCR

On `main` push and semver tags (`v*.*.*`):

```
ghcr.io/<owner>/AI-Lead-intelligence-:sha-<commit>
ghcr.io/<owner>/AI-Lead-intelligence-:1.2.3
ghcr.io/<owner>/AI-Lead-intelligence-:1.2
```

Uses `GITHUB_TOKEN` — no extra secrets for GHCR on same repo.

### Deploy Stages (Placeholder)

```yaml
deploy-staging:
  environment: staging
  if: github.ref == 'refs/heads/main'

deploy-production:
  environment: production
  if: startsWith(github.ref, 'refs/tags/v')
```

Replace echo placeholders with your self-hosted deploy commands:

```yaml
- name: Deploy to staging
  run: |
    ssh deploy@your-vm "cd /opt/ai-lead && docker compose pull api && docker compose up -d api worker"
```

## Running CI Locally (Free)

### Act (Optional)

```powershell
choco install act-cli
act -j test-backend
```

### Mirror CI Test Run

```powershell
pip install -r requirements.txt
$env:DATABASE_URL = "postgresql+asyncpg://postgres:postgres@localhost:5432/ai_lead_intel"
$env:SECRET_KEY = "test-secret"
pytest backend/tests/ -v
```

## Branch Protection (Free)

Configure in GitHub repo settings:

| Rule | Setting |
|------|---------|
| Require PR | Enabled |
| Required checks | `Lint Backend`, `Test Backend`, `Build Frontend`, `Docker Compose Smoke` |
| Require CODEOWNERS | Optional — `.github/CODEOWNERS` exists |

## Secrets Management in CI

| Secret | Used For |
|--------|----------|
| `GITHUB_TOKEN` | GHCR push (automatic) |
| `CLOUDFLARE_API_TOKEN` | Optional Terraform apply job |
| Deploy SSH key | Self-hosted VM deploy |

Never store `.env` contents in workflow files. Use GitHub Environments (`staging`, `production`) with protection rules.

## Adding a Terraform Plan Job (Optional)

```yaml
terraform-plan:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: hashicorp/setup-terraform@v3
    - run: terraform init
      working-directory: infra/terraform/cloudflare
    - run: terraform plan -input=false
      working-directory: infra/terraform/cloudflare
      env:
        CLOUDFLARE_API_TOKEN: ${{ secrets.CLOUDFLARE_API_TOKEN }}
```

Terraform CLI and Cloudflare provider are open source.

## Minute Budget Tips

| Tip | Savings |
|-----|---------|
| Cache pip and npm | Faster jobs, fewer minutes |
| `paths` filters on workflows | Skip CI when only docs change |
| Combine lint steps | One job instead of many |
| `concurrency: cancel-in-progress` | Cancel stale PR runs |

Example paths filter:

```yaml
on:
  push:
    paths-ignore:
      - 'docs/**'
      - '**.md'
```

## Related Documents

- [05-gitops-guide.md](./05-gitops-guide.md) — branch and promotion strategy
- [17-release-management.md](./17-release-management.md) — semver tags triggering CD
- [06-iac-strategy.md](./06-iac-strategy.md) — Terraform in pipeline