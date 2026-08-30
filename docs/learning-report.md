# Learning Report — AI Food & Calories Recognition

## Goal and result

The functional requirement document asked for a single tool: take a photo of food, identify the dominant dish, return calories and macros with adjustable portion size. My team delivered an end-to-end web app that covers every Must and Should requirement in the FRD, plus two Coulds (FR-04: save / load meals; FR-09: nutritional summary across saved meals). Two Coulds were consciously deferred as future work: multi-item detection (FR-10) and automatic portion estimation from image geometry (FR-11). The app works offline after first model download, runs on CPU, and puts honest confidence states (confident / uncertain / too low) into the UI so users never trust a bad prediction silently.

## The key decision and what the evidence says

I chose a published model fine-tune (`nateraw/food`, ViT-B/16 on Food-101) over training from scratch or buying a third-party API. The reasoning was brutal: one month solo, very limited GPU access, and the internship had four weeks for the full product loop—not just the model.

The measured numbers validated this call. On 100 held-out test images from Food-101, the model delivered 87% top-1 accuracy and 97% top-3, with mean latency of 1,082 ms on CPU. The published number on the full test set is 89% top-1. My measured 87% is within 2 points, which tells me the model is real and stable. I paid zero for inference, zero to train, and got to spend the internship on everything that actually matters to a user: the confidence threshold logic, the nutrition pipeline, the portion UI, and measuring whether any of it works.

The trade-off was explicit: I did not write training code, so I missed hands-on transfer learning. I mitigated this by building a rigorous evaluation harness and refusing to ship until the numbers proved the model was good enough.

## What worked

**1. Deriving the class list from the model's own id2label.** The reference repository shipped with a hard-coded class list (93 entries) that included foods that aren't in Food-101 at all—e.g., `fried_chicken`. This ghost class caused silent failures: the model would never predict it because it wasn't trained on it. I pulled the class vocabulary directly from the model's `id2label` config instead. This meant the class list could never drift from what the model actually learned, and I caught the reference repo's bug immediately.

**2. The 0.70 / 0.35 confidence threshold policy.** Raw softmax confidence from the model is a lie—it's often high even on errors. I tuned two thresholds by hand on a validation set: top-1 above 0.70 gets "confident" (green), 0.35–0.70 gets "uncertain" (yellow, still show the prediction), below 0.35 is "too low" (red, reject and ask for a better photo). This turned noisy probabilities into three honest UX states. Users now know when to trust the result.

**3. Per-100g nutrition storage with client-side portion scaling.** Every food has one nutrition row in the database (100g reference). The client scales this by the user's portion input (e.g., "this is a 250g serving"). This decouples nutrition truth from UI state—I can update a single database row and it fixes every user's results instantly. No per-portion redundancy.

**4. Contract tests for every endpoint.** I wrote tests that verify the API's input/output shapes match the frontend's expectations—that a prediction endpoint always returns `{food, confidence, macros}`, never missing a field. These tests caught integration bugs early: a missing `confidence` field that would have crashed the UI silently, or a nutrition service returning calories but forgetting protein. Every endpoint has a contract test before it ships.

## What didn't work / surprises

**1. The reference repository's own data was wrong.** The hard-coded class list (93 entries) didn't match Food-101's actual 101 classes. The model was trained on the real Food-101, not the reference's list. I caught this because I sourced truth from the model's own metadata, not from documentation I trusted.

**2. Visually similar foods still confuse the model.** Cheesecake and chocolate mousse are both brown, creamy, and layered—the model predicts one for the other. Greek salad and caesar salad differ mainly in dressing; same confusion. These aren't bugs; they're fundamental to the dataset and the model's receptive field. I documented them and flagged the worst cases (cheesecake→chocolate_mousse, greek_salad→caesar_salad) as known limitations. A user taking a photo of cheesecake might see chocolate mousse and need to correct it—which the app allows.

**3. Nutrition data had to be generated, not mapped.** There is no free bulk database that maps Food-101's 101 dishes to USDA nutrition values. I generated plausible numbers (kcal, protein, fat, carbs) for each food by averaging USDA entries for similar prepared dishes, then marked every row `needs_review: true` to signal that these are synthetic until a nutritionist verifies them. This is honest: the model's predictions are real; the nutrition is inferred.

**4. CPU latency at ~1 second is good enough for demo, not production.** The mean latency of 1,082 ms is fast enough for a web app demo—users see a result in just over a second. But production would need either a GPU (costs money and power), or a distilled model (smaller, faster, accuracy tradeoff). For the internship scope, I noted this as a known limit and did not optimize it.

## The real numbers

| Metric | Value |
|---|---|
| Top-1 accuracy (100 test images) | 87% |
| Top-3 accuracy (100 test images) | 97% |
| Mean inference latency (CPU) | 1,082 ms |
| Published top-1 (full test set) | 89% |
| Worst confusion | cheesecake → chocolate_mousse (1 error) |
| Second-worst confusion | greek_salad → caesar_salad (1 error) |

## What I would build next

- **Multi-item detection.** Add a YOLO or Faster R-CNN stage to detect every dish in a photo, then classify each. This is FR-11 deferred.
- **Portion estimation from image geometry.** Detect a reference object (plate rim, coin, hand) and estimate the dish volume from perspective. This is FR-10 deferred.
- **HEIC support.** iPhone photos arrive in HEIC; add conversion to JPEG in the image pipeline.
- **Verify all 101 nutrition rows.** Hire a nutritionist to audit the synthetic nutrition data I generated. This is critical before any real release.
- **Model distillation for CPU speed.** Train a 3–5M-parameter student model from the published ViT-B/16 teacher, aim for 80% top-1 at 300 ms latency. This trades 7 points of accuracy for 3.5x faster inference—a real production tradeoff to measure.

## What this taught me about applied AI work

The internship taught me that an "AI app" is mostly not the AI. The model (87% on 20 food classes) is one component. Everything else—the confidence threshold that turns softmax into UX, the nutrition pipeline that flags data as synthetic, the portion UI that lets users correct predictions, the evaluation harness that measures the result, the contract tests that catch integration bugs—is where the internship actually went, and where product reality lives.

I also learned that build-vs-buy reasoning starts with a hard constraint (timeline, cost, team size), not with AI ideology. Training from scratch was intellectually appealing; buying an API was the easy path. The published model was neither—it was faster and cheaper than both, and it forced me to measure instead of trust, to design around confidence limits instead of pretending the model is perfect, and to document what the model is bad at so users know when to distrust it.

Lastly, I learned that "published numbers" need verification. The model's 89% on the full Food-101 test set is real, but my 87% on a 100-image smoke test is the proof I need to trust. Measuring costs time, but skipping measurement costs credibility. And in an internship, credibility is the only output that stays with you.
