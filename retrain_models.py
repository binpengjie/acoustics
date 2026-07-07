from __future__ import annotations
import argparse, json
from pathlib import Path
import joblib, pandas as pd
from sklearn.ensemble import ExtraTreesClassifier, RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.pipeline import Pipeline
from src.feature_extract import META_COLUMNS
ROOT=Path(__file__).resolve().parent
def cols(df): return [c for c in df.columns if c not in META_COLUMNS]
def main():
    p=argparse.ArgumentParser(); p.add_argument("--feature-dir",required=True); p.add_argument("--output-models",default=str(ROOT/"models")); a=p.parse_args(); fd=Path(a.feature_dir); out=Path(a.output_models); out.mkdir(parents=True,exist_ok=True); full=pd.read_csv(fd/"features_full.csv"); win4=pd.read_csv(fd/"features_4s.csv"); c=cols(full)
    fm=Pipeline([("impute",SimpleImputer()),("clf",ExtraTreesClassifier(n_estimators=700,class_weight="balanced",random_state=42,n_jobs=-1,min_samples_leaf=1))]); wm=Pipeline([("impute",SimpleImputer()),("clf",RandomForestClassifier(n_estimators=500,class_weight="balanced_subsample",random_state=42,n_jobs=-1,min_samples_leaf=2))]); fm.fit(full[c],full.label.astype(int)); wm.fit(win4[c],win4.label.astype(int)); joblib.dump(fm,out/"full_clip_extratrees.joblib"); joblib.dump(wm,out/"window_rf_4s.joblib"); (out/"feature_names.json").write_text(json.dumps({"feature_pipeline_version":"classical_features_v1_from_lineB_benchmark","feature_names":c,"n_features":len(c)},indent=2),encoding="utf-8"); print(f"Saved models to {out}"); return 0
if __name__=="__main__": raise SystemExit(main())
