"""Nutrition engine (FR-06/FR-07) + food search (FR-05).

Reads data/foods.json (names + aliases) and data/nutrition_table.json
(per-100g macros + default portion). All scaling is linear from per-100g.
"""
import json
from functools import lru_cache

from config import Config


@lru_cache(maxsize=1)
def _foods() -> list[dict]:
    with open(Config.FOODS_PATH, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _table() -> dict:
    with open(Config.NUTRITION_PATH, encoding="utf-8") as f:
        return json.load(f)


@lru_cache(maxsize=1)
def _by_label() -> dict:
    return {food["label"]: food for food in _foods()}


def display_name(label: str) -> str:
    food = _by_label().get(label)
    return food["display_name"] if food else label.replace("_", " ").title()


def _scaled(per_100g: dict, grams: float) -> dict:
    factor = grams / 100.0
    return {
        "kcal": round(per_100g["kcal"] * factor),
        "protein_g": round(per_100g["protein_g"] * factor, 1),
        "carbs_g": round(per_100g["carbs_g"] * factor, 1),
        "fat_g": round(per_100g["fat_g"] * factor, 1),
    }


def nutrition_block(label: str, portion_g: float | None = None) -> dict | None:
    """Full nutrition payload for one recognized/selected food, or None if unknown."""
    row = _table().get(label)
    if row is None:
        return None
    per_100g = {k: row[k] for k in ("kcal", "protein_g", "carbs_g", "fat_g")}
    default_g = row["default_portion_g"]
    grams = portion_g if portion_g and portion_g > 0 else default_g
    mult = Config.PORTION_MULTIPLIERS
    return {
        "food": label,
        "display_name": display_name(label),
        "per_100g": per_100g,
        "default_portion_g": default_g,
        "portions": {
            "small_g": round(default_g * mult["small"]),
            "medium_g": round(default_g * mult["medium"]),
            "large_g": round(default_g * mult["large"]),
        },
        "estimate": {"portion_g": round(grams), **_scaled(per_100g, grams)},
        "needs_review": row.get("needs_review", True),
    }


def search(query: str, limit: int = 10) -> list[dict]:
    """Substring search over display names and aliases, best matches first."""
    q = query.strip().lower()
    if not q:
        return []
    ranked: list[tuple[int, dict]] = []
    for food in _foods():
        name = food["display_name"].lower()
        aliases = [a.lower() for a in food.get("aliases", [])]
        if name.startswith(q):
            rank = 0
        elif q in name:
            rank = 1
        elif any(a.startswith(q) for a in aliases):
            rank = 2
        elif any(q in a for a in aliases):
            rank = 3
        else:
            continue
        ranked.append((rank, food))
    ranked.sort(key=lambda pair: (pair[0], pair[1]["display_name"]))
    return [
        {"label": food["label"], "display_name": food["display_name"]}
        for _rank, food in ranked[:limit]
    ]
