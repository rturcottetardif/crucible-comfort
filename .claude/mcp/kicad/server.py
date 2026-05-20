#!/usr/bin/env python3
"""
MCP server — KiCad schematic and PCB reader.

Provides read access to KiCad .kicad_sch and .kicad_pcb files via the Crucible
hw-advisor and other agents. Export and validation operations delegate to kicad-cli
(KiCad 7.0+) and degrade gracefully when it is absent.

This server is read-only. Schematic edits require a Bill (Article II — any action
whose consequence cannot be fully reversed by a single git revert requires human
approval). The human uses the KiCad GUI for edits; this server reads the results.

Transport: stdio (JSON-RPC 2.0)
Protocol:  Model Context Protocol (MCP) 1.0

Usage (Claude Code):
  Register in .mcp.json at project root (see README.md in this directory).
"""

import json
import os
import sys
from pathlib import Path

# Locate project root (3 levels up: .claude/mcp/kicad/ → project root)
_SERVER_DIR  = Path(__file__).resolve().parent
_PROJECT_ROOT = _SERVER_DIR.parent.parent.parent
sys.path.insert(0, str(_PROJECT_ROOT))

from crucible.hw import kicad


# ── MCP wire protocol helpers ─────────────────────────────────────────────────

def send(obj: dict) -> None:
    sys.stdout.write(json.dumps(obj) + "\n")
    sys.stdout.flush()


def respond(id, result) -> None:
    send({"jsonrpc": "2.0", "id": id, "result": result})


def error(id, code: int, message: str) -> None:
    send({"jsonrpc": "2.0", "id": id, "error": {"code": code, "message": message}})


def text_result(text: str) -> dict:
    return {"content": [{"type": "text", "text": text}]}


# ── Tool definitions ──────────────────────────────────────────────────────────

TOOLS = [
    {
        "name": "kicad_cli_status",
        "description": (
            "Report whether kicad-cli is available and which features are enabled. "
            "Call this first when the user asks about KiCad export, ERC, or DRC. "
            "BOM, netlist, power rail, and component lookup work without kicad-cli."
        ),
        "inputSchema": {"type": "object", "properties": {}, "required": []},
    },
    {
        "name": "list_kicad_files",
        "description": (
            "Discover all KiCad project files (.kicad_sch, .kicad_pcb, .kicad_pro) "
            "under the project directory. Call this first to confirm schematic or PCB "
            "files exist before calling read_bom or read_netlist."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "project_dir": {
                    "type": "string",
                    "description": (
                        "Directory to search recursively. "
                        "Defaults to the crucible-comfort project root."
                    ),
                }
            },
            "required": [],
        },
    },
    {
        "name": "read_bom",
        "description": (
            "Parse the Bill of Materials from a KiCad schematic (.kicad_sch). "
            "Returns each component's Ref, Value, Footprint, Part Number, and Description. "
            "hw-advisor uses this as authoritative BOM evidence — overrides Markdown BOM "
            "when both are present."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sch_path": {
                    "type": "string",
                    "description": "Path to .kicad_sch file (absolute or relative to project root).",
                }
            },
            "required": ["sch_path"],
        },
    },
    {
        "name": "read_netlist",
        "description": (
            "Return full net connectivity from a KiCad schematic. "
            "Shows which component pins connect to which nets. "
            "Use for signal path tracing (e.g., IMU_SDA, +3V3 rail)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sch_path": {
                    "type": "string",
                    "description": "Path to .kicad_sch file.",
                }
            },
            "required": ["sch_path"],
        },
    },
    {
        "name": "read_power_rails",
        "description": (
            "Return all power rails in the schematic and the components on each. "
            "Use for power budget review and brownout risk analysis."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sch_path": {
                    "type": "string",
                    "description": "Path to .kicad_sch file.",
                }
            },
            "required": ["sch_path"],
        },
    },
    {
        "name": "find_component",
        "description": (
            "Look up a single component by reference designator (e.g. 'U1', 'R3'). "
            "Returns all properties for that component. Case-insensitive."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sch_path": {
                    "type": "string",
                    "description": "Path to .kicad_sch file.",
                },
                "ref": {
                    "type": "string",
                    "description": "Reference designator, e.g. 'U1' or 'r3'.",
                },
            },
            "required": ["sch_path", "ref"],
        },
    },
    {
        "name": "export_schematic",
        "description": (
            "Export schematic as SVG or PDF using kicad-cli (KiCad 7.0+ required). "
            "Returns the output file path. Requires 'brew install --cask kicad' (10.0+). "
            "Returns an informative message if kicad-cli is not found — "
            "parsing tools (BOM, netlist, etc.) still work without it."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sch_path": {
                    "type": "string",
                    "description": "Path to .kicad_sch file.",
                },
                "out_dir": {
                    "type": "string",
                    "description": "Output directory for the generated file.",
                },
                "format": {
                    "type": "string",
                    "description": "svg or pdf (default: svg).",
                },
            },
            "required": ["sch_path", "out_dir"],
        },
    },
    {
        "name": "run_erc",
        "description": (
            "Run Electrical Rules Check on a schematic via kicad-cli. "
            "Returns violations as structured text. "
            "Requires kicad-cli (KiCad 7.0+)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "sch_path": {
                    "type": "string",
                    "description": "Path to .kicad_sch file.",
                }
            },
            "required": ["sch_path"],
        },
    },
    {
        "name": "export_pcb_image",
        "description": (
            "Export PCB copper/silkscreen view as SVG using kicad-cli. "
            "Requires kicad-cli (KiCad 7.0+). Default layers: F.Cu, B.Cu, F.SilkS, B.SilkS, Edge.Cuts."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pcb_path": {
                    "type": "string",
                    "description": "Path to .kicad_pcb file.",
                },
                "out_dir": {
                    "type": "string",
                    "description": "Output directory.",
                },
                "layers": {
                    "type": "string",
                    "description": (
                        "Comma-separated layer names. "
                        "Default: F.Cu,B.Cu,F.SilkS,B.SilkS,Edge.Cuts"
                    ),
                },
            },
            "required": ["pcb_path", "out_dir"],
        },
    },
    {
        "name": "run_drc",
        "description": (
            "Run Design Rules Check on a PCB file via kicad-cli. "
            "Returns violations as structured text. "
            "Requires kicad-cli (KiCad 7.0+)."
        ),
        "inputSchema": {
            "type": "object",
            "properties": {
                "pcb_path": {
                    "type": "string",
                    "description": "Path to .kicad_pcb file.",
                }
            },
            "required": ["pcb_path"],
        },
    },
]


# ── Tool implementations ──────────────────────────────────────────────────────

def _resolve(path: str) -> str:
    """Resolve a path relative to project root if not absolute."""
    p = Path(path)
    if not p.is_absolute():
        p = _PROJECT_ROOT / p
    return str(p)


def tool_kicad_cli_status() -> str:
    cli = kicad.detect_kicad_cli()
    if cli:
        try:
            import subprocess
            result = subprocess.run([cli, "--version"], capture_output=True, text=True, check=False)
            version = result.stdout.strip() or result.stderr.strip()
        except Exception:
            version = "unknown"
        lines = [
            f"kicad-cli: FOUND",
            f"Path:      {cli}",
            f"Version:   {version}",
            "",
            "All 10 tools available:",
            "  Read-only (no kicad-cli): kicad_cli_status, list_kicad_files, read_bom,",
            "                            read_netlist, read_power_rails, find_component",
            "  CLI-dependent:            export_schematic, run_erc, export_pcb_image, run_drc",
        ]
    else:
        lines = [
            "kicad-cli: NOT FOUND",
            "",
            "kicad-cli was introduced in KiCad 7.0.",
            "The installed KiCad 6.x on this machine does not include it.",
            "",
            "To enable export, ERC, and DRC:",
            "  brew install --cask kicad   (installs KiCad 10.0.2 with kicad-cli)",
            "  or set KICAD_CLI=/path/to/kicad-cli",
            "",
            "Available without kicad-cli (working now):",
            "  kicad_cli_status, list_kicad_files, read_bom,",
            "  read_netlist, read_power_rails, find_component",
            "",
            "Unavailable until upgrade:",
            "  export_schematic, run_erc, export_pcb_image, run_drc",
        ]
    return "\n".join(lines)


def tool_list_kicad_files(args: dict) -> str:
    project_dir = args.get("project_dir") or str(_PROJECT_ROOT)
    project_dir = _resolve(project_dir)
    files = kicad.list_project_files(project_dir)
    if not any(files.values()):
        return (
            f"No KiCad files found under: {project_dir}\n\n"
            "Place .kicad_sch or .kicad_pcb files in the hardware/ directory "
            "(e.g. hardware/comfortsense.kicad_sch) and re-run this tool."
        )
    lines = [f"KiCad files found under: {project_dir}", ""]
    for category, paths in files.items():
        lines.append(f"### {category.upper()} ({len(paths)})")
        if paths:
            for p in paths:
                lines.append(f"  {p}")
        else:
            lines.append("  (none)")
        lines.append("")
    return "\n".join(lines)


def tool_read_bom(args: dict) -> str:
    sch_path = _resolve(args["sch_path"])
    try:
        components = kicad.read_bom(sch_path)
    except kicad.KiCadFileError as exc:
        return f"ERROR: {exc}"

    if not components:
        return f"No components found in {sch_path}\n(All symbols may be power symbols or excluded from BOM.)"

    lines = [
        f"BOM — {Path(sch_path).name}",
        f"Source: KiCad schematic (authoritative — overrides Markdown BOM if present)",
        f"Components: {len(components)}",
        "",
        f"{'Ref':<8} {'Value':<24} {'Footprint':<40} {'Part Number':<20} Description",
        "-" * 110,
    ]
    for comp in components:
        fp_short = comp.footprint.split(":")[-1] if ":" in comp.footprint else comp.footprint
        lines.append(
            f"{comp.ref:<8} {comp.value:<24} {fp_short:<40} {comp.part_number:<20} {comp.description}"
        )

    if any(comp.properties for comp in components):
        lines += ["", "--- Extended properties ---"]
        for comp in components:
            if comp.properties:
                lines.append(f"\n{comp.ref}:")
                for k, v in comp.properties.items():
                    lines.append(f"  {k}: {v}")

    return "\n".join(lines)


def tool_read_netlist(args: dict) -> str:
    sch_path = _resolve(args["sch_path"])
    try:
        nets = kicad.read_netlist(sch_path)
    except kicad.KiCadFileError as exc:
        return f"ERROR: {exc}"

    named = [n for n in nets if not n.name.startswith("_unconnected_")]
    unconnected = [n for n in nets if n.name.startswith("_unconnected_")]

    lines = [
        f"Netlist — {Path(sch_path).name}",
        f"Named nets: {len(named)}   Unconnected pins: {len(unconnected)}",
        "",
    ]
    for net in named:
        pin_list = ", ".join(f"{p.ref}.{p.pin_number}({p.pin_name})" for p in net.pins)
        lines.append(f"  {net.name:<20} {pin_list}")

    if unconnected:
        lines += ["", f"Unconnected pins ({len(unconnected)}):"]
        for net in unconnected:
            for p in net.pins:
                lines.append(f"  {p.ref}.{p.pin_number} ({p.pin_name})")

    return "\n".join(lines)


def tool_read_power_rails(args: dict) -> str:
    sch_path = _resolve(args["sch_path"])
    try:
        rails = kicad.read_power_rails(sch_path)
    except kicad.KiCadFileError as exc:
        return f"ERROR: {exc}"

    if not rails:
        return f"No power rails detected in {Path(sch_path).name}."

    lines = [
        f"Power rails — {Path(sch_path).name}",
        f"Rails: {len(rails)}",
        "",
    ]
    for rail in rails:
        comps = ", ".join(rail.components) if rail.components else "(no non-power components)"
        lines.append(f"  {rail.name:<16} {comps}")

    return "\n".join(lines)


def tool_find_component(args: dict) -> str:
    sch_path = _resolve(args["sch_path"])
    ref = args["ref"]
    try:
        comp = kicad.find_component(sch_path, ref)
    except kicad.KiCadFileError as exc:
        return f"ERROR: {exc}"

    if comp is None:
        return f"Component '{ref}' not found in {Path(sch_path).name}."

    lines = [
        f"Component: {comp.ref}",
        f"  Value:       {comp.value}",
        f"  Footprint:   {comp.footprint}",
        f"  Part Number: {comp.part_number or '(not set)'}",
        f"  Description: {comp.description or '(not set)'}",
    ]
    if comp.properties:
        lines.append("  Properties:")
        for k, v in comp.properties.items():
            lines.append(f"    {k}: {v}")

    return "\n".join(lines)


def tool_export_schematic(args: dict) -> str:
    sch_path = _resolve(args["sch_path"])
    out_dir  = _resolve(args["out_dir"])
    fmt      = args.get("format", "svg").lower()
    try:
        if fmt == "pdf":
            out_file = kicad.export_pdf(sch_path, out_dir)
        else:
            out_file = kicad.export_svg(sch_path, out_dir)
        return f"Exported: {out_file}"
    except kicad.KiCadCliNotFoundError as exc:
        return str(exc)
    except RuntimeError as exc:
        return f"Export failed: {exc}"


def tool_run_erc(args: dict) -> str:
    sch_path = _resolve(args["sch_path"])
    try:
        result = kicad.run_erc(sch_path)
    except kicad.KiCadCliNotFoundError as exc:
        return str(exc)

    lines = [
        f"ERC — {Path(sch_path).name}",
        f"Errors: {result.error_count}   Warnings: {result.warning_count}",
        "",
    ]
    if result.violations:
        for v in result.violations:
            lines.append(f"  [{v['type'].upper()}] {v['description']}")
            if v.get("location"):
                lines.append(f"    at {v['location']}")
    else:
        lines.append("No violations found.")

    return "\n".join(lines)


def tool_export_pcb_image(args: dict) -> str:
    pcb_path = _resolve(args["pcb_path"])
    out_dir  = _resolve(args["out_dir"])
    layers_str = args.get("layers", "")
    layers = [l.strip() for l in layers_str.split(",") if l.strip()] if layers_str else None
    try:
        out_file = kicad.export_pcb_image(pcb_path, out_dir, layers)
        return f"Exported: {out_file}"
    except kicad.KiCadCliNotFoundError as exc:
        return str(exc)
    except RuntimeError as exc:
        return f"Export failed: {exc}"


def tool_run_drc(args: dict) -> str:
    pcb_path = _resolve(args["pcb_path"])
    try:
        result = kicad.run_drc(pcb_path)
    except kicad.KiCadCliNotFoundError as exc:
        return str(exc)

    lines = [
        f"DRC — {Path(pcb_path).name}",
        f"Errors: {result.error_count}   Warnings: {result.warning_count}",
        "",
    ]
    if result.violations:
        for v in result.violations:
            lines.append(f"  [{v['type'].upper()}] {v['description']}")
            if v.get("location"):
                lines.append(f"    at {v['location']}")
    else:
        lines.append("No violations found.")

    return "\n".join(lines)


# ── Request dispatcher ────────────────────────────────────────────────────────

def dispatch(method: str, params: dict, id) -> None:
    if method == "initialize":
        respond(id, {
            "protocolVersion": "2024-11-05",
            "capabilities": {"tools": {}},
            "serverInfo": {"name": "kicad", "version": "1.0.0"},
        })

    elif method == "tools/list":
        respond(id, {"tools": TOOLS})

    elif method == "tools/call":
        name = params.get("name", "")
        args = params.get("arguments", {})
        try:
            if name == "kicad_cli_status":
                text = tool_kicad_cli_status()
            elif name == "list_kicad_files":
                text = tool_list_kicad_files(args)
            elif name == "read_bom":
                text = tool_read_bom(args)
            elif name == "read_netlist":
                text = tool_read_netlist(args)
            elif name == "read_power_rails":
                text = tool_read_power_rails(args)
            elif name == "find_component":
                text = tool_find_component(args)
            elif name == "export_schematic":
                text = tool_export_schematic(args)
            elif name == "run_erc":
                text = tool_run_erc(args)
            elif name == "export_pcb_image":
                text = tool_export_pcb_image(args)
            elif name == "run_drc":
                text = tool_run_drc(args)
            else:
                error(id, -32601, f"Unknown tool: {name}")
                return
            respond(id, text_result(text))
        except Exception as exc:
            respond(id, text_result(f"Internal error in {name}: {exc}"))

    elif method.startswith("notifications/"):
        pass  # notifications require no response

    else:
        error(id, -32601, f"Method not found: {method}")


# ── Main loop ─────────────────────────────────────────────────────────────────

def main() -> None:
    for line in sys.stdin:
        line = line.strip()
        if not line:
            continue
        try:
            msg = json.loads(line)
        except json.JSONDecodeError as exc:
            send({"jsonrpc": "2.0", "id": None, "error": {"code": -32700, "message": f"Parse error: {exc}"}})
            continue

        method = msg.get("method", "")
        params = msg.get("params", {})
        msg_id = msg.get("id")

        if msg_id is None and not method.startswith("notifications/"):
            continue  # notification with no id — ignore silently

        dispatch(method, params, msg_id)


if __name__ == "__main__":
    main()
