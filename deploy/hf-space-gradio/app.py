"""Model endpoint Space: meal photo -> top-3 Food-101 predictions (ViT).

Free-tier Gradio Space. The product frontend (Netlify) calls this via
@gradio/client; nutrition lookup/scaling happen client-side there.
"""
import time

import spaces  # ZeroGPU: must be imported before torch CUDA use
import gradio as gr
import torch
from transformers import AutoImageProcessor, AutoModelForImageClassification

MODEL = "nateraw/food"
processor = AutoImageProcessor.from_pretrained(MODEL)
model = AutoModelForImageClassification.from_pretrained(MODEL)
model.eval()
model.to("cuda")


@spaces.GPU
def classify(image):
    if image is None:
        return {"error": "No image provided."}
    t0 = time.perf_counter()
    inputs = processor(images=image.convert("RGB"), return_tensors="pt").to("cuda")
    with torch.no_grad():
        logits = model(**inputs).logits
    probs = torch.nn.functional.softmax(logits[0], dim=-1)
    top = torch.topk(probs, 3)
    predictions = [
        {"label": model.config.id2label[int(i)], "confidence": round(float(p), 4)}
        for i, p in zip(top.indices.cpu(), top.values.cpu())
    ]
    return {
        "predictions": predictions,
        "latency_ms": round((time.perf_counter() - t0) * 1000, 1),
    }


demo = gr.Interface(
    fn=classify,
    inputs=gr.Image(type="pil", label="Meal photo"),
    outputs=gr.JSON(label="Top-3 predictions"),
    title="AI Food & Calories Recognition — model endpoint",
    description=(
        "ViT fine-tuned on Food-101 (nateraw/food). Returns the top-3 dominant-food "
        "predictions with confidences. Estimates only — not medical or dietary advice. "
        "Astrolab Group internship project; the full web app frontend runs on Netlify "
        "and uses this Space as its recognition engine."
    ),
)

if __name__ == "__main__":
    demo.launch()
