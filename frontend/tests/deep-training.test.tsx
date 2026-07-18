import { render, screen, waitFor } from "@testing-library/react";
import userEvent from "@testing-library/user-event";
import { afterEach, describe, expect, it, vi } from "vitest";
import { DeepTrainingWorkspace } from "@/components/forecasting/deep-training";

afterEach(() => vi.unstubAllGlobals());

const experiment = {
  experiment_id: "e",
  model_run_id: "r",
  prepared_dataset_id: "p",
  model_name: "nhits",
  status: "completed",
  current_epoch: null,
  max_steps: 1,
  selected_accelerator: "cpu",
  training_duration_ms: 1200,
  checkpoint_available: true,
  checkpoint_checksum: "a".repeat(64),
  metrics: { mae: 1.25, rmse: 1.5, mape: 0.1, smape: 0.1, wape: 0.1, r2: 0.5 },
  failure_message: null,
  created_at: "2026-01-01T00:00:00Z",
  completed_at: "2026-01-01T00:00:01Z",
};

describe("N-HiTS training workspace", () => {
  it("renders executed metrics and checkpoint state", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        json: async () => ({ total: 1, items: [experiment] }),
      }),
    );
    render(<DeepTrainingWorkspace />);
    expect(await screen.findByText("NHITS")).toBeInTheDocument();
    expect(screen.getByText("1.2500")).toBeInTheDocument();
    expect(screen.getByText("Saved")).toBeInTheDocument();
  });

  it("submits a governed training request", async () => {
    const fetch = vi
      .fn()
      .mockResolvedValueOnce({
        ok: true,
        json: async () => ({ total: 0, items: [] }),
      })
      .mockResolvedValueOnce({ ok: true, json: async () => experiment });
    vi.stubGlobal("fetch", fetch);
    render(<DeepTrainingWorkspace />);
    await userEvent.type(
      screen.getByLabelText(/Prepared dataset UUID/i),
      "00000000-0000-4000-8000-000000000001",
    );
    await userEvent.click(
      screen.getByRole("button", { name: /Start governed training/i }),
    );
    await waitFor(() => expect(fetch).toHaveBeenCalledTimes(2));
    expect(String(fetch.mock.calls[1][0])).toContain(
      "/api/v1/deep/train/nhits",
    );
  });
});
