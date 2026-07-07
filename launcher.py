from __future__ import annotations

import os
import socket
import sys
import threading
import webbrowser
from pathlib import Path


def package_root() -> Path:
    # In a PyInstaller build, keep user-visible files beside the EXE.
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent


ROOT = package_root()


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
        print("Streamlit is not available inside this package.")
        print("If running from source, install requirements_windows.txt first.")
        print(repr(exc))
        return 1

    app_file = ROOT / "app.py"
    if not app_file.exists():
        print(f"Cannot find app.py at: {app_file}")
        print("The portable folder is incomplete. Rebuild with build_windows.bat and keep the whole dist folder together.")
        return 1

    os.chdir(ROOT)
    os.environ.setdefault("OKNG_PACKAGE_ROOT", str(ROOT))
    port = choose_port(8501)
    url = f"http://localhost:{port}"
    print("Starting OKNG Inspector local web app...")
    print(f"Package folder: {ROOT}")
    print(f"Opening {url}")
    threading.Timer(2.0, lambda: webbrowser.open(url)).start()
    sys.argv = [
        "streamlit", "run", str(app_file),
        "--server.port", str(port),
        "--server.headless", "true",
        "--browser.gatherUsageStats", "false",
    ]
    return stcli.main()


if __name__ == "__main__":
    raise SystemExit(main())
