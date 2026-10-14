from __future__ import annotations
from pathlib import Path
import json, os, re, warnings
import numpy as np
import pandas as pd

HERE = Path(__file__).resolve().parent
BASE = HERE.parent
ROOT = BASE.parent
OUT = BASE / 'outputs'
MODELS = BASE / 'models'
LOGS = BASE / 'logs'
CONFIG = BASE / 'config' / 'phase_config.json'
SEED = 42

for p in (OUT, MODELS, LOGS):
    p.mkdir(parents=True, exist_ok=True)

warnings.filterwarnings('ignore', message=r'A single label was found in')
warnings.filterwarnings('ignore', message=r'Only one class was present in')
warnings.filterwarnings('ignore', message=r'UndefinedMetricWarning')


def cfg():
    return json.loads(CONFIG.read_text(encoding='utf-8')) if CONFIG.exists() else {'seed': 42}


def phase_out(name: str) -> Path:
    p = OUT / name
    p.mkdir(parents=True, exist_ok=True)
    return p


def log(msg: str):
    print(f'[{pd.Timestamp.now():%Y-%m-%d %H:%M:%S}] {msg}', flush=True)


def save(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def norm_name(x) -> str:
    s = '' if pd.isna(x) else str(x).upper()
    return re.sub(r'[^A-Z0-9]+', '', s)


def clean_num(x):
    return pd.to_numeric(x, errors='coerce')


def find_first(candidates):
    for c in candidates:
        p = ROOT / c
        if p.exists():
            return p
    return None


def find_phase13_base() -> Path | None:
    candidates = [
        BASE / 'outputs' / 'PHASE_13_ADVANCED_YIELD',
        ROOT / '13_15_NEXT_PHASES' / 'outputs' / 'PHASE_13_ADVANCED_YIELD',
        ROOT / 'MAIZE_PHASES_13_15_DROP_IN' / 'outputs' / 'PHASE_13_ADVANCED_YIELD',
    ]
    for p in candidates:
        if p.exists(): return p
    return None


def find_phase14_base() -> Path | None:
    candidates = [
        BASE / 'outputs' / 'PHASE_14_ADVANCED_DISEASE',
        ROOT / '13_15_NEXT_PHASES' / 'outputs' / 'PHASE_14_ADVANCED_DISEASE',
        ROOT / 'MAIZE_PHASES_13_15_DROP_IN' / 'outputs' / 'PHASE_14_ADVANCED_DISEASE',
    ]
    for p in candidates:
        if p.exists(): return p
    return None


def find_model_file(names):
    candidates=[]
    for base in [BASE/'models', ROOT/'13_15_NEXT_PHASES'/'models', ROOT/'MAIZE_PHASES_13_15_DROP_IN'/'models', ROOT/'08_AUTOMATED_PIPELINE'/'models', ROOT/'08_AUTOMATED_PIPELINE'/'outputs'/'06_TUNING']:
        for name in names:
            candidates.append(base/name)
    for p in candidates:
        if p.exists(): return p
    return None


def metric_regression(y_true, y_pred):
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    y_true=np.asarray(y_true,float); y_pred=np.asarray(y_pred,float)
    return {
        'MAE': float(mean_absolute_error(y_true,y_pred)),
        'RMSE': float(np.sqrt(mean_squared_error(y_true,y_pred))),
        'R2': float(r2_score(y_true,y_pred)) if len(np.unique(y_true))>1 else np.nan
    }


def metric_classification(y_true, y_pred):
    from sklearn.metrics import accuracy_score, balanced_accuracy_score, f1_score
    with warnings.catch_warnings():
        warnings.simplefilter('ignore')
        return {
            'accuracy': float(accuracy_score(y_true,y_pred)),
            'balanced_accuracy': float(balanced_accuracy_score(y_true,y_pred)),
            'f1_macro': float(f1_score(y_true,y_pred,average='macro',zero_division=0))
        }


def safe_groups(n_groups, requested=5):
    return min(requested, n_groups)
