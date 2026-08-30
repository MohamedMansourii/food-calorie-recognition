// Phase 0 shell: upload -> preview/replace -> analyze -> raw predictions.
// The full results screen lands in Phase 3.
import { useState } from "react";
import UploadArea from "./components/UploadArea";
import { analyzeImage, type AnalyzeResult } from "./api";

export default function App() {
  const [file, setFile] = useState<File | null>(null);
  const [previewUrl, setPreviewUrl] = useState<string | null>(null);
  const [result, setResult] = useState<AnalyzeResult | null>(null);
  const [error, setError] = useState<string | null>(null);
  const [busy, setBusy] = useState(false);

  const selectFile = (f: File) => {
    setError(null);
    setResult(null);
    setFile(f);
    setPreviewUrl((old) => {
      if (old) URL.revokeObjectURL(old);
      return URL.createObjectURL(f);
    });
  };

  const analyze = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      setResult(await analyzeImage(file));
    } catch (e) {
      setError(e instanceof Error ? e.message : "Analysis failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="mx-auto max-w-2xl px-4 py-10">
      <h1 className="text-2xl font-bold">AI Food &amp; Calories Recognition</h1>
      <p className="mb-6 text-sm text-slate-500">Estimates only — not medical or dietary advice.</p>

      {!file && <UploadArea onImageSelect={selectFile} onError={setError} />}

      {file && previewUrl && (
        <div className="rounded-2xl bg-white p-4 shadow">
          <img src={previewUrl} alt="Meal preview" className="max-h-80 w-full rounded-xl object-contain" />
          <div className="mt-4 flex gap-3">
            <button
              onClick={analyze}
              disabled={busy}
              className="rounded-lg bg-emerald-600 px-4 py-2 font-medium text-white disabled:opacity-50"
            >
              {busy ? "Analyzing…" : "Analyze"}
            </button>
            <button
              onClick={() => {
                setFile(null);
                setResult(null);
              }}
              className="rounded-lg border border-slate-300 px-4 py-2"
            >
              Replace
            </button>
          </div>
        </div>
      )}

      {error && <p className="mt-4 rounded-lg bg-red-50 p-3 text-red-700">{error}</p>}
      {result && (
        <pre className="mt-4 overflow-x-auto rounded-lg bg-slate-100 p-3 text-xs">
          {JSON.stringify(result, null, 2)}
        </pre>
      )}
    </div>
  );
}
