"use client";
import { useEffect, useState } from "react";
import { ApiError, getForecastStats } from "@/lib/api";
import type { ForecastStats } from "@/types/forecasting";
export function ForecastingSummary() {
  const [stats, setStats] = useState<ForecastStats | null>(null);
  const [error, setError] = useState<string | null>(null);
  useEffect(() => {
    void getForecastStats()
      .then(setStats)
      .catch((e) =>
        setError(
          e instanceof ApiError ? e.message : "Forecast stats unavailable",
        ),
      );
  }, []);
  return (
    <section className="panel p-5">
      <h3 className="font-semibold">Forecasting registry</h3>
      {error ? (
        <p role="alert" className="muted mt-3">
          {error}
        </p>
      ) : !stats ? (
        <p role="status" className="muted mt-3">
          Loading forecasting statistics…
        </p>
      ) : (
        <div className="mt-4 grid gap-3 sm:grid-cols-4">
          <Cell label="Completed" value={stats.completed_experiments} />
          <Cell label="Failed" value={stats.failed_experiments} />
          <Cell label="Awaiting" value={stats.datasets_awaiting_forecasting} />
          <Cell
            label="Average test WAPE"
            value={
              stats.average_test_wape === null
                ? "—"
                : stats.average_test_wape.toFixed(4)
            }
          />
        </div>
      )}
    </section>
  );
}
function Cell({ label, value }: { label: string; value: string | number }) {
  return (
    <div>
      <p className="text-xl font-semibold">{value}</p>
      <p className="muted text-xs">{label}</p>
    </div>
  );
}
