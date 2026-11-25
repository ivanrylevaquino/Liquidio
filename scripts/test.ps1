# ==============================================================================
# Liquidio Test Runner (Windows PowerShell)
# Executes migrations, backend pytest suite, and frontend build validation
# against an isolated temporary SQLite database and throwaway credentials.
# ==============================================================================

[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"

$RepoRoot = Split-Path -Parent $PSScriptRoot
$TempDbName = "liquidio_test_run_$([System.IO.Path]::GetRandomFileName().Substring(0,8)).db"
$TempDbPath = Join-Path $RepoRoot $TempDbName

Write-Host "================================================================" -ForegroundColor Cyan
Write-Host " Starting Liquidio Project Verification & Test Suite" -ForegroundColor Cyan
Write-Host "================================================================" -ForegroundColor Cyan

# 1. Setup / Validate Python Virtual Environment
$VenvDir = Join-Path $RepoRoot ".venv"
if (!(Test-Path $VenvDir)) {
    Write-Host "==> Creating virtual environment at $VenvDir..." -ForegroundColor Yellow
    python -m venv $VenvDir
}

$PythonBin = Join-Path $VenvDir "Scripts\python.exe"
$PipBin = Join-Path $VenvDir "Scripts\pip.exe"
$AlembicBin = Join-Path $VenvDir "Scripts\alembic.exe"
$PytestBin = Join-Path $VenvDir "Scripts\pytest.exe"

if (!(Test-Path $AlembicBin) -or !(Test-Path $PytestBin)) {
    Write-Host "==> Installing backend dependencies into virtual environment..." -ForegroundColor Yellow
    & $PipBin install -q -r (Join-Path $RepoRoot "backend\requirements.txt")
}

# 2. Configure Isolated Test Environment Variables
$NormalizedDbPath = $TempDbPath -replace "\\", "/"
$env:DATABASE_URL = "sqlite:///$NormalizedDbPath"
$env:JWT_SECRET = "test-throwaway-jwt-secret-liquidio-2026"
$env:PYTHONPATH = $RepoRoot

Write-Host "==> Isolated test database: $env:DATABASE_URL" -ForegroundColor Cyan

$TestPassed = $false

try {
    # 3. Test Alembic Migrations
    Write-Host "==> Running Alembic migrations against isolated database..." -ForegroundColor Yellow
    & $AlembicBin upgrade head

    # 4. Run Backend Tests via Pytest
    Write-Host "==> Running backend test suite with pytest..." -ForegroundColor Yellow
    & $PytestBin (Join-Path $RepoRoot "backend\tests") -v

    # 5. Verify Frontend Compilation
    Write-Host "==> Checking frontend compilation..." -ForegroundColor Yellow
    Push-Location (Join-Path $RepoRoot "frontend")
    try {
        if (!(Test-Path "node_modules")) {
            if (Test-Path "package-lock.json") {
                npm ci --silent
            } else {
                npm install --silent
            }
        }
        npm run build
    } finally {
        Pop-Location
    }

    $TestPassed = $true
} catch {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Red
    Write-Host " [FAIL] Test suite encountered errors: $_" -ForegroundColor Red
    Write-Host "================================================================" -ForegroundColor Red
    exit 1
} finally {
    # Clean up temporary database files
    if (Test-Path $TempDbPath) {
        Remove-Item -Force $TempDbPath -ErrorAction SilentlyContinue
    }
    $WalPath = "$TempDbPath-wal"
    if (Test-Path $WalPath) {
        Remove-Item -Force $WalPath -ErrorAction SilentlyContinue
    }
    $ShmPath = "$TempDbPath-shm"
    if (Test-Path $ShmPath) {
        Remove-Item -Force $ShmPath -ErrorAction SilentlyContinue
    }

    # Reset environment variables
    Remove-Item Env:\DATABASE_URL -ErrorAction SilentlyContinue
    Remove-Item Env:\JWT_SECRET -ErrorAction SilentlyContinue
}

if ($TestPassed) {
    Write-Host ""
    Write-Host "================================================================" -ForegroundColor Green
    Write-Host " [PASS] ALL CHECKS PASSED: Migrations, Pytest & Frontend Build!" -ForegroundColor Green
    Write-Host "================================================================" -ForegroundColor Green
}
