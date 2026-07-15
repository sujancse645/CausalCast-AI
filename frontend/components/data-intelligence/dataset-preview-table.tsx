import type { DatasetPreview } from "@/types/dataset";
export function DatasetPreviewTable({ preview }: { preview: DatasetPreview }) {
  return (
    <section aria-labelledby="preview-heading">
      <h3 id="preview-heading" className="font-semibold">
        Bounded preview
      </h3>
      <p className="muted mt-1 text-xs">
        Showing {preview.returned_rows} rows. Values are escaped and long cells
        are truncated.
      </p>
      {preview.rows.length === 0 ? (
        <p className="mt-4 rounded-lg border border-slate-700 p-4 text-sm text-slate-400">
          This header-only dataset has no preview rows.
        </p>
      ) : (
        <div className="mt-4 overflow-x-auto">
          <table className="min-w-full text-left text-xs whitespace-nowrap">
            <caption className="sr-only">Uploaded dataset preview</caption>
            <thead>
              <tr>
                {preview.columns.map((c) => (
                  <th
                    key={c}
                    className="border-b border-slate-700 px-3 py-2 text-slate-400"
                  >
                    {c}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {preview.rows.map((row, i) => (
                <tr key={i}>
                  {preview.columns.map((c) => (
                    <td
                      key={c}
                      title={row[c] ?? "Null"}
                      className="max-w-64 truncate border-b border-slate-800 px-3 py-2"
                    >
                      {row[c] ?? <span className="text-slate-600">null</span>}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}
    </section>
  );
}
