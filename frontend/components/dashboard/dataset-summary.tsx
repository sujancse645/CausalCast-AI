"use client";
import { Database } from "lucide-react";
import { useEffect, useState } from "react";
import {
  getDatasetStats,
  getPreparationStats,
  getQualityStats,
  getSchemaStats,
} from "@/lib/api";
import type { PreparationStats } from "@/types/preparation";
import type { DatasetStats } from "@/types/dataset";
import type { SchemaStats } from "@/types/schema-mapping";
import type { QualityStats } from "@/types/quality";
export function DatasetSummary() {
  const [stats, setStats] = useState<DatasetStats | null>(null);
  const [failed, setFailed] = useState(false);
  const [schemaStats, setSchemaStats] = useState<SchemaStats | null>(null);
  const [qualityStats, setQualityStats] = useState<QualityStats | null>(null);
  const [preparationStats, setPreparationStats] =
    useState<PreparationStats | null>(null);
  useEffect(() => {
    let active = true;
    void getDatasetStats()
      .then((value) => {
        if (active) setStats(value);
      })
      .catch(() => {
        if (active) setFailed(true);
      });
    void getSchemaStats()
      .then((value) => {
        if (active) setSchemaStats(value);
      })
      .catch(() => undefined);
    void getQualityStats()
      .then((value) => {
        if (active) setQualityStats(value);
      })
      .catch(() => undefined);
    void getPreparationStats()
      .then((value) => {
        if (active) setPreparationStats(value);
      })
      .catch(() => undefined);
    return () => {
      active = false;
    };
  }, []);
  return (
    <section className="panel p-5">
      <div className="flex items-center gap-2">
        <Database size={18} className="text-cyan-400" />
        <h3 className="font-semibold">Governed datasets</h3>
      </div>
      {failed ? (
        <p className="mt-4 text-sm text-slate-400">
          Dataset summary unavailable.
        </p>
      ) : !stats ? (
        <p role="status" className="mt-4 text-sm text-slate-400">
          Loading dataset summary…
        </p>
      ) : (
        <div className="mt-4 grid gap-3 sm:grid-cols-3">
          <div>
            <p className="text-2xl font-semibold">{stats.active_datasets}</p>
            <p className="muted text-xs">Active datasets</p>
          </div>
          <div>
            <p className="truncate text-sm">
              {stats.latest_filename ?? "No uploads"}
            </p>
            <p className="muted text-xs">Latest dataset</p>
          </div>
          <div>
            <p className="text-sm">
              {stats.latest_upload_at
                ? new Date(stats.latest_upload_at).toLocaleString()
                : "—"}
            </p>
            <p className="muted text-xs">Latest upload</p>
          </div>
        </div>
      )}
      {schemaStats && (
        <div className="mt-5 grid gap-3 border-t border-slate-800 pt-4 sm:grid-cols-3">
          <div>
            <p className="text-xl font-semibold">
              {schemaStats.awaiting_review}
            </p>
            <p className="muted text-xs">Awaiting schema review</p>
          </div>
          <div>
            <p className="text-xl font-semibold">
              {schemaStats.confirmed_schemas}
            </p>
            <p className="muted text-xs">Confirmed schemas</p>
          </div>
          <div>
            <p className="text-xl font-semibold">
              {schemaStats.unresolved_columns}
            </p>
            <p className="muted text-xs">Unresolved columns</p>
          </div>
        </div>
      )}
      {qualityStats && (
        <div className="mt-5 grid gap-3 border-t border-slate-800 pt-4 sm:grid-cols-3">
          <div>
            <p className="text-xl font-semibold">
              {qualityStats.datasets_not_analyzed}
            </p>
            <p className="muted text-xs">Awaiting quality analysis</p>
          </div>
          <div>
            <p className="text-xl font-semibold">
              {qualityStats.blocked_datasets}
            </p>
            <p className="muted text-xs">Blocked datasets</p>
          </div>
          <div>
            <p className="text-xl font-semibold">
              {qualityStats.quality_ready}
            </p>
            <p className="muted text-xs">Quality-ready datasets</p>
          </div>
          <div>
            <p className="text-xl font-semibold">
              {qualityStats.average_quality_score ?? "—"}
            </p>
            <p className="muted text-xs">Average quality score</p>
          </div>
          <div>
            <p className="text-xl font-semibold">
              {qualityStats.total_blockers}
            </p>
            <p className="muted text-xs">Total blockers</p>
          </div>
        </div>
      )}
      {preparationStats && (
        <div className="mt-5 grid gap-3 border-t border-slate-800 pt-4 sm:grid-cols-4">
          <div>
            <p className="text-xl font-semibold">
              {preparationStats.datasets_awaiting_preparation}
            </p>
            <p className="muted text-xs">Awaiting preparation</p>
          </div>
          <div>
            <p className="text-xl font-semibold">
              {preparationStats.total_prepared_datasets}
            </p>
            <p className="muted text-xs">Prepared versions</p>
          </div>
          <div>
            <p className="text-xl font-semibold">
              {preparationStats.model_ready_datasets}
            </p>
            <p className="muted text-xs">Model-ready artifacts</p>
          </div>
          <div>
            <p className="text-xl font-semibold">
              {preparationStats.average_feature_count ?? "—"}
            </p>
            <p className="muted text-xs">Average features</p>
          </div>
        </div>
      )}
    </section>
  );
}
