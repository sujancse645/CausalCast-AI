"use client";

import { KPICard } from "@/components/analytics/kpi-card";
import { Download, RefreshCw, Filter, Sparkles } from "lucide-react";
import { useCallback, useEffect, useState } from "react";
import { getDashboards, DashboardResponse } from "@/lib/api";

export default function ExecutiveAnalyticsPage() {
  const [isRefreshing, setIsRefreshing] = useState(false);
  const [showToast, setShowToast] = useState(false);
  const [data, setData] = useState<DashboardResponse[] | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(true);

  const fetchDashboardData = useCallback(async () => {
    try {
      setLoading(true);
      setError(null);
      const res = await getDashboards();
      setData(res);
    } catch (caught: unknown) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Failed to load dashboard data",
      );
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    let active = true;
    getDashboards()
      .then((response) => {
        if (active) setData(response);
      })
      .catch((caught: unknown) => {
        if (active) {
          setError(
            caught instanceof Error
              ? caught.message
              : "Failed to load dashboard data",
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

  const handleRefresh = async () => {
    setIsRefreshing(true);
    await fetchDashboardData();
    setIsRefreshing(false);
  };

  const handleExport = () => {
    setShowToast(true);
    setTimeout(() => setShowToast(false), 3000);
  };

  if (loading) {
    return (
      <div className="flex min-h-[400px] items-center justify-center">
        <RefreshCw className="animate-spin text-slate-400" size={32} />
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

  if (!data || data.length === 0) {
    return (
      <div className="flex min-h-[400px] flex-col items-center justify-center text-slate-400">
        <h3 className="mb-2 text-xl font-bold text-white">
          No Dashboard Data Available
        </h3>
        <p>
          The business intelligence engine has not generated any dashboards yet.
        </p>
        <button
          onClick={handleRefresh}
          className="mt-6 flex items-center rounded-lg bg-slate-800 px-4 py-2 transition-colors hover:bg-slate-700"
        >
          <RefreshCw className="mr-2" size={16} /> Check Again
        </button>
      </div>
    );
  }

  const activeDashboard = data[0];
  const revWidget = activeDashboard.widgets?.find(
    (w) => w.title === "Revenue Performance",
  );
  const revenueValue = revWidget?.configuration.actual_value;
  const revenueVariance = revWidget?.configuration.variance;
  const revenueStatus = revWidget?.configuration.status;
  const hasRevenueValue =
    typeof revenueValue === "number" || typeof revenueValue === "string";
  const hasRevenueStatus =
    revenueStatus === "on_track" ||
    revenueStatus === "watch" ||
    revenueStatus === "critical" ||
    revenueStatus === "exceeded";

  return (
    <div className="animate-in fade-in relative space-y-8 pb-12 duration-700">
      {/* Toast Notification */}
      {showToast && (
        <div className="animate-in slide-in-from-bottom-5 fade-in fixed right-4 bottom-4 z-50 duration-300">
          <div className="flex items-center gap-3 rounded-xl border border-emerald-500/30 bg-emerald-500/10 px-6 py-4 text-emerald-200 shadow-2xl backdrop-blur-md">
            <div className="flex h-8 w-8 items-center justify-center rounded-full bg-emerald-500/20">
              <Download size={16} className="text-emerald-400" />
            </div>
            <div>
              <p className="text-sm font-semibold">Export Successful</p>
              <p className="text-xs text-emerald-400/80">
                Your report is downloading securely.
              </p>
            </div>
          </div>
        </div>
      )}

      {/* Header */}
      <div className="flex flex-col justify-between gap-4 md:flex-row md:items-center">
        <div>
          <div className="mb-2 flex items-center gap-2">
            <span className="rounded border border-blue-500/20 bg-blue-500/10 px-2 py-1 text-xs font-bold tracking-wider text-blue-400 uppercase">
              {activeDashboard.name}
            </span>
          </div>
          <h1 className="bg-gradient-to-r from-white via-slate-200 to-slate-500 bg-clip-text text-4xl font-extrabold text-transparent">
            Executive Analytics
          </h1>
          <p className="mt-2 max-w-xl leading-relaxed text-slate-400">
            {activeDashboard.description ||
              "Real-time C-level KPI intelligence and portfolio performance tracking."}
          </p>
        </div>
        <div className="flex items-center gap-3">
          <button className="group flex items-center rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-2 text-sm font-medium text-white transition-all duration-300 hover:bg-slate-700/50">
            <Filter
              size={16}
              className="mr-2 text-slate-400 transition-colors group-hover:text-white"
            />
            Filters
          </button>
          <button
            className="group flex items-center rounded-lg border border-slate-700 bg-slate-800/50 px-4 py-2 text-sm font-medium text-white transition-all duration-300 hover:bg-slate-700/50"
            onClick={handleRefresh}
            disabled={isRefreshing}
          >
            <RefreshCw
              size={16}
              className={`mr-2 text-slate-400 transition-colors group-hover:text-white ${isRefreshing ? "animate-spin text-white" : ""}`}
            />
            Sync Data
          </button>
          <button
            className="flex items-center rounded-lg bg-gradient-to-r from-blue-600 to-indigo-600 px-5 py-2.5 text-sm font-semibold text-white shadow-[0_0_20px_rgba(37,99,235,0.3)] transition-all duration-300 hover:from-blue-500 hover:to-indigo-500 hover:shadow-[0_0_25px_rgba(37,99,235,0.5)] active:scale-95"
            onClick={handleExport}
          >
            <Download size={16} className="mr-2" />
            Export PDF Report
          </button>
        </div>
      </div>

      {/* KPI Grid */}
      <div className="grid grid-cols-1 gap-6 md:grid-cols-2 xl:grid-cols-4">
        {revWidget && hasRevenueValue && hasRevenueStatus ? (
          <KPICard
            title={revWidget.title}
            value={revenueValue}
            variance={
              typeof revenueVariance === "number" ? revenueVariance : undefined
            }
            status={revenueStatus}
            className="shadow-xl shadow-black/50"
          />
        ) : (
          <KPICard
            title="Revenue Performance"
            value="-"
            status="unavailable"
            className="shadow-xl shadow-black/50"
          />
        )}
        <KPICard
          title="Customer Churn Risk"
          value="-"
          status="unavailable"
          className="shadow-xl shadow-black/50"
        />
        <KPICard
          title="Supply Chain Disruption Index"
          value="-"
          status="unavailable"
          className="shadow-xl shadow-black/50"
        />
        <KPICard
          title="Available Free Cash Flow"
          value="-"
          status="unavailable"
          className="shadow-xl shadow-black/50"
        />
      </div>

      {/* Dashboard Sections */}
      <div className="grid grid-cols-1 gap-6 xl:grid-cols-3">
        {/* Main Chart Area */}
        <div className="group relative flex min-h-[450px] flex-col items-center justify-center overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 backdrop-blur-xl xl:col-span-2">
          <p className="text-slate-500">
            Chart data not configured for this dashboard.
          </p>
        </div>

        {/* AI Recommendations */}
        <div className="relative flex flex-col overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/60 shadow-xl shadow-black/50 backdrop-blur-xl">
          <div className="pointer-events-none absolute top-0 right-0 rounded-full bg-blue-500/10 p-32 blur-[100px]" />

          <div className="z-10 border-b border-slate-800/50 p-6">
            <h3 className="flex items-center gap-2 text-lg font-bold text-white">
              <Sparkles size={20} className="text-indigo-400" />
              Decision Intelligence
            </h3>
            <p className="mt-1 text-sm text-slate-400">
              AI-driven actionable insights
            </p>
          </div>

          <div className="z-10 flex flex-1 flex-col items-center justify-center space-y-4 overflow-y-auto p-6 text-center">
            <p className="text-slate-500">No new recommendations available.</p>
          </div>
        </div>
      </div>
    </div>
  );
}
