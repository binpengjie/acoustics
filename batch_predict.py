from __future__ import annotations
import argparse
from pathlib import Path
from src.model_io import load_model_bundle
from src.predict import predict_input_path
from src.utils import ensure_dir
from src.visualization import save_diagnostics
from src.report import generate_html_report
ROOT=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(description="Batch acoustic OK/NG prediction"); p.add_argument("--input",required=True); p.add_argument("--output",required=True); p.add_argument("--mode",default="high_recall",choices=["balanced","high_recall","window_sensitive","engineer_custom"]); p.add_argument("--threshold",type=float,default=None); p.add_argument("--fusion-weight",type=float,default=None); p.add_argument("--window-sec",type=float,default=4.0); p.add_argument("--aggregation",default="max",choices=["max","mean","top-k mean"]); p.add_argument("--review-margin",type=float,default=None); p.add_argument("--diagnostics",action="store_true"); args=p.parse_args()
    out=ensure_dir(args.output); diag=ensure_dir(out/"diagnostics"); bundle=load_model_bundle(ROOT); df,win,feat=predict_input_path(args.input,bundle=bundle,mode=args.mode,threshold=args.threshold,fusion_weight=args.fusion_weight,window_sec=args.window_sec,aggregation=args.aggregation,review_margin=args.review_margin); csv=out/"predictions.csv"; df.to_csv(csv,index=False,encoding="utf-8-sig")
    if args.diagnostics:
        for _,row in df[df["prediction"].isin(["NG","Review"])].head(100).iterrows(): save_diagnostics(row["file"],win.get(row["file"]),diag)
    report=generate_html_report(csv,out/"report.html",ROOT/"configs/app_config.json",ROOT/"configs/threshold_config.json",ROOT/"models/model_metadata.json",input_path=args.input,diagnostics_dir=diag); print(f"Wrote {csv}"); print(f"Wrote {report}"); return 0
if __name__=="__main__": raise SystemExit(main())
