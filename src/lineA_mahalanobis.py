from __future__ import annotations
import json
import numpy as np
from pathlib import Path
from .config import LINEA_MODEL_DIR
from .audio_io import load_for_lineA
from .features import lineA_feature_dict, vectorize_features

class LineAMahalanobis:
    def __init__(self, model_dir: Path = LINEA_MODEL_DIR, threshold_override: float | None = None):
        self.model_dir = Path(model_dir)
        self.schema = json.loads((self.model_dir / "feature_schema.json").read_text(encoding="utf-8"))
        self.threshold_info = json.loads((self.model_dir / "threshold.json").read_text(encoding="utf-8"))
        self.threshold = float(threshold_override if threshold_override is not None else self.threshold_info.get("recommended_threshold", self.threshold_info.get("threshold")))
        arr = np.load(self.model_dir / "lineA_mahalanobis_arrays.npz")
        self.mean = arr["scaler_mean"].astype(float)
        self.scale = arr["scaler_scale"].astype(float)
        self.location = arr["ok_location"].astype(float)
        self.precision = arr["precision"].astype(float)

    def score_features(self, feats: dict):
        x = vectorize_features(feats, self.schema).astype(float)
        z = (x - self.mean) / self.scale - self.location
        v = z @ self.precision
        contrib = (z * v)[0]
        score = float(np.einsum("ij,ij->i", z, v)[0])
        return score, contrib

    def predict_file(self, path: str | Path, topk: int = 8):
        y, sr, info = load_for_lineA(path)
        feats = lineA_feature_dict(y, sr)
        score, contrib = self.score_features(feats)
        flag = bool(score > self.threshold)
        order = np.argsort(np.abs(contrib))[::-1][:topk]
        top = [{"feature": self.schema[i], "contribution": float(contrib[i]), "value": float(feats.get(self.schema[i], 0.0))} for i in order]
        return {
            "lineA_anomaly_score": score,
            "lineA_threshold": self.threshold,
            "lineA_margin": score - self.threshold,
            "lineA_flag": flag,
            "lineA_top_features": top,
            "lineA_feature_values": feats,
            **info,
        }
