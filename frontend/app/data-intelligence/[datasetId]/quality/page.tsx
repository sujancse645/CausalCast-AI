import { DataQualityWorkspace } from "@/components/data-quality/data-quality-workspace";
export default async function QualityPage({
  params,
}: {
  params: Promise<{ datasetId: string }>;
}) {
  const { datasetId } = await params;
  return <DataQualityWorkspace datasetId={datasetId} />;
}
