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
