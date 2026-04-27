# Crucible Case Law

This file records all Judicial Hearing rulings. Entries are written by the prevailing
attorney immediately after the Justice's ruling, before any implementation begins.

Live entries accumulate full argument text. Frozen entries (after stage closeout via
`stage-compactor`) contain only the compact operational record.

---

## Active Precedents

### Standing Order Record — First scaffold authorization

**Date:** 2026-04-27
**Closes:** Police Warning W-S1-A (/session 1 pre-audit)
**Commit:** b69d057 (scaffold) — to be re-cited from this session's governance commit

**Ruling (operative):** `/toolchain scaffold` ran for the first time at commit b69d057
(2026-04-27), generating `src/events.py`, `src/analysis.py`, `src/plot.py`,
`src/signals.py`, `src/algorithm.py` from the Firmware UART Format defined in
`docs/toolchain_config.md` (session_end_marker `SESSION_END`; events `reading`
and `metric`). Confirmed: no prior `src/` directory existed before this commit.
Justice acknowledges the UART Format as the authorized event schema for the
scaffold run.

**Effect under Amendment 11 (Scaffold Immutability, RATIFIED 2026-04-27):**
- `src/events.py`, `src/analysis.py`, `src/plot.py` are infrastructure modules
  — they will be confirmed and frozen at the Stage 1 Justice Gate, after
  code-reviewer audits Article I traceability of all parsed fields. Once frozen,
  they must not be regenerated, overwritten, or modified for the remainder of
  the project without explicit human authorization plus a Bill.
- `src/signals.py` and `src/algorithm.py` are stubs to be implemented in
  Stage 1; they are NOT subject to the Amendment 11 freeze (they are project
  source, not scaffolded analysis modules). Implementation must comply with
  Article I (every constant traces to a domain primitive in Amendment 1).
- Any change to `docs/device_context.md` Signal Inventory or
  `docs/toolchain_config.md` Firmware UART Format that would alter the
  scaffolded modules requires a Bill enacted through the Legislative Process
  before re-scaffolding is permitted.

**Re-scaffold trigger:** silent re-execution of `/toolchain scaffold` after
this date is a violation of Amendment 11 unless preceded by an enacted Bill
authorizing it.

---

---

## Frozen Precedents

### Case 1: XIAO nRF52840 Sense — Platform Resolution for xiaoblesense Board ID

**[FROZEN — Stage 0 closed 2026-04-20]**

**Date:** 2026-04-19
**Prevailing position:** B — arduino-cli + Seeed nRF52 core (official Seeed support)
**Enacted bill:** docs/governance/bills/platform-resolution.md
**Implementation branch:** toolchain/platform-resolution-xiaoblesense
**Compact card:** docs/governance/stage_0_closeout.md

**Ruling (operative):** arduino-cli with FQBN `Seeeduino:nrf52:xiaonRF52840Sense` (v1.1.12) is the sole authorized toolchain. PlatformIO (nordicnrf52) is permanently blocked. Unblocking requires a new Judicial Hearing per Amendment 3.

**Evidence anchors:** E1 (port /dev/cu.usbmodem14301, VID:PID 2886:8045) — E2/E3/E4 (xiaoblesense absent from PlatformIO stock) — E5 (prior boot-loop, resolved at commit 7c4dc96 first clean flash).

**Conditions (operative, numbered for downstream reference):**
1. ~~Select mbed-enabled core~~ — AMENDED by Case 1.1: use `Seeeduino:nrf52:xiaonRF52840Sense` (non-mbed, v1.1.12). See Case 1.1 below.
2. FQBN verified as `Seeeduino:nrf52:xiaonRF52840Sense` — recorded in docs/toolchain_config.md.
3. E1 written to docs/device_context.md Hardware Bring-up History. DONE.
4. E5 written to docs/device_context.md Open Anomalies. RESOLVED at commit 7c4dc96.
5. Amendment 3 ratified 2026-04-19. DONE.
6. PlatformIO blocked in docs/toolchain_config.md Blocked Toolchains, citing E2/E3/E4/E5. DONE.
7. arduino-cli compile with `--build-path build/arduino/xiao_nrf52840_sense/`. RenoneBridge path follow-up Bill pending until Stage 1 sim work begins.
8. Library Manifest in docs/toolchain_config.md updated to arduino-cli lib install syntax with pinned versions. DONE at first successful compile.
9. agent-updater invoked; all 6 agent files + 1 doc updated under Justice approval. DONE (commit 0ab8f88).
1a. (added by Case 1.1) Every project `.ino` targeting `Seeeduino:nrf52:xiaonRF52840Sense` must include `#include "Adafruit_TinyUSB.h"` at top. Build-gated. Enforced by code-reviewer.

---

### Case 1.1 — Supplementary Ruling: Condition 1 amended per FQBN verification evidence

**[FROZEN — Stage 0 closed 2026-04-20]**

**Date:** 2026-04-20
**Supplements:** Case 1 (2026-04-19)
**Compact card:** docs/governance/stage_0_closeout.md

**Ruling (operative):** Condition 1 of Case 1 amended. Active FQBN is `Seeeduino:nrf52:xiaonRF52840Sense` (non-mbed, v1.1.12) — the actively maintained Seeed core. The mbed variant (`Seeeduino:mbed:xiaonRF52840Sense`) is labeled "(No Updates)" and must not be targeted. PDM pin symbols (PIN_PDM_PWR/CLK/DIN = 19/20/21) are identical across both cores; original PDM-drift rationale did not distinguish them. Condition 1a added: `#include "Adafruit_TinyUSB.h"` required in every project .ino.

**Evidence anchors:** arduino-cli board listall (2026-04-20) — variant.h/pins_arduino.h grep (2026-04-20, values 19/20/21 both cores) — smoke-test compile /tmp/xiao_smoke/xiao_smoke.ino (2026-04-20, linker error without TinyUSB include).

**Does not change:** Positions 2–9, Blocked Toolchain entry, prevailing position B.

**E5 status at Case 1.1:** OPEN — deferred to first project flash. Resolved at commit 7c4dc96 (Stage 0 Gate 0.1).

---

### Standing Order Record — Ratification date convention

**[FROZEN — Stage 0 closed 2026-04-20]**

**Date:** 2026-04-20
**Closes:** Police Warning W2 (/session 0 pre-audit)
**Compact card:** docs/governance/stage_0_closeout.md

**Ruling (operative):** Amendment ratification dates in `docs/governance/amendments.md` record the Justice's act of ratification, not the git commit date. Applies to: Amendment 3 (ratified 2026-04-19, commit 2026-04-20); Amendments 2, 4 (ratified and committed 2026-04-20).

---

### Standing Order Record — agent-updater execution (Case 1 Condition 9)

**[FROZEN — Stage 0 closed 2026-04-20]**

**Date:** 2026-04-20
**Closes:** Police Warning W3 (/session 0 pre-audit)
**Commit:** 0ab8f88
**Compact card:** docs/governance/stage_0_closeout.md

**Ruling (operative):** 6 agent files + 1 doc updated under per-edit Justice approval (Article II) to propagate PlatformIO → arduino-cli. Canonical post-Stage-0 state: CLAUDE.md, package-manager.md (pio BLOCKED), simulator-operator.md (arduino-cli compile ELF rebuild), regression-runner.md (ELF path build/arduino/xiaonRF52840Sense/), uart-reader.md (arduino-cli monitor), code-reviewer.md (SKETCH-HEADER-VIOLATION check). Any future agent-updater run must preserve this base state.

---

### Standing Order Record — Police Warning W-Gate0.3-A1 acknowledged

**[FROZEN — Stage 0 closed 2026-04-20]**

**Date:** 2026-04-20
**Closes:** Police Warning W-Gate0.3-A1
**Compact card:** docs/governance/stage_0_closeout.md

**Ruling (operative):** `REPORT_PERIOD_MS = 500` in `firmware/stage0_algo_usb/stage0_algo_usb.ino` line 37 is a UART emission cadence for a Stage 0 liveness smoke test only (no thresholds, no detection logic). Inline practical-basis comment added. This exception (uncited constant in no-threshold sketch) does not extend to Stage 1+ firmware that introduces thresholds or detection logic.
