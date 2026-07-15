import { ModulePage } from "@/components/common/module-page";
export default function Page() {
  return (
    <ModulePage
      title="Model Trust Center"
      description="Inspect data quality, calibration, drift, limitations, and model lineage."
      capabilities={[
        "Model cards and lineage",
        "Calibration monitoring",
        "Data quality and drift signals",
      ]}
    />
  );
}
