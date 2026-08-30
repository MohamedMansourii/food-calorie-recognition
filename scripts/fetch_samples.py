"""Fetch real evaluation images: 5 per class for 20 common Food-101 classes.

Streams the food101 evaluation split ('validation' on the HF hub — Food-101's
official test set) via the `datasets` library, so nothing but the 100 saved
JPEGs ever touches disk. Early-stops once every bucket is full.

Run:  <venv>/python scripts/fetch_samples.py
"""
import os
import sys

from datasets import load_dataset

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT_DIR = os.path.join(REPO_ROOT, "sample_photos")

# 20 common, everyday classes (all verified Food-101 slugs).
TARGET_CLASSES = [
    "pizza", "hamburger", "french_fries", "sushi", "ramen",
    "caesar_salad", "greek_salad", "tacos", "chicken_wings", "chicken_curry",
    "steak", "spaghetti_carbonara", "lasagna", "pancakes", "french_toast",
    "ice_cream", "cheesecake", "chocolate_cake", "donuts", "omelette",
]
PER_CLASS = 5


def main() -> int:
    ds = load_dataset("food101", split="validation", streaming=True)
    label_names = ds.features["label"].names
    targets = {name: 0 for name in TARGET_CLASSES}
    missing = [t for t in TARGET_CLASSES if t not in label_names]
    if missing:
        print(f"ERROR: not Food-101 classes: {missing}")
        return 1

    os.makedirs(OUT_DIR, exist_ok=True)
    seen = 0
    for row in ds:
        seen += 1
        name = label_names[row["label"]]
        count = targets.get(name)
        if count is None or count >= PER_CLASS:
            if seen % 2000 == 0:
                done = sum(targets.values())
                print(f"  streamed {seen} rows, saved {done}/{len(targets) * PER_CLASS}")
            if all(c >= PER_CLASS for c in targets.values()):
                break
            continue
        cls_dir = os.path.join(OUT_DIR, name)
        os.makedirs(cls_dir, exist_ok=True)
        img = row["image"]
        if img.mode != "RGB":
            img = img.convert("RGB")
        img.save(os.path.join(cls_dir, f"{name}_{count + 1}.jpg"), format="JPEG", quality=90)
        targets[name] = count + 1
        if all(c >= PER_CLASS for c in targets.values()):
            break

    total = sum(targets.values())
    print(f"Done: {total} images in {OUT_DIR} (streamed {seen} rows)")
    short = {k: v for k, v in targets.items() if v < PER_CLASS}
    if short:
        print(f"WARNING: incomplete classes: {short}")
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())
