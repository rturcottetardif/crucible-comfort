"""
crucible.ui.server — FastAPI schematic review dashboard.

Routes:
    GET  /                         → dashboard HTML page
    GET  /schematic.svg            → serve hardware/comfortsense.svg
    GET  /api/findings             → merged all_findings.json
    POST /api/findings/{id}/action → engineer action (resolve/escalate/note)
    POST /api/review/trigger       → start a new review run
    GET  /api/review/stream        → SSE stream of live review output
"""

from __future__ import annotations

import asyncio
import json
import subprocess
import sys
from pathlib import Path
from typing import AsyncIterator

from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse, HTMLResponse, StreamingResponse
from fastapi.staticfiles import StaticFiles
from pydantic import BaseModel

from crucible.hw.review import load_findings, merge_findings, save_findings

# ---------------------------------------------------------------------------
# Paths (resolved relative to project root, not this file)
# ---------------------------------------------------------------------------

_HERE = Path(__file__).parent
_PROJECT_ROOT = _HERE.parent.parent
_HARDWARE_DIR = _PROJECT_ROOT / "hardware"
_REVIEW_DIR = _PROJECT_ROOT / "docs" / "schematic_review"
_BILLS_DIR = _PROJECT_ROOT / "docs" / "governance" / "bills"
_STATIC_DIR = _HERE / "static"

SCH_SVG = _HARDWARE_DIR / "comfortsense.svg"
ALL_FINDINGS = _REVIEW_DIR / "all_findings.json"

FINDINGS_FILES = [
    _REVIEW_DIR / "correctness_findings.json",
    _REVIEW_DIR / "layout_findings.json",
    _REVIEW_DIR / "verifier_findings.json",
]

# ---------------------------------------------------------------------------
# App
# ---------------------------------------------------------------------------

app = FastAPI(title="Crucible Schematic Review", version="0.1.0")

# ---------------------------------------------------------------------------
# HTML dashboard
# ---------------------------------------------------------------------------

@app.get("/", response_class=HTMLResponse)
async def dashboard():
    html_path = _STATIC_DIR / "dashboard.html"
    if not html_path.exists():
        raise HTTPException(status_code=500, detail="dashboard.html not found")
    return HTMLResponse(html_path.read_text())


# ---------------------------------------------------------------------------
# Schematic SVG
# ---------------------------------------------------------------------------

@app.get("/schematic.svg")
async def schematic_svg():
    if not SCH_SVG.exists():
        raise HTTPException(status_code=404, detail=f"SVG not found: {SCH_SVG}")
    return FileResponse(SCH_SVG, media_type="image/svg+xml")


# ---------------------------------------------------------------------------
# Findings API
# ---------------------------------------------------------------------------

@app.get("/api/findings")
async def get_findings():
    """Return merged findings from all agent outputs."""
    findings = merge_findings(*FINDINGS_FILES)
    result = []
    for f in findings:
        d = {
            "id": f.id,
            "source": f.source,
            "check": f.check,
            "ref": f.ref,
            "status": f.status,
            "finding": f.finding,
            "fix": f.fix,
            "rule_basis": f.rule_basis,
            "coords": list(f.coords) if f.coords else None,
            "engineer_action": f.engineer_action,
            "note": f.note,
        }
        result.append(d)
    return result


class ActionRequest(BaseModel):
    action: str   # "resolved" | "escalated" | "noted"
    note: str | None = None


@app.post("/api/findings/{finding_id}/action")
async def engineer_action(finding_id: str, body: ActionRequest):
    """Record an engineer action on a finding and persist to all_findings.json."""
    if body.action not in ("resolved", "escalated", "noted"):
        raise HTTPException(status_code=400, detail="action must be resolved|escalated|noted")

    findings = merge_findings(*FINDINGS_FILES)
    target = next((f for f in findings if f.id == finding_id), None)
    if target is None:
        raise HTTPException(status_code=404, detail=f"Finding {finding_id} not found")

    target.engineer_action = body.action
    if body.note:
        target.note = body.note

    save_findings(ALL_FINDINGS, findings)

    # For escalated findings, write a Bill stub file
    if body.action == "escalated":
        _write_bill_stub(target)

    return {"ok": True, "id": finding_id, "action": body.action}


def _write_bill_stub(finding) -> None:
    """Write a pre-filled Bill stub markdown file for the engineer to confirm."""
    _BILLS_DIR.mkdir(parents=True, exist_ok=True)
    safe_id = finding.id.replace("/", "-")
    stub_path = _BILLS_DIR / f"bill_stub_{safe_id}.md"
    fix_text = finding.fix or "(fix not yet specified — review manually)"
    stub_path.write_text(
        f"# Bill Stub — {finding.check}: {finding.ref}\n\n"
        f"> **Status:** DRAFT — engineer must confirm before bill-drafter polishes.\n\n"
        f"## Evidence\n{finding.finding}\n\n"
        f"## Proposed Change\n{fix_text}\n\n"
        f"## Rule Basis\n{finding.rule_basis}\n\n"
        f"## Source\nAgent: {finding.source}  |  Finding ID: {finding.id}\n"
    )


# ---------------------------------------------------------------------------
# Review trigger + SSE stream
# ---------------------------------------------------------------------------

_review_process: subprocess.Popen | None = None
_review_output: list[str] = []


def _ts() -> str:
    import time
    return time.strftime("%H:%M:%S")


@app.post("/api/review/trigger")
async def trigger_review():
    """Start a new /advisor hw review run via claude CLI."""
    global _review_process, _review_output
    if _review_process and _review_process.poll() is None:
        return {"ok": False, "message": "Review already running"}
    _review_output = [
        f"[{_ts()}] Dashboard: launching review subprocess…",
        f"[{_ts()}] Dashboard: schematic = {SCH_SVG.name}",
        f"[{_ts()}] Dashboard: output → docs/schematic_review/",
    ]
    _review_process = subprocess.Popen(
        [sys.executable, "-m", "crucible.ui._review_runner"],
        cwd=str(_PROJECT_ROOT),
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )
    asyncio.create_task(_collect_output())
    return {"ok": True, "message": "Review started"}


async def _collect_output() -> None:
    global _review_process, _review_output
    if _review_process is None:
        return
    loop = asyncio.get_event_loop()
    while True:
        line = await loop.run_in_executor(None, _review_process.stdout.readline)
        if not line:
            break
        _review_output.append(line.rstrip())
    _review_process.wait()


async def _sse_generator() -> AsyncIterator[str]:
    """Yield SSE events from the running review process output."""
    sent = 0
    while True:
        while sent < len(_review_output):
            line = _review_output[sent]
            yield f"data: {json.dumps(line)}\n\n"
            sent += 1
        if _review_process is None or _review_process.poll() is not None:
            yield "data: {\"done\": true}\n\n"
            break
        await asyncio.sleep(0.25)


@app.get("/api/review/stream")
async def review_stream():
    """SSE endpoint — streams live output lines from the running review."""
    return StreamingResponse(
        _sse_generator(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )
