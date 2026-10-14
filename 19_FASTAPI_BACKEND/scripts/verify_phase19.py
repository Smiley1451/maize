from __future__ import annotations

import os
import sys
from pathlib import Path

BASE = Path(__file__).resolve().parents[1]
ROOT = BASE.parent
os.environ.setdefault("MAIZE_PROJECT_ROOT", str(ROOT))
sys.path.insert(0, str(BASE))

checks: list[tuple[str, bool, str]] = []


def check(label: str, condition: bool, detail: str = "") -> None:
    checks.append((label, bool(condition), detail))


def main() -> int:
    print("=" * 62)
    print("PHASE 19: FASTAPI BACKEND VERIFICATION")
    print("=" * 62)

    required = [
        BASE / "app" / "main.py",
        BASE / "app" / "services" / "model_service.py",
        BASE / "app" / "services" / "data_service.py",
        BASE / "app" / "services" / "artifact_service.py",
        BASE / "RUN_PHASE19.ps1",
        BASE / "START_FASTAPI.ps1",
        BASE / "requirements.txt",
        BASE / "README.md",
        BASE / "CONTINGENCY_PLAN.md",
    ]
    for p in required:
        check(f"File exists: {p.relative_to(BASE)}", p.exists())

    try:
        from fastapi.testclient import TestClient
        from app.main import app
        check("FastAPI import", True)
        routes = {getattr(r, "path", "") for r in app.routes}
        must_have = {
            "/health",
            "/ready",
            "/api/v1/status",
            "/api/v1/info",
            "/api/v1/models",
            "/api/v1/predict/all",
            "/api/v1/predict/batch",
            "/api/v1/predict/batch-csv",
            "/api/v1/genotypes",
            "/api/v1/experiments",
            "/api/v1/observations",
            "/api/v1/clusters/status",
            "/api/v1/weather/status",
            "/api/v1/explainability/{model_key}",
            "/api/v1/project/verification",
        }
        for route in must_have:
            check(f"Route present: {route}", route in routes)
        with TestClient(app) as client:
            for endpoint in ["/health", "/ready", "/api/v1/status", "/api/v1/info", "/api/v1/features", "/api/v1/models", "/api/v1/catalog"]:
                resp = client.get(endpoint)
                check(f"Endpoint smoke: {endpoint}", resp.status_code == 200, f"HTTP {resp.status_code}")
    except Exception as exc:
        check("FastAPI import and smoke tests", False, repr(exc))

    failed = 0
    for label, ok, detail in checks:
        print(f"{'PASS' if ok else 'FAIL'}: {label}{(' | ' + detail) if detail else ''}")
        failed += int(not ok)

    out = BASE / "outputs"
    out.mkdir(exist_ok=True)
    (out / "PHASE19_VERIFICATION.txt").write_text(
        "PHASE 19 VERIFICATION: " + ("READY" if failed == 0 else "FAILED") + f"\nPasses={len(checks)-failed}\nFails={failed}\n",
        encoding="utf-8",
    )
    print("=" * 62)
    print(f"PHASE 19 VERIFICATION: {'READY' if failed == 0 else 'FAILED'}")
    return 0 if failed == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
