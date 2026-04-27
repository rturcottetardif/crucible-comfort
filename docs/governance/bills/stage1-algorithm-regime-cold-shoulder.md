# BILL 2-A: Regime Classifier Cold Shoulder + Proxy Inversion Infrastructure in src/algorithm.py

```
Drafted by:    bill-drafter agent
Date drafted:  2026-04-27
Change type:   software (algorithm — Python model)
Branch:        stage1/algorithm-regime-cold-shoulder
Status:        ENACTED — Case 3 ruling 2026-04-27 (no hearing; direct Justice acceptance)
```

---

## Pre-draft A7 + Case 2 analysis

Case 2 (2026-04-27) established that the signal-model class in `src/signals.py` is exempt from Amendment 7's one-per-Bill ceiling because those constants are physically derived predictions, not algorithmic tuning knobs. Case 2 explicitly noted: *"Amendment 7's one-per-iteration ceiling does not apply to physically derived signal-model parameters of `src/signals.py`."* The ruling is class-specific — it names `src/signals.py` by file. It does not extend to `src/algorithm.py`.

Algorithm-calibration constants in `run()` are in the algorithm-calibration class. They govern what the algorithm decides, not what the signal model predicts. The one-per-Bill ceiling applies.

Suggestion 2-A requires three new algorithm-calibration constants: T_COLD_SHOULDER, T_WARM_SHOULDER (regime classifier), W_VIB (fusion weight). Three Bills required: 2-A, 2-B, 2-D. Bill 2-C (microphone proxy) introduces zero new constants and is contingent on Bill 1-Mic.

This Bill (2-A) introduces **one** new algorithm-calibration constant: T_COLD_SHOULDER.

---

## Problem statement

`src/algorithm.py::run()` raises `NotImplementedError` at line 57. This blocks the entire signal-only simulation path: `simulator-operator` cannot produce a pass/fail verdict for any of the eight profiles enacted by Bill 1 (Case 2, 2026-04-27); `/regression` cannot run; the Stage 1 gate cannot close. The path from `signals.py::generate()` output to a domain-primitive verdict (P1 = ΔP/ΔP₀, P2 = hvac_regime) is entirely open.

The architectural baseline for implementation is Suggestion 2-A (Gravity-Subtracted RMS + Regime-Conditioned Threshold), recorded as the active architecture in the Direct ΔP Rejection SOR (`docs/governance/case_law.md` Active Precedents, 2026-04-27). Suggestion 2-A's regime classification step requires two temperature shoulder constants (T_COLD_SHOULDER, T_WARM_SHOULDER). Its fusion step requires one blend weight (W_VIB). Under Amendment 7 as applied to the algorithm-calibration class by Case 2, each of these three constants requires a separate Bill. This is Bill 2-A: it introduces T_COLD_SHOULDER, the first and primary regime-classification boundary.

Without the regime classifier, the algorithm cannot select the correct regime-conditioned inversion path (heating vs cooling I0, heating vs cooling blower frequency), making the ΔP/ΔP₀ estimate regime-blind and physically invalid under Article I.

References:
- `src/algorithm.py` lines 57–61 (NotImplementedError stub)
- `docs/device_context.md` Test Results, Gate 0.3 (2026-04-20): stationary rms_g ∈ [1.0014, 1.0056]; vigorous-motion rms_g ∈ [1.0228, 2.0154] — confirms the non-gravity-subtracted metric suffers false positive on gentle tilt, exactly what gravity subtraction in this Bill corrects
- `docs/device_context.md` Test Results, Gate 0.2 (2026-04-20): az_dc = 0.975 g ≈ 1.03 g stationary magnitude — grounds A_Z_DC = 1.0 g used in the gravity subtraction
- `docs/device_context.md` Signal Inventory: outside_temp unit = °C, normal range −30 to +45 °C — constrains T_COLD_SHOULDER to fall within the operational envelope
- `docs/governance/case_law.md` Active Precedents, Direct ΔP Rejection SOR (2026-04-27): Suggestion 2-A named as active architectural baseline

---

## Proposed change

**File modified:** `/Users/roxanneturcotte/CrucibleStudio/crucible-comfort/src/algorithm.py`
**No other files modified.** `src/signals.py`, `src/events.py`, `src/analysis.py`, `src/plot.py` are untouched.

**Amendment 11 check:** `src/algorithm.py` is NOT part of the frozen scaffold trio (events.py / analysis.py / plot.py). Per the First Scaffold Authorization SOR (case_law.md, 2026-04-27), `algorithm.py` was excluded from the freeze and is explicitly "a stub to be implemented in Stage 1." Changes to `run()`'s return type or body are admissible without re-scaffold.

### 1. Add one new module-level algorithm-calibration constant above `run()`:

```python
# T_COLD_SHOULDER — derived from P2 (HVAC operating regime).
# Physical derivation: Canadian HVAC systems engage heating when outdoor
#   temperature falls below ~5 °C (the minimum balance-point temperature for
#   commercial rooftop heat-pump / gas-furnace units per ASHRAE 90.1 Canadian
#   supplement). T_COLD_SHOULDER = 5 °C is the upper edge of the "clearly
#   heating" zone. Anything below 5 °C is declared heating; anything at or
#   above 5 °C is treated as cooling (conservative bias) until Bill 2-B
#   introduces T_WARM_SHOULDER to carve out the "off" ambiguity band.
#   Stage 2/3 DS18B20 field readings will confirm or adjust this boundary.
# Value: 5.0 °C.
# Traces to: Amendment 1 primitive P2 (outside_temp is the regime proxy).
T_COLD_SHOULDER = 5.0  # °C — traces to A1 P2; conservative heating lower edge
```

### 2. Replace the `NotImplementedError` body of `run()` with the implementation below.

The function signature and docstring are unchanged. The implementation introduces these sub-steps in dependency order:

**Step A — Input validation and signal extraction.** Bill 1's `generate()` returns a `dict[str, np.ndarray]` keyed by signal name. The current `run()` signature accepts `np.ndarray` shape `(n_steps, C)`. Bill 2-A resolves the interface mismatch: `run()` accepts either form — a `dict[str, np.ndarray]` (signal-only simulation path) or an `np.ndarray` (Renode/UART path with column order matching `src.events.ReadingEvent`). Structural infrastructure, no new constant.

**Step B — Regime classification (T_COLD_SHOULDER only):**
```python
temp_c = float(np.mean(outside_temp_arr))
if temp_c < T_COLD_SHOULDER:
    hvac_regime = "heating"
else:
    hvac_regime = "cooling"  # conservative default until Bill 2-B
```
Two-outcome classifier: heating below T_COLD_SHOULDER, cooling at or above. The "off" regime (ambiguity band between cold and warm shoulder) requires T_WARM_SHOULDER (Bill 2-B) and is deferred. Defaulting to "cooling" above the cold shoulder is the conservative regime bias: cooling has higher current baselines (I0_COOLING = 9.0 A vs I0_HEATING = 4.0 A), so a false cooling classification on a heating-mode unit will underestimate dp_ratio (the current proxy sees observed current as "less elevated" relative to a higher baseline) — biasing toward under-alerting rather than false alarm, the less harmful error direction per Device Purpose ("if the device fires too early, filters are replaced prematurely").

**Step C — Gravity-subtracted vibration proxy (no new constant; uses A_Z_DC from signals.py):**
```python
from src.signals import A_Z_DC, A_FUND_CLEAN, ALPHA, I0_HEATING, I0_COOLING, BETA
az_ac = imu_accel_z_arr - A_Z_DC          # remove DC gravity — traces to A1 P1
rms_ac_g = float(np.sqrt(np.mean(az_ac**2)))  # AC RMS — gravity-subtracted P1 vibration proxy
```
A_Z_DC = 1.0 g is the physical constant established at Gate 0.2 (az = 0.975 g ≈ 1.03 g stationary, 2026-04-20). It is not a new algorithm-calibration constant — it was enacted in Bill 1 as a physical constant and is imported here as a read-only dependency.

**Step D — Vibration-to-ΔP/ΔP₀ inversion (no new constant; inverse of Bill 1 forward model):**

The Bill 1 forward model is `rms_ac ≈ A_FUND_CLEAN × dp_ratio^ALPHA × RMS_HARMONIC_FACTOR` where `RMS_HARMONIC_FACTOR = sqrt(0.5 × (1 + 1/9 + 1/36))` is an analytic consequence of the harmonic amplitude stack (1, 1/3, 1/6). It is not a tunable parameter — it is computable to arbitrary precision from the already-enacted Bill 1 model.

```python
RMS_HARMONIC_FACTOR = float(np.sqrt(0.5 * (1.0 + 1.0/9.0 + 1.0/36.0)))
# Analytically derived from Bill 1 harmonic stack — not a calibration constant
if rms_ac_g > 0:
    dp_ratio_vib = (rms_ac_g / (A_FUND_CLEAN * RMS_HARMONIC_FACTOR)) ** (1.0 / ALPHA)
else:
    dp_ratio_vib = 1.0  # noise floor — default to clean
```

**Step E — Current-to-ΔP/ΔP₀ inversion (no new constant; inverse of Bill 1 CT forward model):**
```python
ct_mean = float(np.mean(ct_current_rms_arr))
I0 = I0_HEATING if hvac_regime == "heating" else I0_COOLING
# Inverse of: ct_mean = I0 * (1 + BETA * (dp_ratio - 1))
dp_ratio_ct = 1.0 + (ct_mean / I0 - 1.0) / BETA
```

**Step F — Provisional fusion (no W_VIB yet; equal weight pending Bill 2-D):**
Without W_VIB, equal weighting is the symmetric null hypothesis — it introduces no information about relative proxy reliability. Bill 2-D will replace this with physics-grounded weighting.
```python
dp_ratio_combined = 0.5 * dp_ratio_vib + 0.5 * dp_ratio_ct  # equal weight placeholder
```

**Step G — Alert and output assembly:**
```python
alert = dp_ratio_combined >= 1.8  # Amendment 1 alert window low edge — not a new constant
return {
    "filter_dp_ratio": dp_ratio_combined,
    "filter_dp_pa": None,           # ΔP₀ Pa calibration unavailable until Stage 2
    "hvac_regime": hvac_regime,
    "alert": bool(alert),
    "diagnostics": {
        "rms_ac_g": rms_ac_g,
        "dp_ratio_vib": dp_ratio_vib,
        "dp_ratio_ct": dp_ratio_ct,
        "ct_mean_a": ct_mean,
        "outside_temp_c": temp_c,
    },
}
```

### What this Bill does NOT introduce

- T_WARM_SHOULDER — deferred to Bill 2-B (second regime boundary; one-per-Bill ceiling)
- W_VIB — deferred to Bill 2-D (fusion blend weight; one-per-Bill ceiling)
- Any change to `src/signals.py`, `src/events.py`, `src/analysis.py`, or `src/plot.py`

### Hardware optimization opportunity (Amendment 9)

**None identified by this Bill.** The regime classifier and proxy inversions use all available sensors (IMU, CT, outside_temp). No sensor is made redundant. Hardware optimization can only be evaluated after Stage 2 data reveals per-sensor information content.

---

## Article / Amendment grounding

**Primary:**

- **Article I — Signal First.** T_COLD_SHOULDER traces to P2 (HVAC operating regime; outside_temp proxy) per the four-line derivation block. The gravity-subtraction constant A_Z_DC traces to P1 (Gate 0.2, 2026-04-20). Proxy-inversion constants (A_FUND_CLEAN, ALPHA, I0_HEATING, I0_COOLING, BETA) trace to P1/P2 as established in Bill 1/Case 2. The alert threshold 1.8 is the Amendment 1 primitive boundary — not a new constant. All intermediate quantities carry primitive traces in inline comments.
- **Amendment 1 — Domain Primitives.** Both outputs — `filter_dp_ratio` (P1, dimensionless ratio) and `hvac_regime` (P2, categorical) — are direct realizations of the two primitives.
- **Amendment 7 — Calibration Discipline.** One new algorithm-calibration constant introduced (T_COLD_SHOULDER). A7 four-line derivation block provided. Ceiling not exceeded.
- **Case 2 (2026-04-27) — Algorithm-calibration class not exempt from A7.** The ruling exempted `src/signals.py` signal-model constants only. `src/algorithm.py` constants remain subject to the one-per-Bill ceiling. T_COLD_SHOULDER is the sole new constant in this Bill.

**Supporting:**

- **Amendment 5 — Simulation is the Hardware Proxy.** `run()` with this Bill produces a verdict for all eight Bill 1 profiles, making the simulation path operational for the first time.
- **Amendment 11 — Scaffold Immutability.** algorithm.py is not in the frozen scaffold trio. Change is admissible. No re-scaffold required.
- **Amendment 6 — Signal Plot Mandate.** Algorithm parameter change triggers the plot mandate at enactment. Post-enactment obligation: `/plot evidence` on a representative profile set with human visual confirmation.
- **Amendment 9 — Hardware Optimization Transparency.** No opportunity identified (stated above).

---

## Physical evidence

- **Gate 0.2 (2026-04-20):** stationary az = 0.975 g, magnitude 1.03 g — grounds A_Z_DC = 1.0 g used in gravity subtraction.
- **Gate 0.3 (2026-04-20):** stationary rms_g ∈ [1.0014, 1.0056]; vigorous-motion rms_g ∈ [1.0228, 2.0154] — confirms non-gravity-subtracted RMS suffers false positive on gentle tilt. Step C's gravity subtraction reduces stationary rms_ac_g to ≈ SIGMA_NOISE_G ≈ 0.002 g (noise floor only). Exact problem the Bill corrects.
- **Signal Inventory (`docs/device_context.md`):** outside_temp normal −30 to +45 °C — confirms T_COLD_SHOULDER = 5 °C lies within the operational envelope; hard limits (< −40 °C or > +60 °C) not approached.
- **Bill 1 enacted forward model (Case 2, 2026-04-27):** provides the constants imported in Steps C–F (A_FUND_CLEAN, ALPHA, A_Z_DC, I0_HEATING, I0_COOLING, BETA) and the harmonic structure whose analytic RMS factor is computed in Step D.
- **Direct ΔP Rejection SOR (2026-04-27):** Suggestion 2-A named as active architectural baseline.

---

## Expected outcome

| Primitive | Quantity | Before | After (estimated) |
|---|---|---|---|
| P2 — HVAC operating regime | run() regime output | NotImplementedError on every call | "heating" for all 4 heating profiles (outside_temp = −10 °C); "cooling" for all 4 cooling profiles (outside_temp = +25 °C) — **8 / 8 profiles produce a valid regime string** |
| P1 — Filter ΔP / ΔP₀ | filter_dp_ratio @ clean_heating (true 1.0) | not computable | **≈ 1.0** (rms_ac ≈ noise → dp_ratio_vib ≈ 1.0; ct_mean ≈ 4.0 A → dp_ratio_ct ≈ 1.0) |
| P1 — Filter ΔP / ΔP₀ | filter_dp_ratio @ near_clog_heating (true 1.85) | not computable | **≈ 1.85** (rms_ac ≈ 0.092 g → dp_ratio_vib ≈ 1.85; ct_mean ≈ 4.41 A → dp_ratio_ct ≈ 1.85) |
| P1 — Filter ΔP / ΔP₀ | alert @ near_clog profiles (1.85 ≥ 1.8) | not computable | **True — alert fires per Amendment 1** |
| P1 — Filter ΔP / ΔP₀ | alert @ clean and mid_clog profiles (1.0 / 1.5) | not computable | **False — no false alert** |

---

## Branch

`stage1/algorithm-regime-cold-shoulder`

---

## Bill 2 roadmap (sequential A7 split)

This Bill (2-A) is the first of four. Complete Suggestion 2-A requires:

| Bill | New algorithm-calibration constant | What it enables | Depends on |
|------|-----------------------------------|-----------------|------------|
| **2-A (this Bill)** | T_COLD_SHOULDER = 5.0 °C | Two-outcome regime classifier; gravity-subtracted vibration proxy; CT proxy inversion; provisional 50/50 fusion; alert gate | Bill 1 (enacted) |
| **2-B** | T_WARM_SHOULDER ≈ 15.0 °C | Three-outcome regime classifier ("off" zone 5–15 °C carved out); eliminates conservative cooling-bias default | Bill 2-A |
| **2-C** | None (structural) | Microphone acoustic proxy; extend diagnostics dict | Bill 2-A + Bill 1-Mic |
| **2-D** | W_VIB (dimensionless blend weight) | Replace 50/50 fusion with physics-grounded weighted fusion derived from per-profile proxy variances; completes Suggestion 2-A | Bill 2-A + 2-B |

**Placeholder derivation for T_WARM_SHOULDER (Bill 2-B):** ≈ 15.0 °C — Canadian balance-point upper edge; commercial rooftop units engage cooling above ~15 °C in summer (ASHRAE 90.1 Canadian supplement). Traces to A1 P2.

**Placeholder derivation for W_VIB (Bill 2-D):** `W_VIB = σ_ct / (σ_vib + σ_ct)` where σ_vib, σ_ct are per-proxy error standard deviations across the eight Bill 1 profiles — noise-weighted combination. Requires Bills 2-A and 2-B enacted to compute. Traces to A1 P1.

---

## Sharpest debate points the hearing must resolve

1. **Is RMS_HARMONIC_FACTOR a hidden algorithm-calibration constant?** It is computed analytically from Bill 1's harmonic amplitude ratios (1, 1/3, 1/6). Attorney-A defends: deterministic mathematical consequence of the enacted forward model — naming it would be aliasing, not introducing a new parameter. Attorney-B challenges: any number hardcoded in source that affects detection behaviour falls under A7's plain text, irrespective of derivation.

2. **Is the provisional 0.5 fusion weight a hidden algorithm-calibration constant?** Attorney-A defends: equal weighting is the unique value that introduces zero information about relative proxy reliability — it is the null hypothesis, not a tuning choice. Bill 2-D will replace it with the physics-derived value. Attorney-B challenges: 0.5 is hardcoded and affects whether `alert` fires; the Justice could direct that Bill 2-A omit the combined estimate entirely (return only dp_ratio_vib pending Bill 2-D), removing the debate point at the cost of a less complete first cut.

3. **Cross-module import of signals.py constants into algorithm.py.** Attorney-A defends: the inverse model must use the same physical relationships as the forward model — mathematical requirement, not architectural choice. Stage 2 calibration of forward-model constants propagates automatically. Attorney-B challenges: this couples algorithm correctness to signal-model state, complicating any future Bill that revises Bill 1.

---

*Ready for Judicial debate. Invoke `/judicial hear "Bill 2-A — Regime Classifier Cold Shoulder + Proxy Inversion Infrastructure" A vs B` to assign attorneys and receive a ruling.*
