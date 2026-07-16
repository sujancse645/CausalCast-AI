"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ReferenceLine,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import {
  ApiError,
  createForecastExperiment,
  getForecastArtifactDownloadUrl,
  getForecastComparison,
  getForecastExperiment,
  getForecastModelRegistry,
  getForecastPredictions,
  getPreparation,
  getPreparationSplits,
  listForecastExperiments,
} from "@/lib/api";
import type {
  ForecastComparison,
  ForecastExperiment,
  ForecastExperimentConfig,
  ForecastExperimentSummary,
  ForecastMetricSet,
  ForecastModelDefinition,
  ForecastModelRun,
  ForecastPrediction,
} from "@/types/forecasting";
import type { PreparationResponse, SplitDefinition } from "@/types/preparation";

export function ForecastStatusBadge({ status }: { status: string }) {
  return (
    <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-200 capitalize">
      {status.replaceAll("_", " ")}
    </span>
  );
}
export function SyntheticDataNotice() {
  return (
    <aside className="rounded-xl border border-amber-500/30 bg-amber-500/10 p-4 text-sm text-amber-100">
      Results for the bundled demonstration dataset are produced from
      deterministic synthetic data and are not business performance claims.
    </aside>
  );
}
export function ForecastErrorState({ message }: { message: string }) {
  return (
    <div role="alert" className="panel border-red-500/30 p-5 text-red-200">
      {message}
    </div>
  );
}
export function ForecastExecutionStatus({ stage }: { stage: string }) {
  return (
    <div role="status" className="panel p-5">
      <span className="mr-3 inline-block h-2 w-2 animate-pulse rounded-full bg-cyan-400" />
      {stage}
    </div>
  );
}
export function ForecastSourceSummary({
  item,
  splits,
}: {
  item: PreparationResponse;
  splits: SplitDefinition[];
}) {
  return (
    <section className="panel p-5">
      <h2 className="font-semibold">Governed source</h2>
      <div className="mt-4 grid gap-3 sm:grid-cols-3">
        <Stat label="Prepared dataset" value={item.id} />
        <Stat label="Target" value={item.target_column} />
        <Stat label="Frequency" value={item.frequency} />
        <Stat label="Groups" value={item.group_columns.join(", ") || "None"} />
        <Stat label="Features" value={item.feature_count} />
        <Stat
          label="Checksum"
          value={item.prepared_checksum?.slice(0, 16) ?? "Unavailable"}
        />
      </div>
      <div className="mt-4 text-xs text-slate-400">
        {splits.map((x) => `${x.name}: ${x.start} → ${x.end}`).join(" · ")}
      </div>
    </section>
  );
}
export function BaselineModelSelector({
  models,
  selected,
  setSelected,
}: {
  models: ForecastModelDefinition[];
  selected: string[];
  setSelected: (value: string[]) => void;
}) {
  return (
    <fieldset className="grid gap-3 sm:grid-cols-2">
      <legend className="mb-3 font-semibold">Baseline models</legend>
      {models.map((model) => (
        <label
          key={model.id}
          className="rounded-xl border border-slate-700 p-3"
        >
          <input
            type="checkbox"
            disabled={!model.enabled}
            checked={selected.includes(model.id)}
            onChange={() =>
              setSelected(
                selected.includes(model.id)
                  ? selected.filter((x) => x !== model.id)
                  : [...selected, model.id],
              )
            }
          />{" "}
          <span className="ml-2 font-medium">{model.name}</span>
          <p className="mt-1 text-xs text-slate-400">{model.description}</p>
        </label>
      ))}
    </fieldset>
  );
}
export function ForecastExperimentConfigPanel({
  models,
  onSubmit,
  busy,
}: {
  models: ForecastModelDefinition[];
  onSubmit: (config: ForecastExperimentConfig) => void;
  busy: boolean;
}) {
  const [horizon, setHorizon] = useState(30),
    [season, setSeason] = useState(7),
    [selected, setSelected] = useState<string[]>(
      models.filter((x) => x.enabled).map((x) => x.id),
    );
  const invalid = horizon < 1 || season < 2 || !selected.length;
  return (
    <section className="panel space-y-5 p-5">
      <div className="grid gap-4 sm:grid-cols-3">
        <label>
          Horizon
          <input
            aria-label="Forecast horizon"
            className="mt-1 w-full rounded-lg bg-slate-950 p-2"
            type="number"
            value={horizon}
            onChange={(e) => setHorizon(Number(e.target.value))}
          />
        </label>
        <label>
          Seasonal period
          <input
            aria-label="Seasonal period"
            className="mt-1 w-full rounded-lg bg-slate-950 p-2"
            type="number"
            value={season}
            onChange={(e) => setSeason(Number(e.target.value))}
          />
        </label>
        <label>
          Selection metric
          <select className="mt-1 w-full rounded-lg bg-slate-950 p-2">
            <option value="wape">WAPE</option>
          </select>
        </label>
      </div>
      <BaselineModelSelector
        models={models}
        selected={selected}
        setSelected={setSelected}
      />
      {invalid && (
        <p role="alert" className="text-sm text-amber-300">
          Use a positive horizon, seasonal period of at least two, and one
          model.
        </p>
      )}
      <button
        disabled={invalid || busy}
        className="rounded-xl bg-blue-600 px-5 py-3 disabled:opacity-50"
        onClick={() =>
          onSubmit({
            forecast_horizon: horizon,
            selection_metric: "wape",
            enabled_models: selected,
            moving_average_windows: [7, 14, 28],
            seasonal_period: season,
            backtest_folds: 5,
            evaluate_per_group: true,
            include_exogenous_features: true,
          })
        }
      >
        {busy ? "Experiment running…" : "Run baseline experiment"}
      </button>
    </section>
  );
}
export function ForecastExperimentHistory({
  items,
}: {
  items: ForecastExperimentSummary[];
}) {
  return (
    <section className="panel p-5">
      <h2 className="font-semibold">Experiment history</h2>
      <div className="mt-3 space-y-2">
        {items.length ? (
          items.map((x) => (
            <Link
              className="flex justify-between rounded-lg bg-slate-950/50 p-3"
              key={x.id}
              href={`/forecasting/experiments/${x.id}`}
            >
              <span>Version {x.experiment_version}</span>
              <ForecastStatusBadge status={x.status} />
            </Link>
          ))
        ) : (
          <p className="muted">No forecasting experiments yet.</p>
        )}
      </div>
    </section>
  );
}
export function ForecastWorkspace({
  datasetId,
  preparedId,
}: {
  datasetId: string;
  preparedId: string;
}) {
  const [prepared, setPrepared] = useState<PreparationResponse | null>(null),
    [splits, setSplits] = useState<SplitDefinition[]>([]),
    [models, setModels] = useState<ForecastModelDefinition[]>([]),
    [history, setHistory] = useState<ForecastExperimentSummary[]>([]),
    [error, setError] = useState<string | null>(null),
    [busy, setBusy] = useState(false);
  useEffect(() => {
    void Promise.all([
      getPreparation(preparedId),
      getPreparationSplits(preparedId),
      getForecastModelRegistry(),
      listForecastExperiments(preparedId),
    ])
      .then(([a, b, c, d]) => {
        setPrepared(a);
        setSplits(b.splits);
        setModels(c);
        setHistory(d.items);
      })
      .catch((e) =>
        setError(
          e instanceof ApiError ? e.message : "Forecasting service is offline.",
        ),
      );
  }, [preparedId]);
  const submit = (config: ForecastExperimentConfig) => {
    if (busy) return;
    setBusy(true);
    setError(null);
    void createForecastExperiment(preparedId, config)
      .then((item) => {
        window.location.href = `/forecasting/experiments/${item.id}`;
      })
      .catch((e) => {
        setError(
          e instanceof ApiError ? e.message : "Experiment failed safely.",
        );
        setBusy(false);
      });
  };
  if (error && !prepared) return <ForecastErrorState message={error} />;
  if (!prepared)
    return <ForecastExecutionStatus stage="Loading governed preparation…" />;
  return (
    <div className="space-y-6">
      <Link
        className="text-blue-400"
        href={`/data-intelligence/${datasetId}/preparations/${preparedId}`}
      >
        ← Prepared dataset
      </Link>
      <header>
        <p className="text-xs tracking-[.2em] text-cyan-400 uppercase">
          Phase 3A · Baseline forecasting
        </p>
        <h1 className="mt-2 text-3xl font-semibold">
          Forecast experiment workspace
        </h1>
      </header>
      <SyntheticDataNotice />
      <ForecastSourceSummary item={prepared} splits={splits} />
      {error && <ForecastErrorState message={error} />}{" "}
      {busy ? (
        <ForecastExecutionStatus stage="Validating source, fitting baselines, retraining folds, ranking models, and evaluating the selected model…" />
      ) : (
        <ForecastExperimentConfigPanel
          models={models}
          onSubmit={submit}
          busy={busy}
        />
      )}
      <ForecastExperimentHistory items={history} />
    </div>
  );
}
function metric(value: number | null | undefined) {
  return value === null || value === undefined ? "—" : value.toFixed(4);
}
export function ForecastMetricsGrid({
  metrics,
}: {
  metrics: ForecastMetricSet | null;
}) {
  return (
    <div className="grid gap-3 sm:grid-cols-4">
      <Stat label="WAPE" value={metric(metrics?.wape)} />
      <Stat label="MAE" value={metric(metrics?.mae)} />
      <Stat label="RMSE" value={metric(metrics?.rmse)} />
      <Stat label="sMAPE" value={metric(metrics?.smape)} />
    </div>
  );
}
export function ModelLeaderboard({ runs }: { runs: ForecastModelRun[] }) {
  return (
    <section className="panel overflow-x-auto p-5">
      <h2 className="font-semibold">Model leaderboard</h2>
      <table className="mt-4 w-full min-w-[800px] text-sm">
        <thead>
          <tr>
            <th>Rank</th>
            <th>Model</th>
            <th>Status</th>
            <th>Validation WAPE</th>
            <th>Backtest WAPE</th>
            <th>Validation MAE</th>
            <th>Stability</th>
            <th>Duration</th>
          </tr>
        </thead>
        <tbody>
          {runs.map((x) => (
            <tr className="border-t border-slate-800" key={x.id}>
              <td>{x.rank ?? "—"}</td>
              <td>
                {x.model_name}
                {x.selected && " · Selected"}
              </td>
              <td>
                <ForecastStatusBadge status={x.status} />
              </td>
              <td>{metric(x.validation_metrics?.wape)}</td>
              <td>{metric(x.backtest_metrics?.wape)}</td>
              <td>{metric(x.validation_metrics?.mae)}</td>
              <td>
                {metric(x.backtest_metrics?.fold_wape_standard_deviation)}
              </td>
              <td>{x.training_duration_ms + x.backtest_duration_ms} ms</td>
            </tr>
          ))}
        </tbody>
      </table>
      {runs.some((x) => x.failure_message) && (
        <div className="mt-4 text-sm text-amber-200">
          {runs
            .filter((x) => x.failure_message)
            .map((x) => (
              <p key={x.id}>
                {x.model_name}: {x.failure_message}
              </p>
            ))}
        </div>
      )}
    </section>
  );
}
export function SplitBoundaryLegend({
  experiment,
}: {
  experiment: ForecastExperiment;
}) {
  return (
    <p className="text-xs text-slate-400">
      Validation starts {experiment.validation_start} · Test starts{" "}
      {experiment.test_start}
    </p>
  );
}
export function ForecastChart({
  rows,
  experiment,
}: {
  rows: ForecastPrediction[];
  experiment: ForecastExperiment;
}) {
  const groups = useMemo(
    () => [...new Set(rows.map((x) => x.group ?? "all"))],
    [rows],
  );
  const [group, setGroup] = useState(groups[0] ?? "all");
  const activeGroup = groups.includes(group) ? group : (groups[0] ?? "all");
  const data = rows.filter((x) => (x.group ?? "all") === activeGroup);
  return (
    <section className="panel p-5">
      <div className="flex justify-between">
        <h2 className="font-semibold">Actual vs forecast</h2>
        {groups.length > 1 && (
          <select
            aria-label="Forecast group"
            value={activeGroup}
            onChange={(e) => setGroup(e.target.value)}
            className="bg-slate-950 p-2"
          >
            {groups.map((x) => (
              <option key={x}>{x}</option>
            ))}
          </select>
        )}
      </div>
      <SplitBoundaryLegend experiment={experiment} />
      <div className="mt-4 h-80">
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="#1e293b" />
            <XAxis dataKey="date" hide />
            <YAxis />
            <Tooltip />
            <Legend />
            <ReferenceLine x={experiment.test_start} stroke="#f59e0b" />
            <Line dataKey="actual" stroke="#94a3b8" dot={false} />
            <Line dataKey="prediction" stroke="#22d3ee" dot={false} />
          </LineChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
export function ResidualSummaryPanel({ run }: { run?: ForecastModelRun }) {
  const r = run?.residual_summary;
  return (
    <section className="panel p-5">
      <h2 className="font-semibold">Residual summary</h2>
      {r ? (
        <div className="mt-4 grid gap-3 sm:grid-cols-4">
          <Stat label="Mean residual" value={metric(r.mean)} />
          <Stat label="Spread" value={metric(r.standard_deviation)} />
          <Stat label="Median" value={metric(r.median)} />
          <Stat label="Large residuals" value={r.large_residual_count} />
        </div>
      ) : (
        <p className="muted mt-3">
          Residual details are unavailable. Missing values are not shown as
          zero.
        </p>
      )}
      <p className="muted mt-3 text-xs">
        Residual summaries are descriptive and do not establish statistical
        validity.
      </p>
    </section>
  );
}
export function BacktestResultsTable({ run }: { run?: ForecastModelRun }) {
  return (
    <section className="panel overflow-x-auto p-5">
      <h2 className="font-semibold">Expanding-window backtests</h2>
      <table className="mt-4 w-full text-sm">
        <tbody>
          {run?.per_fold_metrics?.map((x, index) => (
            <tr key={index}>
              <td>Fold {String(x.fold)}</td>
              <td>
                {String(x.train_start)} → {String(x.train_end)}
              </td>
              <td>WAPE {metric(typeof x.wape === "number" ? x.wape : null)}</td>
              <td>MAE {metric(typeof x.mae === "number" ? x.mae : null)}</td>
            </tr>
          ))}
        </tbody>
      </table>
    </section>
  );
}
export function ForecastArtifactDownloads({ runId }: { runId: string }) {
  return (
    <section className="panel p-5">
      <h2 className="font-semibold">Governed artifacts</h2>
      <div className="mt-3 flex flex-wrap gap-3">
        {["model_card", "metrics", "test_predictions", "model"].map((x) => (
          <a
            className="rounded-lg border border-slate-700 px-3 py-2 text-sm"
            key={x}
            href={getForecastArtifactDownloadUrl(runId, x)}
          >
            Download {x.replaceAll("_", " ")}
          </a>
        ))}
      </div>
    </section>
  );
}
export function ForecastExperimentSummaryView({
  experiment,
  comparison,
  predictions,
}: {
  experiment: ForecastExperiment;
  comparison: ForecastComparison;
  predictions: ForecastPrediction[];
}) {
  const selected = comparison.items.find((x) => x.selected);
  return (
    <div className="space-y-6">
      <SyntheticDataNotice />
      <section className="panel p-5">
        <div className="flex justify-between">
          <div>
            <p className="text-xs text-cyan-400 uppercase">
              Experiment {experiment.experiment_version}
            </p>
            <h1 className="text-3xl font-semibold">
              Baseline forecast evaluation
            </h1>
          </div>
          <ForecastStatusBadge status={experiment.status} />
        </div>
        <p className="muted mt-3">
          Selected model: {selected?.model_name ?? "Not selected"} · Ranking
          never uses final test metrics.
        </p>
        <div className="mt-5">
          <ForecastMetricsGrid metrics={selected?.validation_metrics ?? null} />
        </div>
      </section>
      <ModelLeaderboard runs={comparison.items} />
      <ForecastChart rows={predictions} experiment={experiment} />
      <ResidualSummaryPanel run={selected} />
      <BacktestResultsTable run={selected} />
      {selected && <ForecastArtifactDownloads runId={selected.id} />}
    </div>
  );
}
export function ForecastExperimentDetail({
  experimentId,
}: {
  experimentId: string;
}) {
  const [experiment, setExperiment] = useState<ForecastExperiment | null>(null),
    [comparison, setComparison] = useState<ForecastComparison | null>(null),
    [rows, setRows] = useState<ForecastPrediction[]>([]),
    [error, setError] = useState<string | null>(null);
  useEffect(() => {
    void Promise.all([
      getForecastExperiment(experimentId),
      getForecastComparison(experimentId),
      getForecastPredictions(experimentId, { split: "test" }),
    ])
      .then(([a, b, c]) => {
        setExperiment(a);
        setComparison(b);
        setRows(c.items);
      })
      .catch((e) =>
        setError(
          e instanceof ApiError
            ? e.message
            : "Forecast experiment is unavailable.",
        ),
      );
  }, [experimentId]);
  if (error) return <ForecastErrorState message={error} />;
  if (!experiment || !comparison)
    return (
      <ForecastExecutionStatus stage="Loading executed forecast results…" />
    );
  return (
    <ForecastExperimentSummaryView
      experiment={experiment}
      comparison={comparison}
      predictions={rows}
    />
  );
}
function Stat({ label, value }: { label: string; value: string | number }) {
  return (
    <div className="min-w-0">
      <p className="truncate font-semibold" title={String(value)}>
        {value}
      </p>
      <p className="muted text-xs">{label}</p>
    </div>
  );
}
