"""ComfortSense algorithm — Python model.

Implements src/algorithm.py per Bill 2-A (ENACTED 2026-04-27, Case 3),
Bill 2-B (ENACTED 2026-04-27, Case 4), and
Bill 2-D (ENACTED 2026-04-27, Case 5).
Replaces the prior NotImplementedError stub with a regime-conditioned
filter ΔP/ΔP₀ inference using the inverse of Bill 1's signal-model
forward physics (Case 2, 2026-04-27).

The function `run(samples)` accepts either:
  - a dict[str, np.ndarray] keyed by Signal Inventory names (the path
    used by signals.py::generate() output)
  - an np.ndarray of shape (n_steps, C) with column order matching
    src.events.ReadingEvent (ax_g, ay_g, az_g, gx_dps, gy_dps, gz_dps).
    The ndarray path produces a vibration-only verdict — regime defaults
    to "cooling" (Bill 2-A conservative bias) and CT proxy is unavailable.

Constitutional grounding:
  Article I — every constant traces to P1 or P2 per Amendment 1.
  Amendment 1 — outputs filter_dp_ratio (P1) and hvac_regime (P2).
  Amendment 7 + Case 2 — algorithm-calibration class is subject to the
    one-per-Bill ceiling. Bill 2-A introduced T_COLD_SHOULDER; Bill 2-B
    introduced T_WARM_SHOULDER; Bill 2-D introduces W_VIB — the physics-
    derived vibration fusion weight. Proxy-inversion parameters are imports
    from src/signals.py (already enacted under Bill 1 / Case 2).
  Amendment 11 — algorithm.py is excluded from the frozen scaffold trio
    per First Scaffold Authorization SOR (2026-04-27).
"""
from __future__ import annotations

from typing import Any, Mapping

import numpy as np

from src.signals import (
    A_FUND_CLEAN,
    A_Z_DC,
    ALPHA,
    BETA,
    I0_COOLING,
    I0_HEATING,
)


# T_COLD_SHOULDER — derived from P2 (HVAC operating regime).
# Physical derivation: Canadian HVAC systems engage heating when outdoor
#   temperature falls below ~5 °C (the minimum balance-point temperature
#   for commercial rooftop heat-pump / gas-furnace units per ASHRAE 90.1
#   Canadian supplement). T_COLD_SHOULDER = 5 °C is the upper edge of
#   the "clearly heating" zone. Below: heating. At or above: cooling
#   (conservative bias) until Bill 2-B introduces T_WARM_SHOULDER to
#   carve out the "off" ambiguity band. Stage 2/3 DS18B20 field
#   readings will confirm or adjust.
# Value: 5.0 °C.
# Traces to: Amendment 1 primitive P2 (outside_temp is the regime proxy).
T_COLD_SHOULDER = 5.0  # °C — traces to A1 P2; conservative heating upper edge

# T_WARM_SHOULDER — derived from P2 (HVAC operating regime).
# Physical derivation: Canadian commercial rooftop HVAC units engage cooling
#   when outdoor temperature rises above ~15 °C (the upper edge of the
#   balance-point ambiguity band for heat-pump / gas-furnace systems per
#   ASHRAE 90.1 Canadian supplement). Below 5 °C (T_COLD_SHOULDER) the
#   system is clearly in heating mode. Above 15 °C the system is clearly
#   in cooling mode. Between 5 °C and 15 °C the unit is in shoulder season:
#   thermal demand is ambiguous and the blower may be off entirely.
#   Stage 2/3 DS18B20 field readings will confirm or adjust this boundary.
# Value: 15.0 °C.
# Traces to: Amendment 1 primitive P2 (outside_temp is the regime proxy).
T_WARM_SHOULDER = 15.0  # °C — traces to A1 P2; conservative cooling lower edge

# W_VIB_HEATING / W_VIB_COOLING — derived from P1 (Filter ΔP). Bill 3 (Case 6).
# Physical derivation: minimum-variance (inverse-variance) combination of two
#   independent Gaussian proxy estimates for ΔP/ΔP₀. The optimal weight on
#   the vibration proxy is W_VIB = σ_ct² / (σ_vib² + σ_ct²).
#
#   Bill 3: CT sampled at 600 Hz — N_ct = 600 raw AC samples per 1-sec window.
#   σ_raw = 0.05 A (ADC per-sample noise — traces to A1 P1).
#   σ_ct_eff = σ_raw / √(2 × N_ct) = 0.05 / √1200 = 0.001443 A
#   Propagated through CT inversion (σ_ct = σ_ct_eff / (I0 × BETA)):
#     Heating: σ_ct_H = 0.001443 / (4.0 × 0.12) = 0.003007
#     Cooling: σ_ct_C = 0.001443 / (9.0 × 0.12) = 0.001336
#
#   σ_vib unchanged (IMU unchanged at 1660 Hz, SIGMA_NOISE_G = 0.002 g):
#     σ_rms_ac ≈ 0.002 / √(3320) ≈ 3.47e-5 g
#     σ_vib    = 3.47e-5 / (0.05 × 0.7546) ≈ 9.2e-4
#
#   Inverse-variance weights:
#     W_VIB_H = 0.003007² / ((9.2e-4)² + 0.003007²) = 9.042e-6 / 9.888e-6 = 0.9144
#     W_VIB_C = 0.001336² / ((9.2e-4)² + 0.001336²) = 1.786e-6 / 2.632e-6 = 0.6785
#   Difference (0.236) is well above noise floor — regime split warranted (Bill 2-D
#   single-scalar assumption required sub-noise-floor difference; it was 3.1e-4 at 1 Hz).
#
#   CT contribution: 8.6 % heating, 32.2 % cooling. Cooling larger because
#   I0_COOLING (9 A) > I0_HEATING (4 A) → CT inversion more sensitive per unit noise.
# Values: 0.9144 (heating), 0.6785 (cooling). Dimensionless.
# Traces to: Amendment 1 primitive P1 (Filter ΔP / ΔP₀ is the fused output).
W_VIB_HEATING = 0.9144  # dimensionless — traces to A1 P1; min-variance weight, heating
W_VIB_COOLING = 0.6785  # dimensionless — traces to A1 P1; min-variance weight, cooling


def run(samples) -> dict[str, Any]:
    """Run the ComfortSense algorithm against synthetic or captured samples.

    See module docstring for input form details. Returns the dict
    contract specified by Amendment 1:
      filter_dp_ratio: float — Estimated ΔP / ΔP₀
      filter_dp_pa: float | None — Pa value if ΔP₀ calibration available
      hvac_regime: str — "off" | "heating" | "cooling"
      alert: bool — True iff filter_dp_ratio >= 1.8 (A1 alert window low edge)
      diagnostics: dict[str, float]
    """
    # Step A — input adapter (dict or ndarray) — traces to A1 P1/P2.
    if isinstance(samples, Mapping):
        imu_accel_z_arr = np.asarray(samples["imu_accel_z"], dtype=float)
        outside_temp_arr = (
            np.asarray(samples["outside_temp"], dtype=float)
            if "outside_temp" in samples else None
        )
        ct_current_rms_arr = (
            np.asarray(samples["ct_current_rms"], dtype=float)
            if "ct_current_rms" in samples else None
        )
    else:
        # ndarray path — IMU columns only per src.events.ReadingEvent.
        # az_g is column 2 — traces to A1 P1 (Signal Inventory column order).
        arr = np.asarray(samples, dtype=float)
        imu_accel_z_arr = arr[:, 2]
        outside_temp_arr = None
        ct_current_rms_arr = None

    # Step B — regime classification from outside_temp — traces to A1 P2.
    # Three-outcome classifier (Bill 2-B): heating / off / cooling.
    if outside_temp_arr is not None and outside_temp_arr.size > 0:  # P2 present — traces to A1 P2
        temp_c = float(np.mean(outside_temp_arr))
        if temp_c < T_COLD_SHOULDER:
            hvac_regime = "heating"    # traces to A1 P2
        elif temp_c < T_WARM_SHOULDER:
            hvac_regime = "off"        # shoulder-season ambiguity — traces to A1 P2
        else:
            hvac_regime = "cooling"    # traces to A1 P2
    else:
        # ndarray path or missing temp — default to cooling — traces to A1 P2.
        # Conservative bias preserved from Bill 2-A (Case 3): the ndarray path
        # carries no temperature information; "off" cannot be inferred without
        # outside_temp. Bill 2-C / 2-D may revisit this default using proxy
        # signals, but that is out of scope for this Bill.
        temp_c = float("nan")
        hvac_regime = "cooling"

    # Step C — gravity-subtracted vibration proxy — traces to A1 P1.
    # A_Z_DC = 1.0 g (physical constant, Gate 0.2 evidence) imported from signals.py.
    az_ac = imu_accel_z_arr - A_Z_DC
    rms_ac_g = float(np.sqrt(np.mean(az_ac ** 2)))  # AC RMS — traces to A1 P1

    # Step D — vibration → ΔP/ΔP₀ inversion (inverse of Bill 1 forward model).
    # Forward model: rms_ac ≈ A_FUND_CLEAN * dp_ratio^ALPHA * RMS_HARMONIC_FACTOR.
    # RMS_HARMONIC_FACTOR is analytic from Bill 1's harmonic stack (1, 1/3, 1/6) —
    # NOT a calibration constant per Case 3 ruling 2026-04-27. Traces to A1 P1.
    rms_harmonic_factor = float(np.sqrt(0.5 * (1.0 + 1.0 / 9.0 + 1.0 / 36.0)))  # traces to A1 P1
    if rms_ac_g > 0:  # noise-floor guard — traces to A1 P1
        # Inverse: dp_ratio = (rms_ac / (A_FUND_CLEAN * factor))^(1/ALPHA)
        dp_ratio_vib = (
            rms_ac_g / (A_FUND_CLEAN * rms_harmonic_factor)
        ) ** (1.0 / ALPHA)  # traces to A1 P1
    else:
        dp_ratio_vib = 1.0  # default to clean — traces to A1 P1

    # Step E — current → ΔP/ΔP₀ inversion (inverse of Bill 1 CT forward model).
    # Bill 3: ct array now contains raw 600 Hz AC samples; compute true RMS first.
    # "off" regime bypassed — blower stopped → ct ≈ 0 → inversion undefined (Bill 3).
    if (ct_current_rms_arr is not None
            and ct_current_rms_arr.size > 0
            and hvac_regime != "off"):  # P1 CT present, regime defined — traces to A1 P1
        ct_rms = float(np.sqrt(np.mean(ct_current_rms_arr ** 2)))  # true RMS — traces to A1 P1
        i0 = I0_HEATING if hvac_regime == "heating" else I0_COOLING
        # Inverse of: ct_rms = I0 * (1 + BETA * (dp_ratio - 1)) — traces to A1 P1.
        dp_ratio_ct = 1.0 + (ct_rms / i0 - 1.0) / BETA
    else:
        ct_rms = float("nan")
        dp_ratio_ct = float("nan")

    # Step F — regime-dependent physics-derived fusion (Bill 3, Case 6).
    # W_VIB_HEATING / W_VIB_COOLING: minimum-variance weights at 600 Hz CT.
    # "off" regime and missing CT fall through to vibration-only path. Traces to A1 P1.
    if np.isnan(dp_ratio_ct):
        dp_ratio_combined = dp_ratio_vib  # vibration-only path — traces to A1 P1
    else:
        w_vib = W_VIB_HEATING if hvac_regime == "heating" else W_VIB_COOLING  # traces to A1 P1
        dp_ratio_combined = w_vib * dp_ratio_vib + (1.0 - w_vib) * dp_ratio_ct  # traces to A1 P1

    # Step G — alert per Amendment 1 alert window low edge (1.8). Primitive
    # boundary stated in Amendment 1; not a new algorithm-calibration constant.
    alert = dp_ratio_combined >= 1.8  # Amendment 1 primitive P1 alert edge

    return {
        "filter_dp_ratio": float(dp_ratio_combined),
        "filter_dp_pa": None,  # ΔP₀ Pa calibration unavailable until Stage 2
        "hvac_regime": hvac_regime,
        "alert": bool(alert),
        "diagnostics": {
            "rms_ac_g": rms_ac_g,
            "dp_ratio_vib": float(dp_ratio_vib),
            "dp_ratio_ct": float(dp_ratio_ct),
            "ct_rms_a": ct_rms,
            "outside_temp_c": temp_c,
        },
    }
