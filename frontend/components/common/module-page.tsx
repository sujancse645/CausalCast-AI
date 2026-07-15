import { ArrowLeft, CheckCircle2, Clock3 } from "lucide-react";
import Link from "next/link";
export function ModulePage({
  title,
  description,
  capabilities,
}: {
  title: string;
  description: string;
  capabilities: string[];
}) {
  return (
    <section className="mx-auto max-w-5xl">
      <Link
        href="/dashboard"
        className="mb-6 inline-flex items-center gap-2 text-sm text-blue-400"
      >
        <ArrowLeft size={16} />
        Return to dashboard
      </Link>
      <p className="text-xs font-semibold tracking-[.2em] text-cyan-400 uppercase">
        Planned module
      </p>
      <h2 className="mt-2 text-3xl font-semibold">{title}</h2>
      <p className="muted mt-3 max-w-2xl leading-7">{description}</p>
      <div className="mt-8 grid gap-5 md:grid-cols-[1.5fr_1fr]">
        <div className="panel p-6">
          <h3 className="font-semibold">Planned capabilities</h3>
          <ul className="mt-4 space-y-3">
            {capabilities.map((x) => (
              <li key={x} className="flex gap-3 text-sm text-slate-300">
                <CheckCircle2 className="text-blue-400" size={18} />
                {x}
              </li>
            ))}
          </ul>
        </div>
        <div className="panel p-6">
          <Clock3 className="text-violet-400" />
          <h3 className="mt-4 font-semibold">Implementation status</h3>
          <p className="muted mt-2 text-sm">
            Foundation ready. No simulated model results are produced in Phase
            1.
          </p>
          <span className="mt-5 inline-block rounded-full bg-violet-500/10 px-3 py-1 text-xs text-violet-300">
            Pending roadmap phase
          </span>
        </div>
      </div>
    </section>
  );
}
