from pathlib import Path
from app.config import PROJECT_ROOT, ASSISTANT_ROOT
from app.indexer import MANIFEST_JSON

def test_project_root_exists(): assert PROJECT_ROOT.exists()
def test_assistant_root_exists(): assert ASSISTANT_ROOT.exists()
def test_index_manifest_exists_after_collection(): assert MANIFEST_JSON.exists()
def test_no_external_file_paths_in_registry():
    reg=(ASSISTANT_ROOT/'index'/'project_registry.json').read_text(encoding='utf-8')
    assert str(PROJECT_ROOT) not in reg.split('"files"',1)[-1] if '"files"' in reg else True
