# Start AI Lead Intelligence — 100% free local stack
# Usage: .\scripts\start-free-stack.ps1 [-Gateway] [-Monitoring] [-Tunnel]

param(
    [switch]$Gateway,
    [switch]$Monitoring,
    [switch]$Tunnel
)

$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

Write-Host "=== AI Lead Intelligence — Free Stack ===" -ForegroundColor Cyan

# Docker services
Write-Host "`n[1/4] Starting Docker services..." -ForegroundColor Yellow
$composeFiles = @("-f", "docker-compose.yml")
$profiles = @()

if ($Gateway) {
    $composeFiles += "-f", "docker-compose.gateway.yml"
    $profiles += "gateway"
}
if ($Monitoring) {
    $composeFiles += "-f", "docker-compose.monitoring.yml"
    $profiles += "monitoring"
}

$composeArgs = @("compose") + $composeFiles
foreach ($p in $profiles) { $composeArgs += "--profile", $p }
$composeArgs += "up", "-d"
& docker @composeArgs
if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }

# Frontend
Write-Host "`n[2/4] Starting frontend dev server..." -ForegroundColor Yellow
$frontendJob = Start-Job -ScriptBlock {
    Set-Location $using:Root\frontend
    npm run dev
}

Start-Sleep -Seconds 5

# Cloudflare tunnel
if ($Tunnel) {
    Write-Host "`n[3/4] Starting Cloudflare tunnel..." -ForegroundColor Yellow
    if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
        & "$Root\scripts\install-cloudflare.ps1"
    }
    if (Get-Command cloudflared -ErrorAction SilentlyContinue) {
        $tunnelPort = if ($Gateway) { 80 } else { 8000 }
        $tunnelLabel = if ($Gateway) { "Traefik gateway" } else { "API" }
        Start-Process powershell -ArgumentList "-NoExit", "-Command", "cloudflared tunnel --url http://localhost:$tunnelPort"
        Write-Host "  Cloudflare tunnel -> localhost:$tunnelPort ($tunnelLabel)"
    }
} else {
    Write-Host "`n[3/4] Skipping Cloudflare tunnel (use -Tunnel to enable)" -ForegroundColor DarkGray
}

Write-Host "`n[4/4] Stack ready" -ForegroundColor Green
Write-Host "`n=== Architecture ===" -ForegroundColor Cyan
if ($Gateway) {
    Write-Host "  Internet -> Cloudflare (optional) -> Traefik :80 -> Kong /api -> FastAPI"
    Write-Host "                                      -> Next.js :3000"
} else {
    Write-Host "  Frontend :3000  |  API :8000 (direct)"
}

Write-Host "`n=== URLs ===" -ForegroundColor Green
if ($Gateway) {
    Write-Host "  Gateway:     http://localhost        (Traefik)"
    Write-Host "  API via Kong http://localhost/api   (through gateway)"
    Write-Host "  Traefik UI:  http://localhost:8080"
    Write-Host "  Kong Admin:  http://localhost/kong"
    Write-Host "  RabbitMQ:    http://localhost:15672  (ali / ali_dev_pass)"
    Write-Host "  MinIO:       http://localhost:9001   (minioadmin / minioadmin)"
}
Write-Host "  Frontend:    http://localhost:3000"
Write-Host "  API direct:  http://localhost:8000"
Write-Host "  API Docs:    http://localhost:8000/api/docs"
if ($Monitoring) {
    Write-Host "  Prometheus:  http://localhost:9090"
    Write-Host "  Grafana:     http://localhost:3001  (admin / admin)"
    Write-Host "  Loki:        http://localhost:3100"
    Write-Host "  Jaeger:      http://localhost:16686"
}

Write-Host "`nLogin: dev@example.com / DevPass123!" -ForegroundColor Cyan