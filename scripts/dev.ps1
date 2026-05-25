# =============================================================================
# MediCode — Development Startup Script (PowerShell / Windows)
# =============================================================================
# Usage:
#   .\scripts\dev.ps1              # start both services
#   .\scripts\dev.ps1 -Service Backend  # start backend only
#   .\scripts\dev.ps1 -Service Frontend # start frontend only
# =============================================================================

param(
    [ValidateSet("All", "Backend", "Frontend")]
    [string]$Service = "All"
)

$ErrorActionPreference = "Stop"
$PROJECT_ROOT = Split-Path -Parent (Split-Path -Parent $PSCommandPath)
$BACKEND_DIR = Join-Path $PROJECT_ROOT "backend"
$FRONTEND_DIR = Join-Path $PROJECT_ROOT "frontend"

Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan
Write-Host "  MediCode Development Environment" -ForegroundColor Cyan
Write-Host "══════════════════════════════════════════" -ForegroundColor Cyan

function Start-Backend {
    Write-Host "`n[backend] Starting FastAPI server..." -ForegroundColor Green

    Set-Location $BACKEND_DIR

    # Check if .env exists
    if (-not (Test-Path ".env")) {
        Write-Host "[backend] No .env found, copying from .env.example..." -ForegroundColor Yellow
        Copy-Item ".env.example" ".env"
        Write-Host "[backend] Please edit backend\.env and re-run." -ForegroundColor Yellow
        exit 1
    }

    # Check/create virtual environment
    if (-not (Test-Path ".venv")) {
        Write-Host "[backend] Creating Python virtual environment..." -ForegroundColor Yellow
        python -m venv .venv
    }

    # Activate and install deps
    $activateScript = Join-Path ".venv" "Scripts" "Activate.ps1"
    . $activateScript

    if (-not (Test-Path ".venv\.deps_installed")) {
        Write-Host "[backend] Installing Python dependencies..." -ForegroundColor Yellow
        pip install --upgrade pip 2>&1 | Out-Null
        pip install -r requirements.txt 2>&1 | Out-Null
        "" | Out-File ".venv\.deps_installed"
        Write-Host "[backend] Dependencies installed." -ForegroundColor Green
    }

    Write-Host "[backend] Running on http://localhost:8000" -ForegroundColor Green
    Write-Host "[backend] API docs: http://localhost:8000/docs" -ForegroundColor Green
    uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
}

function Start-Frontend {
    Write-Host "`n[frontend] Starting Vite dev server..." -ForegroundColor Green

    Set-Location $FRONTEND_DIR

    # Install deps if needed
    if (-not (Test-Path "node_modules")) {
        Write-Host "[frontend] Installing Node.js dependencies..." -ForegroundColor Yellow
        npm install
        Write-Host "[frontend] Dependencies installed." -ForegroundColor Green
    }

    Write-Host "[frontend] Running on http://localhost:5173" -ForegroundColor Green
    npm run dev
}

# ---- Main ----
switch ($Service) {
    "Backend" { Start-Backend }
    "Frontend" { Start-Frontend }
    "All" {
        $backendJob = Start-Job -ScriptBlock {
            param($dir)
            Set-Location $dir
            $activateScript = Join-Path ".venv" "Scripts" "Activate.ps1"
            if (Test-Path $activateScript) { . $activateScript }
            uvicorn src.main:app --host 0.0.0.0 --port 8000 --reload --log-level info
        } -ArgumentList $BACKEND_DIR

        Write-Host "[wait] Waiting for backend to be ready..." -ForegroundColor Yellow
        $ready = $false
        for ($i = 0; $i -lt 30; $i++) {
            try {
                $response = Invoke-WebRequest -Uri "http://localhost:8000/health" -UseBasicParsing -TimeoutSec 2
                if ($response.StatusCode -eq 200) {
                    Write-Host "[wait] Backend is ready." -ForegroundColor Green
                    $ready = $true
                    break
                }
            } catch { }
            Start-Sleep -Seconds 1
        }

        Start-Frontend

        # Cleanup
        Stop-Job -Job $backendJob -ErrorAction SilentlyContinue
        Remove-Job -Job $backendJob -ErrorAction SilentlyContinue
    }
}
