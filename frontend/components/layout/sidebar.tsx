"use client";

import {
  Activity,
  BarChart3,
  Bot,
  Database,
  Gauge,
  Menu,
  Network,
  ShieldCheck,
  SlidersHorizontal,
  X,
} from "lucide-react";
import Link from "next/link";
import { usePathname } from "next/navigation";
import { useState } from "react";

const items = [
  ["Dashboard", "/dashboard", Gauge],
  ["Data Intelligence", "/data-intelligence", Database],
  ["Baseline Forecasting", "/forecasting", BarChart3],
  ["Causal Intelligence", "/causal-intelligence", Network],
  ["Scenario Lab", "/scenario-lab", Activity],
  ["Budget Optimizer", "/budget-optimizer", SlidersHorizontal],
  ["AI Growth Copilot", "/copilot", Bot],
  ["Model Trust Center", "/trust-center", ShieldCheck],
] as const;

function Navigation({ close }: { close?: () => void }) {
  const pathname = usePathname();
  return (
    <nav aria-label="Primary navigation" className="mt-8 space-y-1">
      {items.map(([label, href, Icon]) => (
        <Link
          key={href}
          href={href}
          onClick={close}
          aria-current={pathname === href ? "page" : undefined}
          className={`flex items-center gap-3 rounded-xl px-3 py-3 text-sm ${pathname === href ? "border border-blue-500/30 bg-blue-500/15 text-white" : "text-slate-400 hover:bg-white/5 hover:text-white"}`}
        >
          <Icon size={18} />
          {label}
        </Link>
      ))}
    </nav>
  );
}

export function Sidebar() {
  const [open, setOpen] = useState(false);
  return (
    <>
      <button
        className="mobile-toggle fixed top-4 left-4 z-40 hidden rounded-lg border border-slate-700 bg-slate-900 p-2"
        aria-label="Open navigation menu"
        onClick={() => setOpen(true)}
      >
        <Menu size={20} />
      </button>
      <aside className="desktop-sidebar fixed inset-y-0 left-0 z-30 w-64 border-r border-slate-800 bg-[#081323] p-5">
        <Brand />
        <Navigation />
        <PhaseBadge />
      </aside>
      {open && (
        <div
          className="fixed inset-0 z-50 bg-black/70"
          onClick={() => setOpen(false)}
        >
          <aside
            className="h-full w-72 bg-[#081323] p-5"
            onClick={(e) => e.stopPropagation()}
          >
            <button
              className="float-right p-2"
              aria-label="Close navigation menu"
              onClick={() => setOpen(false)}
            >
              <X />
            </button>
            <Brand />
            <Navigation close={() => setOpen(false)} />
            <PhaseBadge />
          </aside>
        </div>
      )}
    </>
  );
}
function Brand() {
  return (
    <div className="flex items-center gap-3">
      <span className="grid h-10 w-10 place-items-center rounded-xl bg-blue-600">
        <Activity />
      </span>
      <div>
        <strong>CausalCast AI</strong>
        <div className="text-xs text-slate-500">Decision intelligence</div>
      </div>
    </div>
  );
}
function PhaseBadge() {
  return (
    <div className="absolute right-5 bottom-6 left-5 rounded-xl border border-violet-500/25 bg-violet-500/10 p-3 text-xs text-violet-200">
      Phase 3A · Baseline forecasting
    </div>
  );
}
