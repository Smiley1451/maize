from __future__ import annotations

import os
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
os.environ.setdefault("MAIZE_PROJECT_ROOT", str(BASE.parent))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


def test_health():
    with TestClient(app) as client:
        r = client.get("/health")
        assert r.status_code == 200
        assert r.json()["status"] == "ok"


def test_api_catalog_and_models():
    with TestClient(app) as client:
        assert client.get("/api/v1/catalog").status_code == 200
        assert client.get("/api/v1/models").status_code == 200
        assert client.get("/api/v1/features").status_code == 200


def test_prediction_contract_without_fake_values():
    with TestClient(app) as client:
        r = client.post("/api/v1/predict/all", json={"genotype": "TEST-GENOTYPE", "plant_height": 220, "ear_height": 115})
        assert r.status_code == 200
        body = r.json()
        assert body["genotype"] == "TEST-GENOTYPE"
        assert "model_status" in body
