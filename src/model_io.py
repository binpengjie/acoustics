from __future__ import annotations
from dataclasses import dataclass
from pathlib import Path
import joblib
from .utils import project_root, load_json
@dataclass
class ModelBundle:
    full_model: object; window_model: object; feature_names: list[str]; metadata: dict; threshold_config: dict; app_config: dict; model_config: dict
def load_model_bundle(root=None):
    root=Path(root) if root else project_root(); app=load_json(root/"configs/app_config.json"); mc=load_json(root/"configs/model_config.json"); tc=load_json(root/"configs/threshold_config.json"); fd=load_json(root/mc["feature_names_path"]); md=load_json(root/"models/model_metadata.json")
    return ModelBundle(joblib.load(root/mc["full_clip_model_path"]), joblib.load(root/mc["window_model_path"]), fd["feature_names"], md, tc, app, mc)
