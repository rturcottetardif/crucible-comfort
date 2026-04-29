# Bill 4 — Stage 1 Algorithm Firmware + ALERT UART Event

**Stage:** 1 (Simulation)
**Status:** ENACTED (2026-04-29, Case 7 — Justice direct acceptance)
**Branch:** `stage1/firmware`

---

## 1. Motivation

Stage 1 exit criteria require at least one Renode (Path B) run to validate that the
C firmware implementation agrees with the Python algorithm model. No Stage 1 firmware
exists yet. This Bill creates it and defines the ALERT UART event it emits, which
requires extending the scaffold trio (Amendment 11 Bill requirement).

---

## 2. Changes

### 2a. docs/toolchain_config.md — add ALERT event definition
New `[[event]]` block added to Firmware UART Format section.

### 2b. src/events.py — add AlertEvent (Amendment 11 Bill required)
New `AlertEvent` dataclass: ts_ms (int), dp_ratio (float), regime (str), alert (bool).

### 2c. src/analysis.py — add ALERT_DEF and extend PARSER (Amendment 11 Bill required)
New `ALERT_DEF` EventDefinition; PARSER updated to include it alongside READING and METRIC.

### 2d. firmware/stage1_algo_usb/stage1_algo_usb.ino — Stage 1 algorithm firmware
Two build targets via conditional compilation:

| Target | Build flag | IMU source | UART |
|---|---|---|---|
| Real hardware | (none) | LSM6DS3TR-C at 1660 Hz via I2C | USB CDC (`Serial`) |
| Renode sim | `-DCONFIG_CRUCIBLE_RENODE_SIM` | Virtual stub at 0x400B0000 | UARTE0 (`Serial1`) |

---

## 3. ALERT UART event

Format: `ALERT ts=<ms> dp=<float> regime=<str> alert=<0|1>`

Example: `ALERT ts=1001 dp=1.8510 regime=cooling alert=1`

- `ts`     — firmware `millis()` at emission
- `dp`     — filter_dp_ratio (ΔP/ΔP₀), 4 decimal places
- `regime` — hvac_regime: "cooling" (IMU-only default, Bill 2-A Case 3 conservative bias)
- `alert`  — 1 if dp_ratio ≥ 1.8 (Amendment 1 P1 alert window low edge), else 0

Emitted once per 1660-sample window (~1 Hz at 1660 Hz ODR).

---

## 4. Firmware algorithm constants (Article I)

All constants trace to Amendment 1 P1 (Filter ΔP) via Bills 1–3:

| Constant | Value | Trace |
|---|---|---|
| `A_Z_DC` | 1.0 g | Gate 0.2 gravity reference; Bill 1 Case 2 |
| `A_FUND_CLEAN` | 0.05 g | Clean-filter amplitude; Bill 1 Case 2 |
| `ALPHA` | 1.0 | ΔP exponent; Bill 1 Case 2 |
| `RMS_HARM_FACTOR` | 0.7546 | √(0.5·(1+1/9+1/36)); analytic, Case 3 |
| `ALERT_THRESH` | 1.8 | Amendment 1 P1 alert window low edge |
| `N_WINDOW` | 1660 | IMU ODR × 1 sec; Signal Inventory |

**ALPHA=1 simplification:** dp_ratio = rms_ac / (A_FUND_CLEAN × RMS_HARM_FACTOR).
The `powf(x, 1/ALPHA)` reduces to the identity for ALPHA=1. If Stage 2/3 field
calibration yields ALPHA ≠ 1, this line must be updated via a Bill.

---

## 5. Renode path (sim mode)

Virtual IMU peripheral (sim_imu_stub.py) at 0x400B0000:
- STATUS at offset 0x00 (uint32 LE): 1 = sample ready, 0 = exhausted
- Sample data at offsets 0x04–0x1B: 6 × float32 LE [ax ay az gx gy gz]
- ACK at offset 0x1C: write any value to advance to next sample

Firmware reads az (3rd float, offset 0x0C from data start) each loop, ACKs, and
accumulates into window buffer. When STATUS=0, emits SESSION_END and halts.

UART output captured by sim_uart_stub.py at 0x40002000 (UARTE0). Firmware uses
`Serial1` (hardware UART → UARTE0) in sim mode; `Serial` (USB CDC) in real mode.

---

## 6. Pre-flagged debate points

1. **Serial1 → UARTE0 mapping.** The Seeed nRF52 Arduino core maps `Serial1` to
   hardware UART on UARTE0 (0x40002000), which the sim_uart_stub intercepts. If
   the core maps Serial1 to UARTE1 (0x40028000) instead, the Renode UART output
   will be empty. This is a Stage 1 finding falsifiable by the first Renode run.

2. **CT absent in Renode path.** The RenoneBridge injects N×6 IMU samples only.
   No CT signal injection exists. The firmware therefore uses the IMU-only
   (vibration-only) path with regime="cooling" default (Bill 2-A, Case 3).
   Parity check compares dp_ratio_vib between Python model and firmware. CT
   fusion (W_VIB_HEATING/W_VIB_COOLING) is validated by Path A only.

3. **ALPHA=1 identity substitution.** dp_ratio = rms_ac / denominator (no powf)
   is not a new constant — it is an analytic simplification of the Bill 1 formula
   at ALPHA=1. Not subject to Amendment 7 one-per-Bill ceiling.

4. **events.py and analysis.py modification under Amendment 11.** Stage 1 gate
   is not yet closed, so the scaffold trio is not yet frozen per Amendment 11's
   "once the stage's Justice Gate is signed off" clause. This Bill is the required
   explicit authorization for modifying the scaffold-generated files before gate.

---

## 7. Zero-regression guarantee

AlertEvent is additive — it extends the PARSER's event_definitions list without
removing READING_DEF or METRIC_DEF. Existing READING and METRIC parsing is
unchanged. All existing Path A regression profiles (8/8 PASS, 2026-04-29) are
unaffected.
