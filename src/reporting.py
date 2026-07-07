from __future__ import annotations
from pathlib import Path
import pandas as pd
from sklearn.metrics import confusion_matrix, balanced_accuracy_score, roc_auc_score, average_precision_score

def label_from_path(path: str) -> str | None:
    parts = [p.upper() for p in Path(path).parts]
    if "NG" in parts:
        return "NG"
    if "OK" in parts:
        return "OK"
    return None

def validation_report(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    d = df.copy()
    if "label" not in d:
        d["label"] = d["file_path"].map(label_from_path)
    d = d[d["label"].isin(["OK","NG"])].copy()
    d["y_true"] = (d["label"] == "NG").astype(int)
    d["y_pred"] = (d["final_decision"].isin(["NG","REVIEW"])).astype(int)
    tn, fp, fn, tp = confusion_matrix(d["y_true"], d["y_pred"], labels=[0,1]).ravel()
    lines = ["# Fresh Batch Validation", "", f"- files: {len(d)}", f"- TN={tn}, FP={fp}, FN={fn}, TP={tp}"]
    lines += [
        f"- NG recall: {tp/(tp+fn+1e-12):.4f}",
        f"- NG false-negative rate: {fn/(tp+fn+1e-12):.4f}",
        f"- OK false-positive rate: {fp/(tn+fp+1e-12):.4f}",
        f"- Balanced accuracy: {balanced_accuracy_score(d['y_true'], d['y_pred']):.4f}",
    ]
    if d["lineA_anomaly_score"].notna().any() and len(set(d["y_true"])) == 2:
        lines.append(f"- Line A ROC-AUC: {roc_auc_score(d['y_true'], d['lineA_anomaly_score'].fillna(0)):.4f}")
        lines.append(f"- Line A PR-AUC: {average_precision_score(d['y_true'], d['lineA_anomaly_score'].fillna(0)):.4f}")
    return d, "\n".join(lines) + "\n"
