from __future__ import annotations
from pathlib import Path
import json, os

HERE = Path(__file__).resolve().parent
ASSISTANT_ROOT = HERE.parent
PROJECT_ROOT = ASSISTANT_ROOT.parent
CONFIG_PATH = ASSISTANT_ROOT / "config" / "config.json"
with CONFIG_PATH.open("r", encoding="utf-8") as f:
    CFG = json.load(f)


def env(name: str, default: str | None = None) -> str | None:
    value = os.getenv(name)
    return value if value not in (None, "") else default

LLM_PROVIDER = (env("MAIZE_LLM_PROVIDER", "local") or "local").lower()
LLM_BASE_URL = (env("MAIZE_LLM_BASE_URL", "") or "").rstrip("/")
LLM_API_KEY = env("MAIZE_LLM_API_KEY", "") or ""
LLM_MODEL = env("MAIZE_LLM_MODEL", "") or ""
PHASE19_URL = env("MAIZE_PHASE19_URL", CFG["phase19_url"]) or CFG["phase19_url"]
ASSISTANT_PORT = int(env("MAIZE_ASSISTANT_PORT", str(CFG["assistant_port"])) or CFG["assistant_port"])
