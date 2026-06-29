# Install Cloudflare Tunnel (cloudflared) — 100% free
# Usage: .\scripts\install-cloudflare.ps1

$ErrorActionPreference = "Stop"

Write-Host "=== Cloudflare Tunnel Installer ===" -ForegroundColor Cyan

if (Get-Command cloudflared -ErrorAction SilentlyContinue) {
    $ver = cloudflared --version 2>&1 | Select-Object -First 1
    Write-Host "Already installed: $ver" -ForegroundColor Green
} else {
    Write-Host "Installing cloudflared via winget..." -ForegroundColor Yellow
    winget install --id Cloudflare.cloudflared -e --accept-source-agreements --accept-package-agreements
    $env:Path = [System.Environment]::GetEnvironmentVariable("Path", "Machine") + ";" +
                [System.Environment]::GetEnvironmentVariable("Path", "User")
    if (-not (Get-Command cloudflared -ErrorAction SilentlyContinue)) {
        Write-Host "Install finished. Restart PowerShell, then run: cloudflared --version" -ForegroundColor Yellow
        exit 0
    }
    Write-Host "Installed: $(cloudflared --version 2>&1 | Select-Object -First 1)" -ForegroundColor Green
}

Write-Host "`nNext steps:" -ForegroundColor Cyan
Write-Host "  1. Quick tunnel (no domain):  .\scripts\cloudflare\tunnel-dev.ps1 -Target gateway"
Write-Host "  2. Login for named tunnel:     cloudflared tunnel login"
Write-Host "  3. Full stack + tunnel:        .\scripts\start-free-stack.ps1 -Gateway -Monitoring -Tunnel"
Write-Host "`nDocs: infra\cloudflare\README.md"