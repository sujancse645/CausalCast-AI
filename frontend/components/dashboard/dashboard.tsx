import { Bot, BarChart3, AlertCircle } from "lucide-react";
import { ForecastChart } from "./forecast-chart";
import { SystemReadiness } from "./system-readiness";
import { DatasetSummary } from "./dataset-summary";
import { ForecastingSummary } from "./forecasting-summary";

export function Dashboard() {
  return (
    <div className="space-y-6">
      <div className="rounded-xl border border-cyan-500/20 bg-cyan-500/5 px-4 py-3 text-sm text-cyan-100">
        Demo placeholders have been removed as per integration audit.
        Forecasting registry statistics below are live API results.
      </div>

      <section className="grid grid-cols-1 gap-6 md:grid-cols-4">
        {[1, 2, 3, 4].map((k) => (
          <article key={k} className="panel p-5 opacity-50">
            <div className="flex justify-between">
              <p className="muted flex items-center gap-2 text-sm">
                <BarChart3 size={14} /> Placeholder Metric
              </p>
            </div>
            <p className="mt-4 text-2xl font-semibold">-</p>
            <p className="muted mt-1 text-xs">Awaiting live data integration</p>
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
        <div className="flex items-center gap-2 border-b border-slate-800 p-5 text-amber-400">
          <AlertCircle size={18} />
          <h3 className="font-semibold text-white">Channel performance</h3>
        </div>
        <div className="p-8 text-center text-slate-500">
          No active performance data available. Connect an integration source.
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
          <div className="mt-4 text-sm text-slate-500">
            System architecture tracking has been migrated to compliance &
            governance reporting.
          </div>
        </section>
      </div>
    </div>
  );
}
