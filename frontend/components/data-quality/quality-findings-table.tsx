import type { QualityFinding } from "@/types/quality";
export function QualityFindingsTable({
  items,
  onView,
}: {
  items: QualityFinding[];
  onView: (item: QualityFinding) => void;
}) {
  return (
    <section className="panel overflow-hidden">
      <div className="p-5">
        <h2 className="font-semibold">Quality findings</h2>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[900px] text-left text-sm">
          <caption className="sr-only">Deterministic quality findings</caption>
          <thead>
            <tr>
              {[
                "Severity",
                "Category",
                "Finding",
                "Column",
                "Affected",
                "Blocking",
                "Recommendation",
                "Action",
              ].map((x) => (
                <th className="px-4 py-3 text-xs text-slate-500" key={x}>
                  {x}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {items.map((item) => (
              <tr className="border-t border-slate-800" key={item.id}>
                <td className="px-4 py-3 capitalize">{item.severity}</td>
                <td className="px-4 capitalize">
                  {item.category.replaceAll("_", " ")}
                </td>
                <td className="px-4">{item.title}</td>
                <td className="px-4">{item.affected_column ?? "—"}</td>
                <td className="px-4">
                  {item.affected_row_count ?? "—"}
                  {item.affected_ratio !== null
                    ? ` (${(item.affected_ratio * 100).toFixed(1)}%)`
                    : ""}
                </td>
                <td className="px-4">{item.blocking ? "Yes" : "No"}</td>
                <td className="max-w-72 px-4 text-slate-400">
                  {item.recommendation}
                </td>
                <td className="px-4">
                  <button
                    className="text-blue-400"
                    onClick={() => onView(item)}
                  >
                    View evidence
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
        {!items.length && (
          <p className="p-6 text-sm text-slate-400">
            No findings match these filters.
          </p>
        )}
      </div>
    </section>
  );
}
