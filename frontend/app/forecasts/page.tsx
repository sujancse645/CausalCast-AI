import { ModulePage } from "@/components/common/module-page";
export default function Page() {
  return (
    <ModulePage
      title="Revenue Forecasts"
      description="Probabilistic revenue and ROAS projections with calibrated uncertainty."
      capabilities={[
        "Time-based model validation",
        "Prediction intervals and calibration",
        "Channel and horizon comparisons",
      ]}
    />
  );
}
