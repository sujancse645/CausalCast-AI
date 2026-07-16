"use client";
import Link from "next/link";
import { useCallback, useEffect, useState } from "react";
import {
  ApiError,
  confirmDatasetSchema,
  getDataset,
  getDatasetSchema,
  getSchemaHistory,
  getSemanticRoles,
  inferDatasetSchema,
  updateColumnMapping,
} from "@/lib/api";
import type { DatasetDetail } from "@/types/dataset";
import type {
  ColumnProfile,
  DatasetSchemaDetail,
  SchemaHistoryItem,
  SemanticRoleDefinition,
} from "@/types/schema-mapping";
import { ColumnMappingTable } from "./column-mapping-table";
import { EvidencePanel } from "./evidence-panel";
import { SchemaReadinessSummary } from "./schema-readiness-summary";
import { SchemaVersionHistory } from "./schema-version-history";
export function SchemaMappingWorkspace({ datasetId }: { datasetId: string }) {
  const [dataset, setDataset] = useState<DatasetDetail | null>(null);
  const [schema, setSchema] = useState<DatasetSchemaDetail | null>(null);
  const [roles, setRoles] = useState<SemanticRoleDefinition[]>([]);
  const [history, setHistory] = useState<SchemaHistoryItem[]>([]);
  const [loading, setLoading] = useState(true);
  const [running, setRunning] = useState(false);
  const [saving, setSaving] = useState<string | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [evidence, setEvidence] = useState<ColumnProfile | null>(null);
  const [confirming, setConfirming] = useState(false);
  const load = useCallback(async () => {
    try {
      const [d, r, h] = await Promise.all([
        getDataset(datasetId),
        getSemanticRoles(),
        getSchemaHistory(datasetId),
      ]);
      setDataset(d);
      setRoles(r.items);
      setHistory(h.items);
      try {
        setSchema(await getDatasetSchema(datasetId));
      } catch (e) {
        if (!(e instanceof ApiError && e.status === 404)) throw e;
      }
      setError(null);
    } catch {
      setError(
        "Schema workspace is unavailable. Retry when the backend is online.",
      );
    } finally {
      setLoading(false);
    }
  }, [datasetId]);
  useEffect(() => {
    // The state updates happen after network promises settle; this starts the external synchronization.
    // eslint-disable-next-line react-hooks/set-state-in-effect
    void load();
  }, [load]);
  const run = async () => {
    setRunning(true);
    setError(null);
    try {
      setSchema(
        await inferDatasetSchema(
          datasetId,
          schema ? "Manual rerun from mapping workspace" : "Initial inference",
        ),
      );
      setHistory((await getSchemaHistory(datasetId)).items);
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Inference failed while offline.",
      );
    } finally {
      setRunning(false);
    }
  };
  const change = async (column: ColumnProfile, role: string) => {
    setSaving(column.id);
    try {
      const result = await updateColumnMapping(datasetId, column.id, {
        semantic_role: role,
        reason: "Local user review",
      });
      setSchema((current) =>
        current
          ? {
              ...current,
              summary: result.summary,
              columns: current.columns.map((c) =>
                c.id === column.id ? result.column : c,
              ),
            }
          : current,
      );
    } catch (e) {
      setError(
        e instanceof ApiError ? e.message : "Mapping could not be saved.",
      );
    } finally {
      setSaving(null);
    }
  };
  const confirm = async () => {
    try {
      await confirmDatasetSchema(datasetId);
      setConfirming(false);
      await load();
    } catch (e) {
      setConfirming(false);
      setError(e instanceof ApiError ? e.message : "Confirmation failed.");
    }
  };
  if (loading) return <p role="status">Loading schema workspace…</p>;
  if (!dataset) return <p role="alert">{error ?? "Dataset was not found."}</p>;
  return (
    <div className="space-y-6">
      <Link href="/data-intelligence" className="text-sm text-blue-400">
        ← Return to dataset library
      </Link>
      <header className="flex flex-wrap items-end justify-between gap-4">
        <div>
          <p className="text-xs tracking-[.2em] text-cyan-400 uppercase">
            Phase 2B · Explainable mapping
          </p>
          <h1 className="mt-2 text-2xl font-semibold">
            {dataset.original_filename}
          </h1>
          <p className="muted text-sm">
            {dataset.id.slice(0, 8)}… · {dataset.row_count} rows ·{" "}
            {dataset.column_count} columns
            {schema ? ` · schema v${schema.schema_version}` : ""}
          </p>
        </div>
        <div className="flex gap-2">
          <button
            disabled={running}
            onClick={() => void run()}
            className="rounded-lg bg-blue-600 px-4 py-2 text-sm"
          >
            {running
              ? "Analyzing…"
              : schema
                ? "Rerun inference"
                : "Run inference"}
          </button>
          {schema && (
            <button
              disabled={schema.summary.blocking_issues.length > 0}
              onClick={() => setConfirming(true)}
              className="rounded-lg border border-emerald-500/40 px-4 py-2 text-sm disabled:opacity-40"
            >
              Confirm mapping
            </button>
          )}
        </div>
      </header>
      {error && (
        <p
          role="alert"
          className="rounded-lg border border-rose-500/30 p-3 text-rose-200"
        >
          {error}
        </p>
      )}
      {!schema ? (
        <section className="panel p-10 text-center">
          <h2 className="text-xl font-semibold">No schema proposal yet</h2>
          <p className="muted mt-2">
            Run deterministic inference to create a reviewable proposal.
          </p>
        </section>
      ) : (
        <>
          <SchemaReadinessSummary summary={schema.summary} />
          <ColumnMappingTable
            columns={schema.columns}
            roles={roles}
            saving={saving}
            onRole={(c, r) => void change(c, r)}
            onEvidence={setEvidence}
          />
          <p className="text-xs text-violet-200">
            Manual overrides are versioned derived metadata. Raw data remains
            unchanged.
          </p>
        </>
      )}
      <SchemaVersionHistory items={history} />
      {evidence && (
        <EvidencePanel column={evidence} onClose={() => setEvidence(null)} />
      )}{" "}
      {confirming && (
        <div
          role="dialog"
          aria-modal="true"
          aria-labelledby="confirm-title"
          className="fixed inset-0 z-50 grid place-items-center bg-black/70 p-4"
        >
          <div className="panel max-w-md p-6">
            <h2 id="confirm-title" className="text-lg font-semibold">
              Confirm schema mapping?
            </h2>
            <p className="muted mt-2 text-sm">
              This approves the derived mapping for future phases. Raw data is
              unchanged.
            </p>
            <div className="mt-5 flex gap-3">
              <button
                onClick={() => void confirm()}
                className="rounded-lg bg-emerald-600 px-4 py-2"
              >
                Confirm
              </button>
              <button onClick={() => setConfirming(false)}>Cancel</button>
            </div>
          </div>
        </div>
      )}
    </div>
  );
}
