$ErrorActionPreference = "Stop"
$python = Join-Path (Resolve-Path ".").Path ".venv\Scripts\python.exe"
if (-not (Test-Path $python)) { throw "Run .\scripts\setup.ps1 first." }
Push-Location backend
try { & $python -m alembic upgrade head } finally { Pop-Location }
Write-Host "Database migrations applied." -ForegroundColor Green
