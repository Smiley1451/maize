"""Linux/macOS alternative to run_pipeline.ps1. Interactive controller with the same stage workflow."""
from __future__ import annotations
import json, subprocess, sys
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
SCRIPTS=ROOT/'scripts'; STATE=ROOT/'pipeline_state.json'
STAGES={1:('Model readiness audit','stage_01_readiness.py'),2:('Yield baseline models','stage_02_yield_baseline.py'),3:('TLB + SDM disease models','stage_03_disease_models.py'),4:('PCA + genotype clustering','stage_04_clustering.py'),5:('Weather risk readiness','stage_05_weather_readiness.py'),6:('Group-aware hyperparameter tuning','stage_06_tuning.py'),7:('Model explainability','stage_07_explainability.py'),8:('Model packaging','stage_08_packaging.py'),9:('Final project verification','stage_09_verify.py')}
def load():
    if STATE.exists():
        try:return json.loads(STATE.read_text())
        except:pass
    return {'current':1,'last_completed':0,'last_failed':0,'status':'NEW'}
def save(s): STATE.write_text(json.dumps(s,indent=2))
def run(n):
    s=load(); s.update(current=n,status='RUNNING'); save(s)
    print(f'\nSTEP {n}/9: TRAIN/RUN {STAGES[n][0]}',flush=True)
    r=subprocess.run([sys.executable,str(SCRIPTS/STAGES[n][1])])
    s=load()
    if r.returncode==0:
        s.update(last_completed=n,current=min(n+1,9),last_failed=0,status='DONE')
        print(f'STEP {n} DONE: {STAGES[n][0]}',flush=True)
    else:
        s.update(last_failed=n,status='FAILED')
        print(f'STEP {n} FAILED. Fix/retry from the menu.',flush=True)
    save(s); return r.returncode==0
def status():
    s=load(); print('\nPROJECT PIPELINE STATUS')
    for n,(name,_) in STAGES.items(): print(f'{n}. {name:<36} {"DONE" if n<=s["last_completed"] else "NEXT" if n==s["current"] else "PENDING"}')
    print(s)
def main():
    if len(sys.argv)>1 and sys.argv[1] in {'next','prev','redo','all','status'}:
        a=sys.argv[1]; s=load()
        if a=='next': run(int(s['current'])) if int(s['current'])<=9 else print('All steps completed.')
        elif a=='prev': s['current']=max(1,int(s['current'])-1); save(s)
        elif a=='redo': run(int(s['last_failed'] or s['last_completed'] or 1))
        elif a=='all':
            for n in range(int(s['current']),10):
                if not run(n): sys.exit(2)
        else: status()
        return
    while True:
        status(); print('\n1 Next  2 Previous  3 Redo  4 All remaining  5 Run selected  6 Retry failed  7 Status  8 Exit')
        c=input('Press a number: ').strip()
        s=load()
        if c=='1' and int(s['current'])<=9: run(int(s['current']))
        elif c=='2': s['current']=max(1,int(s['current'])-1); save(s)
        elif c=='3': run(int(s['last_failed'] or s['last_completed'] or 1))
        elif c=='4':
            for n in range(int(s['current']),10):
                if not run(n): break
        elif c=='5': run(int(input('Stage 1-9: ')))
        elif c=='6': run(int(s['last_failed'])) if int(s['last_failed']) else print('No failed step.')
        elif c=='7': status()
        elif c=='8': break
        else: print('Invalid choice.')
if __name__=='__main__': main()
