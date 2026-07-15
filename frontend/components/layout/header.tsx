"use client";
import { Bell, CircleUserRound, RefreshCw } from "lucide-react";
import { usePathname } from "next/navigation";
import { useSystemStatus } from "@/hooks/use-system-status";

const titles: Record<string, string> = {
  "/dashboard": "Executive Dashboard",
  "/data-intelligence": "Data Intelligence",
  "/forecasts": "Revenue Forecasts",
  "/causal-intelligence": "Causal Intelligence",
  "/scenario-lab": "Scenario Lab",
  "/budget-optimizer": "Budget Optimizer",
  "/copilot": "AI Growth Copilot",
  "/trust-center": "Model Trust Center",
};
export function Header() {
  const path = usePathname();
  const { state, retry } = useSystemStatus();
  return (
    <header className="flex min-h-20 items-center justify-between gap-3 border-b border-slate-800 px-5 md:px-8">
      <div className="ml-12 md:ml-0">
        <p className="text-xs text-slate-500">CausalCast command center</p>
        <h1 className="text-lg font-semibold">
          {titles[path] ?? "CausalCast AI"}
        </h1>
      </div>
      <div className="flex items-center gap-2">
        <span className="hidden rounded-full border border-slate-700 px-3 py-1 text-xs text-slate-400 sm:block">
          Development
        </span>
        <button
          onClick={() => void retry()}
          aria-label="Retry API connection"
          className="flex items-center gap-2 rounded-full border border-slate-700 px-3 py-1 text-xs"
        >
          <span
            className={`h-2 w-2 rounded-full ${state === "connected" ? "bg-emerald-400" : state === "checking" ? "animate-pulse bg-amber-300" : "bg-rose-400"}`}
          />
          <span className="hidden sm:inline">API {state}</span>
          {state === "unavailable" && <RefreshCw size={12} />}
        </button>
        <button
          aria-label="Notifications"
          className="rounded-lg p-2 text-slate-400"
        >
          <Bell size={19} />
        </button>
        <button
          aria-label="User profile"
          className="rounded-lg p-2 text-slate-400"
        >
          <CircleUserRound size={21} />
        </button>
      </div>
    </header>
  );
}
