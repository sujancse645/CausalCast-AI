"use client";
import type { ForecastModelDefinition } from "@/types/forecasting";
import type {
  FeatureImportance,
  ShapExplanation,
  TuningSummary,
} from "@/types/gradient-boosting";
const ADVANCED = new Set([
  "lightgbm_regressor",
  "xgboost_regressor",
  "catboost_regressor",
]);
export function DependencyAvailabilityBadge({
  available,
}: {
  available: boolean;
}) {
  return (
    <span className={available ? "text-emerald-300" : "text-amber-300"}>
      {available ? "Available" : "Unavailable"}
    </span>
  );
}
export function AdvancedModelSelector({
  models,
  selected,
  setSelected,
}: {
  models: ForecastModelDefinition[];
  selected: string[];
  setSelected: (items: string[]) => void;
}) {
  return (
    <fieldset className="grid gap-3 sm:grid-cols-3">
      <legend className="mb-3 font-semibold">Gradient-boosting models</legend>
      {models
        .filter((m) => ADVANCED.has(m.id))
        .map((model) => (
          <label
            key={model.id}
            className="rounded-xl border border-slate-700 p-3"
          >
            <input
              type="checkbox"
              disabled={model.dependency_available === false}
              checked={selected.includes(model.id)}
              onChange={() =>
                setSelected(
                  selected.includes(model.id)
                    ? selected.filter((id) => id !== model.id)
                    : [...selected, model.id],
                )
              }
            />{" "}
            <span className="ml-2 font-medium">{model.name}</span>
            <p className="mt-1 text-xs text-slate-400">{model.description}</p>
            <DependencyAvailabilityBadge
              available={model.dependency_available !== false}
            />
          </label>
        ))}
    </fieldset>
  );
}
export function ExplanationDisclaimer() {
  return (
    <p className="rounded-lg border border-amber-500/30 bg-amber-500/10 p-3 text-sm text-amber-100">
      Feature contribution does not prove causation.
    </p>
  );
}
export function TuningSummaryPanel({ summary }: { summary: TuningSummary }) {
  return (
    <section className="panel p-5">
      <h2 className="font-semibold">Chronological tuning</h2>
      <p className="mt-2 text-sm">
        {summary.completed_trials} completed · {summary.failed_trials} failed ·
        best WAPE {summary.best_score?.toFixed(4) ?? "—"}
      </p>
      <pre className="mt-3 overflow-auto text-xs">
        {JSON.stringify(summary.best_parameters, null, 2)}
      </pre>
      <div className="mt-4 overflow-x-auto">
        <table className="w-full text-left text-xs">
          <thead>
            <tr>
              <th>Trial</th>
              <th>Status</th>
              <th>Backtest WAPE</th>
              <th>Duration</th>
            </tr>
          </thead>
          <tbody>
            {summary.items.slice(0, 25).map((trial) => (
              <tr
                className="border-t border-slate-800"
                key={trial.trial_number}
              >
                <td>{trial.trial_number}</td>
                <td>{trial.status}</td>
                <td>{trial.backtest_metric?.toFixed(4) ?? "—"}</td>
                <td>{trial.duration_ms} ms</td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
export function FeatureImportancePanel({
  importance,
  shap,
}: {
  importance: FeatureImportance;
  shap?: ShapExplanation;
}) {
  const items =
    shap?.items ??
    importance.items.map((item) => ({
      feature: item.feature,
      mean_absolute_shap: item.shap_importance ?? item.native_importance ?? 0,
    }));
  return (
    <section className="panel p-5">
      <h2 className="font-semibold">Feature contribution</h2>
      <div className="mt-3 space-y-2">
        {items.slice(0, 15).map((item) => (
          <div className="flex justify-between text-sm" key={item.feature}>
            <span>{item.feature}</span>
            <span>{item.mean_absolute_shap.toFixed(4)}</span>
          </div>
        ))}
      </div>
      <div className="mt-4">
        <ExplanationDisclaimer />
      </div>
    </section>
  );
}
