"use client";
import Link from "next/link";
import { useCallback, useEffect, useMemo, useState } from "react";
import {
  analyzeDatasetQuality,
  ApiError,
  getDataset,
  getDatasetQuality,
  getQualityHistory,
} from "@/lib/api";
import type { DatasetDetail } from "@/types/dataset";
import type {
  QualityFinding,
  QualityHistoryItem,
  QualityReportDetail,
} from "@/types/quality";
import { QualityFindingDetails } from "./quality-finding-details";
import { QualityFindingsTable } from "./quality-findings-table";
import {
  LeakageRiskPanel,
  QualityReadinessPanel,
  QualityReportHistory,
  TemporalQualityPanel,
} from "./quality-panels";
import { QualityScoreCard } from "./quality-score-card";

export function DataQualityWorkspace({ datasetId }: { datasetId: string }) {
  const [dataset, setDataset] = useState<DatasetDetail | null>(null);
  const [report, setReport] = useState<QualityReportDetail | null>(null);
  const [history, setHistory] = useState<QualityHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [selected, setSelected] = useState<QualityFinding | null>(null);
  const [severity, setSeverity] = useState("");
  const [category, setCategory] = useState("");
  const [blocking, setBlocking] = useState(false);
  const load = useCallback(async () => {
    try {
      const [d, h] = await Promise.all([
        getDataset(datasetId),
        getQualityHistory(datasetId),
      ]);
      setDataset(d);
      setHistory(h.items);
      try {
        setReport(await getDatasetQuality(datasetId));
      } catch (e) {
        if (!(e instanceof ApiError && e.status === 404)) throw e;
      }
      setError(null);
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Data-quality service is offline.",
      );
    } finally {
      setLoading(false);
    }
  }, [datasetId]);
  useEffect(() => {
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);
  const run = async () => {
    setRunning(true);
    setError(null);
    try {
      setReport(
        await analyzeDatasetQuality(
          datasetId,
          report ? "Manual rerun" : "Initial analysis",
        ),
      );
      setHistory((await getQualityHistory(datasetId)).items);
    } catch (e) {
      setError(
        e instanceof ApiError
          ? e.message
          : "Quality analysis failed while offline.",
      );
    } finally {
      setRunning(false);
    }
  };
  const filtered = useMemo(
    () =>
      report?.findings.filter(
        (x) =>
          (!severity || x.severity === severity) &&
          (!category || x.category === category) &&
          (!blocking || x.blocking),
      ) ?? [],
    [report, severity, category, blocking],
  );
  if (loading) return <p role="status">Loading data-quality workspace…</p>;
  if (!dataset) return <p role="alert">{error ?? "Dataset not found."}</p>;
  return (
    <div className="space-y-6">
      <nav className="flex flex-wrap gap-4 text-sm">
        <Link href="/data-intelligence" className="text-blue-400">
          ← Dataset library
        </Link>
        <Link
          href={`/data-intelligence/${datasetId}/schema`}
          className="text-cyan-300"
        >
          Schema mapping
        </Link>
        {report && report.readiness_status !== "blocked" && (
          <Link
            href={`/data-intelligence/${datasetId}/prepare`}
            className="text-emerald-300"
          >
            Prepare dataset
          </Link>
        )}
      </nav>
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs tracking-[.2em] text-cyan-400 uppercase">
            Phase 2C · Data Quality Intelligence
          </p>
          <h1 className="mt-2 text-2xl font-semibold">
            {dataset.original_filename}
          </h1>
          <p className="muted text-sm">
            {dataset.row_count} rows · {dataset.column_count} columns
            {report
              ? ` · schema v${report.schema_version} · quality v${report.report_version}`
              : ""}
          </p>
        </div>
        <button
          disabled={running}
          onClick={() => void run()}
          className="rounded-lg bg-blue-600 px-4 py-2 disabled:opacity-50"
        >
          {running
            ? "Analyzing bounded data…"
            : report
              ? "Rerun analysis"
              : "Run analysis"}
        </button>
      </header>
      {error && (
        <p
          role="alert"
          className="rounded-lg border border-rose-500/30 p-3 text-rose-200"
        >
          {error}
        </p>
      )}
      <p className="rounded-lg border border-violet-500/20 p-3 text-sm text-violet-200">
        This report analyzes data quality. It does not modify the raw dataset.
      </p>
      {!report ? (
        <section className="panel p-10 text-center">
          <h2 className="text-xl font-semibold">No quality report yet</h2>
          <p className="muted mt-2">
            Run deterministic analysis after reviewing the schema mapping.
          </p>
        </section>
      ) : (
        <>
          <section className="panel p-5">
            <div className="flex flex-wrap items-end justify-between gap-4">
              <div>
                <p className="muted text-xs">Overall quality score</p>
                <p className="text-4xl font-semibold">
                  {Math.round(report.overall_score)}/100
                </p>
                <p className="mt-1 capitalize">
                  {report.readiness_status.replaceAll("_", " ")}
                </p>
              </div>
              <div className="text-sm">
                <p>
                  Blockers {report.blocker_count} · Errors {report.error_count}{" "}
                  · Warnings {report.warning_count}
                </p>
                <p>
                  Scan coverage {(report.scan_coverage_ratio * 100).toFixed(1)}%
                  · {report.duration_ms} ms
                </p>
                {report.scan_coverage_ratio < 1 && (
                  <p className="text-amber-300">
                    Partial bounded scan; findings do not claim full-file
                    coverage.
                  </p>
                )}
              </div>
            </div>
          </section>
          <section className="grid gap-3 sm:grid-cols-2 xl:grid-cols-4">
            {Object.entries(report.dimension_scores).map(([name, value]) => (
              <QualityScoreCard
                key={name}
                label={name.replaceAll("_", " ")}
                score={value}
              />
            ))}
          </section>
          <QualityReadinessPanel report={report} />
          <TemporalQualityPanel report={report} />
          <LeakageRiskPanel findings={report.findings} />
          <section className="panel p-4">
            <h2 className="sr-only">Finding filters</h2>
            <div className="flex flex-wrap gap-3">
              <select
                aria-label="Filter severity"
                value={severity}
                onChange={(e) => setSeverity(e.target.value)}
                className="rounded border border-slate-700 bg-slate-950 p-2"
              >
                <option value="">All severities</option>
                {["blocker", "error", "warning", "info"].map((x) => (
                  <option key={x}>{x}</option>
                ))}
              </select>
              <select
                aria-label="Filter category"
                value={category}
                onChange={(e) => setCategory(e.target.value)}
                className="rounded border border-slate-700 bg-slate-950 p-2"
              >
                <option value="">All categories</option>
                {Array.from(
                  new Set(report.findings.map((x) => x.category)),
                ).map((x) => (
                  <option key={x}>{x}</option>
                ))}
              </select>
              <label className="flex items-center gap-2">
                <input
                  type="checkbox"
                  checked={blocking}
                  onChange={(e) => setBlocking(e.target.checked)}
                />{" "}
                Blocking only
              </label>
            </div>
          </section>
          <QualityFindingsTable items={filtered} onView={setSelected} />
        </>
      )}
      <QualityReportHistory items={history} />
      {selected && (
        <QualityFindingDetails
          finding={selected}
          onClose={() => setSelected(null)}
        />
      )}
    </div>
  );
}
