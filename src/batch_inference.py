from __future__ import annotations
import argparse
from pathlib import Path
import pandas as pd
from .audio_io import find_audio_files
from .lineA_mahalanobis import LineAMahalanobis
from .lineB_classifier import LineBClassifier
from .fusion import fuse
from .utils import friendly_error

OUTPUT_COLUMNS = [
    "file_path","file_name","duration_sec","sample_rate","channels",
    "lineB_pred","lineB_score_or_probability","lineA_anomaly_score",
    "lineA_threshold","lineA_margin","lineA_flag","final_decision",
    "decision_reason","warning_message","processing_status"
]

def infer_path(path, mode="fusion", recursive=True, threshold_override=None):
    files = find_audio_files(path, recursive=recursive)
    if Path(path).is_file() and not files:
        files = [Path(path)]
    lineA = None if mode == "lineB_only" else LineAMahalanobis(threshold_override=threshold_override)
    lineB = None if mode == "lineA_only" else LineBClassifier()
    rows = []
    for p in files:
        try:
            a = lineA.predict_file(p) if lineA else None
            b = lineB.predict_file(p) if lineB else None
            dec = fuse(a, b, mode)
            info = a or b or {}
            row = {
                "file_path": str(p),
                "file_name": p.name,
                "duration_sec": info.get("duration_sec"),
                "sample_rate": info.get("sample_rate"),
                "channels": info.get("channels"),
                "lineB_pred": b.get("lineB_pred") if b else None,
                "lineB_score_or_probability": b.get("lineB_score_or_probability") if b else None,
                "lineA_anomaly_score": a.get("lineA_anomaly_score") if a else None,
                "lineA_threshold": a.get("lineA_threshold") if a else None,
                "lineA_margin": a.get("lineA_margin") if a else None,
                "lineA_flag": a.get("lineA_flag") if a else None,
                "final_decision": dec["final_decision"],
                "decision_reason": dec["decision_reason"],
                "warning_message": "",
                "processing_status": "ok",
            }
        except Exception as e:
            row = {
                "file_path": str(p), "file_name": Path(p).name, "duration_sec": None,
                "sample_rate": None, "channels": None, "lineB_pred": None,
                "lineB_score_or_probability": None, "lineA_anomaly_score": None,
                "lineA_threshold": threshold_override, "lineA_margin": None, "lineA_flag": None,
                "final_decision": "FAILED", "decision_reason": "处理失败",
                "warning_message": friendly_error(e), "processing_status": "failed",
            }
        rows.append(row)
    if not rows:
        rows.append({"file_path": str(path), "file_name": Path(path).name, "final_decision": "FAILED", "decision_reason": "未找到支持的音频文件", "warning_message": "未找到 WAV/FLAC/MP3/M4A 文件", "processing_status": "failed"})
    df = pd.DataFrame(rows)
    for c in OUTPUT_COLUMNS:
        if c not in df:
            df[c] = None
    return df[OUTPUT_COLUMNS]

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--input", required=True, help="audio file or folder")
    ap.add_argument("--output", required=True, help="output CSV path")
    ap.add_argument("--mode", default="fusion", choices=["fusion","lineB_only","lineA_only","conservative"])
    ap.add_argument("--no-recursive", action="store_true")
    ap.add_argument("--threshold", type=float, default=None)
    args = ap.parse_args()
    df = infer_path(args.input, mode=args.mode, recursive=not args.no_recursive, threshold_override=args.threshold)
    out = Path(args.output)
    out.parent.mkdir(parents=True, exist_ok=True)
    df.to_csv(out, index=False, encoding="utf-8-sig")
    print(str(out))

if __name__ == "__main__":
    main()
