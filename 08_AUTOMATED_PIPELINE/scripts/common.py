from __future__ import annotations

import json, os, re, hashlib, traceback
from pathlib import Path
from datetime import datetime

import numpy as np
import pandas as pd

SEED = 42


def now():
    return datetime.now().strftime('%Y-%m-%d %H:%M:%S')


def log(msg: str):
    print(f"[{now()}] {msg}", flush=True)


def project_root() -> Path:
    return Path(__file__).resolve().parents[2]


def pipeline_root() -> Path:
    return project_root() / '08_AUTOMATED_PIPELINE'


def output_dir(stage: int, name: str) -> Path:
    p = pipeline_root() / 'outputs' / f'{stage:02d}_{name}'
    p.mkdir(parents=True, exist_ok=True)
    return p


def read_csv(rel: str) -> pd.DataFrame:
    return pd.read_csv(project_root() / rel)


def save_csv(df: pd.DataFrame, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(path, index=False)


def norm_name(s) -> str:
    if pd.isna(s): return ''
    s = str(s).upper().replace('–','-').replace('—','-')
    s = re.sub(r'[^A-Z0-9]+', '', s)
    return s


def safe_rmse(y_true, y_pred):
    from sklearn.metrics import mean_squared_error
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def regression_metrics(y_true, y_pred) -> dict:
    from sklearn.metrics import mean_absolute_error, r2_score
    return {
        'n': int(len(y_true)),
        'MAE': float(mean_absolute_error(y_true, y_pred)),
        'RMSE': safe_rmse(y_true, y_pred),
        'R2': float(r2_score(y_true, y_pred)) if len(set(np.asarray(y_true))) > 1 else np.nan,
    }


def classification_metrics(y_true, y_pred) -> dict:
    from sklearn.metrics import accuracy_score, f1_score, confusion_matrix
    labels=np.unique(np.asarray(y_true))
    cm=confusion_matrix(y_true,y_pred,labels=labels)
    recalls=np.divide(np.diag(cm),cm.sum(axis=1),out=np.zeros(len(labels),dtype=float),where=cm.sum(axis=1)!=0)
    bal=float(np.mean(recalls)) if len(recalls) else np.nan
    return {
        'n': int(len(y_true)),
        'accuracy': float(accuracy_score(y_true, y_pred)),
        'balanced_accuracy': bal,
        'f1_macro': float(f1_score(y_true, y_pred, average='macro', zero_division=0)),
    }


def grouped_train_val_test(df: pd.DataFrame, group_col='genotype_id_candidate', train=0.70, val=0.15, seed=SEED):
    from sklearn.model_selection import GroupShuffleSplit
    groups = df[group_col].astype(str).fillna('__MISSING__')
    gss = GroupShuffleSplit(n_splits=1, train_size=train, random_state=seed)
    tr_idx, temp_idx = next(gss.split(df, groups=groups))
    tr = df.iloc[tr_idx].copy()
    temp = df.iloc[temp_idx].copy()
    temp_groups = temp[group_col].astype(str).fillna('__MISSING__')
    val_fraction_of_temp = val / (1-train)
    gss2 = GroupShuffleSplit(n_splits=1, train_size=val_fraction_of_temp, random_state=seed+1)
    va_idx, te_idx = next(gss2.split(temp, groups=temp_groups))
    va = temp.iloc[va_idx].copy(); te = temp.iloc[te_idx].copy()
    return tr.reset_index(drop=True), va.reset_index(drop=True), te.reset_index(drop=True)


def numeric_feature_frame(df, features):
    x = df[features].copy()
    for c in features:
        x[c] = pd.to_numeric(x[c], errors='coerce')
    return x


def try_xgb_regressor(seed=SEED, n_jobs=-1):
    try:
        from xgboost import XGBRegressor
        return XGBRegressor(n_estimators=250, max_depth=3, learning_rate=0.05,
                            subsample=0.9, colsample_bytree=0.9,
                            random_state=seed, n_jobs=n_jobs, objective='reg:squarederror')
    except Exception:
        return None


def try_xgb_classifier(seed=SEED, n_jobs=-1, num_class=None):
    try:
        from xgboost import XGBClassifier
        kwargs = dict(n_estimators=250, max_depth=3, learning_rate=0.05,
                      subsample=0.9, colsample_bytree=0.9,
                      random_state=seed, n_jobs=n_jobs, eval_metric='mlogloss')
        if num_class and num_class > 2:
            kwargs.update({'objective':'multi:softprob', 'num_class':int(num_class)})
        else:
            kwargs.update({'objective':'binary:logistic'})
        return XGBClassifier(**kwargs)
    except Exception:
        return None


def make_preprocessor(scale=False):
    from sklearn.impute import SimpleImputer
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    steps=[('imputer', SimpleImputer(strategy='median', add_indicator=True))]
    if scale:
        steps.append(('scaler', StandardScaler()))
    return Pipeline(steps)


def write_exception(path: Path, e: Exception):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(traceback.format_exc(), encoding='utf-8')


def json_dump(obj, path: Path):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2, default=str), encoding='utf-8')
