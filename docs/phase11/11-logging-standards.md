# 11 — Logging Standards

## Overview

Logging uses **structured JSON** in production-like environments and human-readable text in local dev. Logs are collected via Docker's built-in logging driver — no paid log SaaS required.

## Log Format

Implementation: `backend/infrastructure/observability/logging.py`

### JSON Format (Recommended for Staging/Production)

```json
{
  "timestamp": "2026-06-28T12:00:00.000000+00:00",
  "level": "INFO",
  "logger": "backend.app.discovery",
  "message": "Discovery job completed",
  "event": "discovery.job.completed",
  "request_id": "abc-123",
  "organization_id": "org-456",
  "user_id": "user-789",
  "duration_ms": 1420
}
```

### Text Format (Local Dev)

```
2026-06-28 12:00:00 INFO [backend.main] Application started
```

### Enable JSON Logging

In `.env`:

```ini
LOG_LEVEL=INFO
LOG_JSON=true
```

Wire in application startup (`backend/main.py` or config):

```python
from backend.infrastructure.observability.logging import configure_logging
configure_logging(level=settings.LOG_LEVEL, json_format=settings.LOG_JSON)
```

## Standard Fields

| Field | Required | Description |
|-------|----------|-------------|
| `timestamp` | Yes | UTC ISO-8601 |
| `level` | Yes | DEBUG, INFO, WARNING, ERROR, CRITICAL |
| `logger` | Yes | Python module name |
| `message` | Yes | Human-readable summary |
| `event` | Recommended | Machine-readable event name (`domain.action.result`) |
| `request_id` | Per-request | Correlation ID |
| `organization_id` | When applicable | Tenant context |
| `user_id` | When applicable | Actor |
| `duration_ms` | Operations | Latency |
| `exception` | On error | Stack trace string |

## Event Naming Convention

```
<domain>.<action>.<result>

Examples:
discovery.job.started
discovery.job.completed
discovery.job.failed
auth.login.success
auth.login.failed
api.request.completed
connector.apollo.rate_limited
```

## Log Levels

| Level | When to Use |
|-------|-------------|
| DEBUG | Query details, connector payloads (never secrets) |
| INFO | Request completed, job started/finished |
| WARNING | Retries, degraded dependency, rate limit approached |
| ERROR | Failed operation, recoverable |
| CRITICAL | Data loss risk, security breach |

**Never log:** passwords, API keys, JWT tokens, full PII payloads.

## Viewing Logs

### Docker Compose (Primary)

```powershell
# Follow all services
docker compose logs -f

# Single service
docker compose logs -f api --tail 100

# Worker errors only
docker compose logs worker 2>&1 | Select-String "ERROR"

# Since timestamp
docker compose logs --since 30m api
```

### Export Logs to File

```powershell
docker compose logs --no-color api > logs\api-$(Get-Date -Format yyyyMMdd).log
```

## Celery Worker Logs

Workers log task lifecycle to stdout:

```powershell
docker compose logs -f worker beat
```

Include `task_id` in log extras when logging from tasks (`backend/workers/tasks/`).

## Frontend Logs

Next.js dev server logs to the PowerShell job started by `scripts/start-free-stack.ps1`:

```powershell
Receive-Job -Id <job-id> -Keep
```

Production frontend: browser console + optional self-hosted error tracking (e.g. self-hosted GlitchTip — OSS Sentry alternative).

## Log Rotation (Docker)

Configure logging driver limits in Compose override:

```yaml
api:
  logging:
    driver: json-file
    options:
      max-size: "50m"
      max-file: "5"
```

Prevents unbounded disk use on long-running VMs.

## Optional: Loki Aggregation

For centralized search across services, add Grafana Loki (free). Query in Grafana Explore:

```logql
{container_name="ai-lead-intelligence--api-1"} |= "ERROR"
```

See [09-observability-architecture.md](./09-observability-architecture.md).

## Request Correlation

Middleware should set `request_id` per HTTP request and propagate to:

- Log records
- Celery task kwargs (when spawned from request)
- Response header `X-Request-ID` (recommended)

## Error Logging Pattern

```python
import logging
logger = logging.getLogger(__name__)

try:
    result = await orchestrator.run(job_id)
except ConnectorError as exc:
    logger.error(
        "Discovery job failed",
        extra={
            "event": "discovery.job.failed",
            "request_id": request_id,
            "duration_ms": elapsed,
        },
        exc_info=True,
    )
    raise
```

## Audit vs Application Logs

| Type | Destination |
|------|-------------|
| Application logs | stdout → Docker logs |
| Audit events | `audit_logs` PostgreSQL table + optional log mirror |

Security-sensitive actions (login, export, admin changes) should write to both.

## CI Log Artifacts

GitHub Actions stores workflow logs free for 90 days. Upload test artifacts:

```yaml
uses: actions/upload-artifact@v4
with:
  name: backend-coverage
  retention-days: 7
```

## Related Documents

- [09-observability-architecture.md](./09-observability-architecture.md) — metrics + logs stack
- [19-incident-response.md](./19-incident-response.md) — using logs during incidents
- [18-operational-runbooks.md](./18-operational-runbooks.md) — daily log review