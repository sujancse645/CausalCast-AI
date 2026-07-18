import { DeepForecastingStatusCard } from "@/components/forecasting/deep-forecasting";
export default function Page() {
  return (
    <div className="space-y-6">
      <header>
        <h1 className="text-3xl font-semibold">Forecasting</h1>
        <p className="mt-2 text-slate-400">
          Governed baseline, gradient-boosting, and deep forecasting
          infrastructure.
        </p>
      </header>
      <DeepForecastingStatusCard />
    </div>
  );
}
