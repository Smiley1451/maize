from __future__ import annotations
from pathlib import Path
import sys, json, os, subprocess
ROOT=Path(__file__).resolve().parents[1]; PROJECT=ROOT.parent
sys.path.insert(0,str(ROOT))
checks=[]
def ck(name,ok,note=""):
    ok=bool(ok); checks.append((name,ok,note)); print(f"[{ 'PASS' if ok else 'FAIL'}] {name} {('- '+note) if note else ''}")

try:
    import subprocess
    r=subprocess.run([sys.executable,str(ROOT/'scripts'/'check_powerShell_files.py')],cwd=str(ROOT),capture_output=True,text=True)
    ck('POWERSHELL_FILES', r.returncode==0, (r.stdout+r.stderr).strip())
except Exception as e:
    ck('POWERSHELL_FILES',False,str(e))
from app.indexer import ProjectIndexer, MANIFEST_JSON
try:
    r=ProjectIndexer().build(); ck("INDEX_BUILD", r['chunk_count']>0, f"files={r['file_count']} chunks={r['chunk_count']} errors={len(r['errors'])}")
except Exception as e: ck("INDEX_BUILD",False,str(e))
try:
    from app.assistant import ResearchAssistant
    a=ResearchAssistant(); ck("ASSISTANT_INIT",len(a.retriever.chunks)>0,f"chunks={len(a.retriever.chunks)}")
    for q in ["What is the project status?","Tell me about MAH-22-17","What models are available?","What is Phase 19?"]:
        rr=a.chat(q); ck("CHAT:"+q[:25],rr.get('status')=='ok' and bool(rr.get('answer')),rr.get('provider'))
except Exception as e: ck("ASSISTANT_RUNTIME",False,str(e))
try:
    import fastapi, uvicorn, pandas, sklearn, pypdf, httpx
    ck("DEPENDENCIES",True)
except Exception as e: ck("DEPENDENCIES",False,str(e))
try:
    env=dict(os.environ); env['PYTHONPATH']=str(ROOT)
    p=subprocess.run([sys.executable,'-m','pytest','-q',str(ROOT/'tests')],cwd=str(ROOT),env=env,text=True,capture_output=True,timeout=300)
    (ROOT/'outputs'/'PYTEST_OUTPUT.txt').write_text(p.stdout+'\n'+p.stderr,encoding='utf-8')
    last=p.stdout.splitlines()[-1] if p.stdout else f"exit={p.returncode}"
    ck("PYTEST",p.returncode==0,last)
except Exception as e: ck("PYTEST",False,str(e))
summary_lines=['# Phase 21 Verification','']
summary_lines += [f"- {'PASS' if ok else 'FAIL'}: {name} {note}" for name,ok,note in checks]
summary_lines += ['', 'Overall: '+('READY' if all(ok for _,ok,_ in checks) else 'NOT READY')]
(ROOT/'outputs'/'PHASE21_VERIFICATION.md').write_text('\n'.join(summary_lines)+'\n',encoding='utf-8')
print('PHASE 21 VERIFICATION:', 'READY' if all(ok for _,ok,_ in checks) else 'NOT READY')
raise SystemExit(0 if all(ok for _,ok,_ in checks) else 1)
