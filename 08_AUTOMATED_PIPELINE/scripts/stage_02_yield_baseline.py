from pathlib import Path
import pandas as pd, numpy as np
from common import *

FEATURES=['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage']
TARGET_VARS=['yield_t_per_ha','yield_kg_per_ha','grain_yield_kg_per_ha']


def build_dataset():
    d=read_csv('02_MASTER_DATA/MASTER_MAIZE_ALL_DATA.csv')
    x=d[d['variable'].isin(TARGET_VARS)].copy()
    x['entity_str']=x['entity_name'].astype(str)
    x=x[~x['entity_str'].str.contains(r'mean|CV|C\.V|CD|C\.D',case=False,regex=True,na=False)].copy()
    x['yield_kg_ha']=np.where(x['variable'].eq('yield_t_per_ha'), pd.to_numeric(x['value_numeric'],errors='coerce')*1000, pd.to_numeric(x['value_numeric'],errors='coerce'))
    # Only genotype/check rows with numeric target.
    x=x[x['yield_kg_ha'].notna()].copy()
    keep=['record_id','document_id','experiment_id','experiment_no','trial_no','entity_name','year','season','location','source_page','variable','unit','yield_kg_ha']+FEATURES
    # pivot long observations into genotype rows by experiment/entity
    raw_feature_vars=['days_50_pollen_shedding','days_50_silking','days_75_dry_husk','plant_height_cm','ear_height_cm','plant_stand_000_per_ha','shelling_pct']
    obs=d[d['variable'].isin(raw_feature_vars)].copy()
    obs['num']=pd.to_numeric(obs['value_numeric'],errors='coerce')
    wide=obs.pivot_table(index=['experiment_id','entity_name'],columns='variable',values='num',aggfunc='median').reset_index()
    rename={
      'days_50_pollen_shedding':'days_to_50_percent_pollen_shedding',
      'days_50_silking':'days_to_50_percent_silking',
      'days_75_dry_husk':'days_to_75_percent_dry_husk',
      'plant_height_cm':'plant_height','ear_height_cm':'ear_height',
      'plant_stand_000_per_ha':'plant_stand','shelling_pct':'shelling_percentage'
    }
    wide=wide.rename(columns=rename)
    meta=d.drop_duplicates(['experiment_id','entity_name'])[['experiment_id','experiment_no','trial_no','document_id','year','season','location']]
    out=x[['record_id','document_id','experiment_id','experiment_no','trial_no','entity_name','year','season','location','source_page','unit','yield_kg_ha']].drop_duplicates()
    out=out.merge(wide,on=['experiment_id','entity_name'],how='left',suffixes=('','_feat'))
    out['genotype_key']=out['entity_name'].map(norm_name)
    out=out[out['genotype_key'].ne('')].copy()
    return out


def main():
    log('STEP 2/9: TRAINING YIELD REGRESSION MODELS')
    out=output_dir(2,'YIELD_BASELINE')
    df=build_dataset()
    save_csv(df,out/'ML_YIELD_PIPELINE_READY.csv')
    # deterministic grouped split
    df['genotype_id_candidate']=df['genotype_key']
    tr,va,te=grouped_train_val_test(df,'genotype_id_candidate')
    for part,name in [(tr,'train'),(va,'validation'),(te,'test')]: save_csv(part,out/f'ML_YIELD_{name}.csv')
    models={}
    from sklearn.pipeline import Pipeline
    from sklearn.impute import SimpleImputer
    from sklearn.dummy import DummyRegressor
    from sklearn.linear_model import Ridge
    from sklearn.ensemble import RandomForestRegressor, ExtraTreesRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor
    models['DummyMean']=Pipeline([('imputer',SimpleImputer(strategy='median',add_indicator=True)),('model',DummyRegressor(strategy='mean'))])
    models['Ridge']=Pipeline([('imputer',SimpleImputer(strategy='median',add_indicator=True)),('model',Ridge(alpha=10.0))])
    models['RandomForest']=Pipeline([('imputer',SimpleImputer(strategy='median',add_indicator=True)),('model',RandomForestRegressor(n_estimators=400,min_samples_leaf=2,random_state=SEED,n_jobs=-1))])
    models['ExtraTrees']=Pipeline([('imputer',SimpleImputer(strategy='median',add_indicator=True)),('model',ExtraTreesRegressor(n_estimators=400,min_samples_leaf=2,random_state=SEED,n_jobs=-1))])
    models['GradientBoosting']=Pipeline([('imputer',SimpleImputer(strategy='median',add_indicator=True)),('model',GradientBoostingRegressor(random_state=SEED,n_estimators=250,max_depth=2,learning_rate=0.04,loss='huber'))])
    models['HistGradientBoosting']=Pipeline([('imputer',SimpleImputer(strategy='median',add_indicator=True)),('model',HistGradientBoostingRegressor(max_iter=250,learning_rate=0.05,max_leaf_nodes=15,l2_regularization=1.0,random_state=SEED))])
    xb=try_xgb_regressor()
    if xb is not None:
        models['XGBoost']=Pipeline([('imputer',SimpleImputer(strategy='median',add_indicator=True)),('model',xb)])
        log('XGBoost available')
    else: log('XGBoost not available; sklearn models will be used')
    rows=[]; pred_rows=[]
    Xtr=numeric_feature_frame(tr,FEATURES); Xva=numeric_feature_frame(va,FEATURES); Xte=numeric_feature_frame(te,FEATURES)
    ytr=tr.yield_kg_ha; yva=va.yield_kg_ha; yte=te.yield_kg_ha
    for name,m in models.items():
        log(f'Training {name} yield model...')
        m.fit(Xtr,ytr)
        pva=m.predict(Xva); pte=m.predict(Xte)
        mv=regression_metrics(yva,pva); mt=regression_metrics(yte,pte)
        rows.append({'model':name,'validation_MAE':mv['MAE'],'validation_RMSE':mv['RMSE'],'validation_R2':mv['R2'],'test_MAE':mt['MAE'],'test_RMSE':mt['RMSE'],'test_R2':mt['R2']})
        tmp=te[['record_id','entity_name','genotype_id_candidate','yield_kg_ha']].copy(); tmp['prediction_'+name]=pte; pred_rows.append(tmp[['record_id','entity_name','genotype_id_candidate','yield_kg_ha','prediction_'+name]])
        import joblib; joblib.dump(m,out/f'yield_{name}.joblib')
        log(f'{name} yield model done')
    comp=pd.DataFrame(rows).sort_values(['validation_RMSE','validation_MAE'])
    save_csv(comp,out/'YIELD_MODEL_COMPARISON.csv')
    pp=pred_rows[0]
    for z in pred_rows[1:]: pp=pp.merge(z,on=['record_id','entity_name','genotype_id_candidate','yield_kg_ha'],how='outer')
    save_csv(pp,out/'YIELD_TEST_PREDICTIONS.csv')
    comp.iloc[:1].to_csv(out/'YIELD_BASELINE_SELECTED.csv',index=False)
    (out/'README.txt').write_text('Reproducible baseline yield regression. Target is rebuilt from source observations and standardized to kg/ha: yield_t_per_ha x 1000; kg/ha variables retained. Statistical rows are excluded. Model selection is diagnostic until later grouped cross-validation/tuning.\n',encoding='utf-8')
    log('YIELD BASELINE MODEL TRAINING DONE')

if __name__=='__main__': main()
