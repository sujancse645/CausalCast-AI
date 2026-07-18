import { ModulePage } from "@/components/common/module-page";
import { ExplainabilityDashboard } from "@/components/explainability/explainability-dashboard";
import { Lightbulb } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Explainable AI | CausalCast AI",
  description: "Forecast Diagnostics, Model Transparency, and Root-Cause Analysis",
};

export default function ExplainabilityPage() {
  return (
    <ModulePage title="Explainable AI" icon={<Lightbulb className="text-amber-400" />}>
      <ExplainabilityDashboard />
    </ModulePage>
  );
}
