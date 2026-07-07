# Model Card

## Training Data
1265 WAV files: OK=384, NG=881. All files are 48 kHz stereo and about 15.98 s.

## Line B
ExtraTrees_balanced supervised classifier. Primary OK/NG model. Expected balanced accuracy about 0.9962 and NG false-negative rate about 0.0075 on prior file-level split.

## Line A
Handcrafted full-clip Mahalanobis OK-distribution model. Secondary anomaly monitor and drift detector. Threshold 162.18298627520178. Expected NG FNR about 0.0477 under repeated validation-threshold splits.

## Robustness
Line A was not mainly driven by amplitude or channel artifacts: left/right/mono behaved similarly, and peak/RMS normalization did not hurt performance. Date holdout had uneven groups, so fresh-batch validation is required.

## Limitations
Both models are trained on current Line A/B data. New products, microphone changes, production-line changes, or background noise shifts require validation and likely recalibration.

## Trust Guidance
Trust Line B when new production data is label-stable and matches training distribution. Pay attention to Line A REVIEW when unknown NG types or drift may appear.
