# Phase 8 — Administrator Guide

**Version 3.0** | Workflow Automation Platform

---

## Roles

| Role | Capabilities |
|------|-------------|
| Workflow Creator | Create draft workflows, use templates |
| Workflow Editor | Edit, publish, version workflows |
| Workflow Approver | Approve/reject human-in-the-loop steps |
| Workflow Operator | Execute, pause, resume, cancel runs |
| Workflow Viewer | Read workflows and execution history |
| Workflow Administrator | Full CRUD, permissions, schedules |
| AI Workflow Manager | Configure AI nodes and credit limits |
| Template Manager | Publish org and system templates |

## Initial Setup

1. Run migration `014_phase8_workflow_engine`
2. Seed system templates: `python scripts/seed/workflow_templates.py`
3. Verify Celery beat includes `run-scheduled-workflows`
4. Confirm RabbitMQ consumer processes `workflows.run_execution`

## Tenant Configuration

- Enable workflows per org via `organizations.settings.workflows_enabled`
- Set max concurrent executions in `system_settings.workflow_max_concurrent`
- Configure approval timeout defaults in org settings

## Template Management

System templates (`is_system=true`) are read-only. Clone to customize:

```http
POST /api/v1/workflows
{ "name": "Custom Lead Routing", "template_slug": "lead-assignment", ... }
```

## Monitoring

- Grafana dashboard: `infra/monitoring/grafana/dashboards/workflow-engine.json`
- Key metrics: `workflow_executions_total`, `workflow_duration_seconds`, `workflow_failures_total`

## Credit Controls

AI nodes consume enrichment/scoring credits. Set per-workflow limits in node config `max_credits`.