// App shell: health banner, upload -> preview -> analyze -> results,
// session history, manual correction. FR-01/02/03/04/05/07/08/09.
import { useEffect, useRef, useState } from "react";
import {
  analyzeImage,
  checkHealth,
  getNutrition,
  type AnalyzeResult,
  type FoodSearchHit,
  type Nutrition,
} from "./api";
import HistorySidebar, { type HistoryEntry } from "./components/HistorySidebar";
import ResultView from "./components/ResultView";
import UploadArea from "./components/UploadArea";

export default function App() {
  const [backendUp, setBackendUp] = useState<boolean | null>(null);
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [nutrition, setNutrition] = useState<Nutrition | null>(null);
  const [selectedLabel, setSelectedLabel] = useState<string | null>(null);
  const [grams, setGrams] = useState(0);
  const [history, setHistory] = useState<HistoryEntry[]>([]);
  const nextId = useRef(1);
  const currentEntryId = useRef<number | null>(null); // history row for the photo on screen

  useEffect(() => {
    checkHealth().then(setBackendUp);
  }, []);

  const selectFile = (f: File) => {
    setError(null);
    setResult(null);
    setNutrition(null);
    setSelectedLabel(null);
    setFile(f);
    setPreviewUrl(URL.createObjectURL(f));
  };

  const reset = () => {
    setFile(null);
    setPreviewUrl(null);
    setResult(null);
    setNutrition(null);
    setSelectedLabel(null);
    setError(null);
  };

  const analyze = async () => {
    if (!file || busy) return;
    setBusy(true);
    setError(null);
    try {
      const res = await analyzeImage(file);
      setResult(res);
      setNutrition(res.nutrition);
      setSelectedLabel(res.predictions[0]?.label ?? null);
      currentEntryId.current = null;
      if (res.nutrition) {
        setGrams(res.nutrition.default_portion_g);
        upsertHistory(res.nutrition.display_name, res.nutrition.estimate.kcal, res.nutrition.estimate.portion_g);
      }
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed — is the backend running?");
    } finally {
      setBusy(false);
    }
  };

  // Create or update the history row for the photo currently on screen, so
  // corrections and alternative picks are reflected instead of lost (FR-09).
  const upsertHistory = (displayName: string, kcal: number, portionG: number) => {
    const time = new Date().toLocaleTimeString([], { hour: "2-digit", minute: "2-digit" });
    if (currentEntryId.current !== null) {
      const id = currentEntryId.current;
      setHistory((h) => h.map((e) => (e.id === id ? { ...e, displayName, kcal, portionG } : e)));
    } else {
      const id = nextId.current++;
      currentEntryId.current = id;
      setHistory((h) => [{ id, thumbUrl: previewUrl!, displayName, kcal, portionG, time }, ...h]);
    }
  };

  // Alternative chip or correction-search pick: fetch nutrition for that food.
  const pickFood = async (hit: FoodSearchHit) => {
    try {
      const n = await getNutrition(hit.label);
      setSelectedLabel(hit.label);
      setNutrition(n);
      setGrams(n.default_portion_g);
      upsertHistory(n.display_name, n.estimate.kcal, n.estimate.portion_g);
    } catch (e) {
      setError(e instanceof Error ? e.message : "Could not load nutrition");
    }
  };

  return (
    <div className="min-h-screen">
      {backendUp === false && (
        <div className="bg-red-600 px-4 py-2 text-center text-sm font-medium text-white">
          Recognition service unreachable — check that the backend is running, then reload this page.
        </div>
      )}
      <div className="mx-auto max-w-5xl px-4 py-8">
        <header className="mb-6">
          <h1 className="text-2xl font-bold text-slate-900">AI Food &amp; Calories Recognition</h1>
          <p className="mt-1 text-sm text-slate-500">
            Upload one meal photo → get the food, calories and macros.{" "}
            <span className="font-medium">Estimates only — not medical or dietary advice.</span>
          </p>
        </header>

        <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
          <main className="space-y-4">
            {!file && <UploadArea onImageSelect={selectFile} onError={setError} disabled={busy} />}

            {file && previewUrl && !result && (
              <div className="rounded-2xl bg-white p-4 shadow-sm">
                <img
                  src={previewUrl}
                  alt="Meal preview"
                  className="max-h-96 w-full rounded-xl object-contain"
                />
                <div className="mt-4 flex gap-3">
                  <button
                    onClick={analyze}
                    disabled={busy || backendUp === false}
                    className="rounded-lg bg-emerald-600 px-5 py-2 font-medium text-white hover:bg-emerald-700 disabled:opacity-50"
                  >
                    {busy ? "Analyzing…" : "Analyze"}
                  </button>
                  <button
                    onClick={reset}
                    disabled={busy}
                    className="rounded-lg border border-slate-300 px-4 py-2 hover:bg-slate-50 disabled:opacity-50"
                  >
                    Replace photo
                  </button>
                </div>
                {busy && (
                  <p className="mt-3 animate-pulse text-sm text-slate-500">
                    Running the recognition model…
                  </p>
                )}
              </div>
            )}

            {result && previewUrl && (
              <ResultView
                imageUrl={previewUrl}
                result={result}
                nutrition={nutrition}
                selectedLabel={selectedLabel}
                grams={grams}
                onGramsChange={setGrams}
                onPickFood={pickFood}
                onReset={reset}
              />
            )}

            {error && (
              <p role="alert" className="rounded-xl bg-red-50 p-3 text-sm text-red-700">
                {error}
              </p>
            )}
          </main>

          <HistorySidebar entries={history} />
        </div>
      </div>
    </div>
  );
}
