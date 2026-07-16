export type GradientBoostingModelName =
  "lightgbm_regressor" | "xgboost_regressor" | "catboost_regressor";
export type GradientBoostingStrategy = "global" | "per_group";
export type TuningTrialStatus = "completed" | "failed" | "pruned";
export interface TuningTrial {
  trial_number: number;
  status: TuningTrialStatus;
  parameters: Record<string, unknown>;
  backtest_metric: number | null;
  validation_metric: number | null;
  duration_ms: number;
  failure_message: string | null;
}
export interface TuningSummary {
  model_run_id: string;
  tuning_method: string | null;
  completed_trials: number;
  failed_trials: number;
  best_score: number | null;
  best_iteration: number | null;
  tuning_duration_ms: number;
  best_parameters: Record<string, unknown>;
  trials: TuningTrial[];
}
export interface FeatureImportanceItem {
  feature: string;
  native_importance: number | null;
  shap_importance: number | null;
  feature_type: string;
  leakage_status: string;
}
export interface FeatureImportance {
  model_run_id: string;
  items: FeatureImportanceItem[];
  disclaimer: string;
}
export interface ShapFeatureSummary {
  feature: string;
  mean_absolute_shap: number;
  mean_shap: number;
  direction: string;
}
export interface ShapExplanation {
  model_run_id: string;
  sample_rows: number;
  items: ShapFeatureSummary[];
  disclaimer: string;
}
export interface GradientBoostingStats {
  completed_experiments: number;
  model_wins: Record<string, number>;
  average_tuning_duration_ms: number | null;
  average_improvement_over_baseline: number | null;
  failed_model_count: number;
}
