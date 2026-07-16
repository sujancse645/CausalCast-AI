import { ModulePage } from "@/components/common/module-page";
export default function Page() {
  return (
    <ModulePage
      title="Baseline Forecasting"
      description="Run governed baseline experiments from a model-ready prepared dataset."
      capabilities={[
        "Chronological validation",
        "Expanding-window backtesting",
        "Checksum-validated model artifacts",
      ]}
    />
  );
}
