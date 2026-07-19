# Phase E — Execution Plan (Autonomous QA & Repository Audit)

This plan outlines the implementation of a deterministic, read-only autonomous auditing system for CausalCast AI, as per the Phase E requirements.

## 1. Baseline Inspection Results
Based on a scan of the repository, the following commands are used by the repository:
*   **Backend Startup:** `python -m uvicorn app.main:app --reload`
*   **Frontend Startup:** `npm run dev`
*   **Backend Tests:** `python -m pytest`
*   **Frontend Tests:** `npm test` (vitest)
*   **E2E Tests:** `npx playwright test`
*   **Linting:** `python -m ruff check --no-cache .` (backend), `npm run lint` (frontend)
*   **Formatting:** `python -m ruff format --no-cache .` (backend), `npm run format` (frontend)
*   **Type Checking:** `python -m mypy app` (backend), `npm run typecheck` (frontend)
*   **Production Builds:** `npm run build` (frontend), `docker compose up --build`

## 2. Implementation Strategy

### Milestone E1 — Core Framework (audit/, schemas/, collectors/)
- Scaffold the `audit/` directory.
- Define data models for Findings, Evidence, and Scores using Pydantic (`audit/schemas/`).
- Implement safe subprocess execution via `command_runner.py` with timeouts and secret redaction.
- Implement repository traversal via `file_inventory.py` to count file types and identify placeholders (TODOs, fake mocks).

### Milestone E2 & E3 — Subsystem Analyzers
- **Repository, Backend & Frontend (`audit/analyzers/`)**: Regex/AST parsing to catalog routes, Next.js pages, and API handlers. Map out implemented vs planned features.
- **Database & Testing**: Introspect Alembic migrations (if present) or SQLAlchemy models. Parse JUnit XML or stdout from Pytest/Vitest/Playwright runs.

### Milestone E4 & E5 — Security, Dependency & Performance Analyzers
- Run deterministic security tools (e.g. `pip-audit`, `npm audit`).
- Scan for hardcoded credentials and exposed secrets.
- Aggregate timings from test executions and bundle sizes.

### Milestone E6 & E7 — AI Pipeline & Scoring Engine
- Validate the presence of true model implementations (Baseline, Deep Forecasting, Gradient Boosting) vs hardcoded mocks.
- Score each subsystem based on evidence according to `scoring_policy.yaml`. Calculate Release Readiness (Ready, Conditionally Ready, Not Ready).

### Milestone E8, E9 & E10 — Reporting & CLI wrappers
- Generate Markdown, JSON, and HTML reports.
- Synthesize an optional executive summary using Ollama or OpenAI, falling back to deterministic templates.
- Provide `scripts/release_audit.py`, `release_audit.ps1`, and `release_audit.sh` with profile support (`--profile quick`, `full`, `release`).

### Milestone E11 & E12 — CI Integration & Self-Tests
- Add `.github/workflows/autonomous-audit.yml`.
- Write unit tests for the auditor itself to ensure it handles scanner failures safely.

## 3. Next Steps
Once approved, I will sequentially implement the `audit/` framework starting from E1 (Models and Collectors). 

> No API key is required to begin. The auditor falls back to deterministic templates if no AI provider is configured. You can provide an OpenAI API key or Ollama URL later via environment variables if you want AI-summarized executive reports.
