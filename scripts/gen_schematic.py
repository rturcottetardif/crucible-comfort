#!/usr/bin/env python3
"""
scripts/gen_schematic.py — Generate ComfortSense KiCad schematic.

Extracts symbol definitions from the installed KiCad 10 libraries and assembles
a single-sheet schematic for the ComfortSense HVAC filter monitor, covering:
  - Seeed XIAO nRF52840 Sense module (J1 left / J2 right connectors)
  - CT current-sensing circuit (J_CT, CT1, R_burden, C_bypass)
  - DS18B20 OneWire temperature probe (J_DS18B20, R_OW pull-up)  [rev 0.2]
  - I2C pull-up resistors (R_SDA, R_SCL)
  - Battery input (J_BAT, +BATT / GND / +3V3 rails)

Connectivity is shown with net labels (not routed wires) so the schematic is
readable without auto-routing.

Output: hardware/comfortsense.kicad_sch
"""
from __future__ import annotations
import sys
import uuid as _uuid_mod
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(PROJECT))

import re

KI_SYM = Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols")


# ── Symbol extraction from KiCad libraries ────────────────────────────────────

def extract_sym(lib_name: str, sym_name: str) -> str:
    """Extract a symbol as raw text from a .kicad_sym library.

    Preserves KiCad's original formatting (strings are always quoted in the
    library files, so no re-serialization needed). Renames SymName → LibName:SymName
    in both the top-level definition and sub-symbol definitions.
    """
    lib_path = KI_SYM / f"{lib_name}.kicad_sym"
    text = lib_path.read_text(encoding="utf-8")

    # Find the start of this specific symbol (exact name match, not prefix match)
    pattern = f'(symbol "{sym_name}"'
    start = text.find(pattern)
    if start == -1:
        raise ValueError(f"{sym_name} not found in {lib_name}")

    # Walk parentheses to find the matching close
    depth, i = 0, start
    while i < len(text):
        if text[i] == "(":
            depth += 1
        elif text[i] == ")":
            depth -= 1
            if depth == 0:
                raw = text[start : i + 1]
                break
        i += 1
    else:
        raise ValueError(f"Unclosed symbol {sym_name} in {lib_name}")

    # Only the top-level name gets the library prefix.
    # Sub-symbols (SymName_N_M) remain unprefixed — that is how KiCad embeds them.
    raw = re.sub(
        rf'\(symbol "{re.escape(sym_name)}"',
        f'(symbol "{lib_name}:{sym_name}"',
        raw,
        count=1,
    )
    return raw


# ── UUID / state ──────────────────────────────────────────────────────────────

def uid() -> str:
    return str(_uuid_mod.uuid4())


SHEET_UUID = uid()
_pwr_ref = 0


def next_pwr_ref() -> str:
    global _pwr_ref
    _pwr_ref += 1
    return f"#PWR{_pwr_ref:03d}"


# ── Low-level S-expression string builders ────────────────────────────────────

def _prop(name, value, x, y, rot=0, size=1.27, hide=False, justify=None):
    extras = ""
    if hide:
        extras += "\n        (hide yes)"
    if justify:
        extras += f"\n        (justify {justify})"
    return (
        f'    (property "{name}" "{value}"\n'
        f"      (at {x:.4f} {y:.4f} {rot})\n"
        f"      (effects\n"
        f"        (font (size {size} {size}))"
        f"{extras}\n"
        f"      )\n"
        f"    )"
    )


def _instances(ref, unit=1):
    return (
        f"    (instances\n"
        f'      (project "comfortsense"\n'
        f'        (path "/{SHEET_UUID}"\n'
        f'          (reference "{ref}")\n'
        f"          (unit {unit})\n"
        f"        )\n"
        f"      )\n"
        f"    )"
    )


def sym_inst(lib_id, x, y, rot, ref, value, footprint="",
             ref_offset=(1.27, 0), val_offset=(-1.27, 0),
             mirror="", extra_props=None, unit=1):
    rx, ry = x + ref_offset[0], y + ref_offset[1]
    vx, vy = x + val_offset[0], y + val_offset[1]
    mir = f"\n    (mirror {mirror})" if mirror else ""
    props = [
        _prop("Reference", ref, rx, ry),
        _prop("Value", value, vx, vy),
        _prop("Footprint", footprint, x, y, hide=True),
        _prop("Datasheet", "~", x, y, hide=True),
    ]
    if extra_props:
        for k, v, ex, ey in extra_props:
            props.append(_prop(k, v, ex, ey, hide=True))
    return (
        f"  (symbol\n"
        f'    (lib_id "{lib_id}")\n'
        f"    (at {x:.4f} {y:.4f} {rot}){mir}\n"
        f"    (unit {unit})\n"
        f"    (exclude_from_sim no)\n"
        f"    (in_bom yes)\n"
        f"    (on_board yes)\n"
        f"    (dnp no)\n"
        f'    (uuid "{uid()}")\n'
        + "\n".join(props) + "\n"
        + _instances(ref, unit) + "\n"
        f"  )"
    )


def power_sym(power_name, x, y, rot=0):
    ref = next_pwr_ref()
    return (
        f"  (symbol\n"
        f'    (lib_id "power:{power_name}")\n'
        f"    (at {x:.4f} {y:.4f} {rot})\n"
        f"    (unit 1)\n"
        f"    (exclude_from_sim no)\n"
        f"    (in_bom yes)\n"
        f"    (on_board yes)\n"
        f"    (dnp no)\n"
        f'    (uuid "{uid()}")\n'
        + _prop("Reference", ref, x, y, hide=True) + "\n"
        + _prop("Value", power_name, x + 1.5, y) + "\n"
        + _prop("Footprint", "", x, y, hide=True) + "\n"
        + _prop("Datasheet", "~", x, y, hide=True) + "\n"
        f'    (pin "1" (uuid "{uid()}"))\n'
        + _instances(ref) + "\n"
        f"  )"
    )


def net_label(name, x, y, rot=0):
    return (
        f'  (label "{name}"\n'
        f"    (at {x:.4f} {y:.4f} {rot})\n"
        f"    (effects\n"
        f"      (font (size 1.27 1.27))\n"
        f"      (justify left bottom)\n"
        f"    )\n"
        f'    (uuid "{uid()}")\n'
        f"  )"
    )


def wire(x1, y1, x2, y2):
    return (
        f"  (wire\n"
        f"    (pts (xy {x1:.4f} {y1:.4f}) (xy {x2:.4f} {y2:.4f}))\n"
        f"    (stroke (width 0) (type default))\n"
        f'    (uuid "{uid()}")\n'
        f"  )"
    )


def no_connect(x, y):
    return f'  (no_connect (at {x:.4f} {y:.4f}) (uuid "{uid()}"))'


# ── Schematic assembly ────────────────────────────────────────────────────────
#
# Layout overview (all coords in mm, Y increases downward):
#
#  Y≈55-70:  [CT input J_CT (45,60)] [CT1 (70,60)] [R1 burden] [C1 bypass]
#  Y≈87-107: [I2C R3/R4 (88-99, 97)]   [XIAO J1 (120,115)]  [XIAO J2 (150,115)]
#  Y≈130-150:[DS18B20 J_DS18B20 (45,143)] [R_OW (70,138)]
#  Y≈155:    [Battery J_BAT (35,155)]
#

def build_schematic() -> str:
    # ── Extract lib_symbols ───────────────────────────────────────────────────
    needed = [
        ("Device", "R"),
        ("Device", "C"),
        ("Device", "Transformer_1P_1S"),
        ("Connector_Generic", "Conn_01x07"),
        ("Connector_Generic", "Conn_01x02"),
        ("Connector_Generic", "Conn_01x03"),
        ("power", "GND"),
        ("power", "+3V3"),
        ("power", "+BATT"),
    ]
    lib_symbols_body = "\n".join(extract_sym(lib, sym) for lib, sym in needed)

    elements = []

    # ── Battery connector (J_BAT) ─────────────────────────────────────────────
    # Conn_01x02 at (35, 155).
    # Library pin local coords → global (local_y flipped): pin1=(-5.08,+2.54) → (29.92, 152.46) TOP
    #                                                       pin2=(-5.08,-2.54) → (29.92, 157.54) BOTTOM
    jbat_x, jbat_y = 35.0, 155.0
    elements.append(sym_inst("Connector_Generic:Conn_01x02", jbat_x, jbat_y, 0,
                              "J_BAT", "Battery JST-PH",
                              footprint="Connector_JST:JST_PH_B2B-PH-K_1x02_P2.00mm_Vertical",
                              ref_offset=(3, -3), val_offset=(3, 3)))
    jbat_px = jbat_x - 5.08
    # Place power symbols directly at pin positions — pin is at placement point
    elements.append(power_sym("+BATT", jbat_px, jbat_y - 2.54, rot=0))   # pin 1 (top)
    elements.append(power_sym("GND",   jbat_px, jbat_y + 2.54, rot=180)) # pin 2 (bottom)

    # ── XIAO nRF52840 Sense module — left 7-pin header (J1) ──────────────────
    # Conn_01x07 at (120, 115), rot=0
    # Pins at x=114.92, y offsets: +7.62, +5.08, +2.54, 0, -2.54, -5.08, -7.62
    # XIAO Left pinout: D0/A0, D1/A1, D2, D3, D4/SDA, D5/SCL, D6/TX
    j1_x, j1_y = 120.0, 115.0
    elements.append(sym_inst("Connector_Generic:Conn_01x07", j1_x, j1_y, 0,
                              "J1", "XIAO nRF52840 Sense (Left)",
                              footprint="Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical",
                              ref_offset=(5, -9), val_offset=(5, -11)))
    px = j1_x - 5.08
    # pin_y[0]=j1_y+7.62 (largest y = bottom = pin 7 TX)
    # pin_y[6]=j1_y-7.62 (smallest y = top  = pin 1 D0/A0)
    pin_y = [j1_y + dy for dy in (7.62, 5.08, 2.54, 0, -2.54, -5.08, -7.62)]
    elements.append(no_connect(px, pin_y[0]))                     # pin 7 D6/TX
    elements.append(net_label("SCL",    px, pin_y[1], rot=180))   # pin 6 D5/SCL P0.27
    elements.append(net_label("SDA",    px, pin_y[2], rot=180))   # pin 5 D4/SDA P0.07
    elements.append(net_label("ONEWIRE",px, pin_y[3], rot=180))   # pin 4 D3/P0.29
    elements.append(net_label("ADC_CT", px, pin_y[4], rot=180))   # pin 3 D2/P0.28
    elements.append(no_connect(px, pin_y[5]))                     # pin 2 D1/A1
    elements.append(no_connect(px, pin_y[6]))                     # pin 1 D0/A0

    # ── XIAO right 7-pin header (J2) ─────────────────────────────────────────
    # Conn_01x07 at (150, 115), rot=180
    # After 180° rotation: pin offsets become (+5.08, -dy)
    # Pins at x=155.08, y offsets: -7.62→102.38, -5.08→104.92... etc
    # XIAO Right pinout: VIN, GND, 3V3, D7/MISO, D8/MOSI, D9/SCK, D10/RX
    j2_x, j2_y = 150.0, 115.0
    elements.append(sym_inst("Connector_Generic:Conn_01x07", j2_x, j2_y, 180,
                              "J2", "XIAO nRF52840 Sense (Right)",
                              footprint="Connector_PinHeader_2.54mm:PinHeader_1x07_P2.54mm_Vertical",
                              ref_offset=(-5, -9), val_offset=(-5, -11)))
    px2 = j2_x + 5.08
    # For Conn_01x07 at rot=180, local y flips AND x flips.
    # Library pin 1 at local(-5.08, +7.62) → global(px2, j2_y+7.62) = BOTTOM (largest y)
    # Library pin 7 at local(-5.08, -7.62) → global(px2, j2_y-7.62) = TOP (smallest y)
    # XIAO Right pinout top-to-bottom on PCB: D10/RX, SCK, MOSI, MISO, +3V3, GND, VIN
    # i.e. pin 7→pin 1 from top to bottom.
    pin_y2 = [j2_y + dy for dy in (7.62, 5.08, 2.54, 0, -2.54, -5.08, -7.62)]
    # index 0 = j2_y+7.62 = pin 1 (VIN) at BOTTOM; index 6 = j2_y-7.62 = pin 7 (RX) at TOP
    # Place power symbols directly at pin positions (no wires needed)
    elements.append(power_sym("+BATT", px2, pin_y2[0], rot=0))    # pin 1 VIN
    elements.append(power_sym("GND",   px2, pin_y2[1], rot=180))  # pin 2 GND
    elements.append(power_sym("+3V3",  px2, pin_y2[2], rot=0))    # pin 3 +3V3
    # Pins 4-7 not connected
    for i in range(3, 7):
        elements.append(no_connect(px2, pin_y2[i]))

    # ── I2C pull-up resistors (R3 = SDA, R4 = SCL) ───────────────────────────
    # Placed to the left of J1, above XIAO body, so they don't overlap.
    # Device:R pin offsets from center: pin1=(0,+3.81) LOWER, pin2=(0,−3.81) UPPER.
    # Pull-up wiring: pin1 (lower) → +3V3; pin2 (upper) → net label (connects to J1 by name).
    r3_x, r3_y = 88.0, 97.0   # R3: SDA pull-up
    r4_x, r4_y = 99.0, 97.0   # R4: SCL pull-up

    for rx_pos, ry_pos, rref, rnet in (
        (r3_x, r3_y, "R3", "SDA"),
        (r4_x, r4_y, "R4", "SCL"),
    ):
        elements.append(sym_inst("Device:R", rx_pos, ry_pos, 0, rref, "10k",
                                  footprint="Resistor_SMD:R_0402_1005Metric",
                                  ref_offset=(1.5, 0), val_offset=(-1.5, 0)))
        # pin1 (lower, y+3.81) → +3V3
        elements.append(power_sym("+3V3", rx_pos, ry_pos + 3.81 + 2.54, rot=0))
        elements.append(wire(rx_pos, ry_pos + 3.81, rx_pos, ry_pos + 3.81 + 2.54))
        # pin2 (upper, y-3.81) → net label; net name matches J1 SDA/SCL label for connectivity
        elements.append(net_label(rnet, rx_pos, ry_pos - 3.81, rot=0))

    # ── CT current-sensing circuit ────────────────────────────────────────────
    # Primary (L1/L2) faces the AC wiring, secondary faces the MCU ADC.
    # Transformer_1P_1S pin positions (relative to center):
    #   primary: pin1 (AA) at (-10.16, +5.08), pin2 (AB) at (-10.16, -5.08)
    #   secondary: pin3 (SA) at (+10.16, -5.08), pin4 (SB) at (+10.16, +5.08)
    ct_x, ct_y = 70.0, 60.0
    elements.append(sym_inst("Device:Transformer_1P_1S", ct_x, ct_y, 0,
                              "CT1", "SCT-013-000",
                              footprint="",
                              ref_offset=(0, -9), val_offset=(0, -11)))

    # CT input connector (J_CT) — Conn_01x02 at left of transformer
    jct_x, jct_y = 45.0, 60.0
    elements.append(sym_inst("Connector_Generic:Conn_01x02", jct_x, jct_y, 0,
                              "J_CT", "CT Sensor Input",
                              footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
                              ref_offset=(3, -3), val_offset=(3, 3)))
    # J_CT pin1 at (39.92, 62.54), pin2 at (39.92, 57.46)
    jct_px = jct_x - 5.08
    # wire J_CT pin1 → CT1 primary pin1 (AA)
    ct_aa = (ct_x - 10.16, ct_y + 5.08)
    ct_ab = (ct_x - 10.16, ct_y - 5.08)
    elements.append(wire(jct_px, jct_y + 2.54, ct_aa[0], ct_aa[1]))
    elements.append(wire(jct_px, jct_y - 2.54, ct_ab[0], ct_ab[1]))

    # Burden resistor R1 (68Ω) — vertical, between secondary pins
    # CT secondary: SA at (+10.16, -5.08), SB at (+10.16, +5.08) relative to ct center
    ct_sa = (ct_x + 10.16, ct_y - 5.08)  # SA — top secondary pin
    ct_sb = (ct_x + 10.16, ct_y + 5.08)  # SB — bottom secondary pin
    # R1 placed at (ct_x + 10.16, ct_y) — exactly between SA and SB
    r1_x, r1_y = ct_sa[0], ct_y
    elements.append(sym_inst("Device:R", r1_x, r1_y, 0, "R1", "68R",
                              footprint="Resistor_SMD:R_0402_1005Metric",
                              ref_offset=(1.5, 0), val_offset=(-1.5, 0)))
    # R1 pin1 (0,+3.81) connects to ct_sa.y
    elements.append(wire(r1_x, r1_y + 3.81, ct_sa[0], ct_sa[1]))
    # R1 pin2 (0,-3.81) connects to ct_sb.y
    elements.append(wire(r1_x, r1_y - 3.81, ct_sb[0], ct_sb[1]))
    # Midpoint of R1 (between primary and secondary) — this is the ADC sense point
    # Use a label at R1's midpoint output (pin2 side → ct_sb → high signal)
    # Actual CT sensor output is the voltage across R1; we label the top pin as ADC_CT
    elements.append(wire(r1_x, r1_y + 3.81, r1_x + 5, r1_y + 3.81))
    elements.append(net_label("ADC_CT", r1_x + 5, r1_y + 3.81))
    # SB (bottom) → GND
    elements.append(wire(ct_sb[0], ct_sb[1], ct_sb[0], ct_sb[1] + 2.54))
    elements.append(power_sym("GND", ct_sb[0], ct_sb[1] + 2.54, rot=180))

    # Bypass cap C1 across R1 (parallel to burden resistor)
    c1_x = r1_x + 8.0
    elements.append(sym_inst("Device:C", c1_x, r1_y, 0, "C1", "100nF",
                              footprint="Capacitor_SMD:C_0402_1005Metric",
                              ref_offset=(1.5, 0), val_offset=(-1.5, 0)))
    # C1 pin1 (0,+3.81) → ADC_CT net
    elements.append(wire(c1_x, r1_y + 3.81, c1_x, ct_sa[1]))
    elements.append(wire(c1_x, ct_sa[1], r1_x, ct_sa[1]))
    # C1 pin2 (0,−3.81) → GND
    elements.append(wire(c1_x, r1_y - 3.81, c1_x, ct_sb[1] + 2.54))
    elements.append(power_sym("GND", c1_x, ct_sb[1] + 2.54 + 2.54, rot=180))
    elements.append(wire(c1_x, ct_sb[1] + 2.54, c1_x, ct_sb[1] + 2.54 + 2.54))

    # ── DS18B20 OneWire temperature probe (rev 0.2 — replaces NTC sub-circuit) ──
    # J_DS18B20: 3-pin connector — pin1=VCC, pin2=DATA/ONEWIRE, pin3=GND
    # R_OW: 4.7 kΩ pull-up, +3V3 → ONEWIRE net (DS18B20 open-drain DATA line)
    # ONEWIRE net connects to J1 D3/P0.29 (OUTSIDE_TEMP per toolchain_config.md)
    # Bill 6 / Case 9 — implements Case 8 Condition 3 (DS18B20 Option B)
    jds_x, jds_y = 45.0, 143.0
    elements.append(sym_inst("Connector_Generic:Conn_01x03", jds_x, jds_y, 0,
                              "J_DS18B20", "DS18B20 Temp Probe",
                              footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
                              ref_offset=(3, -4), val_offset=(3, 4)))
    jds_px = jds_x - 5.08
    # Conn_01x03 library: pin1 at local(-5.08,+2.54) → global(jds_px, jds_y-2.54) = TOP
    #                     pin2 at local(-5.08, 0)     → global(jds_px, jds_y)      = MID
    #                     pin3 at local(-5.08,-2.54)  → global(jds_px, jds_y+2.54) = BOTTOM
    # Desired: VCC(top) / DATA(mid) / GND(bottom)
    # Place power symbols directly at pin positions for reliable net assignment.
    elements.append(power_sym("+3V3", jds_px, jds_y - 2.54, rot=0))   # pin 1 (top) → VCC
    elements.append(net_label("ONEWIRE", jds_px, jds_y, rot=180))       # pin 2 (mid) → DATA
    elements.append(power_sym("GND",  jds_px, jds_y + 2.54, rot=180))  # pin 3 (bot) → GND

    # R_OW: 4.7 kΩ pull-up resistor (vertical: pin1=top=+3V3, pin2=bottom=ONEWIRE)
    row_x, row_y = 70.0, 138.0
    elements.append(sym_inst("Device:R", row_x, row_y, 0, "R_OW", "4.7k",
                              footprint="Resistor_SMD:R_0402_1005Metric",
                              ref_offset=(1.5, 0), val_offset=(-1.5, 0)))
    # R_OW pin1 (top) → +3V3
    elements.append(power_sym("+3V3", row_x, row_y + 3.81 + 2.54, rot=0))
    elements.append(wire(row_x, row_y + 3.81, row_x, row_y + 3.81 + 2.54))
    # R_OW pin2 (bottom) → ONEWIRE net label
    elements.append(wire(row_x, row_y - 3.81, row_x + 5.0, row_y - 3.81))
    elements.append(net_label("ONEWIRE", row_x + 5.0, row_y - 3.81))

    # ── Assemble schematic ────────────────────────────────────────────────────
    body = "\n".join(elements)

    return f"""\
(kicad_sch
  (version 20250114)
  (generator "comfortsense_gen")
  (generator_version "1.0")
  (uuid "{SHEET_UUID}")
  (paper "A3")
  (title_block
    (title "ComfortSense HVAC Filter Monitor")
    (date "2026-05-19")
    (rev "0.2")
    (company "CrucibleStudio")
    (comment 1 "nRF52840 Sense + CT current sensor + DS18B20 OneWire temperature probe")
    (comment 2 "KiCad MCP server integration — generated by scripts/gen_schematic.py")
  )
  (lib_symbols
{lib_symbols_body}
  )
{body}
)
"""


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    hw_dir = PROJECT / "hardware"
    hw_dir.mkdir(exist_ok=True)
    out = hw_dir / "comfortsense.kicad_sch"
    content = build_schematic()
    out.write_text(content, encoding="utf-8")
    print(f"Wrote {out}")


if __name__ == "__main__":
    main()
