from __future__ import annotations

import argparse
import csv
import json
import math
import os
import socket
import struct
import subprocess
import sys
import time
import traceback
import wave
from pathlib import Path
from urllib.request import urlopen


def write_wav(path: Path, sr: int = 16000, seconds: float = 1.5) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    n = int(sr * seconds)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        frames = bytearray()
        for i in range(n):
            t = i / sr
            val = int(0.02 * 32767 * math.sin(2 * math.pi * 440 * t))
            frames.extend(struct.pack("<h", val))
        wf.writeframes(bytes(frames))


def port_open(host: str, port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
        sock.settimeout(1.0)
        return sock.connect_ex((host, port)) == 0


def wait_http(url: str, proc: subprocess.Popen, timeout_sec: int) -> tuple[bool, str]:
    deadline = time.time() + timeout_sec
    last_error = ""
    while time.time() < deadline:
        if proc.poll() is not None:
            return False, f"process exited early with returncode={proc.returncode}"
        try:
            with urlopen(url, timeout=3) as resp:
                body = resp.read(4096).decode("utf-8", errors="replace")
                return True, f"http_status={resp.status}; body_prefix={body[:200]!r}"
        except Exception as exc:
            last_error = repr(exc)
            time.sleep(2)
    return False, f"timeout waiting for {url}; last_error={last_error}"


def stop_process(proc: subprocess.Popen) -> None:
    if proc.poll() is not None:
        return
    proc.terminate()
    try:
        proc.wait(timeout=15)
    except subprocess.TimeoutExpired:
        proc.kill()
        proc.wait(timeout=15)


def tail(path: Path, limit: int = 12000) -> str:
    if not path.exists():
        return ""
    return path.read_text(encoding="utf-8", errors="replace")[-limit:]


def run_cmd(cmd: list[str], cwd: Path, log_path: Path, timeout_sec: int = 180) -> subprocess.CompletedProcess:
    with log_path.open("w", encoding="utf-8") as f:
        f.write("COMMAND: " + " ".join(map(str, cmd)) + "\n")
        f.flush()
        proc = subprocess.run(
            cmd,
            cwd=cwd,
            text=True,
            stdout=f,
            stderr=subprocess.STDOUT,
            timeout=timeout_sec,
        )
    return proc


def main() -> int:
    parser = argparse.ArgumentParser(description="Real Windows acceptance test for OKNG Inspector portable package.")
    parser.add_argument("--repo-root", default=".", help="Repository root used for source Python scripts.")
    parser.add_argument("--package-root", default=r"dist\OKNG_Inspector_Windows", help="Portable package folder containing OKNG_Inspector.exe.")
    parser.add_argument("--port", type=int, default=8765)
    parser.add_argument("--timeout-sec", type=int, default=150)
    parser.add_argument("--output-dir", default=r"windows_acceptance_outputs")
    args = parser.parse_args()

    repo_root = Path(args.repo_root).resolve()
    package_root = (repo_root / args.package_root).resolve() if not Path(args.package_root).is_absolute() else Path(args.package_root).resolve()
    out_dir = (repo_root / args.output_dir).resolve()
    out_dir.mkdir(parents=True, exist_ok=True)
    summary_path = out_dir / "windows_acceptance_summary.json"
    exe_path = package_root / "OKNG_Inspector.exe"
    launcher_log = out_dir / "launcher_stdout_stderr.log"
    batch_log = out_dir / "batch_predict.log"
    report_log = out_dir / "generate_report.log"
    synthetic_wav = out_dir / "synthetic_acceptance.wav"
    batch_out = out_dir / "batch_prediction"
    standalone_report = out_dir / "standalone_report.html"

    summary: dict[str, object] = {
        "status": "started",
        "repo_root": str(repo_root),
        "package_root": str(package_root),
        "exe_path": str(exe_path),
        "python": sys.executable,
        "port": args.port,
        "checks": {},
    }

    proc: subprocess.Popen | None = None
    try:
        required = [
            exe_path,
            package_root / "app.py",
            package_root / "src",
            package_root / "models",
            package_root / "configs",
            package_root / "batch_predict.py",
            package_root / "generate_html_report.py",
        ]
        missing = [str(p) for p in required if not p.exists()]
        if missing:
            raise FileNotFoundError("Missing package files: " + json.dumps(missing, ensure_ascii=False))
        summary["checks"]["package_files"] = "passed"

        env = os.environ.copy()
        env["OKNG_CI"] = "1"
        env["OKNG_PORT"] = str(args.port)
        env["STREAMLIT_GLOBAL_DEVELOPMENT_MODE"] = "false"
        with launcher_log.open("w", encoding="utf-8") as f:
            proc = subprocess.Popen(
                [str(exe_path)],
                cwd=package_root,
                env=env,
                stdout=f,
                stderr=subprocess.STDOUT,
                text=True,
            )
            ok, detail = wait_http(f"http://127.0.0.1:{args.port}", proc, args.timeout_sec)
        summary["checks"]["exe_http"] = {"passed": ok, "detail": detail, "launcher_log": str(launcher_log)}
        if not ok:
            raise RuntimeError("Packaged exe did not start localhost: " + detail)

        write_wav(synthetic_wav)
        summary["checks"]["synthetic_wav"] = str(synthetic_wav)

        batch_cmd = [
            sys.executable,
            str(package_root / "batch_predict.py"),
            "--input",
            str(synthetic_wav),
            "--output",
            str(batch_out),
            "--mode",
            "high_recall",
        ]
        batch_result = run_cmd(batch_cmd, cwd=package_root, log_path=batch_log, timeout_sec=240)
        pred_csv = batch_out / "predictions.csv"
        report_html = batch_out / "report.html"
        summary["checks"]["batch_predict"] = {
            "returncode": batch_result.returncode,
            "predictions_csv": str(pred_csv),
            "report_html": str(report_html),
            "log": str(batch_log),
        }
        if batch_result.returncode != 0 or not pred_csv.exists() or not report_html.exists():
            raise RuntimeError("batch_predict.py failed; see " + str(batch_log))
        with pred_csv.open("r", encoding="utf-8-sig", newline="") as f:
            rows = list(csv.DictReader(f))
        if not rows:
            raise RuntimeError("predictions.csv has no rows")
        summary["checks"]["prediction_row"] = rows[0]

        report_cmd = [
            sys.executable,
            str(package_root / "generate_html_report.py"),
            "--predictions",
            str(pred_csv),
            "--output",
            str(standalone_report),
            "--input",
            str(synthetic_wav),
        ]
        report_result = run_cmd(report_cmd, cwd=package_root, log_path=report_log, timeout_sec=120)
        summary["checks"]["standalone_html_report"] = {
            "returncode": report_result.returncode,
            "html": str(standalone_report),
            "log": str(report_log),
            "size_bytes": standalone_report.stat().st_size if standalone_report.exists() else 0,
        }
        if report_result.returncode != 0 or not standalone_report.exists() or standalone_report.stat().st_size == 0:
            raise RuntimeError("generate_html_report.py failed; see " + str(report_log))

        summary["status"] = "passed"
        return 0
    except Exception as exc:
        summary["status"] = "failed"
        summary["error"] = repr(exc)
        summary["traceback"] = traceback.format_exc()
        summary["launcher_log_tail"] = tail(launcher_log)
        summary["batch_log_tail"] = tail(batch_log)
        summary["report_log_tail"] = tail(report_log)
        return 1
    finally:
        if proc is not None:
            stop_process(proc)
        summary_path.write_text(json.dumps(summary, indent=2, ensure_ascii=False), encoding="utf-8")
        print(json.dumps(summary, indent=2, ensure_ascii=False))
        print(f"Wrote {summary_path}")


if __name__ == "__main__":
    raise SystemExit(main())
