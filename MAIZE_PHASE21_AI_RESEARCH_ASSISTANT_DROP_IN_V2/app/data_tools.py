from __future__ import annotations
from pathlib import Path
import re, json
from functools import lru_cache
import pandas as pd
from .config import PROJECT_ROOT, ASSISTANT_ROOT, CFG

SKIP_DIRS={".git",".venv","venv","__pycache__",".pytest_cache","node_modules"}

@lru_cache(maxsize=128)
def read_csv(path_str:str):
    return pd.read_csv(path_str, low_memory=False)


def csv_paths():
    out=[]
    for p in PROJECT_ROOT.rglob("*.csv"):
        parts=set(p.relative_to(PROJECT_ROOT).parts[:-1])
        if parts & SKIP_DIRS: continue
        try:
            if p.stat().st_size <= CFG["max_file_mb"]*1024*1024: out.append(p)
        except OSError: pass
    return sorted(out)

GENO_COLS=["canonical_genotype","canonical_genotype_candidate","genotype","entity_name","raw_genotype_names"]
EXP_COLS=["experiment_id","experiment_no","trial_no","source_section","title","experiment","trial"]


def _norm(x): return re.sub(r"[^a-z0-9]+","",str(x).casefold())


def search_records(query:str, top_k:int=12):
    q=str(query).casefold().strip(); hits=[]
    for p in csv_paths():
        try: df=read_csv(str(p))
        except Exception: continue
        mask=pd.Series(False,index=df.index)
        for c in df.columns:
            mask |= df[c].astype(str).str.casefold().str.contains(q, regex=False, na=False)
        sub=df.loc[mask].head(top_k)
        for idx,row in sub.iterrows():
            hits.append({"path":str(p.relative_to(PROJECT_ROOT)),"row":int(idx)+2,"record":{k:(None if pd.isna(v) else v) for k,v in row.items()}})
            if len(hits)>=top_k: return hits
    return hits


def find_genotype(name:str, exact=False, top_k=50):
    nq=_norm(name); hits=[]
    for p in csv_paths():
        try: df=read_csv(str(p))
        except Exception: continue
        cols=[c for c in GENO_COLS if c in df.columns]
        if not cols: continue
        mask=pd.Series(False,index=df.index)
        for c in cols:
            vals=df[c].astype(str).map(_norm)
            mask |= vals.eq(nq) if exact else vals.str.contains(re.escape(nq), regex=True, na=False)
        sub=df.loc[mask].head(top_k)
        for idx,row in sub.iterrows():
            hits.append({"path":str(p.relative_to(PROJECT_ROOT)),"row":int(idx)+2,"record":{k:(None if pd.isna(v) else v) for k,v in row.items()}})
            if len(hits)>=top_k: return hits
    return hits


def genotype_profile(name:str):
    hits=find_genotype(name, exact=True, top_k=200)
    if not hits:
        hits=find_genotype(name, exact=False, top_k=200)
    domains={}
    for h in hits:
        path=h["path"]
        domain="other"
        low=path.lower()
        for d in ("yield","tlb","sdm","multi_trait"):
            if d in low: domain=d; break
        if domain not in domains: domains[domain]=[]
        domains[domain].append(h)
    return {"query":name,"match_count":len(hits),"domains":domains}


def experiment_search(query:str, top_k=50):
    hits=[]; q=str(query).casefold()
    for p in csv_paths():
        try: df=read_csv(str(p))
        except Exception: continue
        cols=[c for c in EXP_COLS if c in df.columns]
        if not cols: continue
        mask=pd.Series(False,index=df.index)
        for c in cols: mask |= df[c].astype(str).str.casefold().str.contains(q,regex=False,na=False)
        sub=df.loc[mask].head(top_k)
        for idx,row in sub.iterrows():
            hits.append({"path":str(p.relative_to(PROJECT_ROOT)),"row":int(idx)+2,"record":{k:(None if pd.isna(v) else v) for k,v in row.items()}})
    return hits[:top_k]


def domain_summary(domain:str|None=None):
    rows=[]
    for p in csv_paths():
        low=str(p).casefold()
        if domain and domain.casefold() not in low: continue
        try: df=read_csv(str(p))
        except Exception: continue
        rows.append({"path":str(p.relative_to(PROJECT_ROOT)),"rows":len(df),"columns":list(df.columns)})
    return rows[:100]


def project_file_search(query:str, top_k=20):
    import json
    reg=ASSISTANT_ROOT/"index"/"project_registry.json"
    if reg.exists():
        data=json.loads(reg.read_text(encoding="utf-8"))
        candidates=data.get("files",[])
    else:
        candidates=[]
        for p in PROJECT_ROOT.rglob("*"):
            if not p.is_file(): continue
            rel=p.relative_to(PROJECT_ROOT).as_posix()
            if any(part in {".git",".venv","venv","__pycache__",".pytest_cache","node_modules"} for part in p.relative_to(PROJECT_ROOT).parts[:-1]): continue
            candidates.append({"path":rel,"source_type":"other","stage":rel.split("/",1)[0] if "/" in rel else "ROOT"})
    q=str(query).casefold()
    out=[]
    for f in candidates:
        score=0
        s=(f["path"]+" "+f["source_type"]+" "+f["stage"]).casefold()
        if q in s: score+=5
        for token in re.findall(r"[a-z0-9_-]+", q):
            if token in s: score+=1
        if score: out.append({**f,"match_score":score})
    return sorted(out,key=lambda x:(-x["match_score"],x["path"]))[:top_k]
