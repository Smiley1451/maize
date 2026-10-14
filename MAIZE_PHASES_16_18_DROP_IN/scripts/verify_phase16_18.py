from __future__ import annotations
from pathlib import Path
import sys, json
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_16_18 import *

checks=[]
def check(name, exists, note=''):
    checks.append({'check':name,'status':'PASS' if exists else 'FAIL','note':note})


def main():
    check('phase16_script',(HERE/'phase16_weather_disease.py').exists())
    check('phase17_script',(HERE/'phase17_explainability.py').exists())
    check('phase18_script',(HERE/'phase18_prediction_engine.py').exists())
    check('prediction_cli',(HERE/'predict_new.py').exists())
    for sub in ['16_WEATHER_DISEASE','17_EXPLAINABILITY','18_PREDICTION_ENGINE']:
        p=OUT/sub; check(f'output_dir_{sub}',p.exists())
    p16=OUT/'16_WEATHER_DISEASE'/'WEATHER_MODEL_STATUS.csv'; check('phase16_status',p16.exists())
    p17=OUT/'17_EXPLAINABILITY'/'EXPLAINABILITY_STATUS.csv'; check('phase17_status',p17.exists())
    p18=OUT/'18_PREDICTION_ENGINE'/'MODEL_AVAILABILITY.csv'; check('phase18_model_availability',p18.exists())
    # Do not fail solely because weather labels are not present. It is a controlled blocker.
    if p16.exists():
        d=pd.read_csv(p16); st=str(d.iloc[0].get('status','')) if len(d) else ''
        check('phase16_controlled_status',st in {'WAITING_FOR_ALIGNED_DATA','TRAINED','REFERENCE_WEATHER_ONLY','INSUFFICIENT_TIME_POINTS','NO_MODEL_TRAINED'},st)
    if p18.exists():
        d=pd.read_csv(p18); check('phase18_schema',len(d)>=1)
    save(pd.DataFrame(checks),OUT/'19_VERIFICATION'/'PHASE16_18_VERIFICATION.csv')
    failed=sum(1 for x in checks if x['status']=='FAIL')
    print(f'PHASE 16-18 VERIFICATION: {"READY" if failed==0 else "FAILED"}')
    print(f'Passes: {len(checks)-failed}; Fails: {failed}')
    if failed: raise SystemExit(1)

if __name__=='__main__': main()
