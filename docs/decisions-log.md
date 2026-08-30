# Decisions Log

Every autonomous judgment call made during the 2-day build, in order. Format: **D-n — decision** · why · impact.

- **D-1 — Repo lives at `food-calorie-recognition/` inside the project folder; Python venv lives outside OneDrive at `C:\Users\manso\.venvs\foodcal`.** OneDrive locks/syncs tens of thousands of venv files and corrupts builds; keeping the env external keeps the synced repo light while the code stays in the project as instructed. Run scripts reference the venv path explicitly.
- **D-2 — Python 3.11 (not the also-installed 3.14).** PyTorch CPU wheels are guaranteed on 3.11; 3.14 support is not.
- **D-3 — Torch installed from the CPU-only index.** No CUDA GPU is assumed; CPU wheel is ~5× smaller — storage-friendly and sufficient for a demo (ViT inference ≈ 100–500 ms on CPU).
- **D-4 — Reference backend ported nearly 1:1; reference frontend ported as *pattern*, not code.** `foodvisionai`'s backend (Flask + `nateraw/food` ViT) is clean and small — kept its module structure (`app/model/config`). Its frontend is a Figma glassmorphism export carrying 40+ unused Radix/recharts/carousel dependencies, mock data, a Pixabay video background and a hard-coded HF Space URL — that is the "branding and dead code" the brief says to strip. I ported the drag-drop/picker/preview UX and the API-call pattern into a minimal React+TS+Vite+Tailwind app (2 runtime deps instead of ~45). MIT LICENSE kept, attribution in README.
- **D-5 — `reference/` clone deleted immediately after porting.** Per the storage directive: knowledge extracted → files removed. Attribution + LICENSE preserve provenance.
- **D-6 — 8 MB upload cap and the 0.70/0.35 confidence thresholds are config constants from day one** (`backend/config.py`), even though they belong to Phases 2/4 — avoids churn and keeps one source of truth.
- **D-7 — File-type rejection checks both extension and MIME, and unreadable image bytes also return 415.** A `.jpg`-named text file must not reach the model.
- **D-8 — Tailwind v4 via `@tailwindcss/vite`.** No tailwind.config / postcss files needed — fewer files, faster build.
- **D-9 — All bulk generation (data JSONs, doc first drafts) delegated to the `bulk-writer` subagent pinned to Haiku** per the CEO's token-economy directive; the main session only writes production code and refines docs.
- **D-10 — Charter note: the 12-agent agency workflow (G0–G6) is not used for this build.** The CEO's prompt specifies its own phase plan, forbids questions, and mandates a single cheap subagent; direct CEO instructions supersede the standing charter for this engagement.
