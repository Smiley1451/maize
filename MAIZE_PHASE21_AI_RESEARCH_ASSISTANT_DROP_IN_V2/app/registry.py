from __future__ import annotations
from pathlib import Path
import hashlib, json, os
from typing import Any
from .config import PROJECT_ROOT, ASSISTANT_ROOT, CFG
from .parsers import TEXT_EXTS, BINARY_EXTS

IGNORE_DIRS={".git",".venv","venv","__pycache__",".pytest_cache","node_modules","index","logs"}
# Logs are deliberately not ignored during inventory; individual large/transient caches can be excluded by extension.

class ProjectRegistry:
    def __init__(self, root: Path = PROJECT_ROOT):
        self.root=root.resolve()
        self.files: list[dict[str,Any]]=[]

    def _sha(self, p: Path) -> str:
        h=hashlib.sha256()
        with p.open("rb") as f:
            for chunk in iter(lambda:f.read(1024*1024), b""):
                h.update(chunk)
        return h.hexdigest()[:16]

    def scan(self) -> list[dict[str,Any]]:
        rows=[]
        for p in sorted(self.root.rglob("*")):
            if not p.is_file(): continue
            rel=p.relative_to(self.root).as_posix()
            parts=set(p.relative_to(self.root).parts[:-1])
            if parts & {".git",".venv","venv","__pycache__",".pytest_cache","node_modules"}: continue
            try: size=p.stat().st_size
            except OSError: continue
            ext=p.suffix.lower()
            stage=rel.split("/",1)[0] if "/" in rel else "ROOT"
            source_type="binary_artifact" if ext in BINARY_EXTS else ("csv" if ext==".csv" else "pdf" if ext==".pdf" else "text" if ext in TEXT_EXTS else "other")
            rows.append({"file_id": f"F{len(rows)+1:06d}", "path": rel, "extension": ext, "stage": stage,
                         "source_type": source_type, "size_bytes": size, "modified_time": p.stat().st_mtime,
                         "sha256_16": self._sha(p), "indexable": bool(source_type in {"csv","pdf","text"} and size <= CFG["max_file_mb"]*1024*1024),
                         "exists": True})
        self.files=rows
        return rows

    def save(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(json.dumps({"project_root":str(self.root),"file_count":len(self.files),"files":self.files}, indent=2), encoding="utf-8")

    @classmethod
    def load(cls, path: Path):
        data=json.loads(path.read_text(encoding="utf-8"))
        obj=cls(Path(data["project_root"]))
        obj.files=data.get("files",[])
        return obj
