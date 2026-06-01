#!/usr/bin/env python3
"""
scripts/review_dashboard.py — launch the Crucible schematic review dashboard.

Usage:
    python scripts/review_dashboard.py
    python scripts/review_dashboard.py --port 7823
    python scripts/review_dashboard.py --host 0.0.0.0 --port 8080

Opens http://localhost:7823 in your browser after startup.
"""

import argparse
import os
import sys
import webbrowser
from pathlib import Path

# Project root is one level up from scripts/
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
_VENV_PYTHON = _PROJECT_ROOT / ".venv" / "bin" / "python"

# If we're not already running from the project venv, re-exec with it.
# This makes `python scripts/review_dashboard.py` work regardless of which
# Python is active in the shell.
if _VENV_PYTHON.exists() and Path(sys.executable).resolve() != _VENV_PYTHON.resolve():
    os.execv(str(_VENV_PYTHON), [str(_VENV_PYTHON)] + sys.argv)

sys.path.insert(0, str(_PROJECT_ROOT))


def main():
    parser = argparse.ArgumentParser(description="Crucible schematic review dashboard")
    parser.add_argument("--host", default="127.0.0.1", help="Bind host (default: 127.0.0.1)")
    parser.add_argument("--port", type=int, default=7823, help="Bind port (default: 7823)")
    parser.add_argument("--no-browser", action="store_true", help="Don't open browser automatically")
    args = parser.parse_args()

    try:
        import uvicorn
    except ImportError:
        print("ERROR: uvicorn not installed. Run: pip install uvicorn fastapi")
        sys.exit(1)

    url = f"http://{args.host}:{args.port}"
    print(f"Crucible Schematic Review Dashboard")
    print(f"  URL: {url}")
    print(f"  Press Ctrl+C to stop")

    if not args.no_browser:
        import threading
        import time
        def _open():
            time.sleep(1.2)
            webbrowser.open(url)
        threading.Thread(target=_open, daemon=True).start()

    uvicorn.run(
        "crucible.ui.server:app",
        host=args.host,
        port=args.port,
        reload=False,
        log_level="warning",
    )


if __name__ == "__main__":
    main()
