# Operational Runbook — Discovery Platform

**Version 2.0** | AI Lead Intelligence Platform — Phase 5

---

## Table of Contents

1. [Service Overview](#1-service-overview)
2. [Architecture Quick Reference](#2-architecture-quick-reference)
3. [Routine Operations](#3-routine-operations)
4. [Incident Response](#4-incident-response)
5. [Common Issues](#5-common-issues)
6. [Maintenance Procedures](#6-maintenance-procedures)
7. [Escalation](#7-escalation)
8. [Recovery Procedures](#8-recovery-procedures)

---

## 1. Service Overview

| Component | Purpose | Owner |
|-----------|---------|-------|
| Discovery API | `/api/v1/discovery/*` | Backend team |
| Discovery Workers | Celery workers (discovery.*) | Platform team |
| Connector SDK | Provider integrations | Backend team |
| OpenSearch | Search index | Platform team |
| Redis | Queue + cache + rate limits | Platform team |
| PostgreSQL | Job persistence, entities | DBA |

**SLO:** 99.9% availability, p95 async job completion < 60s.

---

## 2. Architecture Quick Reference

```text
User → API Gateway → Discovery API → Redis Queue → Celery Workers
                                        ↓
                              Discovery Orchestrator
                                        ↓
                    ┌───────────────────┼───────────────────┐
                    ▼                   ▼                   ▼
              Connectors          PostgreSQL           OpenSearch
              (Apollo, etc.)      (jobs, entities)     (search index)
```

**Key dashboards:**

- Grafana: `Discovery Platform Overview`
- Grafana: `Connector Health`
- Admin UI: `/admin` → System Health

---

## 3. Routine Operations

### 3.1 Daily Checks (Automated)

| Check | Tool | Alert If |
|-------|------|----------|
| Discovery job failure rate | Grafana | > 5% in 24h |
| DLQ size | Grafana | > 10 entries |
| Connector health | Celery Beat | Any unhealthy > 6h |
| Queue depth | Grafana | > 200 for 30 min |

### 3.2 Weekly Tasks

| Task | Procedure |
|------|-----------|
| Review DLQ | `GET /api/v1/discovery/retry-queue` → replay or discard |
| Connector credit audit | Compare provider dashboard vs `connector_credits_used_total` |
| Staging soak test | Run 100 discovery jobs, verify metrics |
| Certificate expiry | Check TLS certs for provider webhooks |

### 3.3 Monthly Tasks

| Task | Procedure |
|------|-----------|
| Credential rotation | Rotate platform API keys per security policy |
| Index optimization | OpenSearch forcemerge on `leads-*` indices |
| Capacity review | Analyze job volume trends, adjust worker replicas |
| Runbook review | Update based on incidents |

---

## 4. Incident Response

### 4.1 Severity Levels

| Severity | Definition | Response Time |
|----------|------------|---------------|
| P1 | Discovery completely down | 15 min |
| P2 | Major connector outage or > 25% job failures | 30 min |
| P3 | Elevated latency or single connector degraded | 4 hours |
| P4 | Non-critical, workaround available | Next business day |

### 4.2 Incident Workflow

```text
1. Alert fires → On-call acknowledges in PagerDuty
2. Check Grafana Discovery Overview dashboard
3. Identify failing component (API, worker, connector, DB)
4. Apply runbook fix (see Section 5)
5. Communicate status in #incidents Slack channel
6. Resolve → Post-mortem within 48h for P1/P2
```

### 4.3 Communication Template

```text
[INCIDENT] Discovery Platform — {severity}
Status: Investigating | Identified | Monitoring | Resolved
Impact: {description}
Affected: {connectors/tenants}
ETA: {estimate}
```

---

## 5. Common Issues

### 5.1 All Discovery Jobs Failing

**Symptoms:** `discovery_jobs_total{status="failed"}` spike

**Diagnosis:**

```bash
# Check worker health
celery -A backend.workers.celery_app inspect ping

# Check Redis
redis-cli ping

# Check recent logs
kubectl logs -l app=discovery-worker --tail=100
```

**Resolution:**

1. If workers down → restart Celery deployment
2. If Redis down → failover to replica
3. If PostgreSQL down → check connection pool, failover

### 5.2 Single Connector Failing

**Symptoms:** `connector_circuit_state{connector="apollo"}=1`

**Diagnosis:**

```bash
curl -H "Authorization: Bearer $TOKEN" \
  https://api.example.com/api/v1/discovery/connectors/apollo/health
```

**Resolution:**

1. Check provider status page
2. Verify API key not expired: `POST /connectors/apollo/test`
3. If rate limited → wait for reset or reduce concurrency
4. If provider outage → fallback engine uses alternate connector
5. Manual circuit reset: restart worker or wait 5 min auto-half-open

### 5.3 High Queue Backlog

**Symptoms:** `celery_queue_depth{queue="discovery.jobs"} > 500`

**Resolution:**

1. Scale workers: `kubectl scale deployment discovery-worker --replicas=8`
2. Check for stuck jobs: query `discovery_jobs WHERE status='running' AND started_at < NOW() - INTERVAL '10 min'`
3. Cancel stuck jobs: `POST /jobs/{id}/cancel`
4. If provider rate limit → reduce worker concurrency

### 5.4 OpenSearch Index Lag

**Symptoms:** Results not appearing in search after job complete

**Diagnosis:**

```bash
# Check index worker queue
celery -A backend.workers.celery_app inspect reserved -d discovery.index

# Check OpenSearch cluster health
curl http://opensearch:9200/_cluster/health
```

**Resolution:**

1. Scale index workers
2. If cluster red → check disk space, shard allocation
3. Re-index: trigger `discovery.index_results` for affected jobs

### 5.5 Credits Exhausted for Tenant

**Symptoms:** HTTP 402 `CREDITS_EXHAUSTED`

**Resolution:**

1. Verify in billing dashboard
2. Admin can grant emergency credits
3. Notify tenant admin via notification service

### 5.6 DLQ Entries Accumulating

**Symptoms:** `dlq_entries_total` increasing

**Resolution:**

1. Inspect: `GET /api/v1/discovery/retry-queue`
2. Identify root cause from `failure_reason`
3. Fix underlying issue
4. Replay: `POST /api/v1/discovery/dlq/{entry_id}/replay`
5. Discard unrecoverable entries after 7 days

---

## 6. Maintenance Procedures

### 6.1 Deploy New Connector Version

```text
1. Deploy to staging → run contract + integration tests
2. Enable feature flag for canary org
3. Monitor connector metrics for 24h
4. Enable GA feature flag
5. Update provider catalog doc
```

### 6.2 Database Migration

```text
1. Announce maintenance window (if breaking)
2. Scale workers to 0
3. Run alembic upgrade head
4. Verify schema
5. Scale workers back
6. Run smoke test discovery job
```

### 6.3 OpenSearch Index Rebuild

```text
1. Create new index with updated mapping
2. Run reindex from PostgreSQL
3. Swap alias atomically
4. Delete old index after 24h verification
```

### 6.4 Credential Rotation

```text
1. Add new API key to vault (dual-key period)
2. Update connector configs
3. Verify health checks pass
4. Revoke old key after 24h
5. Audit log entry
```

---

## 7. Escalation

| Level | Contact | When |
|-------|---------|------|
| L1 | On-call engineer | All alerts |
| L2 | Backend lead | P1 unresolved > 30 min |
| L3 | Platform architect | Data loss risk, security breach |
| Provider | Provider support | Provider API outage confirmed |

**Provider contacts:**

| Provider | Support |
|----------|---------|
| Apollo | support@apollo.io |
| Clearbit | support@clearbit.com |
| Hunter | support@hunter.io |

---

## 8. Recovery Procedures

### 8.1 Full Platform Recovery

```text
1. Restore PostgreSQL from latest backup
2. Restore Redis (queues will be lost — jobs re-queued from DB)
3. Rebuild OpenSearch indices from PostgreSQL
4. Restart all workers
5. Run smoke tests
6. Enable traffic
```

### 8.2 Point-in-Time Job Recovery

Jobs persisted in `discovery_jobs` table. Re-queue:

```python
# Management command
python -m backend.scripts.requeue_jobs --status=running --before="2026-06-28T10:00:00Z"
```

### 8.3 Data Corruption Recovery

1. Identify affected `job_id` range
2. Soft-delete corrupted results
3. Re-run discovery jobs
4. Re-index affected entities

**RPO:** 1 hour (PostgreSQL WAL archiving)
**RTO:** 2 hours (full platform recovery)