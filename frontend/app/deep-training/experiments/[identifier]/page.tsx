import { DeepTrainingDetail } from "@/components/forecasting/deep-training-detail";

export default async function DeepTrainingDetailPage({
  params,
}: {
  params: Promise<{ identifier: string }>;
}) {
  const { identifier } = await params;
  return <DeepTrainingDetail identifier={identifier} />;
}
