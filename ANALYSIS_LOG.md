# ANALYSIS_LOG

- Inspected Line A outputs and deployable Mahalanobis artifact.
- Inspected Line B outputs and found saved best model `models/classical_full_ExtraTrees_balanced.joblib`.
- Confirmed Line B model requires scikit-learn 1.2.2; newer sklearn failed to unpickle tree dtype.
- Created Streamlit Windows-local package with relative runtime paths.
- Exported Line A model to portable arrays (`lineA_mahalanobis_arrays.npz`) to avoid sklearn dependency for Line A.
- Copied Line B ExtraTrees joblib and reconstructed feature schema from Line B `features_full.csv`.
- Implemented CLI batch inference and Streamlit UI pages.
- Smoke test initially exposed incorrect Line A 24-bit PCM scaling; fixed `src/audio_io.py` to scale by bit depth.
- Final smoke test passed: Line A loaded, Line B loaded, single file inference OK, batch inference OK, required columns OK, app syntax OK, bat files relative.
- Tue Jul  7 02:17:36 UTC 2026: Updated build_windows.bat to detect python/py launcher, create .venv, and call python -m PyInstaller; appended build troubleshooting docs.
- Updated Windows installer to handle missing `py`, PATH issues, winget fallback, custom Python path, and offline wheelhouse installs.
- Tue Jul  7 05:30:38 UTC 2026: Strengthened portable Windows build: top-level app files beside EXE, expanded dependency collection, automatic zip, Chinese build guide.
- 2026-07-07: Ran blind-test inference on `/data1/pengjie/engineering/test` with Line A, Line B, and fusion. Saved detailed analysis under `outputs/reports/blind_test_20260707/`. No failed files; fusion OK/NG/REVIEW = 235/182/48.
## GitHub Actions Windows Build 2026-07-07

- Added `.github/workflows/build-windows.yml` for GitHub-hosted Windows cloud builds only.
- Confirmed official tags exist for `actions/checkout@v6`, `actions/setup-python@v6`, and `actions/upload-artifact@v4`.
- Updated `build_windows.bat` for CI compatibility: project-local `.venv`, `.pip_cache`, `.pyinstaller_config`, `tmp`, no global pip install, no CI pause, fixed portable zip path, and explicit exe/zip verification.
- Added `scripts/smoke_test_windows.py` to validate dependencies, joblib model loading, synthetic wav batch prediction, report output, and localhost Streamlit startup.
- Updated `launcher.py` with `OKNG_CI=1` support: no browser open, `127.0.0.1`, and `OKNG_PORT`.
- Added `README_GITHUB_ACTIONS_CN.md` explaining cloud build usage, artifact download, smoke test coverage, and limitations.
