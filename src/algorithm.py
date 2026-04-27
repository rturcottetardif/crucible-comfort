"""ComfortSense algorithm — Python model.

Implements src/algorithm.py per Bill 2-A (ENACTED 2026-04-27, Case 3) and
Bill 2-B (ENACTED 2026-04-27, Case 4).
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
    introduces T_WARM_SHOULDER. Proxy-inversion parameters are imports
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
    if ct_current_rms_arr is not None and ct_current_rms_arr.size > 0:  # P1 CT present — traces to A1 P1
        ct_mean = float(np.mean(ct_current_rms_arr))
        i0 = I0_HEATING if hvac_regime == "heating" else I0_COOLING
        # Inverse of: ct_mean = I0 * (1 + BETA * (dp_ratio - 1)) — traces to A1 P1.
        dp_ratio_ct = 1.0 + (ct_mean / i0 - 1.0) / BETA
    else:
        ct_mean = float("nan")
        dp_ratio_ct = float("nan")

    # Step F — provisional fusion. 0.5 = symmetric null hypothesis on relative
    # proxy reliability, replaced by Bill 2-D's W_VIB. Traces to A1 P1.
    if np.isnan(dp_ratio_ct):
        dp_ratio_combined = dp_ratio_vib  # vibration-only — traces to A1 P1
    else:
        dp_ratio_combined = 0.5 * dp_ratio_vib + 0.5 * dp_ratio_ct  # null fusion — traces to A1 P1

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
            "ct_mean_a": ct_mean,
            "outside_temp_c": temp_c,
        },
    }
