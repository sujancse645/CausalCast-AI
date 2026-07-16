# Changelog

All notable project changes are documented here.

## 0.3.0 — 2026-07-15

### Phase 2B — Intelligent Schema Mapping

- Added bounded, deterministic physical profiling and multi-signal semantic-role inference with confidence, evidence, alternatives, ambiguity, relationship checks, and readiness issues.
- Added versioned schema, column-profile, and mapping-audit persistence plus role discovery, inference, history, override, confirmation, and aggregate statistics APIs.
- Added the accessible schema-mapping workspace, evidence review, role overrides, confirmation flow, schema status in the dataset library, and real dashboard schema statistics.
- Raw datasets remain immutable; inference runs locally without external AI services and proposed mappings require human confirmation.

## 0.2.0 — 2026-07-15

### Phase 2A — Secure Dataset Ingestion

- Added streamed, size-bounded CSV ingestion with UUID filenames, SHA-256 deduplication, encoding/delimiter validation, strict structural parsing, and cleanup on failure.
- Added the governed Dataset model, Alembic migration, technical metadata persistence, bounded preview metadata, pagination, details, statistics, and reversible archive flow.
- Added the Data Intelligence upload workspace, dataset library, details/preview panel, accessible validation states, and real dashboard dataset summary.
- Added isolated storage/database tests, synthetic demonstration data, persistent Docker storage configuration, migration CI verification, environment settings, and governance documentation.
- CSV is the only supported format; XLSX, schema inference, quality analysis, and transformations remain out of scope.

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
