import { ModulePage } from "@/components/common/module-page";
export default function Page() {
  return (
    <ModulePage
      title="AI Growth Copilot"
      description="Deliver evidence-grounded decision support backed by platform data."
      capabilities={[
        "Source-grounded answers",
        "Recommendation evidence trails",
        "Human approval workflows",
      ]}
    />
  );
}
