export default function Loading() {
  return (
    <div role="status" className="animate-pulse space-y-4">
      <div className="h-8 w-48 rounded bg-slate-800" />
      <div className="grid-auto">
        {[1, 2, 3, 4].map((x) => (
          <div key={x} className="h-32 rounded-xl bg-slate-800" />
        ))}
      </div>
      <span className="sr-only">Loading dashboard</span>
    </div>
  );
}
