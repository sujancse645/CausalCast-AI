import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import {
  DeepForecastingStatusCard,
  DeepReadinessPanel,
} from "@/components/forecasting/deep-forecasting";

const capability = {
  enabled: true,
  engine: "neuralforecast",
  infrastructure_status: "ready",
  training_status: "not_implemented_in_part_1",
  selected_accelerator: "cpu",
  hardware: {
    operating_system: "Windows",
    python_architecture: "64bit",
    cpu_logical_count: 8,
    configured_training_threads: 4,
    available_memory_bytes: null,
    pytorch_available: false,
    cuda_available: false,
    cuda_device_count: 0,
    cuda_device_names: [],
    cuda_version: null,
    mps_available: false,
    selected_accelerator: "cpu",
    selected_device_count: 1,
    cpu_fallback_enabled: true,
    deterministic_mode_configured: true,
  },
  models: [
    ["nhits", "N-HiTS", "infrastructure_ready"],
    ["temporal_fusion_transformer", "Temporal Fusion Transformer", "planned"],
    ["nbeats", "N-BEATS", "planned"],
  ].map(([identifier, display_name, implementation_status]) => ({
    identifier,
    display_name,
    implementation_status,
    family: "deep",
    description: `${display_name} model`,
    enabled_by_default: identifier === "nhits",
    dependency_name: "neuralforecast",
    dependency_available: false,
    supported_frequencies: ["daily"],
    supports_grouped_series: true,
    supports_global_model: true,
    supports_per_group_model: false,
    supports_historical_covariates: true,
    supports_future_covariates: true,
    supports_static_covariates: true,
    supports_quantiles: false,
    supports_probabilistic_loss: false,
    supports_gpu: true,
    supports_cpu: true,
    supports_checkpointing: true,
    supports_early_stopping: true,
    supports_explainability: false,
    minimum_history_formula: "formula",
    recommended_input_window: "window",
    recommended_horizon: "horizon",
    known_limitations: [],
    future_phase: "later",
  })),
  dependencies: [],
  limits: {},
};

describe("deep forecasting foundation", () => {
  it("renders engine, CPU, and planned model statuses", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({ ok: true, json: async () => capability }),
    );
    render(<DeepForecastingStatusCard />);
    expect(screen.getByRole("status")).toHaveTextContent("Loading");
    await waitFor(() => expect(screen.getByText("N-HiTS")).toBeInTheDocument());
    expect(screen.getByText("CPU")).toBeInTheDocument();
    expect(screen.getAllByText("planned")).toHaveLength(2);
    expect(
      screen.getByText(/training is not implemented/i),
    ).toBeInTheDocument();
  });

  it("renders an offline capability error", async () => {
    vi.stubGlobal("fetch", vi.fn().mockRejectedValue(new Error("offline")));
    render(<DeepForecastingStatusCard />);
    await waitFor(() =>
      expect(screen.getByRole("alert")).toHaveTextContent(/offline/i),
    );
  });

  it("submits readiness and renders truthful blockers", async () => {
    const report = {
      readiness_status: "blocked",
      eligible_series_count: 3,
      series_count: 4,
      input_size: 120,
      horizon: 30,
      historical_covariate_count: 2,
      future_covariate_count: 5,
      static_covariate_count: 1,
      synthetic_data: true,
      blockers: ["One series is ineligible."],
      warnings: ["Optional dependency missing."],
      sequence_summary: { total_training_windows: 100 },
    };
    const fetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: false,
        status: 404,
        json: async () => ({ detail: "none" }),
      })
      .mockResolvedValueOnce({ ok: true, json: async () => report });
    vi.stubGlobal("fetch", fetch);
    render(
      <DeepReadinessPanel preparedId="00000000-0000-4000-8000-000000000001" />,
    );
    await userEvent.click(
      screen.getByRole("button", { name: /analyze deep readiness/i }),
    );
    await waitFor(() =>
      expect(screen.getByText("One series is ineligible.")).toBeInTheDocument(),
    );
    expect(
      screen.getByText(/Synthetic demonstration data/),
    ).toBeInTheDocument();
    expect(fetch).toHaveBeenLastCalledWith(
      expect.stringContaining("/deep-readiness"),
      expect.objectContaining({ method: "POST" }),
    );
  });
});
