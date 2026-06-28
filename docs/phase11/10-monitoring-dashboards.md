# 10 — Monitoring Dashboards

## Overview

Grafana dashboards visualize platform health at **http://localhost:3001** when the monitoring profile is active. All components are open source and pre-provisioned from `infra/monitoring/grafana/`.

## Quick Access

```powershell
.\scripts\start-free-stack.ps1 -Monitoring

# Open browser
Start-Process "http://localhost:3001"
```

| Setting | Value |
|---------|-------|
| URL | http://localhost:3001 |
| Default user | `admin` |
| Default password | `admin` |
| Data source | Prometheus → http://prometheus:9090 |

Change the admin password after first login on any shared or staging host.

## Dashboard Inventory

| Dashboard | File | Purpose |
|-----------|------|---------|
| Platform Overview | `infra/monitoring/grafana/dashboards/platform-overview.json` | API, DB, Redis at a glance |

Provisioning config: `infra/monitoring/grafana/provisioning/dashboards/dashboards.yml`

```yaml
providers:
  - name: default
    folder: AI Lead Intelligence
    type: file
    options:
      path: /var/lib/grafana/dashboards
```

## Platform Overview Panels

Expected panels in `platform-overview.json`:

| Panel | Metric / Query | Meaning |
|-------|----------------|---------|
| API Up | `up{job="api"}` | 1 = scraping successfully |
| Request Rate | `rate(http_requests_total[5m])` | Traffic volume |
| Error Rate | 5xx rate / total | Reliability |
| P95 Latency | histogram quantile | User experience |
| PostgreSQL Connections | `pg_stat_activity_count` | DB load |
| Redis Memory | `redis_memory_used_bytes` | Cache pressure |
| Redis Connected Clients | `redis_connected_clients` | Concurrency |

Exact queries depend on metric names exported by `backend/infrastructure/observability/metrics.py`. Verify names:

```powershell
curl http://localhost:8000/metrics | Select-String "http_"
```

## Prometheus Targets

Confirm all targets are UP:

1. Open http://localhost:9090/targets
2. Expect green: `api`, `redis`, `postgres`, `prometheus`

If `api` is down:

```powershell
docker compose ps api
docker compose logs api --tail 30
curl http://localhost:8000/metrics
```

## Creating Custom Panels

### Example: Discovery Job Rate

If the API exports `discovery_jobs_total`:

```promql
rate(discovery_jobs_total[5m])
```

Steps in Grafana:

1. Dashboard → Add → Visualization
2. Data source: Prometheus
3. Enter PromQL query
4. Save to folder **AI Lead Intelligence**

### Example: Celery Queue Length

Requires Redis exporter or custom Celery metrics. Inspect Redis keys:

```powershell
docker compose exec redis redis-cli -n 1 LLEN celery
```

## Dashboard as Code

Export updated dashboards to JSON and commit:

1. Grafana → Dashboard → Share → Export → Save to file
2. Save as `infra/monitoring/grafana/dashboards/<name>.json`
3. PR review — dashboard changes are version controlled

## Useful PromQL Queries

```promql
# API availability (30-day style window for testing)
avg_over_time(up{job="api"}[1h])

# Request rate by status
sum(rate(http_requests_total[5m])) by (status)

# PostgreSQL active connections
pg_stat_activity_count{datname="ai_lead_intel"}

# Redis memory usage MB
redis_memory_used_bytes / 1024 / 1024

# Prometheus scrape failures
scrape_samples_scraped{job="api"} == 0
```

## Alert Annotations on Dashboards

Link panels to Alertmanager (when configured):

- Panel description: "Triggers `ApiDown` alert after 2m"
- See [09-observability-architecture.md](./09-observability-architecture.md)

## Grafana Configuration

Environment from `docker-compose.monitoring.yml`:

```yaml
GF_SECURITY_ADMIN_USER: admin
GF_SECURITY_ADMIN_PASSWORD: admin
GF_USERS_ALLOW_SIGN_UP: "false"
GF_AUTH_ANONYMOUS_ENABLED: "false"
```

Override via `.env` on staging:

```yaml
grafana:
  environment:
    GF_SECURITY_ADMIN_PASSWORD: ${GRAFANA_ADMIN_PASSWORD}
```

## Backup Grafana State

Dashboards are file-provisioned (git is source of truth). User-created dashboards live in `grafana_data` volume:

```powershell
docker run --rm -v ai-lead-intelligence-_grafana_data:/data -v ${PWD}/backup:/backup alpine \
  tar czf /backup/grafana-data.tar.gz -C /data .
```

## Troubleshooting

| Symptom | Fix |
|---------|-----|
| No data in panels | Check Prometheus targets |
| Grafana login fails | Reset admin password via `grafana-cli` |
| Dashboard not listed | Verify volume mount in `docker-compose.monitoring.yml` |
| Stale metrics | `curl -X POST http://localhost:9090/-/reload` |

Reset Grafana admin password:

```powershell
docker compose exec grafana grafana-cli admin reset-admin-password newpassword
```

## Related Documents

- [09-observability-architecture.md](./09-observability-architecture.md) — full observability stack
- [18-operational-runbooks.md](./18-operational-runbooks.md) — daily health checks
- [19-incident-response.md](./19-incident-response.md) — responding to metric alerts