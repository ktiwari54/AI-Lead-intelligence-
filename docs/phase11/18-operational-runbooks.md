# 18 — Operational Runbooks

## Overview

Day-to-day operations for the **free Docker Compose stack** on Windows/PowerShell. All commands reference repo paths and scripts.

## Daily Startup

```powershell
cd C:\Users\PC\AI-Lead-intelligence-

# Full stack with monitoring
.\scripts\start-free-stack.ps1 -Monitoring

# Or Docker only (no frontend job)
docker compose up -d
```

Expected output from start script:

```
Frontend:    http://localhost:3000
API:         http://localhost:8000
Health:      http://localhost:8000/health
Grafana:     http://localhost:3001
```

Login: `dev@example.com` / `DevPass123!`

## Daily Shutdown

```powershell
# Stop containers (preserve volumes)
docker compose down

# With monitoring
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml --profile monitoring down

# Stop frontend job from start script
Get-Job | Stop-Job; Get-Job | Remove-Job
```

## Health Check Runbook

### Quick Check (< 1 minute)

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/health/ready
docker compose ps
```

Healthy response includes dependency status from `backend/app/common/health.py`.

### Full Check (5 minutes)

```powershell
# API
curl http://localhost:8000/health
curl http://localhost:8000/metrics

# Database
docker compose exec db pg_isready -U postgres

# Redis
docker compose exec redis redis-cli ping

# OpenSearch
curl http://localhost:9200/_cluster/health

# Worker
docker compose exec worker celery -A backend.workers.celery_app inspect ping

# Prometheus targets
Start-Process http://localhost:9090/targets

# Grafana
Start-Process http://localhost:3001
```

## Service Restart Runbook

| Service | Command |
|---------|---------|
| API only | `docker compose restart api` |
| Worker | `docker compose restart worker` |
| All app tier | `docker compose restart api worker beat` |
| Database | `docker compose restart db` (brief outage) |
| Full stack | `docker compose down && docker compose up -d` |

After restart:

```powershell
curl http://localhost:8000/health
```

## Logs Runbook

```powershell
# Last 100 lines, follow
docker compose logs -f api --tail 100

# Worker errors
docker compose logs worker --since 1h | Select-String "ERROR"

# Export for incident
docker compose logs --no-color > incident-logs.txt
```

## Database Runbook

### Connect

```powershell
docker compose exec db psql -U postgres -d ai_lead_intel
```

### Run Migrations

```powershell
docker compose exec api alembic upgrade head
```

### Seed Data

```powershell
python scripts\seed\seed_data.py
```

### Init SQL (first boot only)

Mounted from `scripts/init_db.sql` via Compose volume.

## Worker Queue Runbook

```powershell
# Active tasks
docker compose exec worker celery -A backend.workers.celery_app inspect active

# Queue depth (broker DB 1)
docker compose exec redis redis-cli -n 1 LLEN celery

# Scale workers
docker compose up -d --scale worker=4
```

## Monitoring Runbook

### Start Monitoring

```powershell
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml --profile monitoring up -d
```

### Reload Prometheus Config

```powershell
curl -X POST http://localhost:9090/-/reload
```

### Reset Grafana Password

```powershell
docker compose exec grafana grafana-cli admin reset-admin-password newpass
```

## Tunnel Runbook

```powershell
# Quick tunnel
.\scripts\cloudflare\tunnel-dev.ps1 -Target both

# Named tunnel
cloudflared tunnel run ai-lead-dev
```

Install cloudflared:

```powershell
winget install --id Cloudflare.cloudflared
```

## Backup Runbook (Daily on Staging)

```powershell
New-Item -ItemType Directory -Force -Path C:\backups\ai-lead
docker compose exec -T db pg_dump -U postgres -d ai_lead_intel -Fc `
  > C:\backups\ai-lead\ai_lead_intel_$(Get-Date -Format yyyyMMdd).dump
```

See [12-backup-restore.md](./12-backup-restore.md).

## Deploy New Version Runbook

```powershell
cd C:\opt\ai-lead
git pull origin main
docker compose pull api worker
docker compose exec api alembic upgrade head
docker compose up -d api worker beat
curl http://localhost:8000/health
```

## Disk Space Runbook

```powershell
docker system df
docker system prune -f          # Remove unused images
docker volume ls
# Check pgdata size via volume inspect
```

If PostgreSQL disk full — see [19-incident-response.md](./19-incident-response.md).

## Test Runbook

```powershell
# Backend tests (local)
pytest backend/tests/ -v

# Discovery smoke
python backend\scripts\test_discovery_local.py

# CI mirror
docker compose -f docker-compose.yml run --rm api pytest backend/tests/test_health.py -v
```

## CI Smoke (Remote)

Trigger manually: GitHub → Actions → **Free Stack Smoke Test** → Run workflow.

## On-Call Escalation

| Severity | Response Time | Action |
|----------|---------------|--------|
| P1 API down | 30 min | [19-incident-response.md](./19-incident-response.md) |
| P2 Degraded search | 4 hours | Restart opensearch, check logs |
| P3 Monitoring gap | Next business day | Restart prometheus profile |

## Related Documents

- [19-incident-response.md](./19-incident-response.md) — incident playbooks
- [12-backup-restore.md](./12-backup-restore.md) — backup procedures
- [10-monitoring-dashboards.md](./10-monitoring-dashboards.md) — Grafana