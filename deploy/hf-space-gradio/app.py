"""Model endpoint Space: meal photo -> top-3 predictions (Food-101 + Tunisian).

Engines, merged into one top-3:
  1. ViT fine-tuned on Food-101 (nateraw/food) — always on (ZeroGPU).
  2. Own Tunisian classifier — MobileNetV3-Small fine-tuned on three public
     CC-BY-4.0 Roboflow datasets, loaded from the HF hub (CPU, ~5 ms).
  3. Optional: Roboflow-hosted YOLOv8s detector as an extra Tunisian source,
     active only when the ROBOFLOW_API_KEY Space secret is set.

Open-set policy: Tunisian candidates only lead when clearly confident
(closed-vocabulary classifiers always answer something).
"""
import base64
import io
import os
import time

import spaces  # ZeroGPU: must be imported before torch CUDA use
import gradio as gr
import requests
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification

MODEL = "nateraw/food"
processor = AutoImageProcessor.from_pretrained(MODEL)
model = AutoModelForImageClassification.from_pretrained(MODEL)
model.eval()  # CPU on purpose: ZeroGPU charges per-visitor GPU quota; CPU is ~1 s and unlimited

LEAD_STRONG = 0.85
LEAD_NORMAL = 0.55
MIN_KEEP = 0.35
VIT_CONFIDENT = 0.70

# --- own Tunisian classifier (CPU) ----------------------------------------
TUN_REPO = os.environ.get("TUNISIAN_MODEL_REPO", "mansourismatic/tunisian-food-classifier")
tun_model, tun_classes, tun_tf = None, [], None
try:
    from huggingface_hub import hf_hub_download
    from torchvision import models as tvm, transforms as T

    _ckpt = torch.load(hf_hub_download(TUN_REPO, "tunisian_food_mnv3.pt"),
                       map_location="cpu", weights_only=False)
    tun_model = tvm.mobilenet_v3_small()
    tun_model.classifier[3] = torch.nn.Linear(
        tun_model.classifier[3].in_features, len(_ckpt["classes"]))
    tun_model.load_state_dict(_ckpt["state_dict"])
    tun_model.eval()
    tun_classes = _ckpt["classes"]
    tun_tf = T.Compose([
        T.Resize(256), T.CenterCrop(224), T.ToTensor(),
        T.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    print(f"Tunisian classifier loaded: {len(tun_classes)} classes")
except Exception as e:
    print(f"Tunisian classifier unavailable: {e}")

# --- optional Roboflow-hosted detector ------------------------------------
RF_KEY = os.environ.get("ROBOFLOW_API_KEY", "")
RF_MODEL = os.environ.get("ROBOFLOW_MODEL", "detection-tunisian-food-2025/5")
RF_CLASS_TO_SLUG = {
    "Asida-Zkoukou": "assida_zgougou", "Brik": "brik", "Chakchouka": "chakchouka",
    "Chorba": "chorba", "Couscous": "couscous", "Frecasse": "fricasse",
    "Harissa": "harissa", "Kamouniya": "kamounia", "Lablaby": "lablabi",
    "Melloukhia": "mloukhiya", "Salade-Mechweya": "salade_mechouia",
}


@spaces.GPU
def _gpu_placeholder():
    """Never called. Exists only to satisfy ZeroGPU's startup check —
    inference deliberately runs on CPU so anonymous visitors never burn
    ZeroGPU quota (a demo must not die mid-presentation)."""


def vit_classify(image):
    inputs = processor(images=image, return_tensors="pt")
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.nn.functional.softmax(logits[0], dim=-1)
    top = torch.topk(probs, 3)
    return [
        {"label": model.config.id2label[int(i)], "confidence": round(float(p), 4), "source": "food101"}
        for i, p in zip(top.indices.cpu(), top.values.cpu())
    ]


def tunisian_own(image):
    if tun_model is None:
        return []
    x = tun_tf(image).unsqueeze(0)
    with torch.no_grad():
        probs = torch.nn.functional.softmax(tun_model(x)[0], dim=-1)
    top = torch.topk(probs, min(3, len(tun_classes)))
    return [
        {"label": tun_classes[int(i)], "confidence": round(float(p), 4), "source": "tunisian"}
        for i, p in zip(top.indices, top.values) if float(p) >= MIN_KEEP
    ]


def tunisian_roboflow(image):
    if not RF_KEY:
        return []
    buf = io.BytesIO()
    image.save(buf, format="JPEG", quality=90)
    payload = base64.b64encode(buf.getvalue()).decode()
    for host in ("https://detect.roboflow.com", "https://serverless.roboflow.com"):
        try:
            r = requests.post(f"{host}/{RF_MODEL}", params={"api_key": RF_KEY}, data=payload,
                              headers={"Content-Type": "application/x-www-form-urlencoded"},
                              timeout=20)
            if r.status_code != 200:
                continue
            best = {}
            for p in r.json().get("predictions", []):
                slug = RF_CLASS_TO_SLUG.get(p.get("class"))
                if slug:
                    best[slug] = max(best.get(slug, 0.0), float(p["confidence"]))
            return [{"label": s, "confidence": round(c, 4), "source": "tunisian"}
                    for s, c in best.items() if c >= MIN_KEEP]
        except Exception:
            continue
    return []


def merge(vit_preds, tun_preds):
    if not tun_preds:
        return vit_preds[:3]
    tun_top = tun_preds[0]["confidence"]
    vit_top = vit_preds[0]["confidence"]
    if tun_top >= LEAD_STRONG or (tun_top >= LEAD_NORMAL and vit_top < VIT_CONFIDENT):
        ordered = tun_preds + vit_preds
    else:
        ordered = [vit_preds[0]] + tun_preds + vit_preds[1:]
    seen, out = set(), []
    for p in ordered:
        if p["label"] not in seen:
            seen.add(p["label"])
            out.append(p)
    return out[:3]


def classify(image):
    if image is None:
        return {"error": "No image provided."}
    t0 = time.perf_counter()
    image = image.convert("RGB")
    vit_preds = vit_classify(image)

    # combine both Tunisian sources by max confidence per dish
    combined = {}
    for p in tunisian_own(image) + tunisian_roboflow(image):
        cur = combined.get(p["label"])
        if cur is None or p["confidence"] > cur["confidence"]:
            combined[p["label"]] = p
    tun_preds = sorted(combined.values(), key=lambda d: -d["confidence"])

    return {
        "predictions": merge(vit_preds, tun_preds),
        "engines": {"food101": True, "tunisian_own": tun_model is not None,
                    "tunisian_roboflow": bool(RF_KEY)},
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
    }


demo = gr.Interface(
    fn=classify,
    inputs=gr.Image(type="pil", label="Meal photo"),
    outputs=gr.JSON(label="Top-3 predictions"),
    title="AI Food & Calories Recognition — model endpoint",
    description=(
        "Two-engine recognition: ViT fine-tuned on Food-101 (nateraw/food) + a Tunisian-dish "
        "MobileNetV3 fine-tuned on three public CC-BY-4.0 Roboflow datasets "
        "(couscous, brik, ojja, mloukhiya, lablabi, kafteji, merguez…). "
        "Estimates only — not medical or dietary advice. Astrolab Group internship project; "
        "the full web app runs on Netlify using this Space as its recognition engine."
    ),
)

if __name__ == "__main__":
    demo.launch()
