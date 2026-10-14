from common_next import *

OUT=out('PHASE_10_GENOTYPE_REVIEW')
MASTER=root()/'04_NORMALIZATION/GENOTYPE_MASTER.csv'
ALIASES=root()/'04_NORMALIZATION/GENOTYPE_ALIASES.csv'
DEC=OUT/'GENOTYPE_IDENTITY_DECISIONS.csv'
AM=root()/'05_ANALYSIS_MASTER/MAIZE_ANALYSIS_MASTER_LONG.csv'

def domain_audit(am):
    d=am[am['canonical_genotype_candidate'].astype(str).str.strip().ne('')].copy()
    d=d[~d['canonical_genotype_candidate'].astype(str).str.contains(r'general mean|location mean|cd @|cv \(%\)|^cv$|^cd$',case=False,regex=True,na=False)].copy()
    rows=[]
    for (gid,dom),g in d.groupby(['genotype_id_candidate','domain']):
        raw_names=sorted({str(x).strip() for x in g['entity_name'].dropna() if str(x).strip()})
        normalized={norm_name(x) for x in raw_names}
        cats=sorted({str(x).strip() for x in g['category'].dropna() if str(x).strip()})
        safe=(len(normalized)==1 and len(raw_names)>=1)
        rows.append({
          'genotype_id':str(gid),'domain':str(dom),'raw_name_count':len(raw_names),
          'raw_names':' | '.join(raw_names),'normalized_name_count':len(normalized),
          'categories':' | '.join(cats),'domain_identity_status':'DOMAIN_SAFE' if safe else 'DOMAIN_REVIEW_REQUIRED',
          'reason':'One normalized source name inside this domain' if safe else 'Multiple normalized names inside the same domain'
        })
    return pd.DataFrame(rows)

def main():
    log('==============================================================')
    log('PHASE 10: GENOTYPE IDENTITY REVIEW')
    log('==============================================================')
    gm=pd.read_csv(MASTER,dtype=str).fillna('')
    am=pd.read_csv(AM,dtype=str).fillna('')
    audit=domain_audit(am)
    save(audit,OUT/'GENOTYPE_DOMAIN_IDENTITY_AUDIT.csv')
    source_by_gid=gm.set_index('genotype_id')
    rows=[]
    for _,r in gm.iterrows():
        recommended='CONFIRMED' if str(r.get('manual_review_required','')).upper()=='NO' else 'PENDING_REVIEW'
        rows.append({
          'genotype_id':r['genotype_id'],'normalized_key':r.get('normalized_key',''),
          'canonical_candidate_name':r.get('canonical_candidate_name',''),'raw_names':r.get('raw_names',''),
          'raw_name_count':r.get('raw_name_count',''),'source_domains':r.get('source_domains',''),
          'source_categories':r.get('source_categories',''),'experiment_count':r.get('experiment_count',''),
          'source_identity_status':r.get('identity_status',''),'source_manual_review_required':r.get('manual_review_required',''),
          'recommended_global_status':recommended,'final_status':recommended,
          'final_canonical_name':r.get('canonical_candidate_name',''),
          'decision_note':'' if recommended=='CONFIRMED' else 'Cross-domain or category variation exists; domain-safe use may still be allowed.'
        })
    q=pd.DataFrame(rows)
    if DEC.exists():
        old=pd.read_csv(DEC,dtype=str).fillna('')
        keep=[c for c in ['genotype_id','final_status','final_canonical_name','decision_note'] if c in old.columns]
        old=old[keep].drop_duplicates('genotype_id')
        q=q.drop(columns=['final_status','final_canonical_name','decision_note']).merge(old,on='genotype_id',how='left')
        q['final_status']=q['final_status'].replace('',np.nan).fillna(q['recommended_global_status'])
        q['final_canonical_name']=q['final_canonical_name'].replace('',np.nan).fillna(q['canonical_candidate_name'])
        q['decision_note']=q['decision_note'].fillna('')
    save(q,DEC)
    # Keep a simple global identity master alongside the editable decision file.
    save(q,OUT/'GENOTYPE_IDENTITY_MASTER.csv')

    # Domain-safe identity is allowed when the same genotype has one normalized name within the modeling domain.
    lookup={(str(r.genotype_id),str(r.domain)):str(r.domain_identity_status) for _,r in audit.iterrows()}
    mrows=[]
    for _,r in q.iterrows():
        for dom in ['yield','TLB','SDM','OTHER']:
            st=lookup.get((str(r.genotype_id),dom),'')
            if not st: continue
            final=str(r.final_status)
            if final=='EXCLUDED': prod='NO'
            elif final=='CONFIRMED': prod='YES'
            elif st=='DOMAIN_SAFE': prod='YES'
            else: prod='NO'
            mrows.append({'genotype_id':r.genotype_id,'domain':dom,'final_global_status':final,'domain_identity_status':st,'production_eligible':prod,'final_canonical_name':r.final_canonical_name})
    master=pd.DataFrame(mrows)
    save(master,OUT/'GENOTYPE_IDENTITY_DOMAIN_MASTER.csv')
    summary=q['final_status'].value_counts(dropna=False).rename_axis('global_status').reset_index(name='count')
    save(summary,OUT/'PHASE10_SUMMARY.csv')
    (OUT/'REVIEW_INSTRUCTIONS.txt').write_text(
      'Phase 10 review instructions\n\n'
      'GLOBAL identity: Unique source names are auto-confirmed. Alias groups remain PENDING_REVIEW.\n'
      'DOMAIN identity: A genotype can be DOMAIN_SAFE when only one normalized source name occurs inside a modeling domain, even if another domain uses a check/test/category qualifier.\n'
      'To make a pending alias globally confirmed, edit GENOTYPE_IDENTITY_DECISIONS.csv and set final_status=CONFIRMED.\n'
      'Set final_status=EXCLUDED to stop a genotype from production use.\n'
      'After edits, rerun Phase 10, then Phase 11 and Phase 12.\n',encoding='utf-8')
    log(f'GLOBAL IDENTITY: confirmed={int((q.final_status=="CONFIRMED").sum())}, pending={int((q.final_status=="PENDING_REVIEW").sum())}, excluded={int((q.final_status=="EXCLUDED").sum())}')
    for dom in ['yield','TLB','SDM']:
        n=int(((audit.domain==dom)&(audit.domain_identity_status=='DOMAIN_SAFE')).sum())
        log(f'{dom} DOMAIN-SAFE GENOTYPES: {n}')
    log('PHASE 10 DONE: Genotype identity review artifacts ready')
if __name__=='__main__': main()
