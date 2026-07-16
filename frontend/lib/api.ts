import { API_BASE_URL } from "@/lib/config";
import type { HealthResponse, SystemInfoResponse } from "@/types/api";
import type {
  DatasetApiErrorBody,
  DatasetArchiveResponse,
  DatasetDetail,
  DatasetListResponse,
  DatasetPreview,
  DatasetStats,
  DatasetUploadResponse,
} from "@/types/dataset";
import type {
  ColumnMappingUpdateRequest,
  DatasetSchemaDetail,
  SchemaConfirmationResponse,
  SchemaHistoryItem,
  SchemaStats,
  SemanticRoleDefinition,
} from "@/types/schema-mapping";
import type {
  QualityFindingListResponse,
  QualityHistoryItem,
  QualityReportDetail,
  QualityRuleDefinition,
  QualityStats,
} from "@/types/quality";
import type {
  PreparedFeature,
  PreparationConfig,
  PreparationPreview,
  PreparationResponse,
  PreparationStats,
  PreparationSummary,
  SplitDefinition,
  BacktestFold,
} from "@/types/preparation";
import type {
  ForecastComparison,
  ForecastExperiment,
  ForecastExperimentConfig,
  ForecastExperimentSummary,
  ForecastModelDefinition,
  ForecastModelRun,
  ForecastPredictionList,
  ForecastStats,
} from "@/types/forecasting";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly body?: DatasetApiErrorBody,
  ) {
    super(message);
  }
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  timeoutMs = 5000,
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      signal: controller.signal,
    });
    if (!response.ok) {
      const body = (await response.json().catch(() => ({
        detail: `API returned ${response.status}`,
      }))) as DatasetApiErrorBody;
      throw new ApiError(body.detail, response.status, body);
    }
    return (await response.json()) as T;
  } catch (error) {
    throw error instanceof ApiError
      ? error
      : new ApiError("Backend is unavailable");
  } finally {
    clearTimeout(timeout);
  }
}

export const getHealth = () => request<HealthResponse>("/health");
export const getSystemInfo = () =>
  request<SystemInfoResponse>("/api/v1/system/info");
export const uploadDataset = (file: File) => {
  const body = new FormData();
  body.append("file", file);
  return request<DatasetUploadResponse>(
    "/api/v1/datasets/upload",
    { method: "POST", body },
    30000,
  );
};
export const listDatasets = (
  params: {
    page?: number;
    pageSize?: number;
    search?: string;
    status?: string;
  } = {},
) => {
  const query = new URLSearchParams({
    page: String(params.page ?? 1),
    page_size: String(params.pageSize ?? 10),
  });
  if (params.search) query.set("search", params.search);
  if (params.status) query.set("status", params.status);
  return request<DatasetListResponse>(`/api/v1/datasets?${query}`);
};
export const getDataset = (id: string) =>
  request<DatasetDetail>(`/api/v1/datasets/${encodeURIComponent(id)}`);
export const getDatasetPreview = (id: string, limit = 20) =>
  request<DatasetPreview>(
    `/api/v1/datasets/${encodeURIComponent(id)}/preview?limit=${limit}`,
  );
export const archiveDataset = (id: string) =>
  request<DatasetArchiveResponse>(
    `/api/v1/datasets/${encodeURIComponent(id)}`,
    { method: "DELETE" },
  );
export const getDatasetStats = () =>
  request<DatasetStats>("/api/v1/datasets/stats");
export const getSemanticRoles = () =>
  request<{ items: SemanticRoleDefinition[] }>("/api/v1/schema/roles");
export const inferDatasetSchema = (id: string, reason?: string) =>
  request<DatasetSchemaDetail>(
    `/api/v1/datasets/${encodeURIComponent(id)}/schema/infer`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ force_reinfer: true, reason }),
    },
    30000,
  );
export const getDatasetSchema = (id: string) =>
  request<DatasetSchemaDetail>(
    `/api/v1/datasets/${encodeURIComponent(id)}/schema`,
  );
export const getSchemaHistory = (id: string) =>
  request<{ items: SchemaHistoryItem[] }>(
    `/api/v1/datasets/${encodeURIComponent(id)}/schema/history`,
  );
export const updateColumnMapping = (
  datasetId: string,
  columnId: string,
  body: ColumnMappingUpdateRequest,
) =>
  request<{
    column: import("@/types/schema-mapping").ColumnProfile;
    summary: import("@/types/schema-mapping").DatasetSchemaSummary;
  }>(
    `/api/v1/datasets/${encodeURIComponent(datasetId)}/schema/columns/${encodeURIComponent(columnId)}`,
    {
      method: "PATCH",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(body),
    },
  );
export const confirmDatasetSchema = (id: string) =>
  request<SchemaConfirmationResponse>(
    `/api/v1/datasets/${encodeURIComponent(id)}/schema/confirm`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ acknowledge_warnings: true }),
    },
  );
export const getSchemaStats = () =>
  request<SchemaStats>("/api/v1/datasets/schema/stats");
export const analyzeDatasetQuality = (id: string, notes?: string) =>
  request<QualityReportDetail>(
    `/api/v1/datasets/${encodeURIComponent(id)}/quality/analyze`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ force_reanalyze: true, notes }),
    },
    60000,
  );
export const getDatasetQuality = (id: string) =>
  request<QualityReportDetail>(
    `/api/v1/datasets/${encodeURIComponent(id)}/quality`,
  );
export const getQualityHistory = (id: string) =>
  request<{ items: QualityHistoryItem[] }>(
    `/api/v1/datasets/${encodeURIComponent(id)}/quality/history`,
  );
export const getQualityFindings = (
  id: string,
  params: {
    severity?: string;
    category?: string;
    blocking?: boolean;
    column?: string;
    page?: number;
  } = {},
) => {
  const query = new URLSearchParams({
    page: String(params.page ?? 1),
    page_size: "20",
  });
  if (params.severity) query.set("severity", params.severity);
  if (params.category) query.set("category", params.category);
  if (params.blocking !== undefined)
    query.set("blocking", String(params.blocking));
  if (params.column) query.set("column", params.column);
  return request<QualityFindingListResponse>(
    `/api/v1/datasets/${encodeURIComponent(id)}/quality/findings?${query}`,
  );
};
export const getQualityRules = () =>
  request<{ items: QualityRuleDefinition[] }>("/api/v1/quality/rules");
export const getQualityStats = () =>
  request<QualityStats>("/api/v1/datasets/quality/stats");
export const createPreparation = (id: string, config: PreparationConfig) =>
  request<PreparationResponse>(
    `/api/v1/datasets/${encodeURIComponent(id)}/preparations`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ config }),
    },
    60000,
  );
export const listPreparations = (id: string) =>
  request<{ items: PreparationSummary[] }>(
    `/api/v1/datasets/${encodeURIComponent(id)}/preparations`,
  );
export const getPreparation = (id: string) =>
  request<PreparationResponse>(
    `/api/v1/preparations/${encodeURIComponent(id)}`,
  );
export const getPreparationPreview = (id: string) =>
  request<PreparationPreview>(
    `/api/v1/preparations/${encodeURIComponent(id)}/preview`,
  );
export const getPreparationFeatures = (id: string) =>
  request<{ prepared_dataset_id: string; items: PreparedFeature[] }>(
    `/api/v1/preparations/${encodeURIComponent(id)}/features`,
  );
export const getPreparationSplits = (id: string) =>
  request<{
    prepared_dataset_id: string;
    splits: SplitDefinition[];
    backtest_folds: BacktestFold[];
  }>(`/api/v1/preparations/${encodeURIComponent(id)}/splits`);
export const getPreparationStats = () =>
  request<PreparationStats>("/api/v1/preparations/stats");
export const getPreparationDownloadUrl = (id: string) =>
  `${API_BASE_URL}/api/v1/preparations/${encodeURIComponent(id)}/download?format=csv`;
export const createForecastExperiment = (
  preparedId: string,
  config: ForecastExperimentConfig,
) =>
  request<ForecastExperiment>(
    `/api/v1/preparations/${encodeURIComponent(preparedId)}/forecast-experiments`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ config }),
    },
    300000,
  );
export const listForecastExperiments = (preparedId: string) =>
  request<{ items: ForecastExperimentSummary[] }>(
    `/api/v1/preparations/${encodeURIComponent(preparedId)}/forecast-experiments`,
  );
export const getForecastExperiment = (id: string) =>
  request<ForecastExperiment>(
    `/api/v1/forecast-experiments/${encodeURIComponent(id)}`,
  );
export const getForecastModelRuns = (id: string) =>
  request<ForecastModelRun[]>(
    `/api/v1/forecast-experiments/${encodeURIComponent(id)}/models`,
  );
export const getForecastMetrics = (id: string) =>
  request<ForecastModelRun[]>(
    `/api/v1/forecast-experiments/${encodeURIComponent(id)}/metrics`,
  );
export const getForecastComparison = (id: string) =>
  request<ForecastComparison>(
    `/api/v1/forecast-experiments/${encodeURIComponent(id)}/comparison`,
  );
export const getForecastPredictions = (
  id: string,
  params: {
    modelRunId?: string;
    split?: string;
    fold?: number;
    group?: string;
    page?: number;
    pageSize?: number;
  } = {},
) => {
  const query = new URLSearchParams({
    split: params.split ?? "test",
    page: String(params.page ?? 1),
    page_size: String(params.pageSize ?? 500),
  });
  if (params.modelRunId) query.set("model_run_id", params.modelRunId);
  if (params.fold !== undefined) query.set("fold", String(params.fold));
  if (params.group) query.set("group", params.group);
  return request<ForecastPredictionList>(
    `/api/v1/forecast-experiments/${encodeURIComponent(id)}/predictions?${query}`,
  );
};
export const getForecastModelRegistry = () =>
  request<ForecastModelDefinition[]>("/api/v1/forecasting/models");
export const getForecastStats = () =>
  request<ForecastStats>("/api/v1/forecasting/stats");
export const getForecastArtifactDownloadUrl = (
  runId: string,
  artifactType: string,
) =>
  `${API_BASE_URL}/api/v1/forecast-model-runs/${encodeURIComponent(runId)}/download?artifact_type=${encodeURIComponent(artifactType)}`;
