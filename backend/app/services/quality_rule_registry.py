from dataclasses import dataclass


@dataclass(frozen=True)
class QualityRule:
    code: str
    category: str
    title: str
    description: str


RULES = (
    QualityRule("DQ_SCHEMA_001", "schema", "Schema requires review", "The active mapping is not fully confirmed."),
    QualityRule("DQ_COMPLETENESS_001", "completeness", "Missing values", "A mapped column contains null-like values."),
    QualityRule("DQ_COMPLETENESS_002", "completeness", "Empty column", "A column contains no observed values."),
    QualityRule("DQ_DUPLICATE_001", "uniqueness", "Duplicate rows", "Exact row fingerprints repeat."),
    QualityRule("DQ_DUPLICATE_002", "uniqueness", "Duplicate business keys", "A candidate business key repeats."),
    QualityRule("DQ_VALIDITY_001", "validity", "Type inconsistency", "Values conflict with the mapped physical type."),
    QualityRule("DQ_VALIDITY_002", "validity", "Invalid metric values", "A metric contains invalid ranges or signs."),
    QualityRule("DQ_OUTLIER_001", "outlier", "Robust outliers", "Numeric values exceed IQR fences."),
    QualityRule("DQ_CARDINALITY_001", "cardinality", "Constant column", "A column has one observed value."),
    QualityRule("DQ_CARDINALITY_002", "cardinality", "High-cardinality dimension", "A dimension is nearly unique."),
    QualityRule("DQ_TEMPORAL_001", "temporal", "Invalid dates", "Primary-date values fail deterministic parsing."),
    QualityRule("DQ_TEMPORAL_002", "temporal", "Temporal gaps", "Observed intervals exceed the dominant interval."),
    QualityRule("DQ_TEMPORAL_003", "temporal", "Source dates out of order", "Dates move backward in source order."),
    QualityRule("DQ_TEMPORAL_004", "temporal", "Future dates", "Dates occur after the UTC analysis date."),
    QualityRule(
        "DQ_RELATIONSHIP_001",
        "metric_relationship",
        "Metric relationship inconsistency",
        "Mapped metrics conflict with expected approximate relationships.",
    ),
    QualityRule("DQ_LEAKAGE_001", "leakage", "Target copy leakage", "A non-target column is identical to the target."),
    QualityRule(
        "DQ_LEAKAGE_002", "leakage", "Future or post-outcome indicator", "A name suggests future availability."
    ),
    QualityRule(
        "DQ_LEAKAGE_003", "leakage", "Target-derived metric risk", "A metric may mathematically depend on target."
    ),
)
