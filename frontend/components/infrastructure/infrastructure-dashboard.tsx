"use client";

import { useEffect, useState } from "react";
import { getSystemInfo, getHealth } from "@/lib/api";
import {
  Activity,
  Database,
  Server,
  CheckCircle,
  AlertTriangle,
} from "lucide-react";
import type { SystemInfoResponse, HealthResponse } from "@/types/api";

export function InfrastructureDashboard() {
  const [system, setSystem] = useState<SystemInfoResponse | null>(null);
  const [health, setHealth] = useState<HealthResponse | null>(null);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    async function fetchData() {
      try {
        const [sysData, healthData] = await Promise.all([
          getSystemInfo(),
          getHealth(),
        ]);
        setSystem(sysData);
        setHealth(healthData);
      } catch (err) {
        console.error("Failed to load infrastructure data", err);
      } finally {
        setLoading(false);
      }
    }
    fetchData();
    const interval = setInterval(fetchData, 10000);
    return () => clearInterval(interval);
  }, []);

  if (loading && !system) {
    return (
      <div className="p-8 text-center text-slate-400">
        Loading infrastructure data...
      </div>
    );
  }

  const isHealthy = health?.status === "healthy";

  return (
    <div className="space-y-6">
      <div className="grid gap-6 md:grid-cols-2 lg:grid-cols-4">
        {/* API Health */}
        <div className="panel p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-200">API Status</h3>
            {isHealthy ? (
              <CheckCircle className="text-emerald-400" size={20} />
            ) : (
              <AlertTriangle className="text-rose-400" size={20} />
            )}
          </div>
          <p className="mt-2 text-sm text-slate-400">
            {health?.status || "Unknown"}
          </p>
          <div className="mt-4 text-xs text-slate-500">
            Version {system?.application.version || "N/A"}
          </div>
        </div>

        {/* Database */}
        <div className="panel p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-200">Database</h3>
            <Database
              className={
                system?.database.status === "connected"
                  ? "text-emerald-400"
                  : "text-amber-400"
              }
              size={20}
            />
          </div>
          <p className="mt-2 text-sm text-slate-400">
            {system?.database.type || "Unknown"}
          </p>
          <div className="mt-4 text-xs text-slate-500">
            Status: {system?.database.status || "Unknown"}
          </div>
        </div>

        {/* Environment */}
        <div className="panel p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-200">Environment</h3>
            <Server className="text-blue-400" size={20} />
          </div>
          <p className="mt-2 text-sm text-slate-400 capitalize">
            {system?.application.environment || "Development"}
          </p>
          <div className="mt-4 text-xs text-slate-500">
            {system?.application.name || "CausalCast AI"}
          </div>
        </div>

        {/* Observability */}
        <div className="panel p-5">
          <div className="flex items-center justify-between">
            <h3 className="font-semibold text-slate-200">Observability</h3>
            <Activity className="text-purple-400" size={20} />
          </div>
          <p className="mt-2 text-sm text-slate-400">
            Metrics & Traces Enabled
          </p>
          <div className="mt-4 text-xs text-slate-500">
            Prometheus & OpenTelemetry
          </div>
        </div>
      </div>
    </div>
  );
}
