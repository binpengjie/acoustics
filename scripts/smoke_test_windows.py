from __future__ import annotations

import importlib
import json
import os
import subprocess
import sys
import time
import traceback
import argparse
import zipfile
from pathlib import Path
from urllib.request import urlopen


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "smoke_test_outputs"
LOG_PATH = OUT_DIR / "smoke_test_log.txt"
SUMMARY_PATH = OUT_DIR / "smoke_test_summary.json"


def reexec_into_project_venv() -> None:
    if os.environ.get("OKNG_SMOKE_IN_VENV") == "1":
        return
    venv_python = ROOT / ".venv" / "Scripts" / "python.exe"
    if not venv_python.exists():
        return
    try:
        if Path(sys.executable).resolve() == venv_python.resolve():
            return
    except OSError:
        pass
    env = os.environ.copy()
    env["OKNG_SMOKE_IN_VENV"] = "1"
    result = subprocess.run([str(venv_python), str(Path(__file__).resolve()), *sys.argv[1:]], cwd=ROOT, env=env)
    raise SystemExit(result.returncode)


def log(message: str) -> None:
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    print(message, flush=True)
    with LOG_PATH.open("a", encoding="utf-8") as f:
        f.write(message + "\n")


def require_path(path: Path) -> None:
    if not path.exists():
        raise FileNotFoundError(f"Required path missing: {path}")
    log(f"OK path: {path.relative_to(ROOT)}")


def import_versions() -> dict[str, str]:
    modules = {
        "numpy": "numpy",
        "scipy": "scipy",
        "sklearn": "sklearn",
        "joblib": "joblib",
        "streamlit": "streamlit",
        "pandas": "pandas",
        "matplotlib": "matplotlib",
        "pywt": "pywt",
        "soundfile": "soundfile",
    }
    versions: dict[str, str] = {}
    for name, module_name in modules.items():
        module = importlib.import_module(module_name)
        version = getattr(module, "__version__", "unknown")
        versions[name] = str(version)
        log(f"Imported {name}: {version}")
    return versions


def load_models() -> list[dict[str, str]]:
    import joblib

    model_paths = sorted((ROOT / "models").rglob("*.joblib"))
    if not model_paths:
        raise RuntimeError("No joblib models found under models/")
    loaded = []
    for model_path in model_paths:
        model = joblib.load(model_path)
        info = {
            "path": str(model_path.relative_to(ROOT)),
            "type": f"{type(model).__module__}.{type(model).__name__}",
        }
        loaded.append(info)
        log(f"Loaded model: {info['path']} -> {info['type']}")
    return loaded


def create_synthetic_wav() -> Path:
    import numpy as np
    from scipy.io import wavfile

    wav_path = OUT_DIR / "synthetic_test.wav"
    sr = 16000
    t = np.arange(int(sr * 1.5), dtype=np.float32) / sr
    x = 0.02 * np.sin(2.0 * np.pi * 440.0 * t)
    wavfile.write(wav_path, sr, (x * 32767.0).astype(np.int16))
    log(f"Wrote synthetic wav: {wav_path.relative_to(ROOT)}")
    return wav_path


def run_batch_prediction(wav_path: Path) -> dict[str, str]:
    batch_out = OUT_DIR / "batch_prediction"
    batch_out.mkdir(parents=True, exist_ok=True)
    cmd = [
        sys.executable,
        str(ROOT / "batch_predict.py"),
        "--input",
        str(wav_path),
        "--output",
        str(batch_out),
        "--mode",
        "high_recall",
    ]
    log("Running batch prediction CLI")
    result = subprocess.run(cmd, cwd=ROOT, text=True, capture_output=True, timeout=180)
    log(result.stdout.strip())
    if result.stderr.strip():
        log(result.stderr.strip())
    if result.returncode != 0:
        log("Batch CLI failed; trying direct prediction fallback")
        from src.model_io import load_model_bundle
        from src.predict import predict_one_file

        bundle = load_model_bundle(ROOT)
        row, _window_df, _feature_df = predict_one_file(wav_path, bundle=bundle, mode="high_recall")
        if row.get("prediction") == "FAILED":
            raise RuntimeError(f"Direct prediction failed after CLI failure: {row.get('error')}")
        direct_csv = batch_out / "predictions_direct.csv"
        import pandas as pd

        pd.DataFrame([row]).to_csv(direct_csv, index=False, encoding="utf-8-sig")
        return {"mode": "direct_fallback", "predictions_csv": str(direct_csv.relative_to(ROOT))}

    pred_csv = batch_out / "predictions.csv"
    report_html = batch_out / "report.html"
    require_path(pred_csv)
    require_path(report_html)
    return {
        "mode": "batch_cli",
        "predictions_csv": str(pred_csv.relative_to(ROOT)),
        "report_html": str(report_html.relative_to(ROOT)),
    }


def wait_for_http(url: str, process: subprocess.Popen, timeout_sec: int = 90) -> bool:
    deadline = time.time() + timeout_sec
    while time.time() < deadline:
        if process.poll() is not None:
            return False
        try:
            with urlopen(url, timeout=3) as response:
                if 200 <= response.status < 500:
                    return True
        except Exception:
            time.sleep(2)
    return False


def terminate_process(process: subprocess.Popen) -> None:
    if process.poll() is not None:
        return
    process.terminate()
    try:
        process.wait(timeout=15)
    except subprocess.TimeoutExpired:
        process.kill()
        process.wait(timeout=15)


def prepare_package_root(from_zip: bool) -> Path:
    if not from_zip:
        return ROOT / "dist" / "OKNG_Inspector_Windows"
    zip_path = ROOT / "dist" / "OKNG_Inspector_Windows_v0.1.zip"
    require_path(zip_path)
    extract_root = OUT_DIR / "extracted_portable"
    if extract_root.exists():
        import shutil

        shutil.rmtree(extract_root)
    extract_root.mkdir(parents=True, exist_ok=True)
    with zipfile.ZipFile(zip_path, "r") as zf:
        zf.extractall(extract_root)
    package_root = extract_root / "OKNG_Inspector_Windows"
    require_path(package_root)
    return package_root


def run_streamlit_startup_check(package_root: Path, require_packaged_exe: bool = False) -> dict[str, str]:
    url = "http://127.0.0.1:8765"
    env = os.environ.copy()
    env["OKNG_CI"] = "1"
    env["OKNG_PORT"] = "8765"

    exe = package_root / "OKNG_Inspector.exe"
    attempts = []
    if exe.exists():
        attempts.append(("packaged_exe", [str(exe)], package_root))
    elif require_packaged_exe:
        raise FileNotFoundError(f"Packaged exe missing: {exe}")
    if not require_packaged_exe:
        attempts.append(
            (
                "source_streamlit",
                [
                    sys.executable,
                    "-m",
                    "streamlit",
                    "run",
                    str(ROOT / "app.py"),
                    "--server.headless",
                    "true",
                    "--server.port",
                    "8765",
                    "--server.address",
                    "127.0.0.1",
                    "--browser.gatherUsageStats",
                    "false",
                ],
                ROOT,
            )
        )

    attempt_results = []
    for name, cmd, cwd in attempts:
        stream_log = OUT_DIR / f"streamlit_{name}.log"
        log(f"Starting Streamlit check via {name}")
        log(f"Command: {cmd}")
        log(f"CWD: {cwd}")
        with stream_log.open("w", encoding="utf-8") as f:
            process = subprocess.Popen(cmd, cwd=cwd, env=env, stdout=f, stderr=subprocess.STDOUT, text=True)
            try:
                if wait_for_http(url, process):
                    log(f"Streamlit startup passed via {name}: {url}")
                    return {
                        "mode": name,
                        "url": url,
                        "log": str(stream_log.relative_to(ROOT)),
                        "exe": str(exe),
                        "cwd": str(cwd),
                        "attempts": attempt_results,
                    }
                log_tail = ""
                if stream_log.exists():
                    log_tail = stream_log.read_text(encoding="utf-8", errors="replace")[-8000:]
                attempt = {
                    "mode": name,
                    "returncode": process.poll(),
                    "log": str(stream_log.relative_to(ROOT)),
                    "log_tail": log_tail,
                }
                attempt_results.append(attempt)
                log(f"Streamlit did not respond via {name}; returncode={process.poll()}")
                if log_tail:
                    log("Streamlit log tail:\n" + log_tail)
            finally:
                terminate_process(process)

    raise RuntimeError("Streamlit localhost startup check failed; attempts=" + json.dumps(attempt_results, ensure_ascii=False))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--from-zip", action="store_true", help="Extract dist zip and test the exe from the extracted portable folder.")
    parser.add_argument("--require-packaged-exe", action="store_true", help="Fail instead of falling back to source Streamlit if the packaged exe does not start.")
    args = parser.parse_args()
    reexec_into_project_venv()
    os.chdir(ROOT)
    OUT_DIR.mkdir(parents=True, exist_ok=True)
    LOG_PATH.write_text("", encoding="utf-8")
    summary: dict[str, object] = {
        "root": str(ROOT),
        "python": sys.executable,
        "status": "started",
    }
    try:
        log(f"Smoke test root: {ROOT}")
        log(f"Python executable: {sys.executable}")
        required_paths = [
            ROOT / "dist" / "OKNG_Inspector_Windows" / "OKNG_Inspector.exe",
            ROOT / "dist" / "OKNG_Inspector_Windows",
            ROOT / "models",
            ROOT / "configs",
            ROOT / "app.py",
            ROOT / "src",
            ROOT / "README_WINDOWS_USER.md",
        ]
        for path in required_paths:
            require_path(path)
        package_root = prepare_package_root(args.from_zip)
        require_path(package_root / "OKNG_Inspector.exe")
        require_path(package_root / "app.py")
        require_path(package_root / "src")
        require_path(package_root / "models")
        require_path(package_root / "configs")
        summary["portable_package_root"] = str(package_root)
        summary["dependency_versions"] = import_versions()
        summary["loaded_models"] = load_models()
        wav_path = create_synthetic_wav()
        summary["prediction"] = run_batch_prediction(wav_path)
        summary["streamlit"] = run_streamlit_startup_check(package_root, args.require_packaged_exe)
        summary["status"] = "passed"
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"Wrote summary: {SUMMARY_PATH.relative_to(ROOT)}")
        log("Smoke test passed")
        return 0
    except Exception as exc:
        summary["status"] = "failed"
        summary["error"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
        SUMMARY_PATH.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        log(f"Smoke test failed: {exc!r}")
        log(summary["traceback"])
        return 1


if __name__ == "__main__":
    raise SystemExit(main())
