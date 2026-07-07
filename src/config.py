from __future__ import annotations
from pathlib import Path

APP_ROOT = Path(__file__).resolve().parents[1]
MODELS_DIR = APP_ROOT / "models"
OUTPUTS_DIR = APP_ROOT / "outputs"
REPORTS_DIR = OUTPUTS_DIR / "reports"
HISTORY_DIR = OUTPUTS_DIR / "inference_history"
LINEA_MODEL_DIR = MODELS_DIR / "lineA_mahalanobis_handcrafted_full_clip"
LINEB_MODEL_DIR = MODELS_DIR / "lineB_extratrees_balanced"
MANIFEST_PATH = MODELS_DIR / "model_manifest.json"
TARGET_SR = 16000
AUDIO_EXTS = {".wav", ".wave", ".flac", ".mp3", ".m4a", ".aac", ".ogg"}
DEFAULT_MODE = "fusion"
DEFAULT_LANGUAGE = "zh"
