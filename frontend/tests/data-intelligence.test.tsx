import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { vi } from "vitest";
import DataIntelligencePage from "@/app/data-intelligence/page";
import { DatasetLibrary } from "@/components/data-intelligence/dataset-library";
import { validateFile } from "@/components/data-intelligence/dataset-dropzone";
import type { DatasetListResponse } from "@/types/dataset";

const emptyList = {
  items: [],
  pagination: { page: 1, page_size: 10, total_items: 0, total_pages: 0 },
};
const uploaded = {
  id: "11111111-1111-4111-8111-111111111111",
  original_filename: "sample.csv",
  file_extension: "csv",
  mime_type: "text/csv",
  file_size_bytes: 22,
  row_count: 1,
  column_count: 2,
  status: "ready",
  created_at: "2026-07-15T00:00:00Z",
  preview_available: true,
  checksum_sha256: "a".repeat(64),
  column_names: ["name", "value"],
  delimiter: ",",
  encoding: "utf-8",
  updated_at: "2026-07-15T00:00:00Z",
  deleted_at: null,
  ingestion_version: 1,
  source_type: "upload",
  warnings: [],
  preview_rows: [{ name: "A", value: "1" }],
} as const;
function mockApi(
  uploadResponse: Response | Error = new Response(JSON.stringify(uploaded), {
    status: 201,
    headers: { "Content-Type": "application/json" },
  }),
) {
  vi.stubGlobal(
    "fetch",
    vi.fn((input: RequestInfo | URL) => {
      const url = String(input);
      if (url.includes("/datasets/upload"))
        return uploadResponse instanceof Error
          ? Promise.reject(uploadResponse)
          : Promise.resolve(uploadResponse);
      return Promise.resolve(
        new Response(JSON.stringify(emptyList), {
          status: 200,
          headers: { "Content-Type": "application/json" },
        }),
      );
    }),
  );
}
describe("Data Intelligence page", () => {
  it("renders page, upload area, formats, and disabled upload", () => {
    mockApi();
    render(<DataIntelligencePage />);
    expect(
      screen.getByRole("heading", { name: "Data Intelligence" }),
    ).toBeInTheDocument();
    expect(screen.getByText(/CSV only · maximum 25 MB/)).toBeInTheDocument();
    expect(
      screen.getByRole("button", { name: "Upload dataset" }),
    ).toBeDisabled();
  });
  it("selects a valid CSV and shows filename and size", () => {
    mockApi();
    render(<DataIntelligencePage />);
    const file = new File(["a,b\n1,2"], "valid.csv", { type: "text/csv" });
    fireEvent.change(screen.getByLabelText("CSV file"), {
      target: { files: [file] },
    });
    expect(screen.getByText("valid.csv")).toBeInTheDocument();
    expect(screen.getByText(/0.0 KB/)).toBeInTheDocument();
  });
  it("rejects invalid extension", () =>
    expect(validateFile(new File(["x"], "bad.exe"))).toMatch(/Only/));
  it("rejects zero-byte files", () =>
    expect(validateFile(new File([], "empty.csv"))).toMatch(/empty/));
  it("rejects oversized files", () =>
    expect(
      validateFile(
        new File([new Uint8Array(25 * 1024 * 1024 + 1)], "large.csv"),
      ),
    ).toMatch(/25 MB/));
  it("renders successful metadata and preview", async () => {
    mockApi();
    render(<DataIntelligencePage />);
    fireEvent.change(screen.getByLabelText("CSV file"), {
      target: {
        files: [new File(["a,b\n1,2"], "sample.csv", { type: "text/csv" })],
      },
    });
    fireEvent.click(screen.getByRole("button", { name: "Upload dataset" }));
    await waitFor(() =>
      expect(
        screen.getByText(/uploaded and validated successfully/),
      ).toBeInTheDocument(),
    );
    expect(screen.getByText("Bounded preview")).toBeInTheDocument();
    expect(screen.getByText("sample.csv")).toBeInTheDocument();
  });
  it("renders duplicate dataset information", async () => {
    mockApi(
      new Response(
        JSON.stringify({
          detail: "duplicate",
          existing_dataset_id: "existing-1",
        }),
        { status: 409, headers: { "Content-Type": "application/json" } },
      ),
    );
    render(<DataIntelligencePage />);
    fireEvent.change(screen.getByLabelText("CSV file"), {
      target: { files: [new File(["a,b\n1,2"], "dup.csv")] },
    });
    fireEvent.click(screen.getByRole("button", { name: "Upload dataset" }));
    await waitFor(() =>
      expect(screen.getByText(/existing-1/)).toBeInTheDocument(),
    );
  });
  it("shows backend validation errors and retry", async () => {
    mockApi(
      new Response(JSON.stringify({ detail: "Malformed CSV" }), {
        status: 422,
        headers: { "Content-Type": "application/json" },
      }),
    );
    render(<DataIntelligencePage />);
    fireEvent.change(screen.getByLabelText("CSV file"), {
      target: { files: [new File(["bad"], "bad.csv")] },
    });
    fireEvent.click(screen.getByRole("button", { name: "Upload dataset" }));
    await waitFor(() =>
      expect(screen.getByText("Malformed CSV")).toBeInTheDocument(),
    );
    expect(screen.getByText("Retry upload")).toBeInTheDocument();
  });
  it("shows network failures", async () => {
    mockApi(new Error("offline"));
    render(<DataIntelligencePage />);
    fireEvent.change(screen.getByLabelText("CSV file"), {
      target: { files: [new File(["a,b"], "offline.csv")] },
    });
    fireEvent.click(screen.getByRole("button", { name: "Upload dataset" }));
    await waitFor(() =>
      expect(screen.getByText(/Backend is unavailable/)).toBeInTheDocument(),
    );
  });
});
describe("Dataset library", () => {
  const data: DatasetListResponse = {
    items: [{ ...uploaded }],
    pagination: { page: 1, page_size: 10, total_items: 1, total_pages: 2 },
  };
  const props = {
    loading: false,
    error: null,
    page: 1,
    search: "",
    onSearch: vi.fn(),
    onPage: vi.fn(),
    onView: vi.fn(),
    onArchive: vi.fn(),
  };
  it("renders datasets and pagination", () => {
    render(<DatasetLibrary {...props} data={data} />);
    expect(screen.getByText("sample.csv")).toBeInTheDocument();
    fireEvent.click(screen.getByText("Next"));
    expect(props.onPage).toHaveBeenCalledWith(2);
  });
  it("renders empty state", () => {
    render(<DatasetLibrary {...props} data={emptyList} />);
    expect(screen.getByText("No datasets uploaded yet.")).toBeInTheDocument();
  });
  it("provides archive action", () => {
    render(<DatasetLibrary {...props} data={data} />);
    expect(screen.getByRole("button", { name: "Archive" })).toBeInTheDocument();
  });
});
