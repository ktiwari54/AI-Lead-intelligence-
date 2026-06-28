# 09 — Observability Architecture

## Overview

Observability uses **open-source metrics and dashboards** — Prometheus for collection, Grafana for visualization. Optional log aggregation via Loki (also OSS). No Datadog, New Relic, or paid APM.

## Pillars

| Pillar | Tool | Cost |
|--------|------|------|
| **Metrics** | Prometheus + exporters | $0 |
| **Dashboards** | Grafana | $0 |
| **Logs** | Docker logs + optional Loki | $0 |
| **Traces** | Optional OpenTelemetry → Jaeger | $0 (future) |
| **Alerts** | Prometheus Alertmanager | $0 |

## Architecture

```
┌──────────┐     scrape      ┌─────────────┐
│   api    │ ──────────────► │ Prometheus  │
│ /metrics │                 │   :9090     │
└──────────┘                 └──────┬──────┘
                                    │ query
┌──────────────┐     scrape        │
│redis-exporter│ ─────────────────►│
└──────────────┘                   ▼
┌──────────────┐             ┌─────────────┐
│postgres-exp. │ ───────────► │   Grafana   │
└──────────────┘             │   :3001     │
                             └─────────────┘
```

## Enabling the Monitoring Stack

```powershell
# Via start script
.\scripts\start-free-stack.ps1 -Monitoring

# Or manually
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml --profile monitoring up -d
```

Services defined in `docker-compose.monitoring.yml`:

| Service | Image | Role |
|---------|-------|------|
| `prometheus` | `prom/prometheus:v2.55.1` | TSDB, 15-day retention |
| `grafana` | `grafana/grafana:11.4.0` | Dashboards at host :3001 |
| `redis-exporter` | `oliver006/redis_exporter` | Redis metrics |
| `postgres-exporter` | `prometheuscommunity/postgres-exporter` | PG metrics |

## Prometheus Configuration

`infra/monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: api
    metrics_path: /metrics
    static_configs:
      - targets: ["api:8000"]

  - job_name: redis
    static_configs:
      - targets: ["redis-exporter:9121"]

  - job_name: postgres
    static_configs:
      - targets: ["postgres-exporter:9187"]
```

Reload config without restart:

```powershell
curl -X POST http://localhost:9090/-/reload
```

## Application Metrics

Implementation: `backend/infrastructure/observability/metrics.py`

Exposed at `GET /metrics` (`backend/main.py`). Typical metrics:

- HTTP request count and latency histograms
- Active connections
- Custom business counters (discovery jobs, etc.)

Verify:

```powershell
curl http://localhost:8000/metrics
```

## Grafana Provisioning

Auto-configured via:

```
infra/monitoring/grafana/provisioning/datasources/prometheus.yml
infra/monitoring/grafana/provisioning/dashboards/dashboards.yml
infra/monitoring/grafana/dashboards/platform-overview.json
```

Default login: `admin` / `admin` (change on first login in non-dev).

## Health Endpoints

| Endpoint | Use |
|----------|-----|
| `/health` | Full check — db, redis, opensearch |
| `/health/live` | Kubernetes liveness |
| `/health/ready` | Load balancer readiness |

Source: `backend/app/common/health.py`

## Logging (See Doc 11)

Structured JSON logging via `backend/infrastructure/observability/logging.py`:

```python
configure_logging(level="INFO", json_format=True)
```

View container logs:

```powershell
docker compose logs -f api worker
```

## Optional: Loki for Log Aggregation

Add to a future `docker-compose.logging.yml`:

```yaml
loki:
  image: grafana/loki:3.0.0
  ports:
    - "3100:3100"

promtail:
  image: grafana/promtail:3.0.0
  volumes:
    - /var/lib/docker/containers:/var/lib/docker/containers:ro
    - ./infra/monitoring/promtail/config.yml:/etc/promtail/config.yml
```

On Windows Docker Desktop, Promtail may need alternate log path configuration. For dev, `docker compose logs` is sufficient.

## Optional: Alertmanager

```yaml
# docker-compose.monitoring.yml addition
alertmanager:
  image: prom/alertmanager:v0.27.0
  volumes:
    - ./infra/monitoring/alertmanager/alertmanager.yml:/etc/alertmanager/alertmanager.yml
```

Route alerts to free channels:

- Email via SMTP (your existing mail server)
- [Gotify](https://gotify.net/) (self-hosted push)
- Slack incoming webhook (free Slack tier)

Example alert rule (`infra/monitoring/prometheus/alerts.yml`):

```yaml
groups:
  - name: api
    rules:
      - alert: ApiDown
        expr: up{job="api"} == 0
        for: 2m
        labels:
          severity: critical
```

## SLIs and SLOs (Self-Hosted)

| SLI | Source | Target (Dev) |
|-----|--------|--------------|
| API availability | `up{job="api"}` | 99% |
| P95 latency | histogram `http_request_duration_seconds` | < 500ms |
| Error rate | 5xx / total requests | < 1% |
| Worker queue depth | Celery metrics (custom) | < 100 |

## Resource Usage

Monitoring stack approximate footprint:

| Service | RAM |
|---------|-----|
| Prometheus | 200–400 MB |
| Grafana | 100–200 MB |
| Exporters | ~50 MB each |

Acceptable on a 8 GB dev machine alongside the main stack.

## Tear Down Monitoring

```powershell
docker compose -f docker-compose.yml -f docker-compose.monitoring.yml --profile monitoring down
# Keep data:
# (default — volumes prometheus_data, grafana_data persist)
```

## Related Documents

- [10-monitoring-dashboards.md](./10-monitoring-dashboards.md) — dashboard details
- [11-logging-standards.md](./11-logging-standards.md) — log format
- [19-incident-response.md](./19-incident-response.md) — alert response