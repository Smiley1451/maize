from __future__ import annotations
from pathlib import Path
import json, time
from typing import Any
from .registry import ProjectRegistry
from .parsers import chunk_text, parse_text_file, parse_csv_rows, parse_pdf
from .config import PROJECT_ROOT, ASSISTANT_ROOT, CFG

INDEX_JSONL = ASSISTANT_ROOT / "index" / "chunks.jsonl"
REGISTRY_JSON = ASSISTANT_ROOT / "index" / "project_registry.json"
MANIFEST_JSON = ASSISTANT_ROOT / "index" / "index_manifest.json"

class ProjectIndexer:
    def __init__(self):
        self.registry=ProjectRegistry(PROJECT_ROOT)

    def build(self) -> dict[str, Any]:
        started=time.time()
        files=self.registry.scan(); self.registry.save(REGISTRY_JSON)
        INDEX_JSONL.parent.mkdir(parents=True, exist_ok=True)
        chunks=[]; errors=[]; counts={}
        for rec in files:
            if not rec["indexable"] or rec["extension"]==".joblib":
                continue
            path=PROJECT_ROOT / rec["path"]
            try:
                if rec["source_type"]=="csv":
                    for row_no, txt in parse_csv_rows(path, CFG["csv_max_rows_per_file"]):
                        for j,c in enumerate(chunk_text(txt, CFG["chunk_size"], CFG["chunk_overlap"])):
                            chunks.append({"file_id":rec["file_id"],"path":rec["path"],"source_type":"csv","row":row_no,"page":None,"chunk":j,"text":c})
                elif rec["source_type"]=="pdf":
                    for page_no, txt in parse_pdf(path):
                        for j,c in enumerate(chunk_text(txt, CFG["chunk_size"], CFG["chunk_overlap"])):
                            if c:
                                chunks.append({"file_id":rec["file_id"],"path":rec["path"],"source_type":"pdf","row":None,"page":page_no,"chunk":j,"text":c})
                else:
                    txt=parse_text_file(path, CFG["max_index_chars_per_text_file"])
                    for j,c in enumerate(chunk_text(txt, CFG["chunk_size"], CFG["chunk_overlap"])):
                        chunks.append({"file_id":rec["file_id"],"path":rec["path"],"source_type":"text","row":None,"page":None,"chunk":j,"text":c})
                counts[rec["source_type"]]=counts.get(rec["source_type"],0)+1
            except Exception as exc:
                errors.append({"path":rec["path"],"error":str(exc)})
        with INDEX_JSONL.open("w", encoding="utf-8") as f:
            for c in chunks:
                f.write(json.dumps(c, ensure_ascii=False) + "\n")
        manifest={"built_at":time.strftime("%Y-%m-%dT%H:%M:%S"),"project_root":str(PROJECT_ROOT),"file_count":len(files),"chunk_count":len(chunks),"source_counts":counts,"errors":errors,"duration_sec":round(time.time()-started,3)}
        MANIFEST_JSON.write_text(json.dumps(manifest,indent=2),encoding="utf-8")
        return manifest

    @staticmethod
    def load_chunks() -> list[dict[str,Any]]:
        if not INDEX_JSONL.exists(): return []
        out=[]
        with INDEX_JSONL.open("r",encoding="utf-8") as f:
            for line in f:
                if line.strip(): out.append(json.loads(line))
        return out
