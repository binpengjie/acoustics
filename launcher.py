from __future__ import annotations

import os
import socket
import sys
import threading
import traceback
import webbrowser
from pathlib import Path


def package_root() -> Path:
    # In a PyInstaller build, keep user-visible files beside the EXE.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


ROOT = package_root()


def ci_mode_enabled() -> bool:
    return os.environ.get("OKNG_CI", "").strip().lower() in {"1", "true", "yes"}


def write_launcher_log(message: str) -> None:
    try:
        log_path = ROOT / "OKNG_launcher_error.log"
        log_path.write_text(message, encoding="utf-8")
        print(f"Launcher error log: {log_path}")
    except Exception:
        print(message)


def pause_on_error() -> None:
    if ci_mode_enabled():
        return
    try:
        input("Press Enter to close this window...")
    except Exception:
        pass


def port_available(port: int) -> bool:
    with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
        return s.connect_ex(("127.0.0.1", port)) != 0


def choose_port(default: int = 8501) -> int:
    for port in [default, 8502, 8503, 8504, 8505]:
        if port_available(port):
            return port
    return default


def main() -> int:
    try:
        from streamlit.web import cli as stcli
    except Exception as exc:
        msg = (
            "Streamlit is not available inside this package.\n"
            "If running from source, install requirements_windows.txt first.\n"
            f"{repr(exc)}\n\n{traceback.format_exc()}"
        )
        write_launcher_log(msg)
        pause_on_error()
        return 1

    app_file = ROOT / "app.py"
    if not app_file.exists():
        print(f"Cannot find app.py at: {app_file}")
        print("The portable folder is incomplete. Rebuild with build_windows.bat and keep the whole dist folder together.")
        return 1

    os.chdir(ROOT)
    os.environ.setdefault("OKNG_PACKAGE_ROOT", str(ROOT))
    ci_mode = ci_mode_enabled()
    if ci_mode:
        port = int(os.environ.get("OKNG_PORT", "8765"))
        address = "127.0.0.1"
    else:
        port = choose_port(8501)
        address = "localhost"
    url = f"http://{address}:{port}"
    print("Starting OKNG Inspector local web app...")
    print(f"Package folder: {ROOT}")
    print(f"Local URL: {url}")
    if not ci_mode:
        threading.Timer(2.0, lambda: webbrowser.open(url)).start()
    sys.argv = [
        "streamlit", "run", str(app_file),
        "--server.port", str(port),
        "--server.address", address,
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]
    return stcli.main()


if __name__ == "__main__":
    try:
        raise SystemExit(main())
    except SystemExit as exc:
        code = exc.code if isinstance(exc.code, int) else 0
        if code not in (0, None):
            write_launcher_log(f"OKNG Inspector exited with code {code}.")
            pause_on_error()
        raise
    except BaseException:
        write_launcher_log("Unhandled OKNG Inspector launcher error:\n\n" + traceback.format_exc())
        pause_on_error()
        raise
