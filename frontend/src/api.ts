// API client + shared types for the Flask backend.

export interface Prediction {
  label: string;
  display_name: string;
  confidence: number; // 0..1
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

export async function analyzeImage(file: File): Promise<AnalyzeResult> {
  const form = new FormData();
  form.append("image", file);
  const res = await fetch("/api/analyze", { method: "POST", body: form });
  const body = await res.json().catch(() => ({ error: `Server error (${res.status})` }));
  if (!res.ok) throw new Error(body.error ?? `Server error (${res.status})`);
  return body as AnalyzeResult;
}

export async function searchFoods(q: string): Promise<FoodSearchHit[]> {
  const res = await fetch(`/api/foods?q=${encodeURIComponent(q)}`);
  if (!res.ok) throw new Error("Search failed");
  const body = await res.json();
  return body.results as FoodSearchHit[];
}

export async function getNutrition(label: string): Promise<Nutrition> {
  const res = await fetch(`/api/foods/${encodeURIComponent(label)}`);
  const body = await res.json().catch(() => ({ error: `Server error (${res.status})` }));
  if (!res.ok) throw new Error(body.error ?? "Food not found");
  return body as Nutrition;
}

export async function checkHealth(): Promise<boolean> {
  try {
    const res = await fetch("/api/health");
    if (!res.ok) return false;
    const body = await res.json();
    return body.status === "ok";
  } catch {
    return false;
  }
}
