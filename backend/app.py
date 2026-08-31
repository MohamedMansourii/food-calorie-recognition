"""AI Food & Calories Recognition — API server.

Ported and adapted from Rishabh1925/foodvisionai (MIT) — backend/app.py.
Serves the recognition API and, when frontend/dist exists, the built web app.
"""
import os

from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS

import nutrition
import tunisian
from config import Config
from model import get_model

app = Flask(__name__, static_folder=Config.STATIC_DIR, static_url_path="/")
CORS(app, origins=Config.CORS_ORIGINS)
app.config["MAX_CONTENT_LENGTH"] = Config.MAX_IMAGE_SIZE


@app.route("/api/health", methods=["GET"])
def health():
    from model import _instance
    return jsonify({
        "status": "ok",
        "model": Config.MODEL_NAME,
        "model_loaded": _instance is not None,
    })


@app.route("/api/analyze", methods=["POST"])
def analyze():
    if "image" not in request.files:
        return jsonify({"error": "No image file provided. Send multipart field 'image'."}), 400

    file = request.files["image"]
    if not file.filename:
        return jsonify({"error": "No image file selected."}), 400

    bad_ext = not Config.allowed_file(file.filename)
    bad_mime = file.mimetype not in Config.ALLOWED_MIMETYPES
    if bad_ext and bad_mime:
        return jsonify({
            "error": "Unsupported file type. Allowed: " + ", ".join(sorted(Config.ALLOWED_EXTENSIONS)),
        }), 415

    image_bytes = file.read()
    try:
        predictions, latency_ms = get_model().predict(image_bytes, top_k=3)
    except Exception:
        return jsonify({"error": "Could not read that file as an image."}), 415

    # Second engine: Tunisian dishes (no-op when the model isn't present).
    predictions = tunisian.merge(predictions, tunisian.candidates(image_bytes))

    return jsonify(_build_result(predictions, latency_ms))


def _build_result(predictions: list[dict], latency_ms: float) -> dict:
    """Confidence policy (FR-03/04/05) + nutrition block (FR-06/07)."""
    top1 = predictions[0]["confidence"]
    if top1 >= Config.CONFIDENT_THRESHOLD:
        status = "ok"
    elif top1 >= Config.LOW_CONFIDENCE_THRESHOLD:
        status = "low_confidence"
    else:
        status = "no_food"

    enriched = [
        {**p, "display_name": nutrition.display_name(p["label"])} for p in predictions
    ]
    return {
        "status": status,
        "predictions": enriched,
        # No nutrition when nothing matched confidently enough (FR-04/05 path).
        "nutrition": nutrition.nutrition_block(enriched[0]["label"]) if status != "no_food" else None,
        "latency_ms": latency_ms,
        "disclaimer": "Estimates only — not medical or dietary advice.",
    }


@app.route("/api/foods", methods=["GET"])
def foods_search():
    """FR-05: searchable dropdown backing — names + aliases, max 10 hits."""
    return jsonify({"results": nutrition.search(request.args.get("q", ""), limit=10)})


@app.route("/api/foods/<label>", methods=["GET"])
def food_nutrition(label: str):
    """Nutrition for a manually selected / corrected food."""
    block = nutrition.nutrition_block(label)
    if block is None:
        return jsonify({"error": f"Unknown food '{label}'."}), 404
    return jsonify(block)


# --- error handlers -------------------------------------------------------

@app.errorhandler(413)
def too_large(_e):
    mb = Config.MAX_IMAGE_SIZE // (1024 * 1024)
    return jsonify({"error": f"File too large. Maximum size is {mb} MB."}), 413


@app.errorhandler(404)
def not_found(e):
    if request.path.startswith("/api/"):
        return jsonify({"error": "Not found."}), 404
    return spa(request.path)  # SPA fallback for client-side routes


@app.errorhandler(500)
def internal_error(_e):
    return jsonify({"error": "Internal server error."}), 500


# --- packaged frontend ----------------------------------------------------

@app.route("/")
def spa(_path: str = ""):
    index = os.path.join(Config.STATIC_DIR, "index.html")
    if os.path.exists(index):
        return send_from_directory(Config.STATIC_DIR, "index.html")
    return jsonify({"error": "Frontend not built. Run: cd frontend && npm run build"}), 404


if __name__ == "__main__":
    print(f"Loading model {Config.MODEL_NAME} ...")
    get_model()  # warm up before accepting requests
    print(f"Serving on http://localhost:{Config.PORT}")
    app.run(host=Config.HOST, port=Config.PORT, debug=Config.DEBUG)
