# Quick Cloudflare tunnels for local dev (free, no domain required)
param(
    [ValidateSet("api", "app", "gateway", "both")]
    [string]$Target = "gateway"
)

function Start-DevTunnel($Port, $Label) {
    if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
        Write-Host "Run first: .\scripts\install-cloudflare.ps1" -ForegroundColor Red
        exit 1
    }
    Write-Host "Starting Cloudflare tunnel for $Label on port $Port..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cloudflared tunnel --url http://localhost:$Port"
}

switch ($Target) {
    "api"     { Start-DevTunnel 8000 "API (direct)" }
    "app"     { Start-DevTunnel 3000 "Frontend (direct)" }
    "gateway" { Start-DevTunnel 80 "Traefik Gateway (app + /api via Kong)" }
    "both"    {
        Start-DevTunnel 80 "Gateway (Traefik)"
        Start-Sleep -Seconds 2
        Write-Host "Frontend must run locally on :3000 for Traefik to proxy it." -ForegroundColor Yellow
    }
}

Write-Host "Check the new terminal for your *.trycloudflare.com URL" -ForegroundColor Green
Write-Host "Architecture: Internet -> Cloudflare -> tunnel -> Traefik(:80) -> Kong(/api) | Frontend(:3000)" -ForegroundColor DarkGray