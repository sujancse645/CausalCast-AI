import type { DatasetStatus } from "@/types/dataset";
export function DatasetStatusBadge({ status }: { status: DatasetStatus }) {
  return (
    <span className="rounded-full border border-slate-700 px-2 py-1 text-xs capitalize">
      {status}
    </span>
  );
}
