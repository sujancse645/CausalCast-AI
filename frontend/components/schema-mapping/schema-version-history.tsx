import type { SchemaHistoryItem } from "@/types/schema-mapping";
export function SchemaVersionHistory({
  items,
}: {
  items: SchemaHistoryItem[];
}) {
  return (
    <section className="panel p-5">
      <h2 className="font-semibold">Version history</h2>
      {items.length === 0 ? (
        <p className="muted mt-3 text-sm">No schema versions yet.</p>
      ) : (
        <ul className="mt-3 space-y-2">
          {items.map((item) => (
            <li
              key={item.id}
              className="flex justify-between border-b border-slate-800 pb-2 text-sm"
            >
              <span>
                Version {item.schema_version} ·{" "}
                <span className="capitalize">{item.status}</span>
              </span>
              <span className="muted">
                {new Date(item.created_at).toLocaleString()}
              </span>
            </li>
          ))}
        </ul>
      )}
    </section>
  );
}
