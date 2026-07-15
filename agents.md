# CausalCast AI Engineering Rules

1. Inspect the repository and relevant contracts before editing; preserve working features.
2. Prefer small, reviewable, independently testable modules.
3. Keep frontend and backend API contracts synchronized and use typed schemas for every response.
4. Never fabricate AI, model, or analytical output; results must come from real computations.
5. Use chronological, time-based validation for all future time-series models—never random splits.
6. Protect credentials and personal data; never hardcode or commit secrets.
7. Run focused tests after meaningful changes and the full quality suite before completing a phase.
8. Include graceful loading and error states at system boundaries.
9. Use deterministic tools and record assumptions for future automated agent actions.
10. Document every unresolved issue explicitly.
11. Update `CHANGELOG.md` after each completed phase.
12. Before finishing a phase, run backend tests, frontend tests, lint, type checks, and production build.
