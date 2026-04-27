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
| 2026-04-20 | Pre-Stage 0 | Toolchain bring-up (Option A from /toolchain init session) | `/tmp/xiao_smoke/xiao_smoke.ino` — Serial + tick loop, no IMU, no PDM | Compile: 43044 B flash (5%), 7144 B RAM (3%). Upload: "Device programmed", port re-enumerated. UART at 115200 baud: 7 consecutive `tick <ms>` lines at 1s intervals, counter 74000→80000 monotonic, no boot-loop pattern. | PASS | Closes E5. Toolchain path validated: `arduino-cli compile --fqbn Seeeduino:nrf52:xiaonRF52840Sense` → `.elf`/`.hex`/`.zip` at `build/arduino/xiaonRF52840Sense/` → `arduino-cli upload` via adafruit-nrfutil DFU over CDC → clean run. Case 1 Condition 1a (`Adafruit_TinyUSB.h` include) verified required: compile without it failed with `undefined reference to 'Serial'`; compile with it succeeded. |
| 2026-04-20 | 0 | Gate 0.1 — Counter smoke test (formal acceptance) | `/tmp/xiao_smoke/xiao_smoke.ino` — same run as pre-Stage-0 toolchain bring-up above | As recorded above. Counter increments without resets at 1 Hz; build→flash→run→observe loop proven end-to-end. | PASS | Gate 0.1 closed. Pre-Stage-0 toolchain bring-up run formally accepted as Smoke Test 1 evidence per /session 0 Gate 0.1 criteria: counter advances, no resets, serial at 115200 8N1 readable. |
| 2026-04-20 | 0 | Gate 0.2 — Sensor readout (LSM6DS3TR-C IMU) | `firmware/stage0_sensor/stage0_sensor.ino` — powers IMU via `PIN_LSM6DS3TR_C_POWER`, waits 50 ms per [S2 Table 3], I2C init via `Seeed Arduino LSM6DS3` v2.0.5, prints `WHO_AM_I` then raw accel (g) + gyro (dps) at 1 Hz | Compile: 51368 B flash (6%), 7688 B RAM (3%). Upload: "Device programmed", clean re-enumeration. UART capture (8 s, fast-retry serial open): setup banner OK (`IMU_POWER HIGH, waited ms=50` / `IMU_INIT: OK` / `WHO_AM_I: 0x6A` / `WHO_AM_I: PASS`), 9 READING lines at 1 Hz. Accel magnitude `√(0.075² + 0.311² + 0.975²) = 1.03 g` ≈ gravity ✓. Gyro bias ~2 dps (within typical LSM6DS3 spec, not saturated) ✓. Units correct (g for accel, dps for gyro) ✓. First sample (ts=1841) partial (`ax=0.000, az=0.445`) as expected while FIFO primes. | PASS | Gate 0.2 closed. Library `Seeed Arduino LSM6DS3` pinned at v2.0.5 in `docs/toolchain_config.md` Library Manifest. IMU power sequencing verified: datasheet-compliant 50 ms delay before first I2C read (Case 1 Condition 1a TinyUSB include also verified — Serial CDC active). No Article I thresholds introduced in this firmware (raw-readout only, no detection logic). |
| 2026-04-20 | 0 | Gate 0.3 — Algorithm over USB (sensor → algorithm → UART) | `firmware/stage0_algo_usb/stage0_algo_usb.ino` — 100 Hz accel sampling (LSM6DS3 ODR=104 Hz nearest), 500 ms sliding window (50 samples), RMS of accel magnitude √(ax²+ay²+az²), METRIC line emitted at 2 Hz. No detection threshold (Stage 0 liveness only, per Article I sketch-header note). | Compile: 50608 B flash (6%), 7904 B RAM (3%). Upload: "Device programmed" via `arduino-cli upload` over DFU, port re-enumerated at /dev/cu.usbmodem14301. Three consecutive UART captures at 115200 8N1: (1) stationary, 31 METRIC lines over 15 s, rms_g ∈ [1.0014, 1.0056] ≈ gravity + sensor noise ✓; (2) gentle-move, 39 METRIC lines, rms_g ∈ [1.0033, 1.0074] — within noise band, rejected as insufficient separation; (3) vigorous-move (continuous shake / lift), 34 METRIC lines, rms_g ∈ [1.0228, 2.0154] — min 0.017 g above stationary max, peak at ±2g sensor ceiling, clean zero-when-should-be-nonzero trap clearance. Device uptime monotonic across all three captures (292 s → 1427 s), no resets observed. | PASS | Gate 0.3 closed. Sensor → algorithm → UART pipeline proven end-to-end. Police Warning W-Gate0.3-A1 (REPORT_PERIOD_MS citation) resolved inline before flash — see case_law.md Standing Order Record (2026-04-20). Article II flash approval granted by Justice ("flash") 2026-04-20. Gate 0.3 PASS requires TWO conditions in the same firmware: (a) stationary baseline near 1 g gravity, (b) motion response measurably above stationary noise band. Both satisfied. Note: 500 ms sliding RMS of |a| is a crude liveness metric — it rejects gentle tilt (gravity-only motion). For Stage 1 algorithm work, a gravity-subtracted or high-passed variant will be required; that is Bill-governed work, out of Stage 0 scope. |
| 2026-04-20 | 0 | Gate 0.4 — Algorithm over Wireless (BLE NUS transport) | `firmware/stage0_algo_ble/stage0_algo_ble.ino` — algorithm identical to Gate 0.3 sketch (100 Hz accel sampling, 500 ms sliding RMS window, 2 Hz METRIC emission). Adds Bluefruit52 BLE stack: advertises as "ComfortSense", Nordic UART Service (UUIDs 6E400001/2/3-B5A3-F393-E0A9-E50E24DCCA9E), NUS UUID in ADV packet + device name in scan response (Seeed known-issue guard against name truncation), `Bluefruit.configPrphBandwidth(BANDWIDTH_MAX)` before `Bluefruit.begin()` and `Bluefruit.Periph.setConnInterval(6, 24)` (7.5–30 ms conn interval) for throughput, `bleuart.write` called unconditionally (not gated on connected()), METRIC line mirrored to USB Serial for parity. | Compile: 125296 B flash (15%), 14732 B RAM (6%). Two flash attempts: (1) first flash without bandwidth config — BLE NUS discovered + subscribed correctly, but only 23 of 34 bytes per METRIC line delivered (MTU=23, `bleuart.write` silently dropped tail) — diagnostic script `/tmp/gate04_ble_diag.py` recorded the 20+3 byte split pattern; rejected as Article I transport-integrity failure. (2) Second flash after adding `configPrphBandwidth(BANDWIDTH_MAX)` + `setConnInterval(6, 24)` — clean reassembly. Vigorous-motion dual-capture 25 s (`/tmp/gate04_dual_capture.py` — BLE via `BleConsole(device_name='ComfortSense')` + serial concurrent capture): USB 51 lines rms_g ∈ [1.02, 2.46], BLE 46 lines rms_g ∈ [1.38, 2.46] (fewer lines = BLE scan/connect pre-roll, not drop). Byte-for-byte parity in overlap window across full dynamic range — four spot-checks at ts=308181/315181/322181/327681 all match to 4 decimal places between USB and BLE. Peak 2.46 g = ±2g sensor saturation under vigorous shake, matches Gate 0.3 vigorous-motion ceiling. Gentle-motion 40 s capture recorded separately (BLE 75 lines / USB 81 lines, all matching) for the transport liveness record. | PASS | Gate 0.4 closed. Stage 0 CLOSED subject to stage-compactor freeze + `/toolchain lock`. Article II flash approvals granted by Justice twice ("flash" 2026-04-20) — first for initial BLE sketch, second for bandwidth-fix rebuild. All four /session 0 Gate 0.4 failure modes cleared: (a) name not truncated in ADV (name in ScanResponse); (b) data flows post-connect (unconditional write); (c) lines not fragmented on host (MTU throughput sufficient); (d) host receives same algorithm output matching device serial byte-for-byte. Transport primitive established — wireless path from device → ComfortSense BLE peripheral → macOS CoreBluetooth → bleak → BleConsole → host-stdout is end-to-end validated. Gap recorded for Stage 0 closeout: `crucible/transport/ble.py` has no `__main__` CLI so the documented `python crucible/transport/ble.py --device ComfortSense` command in `docs/toolchain_config.md` won't run standalone; Gate 0.4 used inline `asyncio.run(BleConsole('ComfortSense').run())`. CLI gap → Bill follow-up (touches `crucible/` infrastructure, not Standing Order). |

### Signal measurements (evidence pool)

> Discrete measurements cited in case law or Bills. Each entry must name the file
> and the physical quantity it supports.

| Date | Signal | Value | File / log | Physical quantity |
|------|--------|-------|------------|-------------------|
| 2026-04-27 | filter_dp_ratio @ near_clog_heating, 1-sec windows (N=16 Monte Carlo, signal-only sim) | min 1.783 / mean 1.859 / max 1.959 (true 1.85) | `docs/plots/bill2b_regime_classifier.png`; commit 89694ab | P1 detection margin — alert edge (1.8) grazed under short-window noise; min sample under-reads into no-alert zone in heating regime |
| 2026-04-27 | filter_dp_ratio @ past_clog_heating, 1-sec windows (N=16) | min 1.878 / mean 1.998 / max 2.089 (true 2.00) | `docs/plots/bill2b_regime_classifier.png`; commit 89694ab | P1 detection margin — clear alert in all 16 chunks |
| 2026-04-27 | algorithm output spread (max−min), heating vs cooling regimes, 1-sec windows | heating spread 0.13–0.21; cooling spread 0.07–0.11 | `docs/plots/bill2b_regime_classifier.png`; commit 89694ab | P1 noise sensitivity — heating regime ≈ 1.7× higher spread than cooling because I0_HEATING (4 A) is half I0_COOLING (9 A), making the 0.05 A CT Gaussian noise relatively larger; informs Bill 2-D W_VIB derivation |

### Open anomalies

> Issues observed but not yet explained or resolved. An attorney may cite an open
> anomaly as evidence that a position is unsafe — it has the same weight as a
> confirmed measurement.

| Date observed | Description | Stage | Status |
|---------------|-------------|-------|--------|
| Pre-2026-04-19 (exact date unknown) | E5 — Boot-loop anomaly on XIAO nRF52840 Sense under PlatformIO. A prior `pio run` + flash attempt on this board produced corrupted firmware; board entered reboot loop. Colleague resolved the issue by unknown means; resolution not recorded. Failure mode consistent with incorrect memory map, linker script, or bootloader offset from a mismatched platform/board definition (specifically: `xiaoblesense` board ID not present in stock `nordicnrf52` platform — confirmed by `pio boards nrf52` on 2026-04-19). | Spec Gate → Stage 0 pre-flash | **RESOLVED 2026-04-20.** First flash under the enacted arduino-cli toolchain (Seeeduino:nrf52 v1.1.12, FQBN `Seeeduino:nrf52:xiaonRF52840Sense`) succeeded: `arduino-cli upload` via adafruit-nrfutil DFU over CDC completed with "Device programmed"; port re-enumerated cleanly at `/dev/cu.usbmodem14301`; firmware ran stably (7 consecutive 1-second tick events captured 74–80s after upload, monotonic counter, no reset pattern). Closure confirms Case 1 + Case 1.1 ruling: the prior PlatformIO boot-loop was specific to the PlatformIO platform class (now blocked) and does not affect the arduino-cli path. See Test Results Field / HIL test log entry below. |

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
