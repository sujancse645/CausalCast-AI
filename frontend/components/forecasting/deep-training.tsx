"use client";

import { useEffect, useMemo, useState } from "react";
import { ApiError, getDeepExperiments, trainNHiTS } from "@/lib/api";
import type { DeepTrainingExperiment } from "@/types/deep-training";

export function DeepTrainingWorkspace() {
  const [preparedId, setPreparedId] = useState("");
  const [items, setItems] = useState<DeepTrainingExperiment[]>([]);
  const [query, setQuery] = useState("");
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const refresh = () =>
    getDeepExperiments()
      .then((response) => setItems(response.items))
      .catch((reason: unknown) =>
        setError(
          reason instanceof ApiError
            ? reason.message
            : "Training service is offline.",
        ),
      );

  useEffect(() => {
    void refresh();
  }, []);

  const visible = useMemo(
    () =>
      items.filter((item) =>
        `${item.model_name} ${item.status} ${item.prepared_dataset_id}`
          .toLowerCase()
          .includes(query.toLowerCase()),
      ),
    [items, query],
  );

  const train = () => {
    if (!preparedId || busy) return;
    setBusy(true);
    setError(null);
    void trainNHiTS({
      prepared_dataset_id: preparedId,
      configuration: {
        forecast_horizon: 30,
        input_size: 120,
        max_steps: 1000,
        random_seed: 42,
        accelerator: "auto",
      },
    })
      .then((experiment) => setItems((current) => [experiment, ...current]))
      .catch((reason: unknown) =>
        setError(
          reason instanceof ApiError
            ? reason.message
            : "N-HiTS training failed safely.",
        ),
      )
      .finally(() => setBusy(false));
  };

  return (
    <div className="space-y-6">
      <section className="panel space-y-4 p-5">
        <div>
          <p className="text-xs tracking-[.2em] text-violet-300 uppercase">
            Phase 3C Part 2A
          </p>
          <h1 className="mt-1 text-2xl font-semibold">N-HiTS training</h1>
          <p className="mt-2 text-sm text-slate-400">
            Trains only from a checksum-verified, deep-ready prepared dataset.
            Final test rows remain untouched.
          </p>
        </div>
        <label className="block text-sm">
          Prepared dataset UUID
          <input
            className="mt-1 w-full rounded-lg border border-slate-700 bg-slate-950 px-3 py-2"
            value={preparedId}
            onChange={(event) => setPreparedId(event.target.value)}
          />
        </label>
        <button
          className="rounded-lg bg-violet-600 px-4 py-2 disabled:opacity-50"
          disabled={!preparedId || busy}
          onClick={train}
        >
          {busy ? "Training N-HiTS…" : "Start governed training"}
        </button>
        {error && (
          <p className="text-red-300" role="alert">
            {error}
          </p>
        )}
      </section>
      <section className="panel space-y-4 p-5">
        <div className="flex items-center justify-between gap-4">
          <h2 className="text-xl font-semibold">Deep experiments</h2>
          <input
            aria-label="Search experiments"
            className="rounded-lg border border-slate-700 bg-slate-950 px-3 py-2 text-sm"
            placeholder="Search"
            value={query}
            onChange={(event) => setQuery(event.target.value)}
          />
        </div>
        {!items.length && !error ? (
          <p className="text-sm text-slate-400" role="status">
            No deep training experiments yet.
          </p>
        ) : (
          <div className="overflow-x-auto">
            <table className="w-full text-left text-sm">
              <thead>
                <tr>
                  <th>Model</th>
                  <th>Status</th>
                  <th>Hardware</th>
                  <th>MAE</th>
                  <th>Duration</th>
                  <th>Checkpoint</th>
                </tr>
              </thead>
              <tbody>
                {visible.map((item) => (
                  <tr
                    key={item.model_run_id}
                    className="border-t border-slate-800"
                  >
                    <td className="py-3">{item.model_name.toUpperCase()}</td>
                    <td>{item.status}</td>
                    <td>{item.selected_accelerator.toUpperCase()}</td>
                    <td>{item.metrics?.mae?.toFixed(4) ?? "—"}</td>
                    <td>{(item.training_duration_ms / 1000).toFixed(1)}s</td>
                    <td>{item.checkpoint_available ? "Saved" : "—"}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </section>
    </div>
  );
}
