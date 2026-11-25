# Start Liquidio for manual testing: build frontend, migrate DB, serve on :8000
$ErrorActionPreference = "Stop"
Set-Location (Join-Path $PSScriptRoot "..")
$Port = if ($env:PORT) { $env:PORT } else { 8000 }

if (-not (Test-Path .venv)) { python -m venv .venv }
$py = ".venv\Scripts\python.exe"

$req = @("backend\requirements.txt", "requirements.txt") | Where-Object { Test-Path $_ } | Select-Object -First 1
if ($req) { & $py -m pip install -q -r $req; if ($LASTEXITCODE) { throw "pip failed" } }

Push-Location frontend
if (-not (Test-Path node_modules)) { npm ci; if ($LASTEXITCODE) { throw "npm ci failed" } }
npm run build; if ($LASTEXITCODE) { throw "frontend build failed" }
Pop-Location

& .venv\Scripts\alembic.exe upgrade head
if ($LASTEXITCODE) { throw "migrations failed" }

$ans = Read-Host "Create a user account now? [y/N]"
if ($ans -match '^[Yy]') { & $py scripts\create_user.py }

$ip = (Get-NetIPAddress -AddressFamily IPv4 |
  Where-Object { $_.IPAddress -notlike "127.*" -and $_.IPAddress -notlike "169.254.*" } |
  Select-Object -First 1).IPAddress
Write-Host ""
Write-Host "  This computer:      http://localhost:$Port"
if ($ip) { Write-Host "  Phone (same Wi-Fi): http://${ip}:$Port" }
Write-Host "  API docs:           http://localhost:$Port/docs"
Write-Host "  Ctrl+C to stop`n"
& .venv\Scripts\uvicorn.exe backend.app.main:app --host 0.0.0.0 --port $Port