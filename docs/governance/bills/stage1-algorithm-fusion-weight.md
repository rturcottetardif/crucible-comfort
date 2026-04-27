# BILL 2-D: Physics-Derived Vibration Fusion Weight (W_VIB) in src/algorithm.py

```
Drafted by:    bill-drafter agent
Date drafted:  2026-04-27
Change type:   software (algorithm — Python model)
Branch:        stage1/algorithm-fusion-weight
Status:        ENACTED — Case 5 ruling 2026-04-27 (Justice direct ruling on Point 1: physics-derived 0.9999 prevails over design-simplification 1.000)
```

---

## Problem statement

`src/algorithm.py::run()` Step F (Bill 2-A, ENACTED 2026-04-27, Case 3) fuses the vibration-derived dp_ratio proxy and the CT-derived dp_ratio proxy with a hard-coded symmetric weight of 0.5/0.5. Case 3 explicitly accepted this as the "symmetric null hypothesis — the unique value that introduces zero information about relative proxy reliability," conditional on Bill 2-D replacing it with a physics-derived W_VIB.

Evidence that the 0.5 weight is sub-optimal is recorded in `docs/device_context.md` Signal Measurements (commit 89694ab, 2026-04-27):

- `filter_dp_ratio` spread (max − min) over N=16 × 1-sec windows at `near_clog_heating` (true 1.85): **min = 1.783**, mean = 1.859, max = 1.959. The minimum **falls below the Amendment 1 alert edge of 1.8** — detection-margin grazing.
- Heating-regime spread (0.13–0.21) is ≈ 1.7× cooling-regime spread (0.07–0.11). Recorded reason: I0_HEATING (4 A) is half I0_COOLING (9 A), so the 0.05 A CT noise contributes proportionally more in heating mode.

---

## Pre-draft analysis — regime-split test

Amendment 7 + Case 2 require this Bill to introduce **at most one** new algorithm-calibration constant. If the physics-derived value of W_VIB differs meaningfully between heating and cooling regimes, the Bill must split into Bill 2-D-heating and Bill 2-D-cooling.

The derivation below resolves this honestly: W_VIB is regime-independent to four significant figures. **One constant. One Bill. Split not required.**

---

## Proposed change

**File modified:** `src/algorithm.py`. **No other files modified.**

**Amendment 11 check:** algorithm.py excluded from frozen scaffold trio (First Scaffold Authorization SOR, 2026-04-27). No re-scaffold required.

### Change 1 — module docstring header

```
OLD: Implements src/algorithm.py per Bill 2-A (ENACTED 2026-04-27, Case 3) and
     Bill 2-B (ENACTED 2026-04-27, Case 4).
NEW: Implements src/algorithm.py per Bill 2-A (ENACTED 2026-04-27, Case 3),
     Bill 2-B (ENACTED 2026-04-27, Case 4), and
     Bill 2-D (ENACTED [date], [case]).
```

```
OLD: Bill 2-A introduced T_COLD_SHOULDER; Bill 2-B introduces T_WARM_SHOULDER.
NEW: Bill 2-A introduced T_COLD_SHOULDER; Bill 2-B introduced T_WARM_SHOULDER;
     Bill 2-D introduces W_VIB — the physics-derived vibration fusion weight.
```

### Change 2 — add W_VIB constant after T_WARM_SHOULDER

```python
# W_VIB — derived from P1 (Filter ΔP).
# Physical derivation: minimum-variance (inverse-variance) combination of two
#   independent Gaussian proxy estimates for ΔP/ΔP₀. The optimal weight on
#   the vibration proxy is W_VIB = σ_ct² / (σ_vib² + σ_ct²), where σ_vib
#   and σ_ct are the standard deviations of the dp_ratio estimation error
#   from each proxy over a 1-second decision window.
#
#   σ_ct is dominated by the 0.05 A Gaussian noise on ct_current_rms
#   (src/signals.py) sampled at 1 Hz — N_ct = 1 sample per 1-sec window.
#   Propagated through the CT inversion: σ_ct = σ_ct_current / (I0 × BETA).
#     Heating: σ_ct_H = 0.05 / (4.0 × 0.12) = 0.1042
#     Cooling: σ_ct_C = 0.05 / (9.0 × 0.12) = 0.04630
#
#   σ_vib is dominated by SIGMA_NOISE_G = 0.002 g averaged over N_imu = 1660
#   samples per 1-sec window. With ALPHA = 1:
#     σ_rms_ac ≈ SIGMA_NOISE_G / √(2 × N_imu)
#             = 0.002 / √(3320) ≈ 3.47 × 10⁻⁵ g
#     σ_vib = σ_rms_ac / (A_FUND_CLEAN × RMS_HARMONIC_FACTOR)
#           = 3.47 × 10⁻⁵ / (0.05 × 0.7546) ≈ 9.2 × 10⁻⁴
#
#   Inverse-variance weights:
#     W_VIB_H = 0.1042² / ((9.2×10⁻⁴)² + 0.1042²)  ≈ 0.99992
#     W_VIB_C = 0.04630² / ((9.2×10⁻⁴)² + 0.04630²) ≈ 0.99961
#   Difference: |W_VIB_H − W_VIB_C| = 3.1 × 10⁻⁴, smaller than the uncertainty
#   on SIGMA_NOISE_G itself (one significant figure → ~50% relative
#   uncertainty on σ_vib). The regime split is not warranted; the derivation
#   yields a physically single-valued constant.
#
#   W_VIB = 0.9999 adopted (mid-point of 0.99961 and 0.99992 to four
#   significant figures). The vibration proxy averages 1660 samples per
#   1-sec window vs the CT proxy's 1 sample, so the minimum-variance
#   estimator is dominated by vibration. This is a Stage 2 / Stage 3
#   falsifiable prediction — if σ_vib proves > 3σ above the analytic
#   prediction, or if the field decision window admits N_ct > 1 CT sample,
#   W_VIB must be re-derived via a new Bill.
#
#   Roadmap correction: Bill 2-A's roadmap stated W_VIB = σ_ct / (σ_vib + σ_ct)
#   (linear-σ form). The correct minimum-variance formula uses squared
#   variances. Both forms converge to 1.000 in the limit σ_ct >> σ_vib (as
#   here), so the roadmap's prediction was numerically correct.
# Value: 0.9999 (dimensionless).
# Traces to: Amendment 1 primitive P1 (Filter ΔP / ΔP₀ is the fused output).
W_VIB = 0.9999  # dimensionless — traces to A1 P1; min-variance vibration weight
```

### Change 3 — replace Step F in `run()` with W_VIB-weighted fusion

```
OLD:
    # Step F — provisional fusion. 0.5 = symmetric null hypothesis on relative
    # proxy reliability, replaced by Bill 2-D's W_VIB. Traces to A1 P1.
    if np.isnan(dp_ratio_ct):
        dp_ratio_combined = dp_ratio_vib  # vibration-only — traces to A1 P1
    else:
        dp_ratio_combined = 0.5 * dp_ratio_vib + 0.5 * dp_ratio_ct  # null fusion — traces to A1 P1

NEW:
    # Step F — physics-derived fusion (Bill 2-D). W_VIB = minimum-variance
    # (inverse-variance) weight on the vibration proxy, derived from the
    # ratio σ_ct² / (σ_vib² + σ_ct²) using Bill 1 forward-model parameters
    # and Signal Inventory noise specifications. Traces to A1 P1.
    if np.isnan(dp_ratio_ct):
        dp_ratio_combined = dp_ratio_vib  # vibration-only path unchanged — traces to A1 P1
    else:
        dp_ratio_combined = W_VIB * dp_ratio_vib + (1.0 - W_VIB) * dp_ratio_ct  # traces to A1 P1
```

All other lines in `run()` (Steps A, B, C, D, E, G) are identical to enacted Bill 2-B.

### Hardware optimization opportunity (Amendment 9)

The W_VIB ≈ 1.000 result reveals that the CT proxy contributes < 0.01 % to the fused ΔP estimate **under the current 1-sec decision window and 0.05 A CT noise specification**. The CT sensor remains necessary for I0 regime conditioning (via the regime selection in Step E and via the regime classifier in Step B's heating-vs-cooling default — wait, Step B uses outside_temp not CT). Hardware optimization opportunity (A9): `ct_current_rms` for **ΔP fusion** becomes effectively redundant IF Stage 2 confirms σ_ct_current ≈ 0.05 A and the field decision window remains ≈ 1 sec — separate BOM Bill required if human elects to optimize. A longer decision window or lower-noise CT clamp would shift W_VIB down toward a more balanced value and restore CT's information contribution.

---

## Article / Amendment grounding

- **Article I + Amendment 1.** W_VIB traces to P1 via σ_ct ← I0/BETA (Bill 1, Case 2) and σ_vib ← SIGMA_NOISE_G/A_FUND_CLEAN (Bill 1, Case 2 + Gate 0.2/0.3 evidence).
- **Amendment 7 + Case 2.** One new algorithm-calibration constant; ceiling not exceeded. Physically derived, not curve-fit.
- **Case 3.** Discharges the explicit Bill 2-D commitment recorded in Case 3 ruling.
- **Case 4.** Procedural precedent applies — Justice may accept directly when pre-flag points are uncontested.
- **Amendment 5.** W_VIB is a Stage 2 / Stage 3 falsifiable prediction.
- **Amendment 6.** Plot mandate at enactment.
- **Amendment 9.** Hardware optimization opportunity flagged (CT redundancy for ΔP fusion).
- **Amendment 11.** algorithm.py not in frozen trio. No re-scaffold.

---

## Physical evidence

1. `docs/device_context.md` Signal Measurements (2026-04-27, commit 89694ab): near_clog_heating spread min/mean/max = 1.783 / 1.859 / 1.959 — the detection-margin grazing motivation.
2. `docs/device_context.md` Signal Measurements (2026-04-27, commit 89694ab): heating-vs-cooling spread asymmetry 1.7× — empirical confirmation of σ_ct regime asymmetry.
3. `docs/device_context.md` Test Results, Gate 0.2/0.3 (2026-04-20): SIGMA_NOISE_G = 0.002 g.
4. `src/signals.py` (Bill 1, Case 2): I0_HEATING = 4.0, I0_COOLING = 9.0, BETA = 0.12, A_FUND_CLEAN = 0.05, ALPHA = 1.0; ct noise σ = 0.05 A (line 255).
5. Case 3 ruling: explicit Bill 2-D commitment.

---

## Expected outcome

| Quantity | Before (Bill 2-A/B) | After (Bill 2-D) |
|---|---|---|
| Mean filter_dp_ratio @ 8 Bill 1 profiles | 1.00 / 1.50 / 1.85 / 2.00 | **identical** (both proxies unbiased → mean preserved for any W_VIB) |
| Spread (max−min) @ near_clog_heating, N=16 × 1-sec | 0.176 | ≈ 0.176 × (1−W_VIB) ≈ 0.0001 |
| Min @ near_clog_heating | 1.783 (below alert edge) | **≈ 1.859 — clears the 1.8 alert edge in all chunks** |
| Heating spread asymmetry | 1.7× cooling | suppressed — both regimes spread → vibration-only spread (regime-independent) |
| `hvac_regime` output | unchanged | unchanged (Step B untouched) |

**Zero regression on the eight Bill 1 profile means is guaranteed by construction** (both proxies are unbiased in their means, so any convex combination preserves the mean). The detection-margin grazing condition at near_clog_heating **is improved** — the worst-case 1-sec chunk no longer under-reads into the no-alert zone.

---

## Branch

`stage1/algorithm-fusion-weight`

---

## Pre-flagged debate points (Case 3 / Case 4 eligibility)

| # | Point | Drafter assessment |
|---|---|---|
| 1 | **W_VIB = 0.9999 vs 1.000.** At 0.9999, CT formally remains in the ΔP fusion at 0.01 % weight. At 1.000, CT is formally retired from ΔP fusion (the (1−W_VIB) × dp_ratio_ct term becomes identically zero). The physics derivation gives 0.9999; rounding to 1.000 is a *design simplification* that exceeds what the noise analysis alone derives. | **CONTESTED** — recommend either Justice direct ruling on the rounding question, or a Judicial Hearing if the design implication is non-trivial. |
| 2 | Squared-variance correction to Bill 2-A's roadmap formula. | **UNCONTESTED** — formula tightening; numerically identical in this regime. Case 3-eligible. |
| 3 | Regime-split decision (W_VIB_H vs W_VIB_C differ by 3.1 × 10⁻⁴). | **UNCONTESTED** — sub-noise-floor difference; split would create false specificity. Case 3-eligible. |
| 4 | CT retention for I0 regime conditioning vs ΔP fusion. | **UNCONTESTED** as to Bill 2-D scope — A9 BOM Bill is the correct venue. Case 3-eligible. |

The Justice may rule directly on Point 1 (with stated position) or convene a hearing if the architectural implication of W_VIB = 1.000 (formal CT retirement from ΔP fusion) warrants attorney debate.

---

*Ready for Judicial debate on Point 1, OR direct Justice acceptance with stated rounding decision (0.9999 vs 1.000).*
