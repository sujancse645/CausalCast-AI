import { ArrowLeft, CheckCircle2, Clock3 } from "lucide-react";
import Link from "next/link";
import React from "react";

export function ModulePage({
  title,
  description,
  capabilities,
  icon,
  children,
}: {
  title: string;
  description?: string;
  capabilities?: string[];
  icon?: React.ReactNode;
  children?: React.ReactNode;
}) {
  return (
    <section className="mx-auto max-w-5xl animate-in fade-in slide-in-from-bottom-4 duration-700 ease-out">
      <Link
        href="/dashboard"
        className="mb-8 inline-flex items-center gap-2 text-sm text-slate-400 hover:text-blue-400 transition-colors"
      >
        <ArrowLeft size={16} />
        Return to dashboard
      </Link>
      
      <div className="flex items-center gap-4 mb-4">
        {icon && (
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl bg-gradient-to-br from-slate-800 to-slate-900 border border-slate-700 shadow-xl shadow-black/50">
            {icon}
          </div>
        )}
        <div>
          {!icon && (
            <p className="text-xs font-semibold tracking-[.2em] text-cyan-400 uppercase mb-1">
              Planned module
            </p>
          )}
          <h2 className="text-4xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-white to-slate-400">
            {title}
          </h2>
        </div>
      </div>

      {description && (
        <p className="text-slate-400 mt-4 max-w-2xl leading-relaxed text-lg">
          {description}
        </p>
      )}

      {children && (
        <div className="mt-10">
          {children}
        </div>
      )}

      {capabilities && capabilities.length > 0 && (
        <div className="mt-10 grid gap-6 md:grid-cols-[1.5fr_1fr]">
          <div className="rounded-2xl border border-slate-800 bg-slate-900/50 p-8 backdrop-blur-sm shadow-2xl relative overflow-hidden group">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 group-hover:opacity-100 transition-opacity duration-500" />
            <h3 className="font-semibold text-xl text-white mb-6">Planned capabilities</h3>
            <ul className="space-y-4 relative z-10">
              {capabilities.map((x) => (
                <li key={x} className="flex gap-4 text-slate-300 items-start">
                  <CheckCircle2 className="text-emerald-400 shrink-0 mt-0.5" size={20} />
                  <span className="leading-relaxed">{x}</span>
                </li>
              ))}
            </ul>
          </div>
          
          <div className="rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900/50 to-slate-900/80 p-8 backdrop-blur-sm shadow-2xl flex flex-col justify-center items-center text-center">
            <div className="h-16 w-16 rounded-full bg-violet-500/10 flex items-center justify-center mb-6 border border-violet-500/20">
              <Clock3 className="text-violet-400" size={28} />
            </div>
            <h3 className="font-semibold text-lg text-white">Implementation status</h3>
            <p className="text-slate-400 mt-3 text-sm leading-relaxed">
              Foundation ready. No simulated model results are produced in Phase 1.
            </p>
            <span className="mt-6 inline-block rounded-full bg-violet-500/20 border border-violet-500/30 px-4 py-1.5 text-xs font-medium text-violet-300 tracking-wide">
              Pending roadmap phase
            </span>
          </div>
        </div>
      )}
    </section>
  );
}
