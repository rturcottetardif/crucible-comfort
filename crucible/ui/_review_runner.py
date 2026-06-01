"""
crucible.ui._review_runner — subprocess target for the review trigger.

Runs /advisor hw via the claude CLI and streams output to stdout.
The parent FastAPI process captures stdout via Popen pipe.

Invoked by:
    python -m crucible.ui._review_runner
"""

import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent

def main():
    print("[review-runner] Starting /advisor hw review...", flush=True)
    try:
        result = subprocess.run(
            ["claude", "--print", "/advisor hw"],
            cwd=str(PROJECT_ROOT),
            capture_output=False,
            text=True,
        )
        if result.returncode != 0:
            print(f"[review-runner] claude CLI exited with code {result.returncode}", flush=True)
    except FileNotFoundError:
        print(
            "[review-runner] ERROR: 'claude' CLI not found on PATH. "
            "Run the review manually via /advisor hw in Claude Code.",
            flush=True,
        )
    print("[review-runner] Done.", flush=True)


if __name__ == "__main__":
    main()
