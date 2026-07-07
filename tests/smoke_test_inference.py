from __future__ import annotations
from pathlib import Path
import json
import pandas as pd
from src.lineA_mahalanobis import LineAMahalanobis
from src.lineB_classifier import LineBClassifier
from src.batch_inference import infer_path, OUTPUT_COLUMNS

ROOT = Path(__file__).resolve().parents[1]

def main():
    samples = []
    data_root = Path("/data1/pengjie/engineering/acoustic_OKNG_lineA_embedding_anomaly/extracted/5月OK-NG")
    for lab in ["OK", "NG"]:
        samples.extend(sorted((data_root / lab).glob("*.wav"))[:2])
    results = []
    ok = True
    try:
        LineAMahalanobis()
        results.append("- Line A model loaded: OK")
    except Exception as e:
        ok = False; results.append(f"- Line A model loaded: FAILED {e}")
    try:
        LineBClassifier()
        results.append("- Line B model loaded: OK")
    except Exception as e:
        ok = False; results.append(f"- Line B model loaded: FAILED {e}")
    df = infer_path(samples[0], mode="fusion") if samples else pd.DataFrame()
    if not df.empty and set(OUTPUT_COLUMNS).issubset(df.columns):
        results.append("- Single-file inference: OK")
    else:
        ok = False; results.append("- Single-file inference: FAILED")
    batch_df = pd.concat([infer_path(p, mode="fusion") for p in samples], ignore_index=True) if samples else pd.DataFrame()
    batch_df.to_csv(ROOT / "smoke_test_predictions.csv", index=False)
    missing = [c for c in OUTPUT_COLUMNS if c not in batch_df.columns]
    if not missing:
        results.append("- Batch result columns: OK")
    else:
        ok = False; results.append(f"- Batch result columns missing: {missing}")
    try:
        import py_compile
        py_compile.compile(str(ROOT / "app.py"), doraise=True)
        results.append("- Streamlit app syntax import/compile: OK")
    except Exception as e:
        ok = False; results.append(f"- Streamlit app syntax: FAILED {e}")
    for bat in ["install_env.bat", "run_app.bat", "run_cli_batch.bat"]:
        text = (ROOT / bat).read_text(encoding="utf-8")
        if "/data1/" in text:
            ok = False; results.append(f"- {bat}: FAILED contains Linux absolute path")
        else:
            results.append(f"- {bat}: OK relative paths")
    (ROOT / "smoke_test_results.md").write_text("# Smoke Test Results\n\n" + "\n".join(results) + f"\n\nOverall: {'OK' if ok else 'FAILED'}\n", encoding="utf-8")
    print("OK" if ok else "FAILED")

if __name__ == "__main__":
    main()
