"use client";

import { useEffect, useState } from "react";
import {
  ApiError,
  createDeepReadinessReport,
  getDeepForecastCapabilities,
  getDeepReadinessReport,
} from "@/lib/api";
import type {
  DeepForecastCapability,
  DeepForecastReadiness,
} from "@/types/deep-forecasting";

export function DeepReadinessBadge({ status }: { status: string }) {
  return (
    <span className="rounded-full border border-violet-400/30 bg-violet-500/10 px-3 py-1 text-xs text-violet-200 capitalize">
      {status.replaceAll("_", " ")}
    </span>
  );
}

export function DeepModelCapabilityList({
  capability,
}: {
  capability: DeepForecastCapability;
}) {
  return (
    <div className="grid gap-3 md:grid-cols-3">
      {capability.models.map((model) => (
        <article
          className="rounded-xl border border-slate-700 p-4"
          key={model.identifier}
        >
          <div className="flex items-center justify-between gap-2">
            <h3 className="font-semibold">{model.display_name}</h3>
            <DeepReadinessBadge status={model.implementation_status} />
          </div>
          <p className="mt-2 text-sm text-slate-400">{model.description}</p>
          <p className="mt-3 text-xs text-slate-500">
            {model.dependency_available
              ? "Dependencies available"
              : "Optional dependency missing"}
          </p>
        </article>
      ))}
    </div>
  );
}

export function DeepHardwareSummary({
  capability,
}: {
  capability: DeepForecastCapability;
}) {
  const hardware = capability.hardware;
  return (
    <div className="grid gap-3 sm:grid-cols-4">
      <Value label="Engine" value={capability.engine} />
      <Value
        label="Selected accelerator"
        value={hardware.selected_accelerator.toUpperCase()}
      />
      <Value label="CUDA devices" value={hardware.cuda_device_count} />
      <Value
        label="Deterministic"
        value={hardware.deterministic_mode_configured ? "Configured" : "Off"}
      />
    </div>
  );
}

export function DeepForecastingStatusCard() {
  const [capability, setCapability] = useState<DeepForecastCapability | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    void getDeepForecastCapabilities()
      .then(setCapability)
      .catch((reason: unknown) =>
        setError(
          reason instanceof ApiError
            ? `Deep capability service is offline. ${reason.message}`
            : reason instanceof Error
              ? reason.message
              : "Deep capability service is offline.",
        ),
      );
  }, []);
  return (
    <section className="panel space-y-5 p-5">
      <div>
        <p className="text-xs tracking-[.2em] text-violet-300 uppercase">
          Phase 3C Part 1
        </p>
        <h2 className="mt-1 text-xl font-semibold">
          Deep forecasting infrastructure
        </h2>
        <p className="mt-2 text-sm text-slate-400">
          Architecture and governed readiness only. Deep model training is not
          implemented in this part.
        </p>
      </div>
      {error ? (
        <p role="alert" className="text-red-300">
          {error}
        </p>
      ) : !capability ? (
        <p role="status" className="text-slate-400">
          Loading deep forecasting capabilities…
        </p>
      ) : (
        <>
          <DeepHardwareSummary capability={capability} />
          <DeepModelCapabilityList capability={capability} />
        </>
      )}
    </section>
  );
}

export function DeepReadinessPanel({ preparedId }: { preparedId: string }) {
  const [report, setReport] = useState<DeepForecastReadiness | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    void getDeepReadinessReport(preparedId)
      .then(setReport)
      .catch(() => undefined);
  }, [preparedId]);
  const analyze = () => {
    if (busy) return;
    setBusy(true);
    setError(null);
    void createDeepReadinessReport(preparedId, {
      model_name: "nhits",
      horizon: 30,
      input_size: 120,
      scaler_type: "robust",
      scale_per_series: true,
      target_transform: "none",
      accelerator: "auto",
    })
      .then(setReport)
      .catch((reason) =>
        setError(
          reason instanceof ApiError
            ? reason.message
            : "Readiness analysis failed safely.",
        ),
      )
      .finally(() => setBusy(false));
  };
  return (
    <section className="panel space-y-4 p-5">
      <div className="flex items-center justify-between gap-4">
        <div>
          <h2 className="font-semibold">Deep forecasting readiness</h2>
          <p className="text-sm text-slate-400">
            Validates sequences and covariates without training.
          </p>
        </div>
        {report && <DeepReadinessBadge status={report.readiness_status} />}
      </div>
      {error && (
        <p role="alert" className="text-red-300">
          {error}
        </p>
      )}
      {report && (
        <>
          <div className="grid gap-3 sm:grid-cols-4">
            <Value
              label="Series"
              value={`${report.eligible_series_count}/${report.series_count} eligible`}
            />
            <Value label="Input size" value={report.input_size} />
            <Value label="Horizon" value={report.horizon} />
            <Value
              label="Training windows"
              value={report.sequence_summary.total_training_windows}
            />
          </div>
          <p className="text-sm">
            Covariates: {report.historical_covariate_count} historical ·{" "}
            {report.future_covariate_count} future-known ·{" "}
            {report.static_covariate_count} static
          </p>
          {report.synthetic_data && (
            <p className="text-sm text-amber-200">
              Synthetic demonstration data
            </p>
          )}
          {report.blockers.map((item) => (
            <p className="text-sm text-red-200" key={item}>
              {item}
            </p>
          ))}
          {report.warnings.map((item) => (
            <p className="text-sm text-amber-200" key={item}>
              {item}
            </p>
          ))}
        </>
      )}
      <button
        className="rounded-lg bg-violet-600 px-4 py-2 disabled:opacity-50"
        disabled={busy}
        onClick={analyze}
      >
        {busy ? "Analyzing readiness…" : "Analyze deep readiness"}
      </button>
    </section>
  );
}

function Value({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="font-semibold">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}
