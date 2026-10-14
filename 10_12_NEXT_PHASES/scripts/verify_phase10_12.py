from __future__ import annotations
from common_next import *

OUT=base()/"outputs"/"PHASE_12_GENERALIZATION_VALIDATION"
REQS={
    "phase10_decisions": base()/"outputs/PHASE_10_GENOTYPE_REVIEW/GENOTYPE_IDENTITY_DECISIONS.csv",
    "phase10_global_master": base()/"outputs/PHASE_10_GENOTYPE_REVIEW/GENOTYPE_IDENTITY_MASTER.csv",
    "phase10_domain_master": base()/"outputs/PHASE_10_GENOTYPE_REVIEW/GENOTYPE_IDENTITY_DOMAIN_MASTER.csv",
    "yield_strict": base()/"outputs/PHASE_11_PRODUCTION_DATASETS/YIELD_PRODUCTION_STRICT.csv",
    "tlb_strict": base()/"outputs/PHASE_11_PRODUCTION_DATASETS/TLB_PRODUCTION_STRICT.csv",
    "sdm_strict": base()/"outputs/PHASE_11_PRODUCTION_DATASETS/SDM_PRODUCTION_STRICT.csv",
    "manifest": base()/"outputs/PHASE_11_PRODUCTION_DATASETS/PHASE11_DATASET_MANIFEST.csv",
    "reg_summary": OUT/"REGRESSION_GENERALIZATION_SUMMARY.csv",
    "clf_summary": OUT/"CLASSIFICATION_GENERALIZATION_SUMMARY.csv",
    "availability": OUT/"GENERALIZATION_AVAILABILITY.csv",
    "folds": OUT/"ALL_FOLD_LEVEL_RESULTS.csv",
}

def check_file(name,path,problems):
    ok=path.exists() and path.stat().st_size>0
    if not ok: problems.append(f"MISSING_OR_EMPTY:{name}:{path}")
    return ok

def main():
    log('==============================================================')
    log('VERIFY PHASES 10-12 PACKAGE')
    log('==============================================================')
    problems=[]; rows=[]
    for name,path in REQS.items():
        ok=check_file(name,path,problems)
        rows.append({'check':name,'status':'PASS' if ok else 'FAIL','path':str(path)})
    for name in ['yield_strict','tlb_strict','sdm_strict']:
        path=REQS[name]
        if path.exists() and path.stat().st_size:
            try:
                df=pd.read_csv(path)
                rows.append({'check':f'{name}_rows','status':'PASS' if len(df)>0 else 'WARN','path':f'rows={len(df)}'})
                for col in ['genotype_id','experiment_id']:
                    if col not in df.columns: problems.append(f'MISSING_COLUMN:{name}:{col}')
            except Exception as e:
                problems.append(f'READ_ERROR:{name}:{e}')
    # Validate Phase 10 decision values.
    dec=REQS['phase10_decisions']
    if dec.exists():
        d=pd.read_csv(dec,dtype=str).fillna('')
        allowed={'CONFIRMED','PENDING_REVIEW','EXCLUDED'}
        bad=sorted(set(d.final_status.astype(str))-allowed) if 'final_status' in d.columns else ['missing final_status']
        if bad: problems.append('BAD_PHASE10_STATUS:'+ '|'.join(bad))
        rows.append({'check':'phase10_status_values','status':'PASS' if not bad else 'FAIL','path':','.join(bad) or 'CONFIRMED/PENDING_REVIEW/EXCLUDED'})
    # Validate no obvious non-genotype summary rows in strict yield data.
    y=REQS['yield_strict']
    if y.exists():
        d=pd.read_csv(y,dtype=str).fillna('')
        bad=d[d.canonical_genotype_candidate.astype(str).str.contains(r'general mean|location mean|cd @|cv',case=False,regex=True,na=False)]
        if len(bad): problems.append(f'YIELD_SUMMARY_ROWS_IN_STRICT:{len(bad)}')
        rows.append({'check':'yield_summary_rows_absent','status':'PASS' if len(bad)==0 else 'FAIL','path':f'found={len(bad)}'})
    save(pd.DataFrame(rows),OUT/'PHASE10_12_VERIFICATION.csv')
    status='READY' if not problems else 'ISSUES_FOUND'
    (OUT/'PHASE10_12_FINAL_STATUS.txt').write_text(status+'\n' + '\n'.join(problems),encoding='utf-8')
    if problems:
        for p in problems: log('VERIFY ISSUE: '+p)
        raise SystemExit(2)
    log('PHASES 10-12 VERIFICATION: READY')

if __name__=='__main__': main()
