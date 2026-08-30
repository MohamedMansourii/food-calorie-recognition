// Client-side nutrition engine — TS port of backend/nutrition.py, used when
// the app runs against the Hugging Face Space (which only does recognition).
// Same data files, same math: per-100g linear scaling, S/M/L = 0.7/1.0/1.4.
import foodsJson from "../../../data/foods.json";
import tableJson from "../../../data/nutrition_table.json";
import type { FoodSearchHit, Nutrition } from "../api";

interface FoodEntry {
  label: string;
  display_name: string;
  aliases: string[];
}

interface TableRow {
  kcal: number;
  protein_g: number;
  carbs_g: number;
  fat_g: number;
  default_portion_g: number;
  needs_review: boolean;
}

const FOODS = foodsJson as FoodEntry[];
const TABLE = tableJson as Record<string, TableRow>;
const BY_LABEL = new Map(FOODS.map((f) => [f.label, f]));

export const CONFIDENT_THRESHOLD = 0.7; // mirror backend/config.py
export const LOW_CONFIDENCE_THRESHOLD = 0.35;

export function displayName(label: string): string {
  return (
    BY_LABEL.get(label)?.display_name ??
    label.replace(/_/g, " ").replace(/\b\w/g, (c) => c.toUpperCase())
  );
}

export function nutritionBlock(label: string): Nutrition | null {
  const row = TABLE[label];
  if (!row) return null;
  const per100 = {
    kcal: row.kcal,
    protein_g: row.protein_g,
    carbs_g: row.carbs_g,
    fat_g: row.fat_g,
  };
  const d = row.default_portion_g;
  const scale = (g: number) => ({
    kcal: Math.round(per100.kcal * (g / 100)),
    protein_g: Math.round(per100.protein_g * (g / 100) * 10) / 10,
    carbs_g: Math.round(per100.carbs_g * (g / 100) * 10) / 10,
    fat_g: Math.round(per100.fat_g * (g / 100) * 10) / 10,
  });
  return {
    food: label,
    display_name: displayName(label),
    per_100g: per100,
    default_portion_g: d,
    portions: {
      small_g: Math.round(d * 0.7),
      medium_g: Math.round(d * 1.0),
      large_g: Math.round(d * 1.4),
    },
    estimate: { portion_g: Math.round(d), ...scale(d) },
    needs_review: row.needs_review ?? true,
  };
}

export function searchLocal(query: string, limit = 10): FoodSearchHit[] {
  const q = query.trim().toLowerCase();
  if (!q) return [];
  const ranked: Array<[number, FoodEntry]> = [];
  for (const food of FOODS) {
    const name = food.display_name.toLowerCase();
    const aliases = food.aliases.map((a) => a.toLowerCase());
    let rank: number;
    if (name.startsWith(q)) rank = 0;
    else if (name.includes(q)) rank = 1;
    else if (aliases.some((a) => a.startsWith(q))) rank = 2;
    else if (aliases.some((a) => a.includes(q))) rank = 3;
    else continue;
    ranked.push([rank, food]);
  }
  ranked.sort((a, b) => a[0] - b[0] || a[1].display_name.localeCompare(b[1].display_name));
  return ranked.slice(0, limit).map(([, f]) => ({ label: f.label, display_name: f.display_name }));
}
