import { ModulePage } from "@/components/common/module-page";
export default function Page() {
  return (
    <ModulePage
      title="Causal Intelligence"
      description="Explain incremental campaign influence with evidence and explicit assumptions."
      capabilities={[
        "Causal graph workspace",
        "Incrementality analysis",
        "Assumption and sensitivity reporting",
      ]}
    />
  );
}
