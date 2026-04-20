# BILL: XIAO nRF52840 Sense — Platform Resolution for `xiaoblesense` Board ID

```
Proposed by:   Roxanne Turcotte (human engineer) — drafted by bill-drafter agent
Date drafted:  2026-04-19
Change type:   firmware (toolchain configuration)
Branch:        toolchain/platform-resolution-xiaoblesense
Status:        ENACTED — Case 1 ruling 2026-04-19, amended by Case 1.1 2026-04-20
```

---

## Problem statement

The active toolchain record in `docs/toolchain_config.md` Section "Active Firmware Toolchain" currently reads:

    Build: PlatformIO — platform=nordicnrf52, board=xiaoblesense, framework=arduino

The board identifier `xiaoblesense` does not exist in the stock `nordicnrf52` platform distributed with PlatformIO Core 6.1.19. This was verified against the physical board (Seeed XIAO nRF52840 Sense, SKU 102010469) during the `/toolchain init` session on 2026-04-19:

**Physical evidence item 1 — `pio device list` output:**
- Port: `/dev/cu.usbmodem14301`
- Description: `XIAO nRF52840 Sense`
- VID:PID: `2886:8045`

Board is present and enumerated; the MCU is connected and ready.

**Physical evidence item 2 — `pio boards nrf52` output:**
- Returns: `adafruit_feather_nrf52840_sense`, `nicla_sense_me`
- Does NOT return: `xiaoblesense`

The identifier the toolchain record names is absent from the stock platform.

**Physical evidence item 3 — `pio boards | grep xiao` output:**
- Returns: `seeed_xiao` (SAMD21), `seeed_xiao_esp32c3`, `seeed_xiao_esp32c6`, `seeed_xiao_esp32s3`
- Does NOT return: any nRF52 XIAO variant

No PlatformIO stock platform carries a board definition for the nRF52840 Sense under any variant of the XIAO name.

**Physical evidence item 4 — Open anomaly (single-strike, not Amendment 4 threshold):**
A previous PlatformIO flash attempt on this same board model produced corrupted firmware and a boot-loop. A colleague resolved the issue by unknown means. The resolution was not recorded and is not in the Hardware Bring-up History in `docs/device_context.md`. The failure mode is consistent with a mismatched platform/board definition generating incorrect memory layout, linker script, or bootloader offset. This anomaly is not three-strike evidence under Amendment 4 (one occurrence, not three consecutive failures of the same Standing Order), but it is admissible under the Benjamin Franklin Principle as a warning that the platform choice carries documented hardware risk.

**Consequence:** `pio run` with the current toolchain record will fail immediately with a "board not found" error. No firmware can be built, no Stage 0 HIL smoke test can be executed, and Stage 0 cannot be opened until this gap is closed.

The toolchain record contains a self-annotation acknowledging the uncertainty: *"(verify exact board ID with `pio boards nrf52` after first successful `pio run` and amend this line if needed)"*. That verification has now been run. This Bill is the required result.

**Reference:** `docs/toolchain_config.md` — Active Firmware Toolchain section, written 2026-04-19. `docs/device_context.md` — Open Anomalies (boot-loop event, date TBD by human — currently recorded in session memory only, not yet written to the table).

---

## Proposed change

Three candidate resolutions are presented for Judicial debate. Enactment of exactly one candidate is required. The Justice selects; neither attorney self-approves.

### CANDIDATE A — Community platform fork (`maxgerhardt/platform-nordicnrf52`)

Proposed change to `docs/toolchain_config.md`, Active Firmware Toolchain section:

```
OLD:
  Build: PlatformIO — platform=nordicnrf52, board=xiaoblesense, framework=arduino

NEW:
  Build: PlatformIO — platform=https://github.com/maxgerhardt/platform-nordicnrf52,
           board=xiaoblesense, framework=arduino
  Platform resolution: maxgerhardt/platform-nordicnrf52 community fork — provides
    xiaoblesense board definition and Seeed mbed core integration. Version pinned to
    commit [HASH — to be recorded at first successful pio run]. PlatformIO Core 6.1.19.
  Note: UNBLOCKED. Requires active internet connection on first install.
```

Proposed change to `platformio.ini` (file does not yet exist — would be created):

```ini
[env:xiaoblesense]
platform = https://github.com/maxgerhardt/platform-nordicnrf52
board = xiaoblesense
framework = arduino
; Seeed mbed Arduino core — maxgerhardt fork includes xiaoblesense board def
; and board package pointing to Seeed nRF52 Arduino core (framework-arduino-mbed).
; Traces to Amendment 3 (Toolchain Alignment) — enacted [date of enactment].
```

**Pros:**
- Provides `xiaoblesense` board definition exactly as the toolchain record currently names it — no renaming required anywhere else in the project.
- Community fork is widely used in the XIAO nRF52 community; maxgerhardt is an active, well-documented maintainer with a track record across multiple platform forks.
- Inherits the upstream `nordicnrf52` platform, so PlatformIO ecosystem tooling (upload, monitor, lib install) works without modification.
- PDM symbolic names (`PIN_PDM_CLK` / `PIN_PDM_DIN` / `PIN_PDM_PWR`) referenced in `docs/toolchain_config.md` Pin Map are provided by the `mbed_nano` variant.h that this board definition targets — no custom variant required.

**Cons:**
- Third-party dependency: not in Seeed's official PlatformIO registry and not in Nordic Semiconductor's official toolchain. If the fork stalls or disappears, the project loses its build platform.
- Pinning a commit hash mitigates drift but requires a human decision to update the pin, adding governance overhead.
- The boot-loop anomaly (Physical evidence item 4) is unresolved; if it was caused by a platform configuration error in an earlier version of this same fork, Candidate A does not eliminate that risk — it depends on whether the current fork version has corrected the issue.

**Failure mode this candidate prevents:** "board not found" build failure (immediate, confirmed by pio boards evidence above).

**Failure mode this candidate introduces or leaves open:** Upstream fork abandonment (low probability, medium impact). Recurrence of boot-loop if the fork's board definition carries incorrect bootloader offset or memory map (unresolved — requires a post-enactment smoke test to close).

**Maintenance cost:** Low. Update the pinned commit hash when the fork advances; validate with a `pio run` smoke test. One human decision per update.

### CANDIDATE B — Custom board JSON in this repository (`boards/xiaoblesense.json`)

Proposed change to `docs/toolchain_config.md`, Active Firmware Toolchain section:

```
OLD:
  Build: PlatformIO — platform=nordicnrf52, board=xiaoblesense, framework=arduino

NEW:
  Build: PlatformIO — platform=nordicnrf52, board=xiaoblesense, framework=arduino
  Platform resolution: stock nordicnrf52 platform with custom board definition at
    boards/xiaoblesense.json in this repository. Derived from Seeed nRF52 Arduino
    core source. Revision: [JSON file hash — to be recorded at first successful
    pio run]. PlatformIO Core 6.1.19.
  Note: UNBLOCKED. Self-contained — no external platform fork dependency.
```

Proposed change to `platformio.ini` (file does not yet exist — would be created):

```ini
[env:xiaoblesense]
platform = nordicnrf52
board = xiaoblesense
framework = arduino
; Custom board def: boards/xiaoblesense.json — derived from Seeed nRF52 core.
; Traces to Amendment 3 (Toolchain Alignment) — enacted [date of enactment].
```

New file required: `boards/xiaoblesense.json`. Must define: MCU (nRF52840), clock (64 MHz), flash (1 MB internal), RAM (256 KB), bootloader offset (UF2 bootloader, standard Seeed offset — confirm against S1 source), build flags (matching mbed Arduino core for nRF52840), upload method (UF2 drag-drop matching Active Firmware Toolchain flash method in toolchain_config.md). Source of truth: Seeed Studio XIAO nRF52840 Sense Wiki [S1] and the board definition in the maxgerhardt fork (usable as reference, not copied wholesale without attribution).

**Pros:**
- Zero external platform fork dependency. The board definition lives in the project repository — `git revert` can undo any change to it instantly (satisfies Article II reversibility test more directly than Candidate A).
- The project team controls the board definition. If Seeed changes the hardware in a minor revision, the JSON can be updated in a single commit.
- Eliminates the fork-abandonment risk of Candidate A.

**Cons:**
- The project must author and maintain a PlatformIO board JSON from scratch. This requires correctly specifying bootloader offset, upload flags, build flags, and variant paths — an error in any of these is exactly the failure mode that produced the boot-loop anomaly (Physical evidence item 4). This candidate carries the highest risk of recreating that failure.
- Maintenance burden: every time PlatformIO or the nRF52 mbed core updates in a way that changes build flags or memory layout, the JSON must be manually updated. No upstream maintainer does this for the project.
- Toolchain config note in `docs/toolchain_config.md` (Pin Map) relies on `mbed_nano` variant.h for PDM pin symbolic names — the custom JSON must correctly point to that variant; an incorrect variant path silently breaks PDM.

**Failure mode this candidate prevents:** "board not found" build failure (same as Candidate A). Fork abandonment (unique to this candidate vs A).

**Failure mode this candidate introduces or leaves open:** Incorrect bootloader offset in the authored JSON → boot-loop (the documented historical anomaly may be reproduced under this candidate if the JSON is not derived carefully from a verified source).

**Maintenance cost:** High. Every upstream change requires a human-authorized JSON update, a Bill if the change materially affects build behaviour, and a smoke test.

### CANDIDATE C — Abandon PlatformIO; adopt `arduino-cli` with Seeed mbed core

Proposed change to `docs/toolchain_config.md`, Active Firmware Toolchain section:

```
OLD:
  Build: PlatformIO — platform=nordicnrf52, board=xiaoblesense, framework=arduino
  Flash: UF2 drag-drop ...
  Serial monitor: python -m serial.tools.miniterm /dev/cu.usbmodem* 115200 8N1
  Simulation: Renode 1.16 via crucible.sim.renode.RenoneBridge

NEW:
  Build: arduino-cli — core=Seeed nRF52 mbed Arduino core
           (https://files.seeedstudio.com/arduino/package_seeeduino_boards_index.json),
           board FQBN=Seeed_Arduino_Boards:mbed_rp2040:XIAO_nRF52840_Sense
           (exact FQBN to be confirmed at first successful arduino-cli compile).
  Flash: UF2 drag-drop — double-tap reset (unchanged from PlatformIO candidate).
  Serial monitor: arduino-cli monitor -p /dev/cu.usbmodem* --config baudrate=115200
    (or: python -m serial.tools.miniterm — unchanged).
  Simulation: Renode 1.16 via crucible.sim.renode.RenoneBridge — unchanged.
  Platform blocked: PlatformIO blocked for this project pending resolution of
    xiaoblesense board ID gap. Recorded as blocked toolchain entry below.
```

BLOCKED TOOLCHAIN entry to add:

```
PlatformIO nordicnrf52 — blocked 2026-04-19. Reason: board=xiaoblesense not
found in stock platform; xiaoblesense ID unverified at Stage 0 gate.
Resolution path: enact Candidate A or B from BILL "XIAO nRF52840 Sense —
Platform Resolution". Do not unblock until a pio run smoke test confirms correct
flash and clean UART output from the board.
```

Additional required changes under Candidate C:
- `docs/toolchain_config.md` Library Manifest: replace PlatformIO lib install references with `arduino-cli lib install` equivalents.
- `CLAUDE.md` and any agent that references `pio run` or `pio lib install` must be updated via agent-updater after enactment.
- The simulation path (Renode via RenoneBridge) is unaffected — it does not depend on PlatformIO.

**Pros:**
- `arduino-cli` with the official Seeed nRF52 mbed core gives the XIAO nRF52840 Sense first-class, Seeed-maintained support — the board FQBN is published and tested by Seeed. This is the toolchain Seeed themselves use and document in [S1].
- Eliminates the platform fork dependency (Candidate A risk) and the board JSON authoring burden (Candidate B risk) simultaneously.
- If the boot-loop anomaly was platform-configuration-driven, switching to the Seeed-maintained toolchain is the most direct path to eliminating the root cause.

**Cons:**
- Full toolchain replacement. Amendment 3 (Toolchain Alignment, currently PROPOSED) is designed precisely to prevent silent mid-stage toolchain switches. Enacting this candidate is the correct constitutional path — but it is the highest-impact change of the three, touching `docs/toolchain_config.md`, the Library Manifest, any existing `platformio.ini` (not yet created), and all agent references.
- PlatformIO has a richer dependency management model (`lib_deps` in `platformio.ini`) than `arduino-cli`. The Library Manifest in `toolchain_config.md` lists four libraries (`Seeed_Arduino_LSM6DS3`, `OneWire`, `DallasTemperature`, `arduinoFFT`) — all are installable via `arduino-cli`, but the install and pin syntax differs.
- The Renode simulation path in `crucible.sim.renode.RenoneBridge` may reference PlatformIO build artifacts by path convention (`.pio/build/<env>/`). Under `arduino-cli` the build output path changes. This must be verified before Stage 1 opens.
- Cost: if PlatformIO is later needed for a different sub-target, it cannot be introduced without a new Bill.

**Failure mode this candidate prevents:** "board not found" build failure (same as A and B). Boot-loop if root cause was PlatformIO platform misconfiguration (higher confidence than A or B — only this candidate eliminates PlatformIO entirely).

**Failure mode this candidate introduces:** Renode build artifact path mismatch (requires investigation before Stage 1). Higher change surface — more files, more agent references to update.

**Maintenance cost:** Medium. Seeed maintains the core. `arduino-cli` is stable. Cost is concentrated at the toolchain switch moment, not ongoing.

---

## Article / Amendment grounding

**Primary:**

- **Amendment 3 — Toolchain Alignment (PROPOSED, not yet ratified):** *"No agent may introduce a new toolchain, framework, or build system without a Bill enacted through the Legislative Process."* This Bill is the required Bill. However, Amendment 3 is currently PROPOSED and has not been ratified. If it remains unratified at the time of debate, the Bill's standing under Amendment 3 is advisory rather than binding. The Justice should note whether Amendment 3 ratification is a precondition of this hearing or a concurrent action.

  *Recommended action:* ratify Amendment 3 (by removing the PROPOSED prefix in `docs/governance/amendments.md`) before or concurrent with this Judicial Hearing. Ratification requires explicit human approval — silence is not ratification (CONSTITUTION.md, Amendment Ratification Process).

**Supporting:**

- **Article II — Human in the Loop:** The toolchain choice is irreversible within a stage — changing it mid-Stage 0 after a failed flash attempt would require re-running the HIL smoke test from scratch. The human must decide; the agent must not select a candidate unilaterally.
- **Amendment 4 — Three-Strike Escalation Rule (PROPOSED, not yet ratified):** The boot-loop anomaly (Physical evidence item 4) is one occurrence. It does not trigger Amendment 4's three-strike stop. However, if any candidate is enacted and the first flash attempt under the new platform fails, that is strike one of a new three-strike count. The Justice should be aware that a second and third failure under the enacted platform would trigger a mandatory human stop under Amendment 4.
- **Amendment 7 — Calibration Discipline (PROPOSED, not yet ratified):** The platform choice must be evidence-based. Each candidate above has been evaluated against the physical evidence on record (the `pio boards` outputs and the device list). No candidate may be selected on intuition or prior experience alone — the Benjamin Franklin Principle applies to the ruling.

---

## Physical evidence

All items cited exist in the session record and are grounded in `toolchain_config.md` or were produced during the `/toolchain init` session on 2026-04-19.

- **E1.** `pio device list` output (2026-04-19, `/toolchain init` session): Port `/dev/cu.usbmodem14301`, VID:PID 2886:8045, "XIAO nRF52840 Sense". → Physical board is present, enumerated, and identified by OS. → Board identity confirmed as Seeed XIAO nRF52840 Sense. *Cited from:* `/toolchain init` session — not yet recorded in `docs/device_context.md` Test Results table. Human must add this entry to the Hardware Bring-up History before Stage 0 closes.
- **E2.** `pio boards nrf52` output (2026-04-19, `/toolchain init` session): Returns `adafruit_feather_nrf52840_sense`, `nicla_sense_me` — no `xiaoblesense`. → Confirmed absence of the named board ID in the stock `nordicnrf52` platform.
- **E3.** `pio boards | grep xiao` output (2026-04-19, `/toolchain init` session): Returns SAMD21 and ESP32 XIAO variants only — no nRF52 XIAO variant. → Confirmed that the absence is not a naming variant issue within PlatformIO stock.
- **E4.** PlatformIO Core version: `6.1.19` (confirmed by `pio --version`, `/toolchain init` session). → Platform database is current for PlatformIO 6.1.x; the absence of `xiaoblesense` is not an outdated index issue.
- **E5.** Boot-loop anomaly (single occurrence, date unrecorded): A previous PlatformIO flash attempt on this board model produced corrupted firmware and a boot-loop. Colleague resolved by unknown means. Consistent with incorrect memory map or bootloader offset in the platform/board definition. *Warning:* this anomaly is NOT in `docs/device_context.md` Open Anomalies table. Human must add it before the hearing — attorneys cannot cite a table entry that does not exist in the evidence record.
- **E6.** `docs/toolchain_config.md` Active Firmware Toolchain section (written 2026-04-19): Confirms `board=xiaoblesense`, `platform=nordicnrf52`. The self-annotation in that section acknowledges verification was deferred. This Bill completes that deferred verification step.

**Gap:** E5 (boot-loop anomaly) is currently only in session memory — it must be written to `docs/device_context.md` Open Anomalies table before the hearing for attorneys to cite it admissibly.

---

## Expected outcome

**Domain primitive traceability note:** the platform choice is an enabling infrastructure decision, not a direct change to a signal algorithm or threshold. It does not itself produce a measurable change in Filter ΔP (Pa) or HVAC operating regime (categorical). The expected outcome is therefore stated as a toolchain gate metric rather than a domain primitive metric — this is the constitutional limit of what a toolchain Bill can claim.

- **Toolchain gate metric — Build success rate:** Before enactment: 0 % (`pio run` fails immediately with "board not found"). After enactment (any candidate): 100 % of `pio run` (or `arduino-cli compile`) attempts must succeed on the first attempt for this Bill to be considered enacted.
- **Toolchain gate metric — Flash success rate (HIL smoke test, Stage 0):** Before enactment: not measurable (build fails before flash). After enactment: first flash attempt must produce clean UART output on `/dev/cu.usbmodem14301` at 115200 baud with no boot-loop — resolving E5 as "resolved YYYY-MM-DD" in the Open Anomalies table.
- **Domain primitive connection:** A working build and clean flash are the necessary preconditions for any Filter ΔP (Pa) measurement to be taken. Without a functional toolchain, no P1 or P2 signal can be validated on hardware. The toolchain is the physical instrument path — blocking it blocks all downstream primitive measurement.
- **Stage gate dependency:** Stage 0 (HIL Toolchain Lock) cannot open until this Bill is enacted and the smoke test passes. Per Amendment 2 (PROPOSED), Stage 1 cannot open until Stage 0 closes. The domain primitive evidence base is gated entirely behind this resolution.

---

## Rollback plan

- **For any enacted candidate (A, B, or C):** rollback is `git revert` of the merge commit on `toolchain/platform-resolution-xiaoblesense`, restoring `docs/toolchain_config.md` to its pre-enactment state.
- **No hardware BOM changes** are introduced by this Bill — no physical rollback of components is required.
- **If flashing under the enacted candidate produces a boot-loop** (E5 recurrence): power-cycle via USB disconnect → double-tap reset to force UF2 bootloader mount → drag-drop a known-good prior firmware image (or a Seeed factory-signed UF2 from `https://files.seeedstudio.com/...`) to restore a bootable state. Record the failure as strike 1 under Amendment 4 on the enacted candidate. If two more flash failures follow under the same candidate, Amendment 4 mandates a hard human stop and either (a) a new Bill selecting a different candidate or (b) a Judicial Hearing on the enacted candidate's continued standing.
- **Renode simulation path** is unaffected by A and B. Under C, if Renode bridge fails to locate build artifacts, temporary workaround is a hand-edited path override in `crucible.sim.renode.RenoneBridge`; the proper fix is tracked as a follow-up Bill.

---

## Attorney assignment recommendation

This Bill presents three candidates. A standard two-attorney hearing can cover the primary split:

- **Attorney A — argue Candidate A (community platform fork).** Strongest arguments: lowest immediate change surface; proven community adoption; `xiaoblesense` ID already in the toolchain record; does not require `arduino-cli` migration cost. Cite E2, E3, E4 (absence confirmed in stock), and the fork's community track record as *de facto* standard for XIAO nRF52. Vulnerability: must answer for E5 (boot-loop anomaly) — if the fork caused it, Candidate A may reproduce it.
- **Attorney B — argue Candidate C (arduino-cli with Seeed mbed core).** Strongest arguments: first-class Seeed support eliminates the entire platform-gap problem class; highest confidence of closing E5; Seeed official documentation [S1] is based on this toolchain. Cite E5 (the prior boot-loop as evidence that the PlatformIO path carries documented hardware risk) and the Thomas Jefferson Principle (the toolchain that gives the physical measurement the most reliable instrument path is the correct choice). Vulnerability: highest change surface; Renode build artifact path must be confirmed before argument is complete.
- Candidate B (custom board JSON) is the **fallback position**: if Attorney A's platform fork argument fails under cross-examination (fork abandoned, boot-loop reproduced) and Attorney B's arduino-cli argument fails (Renode path incompatibility confirmed), the Justice may direct a Candidate B implementation as a constrained default. It does not require a separate attorney unless the Justice determines the hearing needs a third position argued explicitly.

---

## Branch

`toolchain/platform-resolution-xiaoblesense`

One branch regardless of which candidate is enacted. The enacted candidate's changes are committed to this branch; the Justice specifies which candidate at ruling time. Branch is merged to `main` after the Stage 0 smoke test passes and the Open Anomalies entry for E5 is marked "resolved" in `docs/device_context.md`.

---

## Pre-hearing checklist (human actions required before `/judicial hear`)

1. Write E5 (boot-loop anomaly) to `docs/device_context.md` Open Anomalies table with the observed date, description, and current status "open".
2. Write E1 (`pio device list`, 2026-04-19) to `docs/device_context.md` Hardware Bring-up History table.
3. Ratify Amendment 3 (remove PROPOSED prefix in `docs/governance/amendments.md`) if you want the Bill's Amendment 3 grounding to be binding rather than advisory.
4. Confirm whether Amendment 4 and Amendment 7 should also be ratified before the hearing opens — both are cited as supporting grounding above.

---

*Ready for Judicial debate. Invoke `/judicial hear "XIAO nRF52840 Sense — Platform Resolution for xiaoblesense Board ID" A vs B` to assign attorneys and receive a ruling.*
