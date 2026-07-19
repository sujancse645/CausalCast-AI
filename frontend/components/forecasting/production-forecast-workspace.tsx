"use client";

import {
  createProductionForecast,
  getProductionForecastDataset,
  listProductionForecastDatasets,
} from "@/lib/api";
import type {
  ProductionDatasetMetadata,
  ProductionDatasetSummary,
  ProductionForecastResponse,
} from "@/types/production-forecast";
import {
  AlertTriangle,
  Database,
  LoaderCircle,
  Play,
  RefreshCw,
} from "lucide-react";
import {
  type FormEvent,
  type ReactNode,
  useEffect,
  useMemo,
  useState,
} from "react";
import {
  CartesianGrid,
  Legend,
  Line,
  LineChart,
  ResponsiveContainer,
  Tooltip,
  XAxis,
  YAxis,
} from "recharts";

const integer = new Intl.NumberFormat(undefined, { maximumFractionDigits: 0 });
const decimal = new Intl.NumberFormat(undefined, { maximumFractionDigits: 4 });

export function ProductionForecastWorkspace() {
  const [datasets, setDatasets] = useState<ProductionDatasetSummary[]>([]);
  const [dataset, setDataset] = useState("");
  const [metadata, setMetadata] = useState<ProductionDatasetMetadata | null>(
    null,
  );
  const [horizon, setHorizon] = useState(1);
  const [series, setSeries] = useState("");
  const [forecast, setForecast] = useState<ProductionForecastResponse | null>(
    null,
  );
  const [loadingCatalog, setLoadingCatalog] = useState(true);
  const [running, setRunning] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const loadCatalog = async () => {
    setLoadingCatalog(true);
    setError(null);
    try {
      const items = await listProductionForecastDatasets();
      setDatasets(items);
      setDataset((current) => current || items[0]?.id || "");
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "The dataset catalog is unavailable.",
      );
    } finally {
      setLoadingCatalog(false);
    }
  };

  useEffect(() => {
    let active = true;
    listProductionForecastDatasets()
      .then((items) => {
        if (!active) return;
        setDatasets(items);
        setDataset(items[0]?.id ?? "");
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setError(
          caught instanceof Error
            ? caught.message
            : "The dataset catalog is unavailable.",
        );
      })
      .finally(() => {
        if (active) setLoadingCatalog(false);
      });
    return () => {
      active = false;
    };
  }, []);

  useEffect(() => {
    if (!dataset) return;
    let active = true;
    getProductionForecastDataset(dataset)
      .then((value) => {
        if (!active) return;
        setMetadata(value);
        setHorizon(value.default_horizon);
        setSeries(value.example_series[0] ?? "");
      })
      .catch((caught: unknown) => {
        if (!active) return;
        setError(
          caught instanceof Error
            ? caught.message
            : "Dataset metadata is unavailable.",
        );
      });
    return () => {
      active = false;
    };
  }, [dataset]);

  const selectDataset = (value: string) => {
    setDataset(value);
    setMetadata(null);
    setForecast(null);
    setError(null);
  };

  const runForecast = async (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!metadata) return;
    setRunning(true);
    setError(null);
    try {
      setForecast(
        await createProductionForecast({
          dataset,
          horizon,
          ...(series ? { series } : {}),
        }),
      );
    } catch (caught) {
      setError(
        caught instanceof Error
          ? caught.message
          : "Forecast generation failed.",
      );
    } finally {
      setRunning(false);
    }
  };

  if (loadingCatalog) {
    return (
      <StateMessage
        icon={<LoaderCircle className="animate-spin" />}
        message="Loading real forecast assets…"
      />
    );
  }

  return (
    <div className="space-y-6">
      {error && (
        <div
          role="alert"
          className="flex items-start gap-3 rounded-xl border border-red-500/30 bg-red-500/10 p-4 text-sm text-red-100"
        >
          <AlertTriangle className="mt-0.5 shrink-0" size={18} />
          <div className="flex-1">{error}</div>
          {datasets.length === 0 && (
            <button
              type="button"
              onClick={() => void loadCatalog()}
              className="inline-flex items-center gap-2 text-xs font-semibold"
            >
              <RefreshCw size={14} /> Retry
            </button>
          )}
        </div>
      )}

      {datasets.length === 0 ? (
        <StateMessage
          icon={<Database />}
          message="No validated model-and-dataset pairs are available."
        />
      ) : (
        <form
          onSubmit={runForecast}
          className="panel grid gap-4 p-5 md:grid-cols-4 md:items-end"
        >
          <Field label="Dataset">
            <select
              aria-label="Dataset"
              value={dataset}
              onChange={(event) => selectDataset(event.target.value)}
              className="control"
            >
              {datasets.map((item) => (
                <option key={item.id} value={item.id}>
                  {item.name}
                </option>
              ))}
            </select>
          </Field>
          <Field label="Horizon">
            <input
              aria-label="Horizon"
              type="number"
              min={1}
              max={365}
              value={horizon}
              onChange={(event) => setHorizon(Number(event.target.value))}
              className="control"
            />
          </Field>
          <Field label={metadata?.series_dimension ?? "Series"}>
            <select
              aria-label="Series"
              value={series}
              disabled={!metadata?.series_dimension}
              onChange={(event) => setSeries(event.target.value)}
              className="control disabled:opacity-50"
            >
              {!metadata?.series_dimension && (
                <option value="">Not applicable</option>
              )}
              {metadata?.example_series.map((item) => (
                <option key={item} value={item}>
                  {item}
                </option>
              ))}
            </select>
          </Field>
          <button
            type="submit"
            disabled={!metadata || running}
            className="inline-flex min-h-11 items-center justify-center gap-2 rounded-xl bg-blue-500 px-4 font-semibold text-white hover:bg-blue-400 disabled:cursor-not-allowed disabled:opacity-50"
          >
            {running ? (
              <LoaderCircle className="animate-spin" size={17} />
            ) : (
              <Play size={17} />
            )}
            {running ? "Running model…" : "Generate forecast"}
          </button>
        </form>
      )}

      {metadata && <ModelMetadata metadata={metadata} />}
      {forecast ? (
        <ForecastResult forecast={forecast} />
      ) : (
        datasets.length > 0 && (
          <StateMessage
            icon={<Play />}
            message="Choose a validated asset and generate a real held-out forecast."
          />
        )
      )}
    </div>
  );
}

function Field({ label, children }: { label: string; children: ReactNode }) {
  return (
    <label className="grid gap-2 text-xs font-semibold tracking-wide text-slate-300">
      {label}
      {children}
    </label>
  );
}

function ModelMetadata({ metadata }: { metadata: ProductionDatasetMetadata }) {
  return (
    <section className="panel p-5" aria-labelledby="model-details-heading">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 id="model-details-heading" className="font-semibold">
            Model and data contract
          </h3>
          <p className="mt-1 text-sm text-slate-400">
            {metadata.model_name} · {metadata.model_type} · {metadata.frequency}
          </p>
        </div>
        <span className="rounded-full border border-amber-500/30 bg-amber-500/10 px-3 py-1 text-xs text-amber-200">
          Held-out test prediction
        </span>
      </div>
      <dl className="mt-4 grid gap-3 text-sm sm:grid-cols-2 lg:grid-cols-4">
        <Detail label="Target" value={metadata.target} />
        <Detail
          label="Default horizon"
          value={String(metadata.default_horizon)}
        />
        <Detail
          label="Required features"
          value={String(metadata.features.length)}
        />
        <Detail
          label="Series count"
          value={
            metadata.series_count === null
              ? "Not applicable"
              : integer.format(metadata.series_count)
          }
        />
      </dl>
    </section>
  );
}

function ForecastResult({
  forecast,
}: {
  forecast: ProductionForecastResponse;
}) {
  const data = useMemo(
    () =>
      forecast.predictions.map((point) => ({
        ...point,
        label: new Date(point.timestamp).toLocaleDateString(),
      })),
    [forecast],
  );
  return (
    <section className="panel p-5" aria-labelledby="forecast-result-heading">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h3 id="forecast-result-heading" className="font-semibold">
            {forecast.dataset_name} result
          </h3>
          <p className="mt-1 text-xs text-slate-400">
            Predictions and actuals are clearly separated. These held-out
            estimates are not guaranteed future outcomes.
          </p>
        </div>
        <span className="text-xs text-emerald-300">
          Model loaded from disk · {forecast.runtime_ms} ms
        </span>
      </div>
      <div
        className="mt-5 h-80"
        role="img"
        aria-label={`${forecast.dataset_name} prediction and actual chart`}
      >
        <ResponsiveContainer width="100%" height="100%">
          <LineChart data={data}>
            <CartesianGrid stroke="#22334d" vertical={false} />
            <XAxis dataKey="label" stroke="#94a3b8" minTickGap={30} />
            <YAxis
              stroke="#94a3b8"
              width={80}
              tickFormatter={(value) => integer.format(Number(value))}
            />
            <Tooltip
              contentStyle={{
                background: "#0d192c",
                border: "1px solid #22334d",
              }}
              formatter={(value) => decimal.format(Number(value))}
            />
            <Legend />
            <Line
              type="monotone"
              name="Actual"
              dataKey="actual"
              stroke="#e2e8f0"
              strokeWidth={2}
              dot={false}
              connectNulls={false}
            />
            <Line
              type="monotone"
              name="Prediction"
              dataKey="prediction"
              stroke="#3b82f6"
              strokeWidth={3}
              dot={false}
            />
          </LineChart>
        </ResponsiveContainer>
      </div>
      <div className="mt-5 grid gap-3 sm:grid-cols-2 lg:grid-cols-4">
        {Object.entries(forecast.metrics).map(([name, value]) => (
          <Detail key={name} label={name} value={decimal.format(value)} />
        ))}
      </div>
      <details className="mt-5 text-sm">
        <summary className="cursor-pointer text-slate-300">
          Accessible prediction table
        </summary>
        <div className="mt-3 overflow-x-auto">
          <table className="w-full text-left text-xs">
            <thead className="text-slate-400">
              <tr>
                <th className="p-2">Timestamp</th>
                <th className="p-2">Prediction</th>
                <th className="p-2">Actual</th>
              </tr>
            </thead>
            <tbody>
              {forecast.predictions.map((point) => (
                <tr key={point.timestamp} className="border-t border-slate-800">
                  <td className="p-2">
                    {new Date(point.timestamp).toLocaleString()}
                  </td>
                  <td className="p-2">{decimal.format(point.prediction)}</td>
                  <td className="p-2">
                    {point.actual === null
                      ? "Unavailable"
                      : decimal.format(point.actual)}
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      </details>
    </section>
  );
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/50 p-3">
      <dt className="text-xs text-slate-500">{label}</dt>
      <dd className="mt-1 font-medium break-words text-slate-100">{value}</dd>
    </div>
  );
}

function StateMessage({ icon, message }: { icon: ReactNode; message: string }) {
  return (
    <div className="panel grid min-h-48 place-items-center p-6 text-center text-slate-400">
      <div>
        <span className="mx-auto mb-3 grid h-11 w-11 place-items-center rounded-xl bg-slate-800 text-cyan-300">
          {icon}
        </span>
        <p>{message}</p>
      </div>
    </div>
  );
}
