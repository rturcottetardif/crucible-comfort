#!/usr/bin/env python3
"""
scripts/gen_layout.py — Generate hardware/comfortsense.kicad_pcb.

Extracts footprint definitions from the installed KiCad 10 libraries and
assembles a complete .kicad_pcb file with component placement, board outline,
and net assignments.  Trace routing is NOT performed — open in KiCad GUI for
routing.  Run kicad-cli to export SVG / Gerbers.

Usage:
    python3 scripts/gen_layout.py
    kicad-cli pcb export svg -o hardware/ hardware/comfortsense.kicad_pcb
"""

import re
import uuid
from pathlib import Path

KI_FP = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints")
OUT   = Path(__file__).parent.parent / "hardware" / "comfortsense.kicad_pcb"


# ── Utilities ──────────────────────────────────────────────────────────────────

def uid() -> str:
    return str(uuid.uuid4())


def _walk_to_close(text: str, open_pos: int) -> int:
    """Return index of the ')' that closes the '(' at text[open_pos]."""
    depth = 0
    in_str = False
    esc = False
    i = open_pos
    n = len(text)
    while i < n:
        c = text[i]
        if esc:
            esc = False
        elif in_str:
            if c == "\\":
                esc = True
            elif c == '"':
                in_str = False
        elif c == '"':
            in_str = True
        elif c == "(":
            depth += 1
        elif c == ")":
            depth -= 1
            if depth == 0:
                return i
        i += 1
    return n - 1


# ── Net table ──────────────────────────────────────────────────────────────────

_NET_NAMES = [
    "GND", "+3V3", "+BATT",
    "SDA", "SCL",
    "ADC_CT", "ADC_TEMP",
    "CT_IN_P", "CT_IN_N",
    "D0", "D1", "TX", "RX",
    "SCK", "MOSI", "MISO", "VIN",
]
NETS: dict[str, int] = {n: i + 1 for i, n in enumerate(_NET_NAMES)}


def net_decls() -> str:
    lines = ['\t(net 0 "")']
    for name, idx in NETS.items():
        lines.append(f'\t(net {idx} "{name}")')
    return "\n".join(lines)


# ── Footprint loader ───────────────────────────────────────────────────────────

def inject_nets(text: str, pad_nets: dict[str, str]) -> str:
    """Scan text for (pad "N" ...) blocks and inject (net idx "name") into each."""
    result: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "(" and text[i + 1 : i + 5] == "pad ":
            end = _walk_to_close(text, i)
            block = text[i : end + 1]
            m = re.search(r'\(pad\s+"([^"]+)"', block)
            if m:
                pad_num = m.group(1)
                if pad_num in pad_nets:
                    net_name = pad_nets[pad_num]
                    net_idx = NETS.get(net_name, 0)
                    block = block[:-1] + f'\n\t\t(net {net_idx} "{net_name}")\n\t)'
            result.append(block)
            i = end + 1
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


_UUID_BARE = ("fp_line ", "fp_rect ", "fp_circle ", "fp_arc ", "fp_poly ", "fp_bezier ", "pad ")
_UUID_EFFECTS = ("fp_text ", "property ")


def inject_uuids(text: str) -> str:
    """Add (uuid ...) to footprint sub-elements that lack one."""
    all_targets = _UUID_BARE + _UUID_EFFECTS
    result: list[str] = []
    i = 0
    n = len(text)
    while i < n:
        if text[i] == "(":
            matched = None
            for t in all_targets:
                if text[i + 1 : i + 1 + len(t)] == t:
                    matched = t
                    break
            if matched:
                end = _walk_to_close(text, i)
                block = text[i : end + 1]
                if "(uuid " not in block:
                    if matched in _UUID_EFFECTS:
                        m = re.search(r'\n(\s*)\(effects\b', block)
                        if m:
                            pos = m.start()
                            indent = m.group(1)
                            block = block[:pos] + f'\n{indent}(uuid "{uid()}")' + block[pos:]
                        else:
                            block = block[:-1] + f'\n\t\t(uuid "{uid()}")\n\t)'
                    else:
                        block = block[:-1] + f'\n\t\t(uuid "{uid()}")\n\t)'
                result.append(block)
                i = end + 1
            else:
                result.append(text[i])
                i += 1
        else:
            result.append(text[i])
            i += 1
    return "".join(result)


def _strip_nested(raw: str, *tags: str) -> str:
    """Remove all (tag ...) blocks (any nesting depth) and their preceding whitespace."""
    for tag in tags:
        search = f"({tag}"
        while True:
            pos = raw.find(search)
            if pos == -1:
                break
            after = pos + len(search)
            if after < len(raw) and raw[after] not in (' ', '\t', '\n', '"', ')'):
                # False match — tag is a prefix of a longer token; skip past it
                break
            end = _walk_to_close(raw, pos)
            start = pos
            while start > 0 and raw[start - 1] in ' \t':
                start -= 1
            if start > 0 and raw[start - 1] == '\n':
                start -= 1
            raw = raw[:start] + raw[end + 1:]
    return raw


def place(
    lib: str,
    name: str,
    ref: str,
    value: str,
    x: float,
    y: float,
    rot: float = 0.0,
    pad_nets: dict[str, str] | None = None,
) -> str:
    """Read a .kicad_mod and return a placed footprint block for .kicad_pcb."""
    fp_path = KI_FP / f"{lib}.pretty" / f"{name}.kicad_mod"
    raw = fp_path.read_text(encoding="utf-8")

    # Strip 3D model references and embedded_fonts — path-dependent, breaks portability
    raw = _strip_nested(raw, "model", "embedded_fonts")

    # Add library prefix to top-level footprint name
    raw = re.sub(
        rf'^(\(footprint\s+"){re.escape(name)}"',
        rf'\1{lib}:{name}"',
        raw, count=1, flags=re.MULTILINE,
    )

    # Strip library-only metadata
    raw = re.sub(r'\n\t\(version \d+\)', "", raw)
    raw = re.sub(r'\n\t\(generator\s+"[^"]*"\)', "", raw)
    raw = re.sub(r'\n\t\(generator_version\s+"[^"]*"\)', "", raw)

    # Inject (uuid) and (at X Y [ROT]) immediately after (layer "F.Cu")
    rot_str = f" {rot:.4f}" if rot else ""
    raw = re.sub(
        r'(\n\t\(layer "F\.Cu"\))',
        rf'\1\n\t(uuid "{uid()}")\n\t(at {x:.4f} {y:.4f}{rot_str})',
        raw, count=1,
    )

    # Update Reference property
    raw = raw.replace('"REF**"', f'"{ref}"', 1)

    # Update Value property (default is the footprint name)
    raw = re.sub(
        r'(property "Value" ")[^"]*(")',
        rf'\g<1>{value}\g<2>',
        raw, count=1,
    )

    # Inject net assignments into pads
    if pad_nets:
        raw = inject_nets(raw, pad_nets)

    # Add (uuid ...) to every sub-element that requires one
    raw = inject_uuids(raw)

    return raw


# ── Board geometry ─────────────────────────────────────────────────────────────

def edge_line(x1: float, y1: float, x2: float, y2: float) -> str:
    return (
        f"\t(gr_line\n"
        f"\t\t(start {x1:.4f} {y1:.4f})\n"
        f"\t\t(end {x2:.4f} {y2:.4f})\n"
        f"\t\t(stroke (width 0.05) (type solid))\n"
        f"\t\t(layer \"Edge.Cuts\")\n"
        f"\t\t(uuid \"{uid()}\")\n"
        f"\t)"
    )


def board_rect(x: float, y: float, w: float, h: float) -> str:
    x2, y2 = x + w, y + h
    return "\n".join([
        edge_line(x, y, x2, y),
        edge_line(x2, y, x2, y2),
        edge_line(x2, y2, x, y2),
        edge_line(x, y2, x, y),
    ])


# ── Component placement ────────────────────────────────────────────────────────
#
#  Board: 95 mm × 55 mm.  Canvas origin at (BX, BY).
#
#  Layout (left → right, signals flow from sensors to MCU):
#
#    [J_BAT]  [J_CT ─ R1 ─ C1]  [R3 R4]  [J1 | J2]  ← XIAO rows
#    [J_TEMP ─ R2]
#
#  XIAO module: 21 mm wide; two 1×7 pin rows separated by 18.46 mm (c-to-c).
#

BX, BY = 10.0, 10.0     # board top-left corner on PCB canvas
BW, BH = 95.0, 55.0     # board width × height (mm)
XIAO_SEP = 18.46        # centre-to-centre distance between XIAO pin rows


def all_footprints() -> list[str]:
    conn2 = ("Connector_PinHeader_2.54mm", "PinHeader_1x02_P2.54mm_Vertical")
    conn7 = ("Connector_PinHeader_2.54mm", "PinHeader_1x07_P2.54mm_Vertical")
    r402  = ("Resistor_SMD",   "R_0402_1005Metric")
    c402  = ("Capacitor_SMD",  "C_0402_1005Metric")

    return [
        # Battery connector — top-left
        place(*conn2, ref="J_BAT", value="Battery-2P",
              x=BX + 8, y=BY + 10,
              pad_nets={"1": "+BATT", "2": "GND"}),

        # CT clamp input connector
        place(*conn2, ref="J_CT", value="CT-Clamp-3.5mm",
              x=BX + 8, y=BY + 24,
              pad_nets={"1": "CT_IN_P", "2": "CT_IN_N"}),

        # NTC temperature probe connector
        place(*conn2, ref="J_TEMP", value="NTC-Probe",
              x=BX + 8, y=BY + 40,
              pad_nets={"1": "ADC_TEMP", "2": "GND"}),

        # R1 — CT burden resistor (68 Ω, 0402)
        place(*r402, ref="R1", value="68R",
              x=BX + 26, y=BY + 24, rot=90.0,
              pad_nets={"1": "CT_IN_P", "2": "ADC_CT"}),

        # C1 — CT bypass / anti-alias cap (100 nF, 0402)
        place(*c402, ref="C1", value="100nF",
              x=BX + 34, y=BY + 24,
              pad_nets={"1": "ADC_CT", "2": "GND"}),

        # R2 — NTC voltage divider upper arm (10 kΩ, 0402)
        place(*r402, ref="R2", value="10k",
              x=BX + 26, y=BY + 40, rot=90.0,
              pad_nets={"1": "+3V3", "2": "ADC_TEMP"}),

        # R3 — SDA pull-up (10 kΩ, 0402)
        place(*r402, ref="R3", value="10k",
              x=BX + 52, y=BY + 18,
              pad_nets={"1": "+3V3", "2": "SDA"}),

        # R4 — SCL pull-up (10 kΩ, 0402)
        place(*r402, ref="R4", value="10k",
              x=BX + 52, y=BY + 25,
              pad_nets={"1": "+3V3", "2": "SCL"}),

        # J1 — XIAO nRF52840 Sense left header
        #       Pins (top→bottom): D0 D1 ADC_CT ADC_TEMP SDA SCL GND
        place(*conn7, ref="J1", value="XIAO-Left",
              x=BX + 70, y=BY + 22,
              pad_nets={
                  "1": "D0",      "2": "D1",
                  "3": "ADC_CT",  "4": "ADC_TEMP",
                  "5": "SDA",     "6": "SCL",   "7": "GND",
              }),

        # J2 — XIAO nRF52840 Sense right header (18.46 mm from J1)
        #       Pins (top→bottom): MISO MOSI SCK RX TX GND VIN
        place(*conn7, ref="J2", value="XIAO-Right",
              x=BX + 70 + XIAO_SEP, y=BY + 22,
              pad_nets={
                  "1": "MISO",  "2": "MOSI",  "3": "SCK",
                  "4": "RX",    "5": "TX",    "6": "GND",  "7": "VIN",
              }),
    ]


# ── Static PCB sections ────────────────────────────────────────────────────────

LAYERS = """\
\t(layers
\t\t(0 "F.Cu" signal)
\t\t(2 "B.Cu" signal)
\t\t(13 "F.Paste" user)
\t\t(15 "B.Paste" user)
\t\t(5 "F.SilkS" user "F.Silkscreen")
\t\t(7 "B.SilkS" user "B.Silkscreen")
\t\t(1 "F.Mask" user)
\t\t(3 "B.Mask" user)
\t\t(25 "Edge.Cuts" user)
\t\t(31 "F.CrtYd" user "F.Courtyard")
\t\t(29 "B.CrtYd" user "B.Courtyard")
\t\t(35 "F.Fab" user)
\t\t(33 "B.Fab" user)
\t)"""

SETUP = """\
\t(setup
\t\t(pad_to_mask_clearance 0)
\t\t(allow_soldermask_bridges_in_footprints no)
\t\t(pcbplotparams
\t\t\t(layerselection 0x00010fc_ffffffff)
\t\t\t(plot_on_all_layers_selection 0x0000000_00000000)
\t\t\t(disableapertmacros no)
\t\t\t(usegerberextensions no)
\t\t\t(usegerberattributes yes)
\t\t\t(usegerberadvancedattributes yes)
\t\t\t(creategerberjobfile yes)
\t\t\t(svgprecision 4)
\t\t\t(plotframeref no)
\t\t\t(viasonmask no)
\t\t\t(mode 1)
\t\t\t(useauxorigin no)
\t\t\t(hpglpennumber 1)
\t\t\t(hpglpenspeed 20)
\t\t\t(hpglpendiameter 15.0)
\t\t\t(dxfpolygonmode yes)
\t\t\t(dxfimperialunits yes)
\t\t\t(dxfusepcbnewfont yes)
\t\t\t(psnegative no)
\t\t\t(psa4output no)
\t\t\t(plotreference yes)
\t\t\t(plotvalue yes)
\t\t\t(plotinvisibletext no)
\t\t\t(sketchpadsonfab no)
\t\t\t(subtractmaskfromsilk no)
\t\t\t(outputformat 1)
\t\t\t(mirror no)
\t\t\t(drillshape 1)
\t\t\t(scaleselection 1)
\t\t\t(outputdirectory "")
\t\t)
\t)"""


# ── Assemble and write ─────────────────────────────────────────────────────────

def build() -> str:
    fps   = "\n\n".join(all_footprints())
    nets  = net_decls()
    edges = board_rect(BX, BY, BW, BH)

    return f"""\
(kicad_pcb
\t(version 20241229)
\t(generator "pcbnew")
\t(generator_version "9.0")
\t(general
\t\t(thickness 1.6)
\t\t(legacy_teardrops no)
\t)
\t(paper "A3")
\t(title_block
\t\t(title "ComfortSense HVAC Filter Monitor")
\t\t(rev "0.1")
\t\t(date "2026-05-19")
\t)
{LAYERS}
{SETUP}

{nets}

{fps}

{edges}
)
"""


def main() -> None:
    OUT.parent.mkdir(parents=True, exist_ok=True)
    pcb = build()
    OUT.write_text(pcb, encoding="utf-8")
    print(f"Wrote {OUT}")
    print(f"  Board: {BW} mm × {BH} mm")
    print(f"  Nets:  {len(NETS)} named")
    print(f"  Footprints: {len(all_footprints())}")


if __name__ == "__main__":
    main()
