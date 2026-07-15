$ErrorActionPreference = "Stop"
if (-not (Get-Command python -ErrorAction SilentlyContinue)) { throw "Python 3.11+ is required." }
if (-not (Get-Command npm.cmd -ErrorAction SilentlyContinue)) { throw "Node.js and npm are required." }
if (-not (Test-Path ".venv")) { python -m venv .venv }
& .\.venv\Scripts\python.exe -m pip install --upgrade pip
& .\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
Push-Location frontend
try { npm.cmd ci } finally { Pop-Location }
Write-Host "CausalCast AI dependencies installed." -ForegroundColor Green
