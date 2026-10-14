from __future__ import annotations
from pathlib import Path
import json, os, re, math, warnings
import numpy as np
import pandas as pd

ROOT = Path(__file__).resolve().parents[2]
BASE = Path(__file__).resolve().parents[1]
OUT = BASE / 'outputs'
MODELS = BASE / 'models'
LOGS = BASE / 'logs'
CONFIG = BASE / 'config' / 'phase_config.json'
SEED = 42

for p in (OUT, MODELS, LOGS):
    p.mkdir(parents=True, exist_ok=True)


def cfg():
    return json.loads(CONFIG.read_text(encoding='utf-8'))


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


def clean_num(s):
    return pd.to_numeric(s, errors='coerce')


def yield_correct(value, unit):
    try:
        v = float(value)
    except Exception:
        return np.nan, 'INVALID_VALUE'
    u = '' if pd.isna(unit) else str(unit).strip().lower().replace(' ', '')
    if 't/ha' in u or u in {'tperha','tonne/ha','tonnes/ha'}:
        return v * 1000.0, 'T_PER_HA_TO_KG_PER_HA'
    if 'kg/ha' in u or u in {'kgperha','kg-ha'}:
        return v, 'KG_PER_HA_AS_IS'
    return np.nan, 'UNKNOWN_UNIT'


def pct_rank_high(s):
    return s.rank(pct=True, method='average') * 100.0


def pct_rank_low(s):
    return (1.0 - s.rank(pct=True, method='average')) * 100.0


def pareto_front(df, maximize_cols, minimize_cols):
    vals = df[maximize_cols + minimize_cols].astype(float).to_numpy()
    directions = np.array([1] * len(maximize_cols) + [-1] * len(minimize_cols), dtype=float)
    z = vals * directions
    n = len(z)
    efficient = np.ones(n, dtype=bool)
    for i in range(n):
        if not efficient[i]:
            continue
        for j in range(n):
            if i == j:
                continue
            # j dominates i if j is >= on all objectives and > on at least one.
            if np.all(z[j] >= z[i]) and np.any(z[j] > z[i]):
                efficient[i] = False
                break
    return efficient
