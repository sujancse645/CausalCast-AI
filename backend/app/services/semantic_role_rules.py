from dataclasses import dataclass

from app.models.schema_profile import PhysicalType
from app.services.column_profiler import PhysicalProfile
from app.services.semantic_role_registry import ROLE_SYNONYMS, SemanticRole

NUMERIC_ROLES = {
    SemanticRole.revenue,
    SemanticRole.spend,
    SemanticRole.impressions,
    SemanticRole.clicks,
    SemanticRole.conversions,
    SemanticRole.orders,
    SemanticRole.units_sold,
    SemanticRole.price,
    SemanticRole.discount,
    SemanticRole.cost,
    SemanticRole.profit,
    SemanticRole.roas,
    SemanticRole.ctr,
    SemanticRole.cpc,
    SemanticRole.cpa,
    SemanticRole.conversion_rate,
    SemanticRole.sessions,
    SemanticRole.users,
    SemanticRole.inventory,
}
DATE_ROLES = {SemanticRole.date, SemanticRole.timestamp}
DIMENSION_ROLES = {
    SemanticRole.channel,
    SemanticRole.campaign,
    SemanticRole.customer_id,
    SemanticRole.product_id,
    SemanticRole.product_name,
    SemanticRole.product_category,
    SemanticRole.geography,
    SemanticRole.country,
    SemanticRole.region,
    SemanticRole.city,
    SemanticRole.device,
    SemanticRole.source,
    SemanticRole.medium,
}


@dataclass(frozen=True)
class Candidate:
    role: SemanticRole
    score: float
    evidence: list[dict[str, object]]


def candidates(profile: PhysicalProfile) -> list[Candidate]:
    results: list[Candidate] = []
    tokens = set(profile.normalized_name.split("_"))
    for role, synonyms in ROLE_SYNONYMS.items():
        name_score = 0.0
        match = ""
        if profile.normalized_name in synonyms:
            name_score, match = 0.65, "exact synonym"
        elif any(set(synonym.split("_")) <= tokens for synonym in synonyms):
            name_score, match = 0.45, "token synonym"
        elif profile.normalized_name == "value" and role in {
            SemanticRole.revenue,
            SemanticRole.price,
            SemanticRole.cost,
        }:
            name_score, match = 0.35, "generic metric name"
        if not name_score:
            continue
        compatible = (
            (role in NUMERIC_ROLES and profile.physical_type in {PhysicalType.integer, PhysicalType.float})
            or (role in DATE_ROLES and profile.physical_type in {PhysicalType.date, PhysicalType.datetime})
            or (
                role in DIMENSION_ROLES
                and profile.physical_type in {PhysicalType.categorical, PhysicalType.identifier, PhysicalType.text}
            )
            or role
            in {
                SemanticRole.promotion,
                SemanticRole.holiday,
                SemanticRole.target,
                SemanticRole.identifier,
                SemanticRole.descriptive_text,
            }
        )
        type_score = 0.25 if compatible else -0.25
        distribution = 0.1 if role in NUMERIC_ROLES and profile.nonnegative_rate >= 0.8 else 0.0
        score = max(0.0, min(1.0, name_score + type_score + distribution))
        evidence: list[dict[str, object]] = [
            {
                "evidence_type": "name_match",
                "description": match,
                "score_contribution": name_score,
                "observed_value": profile.normalized_name,
                "expected_pattern": sorted(synonyms)[0],
                "severity": "info",
            },
            {
                "evidence_type": "physical_type",
                "description": "Compatible physical type" if compatible else "Physical type conflicts with role",
                "score_contribution": type_score,
                "observed_value": profile.physical_type.value,
                "expected_pattern": "role-compatible type",
                "severity": "info" if compatible else "warning",
            },
        ]
        if distribution:
            evidence.append(
                {
                    "evidence_type": "distribution",
                    "description": "Sampled numeric values are mostly non-negative",
                    "score_contribution": distribution,
                    "observed_value": round(profile.nonnegative_rate, 3),
                    "expected_pattern": ">= 0.8",
                    "severity": "info",
                }
            )
        results.append(Candidate(role, round(score, 4), evidence))
    return sorted(results, key=lambda item: (-item.score, item.role.value))
