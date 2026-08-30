"""Food-101 image classifier wrapper.

Ported and adapted from Rishabh1925/foodvisionai (MIT) — backend/model.py.
Loads the Hugging Face `nateraw/food` ViT model (fine-tuned on Food-101)
and returns top-k (slug, confidence) predictions for one image.
"""
import io
import time

import torch
from PIL import Image
from transformers import AutoImageProcessor, AutoModelForImageClassification

from config import Config


class FoodClassifier:
    def __init__(self, model_name: str = Config.MODEL_NAME):
        self.model_name = model_name
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        self.processor = AutoImageProcessor.from_pretrained(model_name)
        self.model = AutoModelForImageClassification.from_pretrained(model_name)
        self.model.to(self.device)
        self.model.eval()

    @property
    def labels(self) -> list[str]:
        """The 101 class slugs, in model index order."""
        id2label = self.model.config.id2label
        return [id2label[i] for i in range(len(id2label))]

    def predict(self, image_bytes: bytes, top_k: int = 3) -> tuple[list[dict], float]:
        """Classify one image. Returns (predictions, latency_ms).

        predictions: [{"label": slug, "confidence": 0..1}, ...] best-first.
        """
        start = time.perf_counter()
        image = Image.open(io.BytesIO(image_bytes)).convert("RGB")
        inputs = self.processor(images=image, return_tensors="pt")
        inputs = {k: v.to(self.device) for k, v in inputs.items()}

        with torch.no_grad():
            logits = self.model(**inputs).logits

        probs = torch.nn.functional.softmax(logits[0], dim=-1)
        top = torch.topk(probs, top_k)
        id2label = self.model.config.id2label

        predictions = [
            {"label": id2label[int(idx)], "confidence": round(float(p), 4)}
            for idx, p in zip(top.indices.cpu(), top.values.cpu())
        ]
        latency_ms = round((time.perf_counter() - start) * 1000, 1)
        return predictions, latency_ms


_instance: FoodClassifier | None = None


def get_model() -> FoodClassifier:
    """Lazy singleton so the model loads once, on first request or at boot."""
    global _instance
    if _instance is None:
        _instance = FoodClassifier()
    return _instance
