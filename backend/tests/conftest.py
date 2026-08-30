import io
import os
import sys

import pytest
from PIL import Image

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app as flask_app  # noqa: E402


@pytest.fixture(scope="session")
def client():
    flask_app.config["TESTING"] = True
    with flask_app.test_client() as c:
        yield c


def _jpeg_bytes(size=(224, 224), color=(200, 120, 60)) -> bytes:
    buf = io.BytesIO()
    Image.new("RGB", size, color).save(buf, format="JPEG")
    return buf.getvalue()


@pytest.fixture(scope="session")
def food_image() -> bytes:
    """A real sample photo if Phase 5 fetched one, else a synthetic JPEG."""
    root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    samples = os.path.join(root, "sample_photos")
    if os.path.isdir(samples):
        for cls in sorted(os.listdir(samples)):
            cls_dir = os.path.join(samples, cls)
            if os.path.isdir(cls_dir):
                for name in sorted(os.listdir(cls_dir)):
                    if name.lower().endswith((".jpg", ".jpeg", ".png")):
                        with open(os.path.join(cls_dir, name), "rb") as f:
                            return f.read()
    return _jpeg_bytes()


@pytest.fixture()
def synthetic_image() -> bytes:
    return _jpeg_bytes()
