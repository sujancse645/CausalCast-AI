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
    <section className="animate-in fade-in slide-in-from-bottom-4 mx-auto max-w-5xl duration-700 ease-out">
      <Link
        href="/dashboard"
        className="mb-8 inline-flex items-center gap-2 text-sm text-slate-400 transition-colors hover:text-blue-400"
      >
        <ArrowLeft size={16} />
        Return to dashboard
      </Link>

      <div className="mb-4 flex items-center gap-4">
        {icon && (
          <div className="flex h-14 w-14 items-center justify-center rounded-2xl border border-slate-700 bg-gradient-to-br from-slate-800 to-slate-900 shadow-xl shadow-black/50">
            {icon}
          </div>
        )}
        <div>
          {!icon && (
            <p className="mb-1 text-xs font-semibold tracking-[.2em] text-cyan-400 uppercase">
              Planned module
            </p>
          )}
          <h2 className="bg-gradient-to-r from-white to-slate-400 bg-clip-text text-4xl font-bold text-transparent">
            {title}
          </h2>
        </div>
      </div>

      {description && (
        <p className="mt-4 max-w-2xl text-lg leading-relaxed text-slate-400">
          {description}
        </p>
      )}

      {children && <div className="mt-10">{children}</div>}

      {capabilities && capabilities.length > 0 && (
        <div className="mt-10 grid gap-6 md:grid-cols-[1.5fr_1fr]">
          <div className="group relative overflow-hidden rounded-2xl border border-slate-800 bg-slate-900/50 p-8 shadow-2xl backdrop-blur-sm">
            <div className="absolute inset-0 bg-gradient-to-br from-blue-500/5 to-purple-500/5 opacity-0 transition-opacity duration-500 group-hover:opacity-100" />
            <h3 className="mb-6 text-xl font-semibold text-white">
              Planned capabilities
            </h3>
            <ul className="relative z-10 space-y-4">
              {capabilities.map((x) => (
                <li key={x} className="flex items-start gap-4 text-slate-300">
                  <CheckCircle2
                    className="mt-0.5 shrink-0 text-emerald-400"
                    size={20}
                  />
                  <span className="leading-relaxed">{x}</span>
                </li>
              ))}
            </ul>
          </div>

          <div className="flex flex-col items-center justify-center rounded-2xl border border-slate-800 bg-gradient-to-b from-slate-900/50 to-slate-900/80 p-8 text-center shadow-2xl backdrop-blur-sm">
            <div className="mb-6 flex h-16 w-16 items-center justify-center rounded-full border border-violet-500/20 bg-violet-500/10">
              <Clock3 className="text-violet-400" size={28} />
            </div>
            <h3 className="text-lg font-semibold text-white">
              Implementation status
            </h3>
            <p className="mt-3 text-sm leading-relaxed text-slate-400">
              Foundation ready. No simulated model results are produced in Phase
              1.
            </p>
            <span className="mt-6 inline-block rounded-full border border-violet-500/30 bg-violet-500/20 px-4 py-1.5 text-xs font-medium tracking-wide text-violet-300">
              Pending roadmap phase
            </span>
          </div>
        </div>
      )}
    </section>
  );
}
