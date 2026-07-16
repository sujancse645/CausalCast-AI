export type PreparationStatus =
  "pending" | "running" | "completed" | "failed" | "superseded";
export type PreparationReadinessStatus =
  | "configuration_required"
  | "preparing"
  | "review_required"
  | "model_ready"
  | "blocked";
export interface PreparationConfig {
  target_column: string;
  date_column: string;
  group_columns: string[];
  frequency: "hourly" | "daily" | "weekly" | "monthly" | "quarterly";
  forecast_horizon: number;
  aggregation_rules: Record<string, "sum" | "mean" | "last" | "min" | "max">;
  duplicate_period_policy: "aggregate" | "reject";
  missing_period_policy:
    "preserve" | "insert_null" | "insert_zero_for_flow_metrics" | "reject";
  missing_target_policy: "preserve" | "drop_rows_missing_target";
  lag_periods: number[];
  rolling_windows: number[];
  rolling_statistics: Array<"mean" | "sum" | "min" | "max">;
  include_calendar_features: boolean;
  include_trend_features: boolean;
  include_holiday_features: boolean;
  holiday_dates: string[];
  include_promotion_features: boolean;
  include_derived_metrics: boolean;
  include_missingness_indicators: boolean;
  train_ratio: number;
  validation_ratio: number;
  test_ratio: number;
  backtest_folds: number;
  quality_override: boolean;
  quality_override_reason: string | null;
  output_format: "csv";
}
export interface PreparationSummary {
  id: string;
  source_dataset_id: string;
  preparation_version: number;
  status: PreparationStatus;
  readiness_status: PreparationReadinessStatus;
  row_count: number;
  column_count: number;
  feature_count: number;
  frequency: string;
  created_at: string;
}
export interface PreparationResponse extends PreparationSummary {
  preparation_engine_version: string;
  source_schema_version: number;
  source_quality_report_version: number;
  source_checksum: string;
  prepared_checksum: string | null;
  target_column: string;
  date_column: string;
  group_columns: string[];
  forecast_horizon: number;
  train_rows: number;
  validation_rows: number;
  test_rows: number;
  dropped_rows: number;
  generated_rows: number;
  duration_ms: number;
  warnings: Array<{ code: string; message: string }>;
  configuration: PreparationConfig;
  completed_at: string | null;
}
export interface PreparedFeature {
  id: string;
  feature_name: string;
  source_columns: string[];
  feature_type: string;
  transformation_type: string;
  semantic_role: string;
  physical_type: string;
  availability_type: string;
  leakage_risk: string;
  included: boolean;
  generated: boolean;
  parameters: Record<string, unknown>;
  lineage: Record<string, unknown>;
  description: string;
}
export interface SplitDefinition {
  name: "train" | "validation" | "test";
  start: string;
  end: string;
  rows: number;
}
export interface BacktestFold {
  fold: number;
  train_start: string;
  train_end: string;
  validation_start: string;
  validation_end: string;
}
export interface PreparationPreview {
  prepared_dataset_id: string;
  columns: string[];
  rows: Array<Record<string, string | null>>;
  returned_rows: number;
}
export interface PreparationStats {
  total_prepared_datasets: number;
  model_ready_datasets: number;
  failed_preparations: number;
  average_feature_count: number | null;
  average_duration_ms: number | null;
  datasets_awaiting_preparation: number;
}
