---
title: AI Food Calories Recognition
emoji: 🍕
colorFrom: green
colorTo: yellow
sdk: docker
app_port: 7860
pinned: false
license: mit
---

# AI Food & Calories Recognition

Upload one meal photo → dominant food identified (ViT fine-tuned on Food-101) → estimated calories + protein/carbs/fat for an adjustable portion. **Estimates only — not medical or dietary advice.**

Measured: top-1 87.0%, top-3 97.0% (100 held-out Food-101 test images), ~1 s CPU inference.

Astrolab Group internship project. Source repo includes tests, evaluation harness and full docs. Backend structure ported from [Rishabh1925/foodvisionai](https://github.com/Rishabh1925/foodvisionai) (MIT); model: [nateraw/food](https://huggingface.co/nateraw/food).
