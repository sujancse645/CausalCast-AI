export interface ProductionDatasetSummary {
  id: string;
  name: string;
  model_name: string;
  model_type: string;
  target: string;
  frequency: string;
  default_horizon: number;
  model_available: boolean;
  data_available: boolean;
}

export interface ProductionDatasetMetadata extends ProductionDatasetSummary {
  features: string[];
  series_dimension: string | null;
  series_count: number | null;
  example_series: string[];
  prediction_kind: string;
  metrics: Record<string, number>;
  model_checksum: string | null;
}

export interface ProductionPrediction {
  timestamp: string;
  prediction: number;
  actual: number | null;
}

export interface ProductionForecastRequest {
  dataset: string;
  horizon?: number;
  series?: string;
}

export interface ProductionForecastResponse {
  dataset: string;
  dataset_name: string;
  model_name: string;
  model_type: string;
  model_checksum: string;
  prediction_kind: string;
  target: string;
  frequency: string;
  series: string | null;
  horizon: number;
  rows_used: number;
  prediction_start: string;
  prediction_end: string;
  predictions: ProductionPrediction[];
  metrics: Record<string, number>;
  runtime_ms: number;
  model_loaded_from_disk: boolean;
  generated_at: string;
}
