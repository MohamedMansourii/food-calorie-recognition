// API client + shared types.
//
// Two backends behind one interface (chosen at build time):
//  - default: the local Flask API via fetch('/api/...') — dev + one-URL mode
//  - VITE_SPACE_ID set: recognition via the Hugging Face Space (@gradio/client);
//    search + nutrition run fully client-side from the bundled data files.

export interface Prediction {
  label: string;
  display_name: string;
  confidence: number; // 0..1
  source?: "food101" | "tunisian";
}

export interface Macros {
  kcal: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
}

export interface Nutrition {
  food: string;
  display_name: string;
  per_100g: Macros;
  default_portion_g: number;
  portions: { small_g: number; medium_g: number; large_g: number };
  estimate: Macros & { portion_g: number };
  needs_review: boolean;
}

export type AnalyzeStatus = "ok" | "low_confidence" | "no_food";

export interface AnalyzeResult {
  status: AnalyzeStatus;
  predictions: Prediction[];
  nutrition: Nutrition | null;
  latency_ms: number;
  disclaimer: string;
}

export interface FoodSearchHit {
  label: string;
  display_name: string;
}

const SPACE_ID: string | undefined = import.meta.env.VITE_SPACE_ID;
const DISCLAIMER = "Estimates only — not medical or dietary advice.";

// --- Hugging Face Space mode ---------------------------------------------

let spaceClient: Promise<import("@gradio/client").Client> | null = null;

async function connectSpace() {
  if (!spaceClient) {
    spaceClient = import("@gradio/client").then(({ Client }) => Client.connect(SPACE_ID!));
    spaceClient.catch(() => (spaceClient = null)); // allow retry after failure
  }
  return spaceClient;
}

async function analyzeViaSpace(file: File): Promise<AnalyzeResult> {
  const { CONFIDENT_THRESHOLD, LOW_CONFIDENCE_THRESHOLD, displayName, nutritionBlock } =
    await import("./lib/nutrition");
  const client = await connectSpace();
  const out = (await client.predict("/classify", { image: file })) as {
    data: [{ predictions?: { label: string; confidence: number }[]; latency_ms?: number; error?: string }];
  };
  const payload = out.data[0];
  if (!payload?.predictions) throw new Error(payload?.error ?? "Space returned no predictions");

  const predictions: Prediction[] = payload.predictions.map((p) => ({
    ...p,
    display_name: displayName(p.label),
  }));
  const top1 = predictions[0].confidence;
  const status: AnalyzeStatus =
    top1 >= CONFIDENT_THRESHOLD ? "ok" : top1 >= LOW_CONFIDENCE_THRESHOLD ? "low_confidence" : "no_food";
  return {
    status,
    predictions,
    nutrition: status !== "no_food" ? nutritionBlock(predictions[0].label) : null,
    latency_ms: payload.latency_ms ?? 0,
    disclaimer: DISCLAIMER,
  };
}

// --- public interface ------------------------------------------------------

export async function analyzeImage(file: File): Promise<AnalyzeResult> {
  if (SPACE_ID) return analyzeViaSpace(file);
  const form = new FormData();
  form.append("image", file);
  const res = await fetch("/api/analyze", { method: "POST", body: form });
  const body = await res.json().catch(() => ({ error: `Server error (${res.status})` }));
  if (!res.ok) throw new Error(body.error ?? `Server error (${res.status})`);
  return body as AnalyzeResult;
}

export async function searchFoods(q: string): Promise<FoodSearchHit[]> {
  if (SPACE_ID) return (await import("./lib/nutrition")).searchLocal(q);
  const res = await fetch(`/api/foods?q=${encodeURIComponent(q)}`);
  if (!res.ok) throw new Error("Search failed");
  const body = await res.json();
  return body.results as FoodSearchHit[];
}

export async function getNutrition(label: string): Promise<Nutrition> {
  if (SPACE_ID) {
    const block = (await import("./lib/nutrition")).nutritionBlock(label);
    if (!block) throw new Error(`Unknown food '${label}'.`);
    return block;
  }
  const res = await fetch(`/api/foods/${encodeURIComponent(label)}`);
  const body = await res.json().catch(() => ({ error: `Server error (${res.status})` }));
  if (!res.ok) throw new Error(body.error ?? "Food not found");
  return body as Nutrition;
}

export async function checkHealth(): Promise<boolean> {
  if (SPACE_ID) {
    try {
      await connectSpace();
      return true;
    } catch {
      return false;
    }
  }
  try {
    const res = await fetch("/api/health");
    if (!res.ok) return false;
    const body = await res.json();
    return body.status === "ok";
  } catch {
    return false;
  }
}
