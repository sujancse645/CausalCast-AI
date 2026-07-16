import { ForecastExperimentDetail } from "@/components/forecasting/forecasting";
export default async function Page({
  params,
}: {
  params: Promise<{ experimentId: string }>;
}) {
  const { experimentId } = await params;
  return <ForecastExperimentDetail experimentId={experimentId} />;
}
