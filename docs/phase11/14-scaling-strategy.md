# 14 — Scaling Strategy

## Overview

Scaling progresses from **Docker Compose replicas** on a single host to **optional local Kubernetes HPA** for learning. No paid autoscaling services (AWS ASG, Cloud Run) required.

## Scaling Dimensions

| Component | Stateless? | Scale Method |
|-----------|------------|--------------|
| `api` | Yes | Compose `deploy.replicas` / multiple containers |
| `worker` | Yes (Celery) | Add worker containers |
| `beat` | No — single scheduler | **Always 1 instance** |
| `db` | No | Vertical scaling (more RAM/CPU) |
| `redis` | No (single instance) | Vertical; Redis Cluster for advanced |
| `opensearch` | Cluster-capable | Single-node dev; add nodes later |

## Phase 1: Docker Compose Scaling (Free)

### Scale Workers

```powershell
docker compose up -d --scale worker=4
```

Celery distributes tasks across workers via Redis broker (`CELERY_BROKER_URL` in `docker-compose.yml`).

### Scale API (Requires Load Balancer)

Compose does not load-balance multiple `api` containers on one port by default. Options:

**Option A: Single API + vertical scale** — simplest for dev.

**Option B: nginx reverse proxy (OSS)**

```yaml
# docker-compose.override.yml
nginx:
  image: nginx:alpine
  ports:
    - "8000:80"
  volumes:
    - ./infra/nginx/api-upstream.conf:/etc/nginx/conf.d/default.conf
  depends_on:
    - api

api:
  deploy:
    replicas: 3
  ports: []   # remove direct host port
```

nginx upstream config:

```nginx
upstream api {
    server api:8000;
}
server {
    listen 80;
    location / {
        proxy_pass http://api;
    }
}
```

**Option C: Docker Swarm mode** (free, built into Docker)

```powershell
docker swarm init
docker stack deploy -c docker-compose.yml ai-lead
docker service scale ai-lead_worker=4
```

### Resource Tuning

```yaml
worker:
  command: celery -A backend.workers.celery_app worker --loglevel=info --concurrency=8

opensearch:
  environment:
    - "OPENSEARCH_JAVA_OPTS=-Xms1g -Xmx1g"
```

## Phase 2: Vertical Scaling

| Service | Dev Default | Stressed Dev | Notes |
|---------|-------------|--------------|-------|
| API | 1 CPU / 512 MB | 2 CPU / 1 GB | FastAPI async handles concurrency |
| Worker | concurrency=4 | concurrency=8 | Match CPU cores |
| PostgreSQL | default | 2 GB shared_buffers | Tune in custom postgresql.conf |
| OpenSearch | 512 MB heap | 1 GB heap | `OPENSEARCH_JAVA_OPTS` |
| Redis | default | maxmemory 256mb | `maxmemory-policy allkeys-lru` |

Docker Desktop → Settings → Resources: allocate 8+ GB RAM for full stack + monitoring.

## Phase 3: Kubernetes HPA (Local Practice)

On k3d/minikube with metrics-server:

```yaml
apiVersion: autoscaling/v2
kind: HorizontalPodAutoscaler
metadata:
  name: api-hpa
spec:
  minReplicas: 2
  maxReplicas: 6
  metrics:
    - type: Resource
      resource:
        name: cpu
        target:
          type: Utilization
          averageUtilization: 70
```

Worker HPA based on custom metric (queue depth) requires Prometheus Adapter — advanced, still OSS.

## Bottleneck Identification

Use free metrics before scaling:

```powershell
# API metrics
curl http://localhost:8000/metrics

# Grafana dashboards
Start-Process http://localhost:3001

# PostgreSQL active queries
docker compose exec db psql -U postgres -d ai_lead_intel -c \
  "SELECT count(*) FROM pg_stat_activity WHERE state = 'active';"

# Redis memory
docker compose exec redis redis-cli INFO memory

# Celery inspect
docker compose exec worker celery -A backend.workers.celery_app inspect active
```

## Caching for Scale

Redis cache layer (`backend/infrastructure/cache/redis_cache.py`):

- Increase `CACHE_TTL` in `.env` for read-heavy endpoints
- Cache discovery results per organization

## Database Connection Pool

From `.env.example`:

```ini
DATABASE_POOL_SIZE=20
DATABASE_MAX_OVERFLOW=40
```

Rule of thumb: `pool_size × api_instances + worker_connections < postgres max_connections`.

Check:

```powershell
docker compose exec db psql -U postgres -c "SHOW max_connections;"
```

## OpenSearch Scaling Path

| Stage | Setup |
|-------|-------|
| Dev | Single node (`discovery.type=single-node`) |
| Growth | Add data nodes in Compose or K8s StatefulSet |
| Reindex | Background job from PostgreSQL source of truth |

## When Not to Scale Horizontally

- `beat` — only one scheduler
- PostgreSQL — scale vertically first; read replicas are advanced
- Debugging phase — scale hides performance bugs

## Load Testing (Free Tools)

```powershell
pip install locust
# Or
docker run --rm -it --network host locustio/locust
```

Target `http://localhost:8000/health` and representative API endpoints with auth token.

## Scaling Checklist

- [ ] Metrics show CPU > 70% or queue backlog growing
- [ ] Database connections not exhausted
- [ ] Redis memory within limits
- [ ] `beat` remains at 1 replica
- [ ] Backups still complete within backup window
- [ ] Update runbook with new replica counts

## Related Documents

- [02-kubernetes-architecture.md](./02-kubernetes-architecture.md) — K8s scaling
- [10-monitoring-dashboards.md](./10-monitoring-dashboards.md) — capacity panels
- [15-cost-optimization.md](./15-cost-optimization.md) — scale within free hardware