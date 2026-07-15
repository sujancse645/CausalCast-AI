import { ModulePage } from "@/components/common/module-page";
export default function Page() {
  return (
    <ModulePage
      title="Scenario Lab"
      description="Explore marketing decisions against forecast uncertainty before committing spend."
      capabilities={[
        "Editable what-if scenarios",
        "Baseline comparisons",
        "Uncertainty-aware outcomes",
      ]}
    />
  );
}
