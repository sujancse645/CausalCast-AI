# Changelog

All notable project changes are documented here.

## 0.1.0 — 2026-07-15

### Phase 1 — Foundation

- Created the Next.js analytics command center, responsive navigation, shared placeholder-module shell, accessible states, and centralized demo interface fixture.
- Added typed FastAPI health and system endpoints, centralized Pydantic settings, safe CORS, structured logging, lifecycle management, and safe exception handling.
- Added SQLAlchemy 2 SQLite/PostgreSQL-compatible infrastructure and Alembic migration readiness.
- Added backend and frontend automated tests, Ruff, MyPy, ESLint, Prettier, TypeScript, and GitHub Actions checks.
- Added multi-stage Dockerfiles, Compose health/dependency configuration, environment examples, PowerShell scripts, and engineering documentation.
- Pinned a secure PostCSS override after npm audit identified the version bundled by the latest stable Next.js release; final npm audit reports zero vulnerabilities.

### Validation

- Backend: Ruff format/check passed; MyPy passed; Pytest passed (7 tests, one upstream TestClient deprecation warning).
- Frontend: Prettier, ESLint, TypeScript, Vitest (8 tests), and production build passed.
- Runtime: API, documentation, and all frontend routes returned HTTP 200; offline dashboard remained available.
- Docker: `docker compose config` passed. Image build/runtime validation was unavailable because the Docker Desktop Linux engine was not running.
