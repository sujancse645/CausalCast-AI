import type {
  ColumnProfile,
  SemanticRoleDefinition,
} from "@/types/schema-mapping";
import { ConfidenceIndicator } from "./confidence-indicator";
export function ColumnMappingTable({
  columns,
  roles,
  saving,
  onRole,
  onEvidence,
}: {
  columns: ColumnProfile[];
  roles: SemanticRoleDefinition[];
  saving: string | null;
  onRole: (column: ColumnProfile, role: string) => void;
  onEvidence: (column: ColumnProfile) => void;
}) {
  return (
    <section className="panel overflow-hidden">
      <div className="border-b border-slate-800 p-5">
        <h2 className="font-semibold">Column mappings</h2>
        <p className="muted text-xs">
          Proposals require human review before downstream use.
        </p>
      </div>
      <div className="overflow-x-auto">
        <table className="w-full min-w-[1000px] text-left text-sm">
          <caption className="sr-only">
            Physical and semantic column mappings
          </caption>
          <thead>
            <tr>
              {[
                "Source column",
                "Physical type",
                "Samples",
                "Semantic role",
                "Confidence",
                "Status",
                "Evidence",
              ].map((x) => (
                <th key={x} className="px-4 py-3 text-xs text-slate-500">
                  {x}
                </th>
              ))}
            </tr>
          </thead>
          <tbody>
            {columns.map((column) => (
              <tr key={column.id} className="border-t border-slate-800">
                <td className="px-4 py-3 font-medium">{column.column_name}</td>
                <td className="px-4 capitalize">{column.physical_type}</td>
                <td
                  className="max-w-52 truncate px-4 text-slate-400"
                  title={column.sample_values.join(", ")}
                >
                  {column.sample_values.join(", ") || "No values"}
                </td>
                <td className="px-4">
                  <select
                    aria-label={`Semantic role for ${column.column_name}`}
                    disabled={saving === column.id}
                    value={column.semantic_role}
                    onChange={(e) => onRole(column, e.target.value)}
                    className="rounded-lg border border-slate-700 bg-slate-950 p-2"
                  >
                    <option value="unknown">Unknown</option>
                    {roles
                      .filter((r) => r.role !== "unknown")
                      .map((role) => (
                        <option value={role.role} key={role.role}>
                          {role.label}
                        </option>
                      ))}
                  </select>
                </td>
                <td className="px-4">
                  <ConfidenceIndicator value={column.confidence_score} />
                </td>
                <td className="px-4 capitalize">
                  {column.confirmation_status.replaceAll("_", " ")}
                </td>
                <td className="px-4">
                  <button
                    onClick={() => onEvidence(column)}
                    className="text-blue-400"
                  >
                    View evidence
                  </button>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </section>
  );
}
