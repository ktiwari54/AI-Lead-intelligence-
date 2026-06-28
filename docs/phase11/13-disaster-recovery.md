# 13 — Disaster Recovery

## Overview

Disaster recovery for the **free self-hosted stack** focuses on realistic RPO/RTO targets without multi-region cloud failover. Recovery means restoring Docker Compose on replacement hardware from backups in [12-backup-restore.md](./12-backup-restore.md).

## Failure Scenarios

| Scenario | Severity | Recovery Path |
|----------|----------|---------------|
| API container crash | Low | `docker compose restart api` |
| PostgreSQL corruption | High | Restore `pg_dump` |
| Full host loss | Critical | New VM + restore volumes + `.env` |
| Redis data loss | Medium | Rebuild cache; Celery may re-queue |
| OpenSearch index loss | Medium | Reindex from PostgreSQL |
| Cloudflare tunnel down | Medium | Restart `cloudflared` |
| Accidental `docker compose down -v` | Critical | Volume restore from tar |

## RPO / RTO Targets (Self-Hosted Free)

| Tier | RPO (max data loss) | RTO (max downtime) | Requirements |
|------|-------------------|-------------------|--------------|
| **Local dev** | 24 hours (optional backups) | 1 hour | Re-run Compose |
| **Staging** | 24 hours | 4 hours | Daily `pg_dump`, documented restore |
| **Small production** | 1 hour | 8 hours | Daily backups + encrypted `.env` copy |

These are honest targets for a single-node self-hosted deployment without paid HA infrastructure.

## Recovery Architecture

```
Primary Host (Docker Compose)
    │
    ├── Daily pg_dump → C:\backups\ai-lead (local disk)
    ├── Weekly volume tar → external USB / NAS
    └── .env + cloudflared creds → encrypted archive (offline)

Failover Host (cold standby — optional)
    └── Docker installed, repo cloned, backups synced
```

No hot standby required for dev/small staging. For production, keep a **cold spare** VM image with Docker pre-installed.

## DR Playbook: Full Host Recovery

### 1. Provision Replacement Host

- Install Docker Desktop (Windows) or Docker Engine (Linux VM)
- Install `cloudflared`, `git`
- Clone repository

```powershell
git clone https://github.com/<org>/AI-Lead-intelligence-.git C:\opt\ai-lead
cd C:\opt\ai-lead
```

### 2. Restore Secrets

```powershell
# Restore .env from encrypted backup — do NOT use .env.example in production
Copy-Item \\nas\backups\ai-lead\.env C:\opt\ai-lead\.env
```

### 3. Start Data Layer Only

```powershell
docker compose up -d db redis opensearch
```

### 4. Restore PostgreSQL

```powershell
docker compose exec -T db psql -U postgres -c "CREATE DATABASE ai_lead_intel;"
Get-Content C:\backups\ai-lead\latest.dump -Raw |
  docker compose exec -T db pg_restore -U postgres -d ai_lead_intel --no-owner
```

### 5. Restore Volumes (if used instead of pg_dump)

```powershell
# See 12-backup-restore.md volume restore procedure
```

### 6. Start Application Tier

```powershell
docker compose up -d api worker beat
curl http://localhost:8000/health
```

### 7. Reindex OpenSearch (if index lost)

```powershell
# Trigger reindex job or run management command when implemented
# Interim: searches may be degraded until reindex completes
curl http://localhost:9200/_cluster/health
```

### 8. Restore Ingress

```powershell
# Named tunnel
cloudflared tunnel run ai-lead-dev

# Or quick tunnel for emergency
.\scripts\cloudflare\tunnel-dev.ps1 -Target api
```

### 9. Verify

```powershell
curl http://localhost:8000/health
curl http://localhost:8000/metrics
docker compose ps
pytest backend/tests/test_health.py
```

## DR Playbook: Database Only

```powershell
docker compose stop api worker beat
# restore pg_dump (see 12-backup-restore.md)
docker compose start api worker beat
```

## DR Playbook: Tunnel Failure

```powershell
# Check cloudflared process
Get-Process cloudflared -ErrorAction SilentlyContinue

# Restart
cloudflared tunnel run ai-lead-dev

# Fallback: quick tunnel
.\scripts\cloudflare\tunnel-dev.ps1 -Target both
```

Update DNS only if named tunnel ID changed (Terraform re-apply).

## Communication Template

During incident, post to team channel:

```
INCIDENT: <title>
Impact: API unavailable / degraded search / etc.
Started: <UTC time>
ETA: <estimate>
Workaround: Use local Compose / quick tunnel URL
Lead: <name>
```

## Post-Incident Review

Within 48 hours document:

1. Timeline of detection → recovery
2. Actual RPO/RTO vs targets
3. Root cause
4. Action items (backup gap, monitoring alert, runbook update)

## Testing DR (Quarterly)

| Test | Steps |
|------|-------|
| Tabletop | Walk through full host recovery on paper |
| Partial | Restore `pg_dump` to test database |
| Full (staging) | Rebuild staging VM from backups only |

Record results in `docs/phase11/dr-test-log.md` (create per test).

## What We Do Not Promise (Free Stack)

- Zero-downtime failover
- Cross-region replication
- Automatic multi-AZ database
- 99.99% SLA

Upgrade path: second self-hosted node + manual failover, or accept higher RTO.

## Related Documents

- [12-backup-restore.md](./12-backup-restore.md) — backup procedures
- [19-incident-response.md](./19-incident-response.md) — incident playbooks
- [18-operational-runbooks.md](./18-operational-runbooks.md) — health verification