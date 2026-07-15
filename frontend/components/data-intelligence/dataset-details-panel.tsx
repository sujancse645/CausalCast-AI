"use client";
import type { DatasetDetail, DatasetPreview } from "@/types/dataset";
import { DatasetPreviewTable } from "./dataset-preview-table";
export function DatasetDetailsPanel({
  detail,
  preview,
  onClose,
  onArchive,
}: {
  detail: DatasetDetail;
  preview: DatasetPreview | null;
  onClose: () => void;
  onArchive: () => void;
}) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="details-title"
      className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4"
    >
      <div className="panel max-h-[90vh] w-full max-w-5xl overflow-y-auto p-6">
        <div className="flex justify-between">
          <div>
            <h2 id="details-title" className="text-xl font-semibold">
              {detail.original_filename}
            </h2>
            <p className="muted text-xs">Dataset {detail.id}</p>
          </div>
          <button aria-label="Close dataset details" onClick={onClose}>
            Close
          </button>
        </div>
        <dl className="mt-6 grid gap-4 text-sm sm:grid-cols-3">
          {[
            ["Rows", detail.row_count],
            ["Columns", detail.column_count],
            ["Encoding", detail.encoding ?? "—"],
            [
              "Delimiter",
              detail.delimiter === "\t" ? "Tab" : (detail.delimiter ?? "—"),
            ],
            ["Checksum", detail.checksum_sha256],
            ["Ingestion version", detail.ingestion_version],
          ].map(([k, v]) => (
            <div key={k} className="rounded-lg bg-slate-950/40 p-3">
              <dt className="text-xs text-slate-500">{k}</dt>
              <dd className="mt-1 break-all">{v}</dd>
            </div>
          ))}
        </dl>
        {preview && (
          <div className="mt-6">
            <DatasetPreviewTable preview={preview} />
          </div>
        )}
        <button
          onClick={onArchive}
          className="mt-6 rounded-lg border border-rose-500/40 px-4 py-2 text-rose-300"
        >
          Archive dataset
        </button>
      </div>
    </div>
  );
}
