$ErrorActionPreference = "Stop"
if (-not (Test-Path ".venv\Scripts\python.exe")) { throw "Run .\scripts\setup.ps1 first." }
$root = (Resolve-Path ".").Path
Start-Process powershell -WorkingDirectory "$root\backend" -ArgumentList "-NoExit", "-Command", "& '$root\.venv\Scripts\python.exe' -m uvicorn app.main:app --reload"
Start-Process powershell -WorkingDirectory "$root\frontend" -ArgumentList "-NoExit", "-Command", "npm.cmd run dev"
Write-Host "Development servers launched at http://localhost:3000 and http://localhost:8000"
