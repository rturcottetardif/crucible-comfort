# Stage 0 Closeout — HIL Toolchain Lock

**Frozen:** 2026-04-20
**Authorized by:** Justice (direct confirmation in session, 2026-04-20)
**Police audit:** CLEAN — 7 commits audited, 0 violations outstanding
**Branch:** toolchain/platform-resolution-xiaoblesense

**Stage gate record:** `docs/governance/handoff.md` does not exist at closeout time.
Exit criteria are recorded here from Justice's direct confirmation:

| Gate | Description | Result | Date |
|---|---|---|---|
| 0.1 | Counter smoke test | PASS | 2026-04-20 |
| 0.2 | Sensor readout — LSM6DS3TR-C IMU | PASS | 2026-04-20 |
| 0.3 | Algorithm over USB | PASS | 2026-04-20 |
| 0.4 | Algorithm over BLE NUS wireless | PASS | 2026-04-20 |

**Key commits:**

| Commit | Description |
|---|---|
| e5b97ff | Toolchain enactment — block PlatformIO, enact arduino-cli (Case 1) |
| 0ab8f88 | agent-updater propagation (Condition 9 + Standing Order) |
| 7c4dc96 | First flash under enacted toolchain, closes E5 |
| ee338f5 | Amendments 2 + 4 ratified |
| b10c425 | W1/W2/W3 police warnings closed |
| 0297087 | Gate 0.2 PASS |
| ec03141 | Gates 0.3 + 0.4 PASS |

---

## Compacted Precedents

Five entries from `docs/governance/case_law.md` are frozen under this closeout.
Full argument text lives in the live case law record. The cards below are the
operational law for Stage 1 and beyond.

Full record: `docs/governance/case_law.md`

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Case 1 — XIAO nRF52840 Sense Platform Resolution
Frozen: Stage 0 | Date: 2026-04-20
Full record: docs/governance/case_law.md#case-1-xiao-nrf52840-sense--platform-resolution-for-xiaoblesense-board-id
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
arduino-cli with the Seeed nRF52 core (FQBN Seeeduino:nrf52:xiaonRF52840Sense,
v1.1.12) is the sole authorized toolchain for this project; PlatformIO
(nordicnrf52) is permanently blocked.

NEXT STAGE ENGINEER MUST:
- Compile and flash using: arduino-cli compile --fqbn Seeeduino:nrf52:xiaonRF52840Sense
  --build-path build/arduino/xiao_nrf52840_sense/
- Include #include "Adafruit_TinyUSB.h" at the top of every project .ino file
  (Condition 1a — build-gated; omission is a linker error).
- Install libraries via arduino-cli lib install only; pin each library version in
  docs/toolchain_config.md Library Manifest (Condition 8).
- Use arduino-cli monitor for serial capture; do NOT use pio device monitor.
- Verify FQBN string against live index before any new core install (Condition 2).
- Write any new board bring-up evidence to docs/device_context.md Hardware
  Bring-up History before flash attempts (Condition 3).

NEXT STAGE ENGINEER MUST NEVER:
- Use pio run, pio lib install, pio upload, or any PlatformIO command on this
  project. PlatformIO is BLOCKED per Condition 6.
- Unblock PlatformIO without a new Judicial Hearing (Amendment 3).
- Edit the crucible/ infrastructure package for build-path workarounds; use
  project-local src/ only (Condition 7).
- Omit Adafruit_TinyUSB.h from any .ino targeting Seeeduino:nrf52:xiaonRF52840Sense.

PHYSICAL BASIS:
arduino-cli board listall (2026-04-20): Seeeduino:mbed:xiaonRF52840Sense labeled
"(No Updates)"; Seeeduino:nrf52:xiaonRF52840Sense is the current maintained variant.
E2/E3/E4 confirm xiaoblesense absent from PlatformIO stock platform.
E5 — prior PlatformIO flash produced a boot-loop (single occurrence, colleague-fixed).
E5 resolved: first clean flash under arduino-cli completed in commit 7c4dc96.

REOPENS ONLY IF:
Seeed Studio publishes a new, distinct board support package for SKU 102010469
(new hardware revision with a different VID:PID or mbed deprecation notice), AND
a Judicial Hearing is explicitly declared on Case 1 by name, AND the Justice cites
that publication as a physical change not in scope at Stage 0 close.
A new opinion on PlatformIO support or a community fork alone is not sufficient.
─────────────────────────────────────────────────────────────
```

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Case 1.1 — Condition 1 Amendment: Core Flavor Correction
Frozen: Stage 0 | Date: 2026-04-20
Full record: docs/governance/case_law.md#case-11--supplementary-ruling-condition-1-amended-per-fqbn-verification-evidence
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
Case 1 Condition 1 is amended: the active FQBN is Seeeduino:nrf52:xiaonRF52840Sense
(non-mbed, v1.1.12), not the mbed-enabled variant; PDM pin symbols are identical
across both cores, so the original PDM-drift rationale did not distinguish them.

NEXT STAGE ENGINEER MUST:
- Target Seeeduino:nrf52:xiaonRF52840Sense (non-mbed) for all compiles.
- Include #include "Adafruit_TinyUSB.h" in every .ino (Condition 1a, build-gated).
- Treat Conditions 2–9 of Case 1 as standing unchanged, with FQBN resolved to
  Seeeduino:nrf52:xiaonRF52840Sense.

NEXT STAGE ENGINEER MUST NEVER:
- Target Seeeduino:mbed:xiaonRF52840Sense; that core is "(No Updates)" — frozen.
- Omit Adafruit_TinyUSB.h under the assumption that the mbed core is in use.

PHYSICAL BASIS:
arduino-cli board listall (2026-04-20): mbed variant labeled "(No Updates)".
variant.h / pins_arduino.h grep (2026-04-20): PIN_PDM_PWR/CLK/DIN = 19/20/21
identical in both cores — no PDM symbol drift between them.
Smoke-test compile (2026-04-20): nrf52 core fails without TinyUSB include;
mbed core compiles without it (84120 bytes flash, 43944 bytes RAM).

REOPENS ONLY IF:
Seeed publishes a new mbed-enabled core for SKU 102010469 with active maintenance
status, AND a Judicial Hearing is explicitly declared on Case 1.1 by name, AND the
Justice cites the new publication as a physical change not in scope at Stage 0 close.
─────────────────────────────────────────────────────────────
```

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Standing Order — Ratification Date Convention
Frozen: Stage 0 | Date: 2026-04-20
Full record: docs/governance/case_law.md#standing-order-record--ratification-date-convention-2026-04-20
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
Amendment ratification dates record the Justice's act of ratification, not the
git commit timestamp; the commit is the durable record of that prior act.

NEXT STAGE ENGINEER MUST:
- When recording a new amendment ratification date in docs/governance/amendments.md,
  use the date the Justice said "ratify" (or the date of the ruling that ratified),
  not the date of the commit.
- If ratification and commit occur on different calendar dates, the amendment date
  governs for constitutional precedence; note the commit date separately if relevant.

NEXT STAGE ENGINEER MUST NEVER:
- Backdate or alter a ratification date to match a commit date after the fact.
- Treat the commit date as the authoritative ratification date.

PHYSICAL BASIS:
Amendment 3 ratified 2026-04-19 (concurrent with Case 1 ruling); recorded in
commit dated 2026-04-20. Discrepancy resolved by this Standing Order.
Closes Police Warning W2 (/session 0 pre-audit, 2026-04-20).

REOPENS ONLY IF:
A future constitutional amendment explicitly redefines ratification timing. A new
agent opinion or process preference alone is not sufficient.
─────────────────────────────────────────────────────────────
```

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Standing Order — agent-updater Execution Record (Case 1 Condition 9)
Frozen: Stage 0 | Date: 2026-04-20
Full record: docs/governance/case_law.md#standing-order-record--agent-updater-execution-2026-04-20
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
Six agent files and one doc file were updated under Justice-approved Article II
review to propagate the PlatformIO-to-arduino-cli scope change; all edits are
recorded and closed in commit 0ab8f88.

NEXT STAGE ENGINEER MUST:
- Treat the following as the canonical post-Stage-0 toolchain state in agent files:
  CLAUDE.md (2 pio → arduino-cli), package-manager.md (pio BLOCKED note),
  simulator-operator.md (ELF rebuild via arduino-cli compile),
  regression-runner.md (ELF path: build/arduino/xiaonRF52840Sense/<sketch>.ino.elf),
  uart-reader.md (serial monitor = arduino-cli monitor),
  code-reviewer.md (SKETCH-HEADER-VIOLATION check for Adafruit_TinyUSB.h).
- If any future agent-updater run proposes edits to these files, confirm the
  Stage 0 base state is preserved before applying new changes.

NEXT STAGE ENGINEER MUST NEVER:
- Re-introduce pio run, pio lib install, or pio device monitor in any agent file
  without a new Judicial Hearing unblocking PlatformIO.
- Apply agent-updater changes without per-edit Justice approval (Article II).

PHYSICAL BASIS:
Commit 0ab8f88, branch toolchain/platform-resolution-xiaoblesense, 2026-04-20.
7 edits applied: 6 agent files + 1 doc fix. Closes Police Warning W3.

REOPENS ONLY IF:
A new agent-updater run is triggered by a new ruling that changes toolchain scope,
AND a Judicial Hearing is explicitly declared naming this Standing Order as the
subject. A new Bill alone is not sufficient to undo the commit-level record here.
─────────────────────────────────────────────────────────────
```

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Standing Order — Police Warning W-Gate0.3-A1 Acknowledged
Frozen: Stage 0 | Date: 2026-04-20
Full record: docs/governance/case_law.md#standing-order-record--police-warning-w-gate03-a1-acknowledged-2026-04-20
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
REPORT_PERIOD_MS = 500 in firmware/stage0_algo_usb/stage0_algo_usb.ino (line 37)
is a UART emission cadence for a liveness smoke test only; no threshold or detection
logic is attached; a practical-basis inline comment was added and the warning is closed.

NEXT STAGE ENGINEER MUST:
- Treat the inline comment on REPORT_PERIOD_MS as the Article I citation for that
  constant in stage0_algo_usb.ino; no further action on W-Gate0.3-A1.
- For any new UART emission cadence constant introduced in Stage 1+, provide an
  inline Article I citation (primitive or explicit practical-basis note) from the
  outset; do not allow code-reviewer to flag it as a new warning.

NEXT STAGE ENGINEER MUST NEVER:
- Use REPORT_PERIOD_MS = 500 as a precedent for leaving non-threshold constants
  uncited in production (Stage 1+) firmware; this exception applies only to the
  Stage 0 liveness smoke test sketch.
- Omit inline Article I citations for constants in any sketch that introduces
  thresholds or detection logic.

PHYSICAL BASIS:
firmware/stage0_algo_usb/stage0_algo_usb.ino line 37: REPORT_PERIOD_MS = 500.
Sketch header confirms "no thresholds are introduced" (Stage 0 liveness only).
Practical basis: 2 Hz emission sufficient for ~10 s Gate 0.3 observation window.

REOPENS ONLY IF:
A new sketch reuses REPORT_PERIOD_MS = 500 in a context that does introduce
detection logic or thresholds, AND a Judicial Hearing is explicitly declared on
W-Gate0.3-A1 by name. A code-reviewer flag on a different constant is not sufficient
to reopen this specific precedent.
─────────────────────────────────────────────────────────────
```

---

## Closeout Execution Record

| Step | Action | Result |
|---|---|---|
| 1 | Read docs/governance/case_law.md | 5 Active entries identified for Stage 0 |
| 2 | Read docs/governance/handoff.md | FILE MISSING — proceeded under Justice's direct session confirmation |
| 3 | Produced Settled Precedent Cards | 5 cards written above |
| 4 | Wrote docs/governance/stage_0_closeout.md | This file |
| 5 | Freeze entries in case_law.md | Applied FROZEN markers to all 5 Active entries |
| 6 | Commit | See commit hash below |

**Committed:** see git log — `chore: close Stage 0 — compact case law, freeze precedents`
