# Technical Approach — Decision Note

The functional requirement document leaves the food-recognition engine open. This note compares four realistic approaches against the one-month solo timeline and recommends a model-agnostic approach using a pre-trained public fine-tune, freeing internship time for product logic, evaluation, and end-user experience.

## Options considered

### Option A — Train a CNN from scratch

Food-101 has 75,750 training images. Training a competitive classifier from scratch requires GPU-days, rigorous data augmentation, and ML tuning experience. Expected accuracy after one week of solo effort is realistically 40–60% top-1. Zero direct cost but highest implementation risk.

### Option B — Fine-tune a pretrained model

Fine-tune EfficientNet or ViT pretrained on ImageNet using Food-101. Expected 80–90% top-1 with 1–2 days of GPU time on Colab free tier (availability flaky). Medium effort, medium risk; teaches transfer learning as a core skill.

### Option C — Third-party food-recognition API

Integrate LogMeal, Clarifai, or Google Cloud Vision. Highest food coverage including multi-item meals. Per-call pricing and free-tier caps apply (LogMeal trial limited, Clarifai free tier 1,000 ops/month, GCV label detection is generic, not dish-level). No model ownership; demo depends on live internet and API keys. Lowest build effort but weakest learning value and live-demo dependency risk.

### Option D — Pretrained public model + open scaffold (CHOSEN)

Use the Hugging Face model `nateraw/food` (ViT-B/16 already fine-tuned on Food-101, ~89% published top-1) inside an MIT-licensed Flask+React scaffold, extended with a custom nutrition engine, confidence policy, and UI. Zero training cost, zero API cost, fully offline after first model download. Frees all four weeks for product logic, evaluation, and polish.

## Criteria matrix

| Criterion | A: from scratch | B: fine-tune | C: 3rd-party API | D: pretrained + scaffold |
|-----------|-----------------|--------------|------------------|--------------------------|
| Expected accuracy | 40–60% top-1 | 80–90% top-1 | 85–95% (multi-item) | ~89% top-1 (single-item) |
| Cost | $0 | $0–20 (Colab) | $50–500/month | $0 |
| Setup effort | Very high | Medium | Low | Low |
| Fit in remaining 3 weeks | Poor | Risky | Good | Excellent |
| Demo risk | High (accuracy) | Medium (training time) | High (API/internet) | Low |
| Learning value | Very high (ML) | High (transfer) | Low (API wrapper) | Medium (evals + product) |

## Recommendation

**Option D wins under the hard one-month solo constraint.** Accuracy comes free from the published fine-tune; internship time flows into the full product loop—confidence policy, nutrition mapping, portion-adjustment UX, and a real evaluation harness. The model download is one-time and offline-first, eliminating demo risk from network or API keys.

**Consciously given up:** no hands-on model training (mitigated by building a rigorous evaluation pipeline that still exercises ML measurement). The model vocabulary caps at 101 dishes and single-item meals only. If real-world photos prove weak, **fallback path:** Option C (Clarifai free tier) as a runtime backup, tested in Week 2.

## Decision-gate outcome

Presented end of Week 1; pending mentor review per FRD §9.
