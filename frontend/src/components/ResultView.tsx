// Single-screen result (FR-08): food + confidence, big kcal number, macro
// cards, portion control, alternatives on low confidence, manual correction.
import { useState } from "react";
import type { AnalyzeResult, FoodSearchHit, Nutrition, Prediction } from "../api";
import ConfidenceBadge from "./ConfidenceBadge";
import CorrectionSearch from "./CorrectionSearch";
import PortionControl from "./PortionControl";

interface Props {
  imageUrl: string;
  result: AnalyzeResult;
  nutrition: Nutrition | null;
  selectedLabel: string | null;
  grams: number;
  onGramsChange: (g: number) => void;
  onPickFood: (labelOrHit: FoodSearchHit) => void;
  onReset: () => void;
}

function scale(n: Nutrition, grams: number) {
  const f = grams / 100;
  return {
    kcal: Math.round(n.per_100g.kcal * f),
    protein_g: Math.round(n.per_100g.protein_g * f * 10) / 10,
    carbs_g: Math.round(n.per_100g.carbs_g * f * 10) / 10,
    fat_g: Math.round(n.per_100g.fat_g * f * 10) / 10,
  };
}

export default function ResultView(props: Props) {
  const { imageUrl, result, nutrition, selectedLabel, grams, onGramsChange, onPickFood, onReset } = props;
  const [correcting, setCorrecting] = useState(false);

  const chosen: Prediction | undefined =
    result.predictions.find((p) => p.label === selectedLabel) ?? result.predictions[0];
  const manualPick = !result.predictions.some((p) => p.label === selectedLabel);
  const macros = nutrition ? scale(nutrition, grams) : null;

  return (
    <div className="rounded-2xl bg-white p-5 shadow-sm">
      {/* header row: thumbnail + identification */}
      <div className="flex items-start gap-4">
        <img src={imageUrl} alt="Analyzed meal" className="h-24 w-24 shrink-0 rounded-xl object-cover" />
        <div className="min-w-0 flex-1">
          {result.status === "no_food" && !nutrition ? (
            <>
              <h2 className="text-xl font-bold text-slate-800">No confident match</h2>
              <p className="mt-1 text-sm text-slate-500">
                This doesn't look like a food the model knows. Pick the food manually below.
              </p>
            </>
          ) : (
            <>
              <h2 className="truncate text-xl font-bold text-slate-800">
                {nutrition?.display_name ?? chosen?.display_name}
              </h2>
              <div className="mt-1 flex flex-wrap items-center gap-2">
                {manualPick ? (
                  <span className="rounded-full bg-sky-100 px-2.5 py-0.5 text-xs font-semibold text-sky-800">
                    manually selected
                  </span>
                ) : (
                  chosen && <ConfidenceBadge confidence={chosen.confidence} />
                )}
                {!manualPick && chosen?.source === "tunisian" && (
                  <span className="rounded-full bg-red-100 px-2.5 py-0.5 text-xs font-semibold text-red-800">
                    🇹🇳 Tunisian model
                  </span>
                )}
                <span className="text-xs text-slate-400">analyzed in {Math.round(result.latency_ms)} ms</span>
              </div>
            </>
          )}
        </div>
        <button
          onClick={onReset}
          className="shrink-0 rounded-lg border border-slate-300 px-3 py-1.5 text-sm hover:bg-slate-50"
        >
          New photo
        </button>
      </div>

      {/* low-confidence alternatives (FR-04) */}
      {result.status === "low_confidence" && (
        <div className="mt-4 rounded-xl bg-amber-50 p-3">
          <p className="mb-2 text-sm font-medium text-amber-800">
            Not fully sure — did you mean one of these?
          </p>
          <div className="flex flex-wrap gap-2">
            {result.predictions.map((p) => (
              <button
                key={p.label}
                onClick={() => onPickFood({ label: p.label, display_name: p.display_name })}
                className={`rounded-full border px-3 py-1.5 text-sm ${
                  p.label === (selectedLabel ?? result.predictions[0].label)
                    ? "border-amber-600 bg-amber-600 text-white"
                    : "border-amber-300 bg-white text-amber-900 hover:border-amber-500"
                }`}
              >
                {p.display_name} · {Math.round(p.confidence * 100)}%
              </button>
            ))}
          </div>
        </div>
      )}

      {/* nutrition (FR-06) */}
      {nutrition && macros && (
        <>
          <div className="mt-5 flex items-end gap-2">
            <span className="text-5xl font-extrabold tracking-tight text-slate-900">{macros.kcal}</span>
            <span className="pb-1.5 text-lg font-medium text-slate-500">kcal · {grams} g portion</span>
          </div>
          <div className="mt-4 grid grid-cols-3 gap-3">
            {[
              { name: "Protein", value: macros.protein_g, tone: "bg-sky-50 text-sky-900" },
              { name: "Carbs", value: macros.carbs_g, tone: "bg-orange-50 text-orange-900" },
              { name: "Fat", value: macros.fat_g, tone: "bg-violet-50 text-violet-900" },
            ].map((m) => (
              <div key={m.name} className={`rounded-xl p-3 text-center ${m.tone}`}>
                <p className="text-2xl font-bold">{m.value} g</p>
                <p className="text-xs font-medium opacity-70">{m.name}</p>
              </div>
            ))}
          </div>
          <div className="mt-5">
            <PortionControl nutrition={nutrition} grams={grams} onChange={onGramsChange} />
          </div>
        </>
      )}

      {/* manual correction (FR-05) */}
      <div className="mt-5">
        {correcting || (result.status === "no_food" && !nutrition) ? (
          <CorrectionSearch
            onSelect={(hit) => {
              onPickFood(hit);
              setCorrecting(false);
            }}
            onClose={() => setCorrecting(false)}
          />
        ) : (
          <button onClick={() => setCorrecting(true)} className="text-sm text-emerald-700 underline">
            Wrong food? Search and correct it
          </button>
        )}
      </div>

      <p className="mt-5 border-t border-slate-100 pt-3 text-xs text-slate-400">{result.disclaimer}</p>
    </div>
  );
}
