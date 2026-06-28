# 12 — Backup & Restore

## Overview

Backup strategy uses **free, built-in tools**: `pg_dump` for PostgreSQL, Docker volume archives for Redis/OpenSearch/Grafana/Prometheus data. No paid backup SaaS required.

## What to Back Up

| Asset | Method | Priority |
|-------|--------|----------|
| PostgreSQL (`pgdata`) | `pg_dump` / `pg_dumpall` | Critical |
| Redis (`redisdata`) | RDB snapshot or volume tar | High |
| OpenSearch (`opensearch_data`) | Volume tar or snapshot API | High |
| Grafana dashboards | Git (`infra/monitoring/grafana/dashboards/`) | Medium |
| Prometheus TSDB | Volume tar (optional) | Low |
| `.env` secrets | Encrypted offline copy | Critical |
| Terraform state | Encrypted copy of `terraform.tfstate` | Medium |

## PostgreSQL Backup

### Logical Backup (Recommended)

```powershell
# Create backup directory
New-Item -ItemType Directory -Force -Path C:\backups\ai-lead

# Dump while stack is running (safe for pg_dump)
docker compose exec -T db pg_dump -U postgres -d ai_lead_intel -Fc `
  > C:\backups\ai-lead\ai_lead_intel_$(Get-Date -Format yyyyMMdd_HHmm).dump
```

Plain SQL format:

```powershell
docker compose exec -T db pg_dump -U postgres ai_lead_intel `
  > C:\backups\ai-lead\ai_lead_intel_$(Get-Date -Format yyyyMMdd).sql
```

### Full Cluster Backup

```powershell
docker compose exec -T db pg_dumpall -U postgres `
  > C:\backups\ai-lead\cluster_$(Get-Date -Format yyyyMMdd).sql
```

### Automated Daily Script (PowerShell)

Save as `scripts/backup/pg-backup.ps1`:

```powershell
$BackupDir = "C:\backups\ai-lead"
$RetentionDays = 14
New-Item -ItemType Directory -Force -Path $BackupDir | Out-Null

$File = Join-Path $BackupDir "ai_lead_intel_$(Get-Date -Format yyyyMMdd).dump"
docker compose exec -T db pg_dump -U postgres -d ai_lead_intel -Fc > $File

Get-ChildItem $BackupDir -Filter "*.dump" |
  Where-Object { $_.LastWriteTime -lt (Get-Date).AddDays(-$RetentionDays) } |
  Remove-Item -Force
```

Schedule with Windows Task Scheduler (free).

## PostgreSQL Restore

### Stop writers during restore

```powershell
docker compose stop api worker beat
```

### Restore from custom format

```powershell
# Drop and recreate (DESTRUCTIVE)
docker compose exec -T db psql -U postgres -c "DROP DATABASE IF EXISTS ai_lead_intel;"
docker compose exec -T db psql -U postgres -c "CREATE DATABASE ai_lead_intel;"

# Restore
Get-Content C:\backups\ai-lead\ai_lead_intel_20260628.dump -Raw |
  docker compose exec -T db pg_restore -U postgres -d ai_lead_intel --no-owner
```

### Restore from SQL file

```powershell
Get-Content C:\backups\ai-lead\ai_lead_intel_20260628.sql |
  docker compose exec -T db psql -U postgres -d ai_lead_intel
```

### Restart services

```powershell
docker compose start api worker beat
curl http://localhost:8000/health
```

## Docker Volume Backup

### List Volumes

```powershell
docker volume ls | Select-String "ai-lead"
```

Typical names: `ai-lead-intelligence-_pgdata`, `_redisdata`, `_opensearch_data`.

### Archive Volume

```powershell
$vol = "ai-lead-intelligence-_pgdata"
$date = Get-Date -Format yyyyMMdd

docker run --rm `
  -v ${vol}:/data:ro `
  -v C:\backups\ai-lead:/backup `
  alpine tar czf /backup/${vol}_${date}.tar.gz -C /data .
```

Repeat for `redisdata`, `opensearch_data`, `grafana_data`, `prometheus_data`.

## Volume Restore

```powershell
# Stop dependent services first
docker compose down

docker run --rm `
  -v ai-lead-intelligence-_pgdata:/data `
  -v C:\backups\ai-lead:/backup `
  alpine sh -c "cd /data && tar xzf /backup/ai-lead-intelligence-_pgdata_20260628.tar.gz"

docker compose up -d
```

## Redis Backup

### Trigger RDB save

```powershell
docker compose exec redis redis-cli BGSAVE
docker compose exec redis redis-cli LASTSAVE
```

Copy RDB from volume backup or:

```powershell
docker compose exec redis cat /data/dump.rdb > C:\backups\ai-lead\redis_$(Get-Date -Format yyyyMMdd).rdb
```

## OpenSearch Backup

For single-node dev, volume tar is sufficient. For index-level export:

```powershell
# List indices
curl http://localhost:9200/_cat/indices?v

# Snapshot API requires repository config — use volume backup for free simple approach
```

## Configuration Backup

These live in git — no backup needed beyond normal version control:

- `docker-compose.yml`
- `infra/monitoring/`
- `infra/terraform/cloudflare/main.tf`

**Not in git** — backup encrypted separately:

- `.env`
- `terraform.tfstate`
- `~/.cloudflared/*.json` credentials

## Backup Schedule Recommendation

| Environment | Frequency | Retention |
|-------------|-----------|-----------|
| Local dev | Weekly (optional) | 7 days |
| Staging | Daily | 14 days |
| Production | Daily + pre-release | 30 days |

## Verification (Monthly)

```powershell
# Restore to temp database on staging
docker compose exec db createdb -U postgres ai_lead_restore_test
docker compose exec -T db pg_restore -U postgres -d ai_lead_restore_test < backup.dump
docker compose exec db psql -U postgres -d ai_lead_restore_test -c "\dt"
docker compose exec db dropdb -U postgres ai_lead_restore_test
```

## Related Documents

- [13-disaster-recovery.md](./13-disaster-recovery.md) — RPO/RTO targets
- [18-operational-runbooks.md](./18-operational-runbooks.md) — backup in daily ops
- [15-cost-optimization.md](./15-cost-optimization.md) — free storage options