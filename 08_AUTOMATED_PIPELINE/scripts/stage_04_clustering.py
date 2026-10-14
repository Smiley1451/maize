import numpy as np, pandas as pd
from common import *


def main():
    log('STEP 4/9: RUNNING PCA AND GENOTYPE CLUSTERING')
    out=output_dir(4,'CLUSTERING')
    d=read_csv('06_ML_DATASETS/ML_MULTI_TRAIT_EXPLORATORY.csv')
    features=['days_to_50_percent_pollen_shedding','days_to_50_percent_silking','days_to_75_percent_dry_husk','plant_height','ear_height','plant_stand','shelling_percentage','grain_yield_median','tlb_score_median','sdm_pdi_median']
    x=d[features].apply(pd.to_numeric,errors='coerce')
    keep=x.notna().sum(axis=1)>=5
    x=x.loc[keep].copy(); d2=d.loc[keep].copy()
    from sklearn.impute import SimpleImputer
    from sklearn.preprocessing import StandardScaler
    from sklearn.decomposition import PCA
    from sklearn.cluster import KMeans, AgglomerativeClustering
    from sklearn.metrics import silhouette_score
    xi=SimpleImputer(strategy='median').fit_transform(x)
    xs=StandardScaler().fit_transform(xi)
    pca=PCA(n_components=min(5,xs.shape[1]),random_state=SEED); z=pca.fit_transform(xs)
    pc=pd.DataFrame(z,columns=[f'PC{i+1}' for i in range(z.shape[1])])
    pc.insert(0,'genotype_id_candidate',d2.genotype_id_candidate.values); pc.insert(1,'canonical_genotype_candidate',d2.canonical_genotype_candidate.values)
    save_csv(pc,out/'PCA_SCORES.csv')
    save_csv(pd.DataFrame({'component':[f'PC{i+1}' for i in range(len(pca.explained_variance_ratio_))],'explained_variance_ratio':pca.explained_variance_ratio_}),out/'PCA_VARIANCE.csv')
    rows=[]
    for k in range(2,min(8,len(xs)-1)+1):
        km=KMeans(n_clusters=k,random_state=SEED,n_init=20)
        lab=km.fit_predict(z[:,:min(5,z.shape[1])])
        sil=silhouette_score(z[:,:min(5,z.shape[1])],lab)
        rows.append({'k':k,'silhouette':sil})
    scores=pd.DataFrame(rows); save_csv(scores,out/'KMEANS_SILHOUETTE.csv')
    best_k=int(scores.sort_values('silhouette',ascending=False).iloc[0]['k'])
    km=KMeans(n_clusters=best_k,random_state=SEED,n_init=30).fit(z[:,:min(5,z.shape[1])])
    d2['cluster_kmeans']=km.labels_
    agg=AgglomerativeClustering(n_clusters=best_k).fit(xs)
    d2['cluster_agglomerative']=agg.labels_
    save_csv(d2,out/'GENOTYPE_CLUSTERS.csv')
    profiles=d2.groupby('cluster_kmeans')[features].median(numeric_only=True).reset_index()
    save_csv(profiles,out/'CLUSTER_PROFILES_MEDIAN.csv')
    import matplotlib.pyplot as plt
    plt.figure(figsize=(8,6)); plt.scatter(z[:,0],z[:,1]); plt.xlabel('PC1'); plt.ylabel('PC2'); plt.title('Maize Genotype PCA'); plt.tight_layout(); plt.savefig(out/'PCA_PC1_PC2.png',dpi=180); plt.close()
    log(f'Clustering done; selected K={best_k} using silhouette score')

if __name__=='__main__': main()
