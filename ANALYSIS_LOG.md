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
