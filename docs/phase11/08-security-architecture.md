# 08 — Security Architecture (Free Tier)

## Overview

Security for the free self-hosted stack layers **Cloudflare Free edge protections**, **application auth**, **secrets in `.env`**, and **free CI security scans** — without paid WAF rulesets or cloud KMS.

## Defense in Depth

```
Layer 1: Cloudflare Free (proxied DNS, basic DDoS, Universal SSL)
Layer 2: cloudflared tunnel (no open inbound ports)
Layer 3: FastAPI (JWT, rate limits, RBAC)
Layer 4: PostgreSQL (credentials, row-level org isolation)
Layer 5: Secrets in .env / host environment (not in git)
Layer 6: CI scans (pip-audit, bandit)
```

## Edge Security (Cloudflare Free)

| Feature | Free Tier | Configuration |
|---------|-----------|---------------|
| DDoS protection | Included | Automatic on proxied records |
| Universal SSL | Included | Auto when DNS proxied |
| Basic WAF | Limited managed rules | Dashboard → Security → WAF |
| Bot Fight Mode | Available | Enable in Security settings |
| Rate limiting | Very limited | Prefer app-level rate limits |

Enable Bot Fight Mode and SSL mode **Full (strict)** when using named tunnels with origin on localhost.

### What Free Tier Does Not Include

Advanced custom WAF rules, API Shield, Page Rules (legacy). Compensate with application rate limiting in `backend/app/common/rate_limit.py`.

## Secrets Management

### Development

```powershell
Copy-Item .env.example .env
# Edit .env — never commit
```

Critical variables from `.env.example`:

| Variable | Purpose |
|----------|---------|
| `SECRET_KEY` | JWT signing — must be random in non-dev |
| `DATABASE_URL` | DB credentials |
| `APOLLO_API_KEY` | External connector keys |
| `OPENAI_API_KEY` | AI scoring |

### Production (Self-Hosted)

| Method | Cost |
|--------|------|
| `.env` file on VM (chmod 600) | $0 |
| Windows environment variables | $0 |
| Docker secrets (Swarm) | $0 |
| [SOPS](https://github.com/getsops/sops) + age encryption in git | $0 |
| Bitwarden Secrets Manager self-hosted | $0 (self-host) |

**Minimum standard:** `.env` owned by deploy user, not in git, backed up encrypted offline.

### GitHub Actions Secrets

Store deploy keys and API tokens in GitHub → Settings → Secrets and variables → Actions. Use Environments (`staging`, `production`) with required reviewers.

## Application Security

### Authentication

- JWT access + refresh tokens (`backend/` auth module)
- bcrypt password hashing
- API keys for integrations

### Rate Limiting

Applied per IP/user except health and docs paths. See `backend/app/common/rate_limit.py`.

### Multi-Tenant Isolation

Row-level `organization_id` on all tenant tables (Phase 1 architecture). Enforce in repository layer.

### Input Validation

Pydantic schemas on all API inputs. SQLAlchemy parameterized queries — no raw SQL concatenation.

## Container Security

| Control | Status |
|---------|--------|
| Non-root user | Recommended in production Dockerfile (see [03-docker-standards.md](./03-docker-standards.md)) |
| Minimal base image | `python:3.12-slim` |
| No secrets in image | `.env` via `env_file` in Compose |
| Health checks | Dockerfile + Compose |
| Dependency audit | `pip-audit` in CI |

```powershell
# Local scan
pip install pip-audit bandit
pip-audit -r requirements.txt
bandit -r backend/ -ll -x backend/tests/
```

## Database Security

| Setting | Dev (Compose) | Production |
|---------|---------------|------------|
| Password | `postgres` | Strong random password |
| Host exposure | `5432:5432` published | Remove port mapping |
| SSL | Disabled locally | Enable if remote |
| Backups | Manual `pg_dump` | Scheduled (see doc 12) |

OpenSearch in dev has `DISABLE_SECURITY_PLUGIN=true` — **enable security plugin** before any non-local exposure.

## Redis Security

Dev: no password, port published. Production:

```yaml
redis:
  command: redis-server --requirepass ${REDIS_PASSWORD}
  ports: []   # no host binding
```

Update `REDIS_URL`, `CELERY_BROKER_URL` accordingly.

## Network Security

Prefer Cloudflare tunnel over exposing ports 8000/3000 to the internet. See [07-networking-design.md](./07-networking-design.md).

SSH to VM: key-only, disable password auth, fail2ban (open source) optional.

## Audit Logging

Platform audit events in `audit_logs` table (admin module). Application logs via structured JSON — see [11-logging-standards.md](./11-logging-standards.md).

## Security Checklist (Pre-Exposure)

- [ ] Change `SECRET_KEY` from default
- [ ] Change PostgreSQL password; remove host port
- [ ] Enable OpenSearch security if externally reachable
- [ ] Set `DEBUG=false`, `ENVIRONMENT=production`
- [ ] Restrict `ALLOWED_HOSTS`
- [ ] Use named tunnel + proxied DNS (not raw port forward)
- [ ] Enable Cloudflare Bot Fight Mode
- [ ] Run `pip-audit` and resolve critical CVEs
- [ ] Rotate connector API keys periodically

## Incident Security Response

See [19-incident-response.md](./19-incident-response.md) for credential compromise and API abuse playbooks.

## Related Documents

- [07-networking-design.md](./07-networking-design.md) — tunnel ingress
- [11-logging-standards.md](./11-logging-standards.md) — audit trail in logs
- [04-cicd-pipeline.md](./04-cicd-pipeline.md) — CI security scans