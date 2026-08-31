"""Contract tests for every endpoint (Phase 4).

Run:  <venv>/python -m pytest backend/tests -q
First analyze call loads the ViT model (~10-30 s on CPU) — expected.
"""
import io

MACRO_KEYS = {"kcal", "protein_g", "carbs_g", "fat_g"}


# --- /api/health ----------------------------------------------------------

def test_health(client):
    res = client.get("/api/health")
    assert res.status_code == 200
    body = res.get_json()
    assert body["status"] == "ok"
    assert "model" in body


# --- /api/analyze ---------------------------------------------------------

def test_analyze_full_contract(client, food_image):
    res = client.post(
        "/api/analyze",
        data={"image": (io.BytesIO(food_image), "meal.jpg")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    body = res.get_json()

    assert body["status"] in {"ok", "low_confidence", "no_food"}
    assert len(body["predictions"]) == 3
    for p in body["predictions"]:
        assert {"label", "display_name", "confidence"} <= set(p)
        assert set(p) <= {"label", "display_name", "confidence", "source"}
        assert 0.0 <= p["confidence"] <= 1.0
    # best-first ordering within each engine (merged lists may interleave)
    by_source = {}
    for p in body["predictions"]:
        by_source.setdefault(p.get("source", "food101"), []).append(p["confidence"])
    for confs in by_source.values():
        assert confs == sorted(confs, reverse=True)

    assert body["latency_ms"] > 0
    assert "not medical" in body["disclaimer"]

    if body["status"] == "no_food":
        assert body["nutrition"] is None
    else:
        n = body["nutrition"]
        assert n["food"] == body["predictions"][0]["label"]
        assert set(n["per_100g"]) == MACRO_KEYS
        assert set(n["portions"]) == {"small_g", "medium_g", "large_g"}
        assert set(n["estimate"]) == MACRO_KEYS | {"portion_g"}
        assert n["needs_review"] is True


def test_analyze_no_file(client):
    res = client.post("/api/analyze", data={}, content_type="multipart/form-data")
    assert res.status_code == 400
    assert "error" in res.get_json()


def test_analyze_wrong_type_415(client):
    res = client.post(
        "/api/analyze",
        data={"image": (io.BytesIO(b"not an image"), "notes.txt")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 415
    assert "error" in res.get_json()


def test_analyze_fake_extension_415(client):
    """A .jpg that is not actually image bytes must not crash the model."""
    res = client.post(
        "/api/analyze",
        data={"image": (io.BytesIO(b"plain text pretending"), "fake.jpg")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 415


def test_analyze_too_large_413(client):
    blob = b"\xff" * (9 * 1024 * 1024)  # > 8 MB cap
    res = client.post(
        "/api/analyze",
        data={"image": (io.BytesIO(blob), "huge.jpg")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 413
    assert "error" in res.get_json()


def test_analyze_nonfood_graceful(client, synthetic_image):
    """A flat-color synthetic image must return a valid contract, never 500."""
    res = client.post(
        "/api/analyze",
        data={"image": (io.BytesIO(synthetic_image), "wall.jpg")},
        content_type="multipart/form-data",
    )
    assert res.status_code == 200
    assert res.get_json()["status"] in {"ok", "low_confidence", "no_food"}


# --- /api/foods search ----------------------------------------------------

def test_foods_search(client):
    res = client.get("/api/foods?q=burger")
    assert res.status_code == 200
    results = res.get_json()["results"]
    assert 0 < len(results) <= 10
    assert any(r["label"] == "hamburger" for r in results)
    for r in results:
        assert set(r) == {"label", "display_name"}


def test_foods_search_alias(client):
    res = client.get("/api/foods?q=fries")
    labels = [r["label"] for r in res.get_json()["results"]]
    assert "french_fries" in labels


def test_foods_search_empty_query(client):
    res = client.get("/api/foods?q=")
    assert res.status_code == 200
    assert res.get_json()["results"] == []


# --- /api/foods/<label> ---------------------------------------------------

def test_food_nutrition(client):
    res = client.get("/api/foods/pizza")
    assert res.status_code == 200
    n = res.get_json()
    assert n["food"] == "pizza"
    assert set(n["per_100g"]) == MACRO_KEYS
    default = n["default_portion_g"]
    assert n["portions"]["small_g"] == round(default * 0.7)
    assert n["portions"]["medium_g"] == round(default * 1.0)
    assert n["portions"]["large_g"] == round(default * 1.4)
    # estimate is per_100g scaled to the default portion
    assert n["estimate"]["portion_g"] == round(default)
    assert n["estimate"]["kcal"] == round(n["per_100g"]["kcal"] * default / 100)


def test_food_nutrition_unknown_404(client):
    res = client.get("/api/foods/unicorn_steak")
    assert res.status_code == 404
    assert "error" in res.get_json()


# --- Tunisian foods (search/nutrition-only additions, not model classes) ---

def test_tunisian_alias_search(client):
    """'ejja' (the common spelling) must find Ojja via aliases."""
    labels = [r["label"] for r in client.get("/api/foods?q=ejja").get_json()["results"]]
    assert "ojja" in labels


def test_tunisian_arabic_search(client):
    labels = [r["label"] for r in client.get("/api/foods?q=ملوخية").get_json()["results"]]
    assert "mloukhiya" in labels


def test_merge_policy_units():
    """Engine-merge rules (no models needed)."""
    import tunisian

    vit_hi = [{"label": "pizza", "confidence": 0.95}, {"label": "lasagna", "confidence": 0.02},
              {"label": "ravioli", "confidence": 0.01}]
    vit_lo = [{"label": "risotto", "confidence": 0.30}, {"label": "paella", "confidence": 0.2},
              {"label": "fried_rice", "confidence": 0.1}]
    tun_hi = [{"label": "couscous", "confidence": 0.9, "source": "tunisian"}]
    tun_mid = [{"label": "couscous", "confidence": 0.6, "source": "tunisian"}]

    # no tunisian candidates -> vit untouched
    assert [p["label"] for p in tunisian.merge(list(vit_hi), [])][0] == "pizza"
    # very confident tunisian beats even a confident vit
    assert tunisian.merge(list(vit_hi), list(tun_hi))[0]["label"] == "couscous"
    # mid-confidence tunisian leads only when vit is unsure
    assert tunisian.merge(list(vit_hi), list(tun_mid))[0]["label"] == "pizza"
    assert tunisian.merge(list(vit_lo), list(tun_mid))[0]["label"] == "couscous"
    # always top-3, deduped
    merged = tunisian.merge(list(vit_lo), list(tun_mid))
    assert len(merged) == 3 and len({p["label"] for p in merged}) == 3


def test_tunisian_nutrition_block(client):
    n = client.get("/api/foods/couscous").get_json()
    assert n["food"] == "couscous"
    assert n["needs_review"] is True
    assert n["portions"]["small_g"] == round(n["default_portion_g"] * 0.7)
    for slug in ("marga", "loubia", "mloukhiya", "ojja", "brik", "lablabi"):
        assert client.get(f"/api/foods/{slug}").status_code == 200
