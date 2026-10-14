from __future__ import annotations
import json, re, traceback
from pathlib import Path
from datetime import datetime
import numpy as np
import pandas as pd

SEED=42


def root()->Path:
    return Path(__file__).resolve().parents[2]


def base()->Path:
    return root()/"10_12_NEXT_PHASES"


def out(name:str)->Path:
    p=base()/"outputs"/name
    p.mkdir(parents=True, exist_ok=True)
    return p


def log(msg:str):
    print(f"[{datetime.now():%Y-%m-%d %H:%M:%S}] {msg}", flush=True)


def norm_name(s):
    if pd.isna(s): return ""
    s=str(s).upper().replace("–","-").replace("—","-")
    s=re.sub(r"\(.*?\)", " ", s)
    s=re.sub(r"[^A-Z0-9]+", "", s)
    return s


def save(df,path):
    path.parent.mkdir(parents=True,exist_ok=True)
    df.to_csv(path,index=False)


def read(rel):
    return pd.read_csv(root()/rel)


def load_config():
    p=base()/"config"/"phase_config.json"
    return json.loads(p.read_text(encoding='utf-8'))


def exception_file(path,e):
    path.parent.mkdir(parents=True,exist_ok=True)
    path.write_text(traceback.format_exc(),encoding='utf-8')


def yield_to_kg_ha(value,unit):
    try: v=float(value)
    except Exception: return np.nan, "INVALID"
    u='' if pd.isna(unit) else str(unit).strip().lower().replace(' ','')
    if 't/ha' in u or u in {'tperha','tonne/ha','tonnes/ha'}:
        return v*1000.0, 'T_PER_HA_TO_KG_PER_HA'
    if 'kg/ha' in u or u in {'kgperha','kg-ha'}:
        return v, 'KG_PER_HA_AS_IS'
    return np.nan, 'UNKNOWN_UNIT'


def regression_metrics(y,p):
    from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
    y=np.asarray(y,float); p=np.asarray(p,float)
    return {'n':len(y),'MAE':float(mean_absolute_error(y,p)), 'RMSE':float(np.sqrt(mean_squared_error(y,p))), 'R2':float(r2_score(y,p)) if len(np.unique(y))>1 else np.nan}


def classification_metrics(y_true,pred):
    # Handles single-class folds explicitly. Newer scikit-learn versions emit a
    # UserWarning when confusion_matrix sees a 1x1 case. That warning is not a
    # modeling failure, but Windows PowerShell can surface native stderr as an
    # exception. We therefore calculate the one-class case directly.
    from sklearn.metrics import accuracy_score, confusion_matrix
    yt=list(map(str,y_true)); yp=list(map(str,pred))
    labels=sorted(set(yt) | set(yp))
    accuracy=float(accuracy_score(yt,yp))
    if len(labels)==1:
        # With one observed/predicted class, the fold is perfectly classified
        # because both y_true and y_pred contain that same sole label.
        return {
          'n':len(yt),
          'accuracy':accuracy,
          'balanced_accuracy':1.0,
          'f1_macro':1.0
        }
    cm=confusion_matrix(yt,yp,labels=labels)
    row_totals=cm.sum(axis=1)
    recalls=np.divide(np.diag(cm),row_totals,out=np.zeros(len(labels),dtype=float),where=row_totals!=0)
    balanced=float(np.mean(recalls[row_totals!=0])) if np.any(row_totals!=0) else np.nan
    col_totals=cm.sum(axis=0)
    f1s=[]
    for i in range(len(labels)):
        tp=float(cm[i,i]); precision=tp/float(col_totals[i]) if col_totals[i] else 0.0; recall=float(recalls[i])
        f1=2*precision*recall/(precision+recall) if (precision+recall) else 0.0
        f1s.append(f1)
    f1_macro=float(np.mean(f1s)) if f1s else np.nan
    return {
      'n':len(yt),
      'accuracy':accuracy,
      'balanced_accuracy':balanced,
      'f1_macro':f1_macro
    }


def make_reg_models(seed=SEED):
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, HistGradientBoostingRegressor
    models={
      'Ridge':Ridge(alpha=10.0),
      'RandomForest':RandomForestRegressor(n_estimators=120,random_state=seed,n_jobs=1,min_samples_leaf=2),
      'ExtraTrees':ExtraTreesRegressor(n_estimators=120,random_state=seed,n_jobs=1,min_samples_leaf=2),
      'HistGradientBoosting':HistGradientBoostingRegressor(max_iter=250,random_state=seed)
    }
    try:
        from xgboost import XGBRegressor
        models['XGBoost']=XGBRegressor(n_estimators=250,max_depth=3,learning_rate=0.05,subsample=0.9,colsample_bytree=0.9,random_state=seed,n_jobs=1,objective='reg:squarederror')
    except Exception:
        pass
    return models


def make_clf_models(seed=SEED):
    from sklearn.linear_model import LogisticRegression
    from sklearn.svm import SVC
    from sklearn.ensemble import RandomForestClassifier, ExtraTreesClassifier, HistGradientBoostingClassifier
    models={
      'LogisticRegression':LogisticRegression(max_iter=3000,class_weight='balanced'),
      'SVM':SVC(class_weight='balanced'),
      'RandomForest':RandomForestClassifier(n_estimators=120,random_state=seed,n_jobs=1,min_samples_leaf=2,class_weight='balanced'),
      'ExtraTrees':ExtraTreesClassifier(n_estimators=120,random_state=seed,n_jobs=1,min_samples_leaf=2,class_weight='balanced'),
      'HistGradientBoosting':HistGradientBoostingClassifier(max_iter=250,random_state=seed)
    }
    return models


def pipeline(model,scale=False):
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    steps=[('imputer',SimpleImputer(strategy='median',add_indicator=True)),('model',model)]
    if scale: steps.insert(1,('scaler',StandardScaler()))
    return Pipeline(steps)
