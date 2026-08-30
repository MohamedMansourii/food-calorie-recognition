---
title: Food Calorie Recognition
emoji: 🍕
colorFrom: green
colorTo: yellow
sdk: gradio
app_file: app.py
pinned: false
license: mit
short_description: Meal photo -> top-3 Food-101 predictions (ViT)
---

# AI Food & Calories Recognition — model endpoint

Upload a meal photo → top-3 dominant-food predictions from a ViT fine-tuned on Food-101 ([nateraw/food](https://huggingface.co/nateraw/food)).

Measured on 100 held-out Food-101 test images: **top-1 87.0%, top-3 97.0%**, ~1 s CPU inference. **Estimates only — not medical or dietary advice.**

This Space is the recognition engine of an Astrolab Group internship project; the full web app (upload → calories + macros for an adjustable portion, manual correction, session history) is a separate React frontend that calls this Space via `@gradio/client`. Backend structure of the original app ported from [Rishabh1925/foodvisionai](https://github.com/Rishabh1925/foodvisionai) (MIT).
