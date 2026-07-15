import { Dashboard } from "@/components/dashboard/dashboard";
export default function DashboardPage() {
  return (
    <>
      <div className="mb-6">
        <h2 className="text-2xl font-semibold">Dashboard</h2>
        <p className="muted mt-1 text-sm">
          Revenue intelligence and platform readiness at a glance.
        </p>
      </div>
      <Dashboard />
    </>
  );
}
