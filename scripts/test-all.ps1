$ErrorActionPreference = "Stop"
if (-not (Test-Path ".venv\Scripts\python.exe")) { throw "Run .\scripts\setup.ps1 first." }
$python = (Resolve-Path ".venv\Scripts\python.exe").Path
Push-Location backend
try { & $python -m ruff format --no-cache --check .; & $python -m ruff check --no-cache .; & $python -m mypy --cache-dir "$env:TEMP\causalcast-mypy" app; & $python -m pytest } finally { Pop-Location }
Push-Location frontend
try { npm.cmd run format:check; npm.cmd run lint; npm.cmd run typecheck; npm.cmd test; npm.cmd run build } finally { Pop-Location }
Write-Host "All validation commands passed." -ForegroundColor Green
