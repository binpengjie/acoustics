# RESULT_SUMMARY

Created a Windows-local Streamlit Web App package for industrial acoustic OK/NG inspection.

## Models

- Line B primary classifier: `ExtraTrees_balanced`, copied to `models/lineB_extratrees_balanced/model.joblib`.
- Line A anomaly monitor: `handcrafted_full_clip + mahalanobis_ok`, exported to `models/lineA_mahalanobis_handcrafted_full_clip/lineA_mahalanobis_arrays.npz`.

## Fusion Policy

Default mode uses Line B as primary classifier and Line A as secondary anomaly monitor:

1. Line B predicts NG -> final NG.
2. Line B predicts OK and Line A score <= threshold -> final OK.
3. Line B predicts OK and Line A score > threshold -> final REVIEW.
4. Line B predicts NG and Line A is normal -> final NG with explanation.

Optional modes: `lineB_only`, `lineA_only`, `conservative`.

## Thresholds And Metrics

- Line A threshold: `162.18298627520178`.
- Line A expected NG FNR: `0.0477`.
- Line B expected NG FNR: about `0.0075`.
- Line B expected balanced accuracy: about `0.9962`.

## Windows Use

1. Install Python 3.11.
2. Double-click `install_env.bat`.
3. Double-click `run_app.bat`.
4. Browser opens at `http://localhost:8501`.

## Smoke Test

`smoke_test_results.md` reports Overall: OK.

## Known Limitation

The app was generated and tested on Linux/server. Actual `.bat` double-click launch must still be verified on a Windows PC.

## GitHub Actions Cloud Windows Build

Added workflow `Build OKNG Inspector Windows` at `.github/workflows/build-windows.yml`.

Supported triggers:
- Manual: `workflow_dispatch`
- Tag push: `v*`

The build runs on GitHub-hosted `windows-2025` with Python 3.11 x64, not on the local Windows machine. It runs `build_windows.bat`, verifies `dist/OKNG_Inspector_Windows/OKNG_Inspector.exe` and `dist/OKNG_Inspector_Windows_v0.1.zip`, runs `scripts/smoke_test_windows.py`, then uploads artifact `OKNG_Inspector_Windows_v0.1` with 3-day retention.

Smoke test coverage: file integrity, dependency imports, all `models/**/*.joblib` loading, synthetic wav prediction through `batch_predict.py`, output CSV/HTML report generation, and localhost Streamlit startup.

User download path after a successful run: GitHub repo -> Actions -> Build OKNG Inspector Windows -> selected run -> Artifacts -> `OKNG_Inspector_Windows_v0.1`.

The app remains usable, but thresholds must be revalidated for new dates, product types, and acquisition conditions because group-holdout robustness was weaker than random-split performance.
## Blind Test 2026-07-07

Input data: `/data1/pengjie/engineering/test`, extracted to `/data1/pengjie/engineering/test/extracted`.

Outputs saved under `outputs/reports/blind_test_20260707/`.

Summary:
- Total WAV files: 465; failed inference files: 0.
- Folders: `1.Being合并` = 66 files, `1.LK盲测合并` = 399 files.
- Labels are not present in the blind-test filenames/folders, so these are prediction and consistency results, not accuracy metrics.
- Line A Mahalanobis anomaly monitor flagged 220/465 as anomaly/NG at threshold 162.18298627520178.
- Line B ExtraTrees classifier predicted 182/465 as NG at probability threshold 0.5.
- Fusion decisions: OK = 235, NG = 182, REVIEW = 48, FAILED = 0.
- Binary agreement between Line A flag and Line B class: 407/465 = 87.5%.
- `1.Being合并`: both methods flagged/predicted all 66 files as NG/anomaly.
- `1.LK盲测合并`: Line A flagged 154/399 anomaly, Line B predicted 116/399 NG, fusion REVIEW = 48.

Key files:
- `outputs/reports/blind_test_20260707/blind_test_analysis_summary.md`
- `outputs/reports/blind_test_20260707/blind_test_comparison.csv`
- `outputs/reports/blind_test_20260707/blind_test_batch_summary.csv`
- `outputs/reports/blind_test_20260707/blind_test_method_conflicts.csv`
- `outputs/reports/blind_test_20260707/plots/`
