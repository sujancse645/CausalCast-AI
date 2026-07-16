import type {
  QualityFinding,
  QualityHistoryItem,
  QualityReportDetail,
} from "@/types/quality";
export function QualityReadinessPanel({
  report,
}: {
  report: QualityReportDetail;
}) {
  return (
    <section className="panel p-5">
      <h2 className="font-semibold">Readiness decision</h2>
      <p className="mt-2 text-lg capitalize">
        {report.readiness_status.replaceAll("_", " ")}
      </p>
      <p className="muted mt-2 text-sm">
        {report.blocker_count
          ? `${report.blocker_count} blocking issue(s) require review.`
          : "Quality-ready status supports governed preparation only; it is not forecasting readiness."}
      </p>
    </section>
  );
}
export function TemporalQualityPanel({
  report,
}: {
  report: QualityReportDetail;
}) {
  const t = report.summary.temporal;
  return (
    <section className="panel p-5">
      <h2 className="font-semibold">Temporal quality</h2>
      {!t?.available ? (
        <p className="muted mt-3 text-sm">
          No mapped primary date is available.
        </p>
      ) : (
        <div className="mt-3 grid gap-3 text-sm sm:grid-cols-3">
          <p>
            Frequency: <span className="capitalize">{t.frequency}</span>
          </p>
          <p>
            Range: {t.date_min?.slice(0, 10)} — {t.date_max?.slice(0, 10)}
          </p>
          <p>
            Gaps: {t.gap_count} · Future: {t.future_dates} · Out of order:{" "}
            {t.out_of_order}
          </p>
        </div>
      )}
    </section>
  );
}
export function LeakageRiskPanel({ findings }: { findings: QualityFinding[] }) {
  const leakage = findings.filter((x) => x.category === "leakage");
  return (
    <section className="panel p-5">
      <h2 className="font-semibold">Leakage risk signals</h2>
      <p className="muted mt-2 text-xs">
        Leakage findings are deterministic or heuristic risk signals. Human
        review is required.
      </p>
      <ul className="mt-3 space-y-2 text-sm">
        {leakage.map((x) => (
          <li key={x.id}>
            {x.severity.toUpperCase()} — {x.title}
          </li>
        ))}
        {!leakage.length && (
          <li>No leakage signals were detected in the bounded scan.</li>
        )}
      </ul>
    </section>
  );
}
export function QualityReportHistory({
  items,
}: {
  items: QualityHistoryItem[];
}) {
  return (
    <section className="panel p-5">
      <h2 className="font-semibold">Report history</h2>
      <ul className="mt-3 space-y-2">
        {items.map((x) => (
          <li className="flex justify-between text-sm" key={x.id}>
            <span>
              Version {x.report_version} · schema {x.schema_version} ·{" "}
              {x.status}
            </span>
            <span>
              {Math.round(x.overall_score)}/100 ·{" "}
              {x.readiness_status.replaceAll("_", " ")}
            </span>
          </li>
        ))}
        {!items.length && (
          <li className="muted text-sm">No report versions yet.</li>
        )}
      </ul>
    </section>
  );
}
