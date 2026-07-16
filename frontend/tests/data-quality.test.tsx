import { fireEvent, render, screen, within } from "@testing-library/react";
import { vi } from "vitest";
import { DataQualityWorkspace } from "@/components/data-quality/data-quality-workspace";

const id = "11111111-1111-4111-8111-111111111111";
const dataset = {
  id,
  original_filename: "quality.csv",
  row_count: 100,
  column_count: 4,
};
const finding = {
  id: "f1",
  rule_code: "DQ_LEAKAGE_001",
  category: "leakage",
  severity: "blocker",
  title: "Direct target copy detected",
  description: "A copy was observed.",
  affected_column: "actual_revenue",
  related_columns: ["revenue"],
  affected_row_count: 10,
  affected_ratio: 0.1,
  sample_row_indices: [2, 3],
  evidence: { observed_count: 10, scan_scope: 100 },
  threshold: {},
  recommendation: "Exclude the copy.",
  blocking: true,
  confidence: 1,
};
const report = {
  id: "r1",
  dataset_id: id,
  dataset_filename: "quality.csv",
  report_version: 1,
  schema_version: 1,
  quality_engine_version: "1.0",
  status: "completed",
  readiness_status: "blocked",
  overall_score: 49,
  dimension_scores: {
    completeness: 100,
    uniqueness: 100,
    validity: 100,
    consistency: 100,
    temporal: 93,
    integrity: 100,
    leakage_safety: 50,
  },
  total_findings: 1,
  blocker_count: 1,
  error_count: 0,
  warning_count: 0,
  info_count: 0,
  scanned_rows: 50,
  total_rows: 100,
  scan_coverage_ratio: 0.5,
  analyzed_columns: 4,
  created_at: "2026-07-16T00:00:00Z",
  completed_at: "2026-07-16T00:00:01Z",
  duration_ms: 100,
  summary: {
    temporal: {
      available: true,
      column: "date",
      frequency: "daily",
      date_min: "2026-01-01",
      date_max: "2026-02-01",
      gap_count: 1,
      duplicate_dates: 0,
      out_of_order: 0,
      future_dates: 0,
    },
    scan_mode: "bounded",
  },
  recommendations: [
    { message: "Exclude the copy.", rule_code: "DQ_LEAKAGE_001" },
  ],
  findings: [finding],
};
function response(value: object, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(value), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}
function mockApi(hasReport = true) {
  const fetch = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith(`/datasets/${id}`)) return response(dataset);
    if (url.endsWith("/quality/history"))
      return response({
        items: hasReport
          ? [
              {
                id: "r1",
                report_version: 1,
                schema_version: 1,
                status: "completed",
                readiness_status: "blocked",
                overall_score: 49,
                blocker_count: 1,
                created_at: report.created_at,
              },
            ]
          : [],
      });
    if (url.endsWith("/quality/analyze") && init?.method === "POST")
      return response(report, 201);
    if (url.endsWith("/quality"))
      return hasReport
        ? response(report)
        : response({ detail: "not found" }, 404);
    throw new Error(url);
  });
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("Data quality workspace", () => {
  it("renders no-report state and runs analysis", async () => {
    mockApi(false);
    render(<DataQualityWorkspace datasetId={id} />);
    expect(await screen.findByText("quality.csv")).toBeInTheDocument();
    expect(screen.getByText("No quality report yet")).toBeInTheDocument();
    fireEvent.click(screen.getByRole("button", { name: "Run analysis" }));
    expect(await screen.findByText("49/100")).toBeInTheDocument();
  });
  it("renders score, readiness, dimensions, coverage, temporal and leakage", async () => {
    mockApi();
    render(<DataQualityWorkspace datasetId={id} />);
    expect(await screen.findByText("49/100")).toBeInTheDocument();
    expect(screen.getAllByText(/blocked/i).length).toBeGreaterThan(0);
    expect(screen.getByText(/completeness/i)).toBeInTheDocument();
    expect(screen.getByText(/Partial bounded scan/)).toBeInTheDocument();
    expect(screen.getByText(/Frequency:/)).toBeInTheDocument();
    expect(screen.getByText(/Human review is required/)).toBeInTheDocument();
  });
  it("filters blocking findings", async () => {
    mockApi();
    render(<DataQualityWorkspace datasetId={id} />);
    await screen.findByText("Direct target copy detected");
    fireEvent.change(screen.getByLabelText("Filter severity"), {
      target: { value: "warning" },
    });
    expect(
      screen.getByText("No findings match these filters."),
    ).toBeInTheDocument();
    fireEvent.change(screen.getByLabelText("Filter severity"), {
      target: { value: "" },
    });
    fireEvent.click(screen.getByLabelText("Blocking only"));
    expect(screen.getByText("Direct target copy detected")).toBeInTheDocument();
  });
  it("opens bounded evidence safely", async () => {
    mockApi();
    render(<DataQualityWorkspace datasetId={id} />);
    fireEvent.click(
      await screen.findByRole("button", { name: "View evidence" }),
    );
    const dialog = screen.getByRole("dialog", {
      name: "Direct target copy detected",
    });
    expect(within(dialog).getByText("10")).toBeInTheDocument();
    expect(
      within(dialog).getByText(/Complete raw rows are never included/),
    ).toBeInTheDocument();
  });
  it("renders report history", async () => {
    mockApi();
    render(<DataQualityWorkspace datasetId={id} />);
    expect(await screen.findByText(/Version 1 · schema 1/)).toBeInTheDocument();
  });
  it("handles backend offline", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new Error("offline"))),
    );
    render(<DataQualityWorkspace datasetId={id} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(/unavailable/);
  });
});
