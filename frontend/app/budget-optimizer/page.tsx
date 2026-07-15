import { ModulePage } from "@/components/common/module-page";
export default function Page() {
  return (
    <ModulePage
      title="Budget Optimizer"
      description="Plan risk-aware channel allocations within business constraints."
      capabilities={[
        "Constraint management",
        "Risk-adjusted objectives",
        "Allocation comparison",
      ]}
    />
  );
}
