from common_next import *

OUT=out('PHASE_12_GENERALIZATION_VALIDATION'); DATA=out('PHASE_11_PRODUCTION_DATASETS')
FEATURES=['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage']

def eval_reg(df,name,target):
    from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
    from sklearn.base import clone
    d=df.copy(); d[target]=pd.to_numeric(d[target],errors='coerce'); d=d[d[target].notna()].reset_index(drop=True)
    if len(d)<20 or d.genotype_id.nunique()<3:
        return pd.DataFrame([{'dataset':name,'scheme':'SKIPPED','reason':'insufficient_rows_or_genotype_groups','n':len(d),'groups':d.genotype_id.nunique()}]),pd.DataFrame()
    X=d[FEATURES].apply(pd.to_numeric,errors='coerce'); y=d[target]; models=make_reg_models(); summaries=[]; folds=[]
    cv=GroupKFold(n_splits=min(5,d.genotype_id.nunique()))
    for mn,model in models.items():
        log(f'TRAINING {name} {mn} regression model - grouped CV...'); pipe=pipeline(model,scale=(mn=='Ridge')); mm=[]
        for fi,(tr,te) in enumerate(cv.split(X,y,groups=d.genotype_id),1):
            est=clone(pipe); est.fit(X.iloc[tr],y.iloc[tr]); pr=est.predict(X.iloc[te]); m=regression_metrics(y.iloc[te],pr); m.update(dataset=name,model=mn,scheme='GroupKFold',fold=fi); folds.append(m); mm.append(m)
        summaries.append({'dataset':name,'model':mn,'scheme':'GroupKFold','folds':len(mm),'n':sum(m['n'] for m in mm),'mean_MAE':np.mean([m['MAE'] for m in mm]),'mean_RMSE':np.mean([m['RMSE'] for m in mm]),'mean_R2':np.nanmean([m['R2'] for m in mm])})
        log(f'{name} {mn} regression model done')
    if d.experiment_id.nunique()>=3:
        logo=LeaveOneGroupOut()
        for mn,model in models.items():
            pipe=pipeline(model,scale=(mn=='Ridge')); mm=[]
            for fi,(tr,te) in enumerate(logo.split(X,y,groups=d.experiment_id),1):
                if y.iloc[tr].nunique()<2: continue
                est=clone(pipe); est.fit(X.iloc[tr],y.iloc[tr]); pr=est.predict(X.iloc[te]); m=regression_metrics(y.iloc[te],pr); m.update(dataset=name,model=mn,scheme='LeaveOneExperimentOut',fold=fi,test_experiment=str(d.iloc[te].experiment_id.iloc[0])); folds.append(m); mm.append(m)
            if mm: summaries.append({'dataset':name,'model':mn,'scheme':'LeaveOneExperimentOut','folds':len(mm),'n':sum(m['n'] for m in mm),'mean_MAE':np.mean([m['MAE'] for m in mm]),'mean_RMSE':np.mean([m['RMSE'] for m in mm]),'mean_R2':np.nanmean([m['R2'] for m in mm])})
    return pd.DataFrame(summaries),pd.DataFrame(folds)

def eval_clf(df,name,target):
    from sklearn.model_selection import GroupKFold, LeaveOneGroupOut
    from sklearn.base import clone
    d=df.copy(); d['class_label']=d[target].astype(str).str.strip(); d=d[d.class_label.ne('') & d.class_label.ne('nan')].reset_index(drop=True)
    if len(d)<25 or d.genotype_id.nunique()<3 or d.class_label.nunique()<2:
        return pd.DataFrame([{'dataset':name,'scheme':'SKIPPED','reason':'insufficient_rows_or_classes','n':len(d),'groups':d.genotype_id.nunique()}]),pd.DataFrame()
    X=d[FEATURES].apply(pd.to_numeric,errors='coerce'); y=d.class_label; models=make_clf_models(); summaries=[]; folds=[]
    cv=GroupKFold(n_splits=min(5,d.genotype_id.nunique()))
    for mn,model in models.items():
        log(f'TRAINING {name} {mn} classification model - grouped CV...'); pipe=pipeline(model,scale=(mn in {'LogisticRegression','SVM'})); mm=[]
        for fi,(tr,te) in enumerate(cv.split(X,y,groups=d.genotype_id),1):
            if y.iloc[tr].nunique()<2: continue
            est=clone(pipe); est.fit(X.iloc[tr],y.iloc[tr]); pr=est.predict(X.iloc[te]); m=classification_metrics(y.iloc[te],pr); m.update(dataset=name,model=mn,scheme='GroupKFold',fold=fi); folds.append(m); mm.append(m)
        if mm: summaries.append({'dataset':name,'model':mn,'scheme':'GroupKFold','folds':len(mm),'n':sum(m['n'] for m in mm),'mean_accuracy':np.mean([m['accuracy'] for m in mm]),'mean_balanced_accuracy':np.mean([m['balanced_accuracy'] for m in mm]),'mean_f1_macro':np.mean([m['f1_macro'] for m in mm])})
        log(f'{name} {mn} classification model done')
    if d.experiment_id.nunique()>=3:
        logo=LeaveOneGroupOut()
        for mn,model in models.items():
            pipe=pipeline(model,scale=(mn in {'LogisticRegression','SVM'})); mm=[]
            for fi,(tr,te) in enumerate(logo.split(X,y,groups=d.experiment_id),1):
                if y.iloc[tr].nunique()<2: continue
                # If test contains unseen labels, still evaluate accuracy but flag the fold.
                unseen=sorted(set(y.iloc[te])-set(y.iloc[tr]))
                est=clone(pipe); est.fit(X.iloc[tr],y.iloc[tr]); pr=est.predict(X.iloc[te]); m=classification_metrics(y.iloc[te],pr); m.update(dataset=name,model=mn,scheme='LeaveOneExperimentOut',fold=fi,test_experiment=str(d.iloc[te].experiment_id.iloc[0]),unseen_test_classes='|'.join(unseen)); folds.append(m); mm.append(m)
            if mm: summaries.append({'dataset':name,'model':mn,'scheme':'LeaveOneExperimentOut','folds':len(mm),'n':sum(m['n'] for m in mm),'mean_accuracy':np.mean([m['accuracy'] for m in mm]),'mean_balanced_accuracy':np.mean([m['balanced_accuracy'] for m in mm]),'mean_f1_macro':np.mean([m['f1_macro'] for m in mm])})
    return pd.DataFrame(summaries),pd.DataFrame(folds)

def main():
    log('=============================================================='); log('PHASE 12: GENERALIZATION VALIDATION'); log('==============================================================')
    reg=[]; clf=[]; folds=[]
    y=DATA/'YIELD_PRODUCTION_STRICT.csv'
    if y.exists():
        a,b=eval_reg(pd.read_csv(y),'YIELD','yield_kg_ha'); reg.append(a); folds.append(b)
    for pfx,target,cls in [('TLB','tlb_disease_score','tlb_reaction'),('SDM','sdm_pdi','sdm_reaction')]:
        p=DATA/f'{pfx}_PRODUCTION_STRICT.csv'
        if p.exists():
            d=pd.read_csv(p); a,b=eval_reg(d,pfx,target); reg.append(a); folds.append(b); c,e=eval_clf(d,pfx+'_CLASSIFICATION',cls); clf.append(c); folds.append(e)
    regdf=pd.concat(reg,ignore_index=True) if reg else pd.DataFrame(); clfdf=pd.concat(clf,ignore_index=True) if clf else pd.DataFrame();
    if not regdf.empty: save(regdf,OUT/'REGRESSION_GENERALIZATION_SUMMARY.csv')
    if not clfdf.empty: save(clfdf,OUT/'CLASSIFICATION_GENERALIZATION_SUMMARY.csv')
    fdf=pd.concat([x for x in folds if not x.empty],ignore_index=True) if any(not x.empty for x in folds) else pd.DataFrame()
    if not fdf.empty: save(fdf,OUT/'ALL_FOLD_LEVEL_RESULTS.csv')
    # Candidate table, only within a dataset + scheme.
    candidates=[]
    if not regdf.empty:
        for (ds,sc),s in regdf[regdf.scheme.ne('SKIPPED')].groupby(['dataset','scheme']):
            s=s.sort_values(['mean_RMSE','mean_MAE'],ascending=[True,True]); candidates.append({'dataset':ds,'scheme':sc,'selected_candidate':s.iloc[0]['model'],'selection_rule':'lowest mean RMSE then MAE'})
    if not clfdf.empty:
        for (ds,sc),s in clfdf[clfdf.scheme.ne('SKIPPED')].groupby(['dataset','scheme']):
            s=s.sort_values(['mean_balanced_accuracy','mean_f1_macro'],ascending=[False,False]); candidates.append({'dataset':ds,'scheme':sc,'selected_candidate':s.iloc[0]['model'],'selection_rule':'highest mean balanced accuracy then macro F1'})
    save(pd.DataFrame(candidates),OUT/'GENERALIZATION_MODEL_CANDIDATES.csv')
    # Availability checks for time/place holdout.
    checks=[]
    for name,p in [('YIELD',DATA/'YIELD_PRODUCTION_STRICT.csv'),('TLB',DATA/'TLB_PRODUCTION_STRICT.csv'),('SDM',DATA/'SDM_PRODUCTION_STRICT.csv')]:
        if not p.exists(): continue
        d=pd.read_csv(p)
        for col,label in [('location','Location holdout'),('season','Season holdout')]:
            n=d[col].astype(str).nunique() if col in d.columns else 0
            checks.append({'dataset':name,'validation_type':label,'available_groups':n,'status':'AVAILABLE' if n>=2 else 'NOT_AVAILABLE_YET'})
        checks.append({'dataset':name,'validation_type':'Experiment holdout','available_groups':d.experiment_id.nunique(),'status':'AVAILABLE' if d.experiment_id.nunique()>=3 else 'LIMITED'})
        checks.append({'dataset':name,'validation_type':'Genotype grouped CV','available_groups':d.genotype_id.nunique(),'status':'AVAILABLE' if d.genotype_id.nunique()>=3 else 'NOT_AVAILABLE'})
    save(pd.DataFrame(checks),OUT/'GENERALIZATION_AVAILABILITY.csv')
    (OUT/'INTERPRETATION.txt').write_text('Generalization evidence is dataset-dependent. Grouped genotype CV protects against genotype leakage. Leave-one-experiment-out tests experiment transfer. Location/season holdouts are reported as unavailable when the dataset contains only one location or season. These results do not establish field performance without independent future data.\n',encoding='utf-8')
    log('PHASE 12 DONE: Generalization validation reports created')
if __name__=='__main__': main()
