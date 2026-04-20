# Crucible Case Law

This file records all Judicial Hearing rulings. Entries are written by the prevailing
attorney immediately after the Justice's ruling, before any implementation begins.

Live entries accumulate full argument text. Frozen entries (after stage closeout via
`stage-compactor`) contain only the compact operational record.

---

## Active Precedents

### Case 1: XIAO nRF52840 Sense — Platform Resolution for xiaoblesense Board ID

**Date:** 2026-04-19

**Positions:** A — Candidate A: adopt maxgerhardt/platform-nordicnrf52 community fork for board=xiaoblesense under stock PlatformIO framework=arduino | B — Candidate C: abandon PlatformIO, adopt arduino-cli with Seeed nRF52 mbed core (official Seeed support)

**Prevailing position:** B

**Justice's ruling:** Position B prevails. The Justice ruled that arduino-cli with the Seeed nRF52 mbed core is the supported method from Seeed Studio for the XIAO nRF52840 Sense (SKU 102010469), and therefore the correct instrument path for this project. PlatformIO is superseded for this project from the date of this ruling.

**Physical/empirical basis:**
- Evidence item (b) — WebFetch of https://files.seeedstudio.com/arduino/package_seeeduino_boards_index.json on 2026-04-19: confirmed that the XIAO nRF52840 Sense board is present in Seeed's official package index under packager "Seeeduino", architecture "nrf52", board identifier "xiao_nrf52840_sense". Two maintained core flavors confirmed: "Seeed nRF52 Boards" v1.1.12 and "Seeed nRF52 mbed-enabled Boards" v2.9.3. This is Seeed's own published, maintained distribution — not a community fork.
- E2 — `pio boards nrf52` output (2026-04-19): returns `adafruit_feather_nrf52840_sense` and `nicla_sense_me`; does not return `xiaoblesense`. Confirmed absence of the named board ID in the stock PlatformIO nordicnrf52 platform.
- E3 — `pio boards | grep xiao` output (2026-04-19): returns SAMD21 and ESP32 XIAO variants only; no nRF52 XIAO variant present. Confirmed the absence is not a naming variant issue within PlatformIO stock.
- E4 — PlatformIO Core version 6.1.19 confirmed by `pio --version` (2026-04-19): the platform database is current; the absence of `xiaoblesense` is not an outdated index issue.
- E5 — Boot-loop anomaly (single occurrence, date unrecorded): a prior PlatformIO flash attempt on this board model produced corrupted firmware and a boot-loop; resolution was effected by a colleague by unknown means and is not recorded. Consistent with incorrect memory layout, linker script, or bootloader offset arising from a mismatched platform/board definition. Cited from session memory — must be written to docs/device_context.md Open Anomalies table before implementation begins (see Conditions item 4). E1 (pio device list, /dev/cu.usbmodem14301, VID:PID 2886:8045) was similarly cited from session memory and must be written to docs/device_context.md Hardware Bring-up History before any flash attempt (see Conditions item 3).

**Device outcome protected:** A vendor-maintained, Seeed-published instrument path from firmware source to flashed binary on SKU 102010469, protecting the ability to measure Filter ΔP (Pa) via LSM6DS3TR-C IMU 6-channel vibration and PDM microphone acoustic turbulence, and HVAC operating regime via DS18B20 OneWire thermometer and CT current RMS, without the silent-failure modes — PDM variant.h symbol drift and third-party platform fork abandonment — identified in the hearing record.

**Conditions:**
1. Select the mbed-enabled core flavor specifically: "Seeed nRF52 mbed-enabled Boards" v2.9.3. The Pin Map in docs/toolchain_config.md references PIN_PDM_CLK, PIN_PDM_DIN, and PIN_PDM_PWR from mbed_nano variant.h, which lives in the mbed-enabled core. The non-mbed "Seeed nRF52 Boards" v1.1.12 core is not the correct target for this project.
2. Verify the exact FQBN by running `arduino-cli core search nrf52` after adding the Seeed board index URL (https://files.seeedstudio.com/arduino/package_seeeduino_boards_index.json). The inferred FQBN is Seeeduino:nrf52:xiao_nrf52840_sense, but this string must be confirmed against the live index before it is committed to docs/toolchain_config.md. Record the verified FQBN string in the Active Firmware Toolchain section of that file.
3. Write E1 (pio device list output from 2026-04-19: port /dev/cu.usbmodem14301, VID:PID 2886:8045, description "XIAO nRF52840 Sense") to the Hardware Bring-up History table in docs/device_context.md before any flash attempt under arduino-cli.
4. Write E5 (boot-loop anomaly on prior PlatformIO flash attempt, single occurrence, colleague-fixed by unknown means) to the Open Anomalies table in docs/device_context.md with status "open" and note "superseded by Case 1 ruling — PlatformIO blocked for this project". Mark this anomaly resolved only after the first clean flash under arduino-cli succeeds with clean UART output on /dev/cu.usbmodem14301 at 115200 baud and no boot-loop recurrence.
5. Ratify Amendment 3 (Toolchain Alignment) by removing the PROPOSED prefix in docs/governance/amendments.md before the enacted toolchain record in docs/toolchain_config.md is committed to the implementation branch. Amendment 3 ratification is what gives this ruling full binding weight under the constitutional record. Ratification requires explicit human approval.
6. Block PlatformIO (nordicnrf52) in the Blocked Toolchains section of docs/toolchain_config.md, citing E2, E3, and E4 (xiaoblesense absent from stock platform) and E5 (prior boot-loop). Unblocking PlatformIO for this project requires a new Judicial Hearing per Amendment 3.
7. Configure arduino-cli compile with explicit --build-path build/arduino/xiao_nrf52840_sense/ to produce a stable ELF path for the Renode bridge (crucible.sim.renode.RenoneBridge). The current bridge references PlatformIO build artifact path conventions (.pio/build/<env>/), which do not apply under arduino-cli. File a follow-up Bill to update the RenoneBridge path convention formally. Until that Bill is enacted, a documented hand-edit of the bridge's build path variable in the project-local src/ directory is permitted as a temporary workaround; do not edit the crucible/ infrastructure package.
8. Update the Library Manifest entries in docs/toolchain_config.md (Seeed_Arduino_LSM6DS3, OneWire, DallasTemperature, arduinoFFT) to reference arduino-cli lib install syntax. Pin each library version at the first successful arduino-cli compile using /toolchain add lib for each library in turn. The version strings "TBD — pin at first PlatformIO build" are superseded by this ruling.
9. Invoke the agent-updater agent after enactment to propagate the toolchain change to any agent that references pio run, pio lib install, or pio upload commands. CLAUDE.md agent roster references and any Bureaucracy agent instructions that assume PlatformIO commands must be updated.

**Enacted bill (if any):** platform-resolution.md (docs/governance/bills/platform-resolution.md)

**Implementation branch:** toolchain/platform-resolution-xiaoblesense

---

### Case 1.1 — Supplementary Ruling: Condition 1 amended per FQBN verification evidence

**Date:** 2026-04-20

**Supplements:** Case 1 — XIAO nRF52840 Sense — Platform Resolution for xiaoblesense Board ID (2026-04-19)

**Type:** Condition amendment based on new evidence produced during enactment. Does not change Position B prevailing; does not change any other condition.

**Justice's ruling:** Condition 1 of Case 1 is amended. Where Condition 1 previously required `Seeeduino:mbed:xiaonRF52840Sense` (the "Seeed nRF52 mbed-enabled Boards" core, v2.9.3), it is now amended to require `Seeeduino:nrf52:xiaonRF52840Sense` (the "Seeed nRF52 Boards" core, v1.1.12 — the actively-maintained variant). Project sketches compiled under this core must include `#include "Adafruit_TinyUSB.h"` at the top of the main `.ino` file to provide the `Serial` USB CDC interface.

**Physical/empirical basis:**
- `arduino-cli board listall` output (2026-04-20, this session): `Seeeduino:mbed:xiaonRF52840Sense` is labeled "(No Updates)" in Seeed's own core listing. `Seeeduino:nrf52:xiaonRF52840Sense` is the current, maintained variant. The Thomas Jefferson basis of Case 1 ("supported method from Seeed") points toward the actively-maintained core, not the frozen one.
- `variant.h` / `pins_arduino.h` grep of both installed cores (2026-04-20): `PIN_PDM_PWR`, `PIN_PDM_CLK`, and `PIN_PDM_DIN` are defined with identical values (19, 20, 21) in both cores. The PDM silent-drift risk cited as the primary rationale for the original Condition 1 does not exist between these two specific Seeed-published cores; both expose the same PDM symbols.
- Minimal smoke-test compile (`/tmp/xiao_smoke/xiao_smoke.ino`, 2026-04-20): `Seeeduino:nrf52:xiaonRF52840Sense` fails with linker errors (`undefined reference to 'Serial'`) unless `Adafruit_TinyUSB.h` is included — core uses Adafruit TinyUSB stack. `Seeeduino:mbed:xiaonRF52840Sense` compiles the same sketch without additional includes (84120 bytes = 10% flash, 43944 bytes = 18% RAM). TinyUSB include is a one-line-per-sketch cost acceptable against the benefit of active Seeed maintenance.

**Does not change:**
- Prevailing position: B (Candidate C — arduino-cli + Seeed nRF52 core family) remains the ruling.
- Conditions 2 through 9 of Case 1 stand as written, with FQBN in Condition 2 now resolved to `Seeeduino:nrf52:xiaonRF52840Sense` (the verification this Case 1.1 closes).
- Blocked Toolchain entry for PlatformIO `nordicnrf52` per Condition 6 is unchanged.

**New condition added under Case 1:**
- **Condition 1a (new):** Every project `.ino` file targeting `Seeeduino:nrf52:xiaonRF52840Sense` must include `#include "Adafruit_TinyUSB.h"` at the top. Bureaucracy Standing Order — enforced by `code-reviewer` as an Article I compliance check at each stage gate. Omission produces a linker error before flash, so this is build-gated rather than run-time-gated.

**Outstanding from Case 1:**
- E5 (boot-loop anomaly) remains OPEN. First successful flash under the enacted toolchain closes it. Case 1.1 did not include a flash attempt; the Justice elected evidence-based amendment over flash-based amendment. E5 closure deferred to first project firmware flash in Stage 0.

**Enacted bill:** platform-resolution.md (unchanged — same underlying Bill, same ruling, amended condition).

**Implementation branch:** toolchain/platform-resolution-xiaoblesense (unchanged).

---

### Standing Order Record — Ratification date convention (2026-04-20)

For amendments ratified in the /toolchain init → Case 1 session sequence, the
ratification date stated in `docs/governance/amendments.md` ("RATIFIED YYYY-MM-DD")
refers to the Justice's act of ratification concurrent with the ruling or explicit
command, NOT the date of the git commit that recorded the state change. This is
the governing Crucible convention for this project — the amendment is ratified
when the Justice says "ratify" (or enacts a ruling that ratifies), and the commit
is the durable record of that act.

Applies to:
- Amendment 3 — ratified 2026-04-19 concurrent with Case 1 ruling (commit date 2026-04-20)
- Amendments 2, 4 — ratified 2026-04-20 by explicit Justice command (commit date 2026-04-20)

This note closes Police Warning W2 from the /session 0 pre-audit (2026-04-20).

---

### Standing Order Record — agent-updater execution (2026-04-20)

Under Case 1 Condition 9, `agent-updater` proposed agent-file edits to propagate
the PlatformIO → arduino-cli scope change. Each proposed edit was reviewed
individually and approved by the Justice before apply (per Article II).

**Approved edits (applied in commit 0ab8f88):**

1. `CLAUDE.md` — `pio` → `arduino-cli` (2 occurrences: agent roster + Standing Orders list).
2. `.claude/agents/package-manager.md` — Standing Order install command + required-tools check updated; explicit "pio BLOCKED" note added.
3. `.claude/agents/simulator-operator.md` — ELF rebuild bash block replaced with `arduino-cli compile --build-path ...`.
4. `.claude/agents/regression-runner.md` — ELF path clarifying note added (points at `build/arduino/xiaonRF52840Sense/<sketch>.ino.elf`).
5. `.claude/agents/uart-reader.md` — Conduct Rule 7 added (serial monitor = `arduino-cli monitor`; do NOT use `pio device monitor`).
6. `.claude/agents/code-reviewer.md` — new `SKETCH-HEADER-VIOLATION` check for Case 1.1 Condition 1a (`Adafruit_TinyUSB.h` include); counter + stage-gate-blocker entries added.

**Plus one out-of-scope doc fix applied by Justice (same commit):**

7. `docs/toolchain_config.md` — stale "Amendment 3 currently PROPOSED" Constitutional References note corrected to "RATIFIED 2026-04-19".

All 7 edits applied on branch `toolchain/platform-resolution-xiaoblesense`, commit `0ab8f88`.

This note closes Police Warning W3 from the /session 0 pre-audit (2026-04-20).

---

## Frozen Precedents

*(Populated by stage-compactor at each stage gate.)*
