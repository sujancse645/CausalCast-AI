"use client";
import Link from "next/link";
import { useEffect, useState } from "react";
import {
  ApiError,
  getPreparation,
  getPreparationDownloadUrl,
  getPreparationFeatures,
  getPreparationPreview,
  getPreparationSplits,
} from "@/lib/api";
import type {
  PreparedFeature,
  PreparationPreview,
  PreparationResponse,
  SplitDefinition,
} from "@/types/preparation";
export function PreparationDetail({
  datasetId,
  preparedId,
}: {
  datasetId: string;
  preparedId: string;
}) {
  const [item, setItem] = useState<PreparationResponse | null>(null),
    [preview, setPreview] = useState<PreparationPreview | null>(null),
    [features, setFeatures] = useState<PreparedFeature[]>([]),
    [splits, setSplits] = useState<SplitDefinition[]>([]),
    [error, setError] = useState<string | null>(null);
  useEffect(() => {
    void Promise.all([
      getPreparation(preparedId),
      getPreparationPreview(preparedId),
      getPreparationFeatures(preparedId),
      getPreparationSplits(preparedId),
    ])
      .then(([a, b, c, d]) => {
        setItem(a);
        setPreview(b);
        setFeatures(c.items);
        setSplits(d.splits);
      })
      .catch((e) =>
        setError(
          e instanceof ApiError ? e.message : "Preparation service is offline.",
        ),
      );
  }, [preparedId]);
  if (error) return <p role="alert">{error}</p>;
  if (!item) return <p role="status">Loading prepared dataset…</p>;
  return (
    <div className="space-y-6">
      <Link
        className="text-blue-400"
        href={`/data-intelligence/${datasetId}/prepare`}
      >
        ← Preparation workspace
      </Link>
      <header>
        <p className="text-xs tracking-[.2em] text-cyan-400 uppercase">
          Prepared artifact · Version {item.preparation_version}
        </p>
        <h1 className="mt-2 text-2xl font-semibold">
          Model-ready dataset review
        </h1>
        <p className="muted">
          Prepared artifact derived from immutable raw data.
        </p>
      </header>
      <section className="panel grid gap-4 p-5 sm:grid-cols-4">
        <Stat l="Rows" v={item.row_count} />
        <Stat l="Features" v={item.feature_count} />
        <Stat l="Frequency" v={item.frequency} />
        <Stat l="Status" v={item.readiness_status} />
        <a className="text-cyan-300" href={getPreparationDownloadUrl(item.id)}>
          Download CSV
        </a>
        {item.readiness_status === "model_ready" && (
          <Link
            className="rounded-lg bg-blue-600 px-3 py-2 text-center text-white"
            href={`/data-intelligence/${datasetId}/preparations/${item.id}/forecast`}
          >
            Run baseline forecast
          </Link>
        )}
      </section>
      <section className="panel overflow-x-auto p-5">
        <h2 className="font-semibold">Chronological splits</h2>
        <table className="mt-3 w-full text-sm">
          <tbody>
            {splits.map((x) => (
              <tr key={x.name}>
                <td className="capitalize">{x.name}</td>
                <td>{x.start}</td>
                <td>{x.end}</td>
                <td>{x.rows} rows</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      <section className="panel overflow-x-auto p-5">
        <h2 className="font-semibold">Feature catalog and lineage</h2>
        <table className="mt-3 w-full min-w-[700px] text-sm">
          <thead>
            <tr>
              <th>Feature</th>
              <th>Type</th>
              <th>Availability</th>
              <th>Leakage</th>
              <th>Included</th>
            </tr>
          </thead>
          <tbody>
            {features.map((x) => (
              <tr key={x.id} className="border-t border-slate-800">
                <td>{x.feature_name}</td>
                <td>{x.feature_type}</td>
                <td>{x.availability_type}</td>
                <td>{x.leakage_risk}</td>
                <td>{x.included ? "Yes" : "No"}</td>
              </tr>
            ))}
          </tbody>
        </table>
      </section>
      {preview && (
        <section className="panel overflow-x-auto p-5">
          <h2 className="font-semibold">Bounded preview</h2>
          <table className="mt-3 min-w-max text-sm">
            <thead>
              <tr>
                {preview.columns.map((x) => (
                  <th className="px-2" key={x}>
                    {x}
                  </th>
                ))}
              </tr>
            </thead>
            <tbody>
              {preview.rows.map((r, i) => (
                <tr key={i}>
                  {preview.columns.map((x) => (
                    <td
                      className="max-w-48 truncate px-2"
                      title={r[x] ?? "null"}
                      key={x}
                    >
                      {r[x] ?? "—"}
                    </td>
                  ))}
                </tr>
              ))}
            </tbody>
          </table>
        </section>
      )}
    </div>
  );
}
function Stat({ l, v }: { l: string; v: string | number }) {
  return (
    <div>
      <p className="text-xl font-semibold capitalize">
        {String(v).replaceAll("_", " ")}
      </p>
      <p className="muted text-xs">{l}</p>
    </div>
  );
}
