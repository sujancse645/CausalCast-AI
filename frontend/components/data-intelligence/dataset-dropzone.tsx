"use client";
import { FileUp, X } from "lucide-react";
import { useRef } from "react";

const MAX_BYTES = 25 * 1024 * 1024;
export function validateFile(file: File): string | null {
  if (
    !file.name.toLowerCase().endsWith(".csv") ||
    file.name.split(".").length !== 2
  )
    return "Only single-extension CSV files are supported.";
  if (file.size === 0) return "The selected file is empty.";
  if (file.size > MAX_BYTES)
    return "The selected file exceeds the 25 MB limit.";
  return null;
}
export function DatasetDropzone({
  file,
  error,
  disabled,
  onSelect,
  onClear,
  onUpload,
}: {
  file: File | null;
  error: string | null;
  disabled: boolean;
  onSelect: (file: File, error: string | null) => void;
  onClear: () => void;
  onUpload: () => void;
}) {
  const input = useRef<HTMLInputElement>(null);
  const select = (candidate: File | undefined) => {
    if (candidate) onSelect(candidate, validateFile(candidate));
  };
  return (
    <section className="panel p-6" aria-labelledby="upload-heading">
      <h3 id="upload-heading" className="font-semibold">
        Upload governed dataset
      </h3>
      <p className="muted mt-1 text-sm">
        CSV only · maximum 25 MB · raw files remain immutable
      </p>
      <div
        tabIndex={0}
        role="button"
        aria-label="Select CSV dataset"
        onKeyDown={(e) => {
          if (e.key === "Enter" || e.key === " ") input.current?.click();
        }}
        onDragOver={(e) => e.preventDefault()}
        onDrop={(e) => {
          e.preventDefault();
          select(e.dataTransfer.files[0]);
        }}
        onClick={() => input.current?.click()}
        className="mt-5 grid min-h-44 cursor-pointer place-items-center rounded-xl border border-dashed border-slate-600 bg-slate-950/30 p-6 text-center hover:border-blue-400"
      >
        <div>
          <FileUp className="mx-auto text-blue-400" />
          <p className="mt-3 font-medium">Drop a CSV here or browse</p>
          <p className="muted mt-1 text-xs">
            Technical validation occurs again on the backend.
          </p>
        </div>
        <input
          ref={input}
          className="sr-only"
          type="file"
          accept=".csv,text/csv"
          aria-label="CSV file"
          onChange={(e) => select(e.target.files?.[0])}
        />
      </div>
      {file && (
        <div className="mt-4 flex items-center justify-between rounded-lg border border-slate-700 p-3 text-sm">
          <div>
            <p>{file.name}</p>
            <p className="muted text-xs">
              {(file.size / 1024).toFixed(1)} KB · {file.type || "unknown type"}
            </p>
          </div>
          <button
            aria-label="Clear selected file"
            onClick={onClear}
            className="p-2"
          >
            <X size={17} />
          </button>
        </div>
      )}
      <div aria-live="polite">
        {error && (
          <p role="alert" className="mt-3 text-sm text-rose-300">
            {error}
          </p>
        )}
      </div>
      <button
        disabled={!file || !!error || disabled}
        onClick={onUpload}
        className="mt-4 rounded-lg bg-blue-600 px-5 py-2 text-sm font-medium disabled:cursor-not-allowed disabled:opacity-40"
      >
        {disabled ? "Uploading…" : "Upload dataset"}
      </button>
    </section>
  );
}
