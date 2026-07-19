import { ModulePage } from "@/components/common/module-page";
import { InfrastructureDashboard } from "@/components/infrastructure/infrastructure-dashboard";
import { Server } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Infrastructure & Observability | CausalCast AI",
  description:
    "Monitor backend services, performance metrics, and infrastructure health",
};

export default function InfrastructurePage() {
  return (
    <ModulePage
      title="Infrastructure"
      icon={<Server className="text-blue-400" />}
    >
      <InfrastructureDashboard />
    </ModulePage>
  );
}
