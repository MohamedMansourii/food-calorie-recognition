# AI Food & Calories Recognition

Upload one meal photo → the dominant food is identified (ViT fine-tuned on Food-101, 101 classes) → you get estimated **calories + protein/carbs/fat** for an adjustable portion. Built as a 4-week internship project at **Astrolab Group**, delivered demo-grade: no accounts, no stored user data.

> **Estimates only — not medical or dietary advice.** Every nutrition value is an average for a typical preparation of that dish.

## How it works

```
Browser (React + TS + Tailwind)                Flask API (Python)
┌─────────────────────────────┐   multipart   ┌──────────────────────────────┐
│ drag-drop / picker upload   │──────────────▶│ POST /api/analyze            │
│ preview + Replace           │               │  ├─ validate type/size       │
│ result screen               │◀──────────────│  ├─ ViT nateraw/food (top-3) │
│  ├─ food + confidence badge │     JSON      │  ├─ confidence policy        │
│  ├─ kcal + 3 macro cards    │               │  │   ≥0.70 ok               │
│  ├─ portion S/M/L + grams   │               │  │   0.35–0.70 low_conf     │
│  │   (client-side rescale)  │               │  │   <0.35 no_food          │
│  ├─ "Wrong food?" search ───┼──────────────▶│  └─ nutrition block          │
│  └─ session history         │               │ GET /api/foods?q=  (search)  │
└─────────────────────────────┘               │ GET /api/foods/<label>       │
                                              │ GET /api/health              │
                                              └───────────┬──────────────────┘
                                              data/foods.json (names+aliases)
                                              data/nutrition_table.json
                                              (per-100g macros, 101 classes)
```

Portion math: values are stored **per 100 g**; the UI rescales linearly on the client (`grams / 100 × per_100g`), so portion changes cost zero requests. Presets small/medium/large = 0.7 / 1.0 / 1.4 × each food's default portion.

## Run locally

Backend (Python 3.11 venv):

```bash
python -m venv .venv && .venv/Scripts/pip install --index-url https://download.pytorch.org/whl/cpu torch && .venv/Scripts/pip install -r backend/requirements.txt
```

```bash
.venv/Scripts/python backend/app.py
```

Frontend (dev, hot reload — proxies `/api` to :8000):

```bash
cd frontend && npm install && npm run dev
```

Or one URL (build once, Flask serves it): `cd frontend && npm run build`, then open http://localhost:8000.

First analyze call downloads the model (~350 MB) into the Hugging Face cache; afterwards it's fully local.

## Tests & evaluation

```bash
.venv/Scripts/python -m pytest backend/tests -q
```

```bash
.venv/Scripts/python scripts/fetch_samples.py
```

```bash
.venv/Scripts/python scripts/evaluate.py
```

`fetch_samples.py` streams 100 held-out Food-101 test images (20 common classes × 5); `evaluate.py` measures real accuracy/latency and writes [docs/accuracy-report.md](docs/accuracy-report.md).

## Measured accuracy

<!-- ACCURACY:BEGIN -->
| Metric | Value |
|---|---|
| Top-1 accuracy | **87.0%** (87/100) |
| Top-3 accuracy | **97.0%** (97/100) |
| Mean latency (CPU) | 1082 ms |

Measured on 100 held-out Food-101 test images (20 common classes × 5) on the dev laptop — consistent with the model's published ~89% over the full test set.
<!-- ACCURACY:END -->

Full tables: [docs/accuracy-report.md](docs/accuracy-report.md).

## Deploy (free tier)

```bash
docker build -t food-calories . && docker run -p 8000:8000 food-calories
```

One container serves everything (frontend baked in, model baked in). Works as-is on Render/Railway free tiers — set nothing but the port.

## Limitations (honest list)

- **Single dominant item only** — a full plate returns its most confident single dish (multi-item detection is listed as future work).
- **101 dishes** — the Food-101 vocabulary; anything else lands in "no confident match" + manual search.
- **HEIC/HEIF unsupported** — iPhone photos must be JPG/PNG/WebP/GIF (≤ 8 MB).
- **Nutrition values are per-100g averages** generated for the demo and flagged `needs_review` until manually checked against USDA ([docs/nutrition-review.md](docs/nutrition-review.md)); portions are user-adjusted assumptions, not measured from the image.
- In-session history only; refresh clears it (by design — no accounts, no stored data).

## Docs

| Doc | What's in it |
|---|---|
| [docs/decision-note.md](docs/decision-note.md) | Approach comparison (train vs fine-tuned vs API vs scaffold) + recommendation |
| [docs/accuracy-report.md](docs/accuracy-report.md) | Measured top-1/top-3, per-class, latency, confusions |
| [docs/architecture.md](docs/architecture.md) | Every file + full request flow, plain language |
| [docs/demo-script.md](docs/demo-script.md) | 8-minute walkthrough with fallback plan |
| [docs/learning-report.md](docs/learning-report.md) | What worked, what didn't, real numbers, next steps |
| [docs/decisions-log.md](docs/decisions-log.md) | Every autonomous judgment call made during the build |

## Attribution

Backend structure and upload UX ported from [Rishabh1925/foodvisionai](https://github.com/Rishabh1925/foodvisionai) (MIT — see [LICENSE](LICENSE)); model: [nateraw/food](https://huggingface.co/nateraw/food) (ViT-B/16 fine-tuned on [Food-101](https://www.vision.ee.ethz.ch/datasets_extra/food-101/)).
