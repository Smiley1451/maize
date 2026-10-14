from __future__ import annotations

from pathlib import Path
from typing import Iterable

from app.core.config import PROJECT_ROOT


MODEL_PATTERNS: dict[str, list[str]] = {
    "yield": [
        "yield_advanced_selected.joblib",
        "YIELD_TUNED_RANDOM_FOREST.joblib",
        "yield_tuned_random_forest.joblib",
        "yield_ExtraTrees.joblib",
        "yield_RandomForest.joblib",
    ],
    "tlb_regression": [
        "tlb_advanced_regression_selected.joblib",
        "TLB_TUNED_EXTRATREES.joblib",
        "tlb_tuned_extratrees.joblib",
        "TLB_ExtraTrees.joblib",
    ],
    "tlb_classifier": [
        "tlb_advanced_classifier_selected.joblib",
        "TLB_TUNED_RANDOM_FOREST_CLASSIFIER.joblib",
        "tlb_tuned_random_forest_classifier.joblib",
        "TLB_RandomForest_classifier.joblib",
    ],
    "sdm_regression": [
        "sdm_advanced_regression_selected.joblib",
        "SDM_TUNED_EXTRATREES.joblib",
        "sdm_tuned_extratrees.joblib",
        "SDM_ExtraTrees.joblib",
    ],
    "sdm_classifier": [
        "sdm_advanced_classifier_selected.joblib",
        "SDM_TUNED_RANDOM_FOREST_CLASSIFIER.joblib",
        "sdm_tuned_random_forest_classifier.joblib",
        "SDM_RandomForest_classifier.joblib",
    ],
}


def model_roots() -> list[Path]:
    r = PROJECT_ROOT
    roots = [
        r / "MAIZE_PHASES_16_18_DROP_IN" / "models",
        r / "13_15_NEXT_PHASES" / "models",
        r / "MAIZE_PHASES_13_15_DROP_IN" / "models",
        r / "08_AUTOMATED_PIPELINE" / "models",
        r / "08_AUTOMATED_PIPELINE" / "outputs",
        r / "MAIZE_PHASES_13_15_DROP_IN" / "outputs",
    ]
    return [p for p in roots if p.exists()]


def find_named_model(names: Iterable[str]) -> Path | None:
    for root in model_roots():
        for name in names:
            exact = root / name
            if exact.exists():
                return exact
            try:
                hit = next(root.rglob(name))
                return hit
            except StopIteration:
                pass
    return None


def find_dataset(name: str) -> Path | None:
    direct = [
        PROJECT_ROOT / name,
        PROJECT_ROOT / "10_12_NEXT_PHASES" / "outputs" / "PHASE_11_PRODUCTION_DATASETS" / name,
        PROJECT_ROOT / "13_15_NEXT_PHASES" / "outputs" / name,
        PROJECT_ROOT / "MAIZE_PHASES_13_15_DROP_IN" / "outputs" / name,
        PROJECT_ROOT / "MAIZE_PHASES_16_18_DROP_IN" / "outputs" / name,
        PROJECT_ROOT / "08_AUTOMATED_PIPELINE" / "outputs" / name,
    ]
    for p in direct:
        if p.exists():
            return p
    for base in [PROJECT_ROOT / "10_12_NEXT_PHASES", PROJECT_ROOT / "13_15_NEXT_PHASES", PROJECT_ROOT / "MAIZE_PHASES_13_15_DROP_IN", PROJECT_ROOT / "MAIZE_PHASES_16_18_DROP_IN", PROJECT_ROOT / "08_AUTOMATED_PIPELINE", PROJECT_ROOT / "maize_master_data", PROJECT_ROOT / "maize_analysis_master", PROJECT_ROOT / "maize_normalized_data"]:
        if not base.exists():
            continue
        try:
            hit = next(base.rglob(name))
            return hit
        except StopIteration:
            pass
    return None
