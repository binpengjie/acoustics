# ENGINEERING_NOTES

## Source Inspection

Line A source: `/data1/pengjie/engineering/acoustic_OKNG_lineA_embedding_anomaly`

- Final artifact found: `models/mahalanobis_handcrafted_full_clip/model.joblib`
- Portable export created: `models/lineA_mahalanobis_handcrafted_full_clip/lineA_mahalanobis_arrays.npz`
- Feature schema copied from Line A artifact: 163 features.
- Threshold: 162.18298627520178
- Preprocessing: WAV -> mono average -> resample 16 kHz -> DC removal -> no peak normalization unless values exceed +/-1 -> full-clip handcrafted features.

Line B source: `/data1/pengjie/engineering/acoustic_OKNG_lineB_supervised_classification`

- Final artifact found: `models/classical_full_ExtraTrees_balanced.joblib`
- Copied to `models/lineB_extratrees_balanced/model.joblib`
- Feature schema reconstructed from `features/features_full.csv`: 202 features.
- Required sklearn version: 1.2.2. Newer sklearn 1.9 failed to unpickle old tree dtype, so Windows requirements pin scikit-learn==1.2.2.
- Preprocessing: tolerant WAV reader -> mono average -> resample 16 kHz -> DC removal -> peak normalization -> full-clip Line B classical features.
- Score convention: `predict_proba(X)[:, 1]` = NG probability-like score, threshold 0.5.

## Fusion

Default: Line B is primary; Line A is anomaly monitor. Line B NG -> final NG. Line B OK + Line A normal -> OK. Line B OK + Line A abnormal -> REVIEW.


## Implementation Fixes

- The first smoke test exposed incorrect Line A scores because 24-bit PCM was initially scaled as int32. `src/audio_io.py` now scales integer PCM by bit depth, matching the training-time soundfile scale.
- Line B joblib is loaded with `scikit-learn==1.2.2`; requirements are pinned to avoid tree pickle incompatibility.
- Runtime model loading uses relative paths from the package root. Linux source paths are retained only in this engineering note.
