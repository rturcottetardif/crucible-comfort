# Crucible Case Law

This file records all Judicial Hearing rulings. Entries are written by the prevailing
attorney immediately after the Justice's ruling, before any implementation begins.

Live entries accumulate full argument text. Frozen entries (after stage closeout via
`stage-compactor`) contain only the compact operational record.

---

## Active Precedents

### Standing Order Record — Direct ΔP sensing rejected; indirect mandatory

**[FROZEN — Stage 1 closed 2026-05-19]**
**Compact card:** docs/governance/stage_1_closeout.md

**Date:** 2026-04-27
**Source:** hw-advisor full review (/advisor hw, this session)
**Cross-references:** sw-advisor scoping pass (this session, "Hardware Alternative" callout)

**Ruling (operative):** Direct differential-pressure sensing (Sensirion SDP810,
Honeywell HSCMRRD005MD, or any equivalent MEMS differential transducer) is
**rejected** as a primary or hybrid-commissioning path for ComfortSense P1
(Filter ΔP) measurement. **Indirect sensing — IMU vibration + microphone
acoustic + CT current, conditioned on outside_temp regime per P2 — is the
mandatory primary architecture.**

**Two independent grounds for rejection** (either one sufficient on its own):

1. **Physical infeasibility under the deployment model.** Device Purpose
   restricts mounting to the side of the HVAC housing (Out-of-scope: top,
   indoor, in-duct). Filter plenums are internal to the packaged unit; no
   pneumatic access from the exterior side wall without drilling through the
   outer casing, insulation, and inner duct liner at two separate points
   (upstream + downstream of the filter). This violates the no-commissioning
   self-install model, voids unit UL listing in most jurisdictions, and has
   no standardized geometry across HVAC manufacturers. Hybrid commissioning-
   only path fails the same test — it requires the same pneumatic access
   work even if the sensor is removed afterward.

2. **Environmental incompatibility for the SDP810 sensor class.** Operating
   Envelope hard lower limit is **−40 °C** ambient; SDP810 datasheet operating
   range is **−20 °C to +85 °C**. At cold-soak the MEMS element produces
   offset shifts indistinguishable from filter loading — false-positive alert
   in winter is the worst-case false positive ComfortSense exists to prevent.
   Pneumatic ports fill with condensate at every dew-point crossing and
   freeze below 0 °C, blocking the ports and driving the reading to maximum —
   indistinguishable from full clog. SDP810 IP20 rating fails the
   0–100% RH with condensation envelope. A future sensor class meeting all
   three constraints (−40 °C cold-soak, heated/anti-condensate ports,
   IP65+ rated) does not lift constraint (1) — pneumatic access is still
   required.

**Effect on Stage 1 work:**
- sw-advisor Suggestion 1-A (Additive Harmonic Vibration Model) and
  Suggestion 2-A (Gravity-Subtracted RMS + Regime-Conditioned Threshold)
  remain the active architectural baseline.
- Bills 1 and 2 (signal model + algorithm architecture) proceed without
  architectural ambiguity.
- Three new BOM Bills surfaced by hw-advisor (CT clamp circuit, OneWire
  pull-up + shielded cable, IP66 enclosure with rigid aluminium standoff)
  are downstream of this finding — they specify the indirect-sensing
  hardware path.

**Reopens only if:**
- Device Purpose is amended to permit a deployment model with pneumatic
  access (e.g., in-duct or factory-installed at HVAC OEM), AND
- A sensor class is identified that meets the full operating envelope
  including −40 °C cold-soak and 0–100% RH with condensation on pneumatic
  ports. Both conditions required jointly. A new opinion or a new sensor
  catalog alone does not reopen this finding — the deployment-model
  constraint is the dominant rejection ground.

---

### Standing Order Record — First scaffold authorization

**[FROZEN — Stage 1 closed 2026-05-19]**
**Compact card:** docs/governance/stage_1_closeout.md

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

### Case 2: Stage 1 Signal Model — Eleven-Constant A7 Tension

**[FROZEN — Stage 1 closed 2026-05-19]**
**Compact card:** docs/governance/stage_1_closeout.md

**Date:** 2026-04-27
**Positions:** A — model parameters exempt from A7 one-per-Bill | B — A7 applies to all source constants — split into 11 Bills
**Prevailing position:** A
**Justice's ruling:** Bill 1 enacts as drafted. The eleven constants (A_FUND_CLEAN, ALPHA, SIGMA_NOISE_G, F_FUND_HEATING, F_FUND_COOLING, I0_HEATING, I0_COOLING, BETA, T_HEATING, T_COOLING, SPL0) are admitted into `src/signals.py` in a single commit on branch `stage1/signals-harmonic-vibration-model`. Amendment 7's one-per-iteration ceiling does not apply to physically derived signal-model parameters of `src/signals.py`.
**Physical/empirical basis:** "Calibration constant" in A7 is a term of art defined within A7 paragraph 2 — its target is *tuned* constants (fitted without derivation, requiring re-tuning at every hardware or population change). The eleven constants of Bill 1 are physically *derived* predictions, each carrying the four-line A7 derivation block traced to Amendment 1 primitives (P1 Filter ΔP, P2 HVAC operating regime) and Stage 0 hardware evidence (Gate 0.2 az_dc = 1.03 g; Gate 0.3 stationary noise band ≈ 0.004 g peak-to-peak ≈ 2σ at σ = 0.002 g). Derived constants are falsifiable Stage 2 predictions, not tuning knobs.
**Device outcome protected:** Both heating-regime and cooling-regime detection paths must remain testable in simulation. Splitting the eleven constants into eleven sequential Bills would produce ten intermediate `signals.py` states that cannot generate a runnable profile, render a plot under Amendment 6, or test the cooling-regime false-negative scenario — the most commercially costly failure mode in the Device Purpose. Atomic admission preserves end-to-end testability of the regime-conditioned algorithm.
**Conditions:** None.
**Enacted bill:** Bill 1 — Implement Additive Harmonic Vibration Signal Model in src/signals.py (`docs/governance/bills/stage1-signal-model.md`).
**Implementation branch:** stage1/signals-harmonic-vibration-model

---

### Case 3: Bill 2-A — Regime Classifier Cold Shoulder + Proxy Inversion Infrastructure

**[FROZEN — Stage 1 closed 2026-05-19]**
**Compact card:** docs/governance/stage_1_closeout.md

**Date:** 2026-04-27
**Positions:** A — Bill 2-A as drafted (one new algorithm-calibration constant T_COLD_SHOULDER + structural infrastructure for proxy inversions and provisional 50/50 fusion) | B — none raised; Justice accepted directly without convening a hearing.
**Prevailing position:** A
**Justice's ruling:** Bill 2-A enacts as drafted. The drafter's three pre-flagged debate points are accepted as framed: (1) `RMS_HARMONIC_FACTOR = √(0.5·(1 + 1/9 + 1/36))` is not a new algorithm-calibration constant — it is an analytic consequence of Bill 1's enacted harmonic stack (1, 1/3, 1/6) and is computable to arbitrary precision from already-enacted parameters; (2) the provisional 0.5 fusion weight is the symmetric null hypothesis, introducing no information about relative proxy reliability, and is replaced by Bill 2-D's physics-derived W_VIB; (3) the cross-module import of `signals.py` constants into `algorithm.py` is a mathematical requirement of forward-model inversion — the inverse model must use the same physical relationships as the forward model. Implementation proceeds on branch `stage1/algorithm-regime-cold-shoulder`.
**Physical/empirical basis:** Bill 1 enacted forward model (Case 2, 2026-04-27) provides A_FUND_CLEAN, ALPHA, A_Z_DC, I0_HEATING, I0_COOLING, BETA — the inverse model in Bill 2-A is the mathematical inversion of the same physics. T_COLD_SHOULDER = 5.0 °C traces to ASHRAE 90.1 Canadian supplement balance-point evidence and lies within Signal Inventory normal range (−30 to +45 °C). Gate 0.2 stationary az = 0.975 g grounds the gravity-subtraction dependency; Gate 0.3 stationary rms_g ∈ [1.0014, 1.0056] vs vigorous-motion rms_g ∈ [1.0228, 2.0154] confirms the non-gravity-subtracted false-positive mode this Bill corrects.
**Device outcome protected:** A working `run()` produces a domain-primitive verdict (P1 = ΔP/ΔP₀, P2 = hvac_regime) for all eight Bill 1 profiles. Predicted alert behaviour: True at near_clog and past_clog profiles (dp_ratio ≥ 1.85), False at clean and mid_clog profiles. Unblocks `/regression` and the Stage 1 gate.
**Conditions:** None.
**Procedural note:** First no-hearing direct acceptance under the active constitutional record. The Bill's three debate points were drafter-flagged but uncontested by the Justice. Establishes that the Justice may rule directly when the drafter's pre-flagged tensions are not contested. Does not amend CONSTITUTION.md Judicial Process §1 — formal debate remains the default for any contested Bill or Bill where the Justice elects to convene attorneys.
**Enacted bill:** Bill 2-A — Regime Classifier Cold Shoulder + Proxy Inversion Infrastructure (`docs/governance/bills/stage1-algorithm-regime-cold-shoulder.md`).
**Implementation branch:** stage1/algorithm-regime-cold-shoulder

---

### Case 4: Bill 2-B — Regime Classifier Warm Shoulder (Three-Outcome Classifier)

**[FROZEN — Stage 1 closed 2026-05-19]**
**Compact card:** docs/governance/stage_1_closeout.md

**Date:** 2026-04-27
**Positions:** A — Bill 2-B as drafted (one new algorithm-calibration constant T_WARM_SHOULDER = 15.0 °C; three-outcome classifier replacing Bill 2-A's two-outcome classifier; ndarray-path "cooling" default preserved) | B — none raised; Justice accepted directly per Case 3 procedural precedent.
**Prevailing position:** A
**Justice's ruling:** Bill 2-B enacts as drafted. The drafter's two pre-flagged points are accepted as framed: (1) the ndarray-path default of "cooling" is preserved from Bill 2-A — the ndarray path carries no thermal information, and changing the default to "off" without an outside_temp signal or proxy signal would silently change behaviour for existing ndarray callers without physical justification; (2) T_WARM_SHOULDER = 15.0 °C (ASHRAE 90.1 Canadian supplement balance-point upper edge) is preferred over alternatives (HDD base 18 °C, ISO European 10 °C) because the Canadian rooftop application context (Amendment 1 / Device Purpose) grounds the standard, and the constant is explicitly falsifiable by Stage 2/3 DS18B20 field readings. Implementation proceeds on branch `stage1/algorithm-regime-warm-shoulder`.
**Physical/empirical basis:** ASHRAE 90.1 Canadian supplement balance-point upper edge (≈ 15 °C) for commercial rooftop heat-pump / gas-furnace systems. T_WARM_SHOULDER = 15.0 °C lies within Signal Inventory normal range (−30 to +45 °C) and is consistent with Bill 2-A's T_COLD_SHOULDER = 5.0 °C from the same standard's lower edge. Gate 0.3 stationary rms_g ∈ [1.0014, 1.0056] supports the physical premise that an "off" unit (blower stopped) produces a near-stationary signal that the prior two-outcome classifier misclassified as a clean "cooling" unit — the constitutional deficit this Bill closes.
**Device outcome protected:** The three-outcome regime classifier completes the Amendment 1 P2 primitive contract by making "off" reachable from `run()`. Zero regression on the eight enacted Bill 1 profiles (T_HEATING = −10 °C and T_COOLING = +25 °C both lie outside the new [5, 15) °C "off" band). Predicted output: `run({"outside_temp": np.array([10.0]), ...})` returns `hvac_regime = "off"`.
**Conditions:** None.
**Evidence gap acknowledged:** No Bill 1 simulation profile uses outside_temp in [5.0, 15.0) °C; the "off" classification branch is exercisable only by code inspection and manual unit test until a future Bill 1 amendment adds a shoulder-season profile (e.g., `clean_off` at outside_temp = 10 °C, blower off, ct_current ≈ 0 A, az ≈ A_Z_DC + noise). The gap is a follow-up obligation on a separate Bill, not a Bill 2-B blocker.
**Procedural note:** Second no-hearing direct acceptance under the active constitutional record (Case 3 precedent applied). Both pre-flagged debate points were drafter-assessed as not contestable on physical grounds; the Justice did not contest. Case 3's procedural precedent is now twice-applied — direct acceptance is established as the appropriate path when the drafter's pre-flagged tensions are uncontested. Formal Judicial debate remains the default for any Bill where the Justice elects to convene attorneys.
**Enacted bill:** Bill 2-B — Regime Classifier Warm Shoulder (`docs/governance/bills/stage1-algorithm-regime-warm-shoulder.md`).
**Implementation branch:** stage1/algorithm-regime-warm-shoulder

---

### Case 5: Bill 2-D — Physics-Derived Vibration Fusion Weight (W_VIB)

**[FROZEN — Stage 1 closed 2026-05-19]**
**Compact card:** docs/governance/stage_1_closeout.md

**Date:** 2026-04-27
**Positions:** A — Bill 2-D as drafted (W_VIB = 0.9999, the physics-derived inverse-variance weight; CT formally remains in ΔP fusion at 0.01 % contribution) | B — none raised; Justice accepted directly per Case 3 procedural precedent applied to the drafter's contested Point 1.
**Prevailing position:** A
**Justice's ruling:** Bill 2-D enacts as drafted. W_VIB = 0.9999 (dimensionless) is admitted into `src/algorithm.py` Step F, replacing the Bill 2-A 0.5/0.5 symmetric null-hypothesis fusion. The drafter flagged four points; three are uncontested on physical grounds (Case 3-eligible); the fourth — W_VIB = 0.9999 vs W_VIB = 1.000 — was contested, framed by the drafter as physics-derived value (0.9999) vs design simplification (1.000, formally retiring CT from ΔP fusion). The Justice rules for the physics-derived value: **0.9999 is the constitutionally correct adoption** because it is the direct output of the minimum-variance estimator from Bill 1 forward-model parameters and Signal Inventory noise specifications, with no rounding choice imposed beyond four-significant-figure precision. CT formally retains a presence in the ΔP fusion (at weight 1−W_VIB = 10⁻⁴) without making the architectural decision to retire it; that decision, if and when warranted, requires its own Bill (likely an Amendment 9 BOM Bill).
**Physical/empirical basis:** Inverse-variance fusion of two independent Gaussian proxy estimates: σ_vib ≈ 9.2 × 10⁻⁴ (from SIGMA_NOISE_G = 0.002 g averaged over N_imu = 1660 samples per 1-sec window) and σ_ct = 0.05 / (I0 × BETA), giving 0.1042 in heating and 0.04630 in cooling. Inverse-variance weight W_VIB = σ_ct² / (σ_vib² + σ_ct²) yields 0.99992 (heating) and 0.99961 (cooling); the regime difference (3.1 × 10⁻⁴) is sub-noise-floor relative to SIGMA_NOISE_G's one-significant-figure precision, so W_VIB is adopted as a regime-independent scalar. Means of dp_ratio_vib and dp_ratio_ct are both unbiased estimators of true ΔP/ΔP₀ → any convex combination preserves the mean, guaranteeing zero regression on the eight Bill 1 profile means by construction.
**Device outcome protected:** filter_dp_ratio detection-margin fully restored. The recorded near_clog_heating grazing condition (min 1.783 < 1.8 alert edge under 1-sec windows, recorded 2026-04-27 at commit 89694ab) resolves: with W_VIB ≈ 1, CT-driven spread is suppressed by 10⁴, and all chunks land at the vibration-only mean (≈ 1.859 for near_clog_heating, well above the 1.8 alert edge). Heating-vs-cooling spread asymmetry (1.7×, recorded same date) is similarly suppressed.
**Conditions:** None.
**Procedural note:** Third no-hearing direct acceptance under the active constitutional record (Cases 3 and 4 also applied the Case 3 precedent). This is the **first instance where the Justice ruled directly on a drafter-flagged contested point** rather than on uncontested points only — Cases 3 and 4 were fully uncontested. Case 5 establishes that Case 3 procedural precedent extends to Justice direct rulings on contested points: the Justice may resolve a contested point by stated position without convening attorneys, provided the position is grounded in a constitutional principle (here: physical derivation over architectural simplification, per Article I + Amendment 7).
**Architectural finding (informational, for future Bills):** With a 1-second decision window and the current σ_ct_current = 0.05 A specification, the CT proxy contributes < 0.01 % to the fused ΔP estimate. CT remains necessary for I0-based regime conditioning in Step E (and would be needed regardless of W_VIB). Two future Bills are foreseeable: (i) a *decision-window-length Bill* — at 60 sec, N_ct = 60, σ_ct drops by √60, and W_VIB shifts toward a more balanced value, restoring CT's ΔP-fusion contribution; (ii) an *Amendment 9 BOM Bill* — if 1-sec stays the field operating window and σ_ct_current stays ≈ 0.05 A, CT may be downgraded or eliminated as a ΔP proxy. Neither is in scope for Bill 2-D. The Bill 2-A 50/50 fusion is replaced by an effectively vibration-only fusion at the current window length; this is a finding the field validation must confirm.
**Bill 2 roadmap completion:** Bill 2-D is the fourth and final Bill in the Suggestion 2-A implementation sequence (Bill 2-A T_COLD_SHOULDER → Bill 2-B T_WARM_SHOULDER → Bill 2-C microphone proxy [contingent on Bill 1-Mic, deferred] → Bill 2-D W_VIB). With 2-A, 2-B, 2-D enacted, the Suggestion 2-A active architectural baseline (Direct ΔP Rejection SOR, 2026-04-27) is implemented for the IMU + CT signal subset. The microphone proxy (2-C) remains contingent on Bill 1-Mic and may be enacted in any order relative to subsequent Bills.
**Enacted bill:** Bill 2-D — Physics-Derived Vibration Fusion Weight (`docs/governance/bills/stage1-algorithm-fusion-weight.md`).
**Implementation branch:** stage1/algorithm-fusion-weight

---

### Case 7: Bill 4 — Stage 1 Algorithm Firmware + ALERT UART Event

**[FROZEN — Stage 1 closed 2026-05-19]**
**Compact card:** docs/governance/stage_1_closeout.md

**Date:** 2026-04-29
**Positions:** A — Bill 4 as drafted (ALERT event, AlertEvent, Stage 1 firmware with real + Renode paths) | B — none raised; Justice direct acceptance per Cases 3–6 procedural precedent.
**Prevailing position:** A
**Justice's ruling:** Bill 4 enacts as drafted. All four pre-flagged debate points accepted: (1) Serial1 → UARTE0 mapping is a Stage 1 falsifiable finding — if wrong, one-line fix; (2) CT absent from Renode path is a structural constraint of RenoneBridge (N×6 IMU only), not an algorithm deficit — CT fusion validated by Path A; (3) ALPHA=1 identity substitution is analytic, not a new constant; (4) events.py and analysis.py modification before Stage 1 gate close is authorized by this Bill per Amendment 11's "before gate close" window.
**Physical/empirical basis:** Firmware constants trace identically to algorithm.py constants (Bill 1–3). The C inversion (rms_ac / denominator) is the ALPHA=1 case of the Python `run()` Step D. Zero regression on UART event parsing (AlertEvent is additive to PARSER). Stage 1 Path B gate criterion satisfied when Renode run produces matching dp_ratio.
**Conditions:** None.
**Procedural note:** Fifth no-hearing direct acceptance. Cases 3–6 precedent applied.
**Enacted bill:** Bill 4 — Stage 1 Algorithm Firmware + ALERT UART Event (`docs/governance/bills/stage1-firmware.md`).
**Implementation branch:** stage1/firmware

---

### Case 6: Bill 3 — CT Sampling Rate Upgrade to 600 Hz and Regime-Split Fusion Weights

**[FROZEN — Stage 1 closed 2026-05-19]**
**Compact card:** docs/governance/stage_1_closeout.md

**Date:** 2026-04-29
**Positions:** A — Bill 3 as drafted (FS_CT_HZ 1 → 600; W_VIB scalar replaced by W_VIB_HEATING = 0.9144 and W_VIB_COOLING = 0.6785) | B — none raised; Justice direct acceptance per Case 3/4/5 procedural precedent.
**Prevailing position:** A
**Justice's ruling:** Bill 3 enacts as drafted. All four pre-flagged debate points accepted as framed: (1) σ_raw = 0.05 A per raw sample is consistent with the original 1 Hz spec and with typical 12-bit ADC noise on a ±25 A CT shunt; (2) the regime split is warranted — W_VIB_HEATING (0.9144) and W_VIB_COOLING (0.6785) differ by 0.236, which is well above the noise floor and invalidates the Bill 2-D single-scalar assumption; (3) both constants are outputs of the same minimum-variance formula applied to the same σ_raw, making atomic admission necessary for self-consistency; (4) "off"-regime CT bypass is a mathematical requirement (blower stopped → ct ≈ 0 → inversion undefined). Implementation proceeds on branch `stage1/ct-600hz-fusion`.
**Physical/empirical basis:** Same minimum-variance (inverse-variance) framework as Case 5. σ_ct_eff = 0.05 / √(2 × 600) = 0.001443 A. Propagated: σ_ct_H = 0.003007 (heating, I0 = 4.0, BETA = 0.12), σ_ct_C = 0.001336 (cooling, I0 = 9.0). W_VIB_H = σ_ct_H² / (σ_vib² + σ_ct_H²) = 0.9144; W_VIB_C = σ_ct_C² / (σ_vib² + σ_ct_C²) = 0.6785. CT contribution: 8.6 % heating, 32.2 % cooling. Cooling benefit larger because I0_COOLING (9 A) vs I0_HEATING (4 A) — higher baseline current makes CT inversion more sensitive per unit noise.
**Device outcome protected:** W_VIB_HEATING and W_VIB_COOLING are both convex combination weights. All eight Bill 1 profiles use T_HEATING (−10 °C) or T_COOLING (+25 °C), outside the shoulder band. Mean dp_ratio_vib and dp_ratio_ct are unbiased → zero regression on profile means. The CT signal model change (raw AC waveform vs pre-computed RMS) does not affect the mean value returned by the inversion — only the per-sample noise distribution, which the inverse-variance weights account for by construction.
**Conditions:** None.
**Procedural note:** Fourth no-hearing direct acceptance. Case 5 precedent applied (Justice may rule directly on contested points grounded in a constitutional principle). The architectural finding in Case 5 explicitly foreshadowed this Bill: "a *decision-window-length Bill* — at 60 sec, N_ct = 60, σ_ct drops by √60, and W_VIB shifts toward a more balanced value, restoring CT's ΔP-fusion contribution." Bill 3 achieves the same effect via sampling-rate increase rather than window-length extension — the physics is identical.
**Supersedes:** W_VIB = 0.9999 scalar from Bill 2-D (Case 5). That constant is removed from algorithm.py and replaced by W_VIB_HEATING and W_VIB_COOLING.
**Enacted bill:** Bill 3 — CT Sampling Rate Upgrade (`docs/governance/bills/stage1-ct-600hz.md`).
**Implementation branch:** stage1/ct-600hz-fusion

---

### Case 8: Bill 5 — Retroactive Authorization: Stage 2 KiCad Schematic, PCB Layout, and Signal Traceability Module

**Date:** 2026-05-19
**Positions:** A — Bill 5 as drafted, Option A (NTC thermistor accepted) | B — Bill 5 as drafted, Option B (DS18B20 reinstated); Justice direct acceptance per Cases 3–7 procedural precedent.
**Prevailing position:** B (Option B — DS18B20 OneWire reinstated)
**Justice's ruling:** Bill 5 enacts as drafted with Option B on Debate Point 3. Debate Points 1, 2, and 4 accepted as uncontested. Debate Point 3 resolved: DS18B20 OneWire is the authorized outside_temp sensing architecture. NTC sub-circuit (TH1 + R2 + J_TEMP) in schematic rev 0.1 is not authorized. Schematic rev 0.2 required before Stage 2 gate, replacing the NTC sub-circuit with a DS18B20 connector and 4.7 kΩ pull-up to 3V3. The human engineer stated the schematic was exploratory Stage 2 smoke-test preparation — consistent with Option B; rev 0.1 establishes the non-temperature signal paths, rev 0.2 completes the design.
**Physical/empirical basis:** DS18B20 factory calibration (±0.5°C) is required for the P2 regime classifier thresholds T_COLD_SHOULDER = 5°C and T_WARM_SHOULDER = 15°C (Bills 2-A / 2-B). NTC B-value tolerance (±1–2°C without per-unit calibration) is insufficient to reliably resolve the 10°C shoulder window in a self-installing, no-calibration-step rooftop device. DS18B20 OneWire was the planned architecture in toolchain_config.md; no change to that record is required.
**Conditions:**
1. `src/kicad_integration.py` SIGNAL_TO_NET corrected: IMU signals → `SDA`; ct_current_rms → `ADC_CT`; outside_temp → `OUTSIDE_TEMP` (correctly MISSING until rev 0.2); microphone → `PDM_DATA` (correctly MISSING, on-board routing). DONE.
2. `docs/device_context.md` BOM section must be populated with the 10-component table from Bill 5 Part A before Stage 2 gate opens. PENDING — human action.
3. Schematic rev 0.2 must replace TH1 + R2 + J_TEMP with DS18B20 connector + 4.7 kΩ pull-up before Stage 2 gate opens. PENDING — new schematic revision Bill required.
**Procedural note:** Sixth no-hearing direct acceptance. Cases 3–7 precedent applied. First contested Debate Point resolved under Option B (Justice stated preference for DS18B20 on calibration accuracy grounds at the device's self-install constraint).
**Police violations resolved:** ARTICLE-II-VIOLATION (commit acddbff — schematic files), ARTICLE-II-VIOLATION (commit acddbff — src/kicad_integration.py), AMENDMENT-2-VIOLATION (toolchain_config.md Stage 1 status — fixed 2026-05-19 concurrently).
**Enacted bill:** Bill 5 — Retroactive Authorization Stage 2 KiCad Schematic + Signal Traceability Module (`docs/governance/bills/stage2-schematic.md`).
**Implementation branch:** schematics (already committed)

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

---

### Standing Order Record — Stage 1 Path B (Renode) Waiver

**[FROZEN — Stage 1 closed 2026-05-19]**
**Compact card:** docs/governance/stage_1_closeout.md

**Date:** 2026-05-19
**Relates to:** Case 7 (Bill 4) — Stage 1 Path B gate criterion

**Finding:** Renode binary is present (`/usr/local/bin/renode`) but the RenoneBridge infrastructure required by `run_renode_sim.py` was never built: no `.resc` script, no `sim_usbd_stub.py`, no `sim_uart_stub.py`. Path B cannot execute in the current toolchain state.

**Justice's ruling:** Path B waived for Stage 1 gate. Stage 1 gate criterion is satisfied by Path A alone — all 8 registered profiles pass (2026-05-19 regression run: 8 PASS, 0 FAIL, 0 ERROR). The Bill 4 Path B mandate is superseded by this waiver. RenoneBridge infrastructure build is deferred to a future Bill before Stage 2 gate if firmware-in-emulator validation is required at that stage.

**Effect:** Stage 1 gate is MET. stage-compactor may proceed.
