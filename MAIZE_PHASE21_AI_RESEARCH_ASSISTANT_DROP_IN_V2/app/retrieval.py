from __future__ import annotations
from pathlib import Path
import re, math
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from .indexer import ProjectIndexer
from .config import ASSISTANT_ROOT, CFG

class Retriever:
    def __init__(self):
        self.chunks=[]; self.vectorizer=None; self.matrix=None
        self.refresh()
    def refresh(self):
        self.chunks=ProjectIndexer.load_chunks()
        texts=[c["text"] for c in self.chunks]
        if not texts:
            self.vectorizer=None; self.matrix=None; return
        self.vectorizer=TfidfVectorizer(ngram_range=(1,2), min_df=1, sublinear_tf=True)
        self.matrix=self.vectorizer.fit_transform(texts)
    def search(self, query:str, top_k:int|None=None, stage:str|None=None, source_type:str|None=None):
        top_k=top_k or CFG["retrieval_top_k"]
        if not self.chunks or self.vectorizer is None: return []
        candidate_idx=list(range(len(self.chunks)))
        if stage:
            candidate_idx=[i for i in candidate_idx if self.chunks[i]["path"].split("/",1)[0].casefold()==stage.casefold()]
        if source_type:
            candidate_idx=[i for i in candidate_idx if self.chunks[i]["source_type"]==source_type]
        if not candidate_idx: return []
        qv=self.vectorizer.transform([query])
        sims=cosine_similarity(qv, self.matrix[candidate_idx]).ravel()
        order=np.argsort(-sims)[:top_k]
        out=[]
        for rank, pos in enumerate(order, start=1):
            i=candidate_idx[int(pos)]; c=self.chunks[i]
            out.append({**c,"score":float(sims[int(pos)]),"rank":rank})
        return out

    @staticmethod
    def source_label(item):
        loc=item["path"]
        if item.get("page") is not None: loc += f" page {item['page']}"
        if item.get("row") is not None: loc += f" row {item['row']}"
        return loc
