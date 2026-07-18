import { render, screen } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { describe, expect, it, vi } from "vitest";
import {
  ForecastExperimentConfigPanel,
  ModelLeaderboard,
  SyntheticDataNotice,
} from "@/components/forecasting/forecasting";
import {
  AdvancedModelSelector,
  ExplanationDisclaimer,
  TuningSummaryPanel,
} from "@/components/forecasting/gradient-boosting";

const models = [
  {
    id: "naive_last",
    name: "Last Value Naive",
    family: "naive",
    description: "Repeats history.",
    supports_groups: true,
    supports_trend: false,
    supports_seasonality: false,
    enabled: true,
  },
];

describe("forecasting UI", () => {
  it("renders synthetic notice and baseline selector", () => {
    render(
      <>
        <SyntheticDataNotice />
        <ForecastExperimentConfigPanel
          models={models}
          onSubmit={vi.fn()}
          busy={false}
        />
      </>,
    );
    expect(screen.getByText(/synthetic data/i)).toBeInTheDocument();
    expect(screen.getByText("Last Value Naive")).toBeInTheDocument();
  });

  it("validates horizon and submits typed config", async () => {
    const submit = vi.fn();
    const user = userEvent.setup();
    render(
      <ForecastExperimentConfigPanel
        models={models}
        onSubmit={submit}
        busy={false}
      />,
    );
    const horizon = screen.getByLabelText("Forecast horizon");
    await user.clear(horizon);
    await user.type(horizon, "0");
    expect(screen.getByRole("alert")).toBeInTheDocument();
    await user.clear(horizon);
    await user.type(horizon, "30");
    await user.click(screen.getByRole("button", { name: /run baseline/i }));
    expect(submit).toHaveBeenCalledWith(
      expect.objectContaining({
        forecast_horizon: 30,
        selection_metric: "wape",
      }),
    );
  });

  it("keeps failed models visible and missing metrics non-zero", () => {
    render(
      <ModelLeaderboard
        runs={[
          {
            id: "1",
            experiment_id: "e",
            model_name: "holt_winters",
            model_family: "statistical",
            status: "failed",
            rank: null,
            selection_score: null,
            selected: false,
            validation_metrics: null,
            backtest_metrics: null,
            training_duration_ms: 3,
            backtest_duration_ms: 0,
            failure_message: "Insufficient history",
          },
        ]}
      />,
    );
    expect(screen.getByText("holt_winters")).toBeInTheDocument();
    expect(screen.getByText(/Insufficient history/)).toBeInTheDocument();
    expect(screen.getAllByText("—").length).toBeGreaterThan(0);
  });

  it("disables unavailable advanced dependencies", () => {
    render(
      <AdvancedModelSelector
        models={[
          {
            ...models[0],
            id: "lightgbm_regressor",
            name: "LightGBM",
            family: "gradient_boosting",
            dependency_available: false,
          },
        ]}
        selected={[]}
        setSelected={vi.fn()}
      />,
    );
    expect(screen.getByRole("checkbox", { name: /LightGBM/i })).toBeDisabled();
    expect(screen.getByText("Unavailable")).toBeInTheDocument();
  });

  it("renders tuning failures and the non-causal explanation", () => {
    render(
      <>
        <TuningSummaryPanel
          summary={{
            model_run_id: "r",
            method: "optuna",
            completed_trials: 1,
            failed_trials: 1,
            best_score: 0.2,
            best_parameters: { depth: 3 },
            duration_ms: 12,
            items: [
              {
                trial_number: 0,
                status: "failed",
                parameters: {},
                backtest_metric: null,
                validation_metric: null,
                duration_ms: 4,
                failure_message: "safe failure",
              },
            ],
          }}
        />
        <ExplanationDisclaimer />
      </>,
    );
    expect(screen.getByText(/1 failed/i)).toBeInTheDocument();
    expect(screen.getByText(/does not prove causation/i)).toBeInTheDocument();
  });
});
