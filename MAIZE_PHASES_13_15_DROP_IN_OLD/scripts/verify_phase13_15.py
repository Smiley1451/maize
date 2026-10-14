from pathlib import Path
import json
import pandas as pd

ROOT=Path(__file__).resolve().parents[2]
BASE=ROOT/'13_15_NEXT_PHASES'; OUT=BASE/'outputs'; MODELS=BASE/'models'
checks=[]
def check(name, ok, detail): checks.append({'check':name,'status':'PASS' if ok else 'FAIL','detail':detail})

p13=OUT/'PHASE_13_ADVANCED_YIELD'
p14=OUT/'PHASE_14_ADVANCED_DISEASE'
p15=OUT/'PHASE_15_BREEDING_INTELLIGENCE'
for p in [p13,p14,p15]:
    check(f'output folder {p.name}',p.exists(),str(p))
for f in ['YIELD_ADVANCED_READY.csv','YIELD_UNIT_REAUDIT.csv','ADVANCED_YIELD_MODEL_COMPARISON.csv','SELECTED_YIELD_MODEL.csv']:
    q=p13/f; check(f'Phase13 {f}',q.exists(),str(q))
for f in ['TLB_ADVANCED_READY.csv','SDM_ADVANCED_READY.csv','TLB_REGRESSION_COMPARISON.csv','SDM_REGRESSION_COMPARISON.csv','TLB_CLASSIFICATION_COMPARISON.csv','SDM_CLASSIFICATION_COMPARISON.csv']:
    q=p14/f; check(f'Phase14 {f}',q.exists(),str(q))
for f in ['MULTI_TRAIT_GENOTYPE_PROFILE.csv','GENOTYPE_SCREENING_PROFILES.csv','PARETO_FRONT_GENOTYPES.csv','GENOTYPE_CLUSTERS.csv','PCA_VARIANCE.csv','KMEANS_SILHOUETTE.csv','CLUSTER_PROFILES.csv']:
    q=p15/f; check(f'Phase15 {f}',q.exists(),str(q))

# Data sanity
try:
    y=pd.read_csv(p13/'YIELD_ADVANCED_READY.csv'); check('Phase13 yield rows',len(y)>0,str(len(y)))
    check('Phase13 yield values plausible',float(y.yield_kg_ha_corrected.median())>1000, f"median={y.yield_kg_ha_corrected.median():.2f}")
    c=pd.read_csv(p13/'ADVANCED_YIELD_MODEL_COMPARISON.csv'); check('Phase13 comparison nonempty',len(c)>0,str(len(c)))
except Exception as e: check('Phase13 data readability',False,str(e))
try:
    for disease in ['TLB','SDM']:
        d=pd.read_csv(p14/f'{disease}_ADVANCED_READY.csv'); check(f'{disease} rows',len(d)>0,str(len(d)))
        cm=pd.read_csv(p14/f'{disease}_CLASSIFICATION_COMPARISON.csv'); check(f'{disease} classifier comparison readable',len(cm)>0,str(len(cm)))
except Exception as e: check('Phase14 data readability',False,str(e))
try:
    m=pd.read_csv(p15/'GENOTYPE_SCREENING_PROFILES.csv'); cl=pd.read_csv(p15/'GENOTYPE_CLUSTERS.csv'); check('Phase15 profile rows',len(m)>0,str(len(m))); check('Phase15 cluster rows',len(cl)==len(m),f'profiles={len(m)}, clusters={len(cl)}')
except Exception as e: check('Phase15 data readability',False,str(e))

res=pd.DataFrame(checks); res.to_csv(OUT/'PHASE13_15_VERIFICATION.csv',index=False)
final='READY' if (res.status=='PASS').all() else 'REVIEW'
(OUT/'PHASE13_15_FINAL_STATUS.txt').write_text(f'Status: {final}\nPasses: {(res.status=="PASS").sum()}\nFails: {(res.status=="FAIL").sum()}\n',encoding='utf-8')
print(f'PHASE 13-15 VERIFICATION: {final}')
if final!='READY': raise SystemExit(1)
