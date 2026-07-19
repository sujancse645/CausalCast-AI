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
import type {
  FeatureImportance,
  GradientBoostingStats,
  ShapExplanation,
  TuningSummary,
} from "@/types/gradient-boosting";
import type {
  DeepForecastCapability,
  DeepForecastDependency,
  DeepForecastHardware,
  DeepForecastModelDefinition,
  DeepForecastReadiness,
  DeepForecastReadinessRequest,
} from "@/types/deep-forecasting";
import type {
  DeepTrainingExperiment,
  DeepTrainingList,
  NHiTSTrainingRequest,
} from "@/types/deep-training";
import type {
  RagChatRequest,
  RagDocumentListResponse,
  RagSearchRequest,
  RagSearchResponse,
  RagStreamEvent,
} from "@/types/rag";
import type {
  ProductionDatasetMetadata,
  ProductionDatasetSummary,
  ProductionForecastRequest,
  ProductionForecastResponse,
} from "@/types/production-forecast";

export class ApiError extends Error {
  constructor(
    message: string,
    public readonly status?: number,
    public readonly body?: DatasetApiErrorBody,
  ) {
    super(message);
  }
}

let authToken: string | null = null;
let tokenPromise: Promise<string | null> | null = null;

function getErrorMessage(body: DatasetApiErrorBody, status: number): string {
  if (typeof body.detail === "string") return body.detail;
  if (Array.isArray(body.detail)) {
    const messages = body.detail
      .map((item) =>
        item && typeof item === "object" && "msg" in item
          ? String(item.msg)
          : null,
      )
      .filter((message): message is string => Boolean(message));
    if (messages.length > 0) return messages.join("; ");
  }
  return `API returned ${status}`;
}

async function getAuthToken(): Promise<string | null> {
  if (authToken) return authToken;
  if (tokenPromise) return tokenPromise;

  tokenPromise = Promise.resolve()
    .then(() =>
      fetch(`${API_BASE_URL}/api/v1/auth/login/developer`, {
        method: "POST",
      }),
    )
    .then(async (res) => {
      if (res.ok) {
        const data = await res.json();
        authToken = data.access_token;
        return authToken;
      }
      return null;
    })
    .catch(() => null);

  return tokenPromise;
}

async function request<T>(
  path: string,
  options: RequestInit = {},
  timeoutMs = 5000,
): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const headers = new Headers(options.headers);
    const token = await getAuthToken();
    if (token) {
      headers.set("Authorization", `Bearer ${token}`);
    }

    const response = await fetch(`${API_BASE_URL}${path}`, {
      ...options,
      headers,
      signal: controller.signal,
    });
    if (!response.ok) {
      const body = (await response.json().catch(() => ({
        detail: `API returned ${response.status}`,
      }))) as DatasetApiErrorBody;
      throw new ApiError(getErrorMessage(body, response.status), response.status, body);
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
export const getForecastModelTuning = (runId: string) =>
  request<TuningSummary>(
    `/api/v1/forecast-model-runs/${encodeURIComponent(runId)}/tuning`,
  );
export const getForecastFeatureImportance = (runId: string) =>
  request<FeatureImportance>(
    `/api/v1/forecast-model-runs/${encodeURIComponent(runId)}/feature-importance`,
  );
export const getForecastShap = (runId: string, limit = 50) =>
  request<ShapExplanation>(
    `/api/v1/forecast-model-runs/${encodeURIComponent(runId)}/shap?limit=${limit}`,
  );
export const getGradientBoostingStats = () =>
  request<GradientBoostingStats>("/api/v1/forecasting/gradient-boosting/stats");
export const getDeepForecastCapabilities = () =>
  request<DeepForecastCapability>("/api/v1/forecasting/deep/capabilities");
export const getDeepForecastModels = () =>
  request<DeepForecastModelDefinition[]>("/api/v1/forecasting/deep/models");
export const getDeepForecastHardware = () =>
  request<DeepForecastHardware>("/api/v1/forecasting/deep/hardware");
export const getDeepForecastDependencies = () =>
  request<DeepForecastDependency[]>("/api/v1/forecasting/deep/dependencies");
export const createDeepReadinessReport = (
  preparedId: string,
  payload: DeepForecastReadinessRequest,
) =>
  request<DeepForecastReadiness>(
    `/api/v1/preparations/${encodeURIComponent(preparedId)}/deep-readiness`,
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    30000,
  );
export const getDeepReadinessReport = (preparedId: string) =>
  request<DeepForecastReadiness>(
    `/api/v1/preparations/${encodeURIComponent(preparedId)}/deep-readiness`,
  );
export const trainNHiTS = (payload: NHiTSTrainingRequest) =>
  request<DeepTrainingExperiment>(
    "/api/v1/deep/train/nhits",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    900000,
  );
export const getDeepTrainingStatus = () =>
  request<DeepTrainingList>("/api/v1/deep/train/status");
export const getDeepExperiments = () =>
  request<DeepTrainingList>("/api/v1/deep/experiments");
export const getDeepExperiment = (identifier: string) =>
  request<DeepTrainingExperiment>(
    `/api/v1/deep/experiments/${encodeURIComponent(identifier)}`,
  );
export const getForecastArtifactDownloadUrl = (
  runId: string,
  artifactType: string,
) =>
  `${API_BASE_URL}/api/v1/forecast-model-runs/${encodeURIComponent(runId)}/download?artifact_type=${encodeURIComponent(artifactType)}`;

export const listProductionForecastDatasets = () =>
  request<ProductionDatasetSummary[]>("/api/v1/forecast-datasets");

export const getProductionForecastDataset = (dataset: string) =>
  request<ProductionDatasetMetadata>(
    `/api/v1/forecast-datasets/${encodeURIComponent(dataset)}/metadata`,
  );

export const createProductionForecast = (payload: ProductionForecastRequest) =>
  request<ProductionForecastResponse>(
    "/api/v1/forecast",
    {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify(payload),
    },
    120000,
  );

export interface DashboardResponse {
  id: string;
  name: string;
  dashboard_type: string;
  description?: string;
  status: string;
  widgets: DashboardWidgetResponse[];
}
export interface DashboardWidgetResponse {
  id: string;
  title: string;
  widget_type: string;
  metric_id?: string | null;
  data_source?: string | null;
  configuration: Record<string, unknown>;
  filters: Record<string, unknown>;
  layout: Record<string, unknown>;
}
export async function getDashboards(): Promise<DashboardResponse[]> {
  return request<DashboardResponse[]>("/api/v1/analytics/dashboards");
}

export interface ExplainabilitySummary {
  global_explanations_count: number;
  local_shap_runs: number;
  detected_anomalies: number;
  active_scenarios: number;
}
export async function getExplainabilitySummary(): Promise<ExplainabilitySummary> {
  return request<ExplainabilitySummary>("/api/v1/explainability/summary");
}

export const searchProjectDocuments = (payload: RagSearchRequest) =>
  request<RagSearchResponse>("/api/v1/search", {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify(payload),
  });

export const listProjectDocuments = () =>
  request<RagDocumentListResponse>("/api/v1/documents");

export async function streamRagChat(
  payload: RagChatRequest,
  onEvent: (event: RagStreamEvent) => void,
): Promise<void> {
  const headers = new Headers({
    Accept: "text/event-stream",
    "Content-Type": "application/json",
  });
  const token = await getAuthToken();
  if (token) headers.set("Authorization", `Bearer ${token}`);

  const response = await fetch(`${API_BASE_URL}/api/v1/chat`, {
    method: "POST",
    headers,
    body: JSON.stringify({ ...payload, stream: true }),
  });
  if (!response.ok) {
    const body = (await response.json().catch(() => ({
      detail: `API returned ${response.status}`,
    }))) as DatasetApiErrorBody;
    throw new ApiError(getErrorMessage(body, response.status), response.status, body);
  }
  if (!response.body) throw new ApiError("The response stream is unavailable");

  const reader = response.body.getReader();
  const decoder = new TextDecoder();
  let buffer = "";
  while (true) {
    const { done, value } = await reader.read();
    buffer += decoder.decode(value, { stream: !done });
    const events = buffer.split("\n\n");
    buffer = events.pop() ?? "";
    for (const event of events) {
      const data = event
        .split("\n")
        .find((line) => line.startsWith("data:"))
        ?.slice(5)
        .trim();
      if (data) onEvent(JSON.parse(data) as RagStreamEvent);
    }
    if (done) break;
  }
}
