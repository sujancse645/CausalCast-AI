"use client";

import {
  Activity,
  AlertTriangle,
  Search,
  GitBranch,
  Lightbulb,
} from "lucide-react";
import React, { useState, useEffect } from "react";
import { getExplainabilitySummary, ExplainabilitySummary } from "@/lib/api";

export function ExplainabilityDashboard() {
  const [data, setData] = useState<ExplainabilitySummary | null>(null);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);

  useEffect(() => {
    let active = true;
    getExplainabilitySummary()
      .then((response) => {
        if (active) setData(response);
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Failed to load explainability data",
          );
        }
      })
      .finally(() => {
        if (active) setLoading(false);
      });
    return () => {
      active = false;
    };
  }, []);

  const fetchData = async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getExplainabilitySummary();
      setData(res);
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Failed to load explainability data",
      );
    } finally {
      setLoading(false);
    }
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <Activity className="animate-pulse text-slate-400" size={32} />
      </div>
    );
  }

  if (error) {
    return (
      <div className="flex min-h-[300px] flex-col items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/60 p-6 backdrop-blur-xl">
        <AlertTriangle className="mb-4 text-rose-400" size={48} />
        <h3 className="mb-2 text-xl font-bold text-white">
          Explainability Service Unavailable
        </h3>
        <p className="mb-4 text-slate-400">{error}</p>
        <button
          onClick={fetchData}
          className="rounded-lg bg-slate-800 px-4 py-2 transition-colors hover:bg-slate-700"
        >
          Retry Connection
        </button>
      </div>
    );
  }

  if (!data) {
    return (
      <div className="flex min-h-[300px] flex-col items-center justify-center rounded-2xl border border-slate-800 bg-slate-900/60 p-6 text-slate-400 backdrop-blur-xl">
        <h3 className="mb-2 text-xl font-bold text-white">
          No Explainability Data
        </h3>
        <p>
          Run a deep forecast to generate SHAP values and diagnostic artifacts.
        </p>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in slide-in-from-bottom-4 space-y-8 duration-700 ease-out">
      {/* Top Stats */}
      <div className="grid gap-6 md:grid-cols-4">
        {[
          {
            label: "Global Explanations",
            value: data.global_explanations_count ?? "-",
            icon: <Activity size={20} className="text-blue-400" />,
          },
          {
            label: "Local SHAP Runs",
            value: data.local_shap_runs ?? "-",
            icon: <Search size={20} className="text-emerald-400" />,
          },
          {
            label: "Detected Anomalies",
            value: data.detected_anomalies ?? "-",
            icon: <AlertTriangle size={20} className="text-amber-400" />,
          },
          {
            label: "Active Scenarios",
            value: data.active_scenarios ?? "-",
            icon: <GitBranch size={20} className="text-violet-400" />,
          },
        ].map((stat, i) => (
          <div
            key={i}
            className="panel group relative flex flex-col overflow-hidden p-6 shadow-xl shadow-black/40"
          >
            <div className="absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
            <div className="relative z-10 mb-4 flex items-start justify-between">
              <span className="font-medium text-slate-400">{stat.label}</span>
              {stat.icon}
            </div>
            <span className="relative z-10 text-4xl font-bold text-white">
              {stat.value}
            </span>
          </div>
        ))}
      </div>

      <div className="grid gap-6 md:grid-cols-[2fr_1fr]">
        {/* Main Content Area */}
        <div className="panel min-h-[400px] p-6 shadow-xl shadow-black/40">
          <div className="mb-6 flex items-center gap-3">
            <Lightbulb className="text-amber-400" size={24} />
            <h2 className="text-xl font-semibold">Prediction Explainer</h2>
          </div>

          <div className="flex h-64 flex-col items-center justify-center rounded-xl border border-slate-700/50 bg-slate-800/50 p-6 text-center">
            <Search className="mb-4 text-slate-500" size={48} />
            <p className="mb-2 font-medium text-slate-300">
              Select a Prediction
            </p>
            <p className="max-w-sm text-sm text-slate-500">
              Choose a specific forecast point to visualize SHAP values,
              temporal attention, and counterfactuals.
            </p>
          </div>
        </div>

        {/* Diagnostics Panel */}
        <div className="space-y-6">
          <div className="panel p-6 shadow-xl shadow-black/40">
            <h3 className="mb-4 text-lg font-semibold">Diagnostics Health</h3>
            <div className="flex items-center justify-center p-8 text-sm text-slate-500">
              No recent diagnostic anomalies detected.
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
