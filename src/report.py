from __future__ import annotations
import html
import json
from pathlib import Path
import pandas as pd
from .utils import load_json, timestamp


def summarize_predictions(df):
    return {
        "total_files": int(len(df)),
        "OK": int((df.get("prediction") == "OK").sum()) if not df.empty else 0,
        "Review": int((df.get("prediction") == "Review").sum()) if not df.empty else 0,
        "NG": int((df.get("prediction") == "NG").sum()) if not df.empty else 0,
        "FAILED": int((df.get("prediction") == "FAILED").sum()) if not df.empty else 0,
    }


def generate_html_report(predictions_csv, output_html, app_config_path, threshold_config_path, model_metadata_path, input_path="", diagnostics_dir=None):
    predictions_csv = Path(predictions_csv)
    output_html = Path(output_html)
    df = pd.read_csv(predictions_csv) if predictions_csv.exists() and predictions_csv.stat().st_size else pd.DataFrame()
    app = load_json(app_config_path)
    th = load_json(threshold_config_path)
    md = load_json(model_metadata_path)
    summary = summarize_predictions(df)
    cols = [c for c in ["file_name", "inspection_mode", "threshold_used", "prediction", "risk_level", "final_NG_score", "full_clip_NG_score", "window_max_NG_score", "fusion_NG_score", "suspicious_window_start_sec", "suspicious_window_end_sec", "warning", "error"] if c in df.columns]
    table = df[cols].to_html(index=False, classes="pred-table", float_format=lambda x: f"{x:.4f}") if not df.empty else "<p>No predictions.</p>"
    top = df.sort_values("final_NG_score", ascending=False).head(10)[cols].to_html(index=False, float_format=lambda x: f"{x:.4f}") if not df.empty and "final_NG_score" in df else ""
    app_name = html.escape(str(app.get("app_name", "OKNG Acoustic Inspector")))
    app_version = html.escape(str(app.get("version", "unknown")))
    model_version = html.escape(str(md.get("model_version", "unknown")))
    input_text = html.escape(str(input_path))
    threshold_json = html.escape(json.dumps(th, indent=2, ensure_ascii=False))
    body = """<!doctype html>
<html><head><meta charset="utf-8"><title>OK/NG Inspection Report</title>
<style>
body {{ font-family: Arial, sans-serif; margin: 24px; color: #1f2933; }}
h1, h2 {{ color: #102a43; }}
.badge {{ display:inline-block; padding:6px 10px; margin:4px; border-radius:4px; background:#e3e8ef; }}
.warn {{ padding:12px; background:#fff3cd; border:1px solid #f0d98c; margin:12px 0; }}
table {{ border-collapse: collapse; width: 100%; font-size: 13px; }}
th, td {{ border:1px solid #ccd; padding:6px; text-align:left; }}
th {{ background:#eef2f7; }}
</style></head><body>
<h1>{app_name} Report</h1>
<p>Generated: {generated}</p>
<p>Input: {input_text}</p>
<p>App version: {app_version} | Model version: {model_version}</p>
<div class="warn"><b>Threshold warning:</b> Previous random-split performance was excellent, but robustness under new date/product/condition groups was weaker. Validate thresholds before production use on new conditions.</div>
<h2>Summary</h2>
<span class="badge">Total: {total}</span><span class="badge">OK: {ok}</span><span class="badge">Review: {review}</span><span class="badge">NG: {ng}</span><span class="badge">Failed: {failed}</span>
<h2>Configuration</h2><pre>{threshold_json}</pre>
<h2>Top Suspected NG Files</h2>{top}
<h2>Prediction Table</h2>{table}
<h2>Known Limitations</h2>
<ul><li>Thresholds must be revalidated for new dates, products, microphones, gains, and acquisition conditions.</li><li>WAV is preferred. MP3/M4A support depends on optional codecs.</li><li>Review results require manual inspection.</li></ul>
</body></html>""".format(app_name=app_name, generated=timestamp(), input_text=input_text, app_version=app_version, model_version=model_version, total=summary["total_files"], ok=summary["OK"], review=summary["Review"], ng=summary["NG"], failed=summary["FAILED"], threshold_json=threshold_json, top=top, table=table)
    output_html.parent.mkdir(parents=True, exist_ok=True)
    output_html.write_text(body, encoding="utf-8")
    return output_html
