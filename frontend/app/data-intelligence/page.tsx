import { DataIntelligenceWorkspace } from "@/components/data-intelligence/data-intelligence-workspace";
export default function DataIntelligencePage() {
  return (
    <>
      <div className="mb-6">
        <div className="flex flex-wrap items-center gap-3">
          <h2 className="text-2xl font-semibold">Data Intelligence</h2>
          <span className="rounded-full border border-cyan-500/30 bg-cyan-500/10 px-3 py-1 text-xs text-cyan-200">
            Phase 2A — Ingestion
          </span>
        </div>
        <p className="muted mt-2">
          Upload, validate, and manage governed marketing datasets before
          forecasting.
        </p>
      </div>
      <DataIntelligenceWorkspace />
    </>
  );
}
