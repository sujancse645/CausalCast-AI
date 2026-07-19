import { ModulePage } from "@/components/common/module-page";
import { ProductionForecastWorkspace } from "@/components/forecasting/production-forecast-workspace";
import { LineChart } from "lucide-react";

export default function Page() {
  return (
    <ModulePage
      title="Production Forecasts"
      description="Run checksum-verified trained models over genuine held-out project data."
      icon={<LineChart className="text-blue-300" />}
    >
      <ProductionForecastWorkspace />
    </ModulePage>
  );
}
