import sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.indexer import ProjectIndexer
result=ProjectIndexer().build()
print(f"INDEX BUILD DONE | files={result['file_count']} chunks={result['chunk_count']} errors={len(result['errors'])}")
for e in result['errors'][:20]: print("INDEX ERROR:",e)
raise SystemExit(0 if not result['errors'] else 0)
