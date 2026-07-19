"use client";

import React from "react";
import { ArrowDownRight, ArrowUpRight, Minus } from "lucide-react";

interface KPICardProps {
  title: string;
  value: string | number;
  variance?: number; // percentage (-10 to 10 etc.)
  status?: "on_track" | "watch" | "critical" | "exceeded" | "unavailable";
  trendDirection?: "up" | "down" | "flat";
  unit?: string;
  className?: string;
}

export function KPICard({
  title,
  value,
  variance,
  status = "on_track",
  trendDirection,
  unit,
  className = "",
}: KPICardProps) {
  const isUnavailable = status === "unavailable";

  const statusColors = {
    on_track: "text-emerald-400 bg-emerald-400/10 border-emerald-400/20",
    watch: "text-amber-400 bg-amber-400/10 border-amber-400/20",
    critical: "text-rose-400 bg-rose-400/10 border-rose-400/20",
    exceeded: "text-blue-400 bg-blue-400/10 border-blue-400/20",
    unavailable: "text-slate-500 bg-slate-800/50 border-slate-700/50",
  };

  const TrendIcon =
    trendDirection === "up"
      ? ArrowUpRight
      : trendDirection === "down"
        ? ArrowDownRight
        : Minus;

  return (
    <div
      className={`panel group relative flex flex-col justify-between overflow-hidden p-6 ${className}`}
    >
      <div className="pointer-events-none absolute inset-0 bg-gradient-to-br from-white/5 to-transparent opacity-0 transition-opacity duration-500 group-hover:opacity-100" />

      <div className="relative z-10 mb-4 flex items-start justify-between">
        <h3 className="text-sm font-medium text-slate-400">{title}</h3>
        <span
          className={`rounded border px-2 py-1 text-xs font-medium ${statusColors[status]}`}
        >
          {status.replace("_", " ").toUpperCase()}
        </span>
      </div>

      <div className="relative z-10">
        {isUnavailable ? (
          <span className="text-2xl font-bold text-slate-500">No Data</span>
        ) : (
          <div className="flex items-baseline gap-1">
            <span className="text-4xl font-bold text-white">{value}</span>
            {unit && <span className="text-sm text-slate-400">{unit}</span>}
          </div>
        )}
      </div>

      {!isUnavailable && variance !== undefined && (
        <div className="relative z-10 mt-4 flex items-center gap-2">
          <TrendIcon
            size={16}
            className={variance >= 0 ? "text-emerald-400" : "text-rose-400"}
          />
          <span
            className={`text-sm font-medium ${variance >= 0 ? "text-emerald-400" : "text-rose-400"}`}
          >
            {Math.abs(variance)}%
          </span>
          <span className="text-xs text-slate-500">vs Target</span>
        </div>
      )}
    </div>
  );
}
