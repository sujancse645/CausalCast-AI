"use client";
import Link from "next/link";
import { useEffect, useMemo, useState } from "react";
import {
  ApiError,
  createPreparation,
  getDataset,
  getDatasetQuality,
  getDatasetSchema,
  listPreparations,
} from "@/lib/api";
import type { DatasetDetail } from "@/types/dataset";
import type { QualityReportDetail } from "@/types/quality";
import type { DatasetSchemaDetail } from "@/types/schema-mapping";
import type {
  PreparationConfig,
  PreparationResponse,
  PreparationSummary,
} from "@/types/preparation";

export function PreparationWorkspace({ datasetId }: { datasetId: string }) {
  const [dataset, setDataset] = useState<DatasetDetail | null>(null),
    [schema, setSchema] = useState<DatasetSchemaDetail | null>(null),
    [quality, setQuality] = useState<QualityReportDetail | null>(null),
    [history, setHistory] = useState<PreparationSummary[]>([]),
    [result, setResult] = useState<PreparationResponse | null>(null),
    [loading, setLoading] = useState(true),
    [running, setRunning] = useState(false),
    [error, setError] = useState<string | null>(null);
  const numeric = useMemo(
    () =>
      schema?.columns.filter(
        (x) =>
          ["integer", "float"].includes(x.physical_type) &&
          x.semantic_role !== "ignored",
      ) ?? [],
    [schema],
  );
  const dates = useMemo(
    () =>
      schema?.columns.filter((x) =>
        ["date", "timestamp"].includes(x.semantic_role),
      ) ?? [],
    [schema],
  );
  const dimensions = useMemo(
    () =>
      schema?.columns.filter((x) =>
        [
          "channel",
          "campaign",
          "product_category",
          "region",
          "device",
        ].includes(x.semantic_role),
      ) ?? [],
    [schema],
  );
  const [config, setConfig] = useState<PreparationConfig>({
    target_column: "",
    date_column: "",
    group_columns: [],
    frequency: "daily",
    forecast_horizon: 30,
    aggregation_rules: {},
    duplicate_period_policy: "aggregate",
    missing_period_policy: "preserve",
    missing_target_policy: "drop_rows_missing_target",
    lag_periods: [1, 7, 14, 28],
    rolling_windows: [7, 28],
    rolling_statistics: ["mean"],
    include_calendar_features: true,
    include_trend_features: true,
    include_holiday_features: false,
    holiday_dates: [],
    include_promotion_features: true,
    include_derived_metrics: true,
    include_missingness_indicators: true,
    train_ratio: 0.7,
    validation_ratio: 0.15,
    test_ratio: 0.15,
    backtest_folds: 3,
    quality_override: false,
    quality_override_reason: null,
    output_format: "csv",
  });
  useEffect(() => {
    void Promise.all([
      getDataset(datasetId),
      getDatasetSchema(datasetId),
      getDatasetQuality(datasetId),
      listPreparations(datasetId),
    ])
      .then(([d, s, q, h]) => {
        setDataset(d);
        setSchema(s);
        setQuality(q);
        setHistory(h.items);
        setConfig((c) => ({
          ...c,
          target_column: s.summary.primary_target_candidate ?? "",
          date_column: s.summary.primary_date_candidate ?? "",
        }));
      })
      .catch((e) =>
        setError(
          e instanceof ApiError ? e.message : "Preparation service is offline.",
        ),
      )
      .finally(() => setLoading(false));
  }, [datasetId]);
  const blocked =
    !schema ||
    schema.status !== "confirmed" ||
    !quality ||
    quality.readiness_status === "blocked";
  const submit = async () => {
    setRunning(true);
    setError(null);
    try {
      const value = await createPreparation(datasetId, config);
      setResult(value);
      setHistory((await listPreparations(datasetId)).items);
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Preparation failed while offline.",
      );
    } finally {
      setRunning(false);
    }
  };
  if (loading) return <p role="status">Loading source readiness…</p>;
  return (
    <div className="space-y-6">
      <nav className="flex gap-4 text-sm">
        <Link className="text-blue-400" href="/data-intelligence">
          ← Dataset library
        </Link>
        <Link
          className="text-violet-300"
          href={`/data-intelligence/${datasetId}/quality`}
        >
          Data quality
        </Link>
      </nav>
      <header>
        <p className="text-xs tracking-[.2em] text-cyan-400 uppercase">
          Phase 2D · Governed preparation
        </p>
        <h1 className="mt-2 text-2xl font-semibold">
          Prepare {dataset?.original_filename ?? "dataset"}
        </h1>
        <p className="muted text-sm">
          Immutable source → deterministic features → chronological splits
        </p>
      </header>
      {error && (
        <p
          role="alert"
          className="rounded border border-rose-500/30 p-3 text-rose-200"
        >
          {error}
        </p>
      )}
      <section className="panel p-5">
        <h2 className="font-semibold">1. Source readiness</h2>
        <div className="mt-3 grid gap-3 sm:grid-cols-4">
          <Metric label="Schema" value={schema?.status ?? "unavailable"} />
          <Metric
            label="Quality"
            value={quality?.readiness_status ?? "unavailable"}
          />
          <Metric label="Rows" value={String(dataset?.row_count ?? 0)} />
          <Metric
            label="Blockers"
            value={String(quality?.blocker_count ?? 0)}
          />
        </div>
        {blocked && (
          <p className="mt-3 text-amber-300">
            Preparation is blocked until schema confirmation and a non-blocked
            quality report exist.
          </p>
        )}
      </section>
      <section className="panel space-y-5 p-5">
        <h2 className="font-semibold">2. Time-series configuration</h2>
        <div className="grid gap-4 md:grid-cols-3">
          <Select
            label="Target"
            value={config.target_column}
            options={numeric.map((x) => x.column_name)}
            onChange={(v) => setConfig({ ...config, target_column: v })}
          />
          <Select
            label="Date"
            value={config.date_column}
            options={dates.map((x) => x.column_name)}
            onChange={(v) => setConfig({ ...config, date_column: v })}
          />
          <Select
            label="Frequency"
            value={config.frequency}
            options={["hourly", "daily", "weekly", "monthly", "quarterly"]}
            onChange={(v) =>
              setConfig({
                ...config,
                frequency: v as PreparationConfig["frequency"],
              })
            }
          />
        </div>
        <fieldset>
          <legend className="text-sm text-slate-300">Optional groups</legend>
          <div className="mt-2 flex flex-wrap gap-3">
            {dimensions.map((x) => (
              <label key={x.id} className="text-sm">
                <input
                  type="checkbox"
                  checked={config.group_columns.includes(x.column_name)}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      group_columns: e.target.checked
                        ? [...config.group_columns, x.column_name]
                        : config.group_columns.filter(
                            (v) => v !== x.column_name,
                          ),
                    })
                  }
                />{" "}
                {x.column_name}
              </label>
            ))}
          </div>
        </fieldset>
      </section>
      <section className="panel space-y-4 p-5">
        <h2 className="font-semibold">3. Leakage-safe features</h2>
        <label className="block text-sm">
          Lag periods{" "}
          <input
            aria-label="Lag periods"
            className="ml-2 rounded border border-slate-700 bg-slate-950 p-2"
            value={config.lag_periods.join(",")}
            onChange={(e) =>
              setConfig({
                ...config,
                lag_periods: e.target.value
                  .split(",")
                  .map(Number)
                  .filter(Boolean),
              })
            }
          />
        </label>
        <label className="block text-sm">
          Rolling windows{" "}
          <input
            aria-label="Rolling windows"
            className="ml-2 rounded border border-slate-700 bg-slate-950 p-2"
            value={config.rolling_windows.join(",")}
            onChange={(e) =>
              setConfig({
                ...config,
                rolling_windows: e.target.value
                  .split(",")
                  .map(Number)
                  .filter(Boolean),
              })
            }
          />
        </label>
        <label>
          <input
            type="checkbox"
            checked={config.include_calendar_features}
            onChange={(e) =>
              setConfig({
                ...config,
                include_calendar_features: e.target.checked,
              })
            }
          />{" "}
          Calendar features
        </label>
        <p className="text-sm text-amber-200">
          Target lags and rolling windows use prior observations only.
          Same-period target-derived metrics are excluded.
        </p>
      </section>
      <section className="panel p-5">
        <h2 className="font-semibold">4. Chronological split</h2>
        <p className="muted mt-2">
          Train 70% · Validation 15% · Test 15% · never shuffled
        </p>
        <div
          className="mt-3 grid grid-cols-[7fr_1.5fr_1.5fr] gap-1"
          aria-label="Chronological split timeline"
        >
          <span className="bg-blue-600/40 p-2">Train</span>
          <span className="bg-violet-600/40 p-2">Validation</span>
          <span className="bg-cyan-600/40 p-2">Test</span>
        </div>
      </section>
      <section className="panel p-5">
        <h2 className="font-semibold">5. Review and prepare</h2>
        <p className="muted mt-2 text-sm">
          {config.frequency} frequency · target{" "}
          {config.target_column || "not selected"} · {config.lag_periods.length}{" "}
          lags · {config.rolling_windows.length} rolling windows
        </p>
        {quality &&
          quality.readiness_status !== "quality_ready" &&
          quality.readiness_status !== "blocked" && (
            <div className="mt-4 rounded border border-amber-500/20 bg-amber-500/10 p-4 text-sm text-amber-200">
              <label className="flex cursor-pointer items-start gap-2">
                <input
                  type="checkbox"
                  className="mt-1"
                  checked={config.quality_override}
                  onChange={(e) =>
                    setConfig({ ...config, quality_override: e.target.checked })
                  }
                />
                <span>Override conditional quality warnings.</span>
              </label>
              {config.quality_override && (
                <input
                  className="mt-2 w-full rounded border border-amber-700 bg-black/50 p-2 text-white"
                  placeholder="Required: Reason for override"
                  value={config.quality_override_reason || ""}
                  onChange={(e) =>
                    setConfig({
                      ...config,
                      quality_override_reason: e.target.value,
                    })
                  }
                />
              )}
            </div>
          )}
        <button
          disabled={
            blocked ||
            running ||
            !config.target_column ||
            !config.date_column ||
            (quality &&
              quality.readiness_status !== "quality_ready" &&
              quality.readiness_status !== "blocked" &&
              (!config.quality_override || !config.quality_override_reason))
          }
          onClick={() => void submit()}
          className="mt-4 rounded bg-blue-600 px-4 py-2 disabled:opacity-40"
        >
          {running ? "Preparing governed artifact…" : "Start preparation"}
        </button>
      </section>
      {result && (
        <section className="panel p-5">
          <h2 className="font-semibold">6. Preparation result</h2>
          <div className="mt-3 grid gap-3 sm:grid-cols-4">
            <Metric label="Rows" value={String(result.row_count)} />
            <Metric label="Features" value={String(result.feature_count)} />
            <Metric
              label="Generated periods"
              value={String(result.generated_rows)}
            />
            <Metric label="Readiness" value={result.readiness_status} />
          </div>
          <p className="muted mt-3 font-mono text-xs">
            Checksum {result.prepared_checksum}
          </p>
          <Link
            className="mt-4 inline-block text-cyan-300"
            href={`/data-intelligence/${datasetId}/preparations/${result.id}`}
          >
            View prepared dataset →
          </Link>
        </section>
      )}
      <section className="panel p-5">
        <h2 className="font-semibold">Preparation history</h2>
        {history.length ? (
          <ul className="mt-3 space-y-2">
            {history.map((x) => (
              <li key={x.id}>
                <Link
                  className="text-blue-300"
                  href={`/data-intelligence/${datasetId}/preparations/${x.id}`}
                >
                  Version {x.preparation_version} · {x.status} · {x.row_count}{" "}
                  rows
                </Link>
              </li>
            ))}
          </ul>
        ) : (
          <p className="muted mt-2">No prepared artifacts yet.</p>
        )}
      </section>
    </div>
  );
}
function Metric({ label, value }: { label: string; value: string }) {
  return (
    <div>
      <p className="text-lg font-semibold capitalize">
        {value.replaceAll("_", " ")}
      </p>
      <p className="muted text-xs">{label}</p>
    </div>
  );
}
function Select({
  label,
  value,
  options,
  onChange,
}: {
  label: string;
  value: string;
  options: string[];
  onChange: (v: string) => void;
}) {
  return (
    <label className="text-sm">
      {label}
      <select
        aria-label={label}
        value={value}
        onChange={(e) => onChange(e.target.value)}
        className="mt-1 block w-full rounded border border-slate-700 bg-slate-950 p-2"
      >
        <option value="">Select</option>
        {options.map((x) => (
          <option key={x}>{x}</option>
        ))}
      </select>
    </label>
  );
}
