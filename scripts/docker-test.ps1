# Docker-first dev helpers for AI Lead Intelligence
# Usage:
#   .\scripts\docker-test.ps1                    # run phase 9+10 unit tests
#   .\scripts\docker-test.ps1 -All               # run full test suite
#   .\scripts\docker-test.ps1 -Migrate           # alembic upgrade head
#   .\scripts\docker-test.ps1 -Seed              # seed analytics dashboards
#   .\scripts\docker-test.ps1 -Health            # hit health endpoints
#   .\scripts\docker-test.ps1 -Logs api          # tail api logs (api|worker|beat|db)
#   .\scripts\docker-test.ps1 -Test backend/tests/test_workflows.py

param(
    [switch]$All,
    [switch]$Migrate,
    [switch]$Seed,
    [switch]$Health,
    [string]$Logs,
    [string]$Test,
    [string]$ApiContainer = "",
    [string]$DbContainer = ""
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

function Get-ContainerName {
    param([string]$Service)
    if ($Service -eq "api" -and $ApiContainer) { return $ApiContainer }
    if ($Service -eq "db" -and $DbContainer) { return $DbContainer }

    $names = docker ps --format "{{.Names}}" 2>$null
    if (-not $names) {
        throw "No running Docker containers. Start the stack first: docker compose up -d"
    }

    $match = $names | Where-Object { $_ -match "--$Service-1$" } | Select-Object -First 1
    if (-not $match) {
        throw "Could not find running container for service '$Service'. Is the stack up?"
    }
    return $match
}

function Invoke-DockerExec {
    param([string]$Container, [string[]]$Command)
    & docker exec $Container @Command
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

function Copy-ScriptToContainer {
    param([string]$LocalPath, [string]$Container, [string]$RemotePath)
    if (-not (Test-Path $LocalPath)) {
        throw "File not found: $LocalPath"
    }
    & docker cp $LocalPath "${Container}:${RemotePath}"
    if ($LASTEXITCODE -ne 0) { exit $LASTEXITCODE }
}

$api = Get-ContainerName "api"
$db = Get-ContainerName "db"

Write-Host "=== AI Lead Intelligence - Docker Dev ===" -ForegroundColor Cyan
Write-Host "API container: $api" -ForegroundColor DarkGray
Write-Host "DB container:  $db" -ForegroundColor DarkGray

$actionCount = @($All, $Migrate, $Seed, $Health, [bool]$Logs, [bool]$Test).Where({ $_ }).Count
if ($actionCount -eq 0) {
    $Test = "backend/tests/test_analytics_bi.py backend/tests/test_platform.py backend/tests/test_security.py"
}

if ($Migrate) {
    Write-Host "`n[migrate] alembic upgrade head" -ForegroundColor Yellow
    Invoke-DockerExec $api alembic upgrade head
}

if ($Seed) {
    Write-Host "`n[seed] analytics dashboards" -ForegroundColor Yellow
    $seedLocal = Join-Path $Root "scripts\seed\analytics_dashboards.py"
    Copy-ScriptToContainer $seedLocal $api "/tmp/analytics_dashboards.py"
    Invoke-DockerExec $api python /tmp/analytics_dashboards.py
}

if ($Health) {
    Write-Host "`n[health] API checks" -ForegroundColor Yellow
    $endpoints = @(
        "http://localhost:8000/health",
        "http://localhost:8000/api/v1/platform/health"
    )
    foreach ($url in $endpoints) {
        Write-Host "GET $url" -ForegroundColor DarkGray
        curl.exe -s $url
        Write-Host ""
    }
}

if ($Logs) {
    $service = $Logs.ToLower()
    $container = Get-ContainerName $service
    Write-Host "`n[logs] tailing $container" -ForegroundColor Yellow
    & docker logs $container -f --tail 100
    exit $LASTEXITCODE
}

if ($All -or $Test) {
    $target = if ($All) { "backend/tests" } else { $Test }
    Write-Host "`n[test] pytest $target" -ForegroundColor Yellow
    Invoke-DockerExec $api python -m pytest $target.Split(" ") -v --tb=short
}

Write-Host "`nDone." -ForegroundColor Green