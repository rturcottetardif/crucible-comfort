# Toolchain Configuration

> **Written and maintained by `/toolchain` commands only.**
> All agents read this file before taking any toolchain-dependent action.
> Human edits are permitted but must be followed by `/toolchain validate`.

---

## Lock Status

```
Status:  UNLOCKED
Locked:  —
Evidence: —
```

---

## Hardware

```
Board:    Seeed XIAO nRF52840 Sense 102010469
MCU:      nRF52840, ARM Cortex-M4F, 64 MHz
Sensors:  LSM6DS3TR-C IMU (I2C 0x6A, WHO_AM_I=0x6A, FS ±2g/±250dps, ODR up to 1.66 kHz) [S2]
          MSM261D3526H1CPM PDM microphone
External: Current clamp — TBD (feeds ct_current_rms signal)
          Thermometer — TBD, planned DS18B20 OneWire waterproof probe (feeds outside_temp signal)
Notes:    Must be Sense variant (SKU 102010469) — standard XIAO nRF52840 (SKU 102010448) has no
            onboard IMU or microphone. Physically identical — verify SKU on sticker before flashing.
          IMU powered via P1.08 (software-switched) — drive HIGH and wait ≥45 ms before first I2C read,
            or WHO_AM_I returns 0xFF/0x00 [S2 Table 3].
          P0.27 (IMU_SCL) and P0.09 are NFC antenna pins by default — must be reconfigured as GPIO
            before use (Arduino mbed core handles automatically; Zephyr/nRF SDK must disable NFCT) [S1].
          3.3 V LDO can brown out during BLE TX if Li-Po <3.5 V → causes mid-session IMU reset.
          USB-C CDC serial may take 2–5 s to re-enumerate after soft reset — not power cycle.
          I2C max speed: 400 kHz (Fast Mode). Flash: 1 MB internal + 2 MB QSPI; RAM: 256 KB.
          BLE 5.0, TX 8 dBm, RX −95 dBm. Supply: 3.3 V via onboard LDO (USB 5 V or Li-Po).
```

---

## Pin Map

| Signal | Arduino pin | nRF52840 port/pin | Function | Caution |
|--------|-------------|-------------------|----------|---------|
| IMU_SDA | 4 | P0.07 | I2C SDA (IMU) | — |
| IMU_SCL | 5 | P0.27 | I2C SCL (IMU) | P0.27 = NFC2 by default — configure as GPIO before use [S1] |
| IMU_POWER | — | P1.08 | IMU VCC software switch | Drive HIGH ≥45 ms before first I2C read [S2 Table 3] |
| IMU_INT1 | — | P0.11 | IMU interrupt (DRDY / FIFO watermark) | Required at 1.66 kHz ODR to avoid missed samples |
| PDM_CLK | — | via `PIN_PDM_CLK` in mbed_nano variant.h | PDM microphone clock | Pin fixed by on-board routing; use symbolic name while on Arduino mbed core |
| PDM_DATA | — | via `PIN_PDM_DIN` in mbed_nano variant.h | PDM microphone data | Pin fixed by on-board routing; use symbolic name while on Arduino mbed core |
| PDM_PWR | — | via `PIN_PDM_PWR` in mbed_nano variant.h | PDM microphone power | Pin fixed by on-board routing; use symbolic name while on Arduino mbed core |
| CT_CURRENT | 2 | P0.28 | ADC — CT sensor analog out (`ct_current_rms`) | Requires anti-alias filter + DC bias network on CT output |
| OUTSIDE_TEMP | 3 | P0.29 | OneWire data (DS18B20, `outside_temp`) | Needs 4.7 kΩ pull-up to 3V3; waterproof probe |
| LED_RED | — | P0.26 | RGB red | Active LOW |
| LED_GREEN | — | P0.30 | RGB green | Active LOW |
| LED_BLUE | — | P0.06 | RGB blue | Active LOW |
| LED_PWR | — | P0.13 | Charge indicator | Active LOW — do not drive |

---

## Active Firmware Toolchain

*Enacted by Case 1 (2026-04-19) with Condition 1 amended by Case 1.1 (2026-04-20).
See `docs/governance/case_law.md`. Ratified under Amendment 3 (Toolchain Alignment, 2026-04-19).*

```
Build:          arduino-cli 1.4.1 — core=Seeeduino:nrf52 v1.1.12 (Seeed nRF52 Boards)
                  Board index: https://files.seeedstudio.com/arduino/package_seeeduino_boards_index.json
                  FQBN: Seeeduino:nrf52:xiaonRF52840Sense
                    (verified 2026-04-20 via `arduino-cli board listall` — see Test Results in
                     docs/device_context.md for the verification command and output)
                  Build path (for Renode bridge compatibility — Case 1 Condition 7):
                    arduino-cli compile --fqbn Seeeduino:nrf52:xiaonRF52840Sense \
                      --build-path build/arduino/xiaonRF52840Sense/ <sketch_dir>
                    Produces: build/arduino/xiaonRF52840Sense/<sketch>.ino.elf (+ .bin / .uf2)
                  Sketch requirement (Case 1 Condition 1a, from Case 1.1): every project .ino
                    targeting this FQBN must include `#include "Adafruit_TinyUSB.h"` at the top
                    of the main sketch file. The Seeeduino:nrf52 core uses Adafruit TinyUSB for
                    USB CDC; omitting the include produces a linker error (`undefined reference
                    to Serial`) before flash. Enforced by code-reviewer at each stage gate.
                  Deprecated alternative (do NOT use): Seeeduino:mbed:xiaonRF52840Sense
                    (labelled "No Updates" by Seeed as of 2026-04-20 — frozen core).
Flash:          UF2 drag-drop — double-tap reset to mount XIAO-SENSE bootloader drive,
                  copy build/arduino/xiaonRF52840Sense/<sketch>.ino.uf2 to the mounted volume.
                  Alternative (programmatic): arduino-cli upload -p /dev/cu.usbmodem* \
                    --fqbn Seeeduino:nrf52:xiaonRF52840Sense <sketch_dir>
                    (requires board in bootloader mode — double-tap reset first).
Serial monitor: arduino-cli monitor -p /dev/cu.usbmodem* --config 115200,8,n,1
                  Fallback: python -m serial.tools.miniterm /dev/cu.usbmodem* 115200 8N1
Wireless recv:  python crucible/transport/ble.py --device ComfortSense
Simulation:     Renode 1.16 via crucible.sim.renode.RenoneBridge
                  Build-path adaptation (Case 1 Condition 7, pending follow-up Bill):
                    bridge must read ELF from build/arduino/xiaonRF52840Sense/<sketch>.ino.elf
                    (was .pio/build/<env>/firmware.elf under PlatformIO). Temporary hand-edit
                    permitted in project-local src/ only; do not edit crucible/ infrastructure
                    package without a Bill.
```

---

## Blocked Toolchains

- **2026-04-19 BLOCKED build: PlatformIO platform=nordicnrf52** — `xiaoblesense` board ID not
  present in stock PlatformIO `nordicnrf52` platform. Evidence from /toolchain init session on
  2026-04-19: (a) `pio boards nrf52` returns only `adafruit_feather_nrf52840_sense` and
  `nicla_sense_me`; (b) `pio boards | grep xiao` returns SAMD21 and ESP32 XIAO variants only
  — no nRF52 XIAO variant under any stock platform; (c) PlatformIO Core 6.1.19 confirmed
  current, so the absence is not a stale-index issue. Additionally cited: **E5 boot-loop
  anomaly** — a prior PlatformIO flash attempt on this board produced corrupted firmware and
  a reboot loop (see `docs/device_context.md` Open Anomalies table). Blocked by **Case 1
  ruling** (docs/governance/case_law.md, 2026-04-19) under **Amendment 3 (Toolchain Alignment,
  ratified 2026-04-19)**. Unblocking requires a new Judicial Hearing per Amendment 3.

---

## Firmware UART Format

> **Required for `/toolchain scaffold`** — fill in before running Stage 1.
> This section defines what the firmware emits over UART. It is used to
> generate `src/analysis.py` (UART parser) and `src/events.py` (event types).
> NOT YET DEFINED — populate before Stage 1.

```
session_end_marker: SESSION_END
```

### Event Definitions

> One block per UART event type the firmware emits. Add blocks as needed.
> NOT YET DEFINED — populate before Stage 1.

### Binary Export Format (optional)

> Fill in only if firmware supports a binary bulk export over BLE or UART.
> NOT YET DEFINED.

---

## Library Manifest

| Library | Version | Source | Purpose | Known issues |
|---------|---------|--------|---------|--------------|
| Seeed Arduino LSM6DS3 | 2.0.5 (pinned 2026-04-20 at Gate 0.2 PASS) | Arduino Library Manager (Seeed Studio) — https://github.com/Seeed-Studio/Seeed_Arduino_LSM6DS3 | LSM6DS3TR-C IMU driver (accel + gyro) for P1 (Filter ΔP inference via vibration). Verified at Gate 0.2: `imu.begin()` returns 0, `WHO_AM_I=0x6A`, accel magnitude matches gravity ✓. | Known issue on `ARDUINO_ARCH_MBED` (patch LSM6DS3.cpp `setBitOrder()`) — does NOT apply under `Seeeduino:nrf52` v1.1.12 active core (non-mbed). Install: `arduino-cli lib install "Seeed Arduino LSM6DS3"@2.0.5` |
| OneWire | TBD — pin at first arduino-cli compile | Arduino Library Manager (Paul Stoffregen) | DS18B20 OneWire bus protocol for `outside_temp` (P2 regime proxy) | — |
| DallasTemperature | TBD — pin at first arduino-cli compile | Arduino Library Manager (Miles Burton) | DS18B20 high-level read API | Depends on OneWire — pin both to compatible versions |
| arduinoFFT | TBD — pin at first arduino-cli compile | Arduino Library Manager (Enrique Condes) | Spectral analysis for IMU / mic — optional, include only if on-device FFT chosen | Deferred decision: could run FFT host-side instead |

Bundled with the `Seeeduino:nrf52` v1.1.12 Arduino core — not recorded as separate library entries:
- `Adafruit_TinyUSB` — USB CDC / Serial stack (required `#include` per Case 1 Condition 1a)
- `PDM` — PDM microphone driver (on-board MSM261D3526H1CPM)
- `Bluefruit` / `bluefruit52` — BLE stack (Nordic SoftDevice wrapper)

**Installation commands (arduino-cli):**

```
# one-time: add Seeed board index (already done in this workspace, 2026-04-20)
arduino-cli config add board_manager.additional_urls \
  https://files.seeedstudio.com/arduino/package_seeeduino_boards_index.json
arduino-cli core update-index
arduino-cli core install Seeeduino:nrf52

# per-library (run after versions are pinned by /toolchain add lib):
arduino-cli lib install "Seeed Arduino LSM6DS3"@<version>
arduino-cli lib install "OneWire"@<version>
arduino-cli lib install "DallasTemperature"@<version>
arduino-cli lib install "arduinoFFT"@<version>
```

---

## Repository Registry

| Repo | Branch | Purpose | Notes |
|------|--------|---------|-------|
| `git@github.com:rturcottetardif/crucible-comfort.git` (local: `/Users/roxanneturcotte/CrucibleStudio/crucible-comfort`) | `main` | Active ComfortSense project — firmware source, governance record, Python analysis | Write repo for this session |
| `git@github.com:drsiyaoshao-sudo/crucible-lite.git` | default | Upstream Crucible framework reference — framework patches, agent/command updates, constitutional template | Read-only reference. Do not commit here from this project. Agents may `git clone` or `git fetch` for cross-repo pattern lookup only. |

---

## Stage Status

```
Spec Gate  — Device Specification:  CLOSED 2026-04-16 (Amendment 1 ratified)
Stage 0    — HIL Toolchain Lock:    OPEN 2026-04-20 — Gates 0.1 + 0.2 PASS; 0.3/0.4 pending
Stage 1    — Simulation:            NOT STARTED
Stage 2    — Firmware Integration:  NOT STARTED
Stage 3    — Field Test:            NOT STARTED
Stage 4    — Host Integration:      NOT STARTED
```

---

## Constitutional References

- **Amendment 3 (Toolchain Alignment):** This file is the live implementation of the active toolchain record. Any change to the active toolchain requires updating this file and ratifying or amending Amendment 3. *(Amendment 3 RATIFIED 2026-04-19, concurrent with Case 1 — see `docs/governance/case_law.md`.)*
- **Amendment 4 (Three-Strike Rule):** Blocked toolchain entries in this file are the formal record of strikes. Three strikes → block mandatory.
- **Amendment 2 (Stage Gate Order):** Stage status table above is the authoritative gate record. Stage N cannot open until Stage N-1 is CLOSED here.

---

## Sources cited in this file

- **[S1]** Seeed Studio XIAO nRF52840 Sense Wiki — board summary, pinout, known issues, NFC/GPIO reconfiguration, IMU power sequencing, BLE brownout, USB-C re-enumeration.
- **[S2]** STMicroelectronics LSM6DS3TR-C Datasheet, DS12232 Rev 5 — I2C address, WHO_AM_I, noise density, ODR options, full-scale options, boot time.
