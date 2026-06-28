# Start AI Lead Intelligence — 100% free local stack
# Usage: .\scripts\start-free-stack.ps1 [-Monitoring] [-Tunnel]

param(
    [switch]$Monitoring,
    [switch]$Tunnel
)

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "=== AI Lead Intelligence — Free Stack ===" -ForegroundColor Cyan

# Backend (Docker)
Write-Host "`n[1/3] Starting Docker services..." -ForegroundColor Yellow
$composeFiles = @("-f", "docker-compose.yml")
if ($Monitoring) {
    $composeFiles += @("-f", "docker-compose.monitoring.yml", "--profile", "monitoring")
}
docker compose @composeFiles up -d
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Frontend
Write-Host "`n[2/3] Starting frontend dev server..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:Root\frontend
    npm run dev
}

Start-Sleep -Seconds 5

Write-Host "`n=== Services ===" -ForegroundColor Green
Write-Host "  Frontend:    http://localhost:3000"
Write-Host "  API:         http://localhost:8000"
Write-Host "  API Docs:    http://localhost:8000/api/docs"
Write-Host "  Health:      http://localhost:8000/health"
Write-Host "  Metrics:     http://localhost:8000/metrics"
if ($Monitoring) {
    Write-Host "  Prometheus:  http://localhost:9090"
    Write-Host "  Grafana:     http://localhost:3001  (admin / admin)"
}

if ($Tunnel) {
    Write-Host "`n[3/3] Starting Cloudflare quick tunnel (API)..." -ForegroundColor Yellow
    if (Get-Command cloudflared -ErrorAction SilentlyContinue) {
        Start-Process cloudflared -ArgumentList "tunnel", "--url", "http://localhost:8000"
        Write-Host "  Cloudflare tunnel started in new window (API)"
    } else {
        Write-Host "  cloudflared not installed. Run: winget install --id Cloudflare.cloudflared" -ForegroundColor Red
    }
}

Write-Host "`nLogin: dev@example.com / DevPass123!" -ForegroundColor Cyan
Write-Host "Stop: docker compose down; Stop-Job $($frontendJob.Id); Remove-Job $($frontendJob.Id)" -ForegroundColor DarkGray