export type DeepForecastModelIdentifier =
  "nhits" | "temporal_fusion_transformer" | "nbeats";
export type DeepForecastModelStatus =
  | "unavailable"
  | "dependency_missing"
  | "planned"
  | "infrastructure_ready"
  | "training_ready"
  | "experimental"
  | "production_ready"
  | "disabled";
export interface DeepForecastModelDefinition {
  identifier: DeepForecastModelIdentifier;
  display_name: string;
  family: string;
  description: string;
  implementation_status: DeepForecastModelStatus;
  enabled_by_default: boolean;
  dependency_name: string;
  dependency_available: boolean;
  supported_frequencies: string[];
  supports_grouped_series: boolean;
  supports_global_model: boolean;
  supports_per_group_model: boolean;
  supports_historical_covariates: boolean;
  supports_future_covariates: boolean;
  supports_static_covariates: boolean;
  supports_quantiles: boolean;
  supports_probabilistic_loss: boolean;
  supports_gpu: boolean;
  supports_cpu: boolean;
  supports_checkpointing: boolean;
  supports_early_stopping: boolean;
  supports_explainability: boolean;
  minimum_history_formula: string;
  recommended_input_window: string;
  recommended_horizon: string;
  known_limitations: string[];
  future_phase: string;
}
export interface DeepForecastDependency {
  package_name: string;
  installed: boolean;
  version: string | null;
  minimum_supported_version: string | null;
  maximum_tested_version: string | null;
  compatible: boolean;
  import_error_category: string | null;
  required: boolean;
  optional: boolean;
  models_affected: string[];
}
export interface DeepForecastHardware {
  operating_system: string;
  python_architecture: string;
  cpu_logical_count: number;
  configured_training_threads: number;
  available_memory_bytes: number | null;
  pytorch_available: boolean;
  cuda_available: boolean;
  cuda_device_count: number;
  cuda_device_names: string[];
  cuda_version: string | null;
  mps_available: boolean;
  selected_accelerator: "cpu" | "cuda" | "mps";
  selected_device_count: number;
  cpu_fallback_enabled: boolean;
  deterministic_mode_configured: boolean;
}
export interface DeepForecastCapability {
  enabled: boolean;
  engine: string;
  infrastructure_status: string;
  training_status: "not_implemented_in_part_1";
  selected_accelerator: string;
  models: DeepForecastModelDefinition[];
  dependencies: DeepForecastDependency[];
  hardware: DeepForecastHardware;
  limits: Record<string, number>;
}
export interface DeepForecastReadinessRequest {
  model_name: DeepForecastModelIdentifier;
  target_column?: string;
  time_column?: string;
  group_columns?: string[];
  horizon: number;
  input_size?: number;
  historical_covariates?: string[];
  future_covariates?: string[];
  static_covariates?: string[];
  scaler_type:
    "none" | "standard" | "robust" | "minmax" | "median" | "identity";
  scale_per_series: boolean;
  target_transform: "none" | "log1p" | "signed_log1p" | "boxcox" | "yeojohnson";
  accelerator?: "auto" | "cpu" | "cuda" | "mps";
}
export interface DeepForecastCovariate {
  name: string;
  category: "historical" | "future" | "static" | "excluded";
  approved_for_deep_forecasting: boolean;
  exclusion_reason: string | null;
  future_coverage_status: string;
}
export interface DeepForecastSeriesReadiness {
  series_id: string;
  eligible: boolean;
  observation_count: number;
  required_observations: number;
  missing_target_count: number;
  training_windows: number;
  validation_windows: number;
  test_windows: number;
  failure_reasons: string[];
}
export interface DeepForecastSequenceSummary {
  input_size: number;
  horizon: number;
  minimum_history: number;
  total_training_windows: number;
  total_validation_windows: number;
  total_test_windows: number;
}
export interface DeepForecastReadiness {
  snapshot_id: string;
  prepared_dataset_id: string;
  readiness_status:
    | "ready"
    | "ready_with_warnings"
    | "blocked"
    | "dependency_missing"
    | "disabled";
  deep_forecasting_ready: boolean;
  series_count: number;
  eligible_series_count: number;
  ineligible_series_count: number;
  historical_covariate_count: number;
  future_covariate_count: number;
  static_covariate_count: number;
  target_column: string;
  frequency: string;
  input_size: number;
  horizon: number;
  covariates: DeepForecastCovariate[];
  series: DeepForecastSeriesReadiness[];
  sequence_summary: DeepForecastSequenceSummary;
  warnings: string[];
  blockers: string[];
  synthetic_data: boolean;
  selected_accelerator: string;
  dependency_status: string;
  artifact_checksums: Record<string, string>;
  training_executed: false;
  checkpoint_created: false;
}
