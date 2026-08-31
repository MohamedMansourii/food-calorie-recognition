"""Tunisian-dish classifier (second recognition engine) + merge policy.

Loads the locally trained MobileNetV3-Small (models/tunisian/, falling back to
the published HF hub copy). If neither exists, the app runs ViT-only — this
module never breaks the analyze path.

Open-set caution: a closed-vocabulary classifier always answers something, so
Tunisian candidates only LEAD when clearly confident, and are dropped entirely
below MIN_KEEP.
"""
import io
import os

import torch
from PIL import Image

from config import Config

WEIGHTS_LOCAL = os.path.join(Config.DATA_DIR, "..", "models", "tunisian", "tunisian_food_mnv3.pt")
HUB_REPO = os.environ.get("TUNISIAN_MODEL_REPO", "mansourismatic/tunisian-food-classifier")

LEAD_STRONG = 0.85   # may override even a confident ViT
LEAD_NORMAL = 0.55   # leads when ViT isn't confident
MIN_KEEP = 0.35      # below this a Tunisian candidate is discarded

_model = None
_classes: list[str] = []
_tf = None
_tried = False


def _load():
    global _model, _classes, _tf, _tried
    if _tried:
        return
    _tried = True
    try:
        from torchvision import models as tvm, transforms as T
        path = os.path.abspath(WEIGHTS_LOCAL)
        if not os.path.exists(path):
            from huggingface_hub import hf_hub_download
            path = hf_hub_download(HUB_REPO, "tunisian_food_mnv3.pt")
        ckpt = torch.load(path, map_location="cpu", weights_only=False)
        m = tvm.mobilenet_v3_small()
        m.classifier[3] = torch.nn.Linear(m.classifier[3].in_features, len(ckpt["classes"]))
        m.load_state_dict(ckpt["state_dict"])
        m.eval()
        _model = m
        _classes = ckpt["classes"]
        _tf = T.Compose([
            T.Resize(256), T.CenterCrop(224), T.ToTensor(),
            T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
        ])
        print(f"Tunisian classifier loaded ({len(_classes)} classes) from {path}")
    except Exception as e:  # missing file, no torchvision, offline…
        print(f"Tunisian classifier unavailable: {e}")


def available() -> bool:
    _load()
    return _model is not None


def candidates(image_bytes: bytes, top_k: int = 3) -> list[dict]:
    """Top Tunisian candidates above MIN_KEEP, best first (possibly empty)."""
    _load()
    if _model is None:
        return []
    image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
    x = _tf(image).unsqueeze(0)
    with torch.no_grad():
        probs = torch.nn.functional.softmax(_model(x)[0], dim=-1)
    top = torch.topk(probs, min(top_k, len(_classes)))
    return [
        {"label": _classes[int(i)], "confidence": round(float(p), 4), "source": "tunisian"}
        for i, p in zip(top.indices, top.values)
        if float(p) >= MIN_KEEP
    ]


def merge(vit_preds: list[dict], tun_preds: list[dict]) -> list[dict]:
    """Combine both engines into a best-first top-3 (dedup by label)."""
    for p in vit_preds:
        p.setdefault("source", "food101")
    if not tun_preds:
        return vit_preds[:3]
    vit_top = vit_preds[0]["confidence"]
    tun_top = tun_preds[0]["confidence"]
    if tun_top >= LEAD_STRONG or (tun_top >= LEAD_NORMAL and vit_top < Config.CONFIDENT_THRESHOLD):
        ordered = tun_preds + vit_preds
    else:
        ordered = [vit_preds[0]] + tun_preds + vit_preds[1:]
    seen, out = set(), []
    for p in ordered:
        if p["label"] not in seen:
            seen.add(p["label"])
            out.append(p)
    return out[:3]
