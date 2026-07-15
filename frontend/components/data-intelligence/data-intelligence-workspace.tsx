"use client";
import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  archiveDataset,
  getDataset,
  getDatasetPreview,
  listDatasets,
  uploadDataset,
} from "@/lib/api";
import type {
  DatasetDetail,
  DatasetListResponse,
  DatasetPreview,
  DatasetUploadResponse,
} from "@/types/dataset";
import { DatasetDetailsPanel } from "./dataset-details-panel";
import { DatasetDropzone } from "./dataset-dropzone";
import { DatasetLibrary } from "./dataset-library";
import { DatasetPreviewTable } from "./dataset-preview-table";

export function DataIntelligenceWorkspace() {
  const [file, setFile] = useState<File | null>(null);
  const [fileError, setFileError] = useState<string | null>(null);
  const [uploading, setUploading] = useState(false);
  const [message, setMessage] = useState<string | null>(null);
  const [result, setResult] = useState<DatasetUploadResponse | null>(null);
  const [data, setData] = useState<DatasetListResponse | null>(null);
  const [loading, setLoading] = useState(true);
  const [libraryError, setLibraryError] = useState<string | null>(null);
  const [page, setPage] = useState(1);
  const [search, setSearch] = useState("");
  const [detail, setDetail] = useState<DatasetDetail | null>(null);
  const [preview, setPreview] = useState<DatasetPreview | null>(null);
  const load = useCallback(async () => {
    setLoading(true);
    try {
      setData(await listDatasets({ page, search }));
      setLibraryError(null);
    } catch {
      setLibraryError(
        "Dataset library is unavailable. Retry by changing the page or search.",
      );
    } finally {
      setLoading(false);
    }
  }, [page, search]);
  useEffect(() => {
    let active = true;
    void listDatasets({ page, search })
      .then((response) => {
        if (active) {
          setData(response);
          setLibraryError(null);
        }
      })
      .catch(() => {
        if (active)
          setLibraryError(
            "Dataset library is unavailable. Retry by changing the page or search.",
          );
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, [page, search]);
  const submit = async () => {
    if (!file || fileError) return;
    setUploading(true);
    setMessage(null);
    try {
      const uploaded = await uploadDataset(file);
      setResult(uploaded);
      setMessage("Dataset uploaded and validated successfully.");
      setFile(null);
      await load();
    } catch (error) {
      if (error instanceof ApiError && error.status === 409)
        setMessage(
          `Duplicate dataset. Existing dataset: ${error.body?.existing_dataset_id ?? "unknown"}`,
        );
      else if (error instanceof ApiError) setMessage(error.message);
      else
        setMessage(
          "Network connection failed. Retry when the backend is available.",
        );
    } finally {
      setUploading(false);
    }
  };
  const view = async (id: string) => {
    try {
      const [details, rows] = await Promise.all([
        getDataset(id),
        getDatasetPreview(id),
      ]);
      setDetail(details);
      setPreview(rows);
    } catch {
      setLibraryError("Dataset details could not be loaded.");
    }
  };
  const archive = async (id: string) => {
    if (
      !window.confirm(
        "Archive this dataset? The raw file will move to isolated archive storage.",
      )
    )
      return;
    try {
      await archiveDataset(id);
      setDetail(null);
      setPreview(null);
      await load();
    } catch {
      setLibraryError("Dataset could not be archived.");
    }
  };
  const uploadedPreview = result
    ? {
        dataset_id: result.id,
        columns: result.column_names,
        rows: result.preview_rows,
        returned_rows: result.preview_rows.length,
        max_rows: 20,
      }
    : null;
  return (
    <div className="space-y-6">
      <div className="grid gap-6 xl:grid-cols-[1.05fr_.95fr]">
        <DatasetDropzone
          file={file}
          error={fileError}
          disabled={uploading}
          onSelect={(selected, error) => {
            setFile(selected);
            setFileError(error);
            setMessage(null);
          }}
          onClear={() => {
            setFile(null);
            setFileError(null);
          }}
          onUpload={() => void submit()}
        />
        <section className="panel p-6" aria-live="polite">
          <h3 className="font-semibold">Ingestion status</h3>
          {!message && !result ? (
            <p className="muted mt-4 text-sm">
              Select a CSV to begin secure technical validation.
            </p>
          ) : (
            <>
              <p
                className={`mt-4 text-sm ${message?.includes("successfully") ? "text-emerald-300" : "text-amber-200"}`}
              >
                {message}
              </p>
              {message && !message.includes("successfully") && file && (
                <button
                  onClick={() => void submit()}
                  className="mt-3 text-sm text-blue-400"
                >
                  Retry upload
                </button>
              )}
            </>
          )}
          {result && (
            <dl className="mt-5 grid grid-cols-2 gap-3 text-sm">
              {[
                ["Dataset ID", result.id],
                ["Filename", result.original_filename],
                ["Rows", result.row_count],
                ["Columns", result.column_count],
                ["Encoding", result.encoding ?? "—"],
                [
                  "Delimiter",
                  result.delimiter === "\t" ? "Tab" : (result.delimiter ?? "—"),
                ],
                ["Status", result.status],
                ["Checksum", `${result.checksum_sha256.slice(0, 12)}…`],
              ].map(([k, v]) => (
                <div key={k}>
                  <dt className="text-xs text-slate-500">{k}</dt>
                  <dd className="mt-1 break-all">{v}</dd>
                </div>
              ))}
            </dl>
          )}
        </section>
      </div>
      {uploadedPreview && (
        <section className="panel p-6">
          <DatasetPreviewTable preview={uploadedPreview} />
        </section>
      )}
      <div className="rounded-xl border border-violet-500/20 bg-violet-500/5 p-4 text-sm text-violet-100">
        Phase 2A displays technical ingestion metadata only. Semantic mapping
        and quality analysis will be added in later phases.
      </div>
      <DatasetLibrary
        data={data}
        loading={loading}
        error={libraryError}
        page={page}
        search={search}
        onSearch={(value) => {
          setSearch(value);
          setPage(1);
        }}
        onPage={setPage}
        onView={(id) => void view(id)}
        onArchive={(id) => void archive(id)}
      />
      {detail && (
        <DatasetDetailsPanel
          detail={detail}
          preview={preview}
          onClose={() => setDetail(null)}
          onArchive={() => void archive(detail.id)}
        />
      )}
    </div>
  );
}
