from common_next import *

OUT=out('PHASE_11_PRODUCTION_DATASETS')
IDP=out('PHASE_10_GENOTYPE_REVIEW')/'GENOTYPE_IDENTITY_DOMAIN_MASTER.csv'
AM=root()/'05_ANALYSIS_MASTER/MAIZE_ANALYSIS_MASTER_LONG.csv'
TLB=root()/'08_AUTOMATED_PIPELINE/outputs/03_DISEASE_MODELS/TLB_REGRESSION_READY.csv'
SDM=root()/'08_AUTOMATED_PIPELINE/outputs/03_DISEASE_MODELS/SDM_REGRESSION_READY.csv'
FEATURES=['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage']

def eligible_map():
    d=pd.read_csv(IDP,dtype=str).fillna('')
    return {(str(r.genotype_id),str(r.domain)):str(r.production_eligible) for _,r in d.iterrows()}

def build_yield(am,emap):
    d=am[am.domain.astype(str).str.lower().eq('yield')].copy()
    d=d[d['canonical_genotype_candidate'].astype(str).str.strip().ne('')].copy()
    d=d[~d['canonical_genotype_candidate'].astype(str).str.contains(r'general mean|location mean|cd @|cv \(%\)|^cv$|^cd$',case=False,regex=True,na=False)].copy()
    d['production_eligible']=d.apply(lambda r: emap.get((str(r.genotype_id_candidate),'yield'))=='YES',axis=1)
    key=['experiment_id','experiment_no','trial_no','genotype_id_candidate','canonical_genotype_candidate','entity_name','entity_type','category','year','season','location','source_page']
    for c in key:
        if c not in d.columns: d[c]=np.nan
    d['record_group']=d['experiment_id'].astype(str)+'::'+d['genotype_id_candidate'].astype(str)
    key=['record_group']+key
    piv=d.pivot_table(index=key,columns='canonical_trait',values='standard_value_numeric',aggfunc='first').reset_index()
    piv.columns=[str(c) for c in piv.columns]
    gy=d[d.canonical_trait.eq('grain_yield')][['record_group','unit','value']].drop_duplicates('record_group')
    piv=piv.merge(gy,on='record_group',how='left',suffixes=('','_yield'))
    kg=[]; method=[]
    for _,r in piv.iterrows():
        v,m=yield_to_kg_ha(r.get('grain_yield'),r.get('unit')); kg.append(v); method.append(m)
    piv['yield_kg_ha']=kg; piv['yield_conversion_method']=method
    for f in FEATURES:
        if f not in piv.columns: piv[f]=np.nan
    piv['genotype_id']=piv.genotype_id_candidate.astype(str)
    piv['production_eligible']=piv.apply(lambda r: emap.get((str(r.genotype_id),'yield'))=='YES',axis=1)
    piv['feature_nonmissing_count']=piv[FEATURES].notna().sum(axis=1)
    piv['target_available']=piv.yield_kg_ha.notna()
    return piv

def disease(path,prefix,target,cls,emap):
    d=pd.read_csv(path)
    # Disease-ready files use normalized genotype names as the linkage key, while the
    # analysis master uses internal genotype IDs. Join by normalized canonical name.
    idm=pd.read_csv(IDP,dtype=str).fillna('')
    name_status={}
    for _,r in idm.iterrows():
        if str(r.domain)!=prefix: continue
        key=norm_name(r.final_canonical_name)
        if key: name_status[key]=str(r.production_eligible)
    d['genotype_id']=d.genotype_id_candidate.astype(str)
    d['normalized_genotype_name']=d.canonical_genotype_candidate.map(norm_name)
    d['production_eligible']=d.normalized_genotype_name.map(name_status).fillna('NO').eq('YES')
    d['usable_link']=d.link_confidence.astype(str).str.contains('FULL_FEATURE_LINK',case=False,na=False)
    d['target_value_numeric']=pd.to_numeric(d[target],errors='coerce')
    d['class_label']=d[cls].astype(str).str.strip()
    return d

def main():
    log('=============================================================='); log('PHASE 11: BUILD PRODUCTION DATASETS'); log('==============================================================')
    emap=eligible_map(); am=pd.read_csv(AM)
    y=build_yield(am,emap)
    strict_y=y[y.production_eligible & y.target_available].copy(); exp_y=y.copy()
    save(strict_y,OUT/'YIELD_PRODUCTION_STRICT.csv'); save(exp_y,OUT/'YIELD_EXPLORATORY_ALL_IDENTITIES.csv')
    log(f'YIELD PRODUCTION: {len(strict_y)} rows, {strict_y.genotype_id.nunique()} genotypes, {strict_y.experiment_id.nunique()} experiments')
    manifests=[{'dataset':'YIELD','strict_rows':len(strict_y),'genotypes':strict_y.genotype_id.nunique(),'experiments':strict_y.experiment_id.nunique()}]
    for prefix,path,target,cls in [('TLB',TLB,'tlb_disease_score','tlb_reaction'),('SDM',SDM,'sdm_pdi','sdm_reaction')]:
        d=disease(path,prefix,target,cls,emap)
        strict=d[d.production_eligible & d.usable_link & d.target_value_numeric.notna()].copy()
        if prefix=='SDM': strict=strict[strict.class_label.ne('NG')]
        save(strict,OUT/f'{prefix}_PRODUCTION_STRICT.csv'); save(d,OUT/f'{prefix}_EXPLORATORY_ALL_IDENTITIES.csv')
        manifests.append({'dataset':prefix,'strict_rows':len(strict),'genotypes':strict.genotype_id.nunique(),'experiments':strict.experiment_id.nunique()})
        log(f'{prefix} PRODUCTION: {len(strict)} rows, {strict.genotype_id.nunique()} genotypes, {strict.experiment_id.nunique()} experiments')
    # Multi-trait genotype summary
    mt=strict_y.groupby('genotype_id').agg(yield_median_kg_ha=('yield_kg_ha','median'),yield_n=('yield_kg_ha','size')).reset_index()
    tlb=pd.read_csv(OUT/'TLB_PRODUCTION_STRICT.csv'); sdm=pd.read_csv(OUT/'SDM_PRODUCTION_STRICT.csv')
    if not tlb.empty: mt=mt.merge(tlb.groupby('genotype_id').tlb_disease_score.median().rename('tlb_score_median'),on='genotype_id',how='outer')
    if not sdm.empty: mt=mt.merge(sdm.groupby('genotype_id').sdm_pdi.median().rename('sdm_pdi_median'),on='genotype_id',how='outer')
    save(mt,OUT/'MULTI_TRAIT_PRODUCTION_SUMMARY.csv'); save(pd.DataFrame(manifests),OUT/'PHASE11_DATASET_MANIFEST.csv')
    (OUT/'DATASET_RULES.txt').write_text(
      'Production eligibility uses Phase 10 domain-level identity.\n'
      'A genotype is eligible when globally CONFIRMED or DOMAIN_SAFE inside that modeling domain, unless explicitly EXCLUDED.\n'
      'Exploratory files retain pending identities.\n'
      'Yield is converted to kg/ha only when the recorded unit is t/ha or kg/ha. Unknown units are left unavailable.\n'
      'TLB/SDM rows require full feature linkage and a numeric target; SDM NG rows are excluded from classification-ready production data.\n',encoding='utf-8')
    log('PHASE 11 DONE: Production datasets built')
if __name__=='__main__': main()
