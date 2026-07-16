import type { DatasetSchemaSummary } from "@/types/schema-mapping";
export function SchemaReadinessSummary({
  summary,
}: {
  summary: DatasetSchemaSummary;
}) {
  const values = [
    ["Mapped", summary.mapped_columns],
    ["Unresolved", summary.unresolved_columns],
    ["Ambiguous", summary.ambiguous_columns],
    ["Average confidence", `${Math.round(summary.average_confidence * 100)}%`],
    ["Primary date", summary.primary_date_candidate ?? "Not identified"],
    ["Primary target", summary.primary_target_candidate ?? "Not identified"],
  ];
  return (
    <section className="panel p-5" aria-labelledby="readiness-title">
      <div className="flex justify-between">
        <h2 id="readiness-title" className="font-semibold">
          Mapping readiness
        </h2>
        <span className="rounded-full border border-slate-700 px-3 py-1 text-xs capitalize">
          {summary.readiness_status.replaceAll("_", " ")}
        </span>
      </div>
      <div className="mt-4 grid gap-4 sm:grid-cols-3">
        {values.map(([label, value]) => (
          <div key={label}>
            <p className="text-lg font-semibold">{value}</p>
            <p className="muted text-xs">{label}</p>
          </div>
        ))}
      </div>
      {summary.blocking_issues.length > 0 && (
        <div
          role="alert"
          className="mt-4 rounded-lg border border-rose-500/30 p-3 text-sm text-rose-200"
        >
          <strong>Blocking issues</strong>
          <ul className="mt-2 list-disc pl-5">
            {summary.blocking_issues.map((x) => (
              <li key={x.code}>{x.message}</li>
            ))}
          </ul>
        </div>
      )}
    </section>
  );
}
