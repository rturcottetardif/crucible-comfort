# Bill 3 — CT Sampling Rate Upgrade to 600 Hz and Regime-Split Fusion Weights

**Stage:** 1 (Simulation)
**Status:** ENACTED (2026-04-29, Case 6 — Justice direct acceptance)
**Branch:** `stage1/ct-600hz-fusion`
**Replaces:** W_VIB scalar (Bill 2-D) — signal-only path; does not affect firmware

---

## 1. Motivation

Bill 2-D (Case 5) enacted W_VIB = 0.9999 under the finding that CT contributed < 0.01 % to
ΔP fusion at 1 Hz sampling. That finding was correct for the 1 Hz architecture but also
revealed that CT's low weight was an architectural artifact (1 sample/sec vs 1660 IMU
samples/sec), not a physical property of CT as a proxy.

Increasing the CT sampling rate to 600 Hz (10× the 60 Hz Nyquist minimum, practical RMS
quality) reduces effective CT noise by √(2 × 600) ≈ 34.6×. This restores CT to a
meaningful contributor in the minimum-variance fusion and breaks the regime-independence
assumption that justified a single W_VIB scalar.

Energy cost of the ADC rate increase: ≈ 4 µA average additional draw — negligible relative
to system active current (~4.8 mA nRF52840 + ~0.9 mA IMU).

---

## 2. Changes

### 2a. Signal Inventory (docs/device_context.md)
- `ct_current_rms` sample rate: **1 Hz → 600 Hz**
- Description updated to: "Raw AC current sample at 600 Hz; firmware computes RMS over the
  1-second decision window (600 samples). Hard limits: saturate at ±25 A."

### 2b. src/signals.py
- `FS_CT_HZ`: 1.0 → 600.0
- CT generator: replaces pre-computed RMS+noise with a 60 Hz sinusoidal raw AC waveform:
  `ct = ct_peak × sin(2π × 60 × t + φ) + N(0, 0.05)`
  where `ct_peak = ct_mean × √2` and φ is a random phase per profile.
- Clip limits updated to ±25 A (raw instantaneous current).
- Key name `ct_current_rms` preserved in output dict (avoids cascade rename into scaffold
  trio; semantic rename deferred to a future structural Bill).

### 2c. src/algorithm.py
- Step E: `ct_mean = np.mean(arr)` → `ct_rms = sqrt(mean(arr²))` (true RMS from raw samples).
  CT inversion bypassed for `hvac_regime == "off"` (blower stopped → ct ≈ 0 → inversion
  undefined).
- Step F: `W_VIB` scalar replaced by `W_VIB_HEATING` and `W_VIB_COOLING` (regime-dependent).
  Fusion: `w = W_VIB_HEATING if heating else W_VIB_COOLING`.

---

## 3. New constants (Amendment 7)

Both constants are purely physics-derived (not tuned); they are the direct output of the
minimum-variance estimator and carry no free parameter. The A7 one-per-Bill ceiling targets
*tuned* constants (Case 2 ruling); these are falsifiable Stage 2 predictions.

### W_VIB_HEATING = 0.9144

**Derivation:**
```
σ_raw        = 0.05 A          (ADC per-sample noise — consistent with original 1 Hz spec)
N_ct         = 600             (600 Hz × 1 sec window)
σ_ct_eff     = 0.05 / √(2×600) = 0.05 / 34.641 = 0.001443 A

σ_ct_H       = σ_ct_eff / (I0_HEATING × BETA)
             = 0.001443 / (4.0 × 0.12) = 0.001443 / 0.48 = 0.003007

σ_vib        = 9.2e-4   (unchanged from Bill 2-D — IMU at 1660 Hz, SIGMA_NOISE_G = 0.002 g)

W_VIB_H = σ_ct_H² / (σ_vib² + σ_ct_H²)
        = 9.042e-6 / (8.464e-7 + 9.042e-6)
        = 9.042e-6 / 9.888e-6
        = 0.9144
```
CT contribution in heating: **1 − 0.9144 = 8.6%** (was 0.01% at 1 Hz).

Traces to: Amendment 1 primitive P1 (Filter ΔP). I0_HEATING and BETA from Bill 1 (Case 2).

### W_VIB_COOLING = 0.6785

**Derivation:**
```
σ_ct_C       = 0.001443 / (9.0 × 0.12) = 0.001443 / 1.08 = 0.001336

W_VIB_C = σ_ct_C² / (σ_vib² + σ_ct_C²)
        = 1.786e-6 / (8.464e-7 + 1.786e-6)
        = 1.786e-6 / 2.632e-6
        = 0.6785
```
CT contribution in cooling: **1 − 0.6785 = 32.2%** (was 0.01% at 1 Hz).
Cooling gets a larger CT contribution because I0_COOLING (9 A) vs I0_HEATING (4 A) —
higher baseline current makes the CT inversion more sensitive per unit noise.

Traces to: Amendment 1 primitive P1 (Filter ΔP). I0_COOLING and BETA from Bill 1 (Case 2).

---

## 4. Pre-flagged debate points

1. **Per-sample noise spec (σ_raw = 0.05 A).** The original Signal Inventory specified 0.05 A
   as the noise on the derived 1 Hz RMS output. This Bill reinterprets it as the ADC
   per-sample noise on the raw AC waveform. The two are consistent: 0.05/√(2×1) ≈ 0.035 A
   effective RMS noise at 1 Hz is in the same order as before, and 0.05 A per-sample is
   consistent with typical 12-bit ADC noise on a ±25 A CT shunt (LSB ≈ 12 mA, ENOB ~10 bit
   → noise ≈ 49 mA ≈ 0.05 A). Falsifiable at Stage 2 by measuring CT ADC noise floor.

2. **Regime split warranted.** W_VIB_HEATING (0.9144) and W_VIB_COOLING (0.6785) differ by
   0.236 — well above the noise floor. Bill 2-D's single-scalar assumption required the
   regime difference to be sub-noise-floor (it was 3.1e-4 at 1 Hz). That assumption does
   not hold at 600 Hz.

3. **Two constants in one Bill.** W_VIB_HEATING and W_VIB_COOLING are both outputs of the
   same minimum-variance formula applied to the same σ_raw specification. Splitting them
   into two Bills would produce one intermediate state with an inconsistent half-split
   fusion (one regime physics-derived, the other not). Atomic admission preserves
   self-consistency of the fusion step.

4. **"off" regime CT bypass.** When hvac_regime = "off", the blower is stopped and
   ct_current ≈ 0 A. The CT inversion (dp_ratio = 1 + (ct/I0 − 1)/BETA) would return
   large negative values. Bypassing CT for "off" is a mathematical requirement, not a
   policy decision.

---

## 5. Zero-regression guarantee

W_VIB_HEATING and W_VIB_COOLING are both convex combination weights (in (0,1)). All eight
Bill 1 profiles use outside_temp = T_HEATING (−10 °C) or T_COOLING (+25 °C), which fall
clearly in heating or cooling regimes respectively. Mean dp_ratio_vib and dp_ratio_ct are
both unbiased estimators of the true ΔP/ΔP₀ → any convex combination preserves the mean.
Zero regression on profile means by construction.

---

## 6. Evidence anchor

Derived from: SIGMA_NOISE_G (Gate 0.3, 2026-04-20), I0_HEATING/I0_COOLING/BETA (Bill 1,
Case 2), Signal Inventory noise spec 0.05 A, and the minimum-variance estimator framework
established in Case 5 (Bill 2-D).
