# Architecture — Food Calorie Recognition

## The 30-second version

A React web app (frontend) lets you upload a meal photo. The photo travels to a Flask backend as binary data, which loads it into a Vision Transformer neural network (ViT — an ML model that classifies images by looking at small patches of pixels) pretrained on 101 food types. The model outputs three guesses with confidence scores (0 to 1, where 1 = certain). A policy assigns a status: "ok" if top guess is 70%+ confident, "low_confidence" if 35%–70%, or "no_food" if below 35%. If confident enough, the app looks up per-100g nutrition data (calories, protein, carbs, fat) from a JSON file, scales it by your portion size, and renders the result with portion controls. Clicking "Medium" recalculates instantly on the browser—no server trip.

---

## File map

| File | What it does |
|---|---|
| **Backend** | |
| `backend/app.py` | Flask web server: HTTP routes for `/api/analyze` (POST image), `/api/foods?q=` (search), `/api/foods/<label>` (nutrition lookup), `/api/health` (status check), plus SPA fallback for the frontend. |
| `backend/model.py` | Loads the ViT model from Hugging Face, resizes images to 224×224 pixels, runs inference (forward pass through the neural network), extracts softmax probabilities, and returns top-3 predictions with latency. |
| `backend/nutrition.py` | Reads `data/foods.json` (food names + aliases) and `data/nutrition_table.json` (per-100g macros + default portions). Searches foods by substring, scales nutrition linearly by grams, returns portion presets (small/medium/large). |
| `backend/config.py` | Centralized settings: model name, file upload limits (8 MB), confidence thresholds (0.70 / 0.35), portion multipliers (0.7× / 1.0× / 1.4×), paths to data files and frontend build. |
| **Frontend** | |
| `frontend/src/App.tsx` | App shell: manages file selection, upload, analysis, results, session history, and error states. Calls API client functions; passes data to child components. |
| `frontend/src/api.ts` | HTTP client: `analyzeImage()` POSTs FormData to `/api/analyze`, `searchFoods()` GETs from `/api/foods?q=`, `getNutrition()` GETs from `/api/foods/<label>`. Defines TypeScript types for all responses. |
| `frontend/src/components/UploadArea.tsx` | Drag-and-drop zone or file picker; validates MIME type and size client-side (8 MB max) before sending to App. |
| `frontend/src/components/ConfidenceBadge.tsx` | Small colored badge showing model confidence as a percentage (green ≥70%, amber 35–70%, red <35%). |
| `frontend/src/components/PortionControl.tsx` | Three preset buttons (S/M/L) and a free-form gram input; calls a local scaling function—no server request. |
| `frontend/src/components/CorrectionSearch.tsx` | Hidden until the user clicks "Wrong food?"; debounced text search over food names and aliases via `/api/foods?q=`. |
| `frontend/src/components/ResultView.tsx` | Single-screen result card: photo thumbnail, food name, confidence, three-card macro breakdown (protein/carbs/fat), portion control, and manual correction button. |
| `frontend/src/components/HistorySidebar.tsx` | Right sidebar showing this session's analyzed meals (photo thumbnail, name, kcal, portion, time). Cleared on page refresh. |
| **Data** | |
| `data/foods.json` | List of 101 food objects: `{label, display_name, aliases, ...}`. Labels match model class names (e.g., `"pizza"`). |
| `data/nutrition_table.json` | Nutrition per-100g for each food: `{label: {kcal, protein_g, carbs_g, fat_g, default_portion_g}}`. |
| **Scripts** | |
| `scripts/fetch_samples.py` | Streams 5 real images per Food-101 class (20 classes = 100 images) from Hugging Face dataset hub into `sample_photos/`. Used for testing and accuracy measurement. |
| `scripts/evaluate.py` | Runs the model on every image in `sample_photos/`, computes top-1/top-3 accuracy, per-class stats, mean latency, and confusion matrix; writes results to `docs/accuracy-report.md`. |
| **Deployment** | |
| `Dockerfile` | Two-stage build: (1) Node container builds React → `frontend/dist`, (2) Python container installs PyTorch + dependencies, copies backend, data, and frontend dist, bakes the model into the image, runs gunicorn on port 8000. |

---

## The life of one request

1. **User picks a photo** — UploadArea validates MIME type and file size (8 MB) client-side. If valid, App shows a preview and an "Analyze" button.

2. **User clicks "Analyze"** — App.tsx calls `analyzeImage(file)` from api.ts, which creates FormData with the File and POSTs to `/api/analyze`.

3. **Flask checks the file** — app.py's `analyze()` route verifies the file exists, extension is in the allowed list, and MIME type is an image. Returns 415 (Unsupported Media Type) if not.

4. **Image bytes → PIL → tensor** — model.py's `predict()` opens the byte stream with PIL (Python Imaging Library), converts to RGB if needed, passes it to the ViT processor (which resizes to 224×224 pixels and normalizes pixel values to a standard range).

5. **Forward pass** — The ViT model (downloaded from Hugging Face) runs the tensor through 12 transformer blocks, outputting raw logits (one score per class). Softmax converts logits to probabilities (sum to 1, each 0–1). TopK grabs the three highest.

6. **Confidence policy** — app.py's `_build_result()` checks the top prediction's confidence: ≥0.70 → `status: "ok"`, 0.35–0.70 → `"low_confidence"`, <0.35 → `"no_food"`.

7. **Nutrition lookup** — nutrition.py's `nutrition_block()` looks up the winning food label in `nutrition_table.json`, retrieves the per-100g macros and default portion size. If status is `"no_food"`, nutrition is None.

8. **Response to browser** — Flask returns JSON: `{status, predictions: [...], nutrition: {...} or null, latency_ms, disclaimer}`.

9. **React renders result** — ResultView receives the response, shows the food name + confidence badge, displays a big kcal number, and three macro cards at the default portion size.

10. **User adjusts portion** — PortionControl calls a local `scale()` function in ResultView (no server trip): multiplies per-100g values by `(grams / 100)` and re-renders.

11. **User clicks "Wrong food?"** — CorrectionSearch appears. Typing queries `/api/foods?q=` (debounced 250 ms), which nutrition.py searches over food names + aliases and returns up to 10 matches.

12. **User picks a correction** — App calls `getNutrition(label)` via `/api/foods/<label>`, which returns a fresh nutrition block for that food. ResultView re-renders with the new macros.

13. **Session history** — Each analysis (if nutrition was found) is added to the history array as a HistoryEntry: thumbnail URL, display name, kcal, portion grams, and timestamp. The sidebar renders all entries.

---

## Three deep ideas worth understanding

### 1. Transfer learning: why ViT "just works"
The ViT model was trained on **Food-101**, a dataset of 101 common foods with ~1,000 images each. That training learned to detect visual patterns (cheese, lettuce, bread shape, color, texture). When you upload a pizza, the model applies those learned patterns to your photo without re-learning. This is called **transfer learning**—reusing a pretrained model instead of training from scratch. Upside: ~89% accuracy on unseen pizzas for free. Downside: if your food is not in the 101 classes (e.g., a Tunisian dish), the model guesses the closest match and will be wrong.

### 2. Confidence thresholds as UX design
The three-state system (ok / low_confidence / no_food) is a **product decision**, not just ML logic. A raw softmax might say 42% for pizza, 38% for flatbread, 20% for other. That's mathematically true but terrifying to show the user ("I'm 42% sure it's pizza"). Instead, the policy says: "If I'm 70%+ sure, tell the user I'm confident. If I'm 35–70% sure, tell them I'm unsure and show alternatives (flatbread might be right too). If I'm <35% sure, admit I have no idea and ask the user to pick manually." This is honest communication—uncertainty gets matched to how the user sees it.

### 3. Per-100g as the nutrition contract
All macros live as per-100g in the database. The frontend scales them **linearly** by `(portion_g / 100)`. This contract is simple, cacheable, and scalable: change the portion from 150 g to 200 g, and multiply by 2× — no server round-trip needed. The math is exact only if macros are uniform throughout the food (they're not: the skin of a chicken wing has more fat than the meat), but it's good enough for estimates, and it stays fast.

---

## Where things run

### Development mode
- **Frontend** runs at `http://localhost:5173` (Vite dev server).
- **Backend** runs at `http://localhost:8000` (Flask dev server, `python backend/app.py`).
- Browser requests to `/api/*` are proxied to `localhost:8000` by Vite (via `vite.config.ts`).
- Model is loaded on first request to `/api/analyze` (~2 seconds the first time, then cached in RAM).

### Packaged mode (Docker / production)
- **Dockerfile builds in two stages:**
  1. Node container compiles React → `frontend/dist/` (static HTML + JS bundles).
  2. Python container installs dependencies, copies both backend and frontend dist, preloads the model, runs gunicorn.
- **One URL**: `http://localhost:8000` serves both the API and the frontend SPA (Flask's SPA fallback route `/` serves `index.html` for any path not under `/api/`).
- **Gunicorn** (a Python HTTP server) runs a single worker process with the model preloaded in RAM before accepting requests (faster first request, no thrashing).
- **Model is baked into the image**: Dockerfile's RUN step downloads the 350 MB ViT model and caches it in the Docker layer, so runtime containers don't download it—they boot in seconds.
- Suitable for free tiers (Render, Railway, Fly.io) that give 512 MB–1 GB RAM and no GPU.

---

**Total flow:** Photo → validation → FormData POST → Flask → PIL + ViT → softmax → policy → nutrition lookup → JSON response → React render → portion scales client-side → manual search if needed → next photo.
