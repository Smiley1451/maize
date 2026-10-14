from __future__ import annotations

import os
from pathlib import Path


def discover_project_root() -> Path:
    env = os.getenv("MAIZE_PROJECT_ROOT")
    if env:
        p = Path(env).expanduser().resolve()
        if p.exists():
            return p

    here = Path(__file__).resolve()
    for p in [here.parent, *here.parents]:
        markers = [
            p / "08_AUTOMATED_PIPELINE",
            p / "10_12_NEXT_PHASES",
            p / "MAIZE_PHASES_13_15_DROP_IN",
            p / "MAIZE_PHASES_16_18_DROP_IN",
            p / "maize_master_data",
        ]
        if any(m.exists() for m in markers):
            return p

    cwd = Path.cwd().resolve()
    if (cwd / "08_AUTOMATED_PIPELINE").exists() or (cwd / "maize_master_data").exists():
        return cwd
    if (cwd.parent / "08_AUTOMATED_PIPELINE").exists():
        return cwd.parent
    return cwd


PROJECT_ROOT = discover_project_root()
BACKEND_ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = BACKEND_ROOT / "config"
OUTPUT_DIR = BACKEND_ROOT / "outputs"
LOG_DIR = BACKEND_ROOT / "logs"

APP_NAME = os.getenv("MAIZE_API_NAME", "Maize AI/ML Research API")
APP_VERSION = os.getenv("MAIZE_API_VERSION", "0.1.0")
HOST = os.getenv("MAIZE_API_HOST", "127.0.0.1")
PORT = int(os.getenv("MAIZE_API_PORT", "8000"))
API_PREFIX = os.getenv("MAIZE_API_PREFIX", "/api/v1")
API_KEY = os.getenv("MAIZE_API_KEY", "").strip()
CORS_ORIGINS = [x.strip() for x in os.getenv("MAIZE_CORS_ORIGINS", "*").split(",") if x.strip()]
MAX_BATCH_ROWS = int(os.getenv("MAIZE_MAX_BATCH_ROWS", "500"))


def csv_candidates() -> list[Path]:
    r = PROJECT_ROOT
    return [
        r / "10_12_NEXT_PHASES" / "outputs" / "PHASE_11_PRODUCTION_DATASETS" / "YIELD_PRODUCTION_STRICT.csv",
        r / "10_12_NEXT_PHASES" / "outputs" / "PHASE_11_PRODUCTION_DATASETS" / "TLB_PRODUCTION_STRICT.csv",
        r / "10_12_NEXT_PHASES" / "outputs" / "PHASE_11_PRODUCTION_DATASETS" / "SDM_PRODUCTION_STRICT.csv",
        r / "10_12_NEXT_PHASES" / "outputs" / "PHASE_11_PRODUCTION_DATASETS" / "MULTI_TRAIT_PRODUCTION_SUMMARY.csv",
        r / "13_15_NEXT_PHASES" / "outputs",
        r / "MAIZE_PHASES_13_15_DROP_IN" / "outputs",
        r / "MAIZE_PHASES_16_18_DROP_IN" / "outputs",
        r / "08_AUTOMATED_PIPELINE" / "outputs",
        r / "maize_master_data",
        r / "maize_normalized_data",
        r / "maize_analysis_master",
        r / "maize_ml_datasets",
    ]
