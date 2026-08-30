"""Evaluate the model on sample_photos/ and write docs/accuracy-report.md.

Measures real top-1 / top-3 accuracy, per-class results, mean latency and the
worst confusions. Every number in the project's documents comes from here.

Run:  <venv>/python scripts/evaluate.py
"""
import os
import statistics
import sys
from collections import Counter
from datetime import date

REPO_ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(REPO_ROOT, "backend"))

from model import get_model  # noqa: E402

SAMPLES = os.path.join(REPO_ROOT, "sample_photos")
REPORT = os.path.join(REPO_ROOT, "docs", "accuracy-report.md")


def main() -> int:
    if not os.path.isdir(SAMPLES):
        print("No sample_photos/ — run scripts/fetch_samples.py first.")
        return 1

    print("Loading model…")
    model = get_model()

    per_class: dict[str, dict] = {}
    latencies: list[float] = []
    confusions: Counter = Counter()
    total = top1_hits = top3_hits = 0

    for cls in sorted(os.listdir(SAMPLES)):
        cls_dir = os.path.join(SAMPLES, cls)
        if not os.path.isdir(cls_dir):
            continue
        stats = per_class.setdefault(cls, {"n": 0, "top1": 0, "top3": 0})
        for name in sorted(os.listdir(cls_dir)):
            if not name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            with open(os.path.join(cls_dir, name), "rb") as f:
                preds, latency_ms = model.predict(f.read(), top_k=3)
            latencies.append(latency_ms)
            labels = [p["label"] for p in preds]
            stats["n"] += 1
            total += 1
            if labels[0] == cls:
                stats["top1"] += 1
                top1_hits += 1
            else:
                confusions[(cls, labels[0])] += 1
            if cls in labels:
                stats["top3"] += 1
                top3_hits += 1
        print(f"  {cls}: {stats['top1']}/{stats['n']} top-1")

    top1 = 100 * top1_hits / total
    top3 = 100 * top3_hits / total
    mean_ms = statistics.mean(latencies)
    median_ms = statistics.median(latencies)

    lines = [
        "# Accuracy Report — measured, not estimated",
        "",
        f"Model `nateraw/food` (ViT-B/16 fine-tuned on Food-101) evaluated {date.today().isoformat()} "
        f"on {total} real images from the Food-101 evaluation split "
        f"({len(per_class)} common classes x {total // max(len(per_class), 1)} images), CPU inference on the dev laptop.",
        "",
        "## Overall",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Top-1 accuracy | **{top1:.1f}%** ({top1_hits}/{total}) |",
        f"| Top-3 accuracy | **{top3:.1f}%** ({top3_hits}/{total}) |",
        f"| Mean latency | {mean_ms:.0f} ms |",
        f"| Median latency | {median_ms:.0f} ms |",
        "",
        "## Per-class (top-1 / top-3 out of 5)",
        "",
        "| Class | Top-1 | Top-3 |",
        "|---|---|---|",
    ]
    for cls, s in sorted(per_class.items()):
        lines.append(f"| {cls} | {s['top1']}/{s['n']} | {s['top3']}/{s['n']} |")

    lines += ["", "## Worst confusions (true → predicted)", ""]
    if confusions:
        lines += ["| True class | Predicted | Count |", "|---|---|---|"]
        for (true_cls, pred), n in confusions.most_common(10):
            lines.append(f"| {true_cls} | {pred} | {n} |")
    else:
        lines.append("No top-1 errors in this sample.")

    lines += [
        "",
        "## Notes",
        "",
        "- Images come from the held-out Food-101 evaluation split — the model never saw them in training.",
        "- 5 images/class is a smoke-test sample, not a benchmark; the model's published Food-101 "
        "top-1 is ~89% over the full 25,250-image test set.",
        "- Latency is single-image CPU inference inside the Flask process (no batching, no GPU).",
    ]

    os.makedirs(os.path.dirname(REPORT), exist_ok=True)
    with open(REPORT, "w", encoding="utf-8") as f:
        f.write("\n".join(lines) + "\n")
    print(f"\nTop-1 {top1:.1f}% | Top-3 {top3:.1f}% | mean {mean_ms:.0f} ms -> {REPORT}")
    return 0


if __name__ == "__main__":
    sys.exit(main())
