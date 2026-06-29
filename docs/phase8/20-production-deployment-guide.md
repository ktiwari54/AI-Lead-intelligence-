# Phase 8 — Production Deployment Guide

**Version 3.0** | Workflow Automation Platform

---

## Architecture (Production)

```mermaid
flowchart TB
    subgraph Edge
        CF[Cloudflare]
        Kong[Kong Gateway]
    end
    subgraph App
        API[FastAPI API]
        Worker[Celery Workers]
        Beat[Celery Beat]
    end
    subgraph Data
        PG[(PostgreSQL)]
        Redis[(Redis)]
        RMQ[RabbitMQ]
    end
    CF --> Kong --> API
    API --> PG
    API --> RMQ
    Worker --> PG
    Worker --> RMQ
    Beat --> RMQ
```

## Scaling Guidelines

| Component | Dev | Production |
|-----------|-----|------------|
| API replicas | 1 | 3+ (HPA on CPU) |
| Workflow workers | 1 | 5+ (queue depth HPA) |
| Beat | 1 singleton | 1 singleton |
| PostgreSQL | Single | Primary + read replica |

## Environment Variables

```env
CELERY_BROKER_URL=amqp://user:pass@rabbitmq:5672/
WORKFLOW_MAX_RETRIES=3
WORKFLOW_DEFAULT_TIMEOUT_SECONDS=3600
WORKFLOW_SANDBOX_ENABLED=true
```

## Kubernetes Manifests

Deploy workflow worker pool separately from general workers:

```yaml
# k8s/workflow-worker-deployment.yaml
command: ["celery", "-A", "backend.workers.celery_app", "worker",
          "-Q", "workflows,default", "-c", "4"]
```

## Database Migration

```bash
alembic upgrade 014
python scripts/seed/workflow_templates.py
```

## Rollout Strategy

1. Deploy API with workflows router (read-only smoke test)
2. Run migration during maintenance window
3. Deploy workflow-dedicated Celery workers
4. Enable beat schedule `run-scheduled-workflows`
5. Canary: enable workflows for pilot org only via feature flag

## Observability

- Prometheus scrape `/metrics` for `workflow_*` counters
- Jaeger trace propagation via `X-Correlation-ID`
- Loki log labels: `service=workflow-engine`, `execution_id`

## Security Checklist

- [ ] Tenant isolation verified in integration tests
- [ ] Webhook secrets in Vault/K8s secrets
- [ ] Rate limits on execute endpoint (Kong plugin)
- [ ] SQL action disabled except admin role
- [ ] Audit logging enabled for all mutations