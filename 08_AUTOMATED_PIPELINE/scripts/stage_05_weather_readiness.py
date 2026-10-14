import pandas as pd, numpy as np
from pathlib import Path
from common import *

def main():
    log('STEP 5/9: PREPARING WEATHER-DRIVEN DISEASE RISK DATA')
    out=output_dir(5,'WEATHER_RISK')
    w=read_csv('02_MASTER_DATA/07_weather_monthly_2023.csv')
    save_csv(w,out/'WEATHER_MONTHLY_2023_FEATURES.csv')
    num=[c for c in w.columns if c not in ['document_id','source_page','year','month']]
    summary={}
    for c in num:
        s=pd.to_numeric(w[c],errors='coerce')
        summary[c+'_mean']=s.mean(); summary[c+'_min']=s.min(); summary[c+'_max']=s.max(); summary[c+'_std']=s.std()
    save_csv(pd.DataFrame([summary]),out/'WEATHER_2023_SUMMARY_FEATURES.csv')

    template=Path(pipeline_root()/ 'config' / 'WEATHER_DISEASE_LINKED.csv')
    if not template.exists():
        blocker=pd.DataFrame([{'stage':'weather_risk','status':'BLOCKED_PENDING_LINKAGE','weather_rows':len(w),'disease_month_or_day_target_rows':0,'reason':'Monthly weather exists, but no verified date/location aligned disease outcome table was supplied. Use config/WEATHER_DISEASE_LINKED_TEMPLATE.csv as the required schema.'}])
        save_csv(blocker,out/'WEATHER_MODEL_BLOCKER.csv')
        (out/'NEXT_DATA_NEEDED.txt').write_text('Copy config/WEATHER_DISEASE_LINKED_TEMPLATE.csv to config/WEATHER_DISEASE_LINKED.csv and fill it with verified date/location aligned disease observations for the same season/site. Then rerun step 5.\n',encoding='utf-8')
        return

    x=pd.read_csv(template)
    required=['date','location','disease','disease_score','max_temp_c','min_temp_c','rh_i_pct','rh_ii_pct','wind_speed_km','sunshine_hours','actual_rainfall_mm','actual_rainy_days']
    missing=[c for c in required if c not in x.columns]
    if missing:
        raise ValueError('WEATHER_DISEASE_LINKED.csv missing columns: '+', '.join(missing))
    x['date']=pd.to_datetime(x['date'],errors='coerce'); x=x.dropna(subset=['date','disease_score']).copy()
    for c in required[3:]: x[c]=pd.to_numeric(x[c],errors='coerce')
    if len(x)<30:
        save_csv(pd.DataFrame([{'status':'BLOCKED_TOO_FEW_ROWS','rows':len(x),'reason':'Need more aligned observations for a meaningful time-aware model.'}]),out/'WEATHER_MODEL_BLOCKER.csv')
        log('WEATHER RISK MODEL DEFERRED: too few aligned rows')
        return
    features=['max_temp_c','min_temp_c','rh_i_pct','rh_ii_pct','wind_speed_km','sunshine_hours','actual_rainfall_mm','actual_rainy_days']
    x=x.sort_values('date').reset_index(drop=True)
    # Time-aware holdout: last 20% is test, no random shuffling.
    cut=max(1,int(len(x)*0.8)); tr=x.iloc[:cut].copy(); te=x.iloc[cut:].copy()
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.ensemble import ExtraTreesRegressor
    from sklearn.metrics import mean_absolute_error, r2_score, mean_squared_error
    model=Pipeline([('imp',SimpleImputer(strategy='median',add_indicator=True)),('m',ExtraTreesRegressor(n_estimators=400,min_samples_leaf=2,random_state=SEED,n_jobs=-1))])
    log('Training weather-driven disease regression model...')
    model.fit(tr[features],tr.disease_score)
    pred=model.predict(te[features])
    metrics=pd.DataFrame([{'model':'ExtraTrees','n_train':len(tr),'n_test':len(te),'MAE':mean_absolute_error(te.disease_score,pred),'RMSE':np.sqrt(mean_squared_error(te.disease_score,pred)),'R2':r2_score(te.disease_score,pred) if te.disease_score.nunique()>1 else np.nan}])
    save_csv(metrics,out/'WEATHER_DISEASE_MODEL_METRICS.csv')
    save_csv(pd.DataFrame({'date':te.date,'disease':te.disease,'actual_score':te.disease_score,'predicted_score':pred}),out/'WEATHER_DISEASE_TEST_PREDICTIONS.csv')
    import joblib; joblib.dump(model,out/'WEATHER_DISEASE_EXTRATREES.joblib')
    log('Weather-driven disease regression model done')

if __name__=='__main__': main()
