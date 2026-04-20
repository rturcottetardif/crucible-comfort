# Device Context — RAG Evidence Base

This file is the primary evidence document for all agents operating under the
Crucible Constitutional Governance system. It is read by attorneys before
constructing hearing arguments, by the hw-advisor before making suggestions,
and by the simulator-operator when validating simulation parameters against
known hardware behaviour.

**Agents: read this file before any hearing argument or advisory session.**  
**Humans: keep this file current. A stale BOM or outdated test result here is
a constitutional violation under Article I (Signal First).**

Maintained by: human engineer (primary) + `/toolchain` command (hardware/pin sections).  
Updated after: every field test session, every BOM revision, every schematic change.

---

## Device Purpose

ComfortSense alerts the maintenance team of a commercial packaged rooftop HVAC
unit when the air filter needs to be replaced. The maintenance team's filter-swap
decision depends on the alert: if the device fires too early (false positive),
filters are replaced prematurely, increasing cost to the maintenance company and
generating environmental waste from discarded filters; if the device fires too
late or not at all (false negative), an undetected clog damages HVAC components,
transfers cost to the client, and harms the maintenance company's reputation.
The hardest scenario is **seasonal regime change**: the inference from indirect
signals (vibration, acoustic, motor current) to filter pressure drop depends on
whether the HVAC is in heating or cooling mode — a naive model tuned on one
regime will misread filter state in the other. The device must perform correctly
in both heating (winter) and cooling (summer) regimes across Canadian year-round
rooftop conditions.

**Project target:** Detect the filter-replacement point on a commercial packaged
rooftop HVAC unit in both heating (winter) and cooling (summer) regimes, using
indirect sensing only (no in-line pressure sensor).

**Pass/fail threshold:** The alert must fire when filter ΔP reaches
1.8 × ΔP₀ to 1.9 × ΔP₀ (80–90 % of the clog point, where clog point = 2 × ΔP₀
and ΔP₀ is the installed-new baseline pressure drop). Validated against a
reference pressure measurement in both heating and cooling regimes.

**Domain primitives** (traces to Article I):
1. **Filter ΔP** (Pa) — pressure drop across the HVAC filter; inferred indirectly.
   Measured via: IMU 6-channel (vibration), microphone (acoustic turbulence),
   CT current (blower motor RMS current).
2. **HVAC operating regime** (categorical: heating / cooling / off) —
   thermodynamic mode of the HVAC; conditioning variable for the Filter ΔP
   inference.
   Measured via: outside thermometer.

**Operating envelope:**
- **Normal:** Device mounted on the side of a commercial packaged rooftop HVAC
  unit housing. Ambient: Canadian year-round (≈ −40 °C to +35 °C air; 0–100 %
  RH with condensation and freeze-thaw cycling; rooftop surface temp up to
  ~+60 °C under summer solar loading). Monitoring continuous; result transmission
  every hour; duty cycle matches HVAC runtime (signals valid only when HVAC is
  active).
- **Worst-case:** High wind (rooftop wind shake adds non-HVAC vibration and wind
  noise to IMU and microphone — algorithm must not mistake wind for fan load);
  abnormal dust load (wildfire smoke, dust storms → filter ΔP rises on a
  timescale of hours rather than weeks — algorithm must track rapid-onset
  clogging). Cold soak, peak heat, ice, and extended runtime deferred to a
  later envelope revision.
- **Out-of-scope:** Mounting locations other than the side of the housing (top,
  indoor, inside-duct); HVAC failure modes other than filter clog — ComfortSense
  does not detect and must not claim to detect bearing wear, belt slip, coil
  icing, refrigerant leak, or motor-winding fault.

---

## Signal Inventory

| Signal | Physical quantity | Unit | Normal range | Hard limits | Sample rate | Primitive |
|--------|-------------------|------|--------------|-------------|-------------|-----------|
| imu_accel_x | Linear acceleration (X-axis), HVAC housing | g | ±2 g | saturate at ±2 g | 1.66 kHz | P1 |
| imu_accel_y | Linear acceleration (Y-axis), HVAC housing | g | ±2 g | saturate at ±2 g | 1.66 kHz | P1 |
| imu_accel_z | Linear acceleration (Z-axis), HVAC housing | g | ±2 g | saturate at ±2 g | 1.66 kHz | P1 |
| imu_gyro_x  | Angular velocity (X-axis), HVAC housing    | °/s | ±250 dps | saturate at ±250 dps | 1.66 kHz | P1 |
| imu_gyro_y  | Angular velocity (Y-axis), HVAC housing    | °/s | ±250 dps | saturate at ±250 dps | 1.66 kHz | P1 |
| imu_gyro_z  | Angular velocity (Z-axis), HVAC housing    | °/s | ±250 dps | saturate at ±250 dps | 1.66 kHz | P1 |
| microphone  | Acoustic pressure (airflow / blower signature) | dBSPL | 40–70 dBSPL | clip ≥ ~120 dBSPL; silence < 30 dBSPL (disconnect) | 16 kHz | P1 |
| outside_temp | Outdoor ambient air temperature           | °C  | −30 to +45 °C | fault < −40 °C or > +60 °C; stuck value over long window | 1/60 Hz (≈ 0.0167 Hz) | P2 |
| ct_current_rms | AC current draw, HVAC blower motor (60 Hz, derived RMS-to-DC) | A RMS | 2–15 A RMS | < 0.3 A (fan off); > 25 A (saturation / stall) | 1 Hz | P1 |

**Primitive key:**
- **P1** = Filter ΔP
- **P2** = HVAC operating regime

**Baseline calibration required:** ΔP₀ (installed-new filter baseline) and clean-filter
vibration/acoustic/current signatures must be empirically established per deployment
during Stage 1 simulation and Stage 2 HIL.

---

## Bill of Materials (BOM)

> Component-level record. Every component that touches a domain primitive must be here.
> Include part number, value/spec, supplier, and any substitution notes.
> Delete this instruction block and replace with your actual BOM.

| Ref | Component | Part Number | Value / Spec | Supplier | Notes |
|-----|-----------|-------------|--------------|----------|-------|
| U1  | [MCU board] | — | — | — | [e.g., must be Sense variant] |
| U2  | [Sensor] | — | [I2C addr, ODR, range] | — | — |
| R1  | [Resistor] | — | [Ω, tolerance, power] | — | — |
| C1  | [Capacitor] | — | [μF, voltage] | — | — |
| J1  | [Connector] | — | — | — | — |

**BOM revision:** [vX.Y — YYYY-MM-DD]  
**Known substitution constraints:**  
- [e.g., "U2: LSM6DS3TR-C only — LSM6DSO has different WHO_AM_I and I2C timing"]

---

## Circuit Notes

> Key connections, power rail topology, and any physical issues found during bring-up.
> Include anything an attorney might need to argue a signal-path or power-budget hearing.

### Power topology
- [e.g., "3.3V from on-board LDO via P1.08 software-switched power pin"]
- [e.g., "Battery: 3.7V Li-Po → USB-C charging via onboard PMIC"]

### Key signal paths
- [e.g., "IMU: I2C on SDA=P0.07 / SCL=P0.27, address 0x6A, INT1=P0.11"]
- [e.g., "LED RGB: P0.26 (red), P0.30 (green), P0.06 (blue) — active LOW"]

### Known circuit issues
- [e.g., "P0.27 is also the NFC antenna pin — configure as GPIO before use"]
- [e.g., "IMU power pin must be asserted HIGH ≥ 5ms before first I2C transaction"]

**Schematic revision:** [vX.Y — YYYY-MM-DD]  
**Schematic file:** [path or URL, or "not yet committed"]

---

## Test Results

> Structured record of every validation run. Agents cite entries here by date and type
> when making empirical arguments. An argument citing a test result not in this record
> is inadmissible under the Benjamin Franklin Principle.

### Field / HIL test log

| Date | Stage | Test type | Profile / scenario | Key measurement | Pass/Fail | Notes |
|------|-------|-----------|-------------------|-----------------|-----------|-------|
| YYYY-MM-DD | 0 | HIL smoke | USB serial | [e.g., counter=100 ✓] | PASS | — |
| YYYY-MM-DD | 0 | HIL smoke | IMU I2C | [e.g., WHO_AM_I=0x6A ✓] | PASS | — |
| YYYY-MM-DD | 1 | Simulation | [profile] | [e.g., steps=100, SI=2.1%] | PASS | — |
| YYYY-MM-DD | 2 | Firmware | [scenario] | [e.g., SESSION_END in 18s] | PASS | — |

### Signal measurements (evidence pool)

> Discrete measurements cited in case law or Bills. Each entry must name the file
> and the physical quantity it supports.

| Date | Signal | Value | File / log | Physical quantity |
|------|--------|-------|------------|-------------------|
| YYYY-MM-DD | [e.g., gyr_y peak] | [e.g., 38.4 dps] | [log path] | [e.g., push-off angular velocity] |
| YYYY-MM-DD | [e.g., SI_interval] | [e.g., 2.3%] | [log path] | [e.g., bilateral symmetry] |

### Open anomalies

> Issues observed but not yet explained or resolved. An attorney may cite an open
> anomaly as evidence that a position is unsafe — it has the same weight as a
> confirmed measurement.

| Date observed | Description | Stage | Status |
|---------------|-------------|-------|--------|
| Pre-2026-04-19 (exact date unknown) | E5 — Boot-loop anomaly on XIAO nRF52840 Sense under PlatformIO. A prior `pio run` + flash attempt on this board produced corrupted firmware; board entered reboot loop. Colleague resolved the issue by unknown means; resolution not recorded. Failure mode consistent with incorrect memory map, linker script, or bootloader offset from a mismatched platform/board definition (specifically: `xiaoblesense` board ID not present in stock `nordicnrf52` platform — confirmed by `pio boards nrf52` on 2026-04-19). | Spec Gate → Stage 0 pre-flash | OPEN — superseded by Case 1 ruling (2026-04-19). PlatformIO blocked for this project. Mark resolved only after first clean flash under arduino-cli succeeds with no boot-loop recurrence on `/dev/cu.usbmodem14301` at 115200 baud. |

---

## Hardware Bring-up History

> Chronological record of significant hardware events: new revisions, failures,
> component swaps, and the reason for each. Attorneys use this to establish whether
> a current anomaly has a hardware precedent.

| Date | Event | Impact | Action taken |
|------|-------|--------|--------------|
| 2026-04-19 | Seeed XIAO nRF52840 Sense (SKU 102010469) enumerated via USB-C on macOS 24.6.0. `pio device list` output: port `/dev/cu.usbmodem14301`, VID:PID `2886:8045`, description "XIAO nRF52840 Sense". | Board present and identified by OS — hardware is not the failure point for E5 boot-loop (cited in Case 1). | `/toolchain init` completed. Case 1 hearing (PlatformIO vs arduino-cli) ruled for Position B — arduino-cli + Seeed mbed core. |

---

## Agent Reading Guide

| Agent | Sections to read | Why |
|-------|-----------------|-----|
| Attorney-A / B | All | Full evidence base before constructing any argument |
| hw-advisor | Device Purpose, BOM, Circuit Notes, Open Anomalies | Grounds suggestions in actual hardware |
| simulator-operator | Signal Measurements, Test Results | Validates simulation output against known hardware |
| uart-reader | Test Results, Signal Measurements | Contextualises printed UART output |
| plotter | Domain Primitives, Signal Measurements | Ensures plot annotations use correct physical units and thresholds |
| stage-compactor | Test Results, Hardware Bring-up History | Verifies stage exit criteria before freezing precedents |
