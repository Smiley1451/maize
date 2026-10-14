from __future__ import annotations
from pathlib import Path
import argparse, json, sys
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parent))
from prediction_engine import predict_dataframe


def main():
    ap=argparse.ArgumentParser(description='Predict maize yield, TLB and SDM using packaged models.')
    ap.add_argument('--input',required=True,help='CSV or JSON input file')
    ap.add_argument('--output',default='',help='Output CSV path (default: input_predictions.csv)')
    args=ap.parse_args()
    src=Path(args.input)
    if not src.exists(): raise FileNotFoundError(f'Input file not found: {src}')
    if src.suffix.lower()=='.json':
        obj=json.loads(src.read_text(encoding='utf-8'))
        if isinstance(obj,dict): obj=[obj]
        df=pd.DataFrame(obj)
    else:
        df=pd.read_csv(src)
    out=predict_dataframe(df)
    dest=Path(args.output) if args.output else src.with_name(src.stem+'_predictions.csv')
    dest.parent.mkdir(parents=True,exist_ok=True); out.to_csv(dest,index=False)
    print(f'PREDICTION COMPLETE: {len(out)} rows -> {dest}',flush=True)
    print('Model statuses:',flush=True)
    for c in [x for x in out.columns if x.endswith('_model_status')]:
        print(f'  {c}: {out[c].iloc[0] if len(out) else "NO_ROWS"}',flush=True)

if __name__=='__main__': main()
