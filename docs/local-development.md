# Local development

## Prerequisites

- Python 3.11 or newer
- Node.js 20.9 or newer and npm
- Existing authentic assets described in `docs/data-and-model-assets.md`

Create `.env` from `.env.example`; never commit it. The backend resolves paths from the repository by default, so no permanent `C:\Casualcast AI` dependency is required.

## Backend

```powershell
python -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r backend\requirements-dev.txt
Set-Location backend
..\.venv\Scripts\python.exe -m alembic upgrade head
..\.venv\Scripts\python.exe scripts\index_rag.py
..\.venv\Scripts\python.exe -m uvicorn app.main:app --host 127.0.0.1 --port 8000
```

Verify the worker, not only a reloader parent:

```powershell
Invoke-RestMethod http://127.0.0.1:8000/health
Start-Process http://127.0.0.1:8000/docs
```

Development APIs require a bearer token. `POST /api/v1/auth/login/developer` exists only outside production. Password login is disabled unless explicit environment credentials are configured; no fixed credential is stored in source.

## Frontend

```powershell
Set-Location frontend
npm ci
$env:NEXT_PUBLIC_API_BASE_URL="http://127.0.0.1:8000"
npm run dev
```

The client attempts the development-token endpoint locally. Production builds must use a configured identity flow; do not embed bearer tokens in `NEXT_PUBLIC_*` variables.

## Integration validation

With the backend running:

```powershell
Set-Location ..
.\.venv\Scripts\python.exe scripts\validate_integration.py
.\.venv\Scripts\python.exe scripts\validate_live_api.py
```

The first command reads existing model/data artifacts, refreshes FAISS incrementally, and writes compact reports. The second calls the live HTTP worker and records only received responses.

## Windows file locks

If Ruff, Prettier, Vitest, or Next.js receives EPERM/error 5, stop stale Node/Python workers, verify the exact file is writable, redirect caches to `%TEMP%`, and retry the single operation. Delete `.next` only when no Next.js process is active. Do not restart model training or overwrite data.
