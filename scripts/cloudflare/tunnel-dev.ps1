# Quick Cloudflare tunnels for local dev (free, no domain required)
param(
    [ValidateSet("api", "app", "both")]
    [string]$Target = "both"
)

function Start-DevTunnel($Port, $Label) {
    if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
        Write-Host "Install cloudflared: winget install --id Cloudflare.cloudflared" -ForegroundColor Red
        exit 1
    }
    Write-Host "Starting tunnel for $Label on port $Port..." -ForegroundColor Cyan
    Start-Process powershell -ArgumentList "-NoExit", "-Command", "cloudflared tunnel --url http://localhost:$Port"
}

switch ($Target) {
    "api"  { Start-DevTunnel 8000 "API" }
    "app"  { Start-DevTunnel 3000 "Frontend" }
    "both" {
        Start-DevTunnel 8000 "API"
        Start-Sleep -Seconds 2
        Start-DevTunnel 3000 "Frontend"
    }
}

Write-Host "Check the new terminal windows for your *.trycloudflare.com URLs" -ForegroundColor Green