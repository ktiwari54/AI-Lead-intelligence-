# Phase 8 — Operational Runbook

**Version 3.0** | Workflow Automation Platform

---

## Health Checks

| Check | Command | Expected |
|-------|---------|----------|
| API workflows | `GET /api/v1/workflows` | 200 |
| Celery worker | `celery -A backend.workers.celery_app inspect active` | workers online |
| Beat scheduler | Check `run-scheduled-workflows` in beat logs | every 5 min |
| Queue depth | RabbitMQ UI `:15672` | < 1000 pending |

## Incident: Workflow Executions Stuck

1. Check `workflow_executions` where `status='running'` and `started_at < now() - 1h`
2. Inspect Celery worker logs for `workflows.run_execution` failures
3. Resume or cancel stuck executions via API
4. Restart worker: `docker compose restart worker`

## Incident: High Failure Rate

1. Query `workflow_errors` grouped by `error_code`
2. Check action executor connectivity (SMTP, webhooks, CRM)
3. Enable dry-run mode on affected workflow versions
4. Roll back to previous published version

## Incident: Approval Backlog

1. List pending: `SELECT * FROM workflow_approvals WHERE status='pending'`
2. Send reminders via notification engine
3. Escalate per approval node `escalation_after_hours` config
4. Auto-timeout per policy if configured

## Incident: Event Bus Lag

1. Check `event_store` unpublished count
2. Verify outbox poller and `messaging.dispatch_event` task
3. Replay events from DLQ after root cause fix

## Maintenance

- Archive executions older than 90 days to cold storage
- Vacuum `workflow_execution_logs` partition tables monthly
- Rotate webhook secrets quarterly