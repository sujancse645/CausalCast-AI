import { PreparationDetail } from "@/components/preparation/preparation-detail";
export default async function Page({
  params,
}: {
  params: Promise<{ datasetId: string; preparedDatasetId: string }>;
}) {
  const { datasetId, preparedDatasetId } = await params;
  return (
    <PreparationDetail datasetId={datasetId} preparedId={preparedDatasetId} />
  );
}
