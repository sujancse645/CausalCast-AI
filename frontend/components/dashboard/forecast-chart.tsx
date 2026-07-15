"use client";
import {
  Area,
  CartesianGrid,
  ComposedChart,
  Line,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";
import { forecastData } from "@/lib/demo-data";
export function ForecastChart() {
  return (
    <section className="panel p-5 md:p-6" aria-labelledby="forecast-heading">
      <div className="flex justify-between">
        <div>
          <h3 id="forecast-heading" className="font-semibold">
            Revenue outlook
          </h3>
          <p className="muted mt-1 text-xs">
            Demo historical and forecast series with uncertainty interval,
            values in $K.
          </p>
        </div>
        <span className="text-xs text-cyan-400">DEMO DATA</span>
      </div>
      <div
        className="mt-5 h-72"
        role="img"
        aria-label="Demo revenue chart showing historical revenue and an increasing forecast with widening uncertainty"
      >
        <ResponsiveContainer width="100%" height="100%">
          <ComposedChart data={forecastData}>
            <defs>
              <linearGradient id="range" x1="0" y1="0" x2="0" y2="1">
                <stop offset="5%" stopColor="#3b82f6" stopOpacity={0.25} />
                <stop offset="95%" stopColor="#3b82f6" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="#22334d" vertical={false} />
            <XAxis dataKey="period" stroke="#64748b" />
            <YAxis stroke="#64748b" />
            <Tooltip
              contentStyle={{
                background: "#0d192c",
                border: "1px solid #22334d",
              }}
            />
            <Area
              type="monotone"
              dataKey="high"
              stroke="none"
              fill="url(#range)"
            />
            <Line
              type="monotone"
              dataKey="low"
              stroke="#475569"
              strokeDasharray="4 4"
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="historical"
              stroke="#e2e8f0"
              strokeWidth={2}
              dot={false}
            />
            <Line
              type="monotone"
              dataKey="forecast"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={false}
            />
          </ComposedChart>
        </ResponsiveContainer>
      </div>
    </section>
  );
}
