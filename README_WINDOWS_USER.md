# OKNG Acoustic Inspector - Windows User Guide

This app runs locally on your Windows computer. Audio files are not uploaded to the cloud.

## Launch

1. Unzip `OKNG_Inspector_Windows_v0.1.zip` to a normal folder, for example `D:\OKNG_Inspector_Windows`.
2. Double-click `OKNG_Inspector.exe`.
3. A browser should open at `http://localhost:8501` or another local port shown in the console.

## Inspect Audio

1. Select audio files, enter a folder path, or upload a zip file.
2. Choose `Balanced`, `High Recall`, or `Window Sensitive`.
3. Click `Run Inspection`.
4. Review OK, Review, NG, and Failed counts.
5. Download `predictions.csv` or `report.html`.

## Label Meaning

- `OK`: score is clearly below threshold.
- `Review`: score is close to threshold; manual inspection is recommended.
- `NG`: score is above threshold.
- `FAILED`: file could not be read or processed.

## Important Warning

For new product types, new dates, or new acquisition conditions, validate the threshold before trusting automatic decisions. Previous random-split performance was excellent, but group-holdout robustness was weaker.

## Troubleshooting

- Browser does not open: manually open the local URL shown in the console.
- Port occupied: the launcher tries 8501, 8502, 8503, 8504, 8505.
- Audio unsupported: WAV is recommended. Convert MP3/M4A to WAV if needed.
- Windows Defender warning: internal tools may warn if not code-signed; confirm the package came from engineering.
- App closes immediately: run from Command Prompt and send the console text to engineering.
