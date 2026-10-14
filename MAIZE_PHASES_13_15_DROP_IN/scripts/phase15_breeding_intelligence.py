from __future__ import annotations
import sys
from pathlib import Path
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
sys.path.insert(0, str(Path(__file__).resolve().parent))
from common_13_15 import *

from sklearn.impute import SimpleImputer
from sklearn.preprocessing import StandardScaler
from sklearn.decomposition import PCA
from sklearn.cluster import KMeans, AgglomerativeClustering
from sklearn.metrics import silhouette_score

YIN=OUT/'PHASE_13_ADVANCED_YIELD'/'YIELD_ADVANCED_READY.csv'
TIN=OUT/'PHASE_14_ADVANCED_DISEASE'/'TLB_ADVANCED_READY.csv'
SIN=OUT/'PHASE_14_ADVANCED_DISEASE'/'SDM_ADVANCED_READY.csv'
OUTP=phase_out('PHASE_15_BREEDING_INTELLIGENCE')


def aggregate():
    y=pd.read_csv(YIN); t=pd.read_csv(TIN); s=pd.read_csv(SIN)
    y['name_key']=y['canonical_genotype_candidate'].map(norm_name)
    t['name_key']=t['canonical_genotype_candidate'].map(norm_name)
    s['name_key']=s['canonical_genotype_candidate'].map(norm_name)
    ya=y.groupby('name_key').agg(genotype_name=('canonical_genotype_candidate','first'),yield_kg_ha=('yield_kg_ha_corrected','median'),yield_n=('yield_kg_ha_corrected','size'),pollen=('days_to_50_percent_pollen_shedding','median'),silking=('days_to_50_percent_silking','median'),dry_husk=('days_to_75_percent_dry_husk','median'),plant_height=('plant_height','median'),ear_height=('ear_height','median'),plant_stand=('plant_stand','median'),shelling_percentage=('shelling_percentage','median')).reset_index()
    ta=t.groupby('name_key').agg(tlb_score=('target_value_numeric','median'),tlb_n=('target_value_numeric','size'),tlb_class=('class_label',lambda x:x.mode().iat[0] if not x.mode().empty else x.iloc[0])).reset_index()
    sa=s.groupby('name_key').agg(sdm_pdi=('target_value_numeric','median'),sdm_n=('target_value_numeric','size'),sdm_class=('class_label',lambda x:x.mode().iat[0] if not x.mode().empty else x.iloc[0])).reset_index()
    m=ya.merge(ta,on='name_key',how='inner').merge(sa,on='name_key',how='inner')
    m['match_method']='EXACT_NORMALIZED_NAME'
    m['silking_to_pollen_gap']=m['silking']-m['pollen']
    m['dry_husk_after_silking']=m['dry_husk']-m['silking']
    m['ear_height_ratio']=m['ear_height']/m['plant_height'].replace(0,np.nan)
    save(m,OUTP/'MULTI_TRAIT_GENOTYPE_PROFILE.csv')
    return m


def scores(m):
    c=cfg(); w=c['breeding_index_weights']
    m=m.copy()
    m['yield_score']=pct_rank_high(m.yield_kg_ha)
    m['tlb_resistance_score']=pct_rank_low(m.tlb_score)
    m['sdm_resistance_score']=pct_rank_low(m.sdm_pdi)
    m['breeding_index']=(w['yield']*m.yield_score+w['tlb_resistance']*m.tlb_resistance_score+w['sdm_resistance']*m.sdm_resistance_score)
    cols=['name_key','genotype_name','yield_kg_ha','tlb_score','sdm_pdi','yield_score','tlb_resistance_score','sdm_resistance_score','breeding_index','tlb_class','sdm_class','match_method']
    save(m.sort_values('breeding_index',ascending=False)[cols],OUTP/'GENOTYPE_SCREENING_PROFILES.csv')
    eff=pareto_front(m,['yield_kg_ha'],['tlb_score','sdm_pdi'])
    p=m.loc[eff,cols].copy(); p['pareto_efficient']=True
    save(p.sort_values('breeding_index',ascending=False),OUTP/'PARETO_FRONT_GENOTYPES.csv')
    save(pd.DataFrame([{'yield_weight':w['yield'],'tlb_resistance_weight':w['tlb_resistance'],'sdm_resistance_weight':w['sdm_resistance'],'interpretation':'screening index only; not a biological truth'}]),OUTP/'BREEDING_INDEX_CONFIG.csv')
    return m


def pca_cluster(m):
    feature_cols=['yield_kg_ha','tlb_score','sdm_pdi','pollen','silking','dry_husk','plant_height','ear_height','plant_stand','shelling_percentage']
    X=SimpleImputer(strategy='median').fit_transform(m[feature_cols])
    Z=StandardScaler().fit_transform(X)
    pca=PCA(n_components=min(5,Z.shape[1],len(m)-1),random_state=SEED)
    pcs=pca.fit_transform(Z)
    pca_df=pd.DataFrame({'name_key':m.name_key,'genotype_name':m.genotype_name,'PC1':pcs[:,0],'PC2':pcs[:,1]})
    for i in range(2,pcs.shape[1]): pca_df[f'PC{i+1}']=pcs[:,i]
    save(pca_df,OUTP/'PCA_SCORES.csv')
    var=pd.DataFrame({'component':[f'PC{i+1}' for i in range(len(pca.explained_variance_ratio_))],'explained_variance_ratio':pca.explained_variance_ratio_,'cumulative_variance':np.cumsum(pca.explained_variance_ratio_)})
    save(var,OUTP/'PCA_VARIANCE.csv')
    load=pd.DataFrame(pca.components_,columns=feature_cols,index=[f'PC{i+1}' for i in range(pca.n_components_)])
    load.to_csv(OUTP/'PCA_LOADINGS.csv')
    kc=cfg()['cluster_k_range']; candidates=[]
    for k in range(kc[0],min(kc[1],len(m)-1)+1):
        km=KMeans(n_clusters=k,n_init=20,random_state=SEED).fit(Z)
        candidates.append((k,silhouette_score(Z,km.labels_),km))
    best_k=max(candidates,key=lambda x:x[1])[0]
    km=max(candidates,key=lambda x:x[1])[2]
    m2=m.copy(); m2['cluster']=km.labels_.astype(int); m2['cluster_method']='KMeans'; m2['cluster_k']=best_k; m2['cluster_silhouette']=max(candidates,key=lambda x:x[1])[1]
    save(m2,OUTP/'GENOTYPE_CLUSTERS.csv')
    sil=pd.DataFrame([{'k':k,'silhouette':s} for k,s,_ in candidates]); save(sil,OUTP/'KMEANS_SILHOUETTE.csv')
    prof=m2.groupby('cluster').agg(genotypes=('name_key','size'),yield_median_kg_ha=('yield_kg_ha','median'),tlb_score_median=('tlb_score','median'),sdm_pdi_median=('sdm_pdi','median'),breeding_index_median=('breeding_index','median')).reset_index(); save(prof,OUTP/'CLUSTER_PROFILES.csv')
    corr=m2[['yield_kg_ha','tlb_score','sdm_pdi','pollen','silking','dry_husk','plant_height','ear_height','plant_stand','shelling_percentage']].corr(); corr.to_csv(OUTP/'TRAIT_CORRELATIONS.csv')
    plt.figure(figsize=(8,6)); plt.scatter(pcs[:,0],pcs[:,1]); plt.xlabel('PC1'); plt.ylabel('PC2'); plt.title('Maize genotype PCA'); plt.tight_layout(); plt.savefig(OUTP/'PCA_PC1_PC2.png',dpi=160); plt.close()
    return best_k, max(candidates,key=lambda x:x[1])[1]


def main():
    log('='*62); log('PHASE 15: MULTI-TRAIT GENOTYPE BREEDING INTELLIGENCE'); log('='*62)
    for p in (YIN,TIN,SIN):
        if not p.exists(): raise FileNotFoundError(f'Missing Phase 13/14 output: {p}')
    m=aggregate();
    if len(m)<2: raise ValueError('Not enough exact cross-domain genotype matches for multi-trait analysis')
    m=scores(m)
    best_k,sil=pca_cluster(m)
    (OUTP/'PHASE15_SUMMARY.txt').write_text(f'PHASE 15 DONE\nCross-domain exact normalized-name matches: {len(m)}\nSelected KMeans k: {best_k}\nSilhouette: {sil:.6f}\nPareto-efficient genotypes: {int(pareto_front(m,["yield_kg_ha"],["tlb_score","sdm_pdi"]).sum())}\n',encoding='utf-8')
    log(f'PHASE 15 DATA: {len(m)} exact normalized cross-domain genotype matches')
    log(f'PHASE 15 DONE: breeding intelligence complete (k={best_k}, silhouette={sil:.4f})')
if __name__=='__main__': main()
