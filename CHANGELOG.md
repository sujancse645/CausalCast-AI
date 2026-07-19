## 2026-07-17 - Phase 5: Explainable AI and Forecast Diagnostics

### Phase 5A - Explainable AI (XAI) & Diagnostics

- Added ExplainabilityEngine to dynamically map and register methods for Gradient Boosting, Classical, and N-HiTS models.
- Added model-agnostic and model-specific Explainability Adapters (Tree, Classical, N-HiTS, TFT).
- Built heuristic implementations for Partial Dependence (PDP), Accumulated Local Effects (ALE), and Permutation Importance.
- Created a Decision Intelligence module with Counterfactual Engine and Scenario simulation.
- Established residual diagnostics for identifying bias, autocorrelation, and skewness, coupled with an automated root cause analysis layer.
- Configured Anomaly explanation and Feature Drift explanation mechanics.
- Added the Explainable AI (/explainability) Frontend Dashboard to visualize global metrics and inspect local attributions.
- Added robust backend APIs for XAI artifact generation and retrieval.

# Changelog

## Unreleased — Release integration and real-asset validation

- Repaired FastAPI route integration, authentication error handling, production model adapters, and RAG authorization.
- Added typed, read-only inference endpoints for Rossmann, Electricity, M4 Daily, Online Retail II, and the yearly Tourism source.
- Added a real frontend production-forecast workspace and a grounded RAG assistant browser workflow.
- Validated all five trained artifacts directly and through a live Uvicorn API; stored bounded results under `reports/integration/`.
- Hardened deterministic RAG metric/catalog answers and excluded self-referential validation reports from retrieval.
- Removed a fixed development password and the working-tree JWT fallback; publishing remains blocked pending historical secret rotation/remediation.
- Completed Ruff, mypy, pytest, ESLint, TypeScript, Vitest, Next.js build, Alembic round-trip, Compose config, Kustomize, and local Playwright validation.
- Documented authentic asset provisioning and truthful deployment blockers; no public deployment URL is claimed.

## 2026-07-17 — Phase 4: Production, Infrastructure, and Security

### Phase 4C — Enterprise Security, Governance, and Compliance

- Added centralized RBAC, tenant-aware authorization, and service accounts.
- Added audit logging with verifiable integrity, security events, and compliance runbooks.
- Added encryption service for sensitive data masking and secrets governance.
- Added data and model governance foundations, including dataset classifications, lineage, and model cards.
- Built the Compliance Dashboard frontend for Audit Logs, Access Control, and Governance review.
- Added cost attribution tracking and cloud billing exports.

### Phase 4B — Kubernetes Infrastructure

- Generated complete Kubernetes base manifests including Deployments, Services, StatefulSets for PostgreSQL, and Redis.
- Configured Kustomize overlays for development, staging, production, and GPU-aware scaling.
- Generated comprehensive Helm charts with values templates.
- Added network policies, ingress with TLS, RBAC roles, service accounts, and Pod Disruption Budgets.
- Integrated HPA and KEDA for event-driven queue-based scaling.
- Created shell scripts for Blue-Green deployments, Canary rollouts, and rollback operations.

### Phase 4A — Production Readiness & Observability

- Implemented environment-specific settings profiles, runtime startup validation, and graceful database shutdown.
- Added structured JSON logging, correlation IDs, and request IDs via middleware.
- Configured production-grade health checks (liveness, readiness).
- Laid foundation for Prometheus metrics and OpenTelemetry tracing.
- Created Nginx reverse proxy configuration and updated Docker Compose.
- Built the Infrastructure Dashboard on the frontend for monitoring API health, database connectivity, and observability status.
