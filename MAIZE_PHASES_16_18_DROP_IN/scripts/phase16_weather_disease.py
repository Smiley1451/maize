from __future__ import annotations
from pathlib import Path
import sys, json, warnings
import numpy as np
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_16_18 import *

from sklearn.pipeline import Pipeline
from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import Ridge, LogisticRegression
from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, HistGradientBoostingRegressor, RandomForestClassifier, ExtraTreesClassifier
from sklearn.model_selection import TimeSeriesSplit
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score, balanced_accuracy_score, f1_score
from joblib import dump

OUT16 = phase_out('16_WEATHER_DISEASE')
LINKED = BASE / 'config' / 'WEATHER_DISEASE_LINKED.csv'

DATE_ALIASES=['date','observation_date','weather_date','timestamp','datetime']
LOCATION_ALIASES=['location','site','station']
SCORE_ALIASES=['disease_score','tlb_disease_score','sdm_pdi','disease_value','severity']
CLASS_ALIASES=['risk_label','disease_risk','risk','class_label','disease_class']


def first_col(df, aliases):
    for c in aliases:
        if c in df.columns: return c
    return None


def build_weather_features(df, date_col):
    d=df.copy()
    d[date_col]=pd.to_datetime(d[date_col], errors='coerce')
    d=d[pd.notna(d[date_col])].sort_values(date_col).reset_index(drop=True)
    numeric=[c for c in d.select_dtypes(include=[np.number]).columns if c not in {'disease_score','tlb_disease_score','sdm_pdi','disease_value','severity'}]
    for c in numeric:
        d[c]=pd.to_numeric(d[c], errors='coerce')
        if len(d)>=3:
            d[f'{c}_roll3']=d[c].rolling(3,min_periods=2).mean()
        if len(d)>=7:
            d[f'{c}_roll7']=d[c].rolling(7,min_periods=3).mean()
            d[f'{c}_sum7']=d[c].rolling(7,min_periods=3).sum()
    d['date_year']=d[date_col].dt.year
    d['date_month']=d[date_col].dt.month
    d['date_dayofyear']=d[date_col].dt.dayofyear
    return d


def optional_model(d, date_col, score_col, class_col):
    status=[]
    numeric_features=[c for c in d.select_dtypes(include=[np.number]).columns if c not in {score_col}]
    exclude={date_col,'date_year','date_month','date_dayofyear'}
    features=[c for c in numeric_features if c not in exclude and 'risk' not in c.lower() and 'class' not in c.lower()]
    if not features:
        save(pd.DataFrame([{'status':'NO_NUMERIC_WEATHER_FEATURES'}]), OUT16/'WEATHER_MODEL_STATUS.csv'); return
    n_dates=d[date_col].nunique(); n=len(d)
    if n < 12 or n_dates < 8:
        save(pd.DataFrame([{'status':'INSUFFICIENT_TIME_POINTS','rows':n,'unique_dates':n_dates}]), OUT16/'WEATHER_MODEL_STATUS.csv'); return
    split=max(int(n*0.7), 1)
    if split >= n: split=n-1
    tr=d.iloc[:split]; te=d.iloc[split:]
    Xtr=tr[features]; Xte=te[features]
    rows=[]
    reg_models={
        'Ridge': Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',Ridge(alpha=10.0))]),
        'RandomForest': Pipeline([('imputer',SimpleImputer(strategy='median')),('model',RandomForestRegressor(n_estimators=400,random_state=SEED,n_jobs=1))]),
        'ExtraTrees': Pipeline([('imputer',SimpleImputer(strategy='median')),('model',ExtraTreesRegressor(n_estimators=400,random_state=SEED,n_jobs=1))]),
        'HistGradientBoosting': Pipeline([('imputer',SimpleImputer(strategy='median')),('model',HistGradientBoostingRegressor(max_iter=250,random_state=SEED))])
    }
    if score_col and score_col in d.columns:
        y=pd.to_numeric(d[score_col],errors='coerce')
        keep=y.notna(); tr=d.iloc[:split][keep.iloc[:split].to_numpy()]; te=d.iloc[split:][keep.iloc[split:].to_numpy()]
        if len(tr)>=5 and len(te)>=2:
            for name,m in reg_models.items():
                m.fit(tr[features],pd.to_numeric(tr[score_col],errors='coerce')); p=m.predict(te[features]); met=metric_regression(te[score_col],p)
                rows.append({'task':'regression','model':name,'MAE':met['MAE'],'RMSE':met['RMSE'],'R2':met['R2'],'train_rows':len(tr),'test_rows':len(te)})
                dump({'model':m,'features':features,'target':score_col,'model_name':name,'task':'weather_disease_regression','split_rule':'chronological 70/30'}, MODELS/f'weather_{name.lower()}_regression.joblib')
    if class_col and class_col in d.columns:
        work=d[d[class_col].notna()].copy(); classes=work[class_col].astype(str).str.strip(); work=work[classes.ne('')].copy(); classes=work[class_col].astype(str)
        if classes.nunique()>=2 and len(work)>=12 and work[date_col].nunique()>=8:
            s=max(int(len(work)*0.7),1); tr=work.iloc[:s]; te=work.iloc[s:]
            if tr[class_col].nunique()>=2 and len(te)>=2:
                cls_models={
                    'LogisticRegression': Pipeline([('imputer',SimpleImputer(strategy='median')),('scale',StandardScaler()),('model',LogisticRegression(max_iter=3000))]),
                    'RandomForest': Pipeline([('imputer',SimpleImputer(strategy='median')),('model',RandomForestClassifier(n_estimators=400,random_state=SEED,n_jobs=1,class_weight='balanced'))]),
                    'ExtraTrees': Pipeline([('imputer',SimpleImputer(strategy='median')),('model',ExtraTreesClassifier(n_estimators=400,random_state=SEED,n_jobs=1,class_weight='balanced'))])
                }
                for name,m in cls_models.items():
                    m.fit(tr[features],tr[class_col].astype(str)); p=m.predict(te[features]); met=metric_classification(te[class_col].astype(str),p)
                    rows.append({'task':'classification','model':name,'accuracy':met['accuracy'],'balanced_accuracy':met['balanced_accuracy'],'f1_macro':met['f1_macro'],'train_rows':len(tr),'test_rows':len(te)})
                    dump({'model':m,'features':features,'target':class_col,'model_name':name,'task':'weather_disease_classification','split_rule':'chronological 70/30','classes':sorted(work[class_col].astype(str).unique())}, MODELS/f'weather_{name.lower()}_classifier.joblib')
    save(pd.DataFrame(rows), OUT16/'WEATHER_MODEL_RESULTS.csv')
    save(pd.DataFrame([{'status':'TRAINED' if rows else 'NO_MODEL_TRAINED','rows':len(d),'unique_dates':d[date_col].nunique(),'feature_count':len(features)}]), OUT16/'WEATHER_MODEL_STATUS.csv')


def main():
    log('='*62); log('PHASE 16: WEATHER-DRIVEN DISEASE FORECASTING'); log('='*62)
    candidates=[]
    if LINKED.exists(): candidates.append(('explicit_linked_file',LINKED))
    for rel in cfg().get('weather',{}).get('default_candidate_files',[]):
        p=ROOT/rel
        if p.exists(): candidates.append(('existing_project_file',p))
    if not candidates:
        log('No date/location-aligned weather+disease linked dataset found.')
        save(pd.DataFrame([{'status':'WAITING_FOR_ALIGNED_DATA','reason':'No verified linked weather+disease CSV found','required':'config/WEATHER_DISEASE_LINKED.csv'}]), OUT16/'WEATHER_MODEL_STATUS.csv')
        (OUT16/'NEXT_DATA_NEEDED.txt').write_text('Provide date/location-aligned weather + TLB/SDM labels in config/WEATHER_DISEASE_LINKED.csv. The template is in config/WEATHER_DISEASE_LINKED_TEMPLATE.csv.\n',encoding='utf-8')
        save(pd.DataFrame([{'required_column':'date','purpose':'time alignment'},{'required_column':'location','purpose':'site alignment'},{'required_column':'disease_score or risk_label','purpose':'supervised target'},{'required_column':'numeric weather variables','purpose':'predictor features'}]), OUT16/'WEATHER_INPUT_REQUIREMENTS.csv')
        save(pd.DataFrame([{'file':'config/WEATHER_DISEASE_LINKED.csv','present':False,'used_for_training':False}]), OUT16/'WEATHER_LINKAGE_AUDIT.csv')
        log('PHASE 16 DONE: weather forecasting is blocked only by missing aligned labels; no data was fabricated.')
        return
    source_type, path=candidates[0]
    log(f'Using weather candidate: {path}')
    d=pd.read_csv(path)
    date_col=first_col(d,DATE_ALIASES)
    loc_col=first_col(d,LOCATION_ALIASES)
    score_col=first_col(d,SCORE_ALIASES)
    class_col=first_col(d,CLASS_ALIASES)
    audit={'source':str(path),'source_type':source_type,'rows':len(d),'date_column':date_col or '','location_column':loc_col or '','score_column':score_col or '','class_column':class_col or ''}
    save(pd.DataFrame([audit]), OUT16/'WEATHER_LINKAGE_AUDIT.csv')
    if source_type=='explicit_linked_file' and (date_col is None or (score_col is None and class_col is None)):
        save(pd.DataFrame([{'status':'INPUT_ERROR','reason':'Explicit linked file is missing required date and disease target columns'}]), OUT16/'WEATHER_MODEL_STATUS.csv')
        raise ValueError('Explicit WEATHER_DISEASE_LINKED.csv is missing date and disease target columns.')
    if date_col is None:
        save(pd.DataFrame([{'status':'REFERENCE_WEATHER_ONLY','reason':'Weather file found but no date column for time-aware modeling'}]), OUT16/'WEATHER_MODEL_STATUS.csv')
        log('PHASE 16 DONE: weather reference data found, but no date field is available for time-aware training.')
        return
    d=build_weather_features(d,date_col)
    save(d, OUT16/'WEATHER_DERIVED_FEATURES.csv')
    if source_type!='explicit_linked_file' or (score_col is None and class_col is None):
        save(pd.DataFrame([{'status':'WAITING_FOR_ALIGNED_DATA','reason':'Weather predictors available, but aligned disease labels are not available'}]), OUT16/'WEATHER_MODEL_STATUS.csv')
        (OUT16/'NEXT_DATA_NEEDED.txt').write_text('Use config/WEATHER_DISEASE_LINKED.csv with date, location, and aligned disease_score and/or risk_label.\n',encoding='utf-8')
        log('PHASE 16 DONE: weather features prepared; disease labels are not aligned, so no forecast model was claimed.')
        return
    optional_model(d,date_col,score_col,class_col)
    log('PHASE 16 DONE: weather-driven disease modeling path complete.')

if __name__=='__main__': main()
