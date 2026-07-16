"use client";
import Link from "next/link";
import type { DatasetListResponse } from "@/types/dataset";
import { DatasetStatusBadge } from "./dataset-status-badge";
export function DatasetLibrary({
  data,
  loading,
  error,
  page,
  search,
  onSearch,
  onPage,
  onView,
  onArchive,
}: {
  data: DatasetListResponse | null;
  loading: boolean;
  error: string | null;
  page: number;
  search: string;
  onSearch: (v: string) => void;
  onPage: (v: number) => void;
  onView: (id: string) => void;
  onArchive: (id: string) => void;
}) {
  return (
    <section
      className="panel overflow-hidden"
      aria-labelledby="library-heading"
    >
      <div className="flex flex-col gap-3 border-b border-slate-800 p-5 sm:flex-row sm:items-center sm:justify-between">
        <div>
          <h3 id="library-heading" className="font-semibold">
            Dataset library
          </h3>
          <p className="muted text-xs">
            Persisted ingestion records and archive controls
          </p>
        </div>
        <input
          value={search}
          onChange={(e) => onSearch(e.target.value)}
          aria-label="Search datasets by filename"
          placeholder="Search filenames"
          className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
        />
      </div>
      {loading ? (
        <p role="status" className="p-6 text-sm text-slate-400">
          Loading datasets…
        </p>
      ) : error ? (
        <p role="alert" className="p-6 text-sm text-rose-300">
          {error}
        </p>
      ) : !data?.items.length ? (
        <p className="p-8 text-center text-sm text-slate-400">
          No datasets uploaded yet.
        </p>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full min-w-[760px] text-left text-sm">
            <caption className="sr-only">Uploaded datasets</caption>
            <thead>
              <tr>
                {[
                  "Filename",
                  "Rows",
                  "Columns",
                  "Size",
                  "Status",
                  "Schema",
                  "Quality",
                  "Uploaded",
                  "Actions",
                ].map((x) => (
                  <th className="px-4 py-3 text-xs text-slate-500" key={x}>
                    {x}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {data.items.map((item) => (
                <tr className="border-t border-slate-800" key={item.id}>
                  <td className="px-4 py-3">{item.original_filename}</td>
                  <td className="px-4">{item.row_count}</td>
                  <td className="px-4">{item.column_count}</td>
                  <td className="px-4">
                    {(item.file_size_bytes / 1024).toFixed(1)} KB
                  </td>
                  <td className="px-4">
                    <DatasetStatusBadge status={item.status} />
                  </td>
                  <td className="px-4 text-slate-300 capitalize">
                    {(item.schema_status ?? "not_analyzed").replaceAll(
                      "_",
                      " ",
                    )}
                  </td>
                  <td className="px-4 text-slate-300 capitalize">
                    {(item.quality_status ?? "not_analyzed").replaceAll(
                      "_",
                      " ",
                    )}
                    {item.quality_score != null
                      ? ` · ${Math.round(item.quality_score)}/100`
                      : ""}
                    {(item.quality_blockers ?? 0) > 0
                      ? ` · ${item.quality_blockers} blocker(s)`
                      : ""}
                  </td>
                  <td className="px-4 text-slate-400">
                    {new Date(item.created_at).toLocaleString()}
                  </td>
                  <td className="px-4">
                    <button
                      onClick={() => onView(item.id)}
                      className="mr-3 text-blue-400"
                    >
                      View details
                    </button>
                    {item.status === "ready" && (
                      <Link
                        href={`/data-intelligence/${item.id}/schema`}
                        className="mr-3 text-cyan-300"
                      >
                        Review schema
                      </Link>
                    )}
                    {item.status === "ready" &&
                      item.schema_status !== "not_analyzed" && (
                        <Link
                          href={`/data-intelligence/${item.id}/quality`}
                          className="mr-3 text-violet-300"
                        >
                          {item.quality_status === "not_analyzed"
                            ? "Analyze quality"
                            : "View quality report"}
                        </Link>
                      )}
                    {item.status !== "archived" && (
                      <Link
                        href={`/data-intelligence/${item.id}/prepare`}
                        className="mr-3 text-emerald-300"
                      >
                        Prepare dataset
                      </Link>
                    )}
                    {item.status !== "archived" && (
                      <button
                        onClick={() => onArchive(item.id)}
                        className="text-rose-300"
                      >
                        Archive
                      </button>
                    )}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
      <div className="flex items-center justify-between border-t border-slate-800 p-4 text-sm">
        <button
          disabled={page <= 1}
          onClick={() => onPage(page - 1)}
          className="disabled:opacity-40"
        >
          Previous
        </button>
        <span>
          Page {page} of {data?.pagination.total_pages || 1}
        </span>
        <button
          disabled={!data || page >= data.pagination.total_pages}
          onClick={() => onPage(page + 1)}
          className="disabled:opacity-40"
        >
          Next
        </button>
      </div>
    </section>
  );
}
