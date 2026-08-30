"""Application configuration.

Ported and adapted from Rishabh1925/foodvisionai (MIT) — backend/config.py.
"""
import os

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
REPO_ROOT = BASE_DIR  # flat HF Space bundle


class Config:
    MODEL_NAME = "nateraw/food"  # ViT fine-tuned on Food-101 (101 classes)

    # FR/NFR: reject files over 8 MB with a clean JSON 413.
    MAX_IMAGE_SIZE = 8 * 1024 * 1024
    ALLOWED_EXTENSIONS = {"png", "jpg", "jpeg", "gif", "webp"}
    ALLOWED_MIMETYPES = {"image/png", "image/jpeg", "image/gif", "image/webp"}

    HOST = os.environ.get("HOST", "0.0.0.0")
    PORT = int(os.environ.get("PORT", 8000))
    DEBUG = os.environ.get("FLASK_DEBUG", "0") == "1"

    # Dev origins (Vite). In the packaged build Flask serves the frontend itself.
    CORS_ORIGINS = ["http://localhost:5173", "http://127.0.0.1:5173"]

    # Confidence policy (FR-03 / FR-04 / FR-05)
    CONFIDENT_THRESHOLD = 0.70
    LOW_CONFIDENCE_THRESHOLD = 0.35

    # Portion presets (FR-07): multipliers on each food's default portion.
    PORTION_MULTIPLIERS = {"small": 0.7, "medium": 1.0, "large": 1.4}

    DATA_DIR = REPO_ROOT
    FOODS_PATH = os.path.join(DATA_DIR, "foods.json")
    NUTRITION_PATH = os.path.join(DATA_DIR, "nutrition_table.json")

    # Built frontend (frontend/dist) served by Flask in the packaged build.
    STATIC_DIR = os.path.join(REPO_ROOT, "static")

    @staticmethod
    def allowed_file(filename: str) -> bool:
        return "." in filename and filename.rsplit(".", 1)[1].lower() in Config.ALLOWED_EXTENSIONS
