"""Fine-tune a Tunisian-dish classifier from three public Roboflow datasets.

Datasets (all CC BY 4.0, downloaded as zips into tn_datasets/):
  pfemrds  detection-tunisian-food-2025 v5   (YOLOv8 boxes, 11 classes)
  seg      tunisian-food-seg v3             (COCO polygons+boxes, 21 classes)
  tnex     dataset-tn-annotated-exemples-2  (YOLOv8 boxes, 10 classes)

Pipeline: map dataset classes -> app food slugs -> build classification crops
(bbox + 15% pad, plus the full image labeled by its largest box) -> dedupe by
image hash across datasets -> fine-tune torchvision MobileNetV3-Small -> eval
-> save weights + labels + docs/tunisian-model-report.md.

Run:  <venv>/python scripts/train_tunisian.py [--epochs 12]
"""
import argparse
import hashlib
import io
import json
import os
import random
import sys
from collections import Counter, defaultdict
from datetime import date

import torch
import torch.nn as nn
from PIL import Image
from torch.utils.data import DataLoader, Dataset
from torchvision import models, transforms

REPO = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
RAW = os.path.join(REPO, "tn_datasets")
OUT = os.path.join(REPO, "models", "tunisian")
REPORT = os.path.join(REPO, "docs", "tunisian-model-report.md")
SEED = 42

# dataset class name -> app slug (None = excluded on purpose)
MAPPINGS = {
    "pfemrds": {
        "Asida-Zkoukou": "assida_zgougou", "Brik": "brik", "Chakchouka": "chakchouka",
        "Chorba": "chorba", "Couscous": "couscous", "Frecasse": "fricasse",
        "Harissa": "harissa", "Kamouniya": "kamounia", "Lablaby": "lablabi",
        "Melloukhia": "mloukhiya", "Salade-Mechweya": "salade_mechouia",
    },
    "seg": {
        "baklawa": "baklava", "bambalouni": "bambalouni", "brik": "brik",
        "chorba": "chorba", "couscous": "couscous", "fricasse": "fricasse",
        "kafteji": "kafteji", "lablebi": "lablabi", "makroud": "makroudh",
        "makrouna": "makrouna", "merguez": "merguez", "mloukhiya": "mloukhiya",
        "ojja": "ojja", "salade mechwia": "salade_mechouia", "tajine": "tajine_tunisien",
        # ingredient classes excluded: fish/chicken/egg/lamb/thon/vegetables
    },
    "tnex": {
        "asida-zkoukou": "assida_zgougou", "brik": "brik", "kamouniya": "kamounia",
        "kouskous": "couscous", "lablaby": "lablabi", "makarouna": "makrouna",
        "mloukhiya": "mloukhiya", "slata mechwiya": "salade_mechouia",
        # excluded: "coktail hlou" (drink), "Kskrout kafteji" (sandwich variant)
    },
}


def find_split_dirs(root):
    """Return {split_name: dir} for train/valid/test dirs found anywhere under root."""
    out = {}
    for dirpath, dirnames, _ in os.walk(root):
        for d in dirnames:
            if d in ("train", "valid", "test"):
                out.setdefault(d, os.path.join(dirpath, d))
    return out


def yolo_samples(ds_root, mapping):
    """Yield (split, image_path, [(slug, (l,t,r,b))]) from a YOLOv8 export."""
    yaml_path = None
    for dirpath, _, files in os.walk(ds_root):
        if "data.yaml" in files:
            yaml_path = os.path.join(dirpath, "data.yaml")
            break
    names = []
    with open(yaml_path, encoding="utf-8") as f:
        text = f.read()
    # names: ['a', 'b'] on one line, or a block list
    import re
    m = re.search(r"names:\s*\[(.*?)\]", text, re.S)
    if m:
        names = [n.strip().strip("'\"") for n in m.group(1).split(",")]
    else:
        block = re.search(r"names:\s*\n((?:\s*-\s*.+\n?)+)", text)
        names = [ln.split("-", 1)[1].strip().strip("'\"") for ln in block.group(1).strip().splitlines()]

    for split, sdir in find_split_dirs(ds_root).items():
        img_dir, lbl_dir = os.path.join(sdir, "images"), os.path.join(sdir, "labels")
        if not os.path.isdir(img_dir):
            continue
        for name in os.listdir(img_dir):
            if not name.lower().endswith((".jpg", ".jpeg", ".png")):
                continue
            lbl = os.path.join(lbl_dir, os.path.splitext(name)[0] + ".txt")
            boxes = []
            if os.path.exists(lbl):
                with Image.open(os.path.join(img_dir, name)) as im:
                    W, H = im.size
                for line in open(lbl, encoding="utf-8"):
                    parts = line.split()
                    if len(parts) < 5:
                        continue
                    cls = names[int(parts[0])] if int(parts[0]) < len(names) else None
                    slug = mapping.get(cls)
                    if not slug:
                        continue
                    cx, cy, w, h = (float(v) for v in parts[1:5])
                    boxes.append((slug, ((cx - w / 2) * W, (cy - h / 2) * H,
                                         (cx + w / 2) * W, (cy + h / 2) * H)))
            if boxes:
                yield split, os.path.join(img_dir, name), boxes


def coco_samples(ds_root, mapping):
    for split, sdir in find_split_dirs(ds_root).items():
        ann_path = os.path.join(sdir, "_annotations.coco.json")
        if not os.path.exists(ann_path):
            continue
        coco = json.load(open(ann_path, encoding="utf-8"))
        cats = {c["id"]: c["name"] for c in coco["categories"]}
        imgs = {i["id"]: i["file_name"] for i in coco["images"]}
        by_img = defaultdict(list)
        for a in coco["annotations"]:
            slug = mapping.get(cats.get(a["category_id"]))
            if not slug:
                continue
            x, y, w, h = a["bbox"]
            by_img[a["image_id"]].append((slug, (x, y, x + w, y + h)))
        for img_id, boxes in by_img.items():
            path = os.path.join(sdir, imgs[img_id])
            if os.path.exists(path):
                yield split, path, boxes


def build_crops():
    """Materialize dedup'd classification crops; returns (index, stats)."""
    random.seed(SEED)
    seen_hashes = set()
    index = {"train": [], "val": []}
    stats = Counter()
    crops_dir = os.path.join(RAW, "_crops")
    os.makedirs(crops_dir, exist_ok=True)

    sources = [("pfemrds", yolo_samples), ("seg", coco_samples), ("tnex", yolo_samples)]
    n = 0
    for ds_name, reader in sources:
        ds_root = os.path.join(RAW, ds_name)
        for split, img_path, boxes in reader(ds_root, MAPPINGS[ds_name]):
            with open(img_path, "rb") as f:
                digest = hashlib.md5(f.read()).hexdigest()
            if digest in seen_hashes:
                stats["dup_skipped"] += 1
                continue
            seen_hashes.add(digest)
            bucket = "train" if split == "train" else "val"
            try:
                im = Image.open(img_path).convert("RGB")
            except Exception:
                stats["unreadable"] += 1
                continue
            W, H = im.size
            largest = max(boxes, key=lambda b: (b[1][2] - b[1][0]) * (b[1][3] - b[1][1]))
            picks = [(slug, box, "crop") for slug, box in boxes] + [(largest[0], None, "full")]
            for slug, box, kind in picks:
                if kind == "crop":
                    l, t, r, b = box
                    pw, ph = (r - l) * 0.15, (b - t) * 0.15
                    region = im.crop((max(0, l - pw), max(0, t - ph),
                                      min(W, r + pw), min(H, b + ph)))
                    if region.width < 48 or region.height < 48:
                        stats["tiny_skipped"] += 1
                        continue
                else:
                    region = im
                region.thumbnail((288, 288))
                out_name = f"{n:06d}_{slug}.jpg"
                region.save(os.path.join(crops_dir, out_name), "JPEG", quality=88)
                index[bucket].append((out_name, slug))
                stats[f"{bucket}_samples"] += 1
                stats[f"class_{slug}"] += 1
                n += 1
    return index, stats, crops_dir


class CropDataset(Dataset):
    def __init__(self, items, crops_dir, classes, train):
        self.items, self.dir, self.classes = items, crops_dir, classes
        self.idx = {c: i for i, c in enumerate(classes)}
        self.tf = transforms.Compose(
            ([transforms.RandomResizedCrop(224, scale=(0.6, 1.0)),
              transforms.RandomHorizontalFlip(),
              transforms.ColorJitter(0.2, 0.2, 0.15)] if train else
             [transforms.Resize(256), transforms.CenterCrop(224)])
            + [transforms.ToTensor(),
               transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])]
        )

    def __len__(self):
        return len(self.items)

    def __getitem__(self, i):
        name, slug = self.items[i]
        img = Image.open(os.path.join(self.dir, name)).convert("RGB")
        return self.tf(img), self.idx[slug]


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--epochs", type=int, default=12)
    ap.add_argument("--batch", type=int, default=32)
    args = ap.parse_args()

    torch.manual_seed(SEED)
    random.seed(SEED)

    print("Building crops from the three datasets…")
    index, stats, crops_dir = build_crops()
    classes = sorted({slug for _, slug in index["train"] + index["val"]})
    print(f"classes ({len(classes)}): {classes}")
    print(f"train={len(index['train'])} val={len(index['val'])} "
          f"dups={stats['dup_skipped']} tiny={stats['tiny_skipped']}")

    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = models.mobilenet_v3_small(weights=models.MobileNet_V3_Small_Weights.IMAGENET1K_V1)
    model.classifier[3] = nn.Linear(model.classifier[3].in_features, len(classes))
    model.to(device)

    train_dl = DataLoader(CropDataset(index["train"], crops_dir, classes, True),
                          batch_size=args.batch, shuffle=True, num_workers=0)
    val_dl = DataLoader(CropDataset(index["val"], crops_dir, classes, False),
                        batch_size=args.batch, shuffle=False, num_workers=0)

    opt = torch.optim.AdamW(model.parameters(), lr=3e-4, weight_decay=1e-4)
    sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, T_max=args.epochs)
    loss_fn = nn.CrossEntropyLoss(label_smoothing=0.1)

    best_acc, best_state = 0.0, None
    for epoch in range(args.epochs):
        model.train()
        total = 0.0
        for x, y in train_dl:
            x, y = x.to(device), y.to(device)
            opt.zero_grad()
            loss = loss_fn(model(x), y)
            loss.backward()
            opt.step()
            total += float(loss)
        sched.step()

        model.eval()
        top1 = top3 = seen = 0
        per_class = defaultdict(lambda: [0, 0])  # hits, total
        with torch.no_grad():
            for x, y in val_dl:
                logits = model(x.to(device)).cpu()
                order = logits.argsort(dim=1, descending=True)
                for row, truth in zip(order, y):
                    seen += 1
                    per_class[classes[truth]][1] += 1
                    if row[0] == truth:
                        top1 += 1
                        per_class[classes[truth]][0] += 1
                    if truth in row[:3]:
                        top3 += 1
        acc = top1 / max(seen, 1)
        print(f"epoch {epoch + 1}/{args.epochs} loss={total / len(train_dl):.3f} "
              f"val top1={100 * acc:.1f}% top3={100 * top3 / max(seen, 1):.1f}%")
        if acc > best_acc:
            best_acc = acc
            best_state = {k: v.cpu().clone() for k, v in model.state_dict().items()}
            best_metrics = {"top1": acc, "top3": top3 / max(seen, 1),
                            "per_class": {c: tuple(v) for c, v in per_class.items()}}

    os.makedirs(OUT, exist_ok=True)
    torch.save({"arch": "mobilenet_v3_small", "state_dict": best_state, "classes": classes},
               os.path.join(OUT, "tunisian_food_mnv3.pt"))
    json.dump({"classes": classes}, open(os.path.join(OUT, "labels.json"), "w"))

    lines = [
        "# Tunisian Dish Classifier — training report",
        "",
        f"Trained {date.today().isoformat()}: MobileNetV3-Small (ImageNet init) fine-tuned on "
        f"{len(index['train'])} training / {len(index['val'])} validation samples built from three "
        "public CC-BY-4.0 Roboflow datasets (pfemrds/detection-tunisian-food-2025 v5, "
        "mariems/tunisian-food-seg v3, working-llaze/dataset-tn-annotated-exemples-2 v1). "
        f"{stats['dup_skipped']} cross-dataset duplicate images removed by hash.",
        "",
        "## Validation results (best epoch)",
        "",
        "| Metric | Value |",
        "|---|---|",
        f"| Top-1 accuracy | **{100 * best_metrics['top1']:.1f}%** |",
        f"| Top-3 accuracy | **{100 * best_metrics['top3']:.1f}%** |",
        f"| Classes | {len(classes)} |",
        "",
        "## Per-class (top-1 hits / val samples)",
        "",
        "| Class | Top-1 |",
        "|---|---|",
    ]
    for c in classes:
        hits, tot = best_metrics["per_class"].get(c, (0, 0))
        lines.append(f"| {c} | {hits}/{tot} |")
    lines += [
        "",
        "## Notes",
        "- Samples are bbox crops (15% pad) plus each image labeled by its largest box;",
        "  validation uses the datasets' own valid/test splits, deduplicated across datasets.",
        "- Excluded classes: ingredient labels (fish/chicken/egg/lamb/thon/vegetables),",
        "  'coktail hlou' (drink), 'Kskrout kafteji' (sandwich variant).",
        "- Student-collected datasets: expect label noise; treat numbers as demo-grade.",
    ]
    open(REPORT, "w", encoding="utf-8").write("\n".join(lines) + "\n")
    print(f"\nBest val top-1 {100 * best_acc:.1f}% -> {OUT} + {REPORT}")


if __name__ == "__main__":
    sys.exit(main() or 0)
