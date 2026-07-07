from __future__ import annotations
import argparse
from pathlib import Path
from src.report import generate_html_report
ROOT=Path(__file__).resolve().parent
def main():
    p=argparse.ArgumentParser(); p.add_argument("--predictions",default=str(ROOT/"outputs/predictions.csv")); p.add_argument("--output",default=str(ROOT/"outputs/reports/report.html")); p.add_argument("--input",default=""); a=p.parse_args(); metadata_path=ROOT/"models/model_metadata.json"
    if not metadata_path.exists(): metadata_path=ROOT/"models/model_manifest.json"
    print(generate_html_report(a.predictions,a.output,ROOT/"configs/app_config.json",ROOT/"configs/threshold_config.json",metadata_path,input_path=a.input)); return 0
if __name__=="__main__": raise SystemExit(main())
