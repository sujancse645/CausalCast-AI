import { ModulePage } from "@/components/common/module-page";
import { ComplianceDashboard } from "@/components/compliance/compliance-dashboard";
import { ShieldCheck } from "lucide-react";
import type { Metadata } from "next";

export const metadata: Metadata = {
  title: "Compliance & Governance | CausalCast AI",
  description: "Audit logs, RBAC policies, and Data Governance",
};

export default function CompliancePage() {
  return (
    <ModulePage
      title="Compliance & Governance"
      icon={<ShieldCheck className="text-emerald-400" />}
    >
      <ComplianceDashboard />
    </ModulePage>
  );
}
