"""
crucible.hw.kicad — KiCad schematic and PCB file reader + kicad-cli bridge.

Parses .kicad_sch and .kicad_pcb files using the KiCad S-expression format.
Optionally delegates export and validation to kicad-cli (KiCad 7.0+).

No domain knowledge. No knowledge of ComfortSense, filter ΔP, HVAC, or any
project-specific signal. Project-specific net→signal mapping lives in src/.

Public API
----------
  detect_kicad_cli()                  -> str | None
  list_project_files(project_dir)     -> dict[str, list[str]]
  read_bom(sch_path)                  -> list[Component]
  read_netlist(sch_path)              -> list[Net]
  read_power_rails(sch_path)          -> list[PowerRail]
  find_component(sch_path, ref)       -> Component | None
  export_svg(sch_path, out_dir)       -> str
  export_pdf(sch_path, out_dir)       -> str
  run_erc(sch_path)                   -> ErcResult
  export_pcb_image(pcb_path, out_dir) -> str
  run_drc(pcb_path)                   -> DrcResult

Internal (not exposed as MCP tools — Article II: schematic edits need a Bill)
  update_component_property(sch_path, ref, key, value) -> None
"""
from __future__ import annotations

import json
import os
import re
import shutil
import subprocess
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from crucible.hw import sexpr


# ── Data models ───────────────────────────────────────────────────────────────

@dataclass
class Component:
    ref: str
    value: str
    footprint: str
    part_number: str           # from "Part Number" or "MPN" property; "" if absent
    description: str           # from "Description" property; "" if absent
    properties: dict[str, str] = field(default_factory=dict)


@dataclass
class PinConnection:
    ref: str
    pin_number: str
    pin_name: str


@dataclass
class Net:
    name: str
    pins: list[PinConnection] = field(default_factory=list)


@dataclass
class PowerRail:
    name: str
    components: list[str] = field(default_factory=list)


@dataclass
class ErcResult:
    violations: list[dict[str, str]]
    error_count: int
    warning_count: int
    raw_output: str


@dataclass
class DrcResult:
    violations: list[dict[str, str]]
    error_count: int
    warning_count: int
    raw_output: str


class KiCadCliNotFoundError(RuntimeError):
    """kicad-cli is required but not found.

    kicad-cli was introduced in KiCad 7.0. The macOS app bundle at
    /Applications/KiCad/KiCad.app ships kicad-cli from version 7 onward.

    To install/upgrade: brew install --cask kicad
    """


class KiCadFileError(ValueError):
    """Raised when a .kicad_sch or .kicad_pcb file cannot be parsed."""


# ── kicad-cli detection ───────────────────────────────────────────────────────

_KICAD_CLI_CANDIDATES = [
    "",  # placeholder for env var check
    "kicad-cli",  # PATH
    "/Applications/KiCad/KiCad.app/Contents/MacOS/kicad-cli",  # macOS KiCad 7+
    "/Applications/KiCad.app/Contents/MacOS/kicad-cli",         # alternate macOS layout
    "/usr/bin/kicad-cli",
    "/usr/local/bin/kicad-cli",
    "/opt/homebrew/bin/kicad-cli",
]


def detect_kicad_cli() -> str | None:
    """Return path to kicad-cli binary, or None if not found.

    KiCad 6.x does not ship kicad-cli (introduced in 7.0).
    macOS: brew install --cask kicad installs 10.0.2 which includes kicad-cli.
    """
    env_override = os.environ.get("KICAD_CLI", "")
    candidates = [env_override] + _KICAD_CLI_CANDIDATES[1:] if env_override else _KICAD_CLI_CANDIDATES[1:]

    for candidate in candidates:
        if not candidate:
            continue
        if candidate == "kicad-cli":
            found = shutil.which("kicad-cli")
            if found:
                return found
        elif Path(candidate).is_file():
            return candidate
    return None


def _require_cli() -> str:
    cli = detect_kicad_cli()
    if cli is None:
        raise KiCadCliNotFoundError(
            "kicad-cli not found. kicad-cli was introduced in KiCad 7.0.\n"
            "The installed KiCad 6.x does not include it.\n"
            "Upgrade: brew install --cask kicad  (installs KiCad 10.0.2 with kicad-cli)\n"
            "Alternatively set the KICAD_CLI environment variable to the binary path."
        )
    return cli


# ── File discovery ─────────────────────────────────────────────────────────────

def list_project_files(project_dir: str = ".") -> dict[str, list[str]]:
    """Discover KiCad project files under project_dir (recursive)."""
    root = Path(project_dir)
    return {
        "schematics": sorted(str(p) for p in root.rglob("*.kicad_sch")),
        "pcb":        sorted(str(p) for p in root.rglob("*.kicad_pcb")),
        "project":    sorted(str(p) for p in root.rglob("*.kicad_pro")),
    }


# ── Reference sort key ────────────────────────────────────────────────────────

def _ref_sort_key(ref: str) -> tuple[str, int, str]:
    """Sort R1 < R2 < R10 < U1 < U2 (prefix alphabetical, number numeric)."""
    m = re.match(r"^([A-Za-z_#]+)(\d+)(.*)$", ref)
    if m:
        return m.group(1).upper(), int(m.group(2)), m.group(3)
    return ref.upper(), 0, ""


# ── BOM extraction ────────────────────────────────────────────────────────────

def _extract_properties(sym_node: list) -> dict[str, str]:
    """Extract all property key→value pairs from a symbol node."""
    props: dict[str, str] = {}
    for child in sym_node:
        if isinstance(child, list) and child and child[0] == "property":
            if len(child) >= 3 and isinstance(child[1], str) and isinstance(child[2], str):
                props[child[1]] = child[2]
    return props


def read_bom(sch_path: str) -> list[Component]:
    """Parse all components from a .kicad_sch file.

    Excludes power symbols (ref starts with '#') and symbols with
    property "Exclude from BOM" == "1".
    Returns list sorted by reference designator.
    """
    try:
        tree = sexpr.load(sch_path)
    except Exception as exc:
        raise KiCadFileError(f"Cannot parse {sch_path}: {exc}") from exc

    components: list[Component] = []
    for sym in sexpr.find_all(tree, "symbol"):
        props = _extract_properties(sym)
        ref = props.get("Reference", "")
        if not ref or ref.startswith("#"):
            continue
        if props.get("Exclude from BOM", "0") == "1":
            continue

        part_number = props.get("Part Number", props.get("MPN", ""))
        description = props.get("Description", "")
        remaining = {k: v for k, v in props.items()
                     if k not in {"Reference", "Value", "Footprint",
                                  "Part Number", "MPN", "Description",
                                  "Datasheet", "ki_keywords", "ki_description",
                                  "ki_fp_filters"}}
        components.append(Component(
            ref=ref,
            value=props.get("Value", ""),
            footprint=props.get("Footprint", ""),
            part_number=part_number,
            description=description,
            properties=remaining,
        ))

    # Deduplicate by ref (KiCad schematics can have multiple symbol instances
    # for the same reference in multi-unit components)
    seen: dict[str, Component] = {}
    for comp in components:
        if comp.ref not in seen:
            seen[comp.ref] = comp

    return sorted(seen.values(), key=lambda c: _ref_sort_key(c.ref))


# ── Netlist extraction ────────────────────────────────────────────────────────
#
# KiCad schematic connectivity is encoded as wire segments + net labels.
# We use a union-find structure to group wire endpoints into connected sets,
# then name each set from net_label / global_label nodes whose positions fall
# on a wire endpoint or junction.
#
# Coordinate precision: KiCad uses floating-point mils. We round to 2 decimal
# places to avoid floating-point equality failures.

def _coord(node: list, keys: tuple[str, ...] = ("at",)) -> tuple[float, float] | None:
    """Extract (x, y) from an 'at' sub-expression, or None."""
    for key in keys:
        at = sexpr.find_first(node, key)
        if at and len(at) >= 3:
            try:
                return round(float(at[1]), 2), round(float(at[2]), 2)
            except (ValueError, TypeError):
                pass
    return None


class _UnionFind:
    def __init__(self) -> None:
        self._parent: dict[Any, Any] = {}

    def find(self, x: Any) -> Any:
        if x not in self._parent:
            self._parent[x] = x
        if self._parent[x] != x:
            self._parent[x] = self.find(self._parent[x])
        return self._parent[x]

    def union(self, a: Any, b: Any) -> None:
        ra, rb = self.find(a), self.find(b)
        if ra != rb:
            self._parent[rb] = ra

    def groups(self) -> dict[Any, list[Any]]:
        result: dict[Any, list[Any]] = {}
        for x in self._parent:
            r = self.find(x)
            result.setdefault(r, []).append(x)
        return result


def read_netlist(sch_path: str) -> list[Net]:
    """Extract net connectivity from a .kicad_sch file.

    Reconstructs nets by grouping wire segments (union-find), assigning
    net names from net_label / global_label, and matching symbol pin
    positions to wire groups.
    """
    try:
        tree = sexpr.load(sch_path)
    except Exception as exc:
        raise KiCadFileError(f"Cannot parse {sch_path}: {exc}") from exc

    uf = _UnionFind()

    # 1. Collect wire segment endpoints and union them
    for wire in sexpr.find_all(tree, "wire"):
        pts_node = sexpr.find_first(wire, "pts")
        if not pts_node:
            continue
        xys = sexpr.find_all(pts_node, "xy")
        coords = []
        for xy in xys:
            if len(xy) >= 3:
                try:
                    coords.append((round(float(xy[1]), 2), round(float(xy[2]), 2)))
                except (ValueError, TypeError):
                    pass
        for i in range(len(coords) - 1):
            uf.union(coords[i], coords[i + 1])

    # 2. Collect junctions (explicit connection points)
    for junc in sexpr.find_all(tree, "junction"):
        coord = _coord(junc)
        if coord:
            uf.find(coord)  # ensure it's registered

    # 3. Assign net names from net_label and global_label
    coord_to_name: dict[Any, str] = {}
    for label_key in ("net_label", "global_label", "hierarchical_label"):
        for label in sexpr.find_all(tree, label_key):
            coord = _coord(label)
            name = label[1] if len(label) >= 2 and isinstance(label[1], str) else None
            if coord and name:
                coord_to_name[uf.find(coord)] = name

    # 4. Map symbol pins to their net groups
    # Pin positions require transforming by the parent symbol's 'at' position.
    # For simplicity we match on absolute coordinates (works for un-mirrored symbols).
    pin_to_net: dict[tuple[float, float], str] = {}
    for root_key, net_name in coord_to_name.items():
        for coord, root in list(uf._parent.items()):
            if uf.find(coord) == root_key:
                pin_to_net[coord] = net_name

    # 5. Collect symbol instances and their pin positions
    net_pins: dict[str, list[PinConnection]] = {}

    for sym in sexpr.find_all(tree, "symbol"):
        props = _extract_properties(sym)
        ref = props.get("Reference", "")
        if not ref or ref.startswith("#"):
            continue

        sym_at = _coord(sym)
        if not sym_at:
            continue
        sx, sy = sym_at

        lib_id_node = sexpr.find_first(sym, "lib_id")
        lib_id = lib_id_node[1] if lib_id_node and len(lib_id_node) >= 2 else ""

        # Find pin sub-expressions within this symbol instance
        for pin in sexpr.find_all(sym, "pin"):
            pin_num_node = sexpr.find_first(pin, "number")
            pin_name_node = sexpr.find_first(pin, "name")
            pin_at = _coord(pin)
            if pin_at is None or pin_num_node is None:
                continue

            pin_num = pin_num_node[1] if len(pin_num_node) >= 2 else ""
            pin_name_str = pin_name_node[1] if pin_name_node and len(pin_name_node) >= 2 else ""

            # Absolute pin position (symbol origin + pin offset)
            px = round(sx + pin_at[0], 2)
            py = round(sy + pin_at[1], 2)
            abs_coord = (px, py)

            net_name = pin_to_net.get(abs_coord) or pin_to_net.get(uf.find(abs_coord) if abs_coord in uf._parent else abs_coord)
            if net_name is None:
                net_name = f"_unconnected_{ref}_{pin_num}"

            net_pins.setdefault(net_name, []).append(
                PinConnection(ref=ref, pin_number=str(pin_num), pin_name=pin_name_str)
            )

    nets = [Net(name=name, pins=pins) for name, pins in net_pins.items()]
    return sorted(nets, key=lambda n: n.name)


# ── Power rail extraction ─────────────────────────────────────────────────────

_POWER_PREFIXES = ("+", "VCC", "VDD", "VBAT", "VMCU", "VREF", "AVCC", "AVDD")
_GROUND_NAMES   = {"GND", "GNDA", "AGND", "DGND", "PGND", "EARTH", "0V"}


def _is_power_rail(name: str) -> bool:
    uname = name.upper()
    if uname in _GROUND_NAMES:
        return True
    for prefix in _POWER_PREFIXES:
        if uname.startswith(prefix):
            return True
    return False


def read_power_rails(sch_path: str) -> list[PowerRail]:
    """Return all power rails and the component refs on each.

    A net is a power rail if its name starts with '+', 'VCC', 'VDD', etc.,
    or if it is a standard ground name, or if it has a power symbol (#PWR*).
    """
    try:
        tree = sexpr.load(sch_path)
    except Exception as exc:
        raise KiCadFileError(f"Cannot parse {sch_path}: {exc}") from exc

    # Power symbols declare rails via their "Value" property
    power_nets: set[str] = set()
    for sym in sexpr.find_all(tree, "symbol"):
        props = _extract_properties(sym)
        ref = props.get("Reference", "")
        if ref.startswith("#PWR") or ref.startswith("#FLG"):
            net_name = props.get("Value", "")
            if net_name:
                power_nets.add(net_name)

    # Also catch nets whose names follow power naming conventions
    for label_key in ("net_label", "global_label"):
        for label in sexpr.find_all(tree, label_key):
            name = label[1] if len(label) >= 2 and isinstance(label[1], str) else ""
            if name and _is_power_rail(name):
                power_nets.add(name)

    if not power_nets:
        return []

    # Build set from BOM to map component refs onto rails via netlist
    bom = {comp.ref: comp for comp in read_bom(sch_path)}
    nets = read_netlist(sch_path)

    rails: dict[str, list[str]] = {name: [] for name in power_nets}
    for net in nets:
        if net.name in power_nets:
            for pin in net.pins:
                if pin.ref in bom and pin.ref not in rails[net.name]:
                    rails[net.name].append(pin.ref)

    return sorted(
        [PowerRail(name=name, components=sorted(refs)) for name, refs in rails.items()],
        key=lambda r: r.name,
    )


# ── Component lookup ──────────────────────────────────────────────────────────

def find_component(sch_path: str, ref: str) -> Component | None:
    """Look up a component by reference designator (case-insensitive).

    Returns None if not found.
    """
    target = ref.upper().strip()
    for comp in read_bom(sch_path):
        if comp.ref.upper() == target:
            return comp
    return None


# ── kicad-cli export and validation ──────────────────────────────────────────

def export_svg(sch_path: str, out_dir: str) -> str:
    """Export schematic as SVG using kicad-cli.

    Requires kicad-cli (KiCad 7.0+). Raises KiCadCliNotFoundError if absent.
    Returns absolute path to generated SVG file.
    """
    cli = _require_cli()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [cli, "sch", "export", "svg", "--output", str(out), str(sch_path)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"kicad-cli sch export svg failed:\n{result.stderr}")
    stem = Path(sch_path).stem
    svg = out / f"{stem}.svg"
    return str(svg)


def export_pdf(sch_path: str, out_dir: str) -> str:
    """Export schematic as PDF using kicad-cli.

    Requires kicad-cli (KiCad 7.0+). Raises KiCadCliNotFoundError if absent.
    Returns absolute path to generated PDF file.
    """
    cli = _require_cli()
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    result = subprocess.run(
        [cli, "sch", "export", "pdf", "--output", str(out / f"{Path(sch_path).stem}.pdf"), str(sch_path)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"kicad-cli sch export pdf failed:\n{result.stderr}")
    return str(out / f"{Path(sch_path).stem}.pdf")


def run_erc(sch_path: str) -> ErcResult:
    """Run Electrical Rules Check via kicad-cli.

    Requires kicad-cli (KiCad 7.0+). Raises KiCadCliNotFoundError if absent.
    """
    cli = _require_cli()
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out_file = f.name
    try:
        result = subprocess.run(
            [cli, "sch", "erc", "--format", "json", "--output", out_file, str(sch_path)],
            capture_output=True, text=True, check=False,
        )
        raw = result.stdout + result.stderr
        try:
            data = json.loads(Path(out_file).read_text())
        except Exception:
            data = {}

        violations = []
        errors = warnings = 0
        for sheet in data.get("sheets", []):
            for v in sheet.get("violations", []):
                severity = v.get("severity", "error")
                violations.append({
                    "type": severity,
                    "description": v.get("description", ""),
                    "location": str(v.get("items", [{}])[0].get("pos", "")),
                })
                if severity == "error":
                    errors += 1
                else:
                    warnings += 1

        return ErcResult(
            violations=violations,
            error_count=errors,
            warning_count=warnings,
            raw_output=raw,
        )
    finally:
        Path(out_file).unlink(missing_ok=True)


def export_pcb_image(
    pcb_path: str,
    out_dir: str,
    layers: list[str] | None = None,
) -> str:
    """Export PCB copper/silkscreen view as SVG using kicad-cli.

    Default layers: F.Cu, B.Cu, F.SilkS, B.SilkS, Edge.Cuts
    Requires kicad-cli (KiCad 7.0+). Raises KiCadCliNotFoundError if absent.
    """
    cli = _require_cli()
    if layers is None:
        layers = ["F.Cu", "B.Cu", "F.SilkS", "B.SilkS", "Edge.Cuts"]
    out = Path(out_dir)
    out.mkdir(parents=True, exist_ok=True)
    out_file = out / f"{Path(pcb_path).stem}.svg"
    result = subprocess.run(
        [cli, "pcb", "export", "svg",
         "--layers", ",".join(layers),
         "--output", str(out_file),
         str(pcb_path)],
        capture_output=True, text=True, check=False,
    )
    if result.returncode != 0:
        raise RuntimeError(f"kicad-cli pcb export svg failed:\n{result.stderr}")
    return str(out_file)


def run_drc(pcb_path: str) -> DrcResult:
    """Run Design Rules Check via kicad-cli.

    Requires kicad-cli (KiCad 7.0+). Raises KiCadCliNotFoundError if absent.
    """
    cli = _require_cli()
    import tempfile
    with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
        out_file = f.name
    try:
        result = subprocess.run(
            [cli, "pcb", "drc", "--format", "json", "--output", out_file, str(pcb_path)],
            capture_output=True, text=True, check=False,
        )
        raw = result.stdout + result.stderr
        try:
            data = json.loads(Path(out_file).read_text())
        except Exception:
            data = {}

        violations = []
        errors = warnings = 0
        for v in data.get("violations", []):
            severity = v.get("severity", "error")
            violations.append({
                "type": severity,
                "description": v.get("description", ""),
                "location": str(v.get("items", [{}])[0].get("pos", "")),
            })
            if severity == "error":
                errors += 1
            else:
                warnings += 1

        return DrcResult(
            violations=violations,
            error_count=errors,
            warning_count=warnings,
            raw_output=raw,
        )
    finally:
        Path(out_file).unlink(missing_ok=True)


# ── Internal write path (not an MCP tool — Article II) ───────────────────────

def update_component_property(sch_path: str, ref: str, key: str, value: str) -> None:
    """Write a component property back to a .kicad_sch file.

    Creates a .bak backup before writing. Caller must commit the result.
    NOT exposed as an MCP tool — schematic edits require a Bill (Article II).
    """
    import shutil as _shutil
    path = Path(sch_path)
    backup = path.with_suffix(".kicad_sch.bak")
    _shutil.copy2(path, backup)

    try:
        tree = sexpr.load(sch_path)
    except Exception as exc:
        raise KiCadFileError(f"Cannot parse {sch_path}: {exc}") from exc

    target = ref.upper().strip()
    found = False
    for sym in sexpr.find_all(tree, "symbol"):
        props = _extract_properties(sym)
        if props.get("Reference", "").upper() == target:
            for child in sym:
                if isinstance(child, list) and child and child[0] == "property":
                    if len(child) >= 2 and child[1] == key:
                        if len(child) >= 3:
                            child[2] = value
                        found = True
            break

    if not found:
        raise ValueError(f"Component '{ref}' property '{key}' not found in {sch_path}")

    path.write_text(sexpr.dump(tree), encoding="utf-8")
