# 05 — GitOps Guide (No Paid ArgoCD)

## Overview

GitOps means **git is the source of truth** for infrastructure and application configuration. This guide uses branch strategy, pull requests, and GitHub Actions — not paid ArgoCD Cloud or Flux enterprise features.

## Branch Strategy

```
main (protected) ──────► staging deploy (auto via CD workflow)
  │
  ├── develop ─────────► integration branch (optional)
  │
  ├── feat/* ──────────► feature branches → PR to main
  ├── fix/* ───────────► bugfix branches → PR to main
  └── claude/* ────────► CI runs (configured in ci.yml)
```

| Branch | Purpose | Deploy Target |
|--------|---------|---------------|
| `main` | Production-ready code | Staging (Compose on VM) |
| `develop` | Long-lived integration | Local / shared dev |
| `feat/<name>` | Feature work | Local only |
| `v*.*.*` tag on `main` | Release | Production |

## Environment Promotion Flow

```
Local Dev (Compose)
    │ PR + CI green
    ▼
main branch merge
    │ CD: build → GHCR
    ▼
Staging (self-hosted VM + Compose)
    │ Manual validation + tag vX.Y.Z
    ▼
Production (same VM or second host)
```

No automatic production deploy without a semver tag — enforced in `.github/workflows/cd.yml`:

```yaml
deploy-production:
  if: startsWith(github.ref, 'refs/tags/v')
  environment: production
```

## Configuration as Code

| Asset | Location | Promotion Method |
|-------|----------|------------------|
| Application code | `backend/`, `frontend/` | PR merge |
| Docker Compose | `docker-compose.yml` | PR merge |
| Monitoring | `docker-compose.monitoring.yml`, `infra/monitoring/` | PR merge |
| Terraform DNS | `infra/terraform/cloudflare/` | PR + `terraform apply` |
| Environment vars | `.env.example` (template only) | PR; secrets stay on host |

**Rule:** Never commit `.env`. Update `.env.example` when adding new variables.

## Pull Request Workflow

1. Create branch from `main`.
2. Make changes; test locally:

```powershell
.\scripts\start-free-stack.ps1 -Monitoring
pytest backend/tests/ -v
```

3. Open PR — CI runs automatically:
   - `ci.yml` — lint, test, build
   - `pr-checks.yml` — additional gates
   - `free-stack-smoke.yml` — Compose health

4. Require green checks + review (CODEOWNERS optional).
5. Squash merge to `main`.
6. CD workflow builds and pushes image to GHCR.

## Declarative Deploy on Self-Hosted VM

GitOps-style deploy without ArgoCD:

### Option A: SSH + Compose Pull

On the VM, clone repo once:

```bash
git clone https://github.com/<org>/AI-Lead-intelligence-.git /opt/ai-lead
cd /opt/ai-lead
cp .env.example .env   # configure once
```

CD job or manual deploy:

```bash
cd /opt/ai-lead
git pull origin main
docker compose pull api worker
docker compose up -d api worker beat
docker compose ps
curl -sf http://localhost:8000/health
```

### Option B: Watchtower (Open Source)

Auto-pull new images on a schedule:

```yaml
# Add to docker-compose on VM only
watchtower:
  image: containrrr/watchtower
  volumes:
    - /var/run/docker.sock:/var/run/docker.sock
  environment:
    WATCHTOWER_POLL_INTERVAL: 300
    WATCHTOWER_CLEANUP: "true"
```

### Option C: GitHub Actions SSH Deploy

```yaml
- name: Deploy via SSH
  uses: appleboy/ssh-action@v1
  with:
    host: ${{ secrets.DEPLOY_HOST }}
    username: deploy
    key: ${{ secrets.DEPLOY_SSH_KEY }}
    script: |
      cd /opt/ai-lead && git pull && docker compose up -d --pull always
```

## Drift Detection (Manual, Free)

Weekly operator checklist:

```powershell
# On VM — compare running image to latest GHCR tag
docker compose images
git log -1 --oneline
curl http://localhost:8000/health
```

Document drift in issue tracker if VM was patched manually.

## Rollback Procedure

```powershell
# On VM
git checkout <previous-sha>
docker compose up -d api worker

# Or pin image tag in compose override:
# image: ghcr.io/org/repo:sha-abc1234
```

For production tags, redeploy previous semver:

```powershell
git checkout v1.2.2
docker compose up -d
```

## Flux / ArgoCD (Optional, Self-Hosted)

If you later adopt K8s on owned hardware:

| Tool | Cost | Use |
|------|------|-----|
| Argo CD | Free (self-hosted) | Sync K8s manifests from git |
| Flux CD | Free (CNCF) | GitOps for Helm/Kustomize |

Not required for Docker Compose workflow. Document manifests in `infra/k8s/` when ready.

## Feature Flags in Git

Runtime flags live in `.env` (not git):

```ini
ENABLE_AI_SCORING=true
USE_MOCK_CONNECTORS=true
```

Promote flag changes per environment by updating host `.env`, not by merging secrets.

## PR Template

Use `.github/PULL_REQUEST_TEMPLATE.md`. Include:

- [ ] CI green
- [ ] `.env.example` updated if new env vars
- [ ] Smoke test passed locally
- [ ] Runbook updated if operational change

## Related Documents

- [04-cicd-pipeline.md](./04-cicd-pipeline.md) — workflow details
- [16-environment-configuration.md](./16-environment-configuration.md) — per-env config
- [17-release-management.md](./17-release-management.md) — tagging and releases