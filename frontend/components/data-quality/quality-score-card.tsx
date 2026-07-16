export function QualityScoreCard({
  label,
  score,
}: {
  label: string;
  score: number;
}) {
  const status =
    score >= 90 ? "Strong" : score >= 70 ? "Review" : "Attention required";
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950/30 p-4">
      <p className="muted text-xs">{label}</p>
      <p className="mt-2 text-2xl font-semibold">{Math.round(score)}/100</p>
      <p className="text-xs text-slate-400">{status}</p>
    </div>
  );
}
