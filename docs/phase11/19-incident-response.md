# 19 — Incident Response

## Overview

Incident playbooks for the **free self-hosted stack**. No PagerDuty required — use team chat, email, or self-hosted Gotify for alerts.

## Severity Levels

| Level | Definition | Example |
|-------|------------|---------|
| **P1** | Platform unusable | API down, DB unreachable |
| **P2** | Major feature degraded | Search broken, workers stalled |
| **P3** | Minor impact | Slow queries, single connector failure |
| **P4** | Cosmetic / internal | Grafana panel missing |

## Incident Response Flow

```
Detect → Triage → Mitigate → Resolve → Post-mortem
   │         │          │          │
   │         │          │          └── Update runbooks
   │         │          └── Rollback / restart / restore
   │         └── Assign severity + incident lead
   └── Monitoring alert / user report / health check fail
```

## Detection Sources

| Source | How |
|--------|-----|
| Health endpoint | `curl http://localhost:8000/health` fails |
| Prometheus | `up{job="api"} == 0` |
| Grafana | Platform Overview red panels |
| Users | Login failures, 502 from tunnel |
| CI | `free-stack-smoke.yml` failure on main |

## Playbook: API Down (P1)

### Symptoms

- `curl http://localhost:8000/health` times out or connection refused
- Frontend shows network errors
- Prometheus `api` target DOWN

### Diagnosis

```powershell
docker compose ps api
docker compose logs api --tail 100
docker compose exec api curl -sf http://localhost:8000/health/live
```

### Mitigation Steps

1. **Restart API**

```powershell
docker compose restart api
Start-Sleep -Seconds 10
curl http://localhost:8000/health
```

2. **If crash loop — check dependencies**

```powershell
docker compose ps db redis
docker compose logs db --tail 30
```

3. **If bad deploy — rollback**

```powershell
git checkout <last-good-sha>
docker compose up -d api
```

4. **If tunnel issue — bypass**

```powershell
.\scripts\cloudflare\tunnel-dev.ps1 -Target api
# Communicate temporary URL to stakeholders
```

### Resolution Criteria

- `/health` returns healthy
- `/health/ready` passes
- Sample API login works
- Prometheus target UP for 15+ minutes

## Playbook: Database Full / Disk Full (P1)

### Symptoms

- API logs: `could not extend file`, `No space left on device`
- PostgreSQL refuses connections
- `docker compose exec db pg_isready` fails

### Diagnosis

```powershell
docker system df
docker compose exec db psql -U postgres -c "SELECT pg_size_pretty(pg_database_size('ai_lead_intel'));"
```

### Mitigation Steps

1. **Free Docker disk space**

```powershell
docker system prune -f
docker image prune -a -f   # Careful — re-pull needed
```

2. **Truncate non-critical data** (dev/staging only)

```powershell
docker compose exec db psql -U postgres -d ai_lead_intel -c \
  "DELETE FROM audit_logs WHERE created_at < NOW() - INTERVAL '90 days';"
VACUUM ANALYZE;
```

3. **Emergency backup before destructive ops**

```powershell
docker compose exec -T db pg_dump -U postgres -d ai_lead_intel -Fc > emergency.dump
```

4. **Extend host disk** or move Docker data root (Windows Docker Desktop → Settings → Resources → Disk image location)

### Prevention

- Log rotation in Compose (`max-size`, `max-file`)
- Prometheus retention `15d` not higher on small disks
- Daily backup with retention policy

## Playbook: Worker Queue Backlog (P2)

### Symptoms

- Discovery jobs stuck in pending
- Redis queue length growing

### Diagnosis

```powershell
docker compose exec worker celery -A backend.workers.celery_app inspect active
docker compose exec redis redis-cli -n 1 LLEN celery
docker compose logs worker --tail 50
```

### Mitigation

```powershell
docker compose up -d --scale worker=4
docker compose restart worker
```

Check connector rate limits in logs (`connector.apollo.rate_limited`).

## Playbook: OpenSearch Unavailable (P2)

### Symptoms

- `/health` shows opensearch unhealthy
- Search endpoints fail

### Mitigation

```powershell
docker compose restart opensearch
# Wait for start_period (30s+)
curl http://localhost:9200/_cluster/health
```

If index corrupted — restore volume from backup or reindex from PostgreSQL.

## Playbook: Redis Down (P1/P2)

```powershell
docker compose restart redis
docker compose exec redis redis-cli ping
docker compose restart api worker
```

## Playbook: Credential Compromise (P1)

1. Rotate `SECRET_KEY` in `.env` — invalidates all JWTs
2. Rotate database password
3. Rotate Cloudflare API token and connector API keys
4. Restart all services
5. Review `audit_logs` and application logs for suspicious activity
6. Force user re-login

See [08-security-architecture.md](./08-security-architecture.md).

## Communication Template

```
🚨 INCIDENT P1: API Unavailable
Status: Investigating | Mitigating | Resolved
Impact: All users cannot access platform
Started: 2026-06-28 14:00 UTC
Lead: @operator
Next update: 14:30 UTC
Workaround: None
```

## Post-Incident Review Template

| Field | Content |
|-------|---------|
| Incident ID | INC-2026-001 |
| Duration | 45 minutes |
| Root cause | Disk full on Docker volume |
| RPO/RTO actual | 0 data loss / 45 min recovery |
| Action items | Add disk alert, reduce log retention |
| Runbook updates | 19-incident-response.md § disk |

## Escalation Contacts

Define in team wiki (not in git):

| Role | Contact |
|------|---------|
| Platform lead | — |
| Backend on-call | — |
| Security | — |

## Related Documents

- [18-operational-runbooks.md](./18-operational-runbooks.md) — daily ops
- [13-disaster-recovery.md](./13-disaster-recovery.md) — full host recovery
- [12-backup-restore.md](./12-backup-restore.md) — restore procedures