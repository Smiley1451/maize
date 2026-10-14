from __future__ import annotations

import json
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
os.environ.setdefault("MAIZE_PROJECT_ROOT", str(ROOT.parent))
import sys
sys.path.insert(0, str(ROOT))
from app.main import app

out = ROOT / "outputs" / "openapi.json"
out.parent.mkdir(parents=True, exist_ok=True)
out.write_text(json.dumps(app.openapi(), indent=2), encoding="utf-8")
print(f"OPENAPI EXPORTED: {out}")
