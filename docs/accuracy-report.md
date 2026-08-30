# Accuracy Report — measured, not estimated

Model `nateraw/food` (ViT-B/16 fine-tuned on Food-101) evaluated 2026-08-30 on 100 real images from the Food-101 evaluation split (20 common classes x 5 images), CPU inference on the dev laptop.

## Overall

| Metric | Value |
|---|---|
| Top-1 accuracy | **87.0%** (87/100) |
| Top-3 accuracy | **97.0%** (97/100) |
| Mean latency | 1082 ms |
| Median latency | 894 ms |

## Per-class (top-1 / top-3 out of 5)

| Class | Top-1 | Top-3 |
|---|---|---|
| caesar_salad | 5/5 | 5/5 |
| cheesecake | 4/5 | 4/5 |
| chicken_curry | 4/5 | 4/5 |
| chicken_wings | 4/5 | 5/5 |
| chocolate_cake | 3/5 | 5/5 |
| donuts | 4/5 | 5/5 |
| french_fries | 5/5 | 5/5 |
| french_toast | 5/5 | 5/5 |
| greek_salad | 3/5 | 5/5 |
| hamburger | 5/5 | 5/5 |
| ice_cream | 4/5 | 5/5 |
| lasagna | 3/5 | 4/5 |
| omelette | 4/5 | 5/5 |
| pancakes | 5/5 | 5/5 |
| pizza | 5/5 | 5/5 |
| ramen | 5/5 | 5/5 |
| spaghetti_carbonara | 5/5 | 5/5 |
| steak | 4/5 | 5/5 |
| sushi | 5/5 | 5/5 |
| tacos | 5/5 | 5/5 |

## Worst confusions (true → predicted)

| True class | Predicted | Count |
|---|---|---|
| cheesecake | chocolate_mousse | 1 |
| chicken_curry | hot_and_sour_soup | 1 |
| chicken_wings | takoyaki | 1 |
| chocolate_cake | tiramisu | 1 |
| chocolate_cake | chocolate_mousse | 1 |
| donuts | cup_cakes | 1 |
| greek_salad | caesar_salad | 1 |
| greek_salad | beet_salad | 1 |
| ice_cream | frozen_yogurt | 1 |
| lasagna | macaroni_and_cheese | 1 |

## Notes

- Images come from the held-out Food-101 evaluation split — the model never saw them in training.
- 5 images/class is a smoke-test sample, not a benchmark; the model's published Food-101 top-1 is ~89% over the full 25,250-image test set.
- Latency is single-image CPU inference inside the Flask process (no batching, no GPU).
