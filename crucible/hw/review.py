"""
crucible.hw.review — shared Finding data model for schematic review agents and GUI.

Agents write findings as JSON; the GUI reads them. This module is the contract
between those two layers — no domain knowledge, no project-specific logic.
"""

from __future__ import annotations

import json
from dataclasses import asdict, dataclass, field
from pathlib import Path


@dataclass
class Finding:
    id: str                                  # e.g. "CHK1-R1", "LAYOUT-2-J2"
    source: str                              # "correctness" | "layout" | "verifier"
    check: str                               # human-readable check name
    ref: str                                 # component reference, e.g. "R3"
    status: str                              # "PASS" | "WARN" | "FAIL" | "MATCH" | "MISMATCH" | "MISSING"
    finding: str                             # one-line description of what was found
    rule_basis: str                          # datasheet section, spec reference, or convention
    fix: str | None = None                   # one-line concrete fix for FAIL/WARN
    coords: tuple[float, float] | None = None  # schematic (x, y) in mm for GUI marker
    engineer_action: str | None = None       # "resolved" | "escalated" | "noted"
    note: str | None = None                  # engineer annotation
    gen_patch: str | None = None             # Phase 2: gen_schematic.py delta (future)


def load_findings(path: str | Path) -> list[Finding]:
    """Load findings from a JSON file. Returns empty list if file absent."""
    p = Path(path)
    if not p.exists():
        return []
    raw = json.loads(p.read_text())
    result = []
    for item in raw:
        coords = item.get("coords")
        result.append(Finding(
            id=item["id"],
            source=item["source"],
            check=item["check"],
            ref=item["ref"],
            status=item["status"],
            finding=item["finding"],
            rule_basis=item["rule_basis"],
            fix=item.get("fix"),
            coords=tuple(coords) if coords else None,
            engineer_action=item.get("engineer_action"),
            note=item.get("note"),
            gen_patch=item.get("gen_patch"),
        ))
    return result


def save_findings(path: str | Path, findings: list[Finding]) -> None:
    """Write findings to a JSON file, creating parent dirs as needed."""
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    data = []
    for f in findings:
        d = asdict(f)
        if d["coords"] is not None:
            d["coords"] = list(d["coords"])
        data.append(d)
    p.write_text(json.dumps(data, indent=2))


def merge_findings(*paths: str | Path) -> list[Finding]:
    """Load and merge findings from multiple JSON files, deduplicating by id."""
    seen: dict[str, Finding] = {}
    for path in paths:
        for f in load_findings(path):
            seen[f.id] = f
    return list(seen.values())


def findings_to_bill_stubs(findings: list[Finding]) -> list[dict]:
    """
    Return a list of Bill stub dicts for every FAIL/MISMATCH/MISSING finding.
    Each stub has: title, evidence, proposed_change, rule_basis.
    These are drafts — the engineer confirms before bill-drafter polishes them.
    """
    stubs = []
    for f in findings:
        if f.status not in ("FAIL", "MISMATCH", "MISSING"):
            continue
        stubs.append({
            "title": f"Fix {f.check} — {f.ref}",
            "evidence": f.finding,
            "proposed_change": f.fix or "(fix not yet specified — review manually)",
            "rule_basis": f.rule_basis,
            "finding_id": f.id,
            "source_agent": f.source,
        })
    return stubs
