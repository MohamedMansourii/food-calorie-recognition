// Color-coded confidence badge (FR-08).
interface Props {
  confidence: number; // 0..1
}

export default function ConfidenceBadge({ confidence }: Props) {
  const pct = Math.round(confidence * 100);
  const tone =
    confidence >= 0.7
      ? "bg-emerald-100 text-emerald-800"
      : confidence >= 0.35
        ? "bg-amber-100 text-amber-800"
        : "bg-red-100 text-red-700";
  return (
    <span className={`inline-block rounded-full px-2.5 py-0.5 text-xs font-semibold ${tone}`}>
      {pct}% confident
    </span>
  );
}
