import { Bot, Check, Clock3, TrendingUp } from "lucide-react";
import { channels, kpis, phases } from "@/lib/demo-data";
import { ForecastChart } from "./forecast-chart";
import { SystemReadiness } from "./system-readiness";
import { DatasetSummary } from "./dataset-summary";
import { ForecastingSummary } from "./forecasting-summary";
export function Dashboard() {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 px-4 py-3 text-sm text-cyan-100">
        Demo KPI cards remain illustrative. Forecasting registry statistics
        below are live API results.
      </div>
      <section className="grid-auto">
        {kpis.map((k, i) => (
          <article key={k.label} className="panel p-5">
            <div className="flex justify-between">
              <p className="muted text-sm">{k.label}</p>
              <TrendingUp
                size={17}
                className={i === 3 ? "text-violet-400" : "text-blue-400"}
              />
            </div>
            <p className="mt-4 text-2xl font-semibold">{k.value}</p>
            <p className="muted mt-1 text-xs">{k.detail}</p>
          </article>
        ))}
      </section>
      <DatasetSummary />
      <ForecastingSummary />
      <div className="grid gap-6 xl:grid-cols-[1.7fr_1fr]">
        <ForecastChart />
        <SystemReadiness />
      </div>
      <section className="panel overflow-hidden">
        <div className="border-b border-slate-800 p-5">
          <h3 className="font-semibold">Channel performance</h3>
          <p className="muted text-xs">Demo interface values only</p>
        </div>
        <div className="overflow-x-auto">
          <table className="w-full min-w-[600px] text-left text-sm">
            <thead className="text-xs text-slate-500">
              <tr>
                {["Channel", "Spend", "Revenue", "ROAS", "Status"].map((x) => (
                  <th key={x} className="px-5 py-3 font-medium">
                    {x}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {channels.map((c) => (
                <tr key={c.name} className="border-t border-slate-800">
                  <td className="px-5 py-4 font-medium">{c.name}</td>
                  <td className="px-5 text-slate-400">{c.spend}</td>
                  <td className="px-5">{c.revenue}</td>
                  <td className="px-5">{c.roas}</td>
                  <td className="px-5">
                    <span className="rounded-full bg-blue-500/10 px-2 py-1 text-xs text-blue-300">
                      {c.status}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </section>
      <div className="grid gap-6 lg:grid-cols-2">
        <section className="panel p-6">
          <Bot className="text-violet-400" />
          <h3 className="mt-4 font-semibold">AI recommendation workspace</h3>
          <p className="muted mt-2 text-sm leading-6">
            Budget optimization recommendations will appear after forecasting
            and simulation modules are connected.
          </p>
        </section>
        <section className="panel p-6">
          <h3 className="font-semibold">Architecture progress</h3>
          <div className="mt-4 grid gap-3 sm:grid-cols-2">
            {phases.map((p, i) => (
              <div key={p} className="flex items-center gap-3 text-sm">
                {i === 0 ? (
                  <Check size={16} className="text-emerald-400" />
                ) : (
                  <Clock3 size={16} className="text-slate-600" />
                )}
                <span>
                  <span className="text-slate-500">Phase {i + 1}</span> — {p}
                  <small className="block text-slate-600">
                    {i === 0 ? "Complete" : "Pending"}
                  </small>
                </span>
              </div>
            ))}
          </div>
        </section>
      </div>
    </div>
  );
}
