### BILL: Implement Additive Harmonic Vibration Signal Model in src/signals.py
Proposed by: bill-drafter agent (sw-advisor + hw-advisor evidence)
Date drafted: 2026-04-27
Change type: simulation
Branch: stage1/signals-harmonic-vibration-model

---

**Problem statement:**

`src/signals.py::generate()` is a `NotImplementedError` stub that raises on every
call. This blocks Stage 1 (Simulation) from opening: the signal-only simulation
path calls `generate()` directly, and the Renode path derives synthetic samples
from the same function. Without a physically grounded implementation, no
simulation profiles can run, no regression pass/fail results can be produced,
and the Stage 1 Justice gate cannot be reached.

The stub's return contract (`np.ndarray` of shape `(n_steps, 6)`, columns
ax_g/ay_g/az_g/gx_dps/gy_dps/gz_dps, 100 Hz ODR) is IMU-only and must be
superseded: the Signal Inventory (`docs/device_context.md`) names nine signals
across four physical transducers (IMU 6-axis, ct_current_rms, outside_temp,
microphone). A signal model that generates only 6 IMU columns cannot support the
multi-signal inference required by the filter ΔP algorithm.

The stub recognises only three profiles ("normal", "worst_case_high_wind",
"worst_case_rapid_dust_load") that are not labelled by filter loading level. The
pass/fail criterion — alert must fire at ΔP ∈ [1.8 × ΔP₀, 1.9 × ΔP₀] — requires
profiles that span the ΔP/ΔP₀ axis explicitly, separated by regime
(heating / cooling), to allow a regime-conditioned algorithm to be validated.

References:
- `src/signals.py` lines 60–75 (NotImplementedError on all three profiles)
- `docs/device_context.md` Signal Inventory (9 signals, 4 transducers)
- `docs/device_context.md` Device Purpose: alert at ΔP ∈ [1.8, 1.9] × ΔP₀
- `docs/device_context.md` Test Results, Gate 0.2 (2026-04-20): stationary
  accel magnitude √(0.075² + 0.311² + 0.975²) = 1.03 g ≈ gravity, gyro bias
  ≈ 2 dps — establishes real-hardware noise floor for model grounding.

---

**Proposed change:**

Replace `src/signals.py` with a new implementation of `generate()` that:

1. Changes the function signature from
   `generate(profile: str, n_steps: int) -> np.ndarray`
   to
   `generate(profile: str, n_steps: int) -> dict[str, np.ndarray]`
   returning a dict keyed by signal name matching the Signal Inventory:
   `imu_accel_x`, `imu_accel_y`, `imu_accel_z`, `imu_gyro_x`, `imu_gyro_y`,
   `imu_gyro_z`, `ct_current_rms`, `outside_temp`, `microphone`.
   Each value is a 1-D `np.ndarray` of length `n_steps` (where `n_steps` is
   per-signal — interpreted at the signal's native sample rate from Signal Inventory).

2. Recognises exactly **eight profiles** (new profile registry replacing the
   three-profile stub):

   | Profile name          | ΔP / ΔP₀ | Regime  | Purpose                 |
   |-----------------------|----------|---------|-------------------------|
   | `clean_heating`       | 1.0      | heating | installed-new baseline  |
   | `clean_cooling`       | 1.0      | cooling | installed-new baseline  |
   | `mid_clog_heating`    | 1.5      | heating | mid-life, no alert      |
   | `mid_clog_cooling`    | 1.5      | cooling | mid-life, no alert      |
   | `near_clog_heating`   | 1.85     | heating | **alert region**        |
   | `near_clog_cooling`   | 1.85     | cooling | **alert region**        |
   | `past_clog_heating`   | 2.0      | heating | full clog point         |
   | `past_clog_cooling`   | 2.0      | cooling | full clog point         |

3. Implements the physics model as follows for each profile (all constants
   require the Amendment 7 four-line derivation block — see Derivation Blocks
   section below):

   **IMU SIGNALS (sample rate: 1660 Hz; time axis dt = 1/1660 s):**

   ```
   t = np.arange(n_steps) / 1660.0

   f_fund = F_FUND_HEATING (20 Hz) if regime == "heating"
            else F_FUND_COOLING (32 Hz)

   A_fund = A_FUND_CLEAN * (dp_ratio ** ALPHA)
     where dp_ratio = ΔP/ΔP₀ for the profile,
     A_FUND_CLEAN = 0.05 g, ALPHA = 1.

   For imu_accel_z:
     a_z(t) = A_Z_DC
              + A_fund * sin(2π f_fund t + φ_z)
              + (A_fund/3) * sin(2π 2f_fund t + φ_z2)
              + (A_fund/6) * sin(2π 3f_fund t + φ_z3)
              + N(0, SIGMA_NOISE_G)
     where A_Z_DC = 1.0 g (gravity on vertical housing side),
     φ_z, φ_z2, φ_z3 fixed phases (0, 0, 0 reference).
     Clip to ±2 g (hard limit, Signal Inventory).

   For imu_accel_x and imu_accel_y:
     Same harmonic structure as a_z minus DC gravity offset, with
     independent random phases per axis from
     np.random.default_rng() seeded by hash(profile).
     Clip to ±2 g.

   For imu_gyro_{x,y,z}:
     Zero array + N(0, SIGMA_NOISE_G * 10) in dps. Gyro contributes to
     angular-vibration characterisation at Stage 2, not the scalar RMS
     metric at Stage 1. A future Bill may introduce a gyro signal model.
   ```

   **CT_CURRENT_RMS (sample rate: 1 Hz):**

   ```
   I0 = I0_HEATING (4.0 A) if regime == "heating"
        else I0_COOLING (9.0 A)

   ct_current_rms(t) = I0 * (1 + BETA * (dp_ratio - 1))
                       + N(0, 0.05)   [small Gaussian noise, A]
   Steady-state at Stage 1 (temporal variation deferred to Stage 2).
   Clip to [0.3, 25.0] A (Signal Inventory hard limits).
   ```

   **OUTSIDE_TEMP (sample rate: 1/60 Hz):**

   ```
   T = T_HEATING (-10 °C) if regime == "heating"
       else T_COOLING (25 °C)
   outside_temp[:] = T   [step function; no temporal variation at Stage 1]
   Signal Inventory hard limits: fault < -40 °C or > +60 °C.
   ```

   **MICROPHONE (sample rate: 16 000 Hz):**

   PLACEHOLDER — returns a zero array of length `n_steps` for this Bill.

   Physical reasoning: SPL_dBSPL(ΔP) = SPL0 + 10·log10(ΔP/ΔP₀) where
   SPL0 = 55 dBSPL (clean-filter blower acoustic baseline) is included as a
   constant definition but the waveform generator is deferred to Bill 1-Mic
   (a subsequent Bill). Microphone is secondary at Stage 1 per sw-advisor
   recommendation (IMU + CT suffice for the regime-conditioned threshold);
   introducing a 16 kHz pink-noise generator in this Bill would expand scope
   without Stage 1 algorithmic benefit. The placeholder ensures the signal
   key is present in the returned dict so downstream code does not raise
   `KeyError`. Bill 1-Mic must be enacted before microphone is used in any
   algorithm evaluation.

4. Adds a module-level `PROFILE_TABLE` dict mapping profile name →
   `(dp_ratio: float, regime: str)` for use by `algorithm.py` and
   `regression-runner` without re-parsing profile name strings.

5. Removes the three old stub profiles (`normal`, `worst_case_high_wind`,
   `worst_case_rapid_dust_load`). The worst-case profiles (wind, rapid dust
   load) are deferred to a future Bill grounded in Stage 2 field measurements;
   they cannot be physically grounded without hardware data.

**Note on return-type change:** The signature change from `np.ndarray` to `dict`
is a breaking change relative to the scaffold stub's documented return contract.
This is permitted under Amendment 11 because `signals.py` is explicitly NOT part
of the frozen scaffold trio (case_law.md, First Scaffold Authorization SOR,
2026-04-27). Any downstream caller of `generate()` (currently: none in
production — no Stage 1 algorithm exists yet) must be updated when Bill 2
(algorithm architecture) is enacted.

**File modified:** `/Users/roxanneturcotte/CrucibleStudio/crucible-comfort/src/signals.py`
**No other files modified.**

---

**Article / Amendment grounding:**

**Primary:**

- **Article I — Signal First:** every constant introduced traces to P1 (Filter ΔP)
  or P2 (HVAC operating regime) as defined in Amendment 1. The physics model is
  the formal realisation of the Amendment 1 mapping from domain primitives to
  observable signals.
- **Amendment 1 — Domain Primitives (ComfortSense):** the profile table is
  structured around P1 (dp_ratio axis) and conditioned on P2 (regime axis),
  implementing the two-primitive signal space Amendment 1 defines. Every signal
  array produced traces back to one of the two primitives via the derivation
  blocks below.
- **Amendment 5 — Simulation is the Hardware Proxy:** this Bill is the Stage 1
  binding simulation prediction set. The `generate()` implementation defines what
  the hardware is predicted to produce at each (ΔP/ΔP₀, regime) point. Deviations
  measured in Stage 2 are evidence of a hardware or mounting problem — not a
  firmware problem — unless the simulation test was never written.
- **Amendment 7 — Calibration Discipline:** eleven constants are introduced. The
  count-per-Bill tension is explicitly surfaced for Justice ruling (see
  Constitutional Tension section below). Each constant carries the mandatory
  four-line derivation block.
- **Amendment 9 — Hardware Optimization Transparency:** see Hardware
  Optimization Opportunity section.
- **Amendment 11 — Scaffold Immutability:** `signals.py` is authorised for
  implementation by Bill (case_law.md First Scaffold Authorization SOR,
  2026-04-27 — explicitly excluded from the freeze). The frozen trio
  (events.py, analysis.py, plot.py) is not modified.

**Secondary:**

- **Amendment 6 — Signal Plot Mandate:** this Bill changes the signal model.
  Upon enactment, `/plot profile` must be run for all eight profiles and
  human visual confirmation obtained before Bill 2 is heard. Post-enactment
  obligation, not a gate on this Bill's debate.

---

**Physical evidence:**

- **E1** — Gate 0.2 accel magnitude (2026-04-20): stationary accel magnitude
  √(0.075² + 0.311² + 0.975²) = 1.03 g ≈ 1 g gravity. Grounds A_Z_DC = 1.0 g
  and IMU noise floor magnitude. *Source: docs/device_context.md, Gate 0.2.*
- **E2** — Gate 0.2 gyro bias (2026-04-20): stationary gyro bias ≈ 2 dps.
  Grounds the gyro noise placeholder (10 × SIGMA_NOISE_G ≈ 0.02 dps,
  conservatively below 2 dps observed). *Source: docs/device_context.md,
  Gate 0.2.*
- **E3** — Gate 0.3 stationary RMS floor (2026-04-20): 31 METRIC lines over
  15 s, rms_g ∈ [1.0014, 1.0056]. Width 0.004 g peak-to-peak ≈ 2σ at
  σ = 0.002 g over 50-sample windows. *Source: docs/device_context.md,
  Gate 0.3.*
- **E4** — Signal Inventory hard limits: ±2 g, ±250 dps, 0.3–25 A,
  −40 to +60 °C, 40–70 dBSPL. All model outputs clipped to these limits.
  *Source: docs/device_context.md.*
- **E5** — Case law SOR: Direct ΔP rejected; indirect mandatory (2026-04-27).
  Confirms the indirect-sensing architecture this signal model implements.
  *Source: docs/governance/case_law.md Active Precedents.*
- **E6** — First Scaffold Authorization SOR (2026-04-27): confirms `signals.py`
  is not part of the frozen scaffold trio. *Source: docs/governance/case_law.md
  Active Precedents.*

---

**Expected outcome:**

| Primitive | Quantity | Before | After |
|---|---|---|---|
| P1 | profiles implemented | 0 / 8 | **8 / 8** |
| P1 | peak(a_z_vibration) at clean_heating, 20 Hz | not computable | **0.05 g** |
| P1 | peak(a_z_vibration) at near_clog_heating, 20 Hz | not computable | **0.0925 g** (85 % above clean — measurable by gravity-subtracted RMS) |
| P1 | ct_current_rms at near_clog_cooling | not computable | **9.918 A RMS** (10.2 % above I0_COOLING) |
| P2 | regime separation via outside_temp | not computable | **35 °C** (heating −10, cooling +25; clear of 5–15 °C shoulder) |

Amendment 6 obligation: `/plot profile` run on all 8 profiles; plots saved to
`docs/plots/`; human visual confirmation required before Bill 2 is heard.

---

**Constitutional tension — Amendment 7 one-constant-per-Bill rule:**

Amendment 7 states: *"One new calibration constant may be introduced per
algorithmic iteration."*

This Bill introduces **eleven** constants:
A_FUND_CLEAN, ALPHA, SIGMA_NOISE_G, F_FUND_HEATING, F_FUND_COOLING,
I0_HEATING, I0_COOLING, BETA, T_HEATING, T_COOLING, SPL0.

**Drafter's position (for debate, not advocacy):**
These eleven constants are **physical model parameters** of a synthetic signal
generator — they describe what the physical world is predicted to produce, not
what the algorithm decides. Amendment 7 was written to discipline algorithmic
tuning: a tuned constant (fitted without derivation) requires re-tuning at every
hardware change. Signal model parameters are falsifiable predictions of hardware
behaviour, not tuning choices. When Stage 2 hardware data arrives, the model
parameters will either be confirmed or corrected by measurement — they are
hypotheses, not knobs. The A7 derivation-block requirement applies to each
(documented below). The one-constant-per-Bill count constraint was written to
govern algorithm Bills, not signal model Bills.

**Counter-position (for attorney-B):**
The A7 text makes no distinction between "signal model parameter" and "algorithm
calibration constant" — both are numbers embedded in source that affect detection
behaviour. Permitting eleven constants in one Bill creates precedent for
bypassing A7 in algorithm Bills by calling constants "model parameters." The
Justice should rule on whether the signal-model / algorithm-constant distinction
is constitutionally valid; if so, codify as an Amendment, not a Bill-level
ruling.

**The Justice's ruling on this tension at hearing will determine whether a
clarifying Amendment to A7 is required before Bill 2 proceeds.**

---

**Hardware optimization opportunity (Amendment 9):**

**None identified by this Bill.** The signal model produces outputs for all four
transducers (IMU, CT, outside_temp, microphone placeholder). The signal model
and the BOM are independent: the model describes what hardware is predicted to
produce; it does not alter what hardware is specified. BOM gaps recorded in
`docs/toolchain_config.md` (CT clamp TBD, thermometer TBD) are downstream of
this Bill and governed by separate BOM Bills (case_law.md SOR 2026-04-27). No
sensor can be eliminated from the model at Stage 1 — the algorithm requires all
four modalities to cover the heating/cooling regime split and the ΔP/ΔP₀
detection axis. Hardware optimisation can only be evaluated after Stage 2 data
shows which signals carry the most discriminative information.

---

**Re-scaffold flag (Amendment 11):**

**NOT REQUIRED.** `signals.py` is not a scaffolded module (case_law.md First
Scaffold Authorization SOR 2026-04-27). The return-type change (ndarray → dict)
does not affect the frozen trio (events.py, analysis.py, plot.py); those modules
parse UART output from firmware, not the output of `generate()`.
**`/toolchain scaffold` must NOT be re-run as a result of this Bill.**

---

**Derivation blocks for all introduced constants (Amendment 7 four-line format):**

```
A_FUND_CLEAN — derived from P1 (Filter ΔP).
  Physical derivation: Representative peak accel amplitude at blower fundamental
  frequency on a commercial packaged HVAC housing side-wall, clean filter.
  Stage 2 prior; literature value for light sheet-metal panel with blower at
  nominal speed. Falsifiable Stage 2 prediction.
  Value: 0.05 g.
  Traces to: Amendment 1 primitive P1 (Filter ΔP — vibration is the primary P1 proxy).

ALPHA — derived from P1 (Filter ΔP).
  Physical derivation: First-order linear coupling assumption — A_fund(ΔP) = A0
  × (ΔP/ΔP₀)^1. Blower backpressure increases linearly with restriction in the
  laminar-dominated regime; housing vibration tracks blower torque variation
  linearly at first order. Stage 2 (ΔP, accel) pairs will fit the true exponent.
  Value: 1 (dimensionless).
  Traces to: Amendment 1 primitive P1 (exponent governs P1 → vibration mapping).

SIGMA_NOISE_G — derived from P1 (Filter ΔP).
  Physical derivation: Gate 0.2 stationary accel band 0.004 g peak-to-peak ≈ 2σ
  at σ = 0.002 g. Consistent with LSM6DS3TR-C noise density 90 µg/√Hz × √(1660)
  ≈ 3.7 mg RMS (model is conservative below spec floor). Evidence: E1, E3.
  Value: 0.002 g.
  Traces to: Amendment 1 primitive P1 (noise floor limits Filter ΔP detection).

F_FUND_HEATING — derived from P2 (HVAC operating regime).
  Physical derivation: Heating mode lower blower speed (smaller heating load
  on Canadian rooftop units). Midpoint of literature 15–25 Hz heating range
  (900–1500 RPM 2-pole induction motor). Stage 2 tach/FFT will replace prior.
  Value: 20 Hz.
  Traces to: Amendment 1 primitive P2 (heating regime determines blower speed).

F_FUND_COOLING — derived from P2 (HVAC operating regime).
  Physical derivation: Cooling mode higher blower speed (refrigerant condenser
  air volume demand). Midpoint of 25–40 Hz cooling range (1500–2400 RPM).
  Stage 2 tach/FFT will replace prior.
  Value: 32 Hz.
  Traces to: Amendment 1 primitive P2 (cooling regime determines blower speed).

I0_HEATING — derived from P2 (HVAC operating regime) and P1 (clean baseline).
  Physical derivation: Lower-half of Signal Inventory normal range [2, 8] A,
  adjusted to 4.0 A for heating-only blower stage (2-speed or VFD low-speed).
  Stage 2 CT measurements with clean filter will calibrate.
  Value: 4.0 A RMS.
  Traces to: Amendment 1 primitives P2 (regime) and P1 (ΔP/ΔP₀ = 1 anchor).

I0_COOLING — derived from P2 (HVAC operating regime) and P1 (clean baseline).
  Physical derivation: Upper-half of normal range [8, 15] A, adjusted to 9.0 A
  conservative estimate for 3-ton packaged unit (1/3–1/2 hp blower at 120 V).
  Stage 2 CT measurements with clean filter will calibrate.
  Value: 9.0 A RMS.
  Traces to: Amendment 1 primitives P2 (regime) and P1 (ΔP/ΔP₀ = 1 anchor).

BETA — derived from P1 (Filter ΔP).
  Physical derivation: Induction-motor slip increase per ΔP/ΔP₀ unit above
  baseline. β = 0.12 → 12 % current rise at full clog (ΔP/ΔP₀ = 2). Derived
  from typical 1/3 hp TEFC efficiency curve (10–15 % loss over slip range).
  Stage 2 CT measurements will fit per-unit β.
  Value: 0.12 (dimensionless, A/A per ΔP/ΔP₀ unit).
  Traces to: Amendment 1 primitive P1 (β governs P1 → current mapping).

T_HEATING — derived from P2 (HVAC operating regime).
  Physical derivation: Canadian winter day temperature well below 5 °C lower
  shoulder. Clear regime separation. Stage 2/3 use actual DS18B20 readings.
  Value: −10 °C.
  Traces to: Amendment 1 primitive P2 (outside_temp is the regime proxy).

T_COOLING — derived from P2 (HVAC operating regime).
  Physical derivation: Mild Canadian summer day, well above 15 °C upper
  shoulder. Clear regime separation. Stage 2/3 use actual DS18B20 readings.
  Value: 25 °C.
  Traces to: Amendment 1 primitive P2 (outside_temp is the regime proxy).

SPL0 — derived from P1 (Filter ΔP) — PLACEHOLDER ONLY.
  Physical derivation: ASHRAE applications handbook fan sound-power tables for
  packaged rooftop equipment, conservative lower end at side-wall mounting.
  Stage 2 mic measurements will calibrate. Waveform generator deferred to
  Bill 1-Mic.
  Value: 55 dBSPL.
  Traces to: Amendment 1 primitive P1 (acoustic pressure is a P1 proxy).

A_Z_DC (NOT a calibration constant — physical constant):
  A_Z_DC = 1.0 g is the gravitational acceleration projected on the z-axis when
  the device is mounted on a vertical housing side-wall. Not a model parameter
  — gravity is fixed by mounting geometry. Included for traceability only; does
  NOT count under the A7 constant-per-Bill rule. Evidence: E1 (Gate 0.2,
  az = 0.975 g ≈ 1 g on stationary hardware).
```

---

**Status:** ENACTED — Case 2 ruling 2026-04-27

Ready for Judicial debate. Invoke
`/judicial hear "Bill 1 — Additive Harmonic Vibration Signal Model" A vs B`
to assign attorneys and receive a ruling.

**Sharpest debate points the hearing must resolve:**

1. **A7 one-constant-per-Bill tension.** If upheld, this Bill must split into
   eleven sequential Bills, serialising Stage 1 startup. Attorney-A: defend the
   signal-model / algorithm-constant distinction on physical grounds. Attorney-B:
   argue the A7 text contains no such distinction, and that codifying one needs
   an Amendment, not a Bill-level ruling.

2. **Return-type interface change.** ndarray → dict is breaking. Bind Bill 2's
   algorithm interface to this dict shape now, or leave it open for Bill 2 to
   specify? Drafter recommends binding here to prevent drift.

3. **Microphone placeholder (zero array).** Attorney-B may argue this fails
   Amendment 6 plot mandate ("physically plausible signal"). Attorney-A: the
   placeholder is explicitly disclosed, the waveform generator is a named
   follow-on Bill (Bill 1-Mic), and a zero array satisfies the dict-key contract
   without making a false physical claim.
