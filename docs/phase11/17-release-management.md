# 17 — Release Management

## Overview

Releases use **Semantic Versioning (semver)** and **GitHub Releases** (free) to tag production-ready builds. Container images publish to GHCR via `.github/workflows/cd.yml`.

## Versioning Scheme

```
MAJOR.MINOR.PATCH
  │      │      └── Bug fixes, no API breakage
  │      └───────── New features, backward compatible
  └──────────────── Breaking changes

Pre-release: v1.3.0-rc.1
```

Align with `APP_VERSION` in `.env.example` when cutting releases.

## Branch → Release Flow

```
feat/* → PR → main → staging deploy (automatic image push)
                    → manual QA on staging
                    → git tag v1.2.3 → production deploy
```

## Creating a Release

### 1. Prepare Release Branch (Optional)

```powershell
git checkout main
git pull origin main
# Ensure CI green on main
```

### 2. Update Version References

- `APP_VERSION` in `.env.example`
- `frontend/package.json` version (if applicable)
- CHANGELOG entry (if maintaining CHANGELOG.md)

### 3. Tag and Push

```powershell
git tag -a v1.2.3 -m "Release v1.2.3: discovery improvements"
git push origin v1.2.3
```

### 4. CD Workflow Triggers

`.github/workflows/cd.yml` on `v*.*.*` tags:

- Builds Docker image
- Pushes to `ghcr.io/<org>/AI-Lead-intelligence-:1.2.3`
- Runs `deploy-production` job (configure SSH deploy commands)

### 5. GitHub Release (UI)

1. GitHub → Releases → **Draft a new release**
2. Choose tag `v1.2.3`
3. Title: `v1.2.3`
4. Description: changelog bullets
5. Attach optional artifacts (SQL migration notes)
6. Publish release — **free on all GitHub plans**

### GitHub CLI Alternative

```powershell
gh release create v1.2.3 --title "v1.2.3" --notes "See changelog"
```

## Image Tags Produced

| Event | Tags |
|-------|------|
| Push to `main` | `sha-<commit>`, branch name |
| Tag `v1.2.3` | `1.2.3`, `1.2`, `sha-<commit>` |

From `docker/metadata-action` in `cd.yml`:

```yaml
tags: |
  type=semver,pattern={{version}}
  type=semver,pattern={{major}}.{{minor}}
  type=sha,prefix=sha-
```

## Deploy Production Release

On self-hosted VM:

```powershell
cd C:\opt\ai-lead
git fetch --tags
git checkout v1.2.3

# Pull immutable image
$env:API_IMAGE = "ghcr.io/<org>/AI-Lead-intelligence-:1.2.3"
docker compose -f docker-compose.yml -f docker-compose.staging.yml pull
docker compose up -d api worker beat

curl http://localhost:8000/health
```

## Database Migrations in Releases

**Before** switching traffic to new version:

```powershell
docker compose exec api alembic upgrade head
```

Rollback migration if needed:

```powershell
docker compose exec api alembic downgrade -1
```

Include migration notes in GitHub Release body.

## Release Checklist

- [ ] All CI workflows green on `main`
- [ ] `free-stack-smoke.yml` passed
- [ ] Staging validated manually
- [ ] `.env.example` documents any new variables
- [ ] Alembic migrations tested
- [ ] Backup taken before production deploy ([12-backup-restore.md](./12-backup-restore.md))
- [ ] Tag signed (optional): `git tag -s v1.2.3`
- [ ] GitHub Release published
- [ ] Production health check passed
- [ ] Grafana dashboards show normal metrics

## Hotfix Process

```powershell
git checkout -b fix/critical-bug main
# fix, PR, merge to main
git tag v1.2.4
git push origin v1.2.4
```

Cherry-pick to avoid unrelated changes:

```powershell
git cherry-pick <commit-sha>
```

## Rollback Release

```powershell
git checkout v1.2.2
docker compose up -d api worker
# Consider alembic downgrade if schema changed
```

Document rollback in incident channel.

## Changelog Format (Recommended)

```markdown
## [1.2.3] - 2026-06-28
### Added
- Discovery job retry policy
### Fixed
- Redis connection leak in worker
### Changed
- Prometheus scrape interval 15s → 30s
```

## Pre-Release Builds

```powershell
git tag v1.3.0-rc.1
git push origin v1.3.0-rc.1
```

CD can deploy RC to staging only via workflow condition:

```yaml
if: contains(github.ref, '-rc.')
```

## Related Documents

- [04-cicd-pipeline.md](./04-cicd-pipeline.md) — CD workflow details
- [05-gitops-guide.md](./05-gitops-guide.md) — promotion strategy
- [18-operational-runbooks.md](./18-operational-runbooks.md) — deploy runbook