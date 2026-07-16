import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import { PreparationWorkspace } from "@/components/preparation/preparation-workspace";

const api = vi.hoisted(() => ({
  getDataset: vi.fn(),
  getDatasetSchema: vi.fn(),
  getDatasetQuality: vi.fn(),
  listPreparations: vi.fn(),
  createPreparation: vi.fn(),
}));
vi.mock("@/lib/api", async () => ({
  ...(await vi.importActual<object>("@/lib/api")),
  ...api,
}));
const datasetId = "11111111-1111-4111-8111-111111111111";
const dataset = {
  id: datasetId,
  original_filename: "marketing.csv",
  row_count: 120,
  column_count: 3,
};
const schema = {
  status: "confirmed",
  summary: {
    primary_target_candidate: "revenue",
    primary_date_candidate: "date",
  },
  columns: [
    {
      id: "1",
      column_name: "date",
      physical_type: "date",
      semantic_role: "date",
    },
    {
      id: "2",
      column_name: "revenue",
      physical_type: "float",
      semantic_role: "revenue",
    },
    {
      id: "3",
      column_name: "channel",
      physical_type: "categorical",
      semantic_role: "channel",
    },
  ],
};
const quality = { readiness_status: "quality_ready", blocker_count: 0 };

beforeEach(() => {
  api.getDataset.mockResolvedValue(dataset);
  api.getDatasetSchema.mockResolvedValue(schema);
  api.getDatasetQuality.mockResolvedValue(quality);
  api.listPreparations.mockResolvedValue({ items: [] });
  api.createPreparation.mockReset();
});

test("preparation workspace renders readiness and configuration controls", async () => {
  render(<PreparationWorkspace datasetId={datasetId} />);
  expect(await screen.findByText(/Prepare marketing.csv/)).toBeInTheDocument();
  expect(screen.getByLabelText("Target")).toHaveValue("revenue");
  expect(screen.getByLabelText("Date")).toHaveValue("date");
  expect(screen.getByLabelText("Frequency")).toHaveValue("daily");
  expect(
    screen.getByLabelText("Chronological split timeline"),
  ).toBeInTheDocument();
  expect(
    screen.getByText(
      /Target lags and rolling windows use prior observations only/,
    ),
  ).toBeInTheDocument();
});

test("successful preparation submission renders governed result", async () => {
  api.createPreparation.mockResolvedValue({
    id: "p1",
    row_count: 120,
    feature_count: 18,
    generated_rows: 0,
    readiness_status: "model_ready",
    prepared_checksum: "abc123",
  });
  render(<PreparationWorkspace datasetId={datasetId} />);
  fireEvent.click(
    await screen.findByRole("button", { name: "Start preparation" }),
  );
  expect(await screen.findByText("6. Preparation result")).toBeInTheDocument();
  expect(screen.getByText("18")).toBeInTheDocument();
  await waitFor(() => expect(api.createPreparation).toHaveBeenCalled());
});

test("blocked quality prevents preparation", async () => {
  api.getDatasetQuality.mockResolvedValue({
    ...quality,
    readiness_status: "blocked",
    blocker_count: 2,
  });
  render(<PreparationWorkspace datasetId={datasetId} />);
  expect(await screen.findByText(/Preparation is blocked/)).toBeInTheDocument();
  expect(
    screen.getByRole("button", { name: "Start preparation" }),
  ).toBeDisabled();
});
