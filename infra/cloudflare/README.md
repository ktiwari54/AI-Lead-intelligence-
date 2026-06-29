# Cloudflare Free Tier Setup

All steps use **Cloudflare Free** — no paid plan required.

## Architecture

```
Internet
    │
Cloudflare (Free CDN + SSL + DDoS)
    │
cloudflared tunnel
    │
Traefik :80
    ├── /api  → Kong → FastAPI
    └── /     → Next.js :3000
```

## 1. Install cloudflared (Windows)

```powershell
.\scripts\install-cloudflare.ps1
# or: winget install --id Cloudflare.cloudflared
cloudflared --version
```

## 2. Quick dev tunnel (no domain needed)

Exposes localhost via a temporary `*.trycloudflare.com` URL:

```powershell
# API
cloudflared tunnel --url http://localhost:8000

# Frontend (separate terminal)
cloudflared tunnel --url http://localhost:3000
```

## 3. Named tunnel (your own domain, still free)

1. Sign up at https://dash.cloudflare.com (Free plan)
2. Add your domain and update nameservers
3. Zero Trust → Networks → Tunnels → **Create a tunnel**
4. Copy the tunnel token or credentials JSON to `%USERPROFILE%\.cloudflared\`
5. Copy `tunnel.example.yml` → `tunnel.yml` and fill in UUID + hostnames
6. Route DNS:

```powershell
cloudflared tunnel route dns <tunnel-name> app.yourdomain.com
cloudflared tunnel route dns <tunnel-name> api.yourdomain.com
```

7. Run:

```powershell
cloudflared tunnel --config infra\cloudflare\tunnel.yml run
```

## 4. Free security features (dashboard)

| Feature | Path | Cost |
|---------|------|------|
| SSL/TLS | SSL/TLS → Full | Free |
| DDoS | Automatic | Free |
| CDN | Proxy ON (orange cloud) | Free |
| Basic WAF | Security → WAF | Free (limited rules) |

## 5. Files (never commit secrets)

| File | Commit? |
|------|---------|
| `tunnel.example.yml` | Yes |
| `tunnel.yml` | No — gitignored |
| `*.json` credentials | No — gitignored |