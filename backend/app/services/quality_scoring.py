from app.models.quality import QualityReadiness

WEIGHTS = {
    "completeness": 0.15,
    "uniqueness": 0.10,
    "validity": 0.20,
    "consistency": 0.15,
    "temporal": 0.15,
    "integrity": 0.10,
    "leakage_safety": 0.15,
}
PENALTIES = {"blocker": 50.0, "error": 20.0, "warning": 7.0, "info": 1.0}
CATEGORY_DIMENSION = {
    "completeness": "completeness",
    "uniqueness": "uniqueness",
    "validity": "validity",
    "consistency": "consistency",
    "metric_relationship": "consistency",
    "temporal": "temporal",
    "schema": "integrity",
    "integrity": "integrity",
    "cardinality": "integrity",
    "outlier": "validity",
    "leakage": "leakage_safety",
}


def score(findings: list[dict[str, object]], blocker_cap: int) -> tuple[dict[str, float], float, QualityReadiness]:
    dimensions = {name: 100.0 for name in WEIGHTS}
    for finding in findings:
        dimension = CATEGORY_DIMENSION.get(str(finding["category"]), "integrity")
        dimensions[dimension] = max(0.0, dimensions[dimension] - PENALTIES[str(finding["severity"])])
    overall = round(sum(dimensions[name] * weight for name, weight in WEIGHTS.items()), 2)
    blockers = sum(bool(item["blocking"]) for item in findings)
    errors = sum(item["severity"] == "error" for item in findings)
    warnings = sum(item["severity"] == "warning" for item in findings)
    if blockers:
        overall = min(overall, float(blocker_cap))
        readiness = QualityReadiness.blocked
    elif errors:
        readiness = QualityReadiness.needs_attention
    elif overall >= 90 and warnings <= 2:
        readiness = QualityReadiness.quality_ready
    else:
        readiness = QualityReadiness.conditionally_ready
    return dimensions, overall, readiness
