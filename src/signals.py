"""ComfortSense signal generator — additive harmonic vibration model.

Implements src/signals.py per Bill 1 (ENACTED 2026-04-27, Case 2).
Replaces the prior NotImplementedError stub with a regime-conditioned
multi-signal physics model returning a dict of per-signal arrays.

Eight profiles span the (ΔP/ΔP₀, regime) grid:
  imu_accel_{x,y,z}  — additive harmonic vibration (1660 Hz)
  imu_gyro_{x,y,z}   — Gaussian noise placeholder (1660 Hz)
  ct_current_rms     — slip-driven linear ΔP coupling (1 Hz)
  outside_temp       — regime-step constant (1/60 Hz)
  microphone         — zero placeholder, waveform deferred to Bill 1-Mic (16 kHz)

Each value in the returned dict is a 1-D np.ndarray of length n_steps,
interpreted at the signal's native sample rate (Signal Inventory in
docs/device_context.md). Wall-clock duration therefore differs across signals.

Constitutional grounding:
  Article I (Signal First) — every constant traces to P1 (Filter ΔP) or
    P2 (HVAC operating regime) per Amendment 1.
  Amendment 5 (Simulation is the Hardware Proxy) — outputs are binding
    Stage 2 predictions.
  Amendment 7 (Calibration Discipline) — eleven model parameters carry
    four-line derivation blocks. The A7 one-per-Bill ceiling does NOT
    apply to signal-model constants per Case 2 (2026-04-27).
  Amendment 11 (Scaffold Immutability) — signals.py is excluded from the
    frozen scaffold trio per First Scaffold Authorization SOR (2026-04-27).
"""
from __future__ import annotations

import numpy as np

# Sample rates (Hz) — derived from Signal Inventory in docs/device_context.md.
# Traces to Amendment 1 primitives P1 (IMU/CT/Mic) and P2 (outside_temp).
FS_IMU_HZ = 1660.0  # IMU ODR (Hz) — Signal Inventory; traces to A1 P1
FS_CT_HZ = 600.0  # CT rate (Hz) — Signal Inventory; traces to A1 P1 (Bill 3, Case 6)
FS_TEMP_HZ = 1.0 / 60.0  # outside_temp rate (Hz) — Signal Inventory; traces to A1 P2
FS_MIC_HZ = 16000.0  # microphone rate (Hz) — Signal Inventory; traces to A1 P1


# ────────────────────────────────────────────────────────────────────
# Signal-model constants (Case 2: batch admissible under Amendment 7
# because each carries the four-line derivation block below).
# ────────────────────────────────────────────────────────────────────

# A_FUND_CLEAN — derived from P1 (Filter ΔP).
# Physical derivation: representative peak accel amplitude at blower
#   fundamental frequency on a commercial packaged HVAC housing side-wall,
#   clean filter. Stage 2 prior; literature value for light sheet-metal
#   panel with blower at nominal speed. Falsifiable Stage 2 prediction.
# Value: 0.05 g.
# Traces to: Amendment 1 primitive P1 (vibration is the primary P1 proxy).
A_FUND_CLEAN = 0.05

# ALPHA — derived from P1 (Filter ΔP).
# Physical derivation: first-order linear coupling assumption —
#   A_fund(ΔP) = A0 × (ΔP/ΔP₀)^1. Blower backpressure increases linearly
#   with restriction in the laminar-dominated regime; housing vibration
#   tracks blower torque variation linearly at first order. Stage 2
#   (ΔP, accel) pairs will fit the true exponent.
# Value: 1 (dimensionless).
# Traces to: Amendment 1 primitive P1 (exponent governs P1 → vibration).
ALPHA = 1.0

# SIGMA_NOISE_G — derived from P1 (Filter ΔP).
# Physical derivation: Gate 0.2 stationary accel band 0.004 g peak-to-peak
#   ≈ 2σ at σ = 0.002 g. Consistent with LSM6DS3TR-C noise density
#   90 µg/√Hz × √(1660) ≈ 3.7 mg RMS (model is conservative below spec
#   floor). Evidence: E1, E3 (Gate 0.2 / Gate 0.3, 2026-04-20).
# Value: 0.002 g.
# Traces to: Amendment 1 primitive P1 (noise floor limits Filter ΔP detection).
SIGMA_NOISE_G = 0.002

# F_FUND_HEATING — derived from P2 (HVAC operating regime).
# Physical derivation: heating mode lower blower speed (smaller heating
#   load on Canadian rooftop units). Midpoint of literature 15–25 Hz
#   heating range (900–1500 RPM 2-pole induction motor). Stage 2 tach/FFT
#   will replace this prior.
# Value: 20 Hz.
# Traces to: Amendment 1 primitive P2 (heating regime → blower speed).
F_FUND_HEATING = 20.0

# F_FUND_COOLING — derived from P2 (HVAC operating regime).
# Physical derivation: cooling mode higher blower speed (refrigerant
#   condenser air volume demand). Midpoint of 25–40 Hz cooling range
#   (1500–2400 RPM). Stage 2 tach/FFT will replace this prior.
# Value: 32 Hz.
# Traces to: Amendment 1 primitive P2 (cooling regime → blower speed).
F_FUND_COOLING = 32.0

# I0_HEATING — derived from P2 (HVAC operating regime) and P1 (clean baseline).
# Physical derivation: lower-half of Signal Inventory normal range [2, 8] A,
#   adjusted to 4.0 A for heating-only blower stage (2-speed or VFD low-speed).
#   Stage 2 CT measurements with clean filter will calibrate.
# Value: 4.0 A RMS.
# Traces to: Amendment 1 primitives P2 (regime) and P1 (ΔP/ΔP₀ = 1 anchor).
I0_HEATING = 4.0

# I0_COOLING — derived from P2 (HVAC operating regime) and P1 (clean baseline).
# Physical derivation: upper-half of normal range [8, 15] A, adjusted to
#   9.0 A conservative estimate for 3-ton packaged unit (1/3–1/2 hp blower
#   at 120 V). Stage 2 CT measurements with clean filter will calibrate.
# Value: 9.0 A RMS.
# Traces to: Amendment 1 primitives P2 (regime) and P1 (ΔP/ΔP₀ = 1 anchor).
I0_COOLING = 9.0

# BETA — derived from P1 (Filter ΔP).
# Physical derivation: induction-motor slip increase per ΔP/ΔP₀ unit above
#   baseline. β = 0.12 → 12 % current rise at full clog (ΔP/ΔP₀ = 2). From
#   typical 1/3 hp TEFC efficiency curve (10–15 % loss over slip range).
#   Stage 2 CT measurements will fit per-unit β.
# Value: 0.12 (dimensionless, A/A per ΔP/ΔP₀ unit).
# Traces to: Amendment 1 primitive P1 (β governs P1 → current mapping).
BETA = 0.12

# T_HEATING — derived from P2 (HVAC operating regime).
# Physical derivation: Canadian winter day temperature well below the 5 °C
#   lower regime shoulder. Clear regime separation. Stage 2/3 use actual
#   DS18B20 readings.
# Value: -10 °C.
# Traces to: Amendment 1 primitive P2 (outside_temp is the regime proxy).
T_HEATING = -10.0

# T_COOLING — derived from P2 (HVAC operating regime).
# Physical derivation: mild Canadian summer day, well above the 15 °C upper
#   regime shoulder. Clear regime separation. Stage 2/3 use actual DS18B20
#   readings.
# Value: 25 °C.
# Traces to: Amendment 1 primitive P2 (outside_temp is the regime proxy).
T_COOLING = 25.0

# SPL0 — derived from P1 (Filter ΔP) — PLACEHOLDER ONLY.
# Physical derivation: ASHRAE applications handbook fan sound-power tables
#   for packaged rooftop equipment, conservative lower end at side-wall
#   mounting. Stage 2 mic measurements will calibrate. Waveform generator
#   deferred to Bill 1-Mic.
# Value: 55 dBSPL.
# Traces to: Amendment 1 primitive P1 (acoustic pressure is a P1 proxy).
SPL0 = 55.0

# A_Z_DC — physical constant, NOT a calibration constant.
# Gravitational acceleration projected on the z-axis when the device is
# mounted on a vertical housing side-wall. Fixed by mounting geometry; not
# a tunable parameter and not counted under the A7 one-per-Bill rule.
# Evidence: E1 (Gate 0.2, az = 0.975 g ≈ 1 g on stationary hardware,
# 2026-04-20). Traces to Amendment 1 primitive P1 (gravity reference).
A_Z_DC = 1.0


# ────────────────────────────────────────────────────────────────────
# Profile registry — (ΔP/ΔP₀, regime) tuples per Bill 1 §2.
# ────────────────────────────────────────────────────────────────────

PROFILE_TABLE: dict[str, tuple[float, str]] = {
    "clean_heating":     (1.0,  "heating"),
    "clean_cooling":     (1.0,  "cooling"),
    "mid_clog_heating":  (1.5,  "heating"),
    "mid_clog_cooling":  (1.5,  "cooling"),
    "near_clog_heating": (1.85, "heating"),
    "near_clog_cooling": (1.85, "cooling"),
    "past_clog_heating": (2.0,  "heating"),
    "past_clog_cooling": (2.0,  "cooling"),
}


def generate(profile: str, n_steps: int) -> dict[str, np.ndarray]:
    """Generate synthetic multi-signal samples for a named profile.

    Parameters
    ----------
    profile : str
        One of the eight keys in PROFILE_TABLE.
    n_steps : int
        Length of each returned array. Each signal interprets n_steps at
        its own native sample rate (Signal Inventory) — wall-clock
        duration therefore differs per signal.

    Returns
    -------
    dict[str, np.ndarray]
        Keys match Signal Inventory names: imu_accel_{x,y,z},
        imu_gyro_{x,y,z}, ct_current_rms, outside_temp, microphone.
        Each value is a 1-D float array of length n_steps, clipped to
        Signal Inventory hard limits.

    Raises
    ------
    ValueError
        If `profile` is not a key of PROFILE_TABLE.
    """
    if profile not in PROFILE_TABLE:
        raise ValueError(
            f"unknown profile {profile!r} — valid: {list(PROFILE_TABLE)}. "
            "Register new profiles via a Bill (case_law.md SOR 2026-04-27)."
        )
    dp_ratio, regime = PROFILE_TABLE[profile]

    # Deterministic per-profile RNG — repeated calls produce identical signals.
    rng = np.random.default_rng(abs(hash(profile)) & 0xFFFFFFFF)

    # ── IMU accelerometer (1660 Hz) ────────────────────────────────
    # Harmonic stack: fundamental + 2× + 3× with 1/n amplitude falloff
    # (induction-motor unbalance spectrum — traces to Amendment 1 P1).
    t_imu = np.arange(n_steps) / FS_IMU_HZ
    f_fund = F_FUND_HEATING if regime == "heating" else F_FUND_COOLING
    a_fund = A_FUND_CLEAN * (dp_ratio ** ALPHA)

    # z-axis: gravity DC + harmonic stack + noise. Falloff traces to A1 P1.
    a_z = (
        A_Z_DC
        + a_fund * np.sin(2 * np.pi * f_fund * t_imu)
        + (a_fund / 3.0) * np.sin(2 * np.pi * 2 * f_fund * t_imu)  # 2nd harmonic — traces to A1 P1
        + (a_fund / 6.0) * np.sin(2 * np.pi * 3 * f_fund * t_imu)  # 3rd harmonic — traces to A1 P1
        + rng.normal(0.0, SIGMA_NOISE_G, n_steps)
    )

    # x and y axes: same harmonic stack, no gravity DC, independent phases.
    phi_x = rng.uniform(0.0, 2 * np.pi, 3)
    phi_y = rng.uniform(0.0, 2 * np.pi, 3)
    a_x = (
        a_fund * np.sin(2 * np.pi * f_fund * t_imu + phi_x[0])
        + (a_fund / 3.0) * np.sin(2 * np.pi * 2 * f_fund * t_imu + phi_x[1])  # 2nd harmonic — traces to A1 P1
        + (a_fund / 6.0) * np.sin(2 * np.pi * 3 * f_fund * t_imu + phi_x[2])  # 3rd harmonic — traces to A1 P1
        + rng.normal(0.0, SIGMA_NOISE_G, n_steps)
    )
    a_y = (
        a_fund * np.sin(2 * np.pi * f_fund * t_imu + phi_y[0])
        + (a_fund / 3.0) * np.sin(2 * np.pi * 2 * f_fund * t_imu + phi_y[1])  # 2nd harmonic — traces to A1 P1
        + (a_fund / 6.0) * np.sin(2 * np.pi * 3 * f_fund * t_imu + phi_y[2])  # 3rd harmonic — traces to A1 P1
        + rng.normal(0.0, SIGMA_NOISE_G, n_steps)
    )

    # Saturate accel at ±2 g (Signal Inventory hard limit).
    a_x = np.clip(a_x, -2.0, 2.0)
    a_y = np.clip(a_y, -2.0, 2.0)
    a_z = np.clip(a_z, -2.0, 2.0)

    # ── IMU gyroscope (1660 Hz) ────────────────────────────────────
    # Zero array + Gaussian placeholder noise — traces to Amendment 1 P1
    # (10× SIGMA_NOISE_G in dps, well below the 2 dps stationary bias
    # observed at Gate 0.2). A future Bill will introduce an angular-
    # vibration model for Stage 2.
    gyro_sigma_dps = SIGMA_NOISE_G * 10.0  # placeholder scaling — traces to A1 P1
    g_x = rng.normal(0.0, gyro_sigma_dps, n_steps)
    g_y = rng.normal(0.0, gyro_sigma_dps, n_steps)
    g_z = rng.normal(0.0, gyro_sigma_dps, n_steps)
    # Saturate gyro at ±250 dps (Signal Inventory hard limit).
    g_x = np.clip(g_x, -250.0, 250.0)
    g_y = np.clip(g_y, -250.0, 250.0)
    g_z = np.clip(g_z, -250.0, 250.0)

    # ── CT current raw AC waveform (600 Hz) ───────────────────────
    # Bill 3 (Case 6): raw 60 Hz sinusoidal AC waveform at 600 Hz.
    # Algorithm computes true RMS over the 1-sec window (600 samples).
    # σ_raw = 0.05 A per sample (ADC noise floor — traces to A1 P1).
    # Key name preserved as ct_current_rms for algorithm.py compatibility.
    i0 = I0_HEATING if regime == "heating" else I0_COOLING
    ct_mean = i0 * (1.0 + BETA * (dp_ratio - 1.0))
    ct_peak = ct_mean * np.sqrt(2.0)  # RMS → peak for sinusoid — traces to A1 P1
    ct_phase = rng.uniform(0.0, 2.0 * np.pi)  # random phase per profile
    t_ct = np.arange(n_steps) / FS_CT_HZ
    ct = ct_peak * np.sin(2.0 * np.pi * 60.0 * t_ct + ct_phase) + rng.normal(0.0, 0.05, n_steps)
    # Saturate at ±25 A (raw instantaneous current hard limit — traces to A1 P1).
    ct = np.clip(ct, -25.0, 25.0)

    # ── Outside temp (1/60 Hz) ─────────────────────────────────────
    # Step constant per regime; temporal variation deferred to Stage 2.
    t_outside = T_HEATING if regime == "heating" else T_COOLING
    outside_temp = np.full(n_steps, t_outside, dtype=float)

    # ── Microphone (16 kHz) — placeholder per Bill 1 §3 ────────────
    # Zero array; SPL0 is defined for completeness but the waveform
    # generator is deferred to Bill 1-Mic.
    microphone = np.zeros(n_steps, dtype=float)

    return {
        "imu_accel_x": a_x,
        "imu_accel_y": a_y,
        "imu_accel_z": a_z,
        "imu_gyro_x": g_x,
        "imu_gyro_y": g_y,
        "imu_gyro_z": g_z,
        "ct_current_rms": ct,
        "outside_temp": outside_temp,
        "microphone": microphone,
    }
