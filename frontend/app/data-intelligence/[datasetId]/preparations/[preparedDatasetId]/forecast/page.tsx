import { ForecastWorkspace } from "@/components/forecasting/forecasting";
export default async function Page({
  params,
}: {
  params: Promise<{ datasetId: string; preparedDatasetId: string }>;
}) {
  const { datasetId, preparedDatasetId } = await params;
  return (
    <ForecastWorkspace datasetId={datasetId} preparedId={preparedDatasetId} />
  );
}
