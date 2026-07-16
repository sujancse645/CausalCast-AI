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
13. Treat every uploaded file as untrusted; ingestion must be streaming, bounded, and format-validated.
14. Dataset identifiers exposed outside the backend must be collision-resistant public UUIDs.
15. Never expose internal storage paths, temporary names, or server filesystem details through APIs.
16. Raw datasets are immutable and must never be committed; transformations create traceable derived versions.
17. Future schema inference and analysis must preserve lineage and must not modify raw files.
18. Semantic inference must be explainable and confidence scores deterministic and reproducible.
19. Low-confidence or ambiguous mappings require human review; they are never silently confirmed.
20. Manual overrides must be audited and schema-versioned; future forecasting may use only confirmed mappings.
21. LLM output must never replace deterministic schema validation.
22. Quality analysis never mutates raw data; every score and finding must be reproducible from bounded evidence.
23. Label heuristics explicitly, especially leakage risks, and never overstate them as proven defects.
24. Quality-ready does not mean forecast-ready; future cleaning creates versioned derived datasets with preserved lineage.
25. Every preparation creates a versioned derived artifact with source checksum, configuration, and feature lineage.
26. Time-series splits are chronological; test data never influences transformations or model selection.
27. Lag and rolling features use historical observations only; target-derived same-period features are excluded by default.
28. Final model training may consume only governed prepared datasets, never raw uploads directly.
29. Gradient-boosting tuning uses chronological folds only; final test rows never influence tuning or ranking.
30. Feature importance and SHAP describe model contribution, never causal effect.
31. Failed models and tuning trials remain visible, and all advanced models are compared with executed naïve baselines.
29. Forecast models train only on checksum-verified, model-ready prepared artifacts.
30. Test data cannot influence preprocessing, tuning, ranking, or model selection.
31. Every model is compared with naïve baselines; failed and skipped models remain visible.
32. Forecast metrics must come from executed predictions and synthetic-data metrics must be labelled.
33. Model artifacts require checksums; final test evaluation is controlled and cannot be fabricated.
