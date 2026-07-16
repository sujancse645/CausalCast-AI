import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { vi } from "vitest";

import { SchemaMappingWorkspace } from "@/components/schema-mapping/schema-mapping-workspace";

const dataset = {
  id: "11111111-1111-4111-8111-111111111111",
  original_filename: "marketing.csv",
  row_count: 10,
  column_count: 2,
};
const summary = {
  total_columns: 2,
  mapped_columns: 2,
  confirmed_columns: 0,
  unresolved_columns: 0,
  ambiguous_columns: 0,
  average_confidence: 0.91,
  primary_date_candidate: "date",
  primary_target_candidate: "revenue",
  revenue_candidate: "revenue",
  spend_candidate: null,
  available_marketing_dimensions: [],
  available_performance_metrics: ["revenue"],
  blocking_issues: [],
  warnings: [],
  readiness_status: "mapping_ready",
};
const column = {
  id: "22222222-2222-4222-8222-222222222222",
  column_index: 1,
  column_name: "revenue",
  normalized_column_name: "revenue",
  physical_type: "float",
  semantic_role: "revenue",
  confidence_score: 0.96,
  confirmation_status: "proposed",
  decision_source: "deterministic_inference",
  nullable: false,
  null_count: 0,
  sample_count: 10,
  unique_count: 10,
  parse_success_rate: 1,
  numeric_min: 10,
  numeric_max: 100,
  numeric_mean: 55,
  date_min: null,
  date_max: null,
  string_min_length: null,
  string_max_length: null,
  sample_values: ["10", "20"],
  evidence: [
    {
      evidence_type: "name_exact",
      description: "Exact synonym",
      score_contribution: 0.65,
      observed_value: "revenue",
      expected_pattern: "revenue",
      severity: "info",
    },
  ],
  alternatives: [
    {
      role: "target",
      confidence_score: 0.4,
      summary_evidence: ["Numeric metric"],
    },
  ],
  warnings: [],
};
const schema = {
  id: "33333333-3333-4333-8333-333333333333",
  dataset_id: dataset.id,
  dataset_filename: dataset.original_filename,
  dataset_row_count: 10,
  dataset_column_count: 2,
  schema_version: 1,
  inference_version: "1.0",
  status: "needs_review",
  created_at: "2026-07-15T00:00:00Z",
  updated_at: "2026-07-15T00:00:00Z",
  confirmed_at: null,
  source_checksum: "a".repeat(64),
  sample_row_count: 10,
  summary,
  columns: [column],
};

function response(value: object, status = 200) {
  return Promise.resolve(
    new Response(JSON.stringify(value), {
      status,
      headers: { "Content-Type": "application/json" },
    }),
  );
}

function mockApi(withSchema = true) {
  const fetch = vi.fn((input: RequestInfo | URL, init?: RequestInit) => {
    const url = String(input);
    if (url.endsWith(`/datasets/${dataset.id}`)) return response(dataset);
    if (url.endsWith("/schema/roles"))
      return response({
        items: [
          { role: "revenue", label: "Revenue", description: "Sales value" },
          { role: "ignored", label: "Ignored", description: "Excluded" },
        ],
      });
    if (url.endsWith("/schema/history"))
      return response({
        items: withSchema
          ? [
              {
                id: schema.id,
                schema_version: 1,
                inference_version: "1.0",
                status: "needs_review",
                created_at: schema.created_at,
                confirmed_at: null,
                mapped_columns: 2,
                confirmed_columns: 0,
                unresolved_columns: 0,
              },
            ]
          : [],
      });
    if (url.endsWith("/schema/infer")) return response(schema, 201);
    if (url.includes("/schema/columns/") && init?.method === "PATCH")
      return response({
        column: {
          ...column,
          semantic_role: "ignored",
          confirmation_status: "manually_overridden",
        },
        summary,
      });
    if (url.endsWith("/schema/confirm"))
      return response({
        dataset_id: dataset.id,
        schema_profile_id: schema.id,
        schema_version: 1,
        status: "confirmed",
        confirmed_at: schema.created_at,
        summary,
      });
    if (url.endsWith("/schema"))
      return withSchema
        ? response(schema)
        : response({ detail: "Schema not found" }, 404);
    throw new Error(`Unexpected request ${url}`);
  });
  vi.stubGlobal("fetch", fetch);
  return fetch;
}

describe("Schema mapping workspace", () => {
  it("shows dataset information and the no-schema inference action", async () => {
    mockApi(false);
    render(<SchemaMappingWorkspace datasetId={dataset.id} />);
    expect(await screen.findByText("marketing.csv")).toBeInTheDocument();
    expect(screen.getByText("No schema proposal yet")).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Run inference" }),
    ).toBeInTheDocument();
  });

  it("runs inference and renders proposed role, confidence, and history", async () => {
    mockApi(false);
    render(<SchemaMappingWorkspace datasetId={dataset.id} />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Run inference" }),
    );
    expect(await screen.findByText("96% — Very High")).toBeInTheDocument();
    expect(screen.getByLabelText("Semantic role for revenue")).toHaveValue(
      "revenue",
    );
    expect(screen.getByText(/schema v1/)).toBeInTheDocument();
  });

  it("opens explainable evidence and alternatives", async () => {
    mockApi();
    render(<SchemaMappingWorkspace datasetId={dataset.id} />);
    fireEvent.click(
      await screen.findByRole("button", { name: "View evidence" }),
    );
    const dialog = screen.getByRole("dialog", { name: "Evidence: revenue" });
    expect(dialog).toBeInTheDocument();
    expect(within(dialog).getByText("Exact synonym")).toBeInTheDocument();
    expect(within(dialog).getByText(/target/i)).toBeInTheDocument();
  });

  it("saves a manual ignored override", async () => {
    const fetch = mockApi();
    render(<SchemaMappingWorkspace datasetId={dataset.id} />);
    fireEvent.change(
      await screen.findByLabelText("Semantic role for revenue"),
      { target: { value: "ignored" } },
    );
    await waitFor(() =>
      expect(fetch).toHaveBeenCalledWith(
        expect.stringContaining("/schema/columns/"),
        expect.objectContaining({ method: "PATCH" }),
      ),
    );
  });

  it("uses an accessible confirmation dialog", async () => {
    mockApi();
    render(<SchemaMappingWorkspace datasetId={dataset.id} />);
    fireEvent.click(
      await screen.findByRole("button", { name: "Confirm mapping" }),
    );
    expect(
      screen.getByRole("dialog", { name: "Confirm schema mapping?" }),
    ).toBeInTheDocument();
  });

  it("handles backend failures", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.reject(new Error("offline"))),
    );
    render(<SchemaMappingWorkspace datasetId={dataset.id} />);
    expect(await screen.findByRole("alert")).toHaveTextContent(
      "Schema workspace is unavailable",
    );
  });
});
