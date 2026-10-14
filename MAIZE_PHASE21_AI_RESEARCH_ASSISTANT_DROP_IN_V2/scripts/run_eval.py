from __future__ import annotations
import sys,json,time
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from app.assistant import ResearchAssistant
OUT=ROOT/"outputs"; OUT.mkdir(exist_ok=True)
bench=ROOT/"config"/"benchmark_questions.json"
questions=json.loads(bench.read_text(encoding="utf-8"))
a=ResearchAssistant()
rows=[]
for i,q in enumerate(questions,1):
    print(f"[TEST {i:02d}/{len(questions):02d}] {q['question']}")
    t=time.time(); r=a.chat(q['question']); elapsed=round(time.time()-t,3)
    ok=bool(r.get('answer')) and (bool(r.get('sources')) or q.get('allow_no_source',False))
    rows.append({"id":q['id'],"question":q['question'],"status":"PASS" if ok else "FAIL","provider":r.get('provider'),"sources":len(r.get('sources',[])),"duration_sec":elapsed})
    print("  "+("[PASS] grounded response produced" if ok else "[FAIL] missing grounded response"))
import csv
with (OUT/"AI_EVALUATION_RESULTS.csv").open("w",encoding="utf-8",newline="") as f:
    w=csv.DictWriter(f,fieldnames=rows[0].keys()); w.writeheader(); w.writerows(rows)
passed=sum(x['status']=='PASS' for x in rows)
summary=(f"# AI Evaluation\n\nPASS={passed} FAIL={len(rows)-passed} TOTAL={len(rows)}\n\n"
         "The benchmark checks grounded response generation and source availability; semantic correctness should be reviewed with the actual LLM provider enabled for final evaluation.\n")
(OUT/"AI_EVALUATION_SUMMARY.md").write_text(summary,encoding="utf-8")
print(f"EVALUATION RESULT: PASS={passed} FAIL={len(rows)-passed}")
raise SystemExit(0 if passed==len(rows) else 1)
