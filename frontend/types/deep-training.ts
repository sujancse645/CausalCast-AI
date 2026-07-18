export interface DeepTrainingMetrics {
  mae: number | null;
  rmse: number | null;
  mape: number | null;
  smape: number | null;
  wape: number | null;
  r2: number | null;
}

export interface DeepTrainingExperiment {
  experiment_id: string;
  model_run_id: string;
  prepared_dataset_id: string;
  model_name: string;
  status: string;
  current_epoch: number | null;
  max_steps: number;
  selected_accelerator: string;
  training_duration_ms: number;
  checkpoint_available: boolean;
  checkpoint_checksum: string | null;
  metrics: DeepTrainingMetrics | null;
  failure_message: string | null;
  created_at: string;
  completed_at: string | null;
}

export interface DeepTrainingList {
  items: DeepTrainingExperiment[];
  total: number;
}

export interface NHiTSTrainingRequest {
  prepared_dataset_id: string;
  readiness_snapshot_id?: string;
  configuration: Record<string, unknown>;
}
