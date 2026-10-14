from pathlib import Path
import pandas as pd
from common import *


def main():
    log('STEP 1/9: RUNNING MODEL READINESS AUDIT')
    out=output_dir(1,'READINESS')
    required=[
        '02_MASTER_DATA/MASTER_MAIZE_ALL_DATA.csv',
        '06_ML_DATASETS/ML_YIELD_READY.csv',
        '06_ML_DATASETS/ML_TLB_READY.csv',
        '06_ML_DATASETS/ML_SDM_READY.csv',
        '06_ML_DATASETS/ML_MULTI_TRAIT_EXPLORATORY.csv',
        '02_MASTER_DATA/07_weather_monthly_2023.csv',
    ]
    rows=[]
    root=project_root()
    for rel in required:
        p=root/rel
        rows.append({'path':rel,'exists':p.exists(),'size_bytes':p.stat().st_size if p.exists() else 0})
        log(('FOUND ' if p.exists() else 'MISSING ') + rel)
    save_csv(pd.DataFrame(rows),out/'REQUIRED_INPUTS_AUDIT.csv')

    master=pd.read_csv(root/'02_MASTER_DATA/MASTER_MAIZE_ALL_DATA.csv')
    target_vars=['yield_t_per_ha','yield_kg_per_ha','grain_yield_kg_per_ha']
    y=master[master['variable'].isin(target_vars)].copy()
    y['exclude_summary']=y['entity_name'].astype(str).str.contains(r'mean|CV|C\.V|CD|C\.D',case=False,regex=True,na=False)
    unit_audit=y.groupby(['variable','unit'],dropna=False).size().reset_index(name='rows')
    save_csv(unit_audit,out/'YIELD_UNIT_AUDIT.csv')
    findings=[
        {'finding':'Raw master rows','value':len(master),'status':'INFO'},
        {'finding':'Yield target rows before summary filtering','value':len(y),'status':'INFO'},
        {'finding':'Yield target rows excluded as statistical summary','value':int(y.exclude_summary.sum()),'status':'INFO'},
        {'finding':'Weather months available','value':master[(master.domain=='weather')].entity_name.nunique(),'status':'INFO'},
        {'finding':'Disease datasets require phenotype linkage review','value':'YES','status':'CAUTION'},
        {'finding':'Weather experiment-day disease target linkage','value':'NOT ESTABLISHED','status':'BLOCKER_FOR_WEATHER_MODEL'},
    ]
    save_csv(pd.DataFrame(findings),out/'MODEL_READINESS_FINDINGS.csv')
    (out/'README.txt').write_text(
        'STEP 1 READINESS\n\nThis stage checks required files, audits yield units, and records blockers.\n'
        'No source values are silently corrected here. The yield model stage explicitly applies source-unit conversion to a new modeling target.\n',encoding='utf-8')
    log('MODEL READINESS AUDIT DONE')

if __name__=='__main__': main()
