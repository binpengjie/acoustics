# OKNG Acoustic Inspector - Engineer Guide

## Architecture

Python backend, Streamlit local dashboard, scikit-learn models, and PyInstaller `onedir` Windows package. No cloud service is required.

## Included Models

- `models/full_clip_extratrees.joblib`: full-clip classical features + balanced ExtraTrees.
- `models/window_rf_4s.joblib`: 4-second window classical features + balanced RandomForest.
- `models/feature_names.json`: exact feature order.
- `models/model_metadata.json`: model provenance and benchmark notes.

## Feature Pipeline

Audio is converted to mono, resampled to 16 kHz, mean-centered, and peak-normalized. Features include RMS, peak, crest factor, zero-crossing rate, spectral centroid/bandwidth/rolloff/flatness/contrast, MFCC and delta MFCC statistics, log-Mel statistics, band ratios, and wavelet packet texture ratios.

## Modes And Thresholds

Configured in `configs/threshold_config.json`:

- Balanced: full-clip score, threshold 0.5.
- High Recall: `0.5 * full_clip_score + 0.5 * window_max_score`, threshold 0.42.
- Window Sensitive: 4s window max score, threshold 0.5.

The high-recall threshold came from random-split analysis and must be revalidated for new dates/products/conditions.

## Development Run

```bat
python -m pip install -r requirements_windows.txt
python launcher.py
```

or:

```bat
streamlit run app.py
```

## Batch Prediction

```bat
python batch_predict.py --input "D:\audio_folder" --output "D:\OKNG_results" --mode high_recall --threshold 0.42 --diagnostics
```

## Generate HTML Report

```bat
python generate_html_report.py --predictions "D:\OKNG_results\predictions.csv" --output "D:\OKNG_results\report.html"
```

## Retrain Models

If benchmark feature CSVs are available:

```bat
python retrain_models.py --feature-dir "D:\benchmark\features" --output-models models
```

Update `model_metadata.json`, thresholds, and model version after retraining.

## Build Windows Executable

Run on Windows:

```bat
build_windows.bat
```

Output folder:

`dist\OKNG_Inspector_Windows`

Zip the whole folder for users.

## Production Validation

Validate on labeled OK and NG data from each new date, product group, machine condition, microphone, and gain setting. Track NG recall, NG false-negative rate, and OK false-positive rate.

## Windows Build Troubleshooting: Python Not Found

If `build_windows.bat` prints `Python was not found`, install 64-bit Python 3.11 from:

https://www.python.org/downloads/windows/

During installation, enable:

`Add python.exe to PATH`

Then open a new Command Prompt and check:

```bat
python --version
```

If Windows opens Microsoft Store instead, disable the Store aliases:

`Settings > Apps > Advanced app settings > App execution aliases`

Turn off:

- `python.exe`
- `python3.exe`

The updated `build_windows.bat` creates a local `.venv`, installs requirements there, and runs PyInstaller as:

```bat
.venv\Scripts\python.exe -m PyInstaller ...
```

So you do not need a global `pyinstaller` command on PATH.
