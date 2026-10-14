import json, os, sys
from pathlib import Path
import pandas as pd
from common import *

def main():
    log('STEP 9/9: VERIFYING COMPLETE PIPELINE')
    out=output_dir(9,'FINAL_VERIFICATION')
    root=project_root(); checks=[]
    # Core source/data checks
    for rel in ['00_SOURCE_DOCUMENTS','01_DIGITIZATION','02_MASTER_DATA','03_VALIDATION','04_NORMALIZATION','05_ANALYSIS_MASTER','06_ML_DATASETS','07_MODELING','08_AUTOMATED_PIPELINE']:
        p=root/rel; checks.append({'check':f'folder:{rel}','status':'PASS' if p.exists() else 'FAIL','detail':str(p)})
    # CSV readability sample
    csvs=list(root.glob('**/*.csv'))
    bad=[]
    for p in csvs:
        try:
            pd.read_csv(p,nrows=3)
        except Exception as e: bad.append((str(p),str(e)))
    checks.append({'check':'csv_readability','status':'PASS' if not bad else 'FAIL','detail':f'{len(csvs)} csv files checked; bad={len(bad)}'})
    # Launcher/config checks (PowerShell parser may not be available on this Linux build host).
    for rel in ['run_pipeline.ps1','START_PIPELINE.bat','requirements.txt','config/pipeline_config.json','config/WEATHER_DISEASE_LINKED_TEMPLATE.csv']:
        pth=pipeline_root()/rel; checks.append({'check':f'pipeline_file:{rel}','status':'PASS' if pth.exists() else 'FAIL','detail':str(pth)})
    model_files=list((pipeline_root()/'models').glob('*.joblib'))
    checks.append({'check':'packaged_model_count','status':'PASS' if model_files else 'WARN','detail':f'{len(model_files)} packaged joblib model files'})
    # Python syntax check all scripts
    import py_compile
    scripts=list((root/'08_AUTOMATED_PIPELINE/scripts').glob('*.py'))
    syntax_bad=[]
    for p in scripts:
        try: py_compile.compile(str(p),doraise=True)
        except Exception as e: syntax_bad.append((p.name,str(e)))
    checks.append({'check':'python_syntax','status':'PASS' if not syntax_bad else 'FAIL','detail':f'{len(scripts)} scripts checked; bad={len(syntax_bad)}'})
    # Pipeline outputs
    expected=[
      '02_YIELD_BASELINE/YIELD_MODEL_COMPARISON.csv',
      '03_DISEASE_MODELS/TLB_LINK_AUDIT.csv',
      '03_DISEASE_MODELS/SDM_LINK_AUDIT.csv',
      '04_CLUSTERING/GENOTYPE_CLUSTERS.csv',
      '05_WEATHER_RISK/WEATHER_MODEL_BLOCKER.csv',
      '06_TUNING/TUNING_RESULTS.csv',
      '07_EXPLAINABILITY/YIELD_PERMUTATION_IMPORTANCE.csv',
      '08_MODEL_PACKAGE/MODEL_PACKAGE_MANIFEST.csv'
    ]
    for rel in expected:
        p=pipeline_root()/'outputs'/rel; checks.append({'check':f'output:{rel}','status':'PASS' if p.exists() else 'WARN','detail':str(p)})
    df=pd.DataFrame(checks); save_csv(df,out/'PROJECT_VERIFICATION.csv')
    fails=(df.status=='FAIL').sum(); warns=(df.status=='WARN').sum()
    summary={'passes':int((df.status=='PASS').sum()),'warnings':int(warns),'fails':int(fails),'project_status':'READY' if fails==0 else 'REPAIR_REQUIRED','checked_at':now()}
    json_dump(summary,out/'FINAL_STATUS.json')
    (out/'FINAL_VERIFICATION.txt').write_text(f"Passes: {summary['passes']}\nWarnings: {warns}\nFails: {fails}\nStatus: {summary['project_status']}\n\nWarnings are allowed for data-dependent stages such as weather risk when verified labels are absent.\n",encoding='utf-8')
    log(f'FINAL VERIFICATION COMPLETE: {summary["project_status"]}')
    if fails: sys.exit(2)

if __name__=='__main__': main()
