# BILL: Retroactive Authorization — Stage 2 KiCad Schematic, PCB Layout, and Signal Traceability Module

```
Proposed by:  bill-drafter agent (police audit finding — commit acddbff)
Date drafted: 2026-05-19
Change type:  hardware + software
Branch:       schematics (already committed; retroactive authorization)
Status:       ENACTED 2026-05-19 — Justice direct acceptance, Option B (DS18B20 reinstated)
```

---

## Problem Statement

Commit `acddbff` introduced five files to the repository without a preceding enacted Bill:
`hardware/comfortsense.kicad_sch`, `hardware/comfortsense.kicad_pcb`,
`hardware/comfortsense.kicad_prl`, `hardware/comfortsense.svg`, and
`src/kicad_integration.py`. A constitutional police audit flagged two Article II violations.

**Violation class 1 — hardware commitment without Bill:** committing a full KiCad schematic
and PCB layout constitutes a hardware change. It records a component topology, net
architecture, and BOM that establishes the physical implementation path for Stage 2.
Article II requires explicit human approval via enacted Bill before this class of change.

**Violation class 2 — project pipeline module without Bill:** adding `src/kicad_integration.py`
constitutes a project pipeline change in the `src/` directory. Any change to the `src/`
pipeline requires a Bill per the Legislative Process.

The human engineer's stated intent: the schematics are to improve Stage 2. Stage 1 is
CLOSED as of 2026-05-19 (8/8 profiles PASS, Path B waived, stage-compactor freeze
complete). This Bill retroactively authorizes both violation classes, traces every
schematic component to a domain primitive from Amendment 1, flags the open tensions
for debate, and requests Justice ruling per the Cases 3–7 direct-acceptance precedent.

Reference: police audit commit `acddbff` (2026-05-19); `docs/governance/case_law.md`
Stage 1 Path B Waiver SOR (2026-05-19); `docs/device_context.md` Signal Inventory;
`docs/toolchain_config.md` Pin Map.

---

## Proposed Change

### Part A — Retroactive authorization of hardware files

The following files committed in `acddbff` on branch `schematics` are retroactively
authorized as Stage 2 preparation hardware artifacts. No firmware, algorithm, threshold,
filter coefficient, or FSM condition is changed by these files. No physical hardware has
been fabricated from them. They are design documents only.

**Files authorized:**
- `hardware/comfortsense.kicad_sch` (schematic rev 0.1, 2026-05-19)
- `hardware/comfortsense.kicad_pcb`
- `hardware/comfortsense.kicad_prl`
- `hardware/comfortsense.svg`

**Schematic component inventory with domain primitive traces:**

| Ref | Value / Part | Circuit function | Domain primitive | Pin map anchor |
|-----|-------------|-----------------|-----------------|----------------|
| J1, J2 | XIAO nRF52840 Sense 7-pin headers | MCU breakout — carries all signal pins through the ComfortSense PCB | P1 (IMU/mic/CT channels) + P2 (outside_temp) | Active board; FQBN `Seeeduino:nrf52:xiaonRF52840Sense` |
| J_BAT | Battery JST-PH 2-pin | Li-Po supply to +BATT rail | Power infrastructure | — |
| J_CT | CT Sensor Input 2-pin | External cable entry — SCT-013-000 secondary leads | P1 Filter ΔP — ct_current_rms entry point | CT_CURRENT = P0.28 |
| CT1 | SCT-013-000 split-core CT | Inductive current sensing of HVAC blower motor; no conductor modification required | P1 Filter ΔP — I0_HEATING = 4 A and I0_COOLING = 9 A (Bill 1 / Case 2); resolves "Current clamp — TBD" in toolchain_config.md | CT_CURRENT = P0.28 |
| R1 | 68 Ω burden resistor (0402) | V_CT = I_secondary × 68 Ω. At I0_HEATING = 4 A: V_rms = (4/2000) × 68 = 0.136 V; at I0_COOLING = 9 A: V_rms = 0.306 V. Both within ADC 3.6 V full-scale, both ≥169 LSB above noise floor. | P1 — sets ADC signal range for ct_current_rms; traces to I0_HEATING, I0_COOLING (Bill 1), σ_ct_eff specification (Bill 3 / Case 6) | CT_CURRENT = P0.28 |
| C1 | 100 nF anti-alias capacitor (0402) | RC cutoff f_c = 1/(2π × 68 × 100e-9) ≈ 23.4 kHz — attenuates switching noise above 600 Hz ADC Nyquist | P1 — protects ct_current_rms at FS_CT_HZ = 600 Hz (Bill 3 / Case 6); implements the Gate 0.3 "anti-alias filter required" caution | CT_CURRENT = P0.28 |
| TH1 | NTC 10k thermistor (0402) | Analog temperature sensing — voltage divider midpoint read as ADC_TEMP by nRF52840 ADC | P2 HVAC operating regime — outside_temp signal. **Architecture deviation from DS18B20 OneWire plan — see Debate Point 3** | OUTSIDE_TEMP = P0.29 |
| R2 | 10k fixed resistor (0402) | NTC divider upper leg: +3V3 → R2 → ADC_TEMP → TH1 → GND. Spans −30 to +45 °C with ≥600 ADC count separation between T_COLD_SHOULDER (5 °C) and T_WARM_SHOULDER (15 °C) | P2 — adequate resolution for Bills 2-A / 2-B shoulder constants | OUTSIDE_TEMP / ADC_TEMP path |
| R3 | 10k I2C pull-up (0402) — SDA | I2C bus pull-up for LSM6DS3TR-C SDA; within Fast Mode (400 kHz) acceptable range per [S2]; validated by Gate 0.2 success | P1 — IMU data path (all 6 IMU signals transit SDA) | IMU_SDA = P0.07 |
| R4 | 10k I2C pull-up (0402) — SCL | I2C bus pull-up for LSM6DS3TR-C SCL; same derivation as R3 | P1 — IMU clock path | IMU_SCL = P0.27 (NFC2 pin — configure as GPIO per toolchain_config.md caution) |
| J_TEMP | Temp Sensor 2-pin connector | External cable entry for NTC thermistor probe | P2 — outside_temp entry | ADC_TEMP path |

**Schematic net labels vs Signal Inventory:**

| Schematic net | Signals served | Domain primitive |
|---------------|----------------|-----------------|
| SDA | imu_accel_x/y/z, imu_gyro_x/y/z (I2C bus) | P1 |
| ADC_CT | ct_current_rms | P1 |
| ADC_TEMP | outside_temp | P2 |
| PDM_DATA | microphone | P1 — on-board XIAO routing; no external net (see Debate Point 4) |

No schematic net carries a signal absent from the Signal Inventory.

**BOM record obligation (Amendment 9):** `docs/device_context.md` BOM section must be
populated with the 10-component table above by the human engineer before the Stage 2
gate opens. This is a condition of enactment.

---

### Part B — Retroactive authorization of src/kicad_integration.py

`src/kicad_integration.py` is retroactively authorized as a project pipeline module
providing Signal Inventory and BOM governance traceability for the ComfortSense schematic.

**Constitutional classification:** NOT one of the Amendment 11 frozen scaffold trio
(`src/events.py`, `src/analysis.py`, `src/plot.py`). The First Scaffold Authorization
SOR (case_law.md, 2026-04-27) explicitly excludes project source from the Amendment 11
freeze. `src/kicad_integration.py` is project source: not generated by `/toolchain scaffold`,
not a UART event parser, not an analysis module.

**Module functions:**
- `check_signal_inventory(sch_path)` — cross-checks Signal Inventory against schematic nets; returns Markdown report
- `bom_vs_device_context(sch_path)` — compares schematic BOM against `docs/device_context.md` BOM table; returns Markdown diff

**SIGNAL_TO_NET correction required upon enactment:**

The committed `SIGNAL_TO_NET` maps to pin-map names (`CT_CURRENT`, `OUTSIDE_TEMP`,
`IMU_SDA`) that do not appear as net labels in the schematic. The schematic uses
`ADC_CT`, `ADC_TEMP`, `SDA`. As a result `check_signal_inventory()` reports MISSING
for every signal as committed. The correction (lines 35–45):

```python
# Old (committed — incorrect, does not match schematic net labels):
SIGNAL_TO_NET = {
    "imu_accel_x":    "IMU_SDA",
    "imu_accel_y":    "IMU_SDA",
    "imu_accel_z":    "IMU_SDA",
    "imu_gyro_x":     "IMU_SDA",
    "imu_gyro_y":     "IMU_SDA",
    "imu_gyro_z":     "IMU_SDA",
    "ct_current_rms": "CT_CURRENT",
    "outside_temp":   "OUTSIDE_TEMP",
    "microphone":     "PDM_DATA",
}

# New (correct — matches hardware/comfortsense.kicad_sch rev 0.1 net labels):
SIGNAL_TO_NET = {
    "imu_accel_x":    "SDA",
    "imu_accel_y":    "SDA",
    "imu_accel_z":    "SDA",
    "imu_gyro_x":     "SDA",
    "imu_gyro_y":     "SDA",
    "imu_gyro_z":     "SDA",
    "ct_current_rms": "ADC_CT",
    "outside_temp":   "ADC_TEMP",
    "microphone":     "PDM_DATA",   # correctly MISSING — on-board routing, see Debate Point 4
}
```

Re-scaffold required: NO. No change to Signal Inventory or Firmware UART Format.
Amendment 11 is not triggered. The three frozen scaffold files are unaffected.

---

## Article / Amendment Grounding

- **Article II — Human in the Loop:** Hardware files and `src/kicad_integration.py` were
  committed without an enacted Bill. This Bill retroactively supplies the required human
  decision gate.

- **Amendment 2 — Stage Gate Order (RATIFIED 2026-04-20):** Stage 1 CLOSED. Stage 2 not
  yet open. The schematic is Stage 2 preparation in the inter-stage window. It commits no
  firmware, no threshold, and no code beyond a read-only reporting utility. Amendment 2
  prohibits opening Stage N+1 while Stage N has open failures — Stage 1 has none.

- **Amendment 9 — Hardware Optimization Transparency (RATIFIED 2026-04-27):** The schematic
  resolves CT1 = SCT-013-000 ("Current clamp — TBD") and introduces TH1 = NTC 10k as a
  deviation from the planned DS18B20 OneWire. Both require explicit human authorization and
  BOM record population in `docs/device_context.md`.

- **Amendment 11 — Scaffold Immutability (RATIFIED 2026-04-27):** Confirms
  `src/kicad_integration.py` is project source, not a frozen scaffold module. Does not
  block this Bill.

---

## Physical Evidence

1. **Gate 0.2 PASS (2026-04-20)** — WHO_AM_I = 0x6A confirmed on I2C Fast Mode 400 kHz.
   Grounds R3 = R4 = 10k pull-ups (within LSM6DS3TR-C [S2] acceptable range).

2. **Gate 0.3 PASS (2026-04-20)** — toolchain_config.md pin map caution: "CT sensor analog
   out requires anti-alias filter + DC bias network." Grounds R1 = 68 Ω + C1 = 100 nF.

3. **Signal Measurements (2026-04-27) + Bill 1 constants** — I0_HEATING = 4 A, I0_COOLING
   = 9 A. At SCT-013-000 ratio 1:2000: V_CT_heating = 0.136 V rms, V_CT_cooling = 0.306 V
   rms. Both ≥169 ADC counts above noise floor. Grounds R1 = 68 Ω as minimum adequate
   burden resistor for enacted I0 constants.

4. **Amendment 1 P2 temperature range** — outside_temp normal −30 to +45 °C. NTC B=3950
   curve: 2810 ADC counts across the P2 range; ≥600 counts between T_COLD_SHOULDER (5 °C)
   and T_WARM_SHOULDER (15 °C). Grounds R2 = 10k as adequate for Bills 2-A / 2-B.

5. **toolchain_config.md Pin Map (2026-04-20)** — CT_CURRENT = P0.28, OUTSIDE_TEMP = P0.29,
   IMU_SDA = P0.07, IMU_SCL = P0.27. All four signals appear in J1/J2 header connections
   in the schematic.

---

## Expected Outcome

- **After SIGNAL_TO_NET correction:** `check_signal_inventory()` returns FOUND for 8 of 9
  Signal Inventory signals; MISSING for microphone (correct — on-board routing).
- **After BOM table population:** `bom_vs_device_context()` transitions from all-MISSING to
  PASS state. Amendment 9 obligation satisfied.
- **Article II compliance:** Police violations from commit `acddbff` resolved.
- **Stage 2 readiness:** Schematic provides the hardware reference for firmware pin
  assignments, ADC configurations, and signal conditioning parameters.

---

## Rollback Plan

No physical hardware has been fabricated. `git revert acddbff` removes all five files in
a single atomic commit. No downstream module imports `src/kicad_integration.py`. The
Stage 1 analysis pipeline is unaffected.

---

## Pre-Flagged Debate Points

*Points 1, 2, and 4 are assessed as uncontested. Point 3 requires an explicit Justice ruling.*

**Debate Point 1 — Is src/kicad_integration.py subject to Amendment 11 freeze?**
No. Amendment 11 names exactly three files. The First Scaffold Authorization SOR
explicitly carves out project source from the freeze on the same grounds that apply here.
**Drafter assessment: uncontested.**

**Debate Point 2 — SIGNAL_TO_NET mismatch: function non-operational as committed.**
The correction (Part B) is a labeling fix — net names from the schematic replace pin-map
names. No new signal, constant, or architecture is introduced. The correct net labels are
mechanically readable from the schematic.
**Drafter assessment: uncontested.**

**Debate Point 3 — NTC thermistor vs DS18B20 OneWire: requires Justice ruling.**
`toolchain_config.md` specifies DS18B20 OneWire for OUTSIDE_TEMP. The schematic uses
NTC 10k + R2 voltage divider. Both serve P2. The choice determines Stage 2 firmware
architecture (ADC + Steinhart-Hart vs OneWire + DallasTemperature library).

- **Option A — Accept NTC:** Update `toolchain_config.md` OUTSIDE_TEMP pin map row
  (ADC, not OneWire; remove DS18B20 reference; remove OneWire/DallasTemperature from
  Library Manifest). Stage 2 firmware reads ADC on P0.29.
- **Option B — Reinstate DS18B20:** Reject NTC. New schematic revision replaces TH1 + R2
  with DS18B20 connector + 4.7 kΩ pull-up. All other components in this Bill authorized;
  temperature sub-circuit deferred to schematic rev 0.2 Bill.

**Justice must choose Option A or Option B.**

**Debate Point 4 — microphone MISSING from schematic: correct, not a defect.**
MSM261D3526H1CPM is on-board the XIAO module; PDM pins are internally routed by Seeed.
PDM_DATA correctly reports MISSING from the host PCB schematic. The microphone remains
a fully enumerated Signal Inventory signal and P1 domain primitive.
**Drafter assessment: uncontested. Optional: update SIGNAL_TO_NET comment to state this
explicitly (comment-only, no code change required).**

---

**Enacted bill:** Bill 5 — Retroactive Authorization Stage 2 KiCad Schematic + Signal Traceability Module (`docs/governance/bills/stage2-schematic.md`)
**Justice's ruling on Debate Point 3:** Option B. DS18B20 OneWire is reinstated as the outside_temp sensing architecture. The NTC sub-circuit (TH1 + R2 + J_TEMP) in schematic rev 0.1 is **not authorized**. A schematic rev 0.2 is required before Stage 2 gate, replacing TH1 + R2 with a DS18B20 connector and 4.7 kΩ pull-up to 3V3. `toolchain_config.md` OUTSIDE_TEMP pin map row is unchanged (OneWire, DS18B20). `SIGNAL_TO_NET["outside_temp"]` maps to `"OUTSIDE_TEMP"` (no authorized net in rev 0.1 — correctly MISSING until rev 0.2).
**Context:** The human engineer stated the schematic work was exploratory Stage 2 smoke-test preparation, not a final production design. This is consistent with Option B — rev 0.1 establishes the non-temperature signal paths; rev 0.2 completes the design.
**Implementation branch:** schematics (already committed)
