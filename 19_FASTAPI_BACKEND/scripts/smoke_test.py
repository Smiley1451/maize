from __future__ import annotations

import os
import sys
from pathlib import Path

os.environ.setdefault("MAIZE_PROJECT_ROOT", str(Path(__file__).resolve().parents[2].parent))
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from fastapi.testclient import TestClient  # noqa: E402
from app.main import app  # noqa: E402


def main() -> int:
    print("=" * 62)
    print("PHASE 19: FASTAPI SMOKE TEST")
    print("=" * 62)
    with TestClient(app) as client:
        checks = [
            ("GET /health", client.get("/health")),
            ("GET /ready", client.get("/ready")),
            ("GET /api/v1/status", client.get("/api/v1/status")),
            ("GET /api/v1/info", client.get("/api/v1/info")),
            ("GET /api/v1/features", client.get("/api/v1/features")),
            ("GET /api/v1/models", client.get("/api/v1/models")),
            ("GET /api/v1/catalog", client.get("/api/v1/catalog")),
            ("GET /api/v1/genotypes?limit=5", client.get("/api/v1/genotypes?limit=5")),
            ("GET /api/v1/experiments?limit=5", client.get("/api/v1/experiments?limit=5")),
            ("GET /api/v1/clusters/status", client.get("/api/v1/clusters/status")),
            ("GET /api/v1/weather/status", client.get("/api/v1/weather/status")),
            ("GET /api/v1/explainability/yield", client.get("/api/v1/explainability/yield")),
            ("GET /api/v1/project/verification", client.get("/api/v1/project/verification")),
            ("POST /api/v1/predict/all", client.post("/api/v1/predict/all", json={"genotype": "SMOKE-TEST", "plant_height": 220, "ear_height": 115})),
        ]
        failed = 0
        for name, response in checks:
            ok = 200 <= response.status_code < 300
            print(f"{'PASS' if ok else 'FAIL'}: {name} -> {response.status_code}")
            if not ok:
                print(response.text[:500])
                failed += 1
    print("=" * 62)
    print(f"PHASE 19 SMOKE TEST: {'READY' if failed == 0 else 'FAILED'}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
