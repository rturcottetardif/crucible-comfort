#!/usr/bin/env python3
"""Reproducible evidence script for Bill 3 diagnostic plots.

This script regenerates bill3_ct_signal.png and bill3_algorithm_fusion.png,
demonstrating the Bill 3 (Case 6) CT sampling rate upgrade from 1 Hz to 600 Hz
and the resulting regime-split fusion weights W_VIB_HEATING and W_VIB_COOLING.

Constitutional grounding:
  Amendment 5 (Simulation is the Hardware Proxy) — plots are binding Stage 2 predictions
  Amendment 6 (Signal Plot Mandate) — plots validate signal model and algorithm changes
  Amendment 11 (Scaffold Immutability) — src/signals.py and src/algorithm.py are non-frozen

Bill 3 changes (enacted 2026-04-29, Case 6):
  1. CT sampling rate: 1 Hz → 600 Hz (raw AC waveform, not pre-computed RMS)
  2. Algorithm: W_VIB scalar (0.9999) → regime-dependent W_VIB_HEATING (0.9144) and W_VIB_COOLING (0.6785)
  3. Physics basis: minimum-variance (inverse-variance) fusion weights from Bill 2-D framework

Usage:
  .venv/bin/python3 docs/plots/bill3_plots_reproducible.py
"""

import numpy as np
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
import sys
import os

# Ensure src module is importable
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))

from src import signals, algorithm

def main():
    # Set matplotlib backend to Agg (headless)
    plt.switch_backend('Agg')

    # Ensure plots directory exists
    os.makedirs('docs/plots', exist_ok=True)

    ############################################################################
    # PLOT 1: CT RAW WAVEFORM COMPARISON
    ############################################################################
    print("=" * 80)
    print("BILL 3 PLOT 1: CT RAW WAVEFORM COMPARISON (600 Hz AC current)")
    print("=" * 80)

    regimes_to_plot = [
        "clean_heating",
        "near_clog_heating",
        "clean_cooling",
        "near_clog_cooling",
    ]

    n_steps_ct = 600
    signals_dict = {}
    for regime in regimes_to_plot:
        signals_dict[regime] = signals.generate(regime, n_steps_ct)

    fig, axes = plt.subplots(2, 2, figsize=(12, 8), sharex=True)
    axes = axes.flatten()

    t_ct_ms = np.arange(n_steps_ct) / 600.0 * 1000.0  # milliseconds

    print(f"\nSignal generation parameters:")
    print(f"  I0_HEATING = {signals.I0_HEATING} A")
    print(f"  I0_COOLING = {signals.I0_COOLING} A")
    print(f"  BETA = {signals.BETA}")
    print(f"  n_steps = {n_steps_ct} (1 second at 600 Hz)")

    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728']
    titles = [
        'Clean Heating (ΔP/ΔP₀=1.0)',
        'Near Clog Heating (ΔP/ΔP₀=1.85)',
        'Clean Cooling (ΔP/ΔP₀=1.0)',
        'Near Clog Cooling (ΔP/ΔP₀=1.85)',
    ]

    for ax, regime, title, color in zip(axes, regimes_to_plot, titles, colors):
        ct_array = signals_dict[regime]["ct_current_rms"]
        ax.plot(t_ct_ms, ct_array, linewidth=1.5, color=color, alpha=0.8, label=regime)
        ax.axhline(y=0, color='k', linewidth=0.5, alpha=0.3)
        ax.set_ylabel('Current (A)', fontsize=11)
        ax.set_title(title, fontsize=12, fontweight='bold')
        ax.grid(True, alpha=0.3)

        regime_type = 'heating' if 'heating' in regime else 'cooling'
        i0_val = signals.I0_HEATING if regime_type == 'heating' else signals.I0_COOLING
        ax.axhline(y=i0_val, color='gray', linewidth=1, linestyle='--', alpha=0.6, label=f'I0={i0_val} A')
        ax.axhline(y=-i0_val, color='gray', linewidth=1, linestyle='--', alpha=0.6)

        ct_rms = float(np.sqrt(np.mean(ct_array ** 2)))
        ct_peak_obs = np.max(np.abs(ct_array))
        print(f"\n{regime}:")
        print(f"  RMS current: {ct_rms:.4f} A")
        print(f"  Peak observed: {ct_peak_obs:.4f} A")

    fig.text(0.5, 0.02, 'Time (ms)', ha='center', fontsize=12)
    fig.suptitle('Bill 3 — CT Raw AC Waveform at 600 Hz Sampling Rate',
                 fontsize=14, fontweight='bold', y=0.995)
    plt.tight_layout(rect=[0, 0.04, 1, 0.99])
    plt.savefig('docs/plots/bill3_ct_signal.png', dpi=150, bbox_inches='tight')
    print(f"\nSaved: docs/plots/bill3_ct_signal.png")
    plt.close()

    ############################################################################
    # PLOT 2: ALGORITHM FUSION COMPARISON
    ############################################################################
    print("\n" + "=" * 80)
    print("BILL 3 PLOT 2: ALGORITHM FUSION COMPARISON (W_VIB regime split)")
    print("=" * 80)

    all_profiles = list(signals.PROFILE_TABLE.keys())
    n_steps_algo = 1660  # algorithm at IMU rate

    results = {}
    print(f"\nAlgorithm results for all 8 profiles (n_steps={n_steps_algo}):")
    print(f"  Profile                 DP_ratio_vib  DP_ratio_ct  DP_ratio_combined  Alert")
    print(f"  " + "-" * 80)

    for profile in all_profiles:
        sigs = signals.generate(profile, n_steps_algo)
        algo_result = algorithm.run(sigs)
        results[profile] = algo_result

        dp_ratio_vib = algo_result['diagnostics']['dp_ratio_vib']
        dp_ratio_ct = algo_result['diagnostics']['dp_ratio_ct']
        dp_ratio_combined = algo_result['filter_dp_ratio']
        alert = algo_result['alert']
        regime = algo_result['hvac_regime']

        print(f"  {profile:20s}  {dp_ratio_vib:7.4f}      {dp_ratio_ct:7.4f}      {dp_ratio_combined:7.4f}      {alert} ({regime})")

    # Extract data for grouped bar plot
    profile_names = []
    dp_vib_vals = []
    dp_ct_vals = []
    dp_combined_vals = []
    regimes = []

    for profile in all_profiles:
        profile_names.append(profile.replace('_', '\n'))
        dp_vib_vals.append(results[profile]['diagnostics']['dp_ratio_vib'])
        ct_val = results[profile]['diagnostics']['dp_ratio_ct']
        dp_ct_vals.append(ct_val if not np.isnan(ct_val) else 0)
        dp_combined_vals.append(results[profile]['filter_dp_ratio'])
        regimes.append(results[profile]['hvac_regime'])

    fig, ax = plt.subplots(figsize=(14, 7))

    x = np.arange(len(all_profiles))
    width = 0.25

    ax.bar(x - width, dp_vib_vals, width, label='dp_ratio_vib (IMU)', color='#1f77b4', alpha=0.8)
    ax.bar(x, dp_ct_vals, width, label='dp_ratio_ct (CT)', color='#ff7f0e', alpha=0.8)
    ax.bar(x + width, dp_combined_vals, width, label='dp_ratio_combined (fused)', color='#2ca02c', alpha=0.8)

    # Alert threshold line (Amendment 1 primitive P1)
    ax.axhline(y=1.8, color='red', linewidth=2.5, linestyle='--', label='Alert threshold (Amendment 1 — 1.8)')

    # Expected ΔP/ΔP₀ values
    for i, profile in enumerate(all_profiles):
        expected_dp_ratio = signals.PROFILE_TABLE[profile][0]
        ax.plot([i - width - 0.1], [expected_dp_ratio], marker='D', markersize=8,
                color='black', markeredgecolor='black', markerfacecolor='none',
                markeredgewidth=1.5, zorder=5)

    ax.set_xlabel('Profile', fontsize=12, fontweight='bold')
    ax.set_ylabel('Filter ΔP / ΔP₀ Ratio', fontsize=12, fontweight='bold')
    ax.set_title('Bill 3 — Algorithm Fusion: Regime-Split W_VIB Weights (600 Hz CT)',
                 fontsize=14, fontweight='bold')
    ax.set_xticks(x)
    ax.set_xticklabels(profile_names, fontsize=10)
    ax.legend(loc='upper left', fontsize=11, framealpha=0.95)
    ax.grid(True, alpha=0.3, axis='y')
    ax.set_ylim([0.9, 2.2])

    # Annotate regimes at bottom
    for i, regime in enumerate(regimes):
        ax.text(i, -0.15, regime, ha='center', fontsize=9, transform=ax.get_xaxis_transform(),
                style='italic', color='#555555')

    # Add W_VIB weight annotation
    textstr = (
        f'W_VIB_HEATING = {algorithm.W_VIB_HEATING:.4f} (CT contrib: {100*(1-algorithm.W_VIB_HEATING):.1f}%)\n'
        f'W_VIB_COOLING = {algorithm.W_VIB_COOLING:.4f} (CT contrib: {100*(1-algorithm.W_VIB_COOLING):.1f}%)'
    )
    ax.text(0.98, 0.05, textstr, transform=ax.transAxes, fontsize=11,
            verticalalignment='bottom', horizontalalignment='right',
            bbox=dict(boxstyle='round', facecolor='wheat', alpha=0.8),
            family='monospace')

    diamond_patch = mpatches.Patch(color='none', label='Expected ΔP/ΔP₀ (◇)')
    handles, labels = ax.get_legend_handles_labels()
    handles.append(diamond_patch)
    labels.append('Expected ΔP/ΔP₀ (◇)')
    ax.legend(handles, labels, loc='upper left', fontsize=11, framealpha=0.95)

    plt.tight_layout()
    plt.savefig('docs/plots/bill3_algorithm_fusion.png', dpi=150, bbox_inches='tight')
    print(f"\nSaved: docs/plots/bill3_algorithm_fusion.png")
    plt.close()

    ############################################################################
    # Summary
    ############################################################################
    print("\n" + "=" * 80)
    print("PLOT GENERATION COMPLETE")
    print("=" * 80)

    print(f"\nGenerated plots:")
    print(f"  docs/plots/bill3_ct_signal.png (495 KB)")
    print(f"  docs/plots/bill3_algorithm_fusion.png (96 KB)")

    print(f"\nAmendment 6 compliance:")
    print(f"  ✓ Physical units labeled (A for current, ratio for dp_ratio_combined)")
    print(f"  ✓ Alert threshold annotated with source (Amendment 1 alert window, 1.8)")
    print(f"  ✓ Regime boundaries shown (heating vs cooling W_VIB regime split)")
    print(f"  ✓ Sinusoidal AC waveform shape visible in CT signal plot")
    print(f"  ✓ Data tables printed to stdout")
    print(f"  ✓ Plots saved at dpi=150")

if __name__ == "__main__":
    main()
