"""
crucible.ui._review_runner — subprocess target for the review trigger.

Streams /advisor hw output line by line to stdout so the FastAPI SSE
endpoint can forward each line to the dashboard in real time.
"""

import subprocess
import sys
import time
from pathlib import Path

PROJECT_ROOT = Path(__file__).parent.parent.parent
REVIEW_DIR = PROJECT_ROOT / "docs" / "schematic_review"
FINDINGS_FILES = [
    REVIEW_DIR / "correctness_findings.json",
    REVIEW_DIR / "layout_findings.json",
    REVIEW_DIR / "verifier_findings.json",
]


def ts():
    return time.strftime("%H:%M:%S")


def log(msg: str) -> None:
    print(f"[{ts()}] {msg}", flush=True)


def main():
    log("── Review started ──────────────────────────────")
    log("Invoking: claude --print '/advisor hw'")
    log("(this may take 30–90 s while agents run in parallel)")
    log("")

    # Check schematic exists
    sch_files = list((PROJECT_ROOT / "hardware").glob("*.kicad_sch"))
    if sch_files:
        log(f"Schematic: {sch_files[0].name}")
    else:
        log("WARNING: No .kicad_sch found in hardware/ — agents may skip schematic checks")

    log("")
    log("Spawning hw-advisor → schematic-correctness, schematic-layout, schematic-verifier")
    log("─────────────────────────────────────────────────────────────────────────────────")

    try:
        proc = subprocess.Popen(
            ["claude", "--print", "/advisor hw"],
            cwd=str(PROJECT_ROOT),
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT,
            text=True,
            bufsize=1,
        )
        for line in proc.stdout:
            print(line, end="", flush=True)
        proc.wait()
        if proc.returncode != 0:
            log(f"WARNING: claude CLI exited with code {proc.returncode}")
    except FileNotFoundError:
        log("ERROR: 'claude' CLI not found on PATH.")
        log("Run the review manually via /advisor hw in Claude Code,")
        log("then reload this page — the findings panel will update automatically.")
        sys.exit(1)

    log("")
    log("─────────────────────────────────────────────────────────────────────────────────")
    log("Agent run complete. Checking output files…")
    log("")

    found_any = False
    import json
    total_fail = total_warn = total_pass = 0
    for path in FINDINGS_FILES:
        if path.exists():
            try:
                items = json.loads(path.read_text())
                fail = sum(1 for x in items if x.get("status") in ("FAIL", "MISMATCH"))
                warn = sum(1 for x in items if x.get("status") in ("WARN", "MISSING"))
                pas  = sum(1 for x in items if x.get("status") in ("PASS", "MATCH"))
                total_fail += fail; total_warn += warn; total_pass += pas
                log(f"  {path.name}: {fail} FAIL  {warn} WARN  {pas} PASS")
                found_any = True
            except Exception as e:
                log(f"  {path.name}: parse error — {e}")
        else:
            log(f"  {path.name}: not written (agent may not have run)")

    if found_any:
        log("")
        log(f"Total: {total_fail} FAIL  {total_warn} WARN  {total_pass} PASS")
    else:
        log("")
        log("No findings files written — check agent output above for errors.")

    log("")
    log("── Review done — reload findings panel ─────────")


if __name__ == "__main__":
    main()
