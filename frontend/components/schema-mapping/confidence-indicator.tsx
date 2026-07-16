export function ConfidenceIndicator({ value }: { value: number }) {
  const percent = Math.round(value * 100);
  const label =
    percent >= 90
      ? "Very High"
      : percent >= 75
        ? "High"
        : percent >= 60
          ? "Moderate"
          : percent >= 40
            ? "Low"
            : "Unresolved";
  return (
    <span
      aria-label={`Confidence ${percent} percent, ${label}`}
      className="text-sm whitespace-nowrap"
    >
      {percent}% — {label}
    </span>
  );
}
