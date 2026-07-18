"use client";

import { useEffect, useState } from "react";
import { ApiError, getDeepExperiment } from "@/lib/api";
import type { DeepTrainingExperiment } from "@/types/deep-training";

export function DeepTrainingDetail({ identifier }: { identifier: string }) {
  const [experiment, setExperiment] = useState<DeepTrainingExperiment | null>(
    null,
  );
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    void getDeepExperiment(identifier)
      .then(setExperiment)
      .catch((reason: unknown) =>
        setError(
          reason instanceof ApiError
            ? reason.message
            : "Experiment service is offline.",
        ),
      );
  }, [identifier]);
  if (error)
    return (
      <p role="alert" className="text-red-300">
        {error}
      </p>
    );
  if (!experiment) return <p role="status">Loading training details…</p>;
  return (
    <div className="space-y-6">
      <header>
        <p className="text-xs tracking-[.2em] text-violet-300 uppercase">
          N-HiTS experiment
        </p>
        <h1 className="text-2xl font-semibold">{experiment.model_run_id}</h1>
      </header>
      <section className="panel grid gap-4 p-5 sm:grid-cols-4">
        <Value label="Status" value={experiment.status} />
        <Value
          label="Hardware"
          value={experiment.selected_accelerator.toUpperCase()}
        />
        <Value label="Training steps" value={experiment.max_steps} />
        <Value
          label="Duration"
          value={`${(experiment.training_duration_ms / 1000).toFixed(1)}s`}
        />
      </section>
      <section className="panel grid gap-4 p-5 sm:grid-cols-3">
        <Value label="MAE" value={format(experiment.metrics?.mae)} />
        <Value label="RMSE" value={format(experiment.metrics?.rmse)} />
        <Value label="WAPE" value={format(experiment.metrics?.wape)} />
      </section>
      <section className="panel space-y-2 p-5">
        <h2 className="font-semibold">Checkpoint</h2>
        <p>
          {experiment.checkpoint_available
            ? "Available and checksummed"
            : "Unavailable"}
        </p>
        {experiment.checkpoint_checksum && (
          <code className="text-xs break-all">
            {experiment.checkpoint_checksum}
          </code>
        )}
      </section>
    </div>
  );
}

function format(value: number | null | undefined) {
  return value == null ? "—" : value.toFixed(4);
}
function Value({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="font-semibold capitalize">{value}</p>
      <p className="text-xs text-slate-500">{label}</p>
    </div>
  );
}
