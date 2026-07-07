# AGENT_STATE

Last update: 2026-07-07

Current valid Windows Streamlit package is in this directory.

GitHub Actions cloud build has been added:
- Workflow: `.github/workflows/build-windows.yml`
- Manual trigger: GitHub Actions -> Build OKNG Inspector Windows -> Run workflow
- Tag trigger: push tags matching `v*`
- Smoke test script: `scripts/smoke_test_windows.py`
- Artifact: `OKNG_Inspector_Windows_v0.1`

Primary entry points:
- `app.py`
- `install_env.bat`
- `run_app.bat`
- `run_cli_batch.bat`
- `src/batch_inference.py`

Model directories:
- `models/lineA_mahalanobis_handcrafted_full_clip/`
- `models/lineB_extratrees_balanced/`
- `models/model_manifest.json`

Smoke test passed on Linux/server using sklearn 1.2.2. Windows double-click behavior still needs verification on an actual Windows PC.

Important fix: 24-bit PCM scaling in `src/audio_io.py` was corrected so Line A Mahalanobis scores match training scale.


## Installer Update

`install_env.bat` has been made robust against missing Python Launcher (`py` not recognized). It now detects multiple Python entry points, common install locations, optional `winget`, custom `OKNG_PYTHON`, and offline `wheelhouse/` installs.
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
