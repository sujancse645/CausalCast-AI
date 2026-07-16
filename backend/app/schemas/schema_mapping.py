from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class SemanticRoleDefinition(BaseModel):
    role: str
    label: str
    description: str


class SchemaRoleListResponse(BaseModel):
    items: list[SemanticRoleDefinition]


class ColumnEvidence(BaseModel):
    evidence_type: str
    description: str
    score_contribution: float
    observed_value: str | float | int | bool | None
    expected_pattern: str
    severity: str


class ColumnCandidate(BaseModel):
    role: str
    confidence_score: float
    summary_evidence: list[str]


class SchemaValidationIssue(BaseModel):
    code: str
    message: str
    severity: str
    column_names: list[str] = []


class ColumnProfileResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    id: str
    column_index: int
    column_name: str
    normalized_column_name: str
    physical_type: str
    semantic_role: str
    confidence_score: float
    confirmation_status: str
    decision_source: str
    nullable: bool
    null_count: int
    sample_count: int
    unique_count: int
    parse_success_rate: float
    numeric_min: float | None
    numeric_max: float | None
    numeric_mean: float | None
    date_min: str | None
    date_max: str | None
    string_min_length: int | None
    string_max_length: int | None
    sample_values: list[str]
    evidence: list[ColumnEvidence]
    alternatives: list[ColumnCandidate]
    warnings: list[SchemaValidationIssue]


class DatasetSchemaSummary(BaseModel):
    total_columns: int
    mapped_columns: int
    confirmed_columns: int
    unresolved_columns: int
    ambiguous_columns: int
    average_confidence: float
    primary_date_candidate: str | None
    primary_target_candidate: str | None
    revenue_candidate: str | None
    spend_candidate: str | None
    available_marketing_dimensions: list[str]
    available_performance_metrics: list[str]
    blocking_issues: list[SchemaValidationIssue]
    warnings: list[SchemaValidationIssue]
    readiness_status: str


class DatasetSchemaDetail(BaseModel):
    id: str
    dataset_id: str
    dataset_filename: str
    dataset_row_count: int
    dataset_column_count: int
    schema_version: int
    inference_version: str
    status: str
    created_at: datetime
    updated_at: datetime
    confirmed_at: datetime | None
    source_checksum: str
    sample_row_count: int
    summary: DatasetSchemaSummary
    columns: list[ColumnProfileResponse]


class SchemaInferenceRequest(BaseModel):
    force_reinfer: bool = False
    reason: str | None = Field(default=None, max_length=500)


class SchemaInferenceResponse(DatasetSchemaDetail):
    pass


class SchemaHistoryItem(BaseModel):
    id: str
    schema_version: int
    inference_version: str
    status: str
    created_at: datetime
    confirmed_at: datetime | None
    mapped_columns: int
    confirmed_columns: int
    unresolved_columns: int


class SchemaHistoryResponse(BaseModel):
    items: list[SchemaHistoryItem]


class ColumnMappingUpdateRequest(BaseModel):
    semantic_role: str
    reason: str | None = Field(default=None, max_length=500)


class ColumnMappingUpdateResponse(BaseModel):
    column: ColumnProfileResponse
    summary: DatasetSchemaSummary


class SchemaConfirmationRequest(BaseModel):
    acknowledge_warnings: bool = False


class SchemaConfirmationResponse(BaseModel):
    dataset_id: str
    schema_profile_id: str
    schema_version: int
    status: str
    confirmed_at: datetime
    summary: DatasetSchemaSummary


class SchemaStatsResponse(BaseModel):
    awaiting_review: int
    confirmed_schemas: int
    unresolved_columns: int
