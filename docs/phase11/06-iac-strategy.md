# 06 — Infrastructure as Code Strategy

## Overview

Infrastructure as Code uses the **open-source Terraform CLI** and the free **Cloudflare provider** to manage DNS records for tunnel ingress. Application runtime remains Docker Compose on self-hosted hardware — no Terraform Cloud paid features required.

## IaC Scope

| In Scope | Tool | Path |
|----------|------|------|
| Cloudflare DNS (CNAME → tunnel) | Terraform | `infra/terraform/cloudflare/` |
| Docker services | Compose YAML | `docker-compose.yml` |
| Monitoring stack | Compose + configs | `docker-compose.monitoring.yml`, `infra/monitoring/` |
| CI/CD | GitHub Actions YAML | `.github/workflows/` |
| K8s manifests (future) | Plain YAML / Kustomize | `infra/k8s/local/` |

| Out of Scope (Paid Cloud) | Alternative |
|---------------------------|-------------|
| Terraform Cloud Teams | Local state + git |
| AWS/Azure/GCP resources | Self-hosted Docker |
| Cloudflare paid plans | Free tier only |

## Terraform Layout

```
infra/terraform/cloudflare/
├── main.tf                  # Provider + DNS records
└── terraform.tfvars.example # Variable template
```

### Provider Configuration

From `main.tf`:

```hcl
terraform {
  required_version = ">= 1.5"
  required_providers {
    cloudflare = {
      source  = "cloudflare/cloudflare"
      version = "~> 5.0"
    }
  }
}

provider "cloudflare" {
  api_token = var.cloudflare_api_token
}
```

### Managed Resources

| Resource | Record | Target |
|----------|--------|--------|
| `cloudflare_dns_record.app` | `app.yourdomain.com` | `{tunnel_id}.cfargotunnel.com` |
| `cloudflare_dns_record.api` | `api.yourdomain.com` | `{tunnel_id}.cfargotunnel.com` |

Both records use `proxied = true` for free CDN/WAF/basic DDoS.

## Setup (Windows)

### Install Terraform

```powershell
winget install Hashicorp.Terraform
terraform version
```

### Configure Variables

```powershell
cd C:\Users\PC\AI-Lead-intelligence-\infra\terraform\cloudflare
Copy-Item terraform.tfvars.example terraform.tfvars
```

Edit `terraform.tfvars`:

```hcl
cloudflare_api_token = "..."   # Or use env var instead
zone_id              = "abc123..."
domain               = "yourdomain.com"
tunnel_id            = "uuid-from-cloudflare-dashboard"
```

**Never commit `terraform.tfvars`** — add to `.gitignore`.

### API Token Permissions (Free)

Create token at Cloudflare dashboard → My Profile → API Tokens:

| Permission | Access |
|------------|--------|
| Zone → DNS → Edit | Specific zone |
| Account → Cloudflare Tunnel → Read | Optional |

### Initialize and Apply

```powershell
$env:CLOUDFLARE_API_TOKEN = "your-token"
terraform init
terraform plan
terraform apply
```

## State Management (Free Options)

| Method | Pros | Cons |
|--------|------|------|
| **Local state** (`terraform.tfstate`) | Simplest | Not shared across team |
| **Git-ignored remote** (S3-compatible on MinIO) | Team sharing | Requires MinIO host |
| **GitHub Actions artifact** | CI backup | Manual restore |

Recommended for small teams:

```hcl
# backend.tf (optional — when you have free MinIO or self-hosted S3)
terraform {
  backend "s3" {
    bucket = "terraform-state"
    key    = "cloudflare/dns.tfstate"
    endpoint = "https://minio.local:9000"
    skip_credentials_validation = true
    skip_metadata_api_check     = true
    force_path_style            = true
  }
}
```

For solo dev, local state is fine. Back up `terraform.tfstate` with your volume backups.

## Cloudflare Tunnel Config (Manual + IaC)

Terraform manages DNS only. Tunnel routing is configured in `~/.cloudflared/config.yml` or Cloudflare dashboard:

```yaml
tunnel: <tunnel-id>
credentials-file: C:\Users\PC\.cloudflared\<tunnel-id>.json

ingress:
  - hostname: api.yourdomain.com
    service: http://localhost:8000
  - hostname: app.yourdomain.com
    service: http://localhost:3000
  - service: http_status:404
```

Start named tunnel:

```powershell
cloudflared tunnel run <tunnel-name>
```

Quick tunnels (`*.trycloudflare.com`) need no Terraform — see `scripts/cloudflare/tunnel-dev.ps1`.

## Compose as IaC

`docker-compose.yml` is declarative infrastructure. Version-pin images:

```yaml
db:
  image: pgvector/pgvector:pg16   # pin digest for reproducibility
```

Export running config for audit:

```powershell
docker compose config > compose-resolved.yml
```

## CI Integration

Add optional workflow job:

```yaml
terraform-validate:
  runs-on: ubuntu-latest
  steps:
    - uses: actions/checkout@v4
    - uses: hashicorp/setup-terraform@v3
    - run: terraform fmt -check -recursive
      working-directory: infra/terraform/cloudflare
    - run: terraform init -backend=false
      working-directory: infra/terraform/cloudflare
    - run: terraform validate
      working-directory: infra/terraform/cloudflare
```

`terraform apply` should remain manual or environment-gated — not auto on every PR.

## Change Process

1. Edit `main.tf` or variables.
2. `terraform plan` locally — review diff.
3. Open PR with plan output pasted in description.
4. Merge after review.
5. `terraform apply` from trusted operator machine or gated CI job.

## Destroy (Careful)

```powershell
terraform destroy
# Removes DNS records only — does not delete tunnel or Compose stack
```

## Related Documents

- [01-cloud-architecture.md](./01-cloud-architecture.md) — tunnel options
- [07-networking-design.md](./07-networking-design.md) — DNS and routing
- [04-cicd-pipeline.md](./04-cicd-pipeline.md) — CI validation jobs