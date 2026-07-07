from __future__ import annotations
import json
from datetime import datetime
from pathlib import Path
import traceback
import zipfile

def project_root() -> Path:
    return Path(__file__).resolve().parents[1]

def timestamp() -> str:
    return datetime.now().strftime("%Y%m%d_%H%M%S")

def read_json(path: Path):
    return json.loads(path.read_text(encoding="utf-8"))

def load_json(path: Path):
    return read_json(Path(path))

def collect_audio_files(input_path, supported_extensions=None) -> list[Path]:
    exts = {e.lower() for e in (supported_extensions or [".wav", ".flac", ".mp3", ".m4a"])}
    path = Path(input_path)
    if path.is_file() and path.suffix.lower() == ".zip":
        extract_dir = project_root() / "outputs" / "zip_inputs" / f"{path.stem}_{timestamp()}"
        extract_dir.mkdir(parents=True, exist_ok=True)
        with zipfile.ZipFile(path, "r") as zf:
            zf.extractall(extract_dir)
        path = extract_dir
    if path.is_file():
        return [path] if path.suffix.lower() in exts else []
    if path.is_dir():
        return sorted(p for p in path.rglob("*") if p.is_file() and p.suffix.lower() in exts)
    return []

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
