export type PhysicalType =
  | "integer"
  | "float"
  | "boolean"
  | "date"
  | "datetime"
  | "categorical"
  | "identifier"
  | "text"
  | "empty"
  | "mixed"
  | "unknown";
export type MappingStatus =
  "proposed" | "confirmed" | "manually_overridden" | "rejected" | "unresolved";
export type SchemaStatus =
  | "pending"
  | "inferred"
  | "needs_review"
  | "confirmed"
  | "superseded"
  | "failed";
export interface SemanticRoleDefinition {
  role: string;
  label: string;
  description: string;
}
export interface ColumnEvidence {
  evidence_type: string;
  description: string;
  score_contribution: number;
  observed_value: string | number | boolean | null;
  expected_pattern: string;
  severity: string;
}
export interface ColumnCandidate {
  role: string;
  confidence_score: number;
  summary_evidence: string[];
}
export interface SchemaValidationIssue {
  code: string;
  message: string;
  severity: string;
  column_names: string[];
}
export interface ColumnProfile {
  id: string;
  column_index: number;
  column_name: string;
  normalized_column_name: string;
  physical_type: PhysicalType;
  semantic_role: string;
  confidence_score: number;
  confirmation_status: MappingStatus;
  decision_source: string;
  nullable: boolean;
  null_count: number;
  sample_count: number;
  unique_count: number;
  parse_success_rate: number;
  numeric_min: number | null;
  numeric_max: number | null;
  numeric_mean: number | null;
  date_min: string | null;
  date_max: string | null;
  string_min_length: number | null;
  string_max_length: number | null;
  sample_values: string[];
  evidence: ColumnEvidence[];
  alternatives: ColumnCandidate[];
  warnings: SchemaValidationIssue[];
}
export interface DatasetSchemaSummary {
  total_columns: number;
  mapped_columns: number;
  confirmed_columns: number;
  unresolved_columns: number;
  ambiguous_columns: number;
  average_confidence: number;
  primary_date_candidate: string | null;
  primary_target_candidate: string | null;
  revenue_candidate: string | null;
  spend_candidate: string | null;
  available_marketing_dimensions: string[];
  available_performance_metrics: string[];
  blocking_issues: SchemaValidationIssue[];
  warnings: SchemaValidationIssue[];
  readiness_status: string;
}
export interface DatasetSchemaDetail {
  id: string;
  dataset_id: string;
  dataset_filename: string;
  dataset_row_count: number;
  dataset_column_count: number;
  schema_version: number;
  inference_version: string;
  status: SchemaStatus;
  created_at: string;
  updated_at: string;
  confirmed_at: string | null;
  source_checksum: string;
  sample_row_count: number;
  summary: DatasetSchemaSummary;
  columns: ColumnProfile[];
}
export interface SchemaHistoryItem {
  id: string;
  schema_version: number;
  inference_version: string;
  status: SchemaStatus;
  created_at: string;
  confirmed_at: string | null;
  mapped_columns: number;
  confirmed_columns: number;
  unresolved_columns: number;
}
export interface ColumnMappingUpdateRequest {
  semantic_role: string;
  reason?: string;
}
export interface SchemaConfirmationResponse {
  dataset_id: string;
  schema_profile_id: string;
  schema_version: number;
  status: "confirmed";
  confirmed_at: string;
  summary: DatasetSchemaSummary;
}
export interface SchemaStats {
  awaiting_review: number;
  confirmed_schemas: number;
  unresolved_columns: number;
}
