# BILL: Schematic Rev 0.2 — Replace NTC Sub-circuit with DS18B20 OneWire Connector

```
Proposed by:  bill-drafter agent (implements Case 8 Condition 3)
Date drafted: 2026-05-19
Change type:  hardware
Branch:       bill/schematic-rev2-ds18b20
Status:       ENACTED 2026-05-19 — Justice direct acceptance, all points uncontested
```

---

## Problem Statement

Case 8 (enacted Bill 5, 2026-05-19) ruled Option B — DS18B20 OneWire is the authorized
outside_temp sensing architecture — and imposed an explicit pre-condition on Stage 2 gate
opening (Condition 3):

> "Schematic rev 0.2 must replace TH1 + R2 + J_TEMP with DS18B20 connector + 4.7 kΩ
> pull-up before Stage 2 gate opens."

Schematic rev 0.1 used an NTC 10k thermistor sub-circuit (TH1 + R2 divider + J_TEMP
2-pin connector, net ADC_TEMP) for outside_temp sensing. That sub-circuit was explicitly
not authorized by Case 8. Rev 0.1 is accepted only as a partial schematic establishing
the non-temperature signal paths. This Bill authorizes rev 0.2.

Additionally, rev 0.1 had a pin assignment error: ADC_CT was placed on J1 pin D0/A0
(P0.02) and ADC_TEMP on D1/A1 (P0.03), but toolchain_config.md (LOCKED 2026-04-20)
specifies CT_CURRENT on Arduino pin 2 / P0.28 (= D2) and OUTSIDE_TEMP on Arduino pin 3
/ P0.29 (= D3). Rev 0.2 corrects this concurrently.

---

## Proposed Change

**File:** `scripts/gen_schematic.py` (generator) → regenerates `hardware/comfortsense.kicad_sch`
**Revision:** 0.1 → 0.2

### Removals

| Component | Value | Reason |
|-----------|-------|--------|
| TH1 | NTC 10k (0402) | Not authorized — Case 8 Option B |
| R2 | 10k fixed (0402) | Not authorized — Case 8 Option B |
| J_TEMP | 2-pin connector | Not authorized — Case 8 Option B |
| Net ADC_TEMP | — | Removed with above components |

### Additions

| Component | Value | Function |
|-----------|-------|----------|
| J_DS18B20 | 3-pin connector (VCC / DATA / GND) | Waterproof DS18B20 probe cable entry |
| R_OW | 4.7 kΩ pull-up (0402) | OneWire bus pull-up: +3V3 → ONEWIRE net |
| Net ONEWIRE | — | DATA line: J_DS18B20 pin 2 → R_OW → J1 D3/P0.29 |

### Pin assignment correction (concurrent)

| J1 pin | Signal | Rev 0.1 (wrong) | Rev 0.2 (correct) |
|--------|--------|-----------------|-------------------|
| D0/A0 (P0.02) | — | ADC_CT | no_connect |
| D1/A1 (P0.03) | — | ADC_TEMP | no_connect |
| D2 (P0.28) | CT_CURRENT | no_connect | ADC_CT |
| D3 (P0.29) | OUTSIDE_TEMP | no_connect | ONEWIRE |

### src/kicad_integration.py — SIGNAL_TO_NET update

```python
# Old (rev 0.1 placeholder — net OUTSIDE_TEMP not in schematic; MISSING):
"outside_temp":   "OUTSIDE_TEMP",

# New (rev 0.2 — ONEWIRE net present; reports FOUND):
"outside_temp":   "ONEWIRE",
```

Re-scaffold required: NO. Signal Inventory and Firmware UART Format unchanged.
Amendment 11 not triggered.

---

## Article / Amendment Grounding

- **Article II:** Case 8 Condition 3 is an explicit Justice mandate requiring this Bill.
- **Amendment 2:** Stage 2 pre-condition (Case 8 Condition 3) closes upon enactment.
- **Amendment 9:** BOM change (3 removed, 2 added) requires Bill + BOM update in
  `docs/device_context.md`. BOM update is a condition of enactment.

---

## Physical Evidence

1. **Case 8 ruling (2026-05-19):** DS18B20 ±0.5°C factory calibration required for
   T_COLD_SHOULDER = 5°C / T_WARM_SHOULDER = 15°C (10°C window). NTC ±1–2°C tolerance
   is insufficient for a self-installing device.
2. **Bills 2-A / 2-B (Cases 3/4):** Shoulder thresholds enacted; DS18B20 accuracy
   provides ±5% boundary error vs NTC's ±10–20%.
3. **toolchain_config.md Pin Map (LOCKED 2026-04-20):** OUTSIDE_TEMP = P0.29 / Arduino
   pin 3 / OneWire + 4.7 kΩ pull-up. Grounds both the DS18B20 architecture and
   R_OW = 4.7 kΩ value.
4. **toolchain_config.md Library Manifest:** OneWire and DallasTemperature libraries
   listed as planned dependencies — DS18B20 architecture anticipated since Stage 0.

---

## Expected Outcome

- `check_signal_inventory()` on rev 0.2: `outside_temp → ONEWIRE: FOUND` (was MISSING)
- Pin assignment error corrected: ADC_CT on D2/P0.28, ONEWIRE on D3/P0.29
- Case 8 Condition 3: CLOSED upon enactment
- Stage 2 gate pre-condition (schematic rev 0.2): MET

---

## Pre-Flagged Debate Points (all uncontested)

**Point 1 — Amendment 11 applicability to src/kicad_integration.py:**
No. Amendment 11 names exactly three frozen modules. `src/kicad_integration.py` is
project source. Net-name string correction only. Uncontested.

**Point 2 — SIGNAL_TO_NET correction is a labeling fix, not a new signal:**
`ONEWIRE` is the schematic net name for the same P2 domain primitive (outside_temp).
No new domain information introduced. Uncontested.

**Point 3 — ONEWIRE vs OUTSIDE_TEMP as net label:**
ONEWIRE names the bus protocol (determines firmware library: DallasTemperature over
OneWire). Constitutionally valid. If Justice prefers OUTSIDE_TEMP as the net name,
the same one-line SIGNAL_TO_NET update applies. Uncontested either way.

---

**Enacted bill:** Bill 6 — Schematic Rev 0.2 DS18B20 (`docs/governance/bills/stage2-schematic-rev2.md`)
**Implementation branch:** main (direct — implements pre-decided Case 8 ruling)
