from __future__ import annotations
import json
from pathlib import Path
import joblib
import numpy as np
import pandas as pd
from .config import LINEB_MODEL_DIR
from .audio_io import load_for_lineB
from .features import lineB_feature_dict, vectorize_features

class LineBClassifier:
    def __init__(self, model_dir: Path = LINEB_MODEL_DIR):
        self.model_dir = Path(model_dir)
        self.schema = json.loads((self.model_dir / "feature_schema.json").read_text(encoding="utf-8"))
        self.metadata = json.loads((self.model_dir / "metadata.json").read_text(encoding="utf-8"))
        self.model = joblib.load(self.model_dir / "model.joblib")
        self.threshold = float(self.metadata.get("decision_threshold", 0.5))

    def predict_file(self, path: str | Path):
        y, sr, info = load_for_lineB(path)
        feats = lineB_feature_dict(y)
        x = pd.DataFrame(vectorize_features(feats, self.schema), columns=self.schema)
        if hasattr(self.model, "predict_proba"):
            proba = self.model.predict_proba(x)[0]
            classes = list(getattr(self.model, "classes_", [0, 1]))
            idx = classes.index(1) if 1 in classes else -1
            score_ng = float(proba[idx])
        elif hasattr(self.model, "decision_function"):
            raw = float(self.model.decision_function(x)[0])
            score_ng = 1.0 / (1.0 + np.exp(-raw))
        else:
            score_ng = float(self.model.predict(x)[0])
        pred = "NG" if score_ng >= self.threshold else "OK"
        return {
            "lineB_pred": pred,
            "lineB_score_or_probability": score_ng,
            "lineB_threshold": self.threshold,
            "lineB_feature_values": feats,
            **info,
        }
