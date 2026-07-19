import { ProductionForecastWorkspace } from "@/components/forecasting/production-forecast-workspace";
import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { beforeEach, describe, expect, it, vi } from "vitest";

const mocks = vi.hoisted(() => ({
  list: vi.fn(),
  metadata: vi.fn(),
  forecast: vi.fn(),
}));

vi.mock("@/lib/api", () => ({
  listProductionForecastDatasets: mocks.list,
  getProductionForecastDataset: mocks.metadata,
  createProductionForecast: mocks.forecast,
}));

describe("ProductionForecastWorkspace", () => {
  beforeEach(() => {
    mocks.list.mockResolvedValue([
      {
        id: "tourism",
        name: "Tourism (yearly source)",
        model_name: "xgboost_model",
        model_type: "XGBRegressor",
        target: "value",
        frequency: "yearly",
        default_horizon: 2,
        model_available: true,
        data_available: true,
      },
    ]);
    mocks.metadata.mockResolvedValue({
      id: "tourism",
      name: "Tourism (yearly source)",
      model_name: "xgboost_model",
      model_type: "XGBRegressor",
      target: "value",
      frequency: "yearly",
      default_horizon: 2,
      model_available: true,
      data_available: true,
      features: ["lag_1"],
      series_dimension: "unique_id",
      series_count: 427,
      example_series: ["T1"],
      prediction_kind: "held_out_test",
      metrics: { RMSE: 123264.1 },
      model_checksum: "checksum",
    });
    mocks.forecast.mockResolvedValue({
      dataset: "tourism",
      dataset_name: "Tourism (yearly source)",
      model_name: "xgboost_model",
      model_type: "XGBRegressor",
      model_checksum: "checksum",
      prediction_kind: "held_out_test",
      target: "value",
      frequency: "yearly",
      series: "T1",
      horizon: 2,
      rows_used: 2,
      prediction_start: "2034-01-01T00:00:00Z",
      prediction_end: "2035-01-01T00:00:00Z",
      predictions: [
        { timestamp: "2034-01-01T00:00:00Z", prediction: 8997.5, actual: 9010 },
        { timestamp: "2035-01-01T00:00:00Z", prediction: 6448.7, actual: 6500 },
      ],
      metrics: { RMSE: 123264.1 },
      runtime_ms: 44,
      model_loaded_from_disk: true,
      generated_at: "2026-07-19T00:00:00Z",
    });
  });

  it("loads real-asset metadata and renders returned predictions", async () => {
    const user = userEvent.setup();
    render(<ProductionForecastWorkspace />);

    expect(
      await screen.findByText("Model and data contract"),
    ).toBeInTheDocument();
    await user.click(screen.getByRole("button", { name: "Generate forecast" }));

    expect(
      await screen.findByText("Tourism (yearly source) result"),
    ).toBeInTheDocument();
    expect(screen.getByText("8,997.5")).toBeInTheDocument();
    expect(
      screen.getByText(/not guaranteed future outcomes/i),
    ).toBeInTheDocument();
    expect(mocks.forecast).toHaveBeenCalledWith({
      dataset: "tourism",
      horizon: 2,
      series: "T1",
    });
  });

  it("shows a backend-unavailable state", async () => {
    mocks.list.mockRejectedValue(new Error("Backend is unavailable"));
    render(<ProductionForecastWorkspace />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Backend is unavailable",
    );
    expect(
      screen.getByText("No validated model-and-dataset pairs are available."),
    ).toBeInTheDocument();
  });
});
