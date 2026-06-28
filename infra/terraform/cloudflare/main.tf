# Free-tier Cloudflare DNS management via Terraform (open-source CLI)
# Usage:
#   cd infra/terraform/cloudflare
#   set CLOUDFLARE_API_TOKEN=your-token
#   terraform init && terraform plan

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

variable "cloudflare_api_token" {
  type      = string
  sensitive = true
}

variable "zone_id" {
  type        = string
  description = "Cloudflare zone ID from dashboard"
}

variable "domain" {
  type    = string
  default = "yourdomain.com"
}

# CNAME records pointing to Cloudflare Tunnel (free ingress)
resource "cloudflare_dns_record" "app" {
  zone_id = var.zone_id
  name    = "app"
  content = "${var.tunnel_id}.cfargotunnel.com"
  type    = "CNAME"
  proxied = true
  ttl     = 1
}

resource "cloudflare_dns_record" "api" {
  zone_id = var.zone_id
  name    = "api"
  content = "${var.tunnel_id}.cfargotunnel.com"
  type    = "CNAME"
  proxied = true
  ttl     = 1
}

variable "tunnel_id" {
  type        = string
  description = "Cloudflare Tunnel UUID"
}