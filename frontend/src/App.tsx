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
import { BowlIcon, GithubIcon } from "./components/icons";
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
      <div className="mx-auto max-w-5xl px-4 py-8 sm:py-10">
        <header className="mb-8 flex items-start gap-4">
          <div className="flex h-12 w-12 shrink-0 items-center justify-center rounded-2xl bg-gradient-to-br from-emerald-500 to-teal-600 text-white shadow-md shadow-emerald-500/25">
            <BowlIcon className="h-6 w-6" />
          </div>
          <div>
            <h1 className="text-2xl font-extrabold tracking-tight text-slate-900 sm:text-3xl">
              AI Food &amp;{" "}
              <span className="bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
                Calories
              </span>{" "}
              Recognition
            </h1>
            <p className="mt-1 text-sm text-slate-500">
              One meal photo → food, calories and macros.{" "}
              <span className="font-medium text-slate-600">Estimates only — not medical or dietary advice.</span>
            </p>
            <div className="mt-2 flex flex-wrap gap-1.5 text-[11px] font-medium">
              <span className="rounded-full bg-white/80 px-2 py-0.5 text-slate-500 ring-1 ring-slate-200">ViT · Food-101</span>
              <span className="rounded-full bg-white/80 px-2 py-0.5 text-slate-500 ring-1 ring-slate-200">🇹🇳 Tunisian model · 19 dishes</span>
              <span className="rounded-full bg-white/80 px-2 py-0.5 text-slate-500 ring-1 ring-slate-200">121 foods · FR/AR search</span>
            </div>
          </div>
        </header>

        <div className="grid gap-6 lg:grid-cols-[1fr_280px]">
          <main className="space-y-4">
            {!file && <UploadArea onImageSelect={selectFile} onError={setError} disabled={busy} />}

            {file && previewUrl && !result && (
              <div className="rise-in rounded-3xl bg-white p-4 shadow-lg shadow-slate-900/5 ring-1 ring-slate-100">
                <img
                  src={previewUrl}
                  alt="Meal preview"
                  className="max-h-96 w-full rounded-2xl object-contain"
                />
                <div className="mt-4 flex flex-wrap items-center gap-3">
                  <button
                    onClick={analyze}
                    disabled={busy || backendUp === false}
                    className="rounded-xl bg-gradient-to-r from-emerald-600 to-teal-600 px-6 py-2.5 font-semibold text-white shadow-md shadow-emerald-600/25 transition-all hover:shadow-lg hover:shadow-emerald-600/30 hover:brightness-105 disabled:opacity-50 disabled:shadow-none"
                  >
                    {busy ? "Analyzing…" : "Analyze photo"}
                  </button>
                  <button
                    onClick={reset}
                    disabled={busy}
                    className="rounded-xl border border-slate-200 bg-white px-4 py-2.5 font-medium text-slate-600 transition-colors hover:border-slate-300 hover:bg-slate-50 disabled:opacity-50"
                  >
                    Replace photo
                  </button>
                  {busy && (
                    <span className="flex items-center gap-2 text-sm text-slate-500">
                      <span className="h-4 w-4 animate-spin rounded-full border-2 border-emerald-500 border-t-transparent" />
                      Running both recognition models…
                    </span>
                  )}
                </div>
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

        <footer className="mt-10 flex flex-col items-center gap-1.5 border-t border-slate-200/70 pt-5 text-center text-xs text-slate-400">
          <p className="text-sm font-semibold text-slate-600">
            Designed &amp; built by{" "}
            <span className="bg-gradient-to-r from-emerald-600 to-teal-600 bg-clip-text text-transparent">
              Mohamed Mansouri
            </span>
          </p>
          <a
            href="https://github.com/MohamedMansourii/food-calorie-recognition"
            target="_blank"
            rel="noreferrer"
            className="flex items-center gap-1.5 text-slate-400 transition-colors hover:text-emerald-600"
          >
            <GithubIcon className="h-3.5 w-3.5" /> View the source on GitHub
          </a>
          <p>© 2026 Mohamed Mansouri</p>
        </footer>
      </div>
    </div>
  );
}
