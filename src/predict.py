from __future__ import annotations
from pathlib import Path
import numpy as np, pandas as pd
from .audio_io import load_audio
from .feature_extract import extract_full_features, extract_window_features, align_feature_frame
from .model_io import load_model_bundle, ModelBundle
from .utils import collect_audio_files, timestamp
def _proba(model,xdf):
    if hasattr(model,"predict_proba"): return model.predict_proba(xdf)[:,1]
    s=np.asarray(model.decision_function(xdf),dtype=float); return (s-s.min())/(s.max()-s.min()+1e-12)
def aggregate_scores(scores, method="max", top_k=3):
    scores=np.asarray(scores,dtype=float)
    if scores.size==0: return float("nan")
    if method=="mean": return float(np.mean(scores))
    if method=="top-k mean": return float(np.mean(np.sort(scores)[-min(int(top_k),len(scores)):]))
    return float(np.max(scores))
def threshold_for_mode(bundle, mode, custom_threshold=None):
    if custom_threshold is not None: return float(custom_threshold)
    return float({"balanced":bundle.threshold_config["balanced_threshold"],"high_recall":bundle.threshold_config["high_recall_threshold"],"window_sensitive":bundle.threshold_config["window_sensitive_threshold"]}.get(mode,bundle.threshold_config.get("balanced_threshold",0.5)))
def classify(score, threshold, review_margin):
    if not np.isfinite(score): return "FAILED","failed"
    if score>=threshold: return "NG","high"
    if score>=threshold-review_margin: return "Review","medium"
    return "OK","low"
def predict_one_file(path, bundle=None, mode="high_recall", threshold=None, fusion_weight=None, window_sec=4.0, aggregation="max", review_margin=None, batch_label=""):
    bundle=bundle or load_model_bundle(); review_margin=float(bundle.threshold_config.get("review_margin",0.05) if review_margin is None else review_margin); fusion_weight=float(bundle.threshold_config.get("fusion_weight_full",0.5) if fusion_weight is None else fusion_weight); threshold_used=threshold_for_mode(bundle,mode,threshold)
    base={"file":str(path),"file_name":Path(path).name,"run_time":timestamp(),"app_version":bundle.app_config.get("version"),"model_version":bundle.metadata.get("model_version"),"inspection_mode":mode,"threshold_used":threshold_used,"fusion_weight_full":fusion_weight,"window_sec":window_sec,"aggregation":aggregation,"batch_label":batch_label,"duration_sec":None,"original_sample_rate":None,"channels":None,"warning":"","error":""}
    try:
        x,info=load_audio(path,target_sr=int(bundle.model_config.get("sample_rate_hz",16000))); base.update({"duration_sec":info.duration_sec,"original_sample_rate":info.original_sample_rate,"channels":info.channels,"warning":info.warning})
        full_df=align_feature_frame(extract_full_features(x,bundle.feature_names),bundle.feature_names); full_score=float(_proba(bundle.full_model,full_df)[0])
        win_raw=extract_window_features(x,window_sec,bundle.feature_names); win_x=align_feature_frame(win_raw,bundle.feature_names); win_scores=_proba(bundle.window_model,win_x); win_raw["window_NG_score"]=win_scores
        win_score=aggregate_scores(win_scores,aggregation); best_idx=int(np.argmax(win_scores)) if len(win_scores) else 0; start=float(win_raw.iloc[best_idx].get("window_start_sec",0.0)) if len(win_raw) else None; end=float(win_raw.iloc[best_idx].get("window_end_sec",0.0)) if len(win_raw) else None
        fusion=float(fusion_weight*full_score+(1.0-fusion_weight)*win_score); final=full_score if mode=="balanced" else (win_score if mode=="window_sensitive" else fusion); pred,risk=classify(final,threshold_used,review_margin)
        row=dict(base); row.update({"full_clip_NG_score":full_score,"window_max_NG_score":win_score,"fusion_NG_score":fusion,"final_NG_score":final,"prediction":pred,"risk_level":risk,"suspicious_window_start_sec":start,"suspicious_window_end_sec":end}); return row, win_raw[["window_index","window_start_sec","window_end_sec","window_NG_score"]].copy(), full_df.copy()
    except Exception as exc:
        row=dict(base); row.update({"error":repr(exc),"prediction":"FAILED","risk_level":"failed","full_clip_NG_score":np.nan,"window_max_NG_score":np.nan,"fusion_NG_score":np.nan,"final_NG_score":np.nan,"suspicious_window_start_sec":None,"suspicious_window_end_sec":None}); return row,pd.DataFrame(),pd.DataFrame()
def predict_files(paths, bundle=None, **kwargs):
    bundle=bundle or load_model_bundle(); rows=[]; windows={}; features={}
    for p in paths:
        row,win,feat=predict_one_file(p,bundle=bundle,**kwargs); rows.append(row); windows[str(p)]=win; features[str(p)]=feat
    return pd.DataFrame(rows),windows,features
def predict_input_path(input_path,bundle=None,**kwargs):
    bundle=bundle or load_model_bundle(); return predict_files(collect_audio_files(input_path,bundle.app_config.get("supported_extensions")),bundle=bundle,**kwargs)
