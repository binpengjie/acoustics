from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
import traceback

def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")

def friendly_error(exc: Exception) -> str:
    msg = str(exc) or exc.__class__.__name__
    low = msg.lower()
    if "format" in low or "riff" in low or "wav" in low:
        return f"文件无法读取或音频格式暂不支持: {msg}"
    if "model" in low or "joblib" in low:
        return f"模型文件缺失或版本不兼容: {msg}"
    return f"推理失败，请查看日志: {msg}"
