import type { QualityFinding } from "@/types/quality";
export function QualityFindingDetails({
  finding,
  onClose,
}: {
  finding: QualityFinding;
  onClose: () => void;
}) {
  return (
    <div
      role="dialog"
      aria-modal="true"
      aria-labelledby="finding-title"
      className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4"
    >
      <section className="panel max-h-[85vh] w-full max-w-xl overflow-y-auto p-6">
        <div className="flex justify-between">
          <h2 id="finding-title" className="text-xl font-semibold">
            {finding.title}
          </h2>
          <button onClick={onClose}>Close</button>
        </div>
        <p className="muted mt-2 text-sm">
          {finding.rule_code} · {finding.category}
        </p>
        <p className="mt-4 text-sm">{finding.description}</p>
        <h3 className="mt-5 font-medium">Bounded evidence</h3>
        <dl className="mt-2 space-y-2 text-sm">
          {Object.entries(finding.evidence).map(([key, value]) => (
            <div key={key} className="flex justify-between gap-4">
              <dt className="text-slate-400">{key.replaceAll("_", " ")}</dt>
              <dd className="text-right">{String(value)}</dd>
            </div>
          ))}
        </dl>
        <p className="mt-5 text-sm text-cyan-200">{finding.recommendation}</p>
        <p className="muted mt-4 text-xs">
          Row indices are bounded. Complete raw rows are never included.
        </p>
      </section>
    </div>
  );
}
