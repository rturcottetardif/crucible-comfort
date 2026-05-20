# Stage 1 Closeout — Simulation (Signal-Only Regression + Firmware)

**Frozen:** 2026-05-19
**Authorized by:** Justice (direct confirmation in session, 2026-05-19)
**Police audit:** CLEAN (Justice statement at gate)
**Branch:** stage1/firmware (last merge before gate)

**Stage gate record:** `docs/governance/handoff.md` does not exist at closeout time.
Exit criteria are recorded here from Justice's direct confirmation and the
Standing Order Record (Path B Waiver, 2026-05-19 — case_law.md):

| Gate | Description | Result | Date |
|---|---|---|---|
| Path A | Signal-only regression — 8/8 profiles PASS | PASS | 2026-05-19 |
| Path B | Renode firmware-in-emulator | WAIVED — RenoneBridge not built | 2026-05-19 |

**Note:** Path B waiver is operative and binding. RenoneBridge infrastructure
(`.resc`, `sim_usbd_stub.py`, `sim_uart_stub.py`) is deferred to a future Bill
before Stage 2 gate if firmware-in-emulator validation is required at that stage.

**Key commits:**

| Commit | Description |
|---|---|
| b69d057 | First scaffold — generates src/ (events.py, analysis.py, plot.py, signals.py, algorithm.py) |
| (stage1/signals-harmonic-vibration-model) | Bill 1 enacted — additive harmonic vibration signal model |
| (stage1/algorithm-regime-cold-shoulder) | Bill 2-A enacted — T_COLD_SHOULDER + proxy inversion infrastructure |
| (stage1/algorithm-regime-warm-shoulder) | Bill 2-B enacted — T_WARM_SHOULDER + three-outcome classifier |
| (stage1/algorithm-fusion-weight) | Bill 2-D enacted — W_VIB physics-derived fusion weight |
| (stage1/ct-600hz-fusion) | Bill 3 enacted — CT 600 Hz upgrade + regime-split W_VIB_HEATING / W_VIB_COOLING |
| (stage1/firmware) | Bill 4 enacted — Stage 1 firmware + ALERT UART event |
| acddbff | hw: schematic sub-agents + PCB layout generator + SVG export |

---

## Amendments Ratified During Stage 1

| # | Title | Ratified |
|---|---|---|
| 5 | Simulation is the Hardware Proxy | 2026-04-27 |
| 6 | Signal Plot Mandate | 2026-04-27 |
| 7 | Calibration Discipline | 2026-04-27 |
| 9 | Hardware Optimization Transparency | 2026-04-27 |
| 11 | Scaffold Immutability | 2026-04-27 |

Amendments 8 and 10 remain PROPOSED (not ratified during Stage 1).

---

## Enacted Bills Summary

| Bill | Case | What changed | Key constants |
|---|---|---|---|
| Bill 1 — Additive Harmonic Vibration Signal Model | Case 2 | `src/signals.py` implement `generate()` — 8 profiles, 4 signals, harmonic IMU model | A_FUND_CLEAN=0.05g, ALPHA=1, SIGMA_NOISE_G=0.002g, F_FUND_HEATING=20Hz, F_FUND_COOLING=32Hz, I0_HEATING=4.0A, I0_COOLING=9.0A, BETA=0.12, T_HEATING=−10°C, T_COOLING=25°C, SPL0=55dBSPL |
| Bill 2-A — Regime Classifier Cold Shoulder + Proxy Inversion Infrastructure | Case 3 | `src/algorithm.py` implement `run()` — two-outcome classifier, gravity-subtracted RMS, CT inversion, provisional 50/50 fusion | T_COLD_SHOULDER=5.0°C |
| Bill 2-B — Regime Classifier Warm Shoulder | Case 4 | `src/algorithm.py` — three-outcome classifier adds "off" regime (5–15°C band) | T_WARM_SHOULDER=15.0°C |
| Bill 2-D — Physics-Derived Vibration Fusion Weight | Case 5 | `src/algorithm.py` Step F — replaces 50/50 fusion with min-variance weight | W_VIB=0.9999 (superseded by Bill 3) |
| Bill 3 — CT Sampling Rate Upgrade | Case 6 | `src/signals.py` FS_CT_HZ 1→600Hz raw AC waveform; `src/algorithm.py` Step E true RMS + regime-split fusion | W_VIB_HEATING=0.9144, W_VIB_COOLING=0.6785; supersedes W_VIB scalar |
| Bill 4 — Stage 1 Algorithm Firmware + ALERT UART Event | Case 7 | `firmware/stage1_algo_usb/stage1_algo_usb.ino` created; `src/events.py` AlertEvent added; `src/analysis.py` ALERT_DEF + PARSER extended | ALERT_THRESH=1.8, N_WINDOW=1660, RMS_HARM_FACTOR=0.7546 |

---

## Cases Summary

| Case | Ruling (one line) |
|---|---|
| SOR — Direct ΔP Rejected | Direct differential-pressure sensing is permanently rejected; indirect sensing (IMU + mic + CT conditioned on P2) is the mandatory primary architecture. |
| SOR — First Scaffold Authorization | `/toolchain scaffold` ran once at b69d057; `src/events.py`, `src/analysis.py`, `src/plot.py` frozen at Stage 1 gate; `src/signals.py` and `src/algorithm.py` are implementation stubs subject to Bills, not the freeze. |
| Case 2 | Bill 1's eleven constants are physically derived signal-model predictions exempt from Amendment 7's one-per-Bill ceiling; algorithm-calibration constants remain subject to it. |
| Case 3 | Bill 2-A enacted directly; establishes that the Justice may rule directly when the drafter's pre-flagged tensions are uncontested. |
| Case 4 | Bill 2-B enacted directly; Case 3 procedural precedent applied a second time. |
| Case 5 | Bill 2-D enacted; first direct Justice ruling on a contested point — physics-derived value (0.9999) prevails over design simplification (1.000); Article I grounds rounding discipline. |
| Case 6 | Bill 3 enacted directly; CT 600 Hz upgrade restores CT as a meaningful ΔP proxy (8.6% heating, 32.2% cooling); W_VIB scalar superseded by regime-split W_VIB_HEATING/W_VIB_COOLING. |
| Case 7 | Bill 4 enacted directly; Stage 1 firmware + ALERT event; events.py/analysis.py modification authorized before Stage 1 gate close per Amendment 11 "before gate close" window. |
| SOR — Path B Waiver | Renode path waived for Stage 1 gate; Path A 8/8 PASS is the sole gate criterion; RenoneBridge build deferred to a future Bill before Stage 2 gate. |

---

## Open Findings / Deferred Items

| Item | Source | Deferred to |
|---|---|---|
| RenoneBridge infrastructure (`.resc`, `sim_usbd_stub.py`, `sim_uart_stub.py`) | Path B Waiver SOR (2026-05-19) | Future Bill before Stage 2 gate (if firmware-in-emulator validation required) |
| Bill 1-Mic — microphone acoustic signal model | Bill 1, Case 2 | Future Bill (mic placeholder = zero array at Stage 1) |
| Bill 2-C — microphone proxy in algorithm | Case 3 Bill 2 roadmap | Future Bill (contingent on Bill 1-Mic) |
| Shoulder-season simulation profile (clean_off, outside_temp ≈ 10°C) | Case 4 evidence gap | Future Bill (follow-up obligation on Bill 1 profile registry) |
| Amendment 9 BOM Bill — CT redundancy for ΔP fusion at long decision windows | Case 5 architectural finding | Future Bill (Stage 3 pre-field evaluation) |
| Bill 2-D-window — decision window length evaluation | Case 5 architectural finding | Future Bill (Stage 2/3 field window calibration) |
| ALPHA field calibration (currently 1; Stage 2 fit) | Bill 1/4, Cases 2/7 | Stage 2 field validation — update via Bill if ALPHA ≠ 1 |
| CT BOM Bills (CT clamp circuit, OneWire pull-up + shielded cable, IP66 enclosure) | Direct ΔP Rejection SOR | Active BOM Bills downstream of Stage 1 architecture |

---

## Compacted Precedents

Eight entries from `docs/governance/case_law.md` are frozen under this closeout.
Full argument text lives in the live case law record. The cards below are the
operational law for Stage 2 and beyond.

Full record: `docs/governance/case_law.md`

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Standing Order — Direct ΔP Sensing Rejected; Indirect Mandatory
Frozen: Stage 1 | Date: 2026-05-19
Full record: docs/governance/case_law.md#standing-order-record--direct-p-sensing-rejected-indirect-mandatory
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
Direct differential-pressure sensing (any MEMS ΔP transducer) is permanently
rejected as a primary or hybrid path; IMU vibration + microphone acoustic +
CT current conditioned on outside_temp regime (P2) is the mandatory primary
sensing architecture.

NEXT STAGE ENGINEER MUST:
- Ground all algorithm and firmware changes in the indirect-sensing triad
  (IMU + mic + CT), conditioned on P2 (outside_temp regime proxy).
- Treat sw-advisor Suggestions 1-A and 2-A as the active architectural baseline.
- Cite the two independent rejection grounds (physical infeasibility +
  SDP810-class environmental incompatibility) when defending the architecture
  against any future hardware proposal involving a ΔP transducer.

NEXT STAGE ENGINEER MUST NEVER:
- Introduce a direct ΔP sensor (Sensirion SDP810, Honeywell HSCMRRD005MD, or
  any equivalent MEMS differential transducer) without a new Judicial Hearing
  that addresses both rejection grounds jointly.
- Treat a new sensor catalog alone as sufficient to reopen this precedent —
  the deployment-model constraint (no pneumatic access from exterior side wall)
  is the dominant rejection ground and is independent of sensor specification.

PHYSICAL BASIS:
Two independent grounds. (1) Device Purpose: mounting restricted to HVAC housing
exterior side wall — no pneumatic access to filter plenum without drilling through
outer casing, insulation, and inner duct liner (two points). Incompatible with
self-install model; voids UL listing; no standardized geometry. (2) SDP810 class:
operating range −20 to +85°C vs project hard lower limit −40°C; condensate
freezing at 0°C blocks pneumatic ports; IP20 rating fails 0–100% RH with
condensation. Both grounds documented in case_law.md SOR (2026-04-27).

REOPENS ONLY IF:
Device Purpose is amended to permit a deployment model with pneumatic access
(e.g., in-duct or factory-installed at HVAC OEM), AND a sensor class is
identified that meets the full envelope including −40°C cold-soak and 0–100% RH
with condensation on pneumatic ports. Both conditions required jointly.
─────────────────────────────────────────────────────────────
```

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Standing Order — First Scaffold Authorization
Frozen: Stage 1 | Date: 2026-05-19
Full record: docs/governance/case_law.md#standing-order-record--first-scaffold-authorization
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
`/toolchain scaffold` ran exactly once at commit b69d057 (2026-04-27); the
generated trio (src/events.py, src/analysis.py, src/plot.py) is now frozen
under Amendment 11; src/signals.py and src/algorithm.py are implementation
stubs subject to Bills, not to the freeze.

NEXT STAGE ENGINEER MUST:
- Treat src/events.py, src/analysis.py, and src/plot.py as immutable for the
  remainder of the project unless explicit human authorization plus a Bill
  permit re-scaffolding.
- Use src/signals.py (generate()) and src/algorithm.py (run()) as the
  authoritative Python algorithm model; update them only via enacted Bills.
- Cite this SOR when justifying why the scaffold trio cannot be silently
  regenerated during debugging.

NEXT STAGE ENGINEER MUST NEVER:
- Re-run `/toolchain scaffold` without an enacted Bill explicitly authorizing it.
- Modify src/events.py, src/analysis.py, or src/plot.py outside the Bill
  process, even for minor label or formatting changes.
- Treat a change to docs/device_context.md Signal Inventory or
  docs/toolchain_config.md Firmware UART Format as implicitly authorizing
  re-scaffold; a Bill is required.

PHYSICAL BASIS:
Commit b69d057, 2026-04-27. Scaffold input: SESSION_END session_end_marker;
events `reading` and `metric` as defined in docs/toolchain_config.md Firmware
UART Format. No prior src/ directory existed before this commit (confirmed in
SOR text).

REOPENS ONLY IF:
An enacted Bill explicitly names re-scaffold as its authorized action and cites
a physical change to the Signal Inventory or Firmware UART Format that is
constitutionally incompatible with the frozen trio.
─────────────────────────────────────────────────────────────
```

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Case 2 — Stage 1 Signal Model: Eleven-Constant A7 Tension
Frozen: Stage 1 | Date: 2026-05-19
Full record: docs/governance/case_law.md#case-2-stage-1-signal-model--eleven-constant-a7-tension
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
Signal-model parameters in src/signals.py (physically derived, falsifiable
Stage 2 predictions) are exempt from Amendment 7's one-per-Bill ceiling;
algorithm-calibration constants in src/algorithm.py (tuned, governing what
the algorithm decides) remain subject to it.

NEXT STAGE ENGINEER MUST:
- Apply the A7 one-per-Bill ceiling to any new constant introduced in
  src/algorithm.py that governs detection behaviour (threshold, weight, cutoff).
- Document every constant — in either src/signals.py or src/algorithm.py —
  with the four-line Amendment 7 derivation block (primitive, derivation,
  value, trace).
- Treat the eleven Bill 1 constants as falsifiable Stage 2/3 predictions;
  update each via a Bill when field evidence contradicts the prior.

NEXT STAGE ENGINEER MUST NEVER:
- Introduce a tuned (fitted without physical derivation) constant into
  src/algorithm.py under the claim of being a "signal-model parameter."
  The class distinction is file-specific and governed by this ruling.
- Bypass the one-per-Bill ceiling for src/algorithm.py constants by
  grouping them as "jointly self-consistent" without Justice ruling;
  Bill 3's two-constant exception required and received Justice direct
  acceptance citing the minimum-variance self-consistency argument.

PHYSICAL BASIS:
Gate 0.2 az_dc = 0.975 g (2026-04-20); Gate 0.3 stationary rms_g ∈
[1.0014, 1.0056], noise band ≈ 0.004 g peak-to-peak ≈ 2σ at σ = 0.002 g
over 50-sample windows. Both measurements ground SIGMA_NOISE_G and A_Z_DC
and confirm the eleven Bill 1 constants are hardware-grounded predictions,
not tuning knobs. Source: docs/device_context.md Test Results, Gates 0.2/0.3.

REOPENS ONLY IF:
A Judicial Hearing is explicitly declared on Case 2 by name, citing a
physical change (new sensor class, new signal domain, new population) that
introduces a category of constant not covered by the signal-model /
algorithm-calibration distinction established here.
─────────────────────────────────────────────────────────────
```

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Case 3 — Bill 2-A: Regime Classifier Cold Shoulder + Proxy Inversion Infrastructure
Frozen: Stage 1 | Date: 2026-05-19
Full record: docs/governance/case_law.md#case-3-bill-2-a--regime-classifier-cold-shoulder--proxy-inversion-infrastructure
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
T_COLD_SHOULDER = 5.0°C (ASHRAE 90.1 Canadian supplement heating balance-point
lower edge) is the enacted lower regime boundary in src/algorithm.py; gravity-
subtracted RMS + CT inversion + provisional 50/50 fusion (replaced by Bill 2-D)
is the enacted algorithm structure; the Justice may rule directly when
drafter-flagged tensions are uncontested.

NEXT STAGE ENGINEER MUST:
- Use T_COLD_SHOULDER = 5.0°C as the heating/shoulder boundary in all
  algorithm and firmware that implements regime classification.
- Compute gravity-subtracted AC RMS as: az_ac = imu_accel_z − A_Z_DC;
  rms_ac = sqrt(mean(az_ac²)) — this is the enacted Step C.
- Import signal-model constants (A_Z_DC, A_FUND_CLEAN, ALPHA, I0_HEATING,
  I0_COOLING, BETA) from src/signals.py into src/algorithm.py (cross-module
  import is a mathematical requirement of forward-model inversion, not an
  architectural choice — Case 3 ruling).
- Falsify T_COLD_SHOULDER against Stage 2/3 DS18B20 field readings; update
  via a Bill if the boundary is wrong.

NEXT STAGE ENGINEER MUST NEVER:
- Change T_COLD_SHOULDER without an enacted Bill citing field evidence.
- Decouple the algorithm inversion constants from the signal-model forward
  constants (they must use the same physical relationships — Case 3 operative).
- Treat the conservative "cooling" default (ndarray path, no outside_temp)
  as a free design parameter; it is the enacted behaviour from Case 3 and
  persists through Case 4.

PHYSICAL BASIS:
ASHRAE 90.1 Canadian supplement balance-point lower edge ≈ 5°C for commercial
rooftop heat-pump / gas-furnace systems. Gate 0.3 (2026-04-20): stationary
rms_g ∈ [1.0014, 1.0056] vs vigorous-motion rms_g ∈ [1.0228, 2.0154] —
confirms non-gravity-subtracted RMS suffers false positive on gentle tilt;
gravity subtraction reduces stationary rms_ac_g to noise floor ≈ 0.002 g.
Source: docs/device_context.md Test Results, Gate 0.3.

REOPENS ONLY IF:
A Judicial Hearing is explicitly declared on Case 3 by name, citing Stage 2/3
DS18B20 field measurements that place the actual heating/shoulder transition
outside 5.0°C by more than the Signal Inventory noise floor.
─────────────────────────────────────────────────────────────
```

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Case 4 — Bill 2-B: Regime Classifier Warm Shoulder
Frozen: Stage 1 | Date: 2026-05-19
Full record: docs/governance/case_law.md#case-4-bill-2-b--regime-classifier-warm-shoulder-three-outcome-classifier
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
T_WARM_SHOULDER = 15.0°C (ASHRAE 90.1 Canadian supplement cooling balance-point
upper edge) is the enacted upper regime boundary; the three-outcome classifier
(heating / off / cooling) completes the Amendment 1 P2 primitive contract by
making hvac_regime = "off" reachable from run().

NEXT STAGE ENGINEER MUST:
- Apply the three-outcome regime classifier in all algorithm and firmware:
  temp < 5.0°C → "heating"; 5.0 ≤ temp < 15.0°C → "off";
  temp ≥ 15.0°C → "cooling".
- Bypass CT inversion (dp_ratio_ct) when hvac_regime = "off" — blower
  stopped means ct ≈ 0 A and the inversion is undefined (Case 6 / Bill 3).
- Return hvac_regime = "off" in any real-hardware or simulation run where
  outside_temp falls in [5.0, 15.0) °C.
- Falsify T_WARM_SHOULDER against Stage 2/3 DS18B20 field readings; update
  via a Bill if the boundary is wrong.

NEXT STAGE ENGINEER MUST NEVER:
- Use a two-outcome classifier (heating/cooling only) in any Stage 2+ code
  — the "off" regime is a P2 constitutional requirement (Amendment 1).
- Change T_WARM_SHOULDER without an enacted Bill citing field evidence.
- Change the ndarray-path default from "cooling" to "off" without a Bill
  and physical justification (Case 4 operative: the default preserves
  Bill 2-A's conservative bias for callers without outside_temp access).

PHYSICAL BASIS:
ASHRAE 90.1 Canadian supplement balance-point upper edge ≈ 15°C for commercial
rooftop heat-pump / gas-furnace systems. Gate 0.3 stationary rms_g ∈
[1.0014, 1.0056] (blower-off signal) vs vigorous-motion rms_g ∈ [1.0228, 2.0154]
(blower-on signal) — confirms the physical premise that an "off" unit produces
a near-stationary signal distinct from heating or cooling. Source:
docs/device_context.md Test Results, Gate 0.3.

REOPENS ONLY IF:
A Judicial Hearing is explicitly declared on Case 4 by name, citing Stage 2/3
DS18B20 field measurements that place the actual shoulder-season boundary
outside 15.0°C by more than the Signal Inventory noise floor.
─────────────────────────────────────────────────────────────
```

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Case 5 — Bill 2-D: Physics-Derived Vibration Fusion Weight (W_VIB)
Frozen: Stage 1 | Date: 2026-05-19
Full record: docs/governance/case_law.md#case-5-bill-2-d--physics-derived-vibration-fusion-weight-wvib
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
W_VIB = 0.9999 (minimum-variance inverse-variance weight on the vibration proxy)
is the constitutionally correct adoption at 1 Hz CT sampling; the physics-derived
value (0.9999) prevails over design simplification (1.000, formal CT retirement)
because Article I requires physical derivation over architectural rounding; W_VIB
is superseded by W_VIB_HEATING / W_VIB_COOLING at 600 Hz (Bill 3 / Case 6).

NEXT STAGE ENGINEER MUST:
- Use W_VIB_HEATING = 0.9144 and W_VIB_COOLING = 0.6785 (Bill 3 / Case 6) as the
  operative fusion weights — they supersede W_VIB = 0.9999 in all current code.
- If CT sampling rate ever reverts to 1 Hz (e.g., power budget constraint),
  re-derive W_VIB from the minimum-variance formula using the 1 Hz noise
  parameters and enact the result via a Bill before deploying.
- Treat the Case 5 precedent on rounding discipline as binding: when a
  physical derivation yields a specific value, that value is adopted; rounding
  to a design-convenient integer requires an explicit Bill.

NEXT STAGE ENGINEER MUST NEVER:
- Round a physics-derived weight to a design-convenient value (e.g., 0.9999 → 1.0,
  effectively retiring CT from fusion) without a Bill and Justice ruling.
- Formally retire CT from ΔP fusion without an Amendment 9 BOM Bill — CT's
  low weight at 1 Hz is an architectural artifact of sample count, not a
  physical finding that CT carries no ΔP information.

PHYSICAL BASIS:
Signal Measurements (commit 89694ab, 2026-04-27): near_clog_heating spread
min = 1.783 (below the 1.8 alert edge) under 50/50 fusion — detection-margin
grazing that motivated W_VIB. Heating-vs-cooling spread asymmetry 1.7× confirmed.
σ_vib ≈ 9.2 × 10⁻⁴ (1660 samples/sec, SIGMA_NOISE_G = 0.002 g);
σ_ct_H = 0.1042, σ_ct_C = 0.04630 (1 Hz). W_VIB = 0.99992 (heating) and 0.99961
(cooling); regime difference 3.1 × 10⁻⁴ — sub-noise-floor, scalar adopted.
Source: docs/device_context.md Signal Measurements; docs/governance/case_law.md
Case 5 physical basis.

REOPENS ONLY IF:
A Judicial Hearing is explicitly declared on Case 5 by name, citing a hardware
change (new CT sensor, new sample rate, new decision window) that alters the
minimum-variance computation by more than the SIGMA_NOISE_G relative uncertainty
(≈ 50% on σ_vib). Note: Bill 3 / Case 6 already superseded the numerical value
for the 600 Hz architecture; Case 5 governs the rounding-discipline principle.
─────────────────────────────────────────────────────────────
```

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Case 6 — Bill 3: CT Sampling Rate Upgrade to 600 Hz and Regime-Split Fusion Weights
Frozen: Stage 1 | Date: 2026-05-19
Full record: docs/governance/case_law.md#case-6-bill-3--ct-sampling-rate-upgrade-to-600-hz-and-regime-split-fusion-weights
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
CT sampling rate is upgraded to 600 Hz; W_VIB_HEATING = 0.9144 and
W_VIB_COOLING = 0.6785 are the operative minimum-variance fusion weights for all
Stage 2+ code; the W_VIB = 0.9999 scalar from Bill 2-D is superseded and removed.

NEXT STAGE ENGINEER MUST:
- Sample CT at 600 Hz in firmware and signal model; compute true RMS over the
  1-second window (600 samples): ct_rms = sqrt(mean(arr²)).
- Use W_VIB_HEATING = 0.9144 in the Step F fusion when hvac_regime = "heating".
- Use W_VIB_COOLING = 0.6785 in the Step F fusion when hvac_regime = "cooling".
- Bypass CT inversion entirely when hvac_regime = "off" (blower stopped,
  ct ≈ 0 A, inversion undefined — mathematical requirement, not policy).
- Treat both weights as Stage 2 falsifiable predictions; re-derive via a Bill
  if σ_ct_current deviates materially from 0.05 A per sample.

NEXT STAGE ENGINEER MUST NEVER:
- Reintroduce W_VIB = 0.9999 scalar in any new file or firmware; it is
  superseded by the regime-split weights.
- Use a single regime-independent W_VIB at 600 Hz — the regime split
  (ΔW = 0.236) is above the noise floor and is constitutionally required.
- Apply the CT inversion step when hvac_regime = "off" — this is a
  mathematical constraint, not a design choice.

PHYSICAL BASIS:
σ_ct_eff = 0.05/√(2×600) = 0.001443 A at 600 Hz.
W_VIB_HEATING: σ_ct_H = 0.003007 → W = 9.042e-6/(8.464e-7+9.042e-6) = 0.9144.
W_VIB_COOLING: σ_ct_C = 0.001336 → W = 1.786e-6/(8.464e-7+1.786e-6) = 0.6785.
CT contribution: 8.6% heating, 32.2% cooling.
Derivation inputs: SIGMA_NOISE_G (Gate 0.3, 2026-04-20), I0_HEATING=4.0/
I0_COOLING=9.0/BETA=0.12 (Bill 1, Case 2), 0.05 A per-sample noise spec.
Source: docs/governance/bills/stage1-ct-600hz.md §3.

REOPENS ONLY IF:
A Judicial Hearing is explicitly declared on Case 6 by name, citing a Stage 2
CT ADC measurement that places σ_raw materially outside 0.05 A, or a hardware
change that alters the CT clamp specification, or a change to the decision window
length. A new opinion on fusion weight balance alone is not sufficient.
─────────────────────────────────────────────────────────────
```

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Case 7 — Bill 4: Stage 1 Algorithm Firmware + ALERT UART Event
Frozen: Stage 1 | Date: 2026-05-19
Full record: docs/governance/case_law.md#case-7-bill-4--stage-1-algorithm-firmware--alert-uart-event
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
Bill 4 enacted the Stage 1 firmware (firmware/stage1_algo_usb/stage1_algo_usb.ino)
with ALERT UART event, AlertEvent dataclass, and PARSER extension; modifications
to src/events.py and src/analysis.py before Stage 1 gate close were authorized
by this Bill per Amendment 11's "before gate close" window; the scaffold trio is
now fully frozen as of this closeout.

NEXT STAGE ENGINEER MUST:
- Treat src/events.py, src/analysis.py, and src/plot.py as frozen (Amendment 11);
  any modification requires an enacted Bill.
- Use the ALERT event format: `ALERT ts=<ms> dp=<float> regime=<str> alert=<0|1>`
  for all firmware UART emission of filter detection verdicts.
- Include `#include "Adafruit_TinyUSB.h"` at the top of every .ino targeting
  Seeeduino:nrf52:xiaonRF52840Sense (Case 1 / Case 1.1 — still operative).
- Build Stage 1+ firmware with --build-path build/arduino/xiao_nrf52840_sense/.
- If Stage 2 requires Renode validation, build RenoneBridge infrastructure
  (.resc, sim_usbd_stub.py, sim_uart_stub.py) via an enacted Bill first.
- Verify the Serial1 → UARTE0 mapping in the first Renode run (noted as a
  Stage 1 falsifiable finding in Bill 4).

NEXT STAGE ENGINEER MUST NEVER:
- Flash firmware to physical hardware without explicit human approval
  (Article II — irreversible).
- Modify src/events.py, src/analysis.py, or src/plot.py without an enacted Bill.
- Use CT fusion weights W_VIB_HEATING / W_VIB_COOLING in the Renode (Path B)
  path — Renode injects IMU-only samples; CT is absent from the Path B path
  by structural constraint of RenoneBridge (Bill 4 / Case 7 finding).

PHYSICAL BASIS:
Path A regression: 8/8 profiles PASS (2026-05-19). Firmware constants trace
identically to algorithm.py (Bills 1–3): A_FUND_CLEAN=0.05g, A_Z_DC=1.0g,
ALPHA=1, RMS_HARM_FACTOR=0.7546, ALERT_THRESH=1.8, N_WINDOW=1660. ALPHA=1
simplification (dp_ratio = rms_ac/denominator, no powf) is an analytic identity,
not a new constant. Source: docs/governance/bills/stage1-firmware.md §4.

REOPENS ONLY IF:
A Judicial Hearing is explicitly declared on Case 7 by name, citing a Stage 2
hardware result (Serial1 → UARTE0 mapping failure, or ALPHA field calibration
returning ALPHA ≠ 1) that was identified as a Stage 1 falsifiable finding.
─────────────────────────────────────────────────────────────
```

---

```
─────────────────────────────────────────────────────────────
SETTLED PRECEDENT: Standing Order — Stage 1 Path B (Renode) Waiver
Frozen: Stage 1 | Date: 2026-05-19
Full record: docs/governance/case_law.md#standing-order-record--stage-1-path-b-renode-waiver
─────────────────────────────────────────────────────────────

WHAT IS DECIDED (one sentence):
Renode Path B is waived for the Stage 1 gate; Path A alone (8/8 PASS,
2026-05-19) satisfies the Stage 1 exit criterion; RenoneBridge infrastructure
is deferred to a future Bill before Stage 2 gate if firmware-in-emulator
validation is required at that stage.

NEXT STAGE ENGINEER MUST:
- Treat Stage 1 as closed on Path A evidence alone (8/8 PASS). No Renode
  run is required retroactively.
- Before Stage 2 gate closes, evaluate whether Renode validation is required
  for that stage's exit criteria; if so, enact a Bill to build RenoneBridge
  infrastructure before starting Stage 2 work.
- If RenoneBridge is built, validate the Serial1 → UARTE0 mapping and confirm
  CT-absent Renode path parity (dp_ratio_vib only, regime="cooling" default).

NEXT STAGE ENGINEER MUST NEVER:
- Treat the Path B waiver as permanent or as precedent that Renode validation
  is always optional — the waiver applies to Stage 1 only and was granted
  because RenoneBridge infrastructure was never built, not because Path B
  is constitutionally unnecessary.
- Skip the Bill process to build or modify RenoneBridge infrastructure —
  it is a new toolchain component governed by Amendment 3.

PHYSICAL BASIS:
Regression run 2026-05-19: 8 PASS, 0 FAIL, 0 ERROR across all registered
Stage 1 profiles. Renode binary present at /usr/local/bin/renode; no .resc
script, no sim_usbd_stub.py, no sim_uart_stub.py — Path B structurally
unavailable. Source: Standing Order Record in docs/governance/case_law.md
(2026-05-19).

REOPENS ONLY IF:
A Judicial Hearing is explicitly declared on this SOR by name, citing a
Stage 2 failure that would have been caught by Path B (firmware-level bug
not visible in signal-only simulation). A new opinion that Renode validation
is important is not sufficient to reopen this precedent.
─────────────────────────────────────────────────────────────
```

---

## Closeout Execution Record

| Step | Action | Result |
|---|---|---|
| 1 | Read docs/governance/case_law.md | 7 Active entries identified for Stage 1 (Cases 2–7 + Path B Waiver SOR) + 2 SORs without Case numbers |
| 2 | Read docs/governance/handoff.md | FILE MISSING — proceeded under Justice's direct session confirmation (Path B Waiver SOR: "stage-compactor may proceed") — identical precedent to Stage 0 |
| 3 | Read docs/governance/amendments.md | 5 amendments ratified during Stage 1: A5, A6, A7, A9, A11 |
| 4 | Read docs/governance/bills/stage1-*.md | 6 bills read: Bills 1, 2-A, 2-B, 2-D, 3, 4 |
| 5 | Read docs/governance/stage_0_closeout.md | Format and conventions confirmed |
| 6 | Produced Settled Precedent Cards | 8 cards written above (2 SORs + Cases 2–7 + Path B Waiver SOR) |
| 7 | Wrote docs/governance/stage_1_closeout.md | This file |
| 8 | Freeze entries in case_law.md | Applied FROZEN markers to all 8 Active entries |
| 9 | Commit | See commit hash below |

**Committed:** see git log — `chore: close Stage 1 — compact case law, freeze precedents`
