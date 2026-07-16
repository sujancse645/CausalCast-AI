export type ConnectivityState = "checking" | "connected" | "unavailable";

export interface HealthResponse {
  status: "healthy" | "degraded";
  service: string;
  version: string;
  environment: string;
  timestamp: string;
}

export interface SystemInfoResponse {
  application: { name: string; version: string; environment: string };
  backend: { framework: "FastAPI"; status: "operational" };
  database: { type: string; status: "connected" | "unavailable" };
  modules: Record<
    | "data_intelligence"
    | "forecasting"
    | "causal_intelligence"
    | "simulation"
    | "optimization"
    | "rag_copilot",
    | "planned"
    | "next"
    | "preparation_ready"
    | "baseline_forecasting_ready"
    | "gradient_boosting_ready"
  >;
}
