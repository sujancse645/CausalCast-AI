"use client";
import {
  AlertCircle,
  CheckCircle2,
  LoaderCircle,
  RefreshCw,
} from "lucide-react";
import { useSystemStatus } from "@/hooks/use-system-status";
export function SystemReadiness() {
  const { state, system, retry } = useSystemStatus();
  const backend =
    state === "connected"
      ? "Operational"
      : state === "checking"
        ? "Checking"
        : "Unavailable";
  const rows = [
    ["Frontend", "Operational"],
    ["Backend", backend],
    [
      "Database",
      system?.database.status ??
        (state === "checking" ? "Checking" : "Unavailable"),
    ],
    [
      "Data Ingestion",
      system?.modules.data_intelligence === "ingestion_ready"
        ? "Operational"
        : "Planned",
    ],
    ["Forecasting Engine", "Planned"],
    ["Causal Engine", "Planned"],
    ["Scenario Engine", "Planned"],
    ["RAG Copilot", "Planned"],
  ];
  return (
    <section className="panel p-5">
      <div className="flex items-center justify-between">
        <h3 className="font-semibold">System readiness</h3>
        {state === "unavailable" && (
          <button
            onClick={() => void retry()}
            className="flex items-center gap-1 text-xs text-blue-400"
          >
            <RefreshCw size={13} />
            Retry
          </button>
        )}
      </div>
      {state === "checking" && (
        <p className="mt-2 flex items-center gap-2 text-xs text-slate-400">
          <LoaderCircle className="animate-spin" size={14} />
          Checking API connectivity…
        </p>
      )}
      {state === "unavailable" && (
        <p role="alert" className="mt-2 flex gap-2 text-xs text-rose-300">
          <AlertCircle size={14} />
          Backend unavailable. Dashboard remains usable.
        </p>
      )}
      <div className="mt-4 space-y-3">
        {rows.map(([name, status]) => (
          <div
            key={name}
            className="flex items-center justify-between border-b border-slate-800 pb-2 text-sm"
          >
            <span className="text-slate-400">{name}</span>
            <span className="flex items-center gap-2 text-xs">
              <CheckCircle2
                size={13}
                className={
                  status === "Operational" || status === "connected"
                    ? "text-emerald-400"
                    : "text-slate-600"
                }
              />
              {status}
            </span>
          </div>
        ))}
      </div>
    </section>
  );
}
