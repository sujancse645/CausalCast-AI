import { SchemaMappingWorkspace } from "@/components/schema-mapping/schema-mapping-workspace";
export default async function SchemaPage({
  params,
}: {
  params: Promise<{ datasetId: string }>;
}) {
  const { datasetId } = await params;
  return <SchemaMappingWorkspace datasetId={datasetId} />;
}
