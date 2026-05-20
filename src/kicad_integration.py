"""
src.kicad_integration — ComfortSense-specific KiCad integration.

Bridges crucible.hw.kicad (infrastructure, domain-agnostic) to ComfortSense's
Signal Inventory and BOM governance record. Does not modify schematics.

Usage:
    from src.kicad_integration import check_signal_inventory, bom_vs_device_context
    from src.kicad_integration import SCHEMATIC_PATH, PCB_PATH

    report = check_signal_inventory(SCHEMATIC_PATH)
    diff   = bom_vs_device_context(SCHEMATIC_PATH)
"""
from __future__ import annotations

from pathlib import Path

from crucible.hw.kicad import (
    KiCadFileError,
    Net,
    read_bom,
    read_netlist,
)

# Default file paths — update when the actual schematic is committed.
SCHEMATIC_PATH = "hardware/comfortsense.kicad_sch"
PCB_PATH       = "hardware/comfortsense.kicad_pcb"

# Maps Signal Inventory names (Amendment 1, from docs/device_context.md)
# to the expected KiCad net names in the schematic.
#
# Maintained by the human engineer per schematic revision.
# IMU signals share one I2C bus (IMU_SDA / IMU_SCL) — they cannot be
# individually resolved to nets; the mapping records the bus net.
SIGNAL_TO_NET: dict[str, str] = {
    "imu_accel_x":    "SDA",
    "imu_accel_y":    "SDA",
    "imu_accel_z":    "SDA",
    "imu_gyro_x":     "SDA",
    "imu_gyro_y":     "SDA",
    "imu_gyro_z":     "SDA",
    "ct_current_rms": "ADC_CT",
    # DS18B20 OneWire — ONEWIRE net: J_DS18B20 pin 2 → P0.29. Rev 0.2 (Bill 6 / Case 9).
    "outside_temp":   "ONEWIRE",
    # On-board XIAO routing — no external net in ComfortSense PCB; correctly MISSING
    "microphone":     "PDM_DATA",
}


def check_signal_inventory(sch_path: str) -> str:
    """Cross-check Signal Inventory (Amendment 1) against actual schematic nets.

    Returns a Markdown-formatted report:
    - Signals with a matching net in the schematic (FOUND)
    - Signals with no matching net (MISSING from schematic)
    - Schematic nets with no Signal Inventory entry (UNDOCUMENTED)

    hw-advisor calls this during 'pins' and 'signal' focus reviews.
    """
    try:
        nets = read_netlist(sch_path)
    except KiCadFileError as exc:
        return f"Cannot read netlist from {sch_path}: {exc}"

    schematic_net_names = {n.name for n in nets if not n.name.startswith("_unconnected_")}
    expected_nets = set(SIGNAL_TO_NET.values())

    lines = [
        f"# Signal Inventory ↔ Schematic Cross-Check",
        f"Source: {sch_path}",
        "",
        "## Signal Inventory Coverage",
        "",
        f"{'Signal':<20} {'Expected Net':<20} Status",
        "-" * 55,
    ]

    missing_nets: list[str] = []
    for signal, net_name in sorted(SIGNAL_TO_NET.items()):
        if net_name in schematic_net_names:
            lines.append(f"{signal:<20} {net_name:<20} FOUND")
        else:
            lines.append(f"{signal:<20} {net_name:<20} MISSING")
            missing_nets.append(net_name)

    if missing_nets:
        unique_missing = sorted(set(missing_nets))
        lines += [
            "",
            "## Nets missing from schematic",
            "",
            "These nets are expected by the Signal Inventory but not found in the schematic.",
            "Either the net is named differently or the signal path is not yet drawn.",
            "",
        ]
        for net in unique_missing:
            signals = [s for s, n in SIGNAL_TO_NET.items() if n == net]
            lines.append(f"- `{net}` (required by: {', '.join(signals)})")

    # Nets in schematic that don't appear in SIGNAL_TO_NET
    undocumented = schematic_net_names - expected_nets
    # Filter out power rails and internal nets
    undocumented = {n for n in undocumented
                    if not n.startswith("+") and not n.startswith("#")
                    and n not in {"GND", "GNDA", "AGND", "3V3", "+3V3", "VCC", "VDD"}}
    if undocumented:
        lines += [
            "",
            "## Schematic nets not in Signal Inventory",
            "",
            "These nets exist in the schematic but have no Signal Inventory entry.",
            "If they carry a domain signal (P1: filter ΔP, P2: HVAC regime), add them.",
            "",
        ]
        for net in sorted(undocumented):
            lines.append(f"- `{net}`")

    return "\n".join(lines)


def bom_vs_device_context(sch_path: str) -> str:
    """Compare schematic BOM against docs/device_context.md BOM section.

    Reads the Markdown BOM table from device_context.md and compares it
    against the authoritative schematic BOM.

    Returns a Markdown-formatted diff report highlighting:
    - Components in schematic but not in device_context BOM
    - Components in device_context BOM but not in schematic
    - Value mismatches between the two sources

    hw-advisor calls this during 'bom' focus reviews.
    """
    try:
        sch_components = read_bom(sch_path)
    except KiCadFileError as exc:
        return f"Cannot read BOM from {sch_path}: {exc}"

    sch_bom = {comp.ref: comp for comp in sch_components}

    # Parse device_context.md BOM table
    project_root = Path(sch_path).parent.parent
    device_context_path = project_root / "docs" / "device_context.md"

    if not device_context_path.exists():
        return f"docs/device_context.md not found at {device_context_path}"

    dc_text = device_context_path.read_text(encoding="utf-8")
    dc_bom = _parse_markdown_bom(dc_text)

    lines = [
        "# BOM: Schematic vs device_context.md",
        f"Schematic source: {sch_path}",
        f"Governance source: {device_context_path}",
        "",
    ]

    # Components in schematic but not in device_context
    only_in_sch = sorted(set(sch_bom) - set(dc_bom), key=lambda r: r)
    if only_in_sch:
        lines += [
            "## In schematic, NOT in device_context.md BOM",
            "",
            "These components need to be added to the BOM table in device_context.md.",
            "",
        ]
        for ref in only_in_sch:
            comp = sch_bom[ref]
            lines.append(f"- **{ref}**: {comp.value} ({comp.footprint})")
        lines.append("")

    # Components in device_context but not in schematic
    only_in_dc = sorted(set(dc_bom) - set(sch_bom), key=lambda r: r)
    if only_in_dc:
        lines += [
            "## In device_context.md BOM, NOT in schematic",
            "",
            "These components are documented but not found in the schematic.",
            "Either the schematic is incomplete or the component was removed.",
            "",
        ]
        for ref in only_in_dc:
            lines.append(f"- **{ref}**: {dc_bom[ref]}")
        lines.append("")

    # Value mismatches
    common = set(sch_bom) & set(dc_bom)
    mismatches = [(ref, sch_bom[ref].value, dc_bom[ref]) for ref in sorted(common)
                  if sch_bom[ref].value and dc_bom[ref] and sch_bom[ref].value != dc_bom[ref]]
    if mismatches:
        lines += [
            "## Value mismatches",
            "",
            "Schematic value differs from device_context.md value.",
            "The schematic is authoritative — update device_context.md to match.",
            "",
            f"{'Ref':<8} {'Schematic':<24} device_context.md",
            "-" * 60,
        ]
        for ref, sch_val, dc_val in mismatches:
            lines.append(f"{ref:<8} {sch_val:<24} {dc_val}")
        lines.append("")

    if not only_in_sch and not only_in_dc and not mismatches:
        lines += [
            "## PASS — BOM is consistent",
            "",
            "All components match between the schematic and device_context.md BOM.",
        ]

    return "\n".join(lines)


def _parse_markdown_bom(text: str) -> dict[str, str]:
    """Parse a Markdown BOM table from device_context.md.

    Extracts | Ref | ... | Value / Spec | ... rows.
    Returns dict of ref → value string.
    """
    bom: dict[str, str] = {}
    in_bom = False
    header_seen = False

    for line in text.splitlines():
        stripped = line.strip()

        # Detect the BOM section by its header
        if "## Bill of Materials" in stripped or "## BOM" in stripped:
            in_bom = True
            header_seen = False
            continue

        if in_bom:
            # Stop at the next ## section
            if stripped.startswith("## ") and "BOM" not in stripped and "Bill" not in stripped:
                break

            if stripped.startswith("|") and stripped.endswith("|"):
                cols = [c.strip() for c in stripped.split("|")[1:-1]]

                # Skip the header row and separator row
                if not header_seen:
                    if any(c.lower() in {"ref", "component", "reference"} for c in cols):
                        header_seen = True
                    continue
                if all(c.replace("-", "").replace(":", "").strip() == "" for c in cols):
                    continue  # separator row

                if cols and cols[0] and not cols[0].startswith("["):
                    ref = cols[0]
                    # Value is typically column 3 (index 2) or 2 (index 1)
                    value = cols[2] if len(cols) > 2 else (cols[1] if len(cols) > 1 else "")
                    if ref and not ref.startswith("—") and not ref.startswith("-"):
                        bom[ref] = value

    return bom
