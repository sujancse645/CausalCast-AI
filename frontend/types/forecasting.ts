export type ForecastExperimentStatus =
  | "pending"
  | "validating"
  | "training"
  | "backtesting"
  | "selecting"
  | "test_evaluating"
  | "completed"
  | "failed";
export type ForecastModelStatus =
  "pending" | "fitting" | "backtesting" | "completed" | "failed" | "skipped";
export type ForecastEvaluationType =
  "validation" | "backtest_fold" | "backtest_aggregate" | "final_test";
export interface ForecastModelDefinition {
  id: string;
  name: string;
  family: string;
  description: string;
  supports_groups: boolean;
  supports_trend: boolean;
  supports_seasonality: boolean;
  enabled: boolean;
  supported_feature_types?: string[];
  categorical_support?: boolean;
  tuning_support?: boolean;
  early_stopping_support?: boolean;
  explanation_support?: boolean;
  dependency_available?: boolean;
  dependency_version?: string | null;
  default_parameters?: Record<string, unknown>;
}
export interface ForecastExperimentConfig {
  target_column?: string | null;
  forecast_horizon?: number | null;
  selection_metric?: "wape" | "mae" | "rmse" | "smape" | null;
  enabled_models: string[];
  moving_average_windows?: number[] | null;
  seasonal_period?: number | null;
  backtest_folds?: number | null;
  evaluate_per_group: boolean;
  include_exogenous_features: boolean;
  linear_feature_allowlist?: string[] | null;
  notes?: string | null;
  strategy?: "global" | "per_group";
  tuning_trials?: number | null;
  tuning_timeout_seconds?: number | null;
  early_stopping_rounds?: number | null;
  generate_shap?: boolean;
  tuning_folds?: number | null;
}
export interface ForecastExperimentSummary {
  id: string;
  prepared_dataset_id: string;
  experiment_version: number;
  status: ForecastExperimentStatus;
  target_column: string;
  frequency: string;
  selected_model_run_id: string | null;
  created_at: string;
  completed_at: string | null;
}
export interface ForecastExperiment extends ForecastExperimentSummary {
  forecasting_engine_version: string;
  date_column: string;
  group_columns: string[];
  forecast_horizon: number;
  selection_metric: string;
  random_seed: number;
  configuration: Record<string, unknown>;
  prepared_artifact_checksum: string;
  source_dataset_checksum: string;
  train_start: string;
  train_end: string;
  validation_start: string;
  validation_end: string;
  test_start: string;
  test_end: string;
  backtest_fold_count: number;
  validation_completed_at: string | null;
  test_evaluated_at: string | null;
  failure_message: string | null;
  metadata: Record<string, unknown>;
}
export interface ForecastMetricSet {
  row_count: number;
  mae: number | null;
  rmse: number | null;
  wape: number | null;
  smape: number | null;
  mase: number | null;
  bias: number | null;
  mean_error: number | null;
  median_absolute_error: number | null;
  warnings: string[];
  fold_wape_standard_deviation?: number;
}
export interface ForecastResidualSummary {
  mean: number;
  standard_deviation: number;
  median: number;
  minimum: number;
  maximum: number;
  positive_ratio: number;
  autocorrelation_lag_1: number | null;
  large_residual_count: number;
}
export interface ForecastModelRun {
  id: string;
  experiment_id: string;
  model_name: string;
  model_family: string;
  status: ForecastModelStatus;
  rank: number | null;
  selection_score: number | null;
  selected: boolean;
  validation_metrics: ForecastMetricSet | null;
  backtest_metrics: ForecastMetricSet | null;
  training_duration_ms: number;
  backtest_duration_ms: number;
  failure_message: string | null;
  model_version?: string;
  hyperparameters?: Record<string, unknown>;
  fitted_on?: string;
  supports_groups?: boolean;
  supports_trend?: boolean;
  supports_seasonality?: boolean;
  artifact_checksum?: string | null;
  per_fold_metrics?: Array<Record<string, unknown>>;
  per_group_metrics?: Array<Record<string, unknown>>;
  residual_summary?: ForecastResidualSummary | null;
  completed_at?: string | null;
  tuning_method?: string | null;
  tuning_trial_count?: number;
  failed_trial_count?: number;
  tuning_duration_ms?: number;
  best_iteration?: number | null;
  best_score?: number | null;
  feature_count?: number;
  explanation_available?: boolean;
  global_model?: boolean;
  strategy?: "global" | "per_group" | null;
  dependency_version?: string | null;
}
export interface ForecastComparison {
  experiment_id: string;
  selected_model_run_id: string | null;
  selection_method: string;
  items: ForecastModelRun[];
}
export interface ForecastPrediction {
  date: string;
  actual: number;
  prediction: number;
  residual: number;
  split: string;
  fold: number | null;
  group: string | null;
}
export interface ForecastPredictionList {
  experiment_id: string;
  model_run_id: string;
  split: string;
  items: ForecastPrediction[];
  page: number;
  page_size: number;
  total: number;
  pages: number;
}
export interface ForecastStats {
  total_experiments: number;
  completed_experiments: number;
  failed_experiments: number;
  selected_model_distribution: Record<string, number>;
  average_test_wape: number | null;
  datasets_awaiting_forecasting: number;
  latest_experiment_status: string | null;
}
export interface ForecastWarning {
  code: string;
  message: string;
}
export interface ForecastValidationIssue extends ForecastWarning {
  blocking: boolean;
}
export interface ForecastArtifact {
  id: string;
  model_run_id: string;
  artifact_type: string;
  checksum: string;
  row_count: number;
  created_at: string;
}
