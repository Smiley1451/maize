from pathlib import Path
import json
from app.indexer import ProjectIndexer
from app.retrieval import Retriever

def test_project_index_exists_after_build():
    r=ProjectIndexer().build(); assert r['file_count']>0; assert r['chunk_count']>0

def test_retrieval_finds_phase19():
    rr=Retriever().search('Phase 19 FastAPI backend', top_k=5)
    assert rr
    assert any('19_FASTAPI_BACKEND' in x['path'] for x in rr)

def test_retrieval_sources_have_metadata():
    rr=Retriever().search('maize yield model',top_k=3)
    assert rr
    for x in rr: assert 'path' in x and 'text' in x and 'score' in x
