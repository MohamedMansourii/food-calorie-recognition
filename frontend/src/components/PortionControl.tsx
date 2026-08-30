// Portion adjustment (FR-07): S/M/L chips + free grams input.
// Recomputation happens client-side from per_100g — no server round-trip.
import type { Nutrition } from "../api";

interface Props {
  nutrition: Nutrition;
  grams: number;
  onChange: (grams: number) => void;
}

export default function PortionControl({ nutrition, grams, onChange }: Props) {
  const presets = [
    { key: "S", label: "Small", g: nutrition.portions.small_g },
    { key: "M", label: "Medium", g: nutrition.portions.medium_g },
    { key: "L", label: "Large", g: nutrition.portions.large_g },
  ];

  return (
    <div>
      <p className="mb-2 text-sm font-medium text-slate-600">Portion size</p>
      <div className="flex flex-wrap items-center gap-2">
        {presets.map((p) => (
          <button
            key={p.key}
            onClick={() => onChange(p.g)}
            className={`rounded-full border px-3 py-1.5 text-sm transition-colors ${
              grams === p.g
                ? "border-emerald-600 bg-emerald-600 text-white"
                : "border-slate-300 bg-white text-slate-700 hover:border-emerald-400"
            }`}
          >
            {p.label} · {p.g} g
          </button>
        ))}
        <label className="ml-1 flex items-center gap-1.5 text-sm text-slate-600">
          <input
            type="number"
            min={1}
            max={2000}
            value={grams}
            onChange={(e) => {
              const v = Number(e.target.value);
              if (Number.isFinite(v) && v > 0 && v <= 2000) onChange(v);
            }}
            className="w-20 rounded-lg border border-slate-300 px-2 py-1.5 text-right"
            aria-label="Portion in grams"
          />
          g
        </label>
      </div>
    </div>
  );
}
