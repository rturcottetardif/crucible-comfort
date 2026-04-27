# BILL 2-B: Regime Classifier Warm Shoulder — Three-Outcome Classifier in src/algorithm.py

```
Drafted by:    bill-drafter agent
Date drafted:  2026-04-27
Change type:   software (algorithm — Python model)
Branch:        stage1/algorithm-regime-warm-shoulder
Status:        ENACTED — Case 4 ruling 2026-04-27 (no hearing; Case 3 precedent applied)
```

---

## Problem statement

Bill 2-A (ENACTED 2026-04-27, Case 3) introduced T_COLD_SHOULDER = 5.0 °C and a two-outcome classifier: heating below the cold shoulder, cooling at or above. This conservative bias is physically correct for below-5 °C and above-15 °C conditions, but it collapses the genuine shoulder-season ambiguity band (≈ 5–15 °C) into "cooling." A commercial rooftop unit in spring or fall at ≈ 10 °C outdoor temperature is typically neither heating nor cooling — the blower is off, thermal demand is zero, and the fan and motor current signals are near their noise floors. The current classifier returns regime = "cooling" for such a unit, causing dp_ratio_vib ≈ noise floor and dp_ratio_ct ≈ noise floor to be interpreted against the cooling-regime baselines and reporting filter_dp_ratio ≈ 1.0 with hvac_regime = "cooling" — a physically misclassified state.

The "off" regime is one of the three valid hvac_regime values declared by Amendment 1 P2. The current two-outcome classifier makes hvac_regime = "off" unreachable from `run()`, leaving the algorithm in permanent constitutional deficit with respect to the P2 primitive contract.

This Bill — Bill 2-B, the second in the four-Bill Suggestion 2-A roadmap recorded in Bill 2-A and Case 3 — introduces T_WARM_SHOULDER = 15.0 °C, the upper edge of the shoulder-season ambiguity band, and replaces the two-outcome classifier with a three-outcome classifier:
- outside_temp < T_COLD_SHOULDER (5 °C) → "heating"
- T_COLD_SHOULDER ≤ outside_temp < T_WARM_SHOULDER (15 °C) → "off"
- outside_temp ≥ T_WARM_SHOULDER (15 °C) → "cooling"

The eight enacted Bill 1 simulation profiles use outside_temp values of −10 °C and +25 °C exclusively. Both lie outside the [5, 15) °C "off" band. Zero regression on the existing eight profiles is expected and verifiable.

References:
- `src/algorithm.py` lines 86–94 (Step B — Bill 2-A two-outcome classifier)
- `docs/device_context.md` Signal Inventory (outside_temp, normal range −30 to +45 °C)
- Bill 2-A roadmap table (`docs/governance/bills/stage1-algorithm-regime-cold-shoulder.md`, Bill 2-B row)
- Case 3 ruling 2026-04-27 (Bill 2 roadmap recorded as operative)

---

## Proposed change

**File modified:** `src/algorithm.py`
**No other files modified.** `src/signals.py`, `src/events.py`, `src/analysis.py`, `src/plot.py` are untouched.

**Amendment 11 check:** `src/algorithm.py` is excluded from the frozen scaffold trio per First Scaffold Authorization SOR (case_law.md, 2026-04-27). No re-scaffold required.

### Change 1 — module docstring header (line 4)

Update the Bill enactment line:

```
OLD: Implements src/algorithm.py per Bill 2-A (ENACTED 2026-04-27, Case 3).
NEW: Implements src/algorithm.py per Bill 2-A (ENACTED 2026-04-27, Case 3) and
     Bill 2-B (ENACTED [date], [case]).
```

### Change 2 — module docstring constitutional grounding block

```
OLD: Amendment 7 + Case 2 — algorithm-calibration class is subject to the
       one-per-Bill ceiling. This Bill introduces ONE new constant
       (T_COLD_SHOULDER); proxy-inversion parameters are imports from
       src/signals.py (already enacted under Bill 1 / Case 2).

NEW: Amendment 7 + Case 2 — algorithm-calibration class is subject to the
       one-per-Bill ceiling. Bill 2-A introduced T_COLD_SHOULDER; Bill 2-B
       introduces T_WARM_SHOULDER. Proxy-inversion parameters are imports
       from src/signals.py (already enacted under Bill 1 / Case 2).
```

### Change 3 — add one new module-level algorithm-calibration constant immediately after T_COLD_SHOULDER

```python
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
```

### Change 4 — replace Step B in `run()` (lines 86–94) with three-outcome classifier

```python
# Step B — regime classification from outside_temp — traces to A1 P2.
# Three-outcome classifier (Bill 2-B): heating / off / cooling.
# ndarray path (no outside_temp): cooling default preserved from Bill 2-A
# — the three-outcome classifier requires a temperature input and cannot
# be applied when outside_temp is unavailable.
if outside_temp_arr is not None and outside_temp_arr.size > 0:
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
```

Steps C through G are identical to Bill 2-A (no other lines in `run()` change).

### What this Bill does NOT introduce

- W_VIB — deferred to Bill 2-D
- Microphone proxy — deferred to Bill 2-C (contingent on Bill 1-Mic)
- Any change to `src/signals.py`, `src/events.py`, `src/analysis.py`, or `src/plot.py`

### Hardware optimization opportunity (Amendment 9)

**None.** The classifier consumes the existing `outside_temp` signal; no sensor is made redundant.

---

## Article / Amendment grounding

**Primary:**

- **Article I — Signal First.** T_WARM_SHOULDER traces to P2 per the four-line A7 derivation block. Derived from the ASHRAE 90.1 Canadian supplement balance-point upper edge — a physical climate threshold, not a tuned parameter.
- **Amendment 1 — Domain Primitives.** P2 declares three valid states: heating / cooling / off. Bill 2-A left "off" unreachable; this Bill completes the P2 primitive contract by making all three states producible.
- **Amendment 7 — Calibration Discipline.** One new algorithm-calibration constant (T_WARM_SHOULDER). Four-line derivation block provided. Ceiling not exceeded.
- **Case 2 (2026-04-27).** Algorithm-calibration class subject to A7. Signal-model exemption applies only to `src/signals.py`, not `src/algorithm.py`.
- **Case 3 (2026-04-27).** Bill 2 roadmap recorded as operative. Procedural precedent: Justice may accept directly when drafter's pre-flagged debate points are uncontested.

**Supporting:**

- **Amendment 5.** Zero regression on the eight enacted Bill 1 profiles is verifiable post-enactment.
- **Amendment 6.** Algorithm parameter change → plot mandate at enactment.
- **Amendment 11.** algorithm.py not in frozen trio. No re-scaffold.

---

## Physical evidence

1. **Signal Inventory (`docs/device_context.md`):** outside_temp normal range −30 to +45 °C; T_WARM_SHOULDER = 15.0 °C is well within the operational envelope.
2. **Bill 2-A roadmap placeholder derivation:** "≈ 15.0 °C — Canadian balance-point upper edge; commercial rooftop units engage cooling above ~15 °C in summer (ASHRAE 90.1 Canadian supplement). Traces to A1 P2." Carried forward as the primary physical basis, consistent with T_COLD_SHOULDER = 5 °C from the same standard.
3. **Gate 0.3 (2026-04-20):** stationary rms_g ∈ [1.0014, 1.0056] vs vigorous-motion rms_g ∈ [1.0228, 2.0154] — supports the physical premise that an "off" unit (blower stopped) produces a near-stationary signal that the two-outcome classifier misclassifies as a clean "cooling" unit.
4. **Bill 1 PROFILE_TABLE (Case 2, 2026-04-27):** T_HEATING = −10 °C and T_COOLING = +25 °C are the only outside_temp values in the eight enacted profiles. Both lie outside [5, 15) °C — zero regression by inspection.

### Evidence gap (acknowledged, not a blocker)

No Bill 1 simulation profile uses an `outside_temp` value in the [5.0, 15.0) °C shoulder-season band. The "off" classification branch is exercisable only by code inspection and manual unit test (e.g., `run({"outside_temp": np.array([10.0]), ...})`) until a future Bill adds a shoulder-season profile to `src/signals.py`. This does **not** block Bill 2-B: the "off" branch is a pure classifier change with no inversion arithmetic; the threshold's physical correctness rests on the ASHRAE derivation and the Signal Inventory envelope. Recommended follow-up: a shoulder-season profile Bill (e.g., `clean_off` at outside_temp = 10 °C, blower = off, ct_current ≈ 0 A, az ≈ A_Z_DC + noise) — a Bill 1 amendment, separate from Bill 2-B's scope.

---

## Expected outcome

| Primitive | Quantity | Before (Bill 2-A) | After (Bill 2-B) |
|---|---|---|---|
| P2 — HVAC operating regime | Producibility of "off" | unreachable | **returned for outside_temp ∈ [5.0, 15.0) °C** |
| P2 — eight Bill 1 profiles, regime | heating @ −10 °C / cooling @ +25 °C | unchanged | **identical — zero regression** |
| P1 — filter_dp_ratio for the eight Bill 1 profiles | 1.00 / 1.50 / 1.85 / 2.00 | unchanged | **identical — zero regression** |
| P1 — alert behaviour (eight profiles) | True at near_clog_*, past_clog_* only | unchanged | **identical — zero regression** |

---

## Branch

`stage1/algorithm-regime-warm-shoulder`

---

## Pre-flagged debate points (Case 3 no-hearing eligibility)

1. **ndarray path default preserved as "cooling".** With a three-outcome classifier now available, an attorney might argue the ndarray default should change to "off". Drafter position: the ndarray path carries no thermal information; "off" requires either `outside_temp` evidence or a proxy signal (vibration noise floor, zero CT). Defaulting to "cooling" is the same conservative bias Case 3 accepted; changing it to "off" would suppress Steps E/F entirely and silently change behaviour for existing ndarray callers without physical justification. **Assessment:** not contestable on physical grounds — direct carry-forward of Bill 2-A's enacted behaviour.

2. **T_WARM_SHOULDER value precision (15 °C).** An attorney might argue 18 °C (Heating Degree Day standard) or 10 °C (ISO 15927-6 European base). Drafter position: 15 °C is the ASHRAE 90.1 Canadian supplement value cited in Bill 2-A's roadmap (which Case 3 accepted), grounded in the Canadian rooftop application context (Amendment 1 / Device Purpose). The constant is falsifiable — Stage 2/3 field readings can adjust it with physical evidence. **Assessment:** not contestable as a blocker — physically derived, within envelope, explicitly subject to field confirmation.

If neither point is contested, the Justice may apply Case 3 procedural precedent and accept directly.

---

*Ready for Judicial debate. Invoke `/judicial hear "Bill 2-B — Regime Classifier Warm Shoulder" A vs B` to assign attorneys, OR apply Case 3 precedent for direct acceptance.*
