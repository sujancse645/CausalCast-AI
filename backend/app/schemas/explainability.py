from datetime import datetime
from typing import Any

from pydantic import BaseModel, Field


class ExplanationMethodSchema(BaseModel):
    name: str
    description: str
    requires_background_data: bool
    is_global: bool
    is_local: bool


class CapabilitiesResponse(BaseModel):
    supported: bool
    reason: str
    methods: list[ExplanationMethodSchema]


class ExplainabilitySummaryResponse(BaseModel):
    global_explanations_count: int
    local_shap_runs: int
    detected_anomalies: int
    active_scenarios: int


class ExplanationRequest(BaseModel):
    explanation_type: str = Field(..., description="e.g. global_feature_importance, local_feature_attribution")
    method: str = Field(..., description="e.g. tree_shap_global")
    parameters: dict[str, Any] = Field(default_factory=dict)
    force_refresh: bool = False


class ExplanationResponse(BaseModel):
    id: str
    explanation_type: str
    model_run_id: str
    prediction_id: str | None = None
    method: str
    method_version: str
    status: str
    reliability_score: float | None = None
    warnings: list[str] = Field(default_factory=list)
    limitations: list[str] = Field(default_factory=list)
    runtime_ms: int
    created_at: datetime
    # Optionally, the data could be included directly or fetched via artifact depending on size.
    # We include it for simplicity in the API response unless it's huge.
    data: dict[str, Any] | None = None
