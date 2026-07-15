import { API_BASE_URL } from "@/lib/config";
import type { HealthResponse, SystemInfoResponse } from "@/types/api";

export class ApiError extends Error {}

async function request<T>(path: string, timeoutMs = 5000): Promise<T> {
  const controller = new AbortController();
  const timeout = setTimeout(() => controller.abort(), timeoutMs);
  try {
    const response = await fetch(`${API_BASE_URL}${path}`, {
      signal: controller.signal,
    });
    if (!response.ok) throw new ApiError(`API returned ${response.status}`);
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
