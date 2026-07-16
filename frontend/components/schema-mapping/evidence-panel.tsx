import type { ColumnProfile } from "@/types/schema-mapping";
import { ConfidenceIndicator } from "./confidence-indicator";
export function EvidencePanel({
  column,
  onClose,
}: {
  column: ColumnProfile;
  onClose: () => void;
}) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="evidence-title"
      className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4"
    >
      <section className="panel max-h-[85vh] w-full max-w-2xl overflow-y-auto p-6">
        <div className="flex justify-between">
          <div>
            <h2 id="evidence-title" className="text-xl font-semibold">
              Evidence: {column.column_name}
            </h2>
            <p className="muted text-xs">
              Normalized as {column.normalized_column_name} ·{" "}
              {column.physical_type}
            </p>
          </div>
          <button onClick={onClose}>Close</button>
        </div>
        <div className="mt-5">
          <ConfidenceIndicator value={column.confidence_score} />
        </div>
        <h3 className="mt-6 font-medium">Supporting evidence</h3>
        <ul className="mt-2 space-y-2">
          {column.evidence.map((e, i) => (
            <li
              className="rounded-lg bg-slate-950/40 p-3 text-sm"
              key={`${e.evidence_type}-${i}`}
            >
              {e.description}
              <span className="muted block text-xs">
                Contribution {e.score_contribution >= 0 ? "+" : ""}
                {e.score_contribution.toFixed(2)} · observed{" "}
                {String(e.observed_value)}
              </span>
            </li>
          ))}
        </ul>
        <h3 className="mt-6 font-medium">Alternative candidates</h3>
        <ul className="mt-2 space-y-2">
          {column.alternatives.map((a) => (
            <li key={a.role} className="flex justify-between text-sm">
              <span className="capitalize">{a.role.replaceAll("_", " ")}</span>
              <ConfidenceIndicator value={a.confidence_score} />
            </li>
          ))}
        </ul>
        <p className="mt-6 text-xs text-violet-200">
          Samples are bounded derived metadata. Raw data remains unchanged.
        </p>
      </section>
    </div>
  );
}
