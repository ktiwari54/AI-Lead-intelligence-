# 15 — Cost Optimization ($0 Dev Stack)

## Overview

The AI Lead Intelligence Platform is designed for **$0 software licensing** in development and small self-hosted deployments. This document maps every component to a free alternative and lists practical savings tactics.

## Stack Cost Map

| Component | Choice | Cost |
|-----------|--------|------|
| Runtime | Docker Compose on owned PC/VM | $0 |
| Database | PostgreSQL (pgvector image) | $0 |
| Cache/Queue | Redis 7 Alpine | $0 |
| Search | OpenSearch single-node | $0 |
| API/Workers | Python FastAPI + Celery | $0 |
| Frontend | Next.js dev server | $0 |
| Ingress | Cloudflare Free + cloudflared | $0 |
| DNS | Cloudflare Free (if domain owned) | $0 domain registration only |
| CI/CD | GitHub Actions | $0 public / included minutes |
| Container registry | GHCR | $0 public packages |
| Monitoring | Prometheus + Grafana | $0 |
| IaC | Terraform OSS + Cloudflare provider | $0 |
| K8s practice | k3d / minikube | $0 |
| Security scan | pip-audit, bandit | $0 |

**Total software cost: $0.** Hardware and domain registration are the only real expenses.

## Hardware Optimization

### Minimum Dev Machine

| Resource | Minimum | Recommended |
|----------|---------|-------------|
| RAM | 8 GB | 16 GB |
| CPU | 4 cores | 8 cores |
| Disk | 20 GB free | 50 GB SSD |

### Reduce Local Footprint

```powershell
# Start only what you need
docker compose up -d db redis api

# Skip OpenSearch if not testing search
docker compose up -d db redis api worker

# Lower OpenSearch heap in docker-compose.yml
OPENSEARCH_JAVA_OPTS=-Xms256m -Xmx256m
```

### Stop When Idle

```powershell
docker compose stop
# Or full teardown preserving data:
docker compose down
```

## Cloudflare Free Tier Maximization

| Feature | Use For | Avoid |
|---------|---------|-------|
| Quick tunnels | Demos, webhooks | Production without named tunnel |
| Proxied CNAME | SSL + basic protection | Unproxied DNS exposing origin IP |
| Bot Fight Mode | Simple bot mitigation | Paid bot management |
| Free analytics | Traffic overview | Paid Log Explorer |

No Workers paid plan needed — API runs on your host.

## GitHub Actions Minute Savings

| Tactic | Implementation |
|--------|----------------|
| Path filters | Skip CI on `docs/**` only changes |
| Caching | `cache: pip`, `cache: npm` (already in `ci.yml`) |
| Public repo | Unlimited minutes for public open source |
| Concurrency cancel | Cancel outdated PR runs |
| Smoke vs full CI | `free-stack-smoke.yml` is lighter than full test matrix |

## Storage Cost (Backups)

| Option | Cost |
|--------|------|
| Local disk `C:\backups` | $0 |
| USB external drive | One-time hardware |
| Self-hosted NAS (Samba) | $0 software |
| MinIO on homelab | $0 (S3-compatible API) |

Avoid paid S3 unless you already have AWS credits.

## Connector API Costs

External data providers (Apollo, Clearbit, Hunter) may charge per call. Dev cost control:

```ini
USE_MOCK_CONNECTORS=true
```

Uses `backend/connectors/mock_discovery.py` — zero external API spend.

## AI Provider Costs

```ini
ENABLE_AI_SCORING=false   # CI already sets this
OPENAI_API_KEY=           # Leave blank in dev
ANTHROPIC_API_KEY=
```

Disable in `.env` for local work; enable only when testing scoring features.

## Image Registry

Use GHCR with `GITHUB_TOKEN` — no Docker Hub paid plan needed. CI builds with GHA cache (`type=gha`) avoids repeated full builds.

## Monitoring Retention

Prometheus 15-day retention (configured in `docker-compose.monitoring.yml`):

```yaml
--storage.tsdb.retention.time=15d
```

Reduce to `7d` on disk-constrained hosts.

## Email / Notifications

Skip paid SendGrid/Mailgun in dev:

```ini
SMTP_HOST=
```

Use MailHog (OSS) for local email capture if testing notifications:

```yaml
mailhog:
  image: mailhog/mailhog
  ports:
    - "1025:1025"
    - "8025:8025"
```

## Cost Comparison (What We Replaced)

| Paid Alternative | Our Free Choice | Est. Savings |
|------------------|-----------------|--------------|
| AWS ECS + RDS | Docker Compose | $50–500+/mo |
| Datadog | Prometheus + Grafana | $15–100+/host/mo |
| Cloudflare Pro | Cloudflare Free | $20/mo |
| ArgoCD Cloud | Git + GitHub Actions | $ |
| Managed OpenSearch | Self-hosted container | $70+/mo |

## Monthly Cost Checklist

- [ ] No unexpected cloud bills (verify no AWS/GCP credentials in use)
- [ ] Connector mock mode in non-demo dev
- [ ] AI scoring disabled when not needed
- [ ] Docker images pruned: `docker system prune -f`
- [ ] Backup retention policy enforced (see [12-backup-restore.md](./12-backup-restore.md))
- [ ] GitHub Actions minutes within quota (private repos)

## When Spending Makes Sense (Optional)

Domain name (~$10/year) and dedicated VPS (~$5–20/month) are the only common cash costs for a small public deployment — still no paid SaaS required.

## Related Documents

- [01-cloud-architecture.md](./01-cloud-architecture.md) — free stack design
- [14-scaling-strategy.md](./14-scaling-strategy.md) — scale on owned hardware
- [16-environment-configuration.md](./16-environment-configuration.md) — dev vs prod flags