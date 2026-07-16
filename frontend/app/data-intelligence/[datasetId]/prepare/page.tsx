import { PreparationWorkspace } from "@/components/preparation/preparation-workspace";
export default async function Page({
  params,
}: {
  params: Promise<{ datasetId: string }>;
}) {
  const { datasetId } = await params;
  return <PreparationWorkspace datasetId={datasetId} />;
}
