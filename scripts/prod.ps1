# =============================================================================
# MediCode — Production Startup Script (PowerShell / Windows)
# =============================================================================
# Usage:
#   .\scripts\prod.ps1 help
#   .\scripts\prod.ps1 up
# =============================================================================

param(
    [Parameter(Position = 0)]
    [ValidateSet("up", "down", "restart", "logs", "build", "pull", "status", "shell", "backup", "migrate", "help")]
    [string]$Command = "help"
)

$ErrorActionPreference = "Stop"
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
Set-Location $PROJECT_ROOT

$COMPOSE_ARGS = @("-f", "docker-compose.yml", "-f", "docker-compose.prod.yml")

# Ensure .env exists
if (-not (Test-Path ".env")) {
    Write-Host "[error] No .env file found at project root." -ForegroundColor Red
    Write-Host "Copy .env.example to .env and configure it:" -ForegroundColor Yellow
    Write-Host "  Copy-Item .env.example .env && notepad .env" -ForegroundColor Yellow
    exit 1
}

function Show-Help {
    Write-Host "MediCode Production Commands:" -ForegroundColor Cyan
    Write-Host "  up          Start production stack (detached)"
    Write-Host "  down        Stop production stack"
    Write-Host "  restart     Restart all services"
    Write-Host "  logs        Tail logs (Ctrl+C to exit)"
    Write-Host "  build       Rebuild Docker images"
    Write-Host "  pull        Pull latest images from registry"
    Write-Host "  status      Show running containers"
    Write-Host "  shell       Open a shell in the backend container"
    Write-Host "  backup      Run database backup"
    Write-Host "  migrate     Run Alembic migrations"
}

switch ($Command) {
    "up" {
        Write-Host "[prod] Starting production stack..." -ForegroundColor Green
        docker compose $COMPOSE_ARGS up -d --wait --wait-timeout 60
        docker compose ps
    }
    "down" {
        Write-Host "[prod] Stopping production stack..." -ForegroundColor Yellow
        docker compose $COMPOSE_ARGS down --remove-orphans
    }
    "restart" {
        Write-Host "[prod] Restarting production stack..." -ForegroundColor Yellow
        docker compose $COMPOSE_ARGS restart
    }
    "logs" {
        docker compose $COMPOSE_ARGS logs -f --tail=100
    }
    "build" {
        Write-Host "[prod] Rebuilding Docker images..." -ForegroundColor Green
        docker compose $COMPOSE_ARGS build --no-cache --pull
    }
    "pull" {
        Write-Host "[prod] Pulling latest images..." -ForegroundColor Green
        docker compose $COMPOSE_ARGS pull
    }
    "status" {
        docker compose $COMPOSE_ARGS ps
        try {
            $health = Invoke-RestMethod -Uri "http://localhost:8000/health" -TimeoutSec 5
            Write-Host "Backend health: $($health | ConvertTo-Json)" -ForegroundColor Green
        } catch {
            Write-Host "Backend health: unreachable" -ForegroundColor Red
        }
    }
    "shell" {
        docker compose $COMPOSE_ARGS exec backend sh
    }
    "backup" {
        Write-Host "[prod] Running database backup..." -ForegroundColor Green
        $backupScript = Join-Path $PROJECT_ROOT "scripts" "backup.ps1"
        if (Test-Path $backupScript) {
            & $backupScript
        } else {
            Write-Host "Backup script not found." -ForegroundColor Yellow
        }
    }
    "migrate" {
        Write-Host "[prod] Running Alembic migrations..." -ForegroundColor Green
        docker compose $COMPOSE_ARGS exec backend alembic upgrade head
    }
    "help" {
        Show-Help
    }
}
