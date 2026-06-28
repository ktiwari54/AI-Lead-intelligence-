# 07 — Networking Design

## Overview

Networking spans the **Docker Compose internal network**, host-published ports, and optional **Cloudflare tunnel** ingress. All patterns work on Windows with Docker Desktop and free Cloudflare tooling.

## Docker Compose Network

Compose creates a default bridge network per project. All services resolve each other by service name:

| From | To | URL |
|------|-----|-----|
| `api` | `db` | `postgresql+asyncpg://postgres:postgres@db:5432/ai_lead_intel` |
| `api` | `redis` | `redis://redis:6379/0` |
| `api` | `opensearch` | `http://opensearch:9200` |
| `worker` | `db`, `redis` | Same as api |
| `prometheus` | `api` | `http://api:8000/metrics` |
| `prometheus` | exporters | `redis-exporter:9121`, `postgres-exporter:9187` |

### Published Ports (Host → Container)

| Host Port | Service | Exposure |
|-----------|---------|----------|
| 8000 | api | Local / tunnel target |
| 5432 | db | Local dev tools only |
| 6379 | redis | Local dev tools only |
| 9200 | opensearch | Local dev / debugging |
| 9090 | prometheus | Monitoring profile |
| 3001 | grafana | Monitoring profile |
| 3000 | frontend | Host process (not in Compose) |

**Production hardening:** Remove host port bindings for `db`, `redis`, and `opensearch` — access only inside Docker network.

### Custom Network (Optional)

```yaml
networks:
  ai-lead-net:
    driver: bridge

services:
  api:
    networks:
      - ai-lead-net
```

Default bridge is sufficient for this stack.

## Frontend → API Routing

| Environment | `NEXT_PUBLIC_API_URL` |
|-------------|----------------------|
| Local dev | `http://localhost:8000/api/v1` |
| Cloudflare tunnel | `https://<api-tunnel>.trycloudflare.com/api/v1` |
| Named domain | `https://api.yourdomain.com/api/v1` |

Set in `frontend/.env.local` (from `frontend/.env.local.example`).

## Cloudflare Tunnel Architecture

### Quick Tunnel (Development)

```
Internet → Cloudflare Edge → cloudflared → localhost:8000 (api)
                                        → localhost:3000 (frontend)
```

```powershell
.\scripts\cloudflare\tunnel-dev.ps1 -Target both
```

Each tunnel prints a unique `https://<random>.trycloudflare.com` URL in its terminal window. No DNS or Terraform required.

### Named Tunnel (Staging/Production)

```
User → api.yourdomain.com (Cloudflare DNS, proxied)
     → Cloudflare Edge (TLS, basic WAF)
     → cloudflared daemon on host
     → http://localhost:8000
```

Steps:

1. `cloudflared tunnel create ai-lead-dev`
2. Configure ingress in `config.yml` (see [06-iac-strategy.md](./06-iac-strategy.md))
3. `cloudflared tunnel route dns ai-lead-dev api.yourdomain.com`
4. Terraform manages CNAME records: `infra/terraform/cloudflare/main.tf`
5. `cloudflared tunnel run ai-lead-dev`

Install on Windows:

```powershell
winget install --id Cloudflare.cloudflared
cloudflared --version
```

## TLS Termination

| Layer | TLS Handler |
|-------|-------------|
| Quick tunnel | Cloudflare (automatic HTTPS) |
| Named tunnel + proxied DNS | Cloudflare (automatic HTTPS) |
| Local only | No TLS — HTTP on localhost |
| Self-signed local TLS | Optional Caddy or nginx reverse proxy (OSS) |

No paid Cloudflare SSL features needed — Universal SSL is free.

## CORS and Allowed Hosts

Backend `.env`:

```ini
ALLOWED_HOSTS=["*"]   # Dev only — restrict in staging/production
```

When using tunnels, add tunnel hostnames to CORS origins in FastAPI middleware if needed.

Rate limiting excludes health endpoints (`backend/app/common/rate_limit.py`):

```python
if request.url.path in ("/health", "/api/docs", ...):
```

## Prometheus Scraping Network

`infra/monitoring/prometheus/prometheus.yml`:

```yaml
scrape_configs:
  - job_name: api
    metrics_path: /metrics
    static_configs:
      - targets: ["api:8000"]
```

Prometheus must share the Compose network with `api` — achieved by running the monitoring overlay on the same project.

## Firewall Guidance (Self-Hosted VM)

| Port | Inbound | Notes |
|------|---------|-------|
| 22 | SSH admin only | Key-based auth |
| 80/443 | Not required if using tunnel | cloudflared initiates outbound |
| 8000, 3000 | Block from internet | Tunnel or reverse proxy only |

Cloudflare tunnel uses **outbound-only** connections — no inbound firewall holes required.

## DNS Record Summary (Free Cloudflare)

| Record | Type | Content | Proxied |
|--------|------|---------|---------|
| `api` | CNAME | `{tunnel-id}.cfargotunnel.com` | Yes |
| `app` | CNAME | `{tunnel-id}.cfargotunnel.com` | Yes |

TTL = 1 (auto) when proxied.

## Debugging Connectivity

```powershell
# Inside api container
docker compose exec api curl -sf http://db:5432  # TCP — use pg client
docker compose exec api curl -sf http://redis:6379
docker compose exec api curl -sf http://opensearch:9200/_cluster/health

# From host
curl http://localhost:8000/health
docker compose logs api --tail 50

# Tunnel status
cloudflared tunnel info ai-lead-dev
```

## Related Documents

- [01-cloud-architecture.md](./01-cloud-architecture.md) — full stack diagram
- [06-iac-strategy.md](./06-iac-strategy.md) — Terraform DNS
- [08-security-architecture.md](./08-security-architecture.md) — WAF and secrets