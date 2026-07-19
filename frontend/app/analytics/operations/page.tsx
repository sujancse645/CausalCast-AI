"use client";

import { KPICard } from "@/components/analytics/kpi-card";
import { Search, Filter, Settings, Activity, Cpu } from "lucide-react";
import { useEffect, useState } from "react";
import { getDashboards } from "@/lib/api";

export default function OperationsAnalyticsPage() {
  const [searchTerm, setSearchTerm] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    let active = true;
    getDashboards()
      .catch((caught: unknown) => {
        if (active) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Failed to load operations dashboard",
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

  const fetchDashboardData = async () => {
    try {
      setLoading(true);
      setError(null);
      await getDashboards();
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Failed to load operations dashboard",
      );
    } finally {
      setLoading(false);
    }
  };

  const handleRefresh = async () => {
    await fetchDashboardData();
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
      <div className="rounded-xl border border-rose-500/20 bg-rose-500/10 p-6 text-rose-400">
        <h3 className="mb-2 text-lg font-bold">Error Loading Dashboard</h3>
        <p>{error}</p>
        <button
          onClick={handleRefresh}
          className="mt-4 rounded-lg bg-rose-500/20 px-4 py-2 transition-colors hover:bg-rose-500/30"
        >
          Retry
        </button>
      </div>
    );
  }

  return (
    <div className="animate-in fade-in space-y-8 pb-12 duration-700">
      {/* Header */}
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <h1 className="bg-gradient-to-r from-white via-slate-200 to-slate-500 bg-clip-text text-4xl font-extrabold text-transparent">
            Operations Center
          </h1>
          <p className="mt-2 max-w-xl leading-relaxed text-slate-400">
            Real-time monitoring of service levels, system capacity, and
            automated diagnostic resolution.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="group relative">
            <Search
              className="absolute top-1/2 left-3 -translate-y-1/2 text-slate-400 transition-colors group-focus-within:text-blue-400"
              size={16}
            />
            <input
              type="text"
              placeholder="Search metrics & alerts..."
              className="w-72 rounded-lg border border-slate-700 bg-slate-900/60 py-2.5 pr-4 pl-9 text-sm text-white shadow-lg backdrop-blur-xl transition-all focus:border-blue-500 focus:ring-2 focus:ring-blue-500/20 focus:outline-none"
              value={searchTerm}
              onChange={(e) => setSearchTerm(e.target.value)}
            />
          </div>
          <button className="group rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-2.5 text-sm font-medium text-white shadow-lg transition-all duration-300 hover:bg-slate-700/50">
            <Filter
              size={16}
              className="text-slate-400 transition-colors group-hover:text-white"
            />
          </button>
          <button className="group rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-2.5 text-sm font-medium text-white shadow-lg transition-all duration-300 hover:bg-slate-700/50">
            <Settings
              size={16}
              className="text-slate-400 transition-colors group-hover:text-white"
            />
          </button>
        </div>
      </div>

      {/* Metric Groups */}
      <div className="space-y-10">
        {/* Service Level */}
        <div>
          <div className="mb-6 flex items-center gap-3 border-b border-slate-800/80 pb-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-blue-500/20 bg-blue-500/10">
              <Activity size={18} className="text-blue-400" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white">
              Service Levels
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            <KPICard
              title="Ticket Resolution Time"
              value="-"
              status="unavailable"
              className="shadow-xl shadow-black/40"
            />
            <KPICard
              title="SLA Compliance Rate"
              value="-"
              status="unavailable"
              className="shadow-xl shadow-black/40"
            />
            <KPICard
              title="Escalation Rate"
              value="-"
              status="unavailable"
              className="shadow-xl shadow-black/40"
            />
            <KPICard
              title="Customer Satisfaction"
              value="-"
              status="unavailable"
              className="shadow-xl shadow-black/40"
            />
          </div>
        </div>

        {/* Capacity */}
        <div>
          <div className="mb-6 flex items-center gap-3 border-b border-slate-800/80 pb-3">
            <div className="flex h-8 w-8 items-center justify-center rounded-lg border border-emerald-500/20 bg-emerald-500/10">
              <Cpu size={18} className="text-emerald-400" />
            </div>
            <h2 className="text-2xl font-bold tracking-tight text-white">
              Capacity & Throughput
            </h2>
          </div>
          <div className="grid grid-cols-1 gap-6 md:grid-cols-2 lg:grid-cols-4">
            <KPICard
              title="Server Utilization"
              value="-"
              status="unavailable"
              className="shadow-xl shadow-black/40"
            />
            <KPICard
              title="Processing Backlog"
              value="-"
              status="unavailable"
              className="shadow-xl shadow-black/40"
            />
            <KPICard
              title="Daily Throughput"
              value="-"
              status="unavailable"
              className="shadow-xl shadow-black/40"
            />
            <KPICard
              title="Error Rate"
              value="-"
              status="unavailable"
              className="shadow-xl shadow-black/40"
            />
          </div>
        </div>
      </div>

      {/* Diagnostics Table */}
      <div className="flex min-h-[200px] items-center justify-center overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 shadow-2xl shadow-black/50 backdrop-blur-xl">
        <p className="text-slate-400">
          No active diagnostic incidents configured.
        </p>
      </div>
    </div>
  );
}
