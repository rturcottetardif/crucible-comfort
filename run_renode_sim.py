"""
Path B Renode simulation runner — Stage 1 gate validation.
Profile: near_clog_cooling (dp_ratio=1.85, regime=cooling)
ELF: build/arduino/xiaonRF52840Sense/stage1_algo_usb.ino.elf

Dispatched by simulator-operator agent (Standing Order, Amendment 5).
Constitutional basis: Bill 4 / Case 7 — ALERT event; Renode path required
for Stage 1 gate per Path B mandate.

Infrastructure note: This runner extends the RenoneBridge _configure_renode
sequence with a USBD no-op stub (sim_usbd_stub.py) to prevent the SVD-backed
USBD from triggering spurious interrupts. The watchpoint hook at 0x40002008 is
intentionally OMITTED here — sim_uart_stub.py fires self.IRQ.Set()/Unset()
directly after each STARTTX, which is sufficient to unblock Serial1.print().
Adding the watchpoint as well double-fires IRQ 2 (UARTE0) causing re-entrant
ISR stack overflow and the 0xA5A5A5A4 crash. Omitting the watchpoint is the
correct configuration when sim_uart_stub.py has its own IRQ firing logic.

This workaround is project-local per toolchain_config.md Case 1 Condition 7
scope. A follow-up Bill is required to update crucible/sim/renode.py formally.
"""
import sys
import os
import socket
import subprocess
import tempfile
import time
from pathlib import Path

# Ensure project root is on sys.path
PROJECT_ROOT = "/Users/roxanneturcotte/CrucibleStudio/crucible-comfort"
if PROJECT_ROOT not in sys.path:
    sys.path.insert(0, PROJECT_ROOT)

import numpy as np

from src.signals import generate, PROFILE_TABLE
from src.analysis import PARSER
from crucible.sim.renode import detect_renode
from crucible.sim.renode import _CFG_IMU_PATH, _CFG_LOG_PATH, _CFG_SENT_PATH
from crucible.sim.renode import _TELNET_HOST, _TELNET_PORT
from crucible.sim.renode import _MonitorClient

ELF_PATH    = os.path.join(PROJECT_ROOT, "build/arduino/xiaonRF52840Sense/stage1_algo_usb.ino.elf")
STUBS_DIR   = os.path.join(PROJECT_ROOT, "crucible/sim/stubs")
IMU_STUB    = os.path.join(STUBS_DIR, "sim_imu_stub.py")
UART_STUB   = os.path.join(STUBS_DIR, "sim_uart_stub.py")
USBD_STUB   = os.path.join(STUBS_DIR, "sim_usbd_stub.py")
PROFILE     = "near_clog_cooling"
# N_WINDOW = 1660 (one decision window per firmware). Run 3 windows for
# at least two ALERT events after the 450-sample stationary prefix.
N_STEPS     = 1660 * 3
N_PRE       = 450  # stationary calibration prefix samples

BOOT_TIMEOUT_S    = 20.0
SESSION_TIMEOUT_S = 300.0
POLL_INTERVAL_S   = 0.5

print("=" * 70)
print("SIMULATION PATH: Renode (thorough) — caller explicitly requested Path B")
print(f"Profile : {PROFILE}")
print(f"ELF     : {ELF_PATH}")
print(f"ELF size: {os.path.getsize(ELF_PATH):,} bytes")
print(f"n_steps : {N_STEPS} samples @ 1660 Hz = {N_STEPS/1660:.2f}s signal")
print(f"Renode  : {detect_renode()}")
print("=" * 70)

# ── Step 1: Generate signal sequence ────────────────────────────────────────
print("\n[1/5] Generating signal sequence...")
signal_dict = generate(PROFILE, N_STEPS)
az_array = signal_dict["imu_accel_z"]

# Build N x 6 float32 array expected by stubs ([ax ay az gx gy gz])
samples = np.column_stack([
    signal_dict["imu_accel_x"],
    signal_dict["imu_accel_y"],
    signal_dict["imu_accel_z"],
    signal_dict["imu_gyro_x"],
    signal_dict["imu_gyro_y"],
    signal_dict["imu_gyro_z"],
]).astype(np.float32)

print(f"    Generated {len(samples)} samples, az mean={np.mean(az_array):.4f} g, "
      f"az ac_rms={float(np.sqrt(np.mean((az_array - 1.0)**2))):.6f} g")
print(f"    Profile dp_ratio (target): {PROFILE_TABLE[PROFILE][0]:.2f}, "
      f"regime: {PROFILE_TABLE[PROFILE][1]}")

# ── Step 2: Path A reference ─────────────────────────────────────────────────
print("\n[2/5] Computing Path A reference dp_ratio (Python model)...")
from src.algorithm import run as run_algorithm
path_a_result = run_algorithm(signal_dict)
print(f"    Path A dp_ratio  = {path_a_result['filter_dp_ratio']:.4f}")
print(f"    Path A regime    = {path_a_result['hvac_regime']}")
print(f"    Path A alert     = {path_a_result['alert']}")
print(f"    Path A rms_ac_g  = {path_a_result['diagnostics']['rms_ac_g']:.6f} g")
print(f"    Path A vib dp    = {path_a_result['diagnostics']['dp_ratio_vib']:.4f}")

# ── Step 3: Prepare IMU f32 file ─────────────────────────────────────────────
print("\n[3/5] Preparing IMU sample file and launching Renode...")

stationary = np.zeros((N_PRE, 6), dtype=np.float32)
stationary[:, 2] = 1.0   # az = 1 g (gravity) — stationary calibration prefix
full_samples = np.vstack([stationary, samples]).astype(np.float32)
n_total = len(full_samples)

imu_path  = Path("/tmp/crucible_imu_sim.f32")
uart_path = Path.home() / "crucible_uart.log"
sentinel  = Path(str(uart_path) + ".done")

full_samples.tofile(str(imu_path))
uart_path.unlink(missing_ok=True)
sentinel.unlink(missing_ok=True)
Path(os.path.expanduser("~/.crucible_stub_idx.txt")).unlink(missing_ok=True)

_CFG_IMU_PATH.write_text(str(imu_path))
_CFG_LOG_PATH.write_text(str(uart_path))
_CFG_SENT_PATH.write_text(str(sentinel))

print(f"    IMU file: {imu_path} ({os.path.getsize(str(imu_path)):,} bytes, "
      f"{n_total} samples = {N_PRE} stationary + {N_STEPS} signal)")

# ── Step 3b: Launch Renode ────────────────────────────────────────────────────
renode_bin = detect_renode()
renode_log = Path(tempfile.mktemp(suffix="_renode.log"))
proc = subprocess.Popen(
    [renode_bin, "--disable-xwt", "--port", str(_TELNET_PORT)],
    stdout=open(str(renode_log), "w"),
    stderr=subprocess.STDOUT,
)

wall_start = time.monotonic()
monitor = None
deadline = time.monotonic() + BOOT_TIMEOUT_S
while time.monotonic() < deadline:
    try:
        monitor = _MonitorClient(_TELNET_HOST, _TELNET_PORT)
        monitor._recv_until(b") \x1b[0m", timeout=5.0)
        break
    except (ConnectionRefusedError, OSError, TimeoutError):
        time.sleep(0.3)
        monitor = None
if monitor is None:
    proc.terminate()
    tail = renode_log.read_text(errors="replace")[-500:] if renode_log.exists() else ""
    print(f"[PIPELINE-ERROR] Renode monitor did not open within {BOOT_TIMEOUT_S}s")
    print(f"Renode log tail:\n{tail}")
    sys.exit(1)

print("    Renode monitor connected")

# ── Step 3c: Configure Renode ─────────────────────────────────────────────────
def mon_send(cmd, timeout=30.0, label=None):
    resp = monitor.send(cmd, timeout=timeout)
    tag = label or cmd[:40]
    print(f"    [Renode] {tag}: {resp.strip()!r}")
    if "error" in resp.lower() or "exception" in resp.lower():
        raise RuntimeError(f"Renode command failed [{tag}]: {resp.strip()}")
    return resp

# REPL 1: nrf52840 base + IMU stub at 0x400B0000
repl1_content = (
    'using "platforms/cpus/nrf52840.repl"\n\n'
    'sim_imu: Python.PythonPeripheral @ sysbus 0x400B0000\n'
    '    size: 0x100\n'
    f'    filename: "{IMU_STUB}"\n'
    '    initable: true\n'
)
# REPL 2: USBD no-op stub at 0x40027000.
# The SVD-backed nrf52840.repl tags 0x40027000 as USBD but does not register a
# peripheral model. Without a PythonPeripheral here, Renode fires spurious
# USBD_IRQHandler calls via the SVD interrupt model, corrupting the FreeRTOS
# stack (0xA5A5A5A4 crash). Registering a PythonPeripheral absorbs all
# reads/writes silently and prevents the spurious IRQ.
repl2_content = (
    'sim_usbd: Python.PythonPeripheral @ sysbus <0x40027000, +0x1000>\n'
    '    size: 0x1000\n'
    f'    filename: "{USBD_STUB}"\n'
    '    initable: true\n'
)
# REPL 3: UART Python stub (replaces built-in uart0).
# NOTE: The watchpoint hook at 0x40002008 used by the upstream RenoneBridge
# is intentionally OMITTED. sim_uart_stub.py fires self.IRQ.Set()/Unset()
# itself on STARTTX — that is sufficient to unblock nrfx UARTE ISR.
# Adding the watchpoint as well double-fires IRQ 2 and causes re-entrant ISR
# stack overflow (the 0xA5A5A5A4 crash during UART transmission).
repl3_content = (
    'sim_uart: Python.PythonPeripheral @ sysbus <0x40002000, +0x1000>\n'
    '    size: 0x1000\n'
    f'    filename: "{UART_STUB}"\n'
    '    initable: true\n'
)

tmp_files = []
try:
    for content in [repl1_content, repl2_content, repl3_content]:
        with tempfile.NamedTemporaryFile(mode="w", suffix=".repl", delete=False) as f:
            f.write(content)
            tmp_files.append(f.name)

    mon_send('mach create "device"', label="mach create")
    mon_send(f"machine LoadPlatformDescription @{tmp_files[0]}", label="LoadPlatformDesc (nrf52840+IMU)")
    # USBD stub must be loaded before uart0 unregister so the SVD USBD cannot
    # fire between uart0 removal and uart stub registration.
    mon_send(f"machine LoadPlatformDescription @{tmp_files[1]}", label="LoadPlatformDesc (USBD no-op)")
    mon_send("sysbus Unregister uart0", label="Unregister uart0")
    mon_send(f"machine LoadPlatformDescription @{tmp_files[2]}", label="LoadPlatformDesc (UART stub)")
    mon_send(f"sysbus LoadELF @{ELF_PATH}", timeout=60.0, label="LoadELF")
    # No watchpoint hook -- sim_uart_stub.py handles IRQ firing internally.

    # Boot: run 2.0s simulated time to let FreeRTOS/USB init settle.
    # Longer window reduces risk of timeout if FreeRTOS tick is slow in Renode.
    print("    [Renode] RunFor 2.0s (boot) — waiting up to 120s wall time...")
    mon_send('emulation RunFor "2.0"', timeout=120.0, label="RunFor 2.0s (boot)")

except Exception as exc:
    print(f"\n[PIPELINE-ERROR] Renode configuration failed: {type(exc).__name__}: {exc}")
    try:
        monitor.send("quit")
    except Exception:
        pass
    proc.terminate()
    if renode_log.exists():
        print(f"\n[Renode log tail]\n{renode_log.read_text(errors='replace')[-2000:]}\n[/Renode log]")
    for f in tmp_files:
        try: os.unlink(f)
        except Exception: pass
    sys.exit(1)

# ── Step 3d: Poll for session end ─────────────────────────────────────────────
print(f"\n    [Renode] Polling for SESSION_END sentinel (timeout {SESSION_TIMEOUT_S}s)...")
odr_hz   = 1660.0
walk_s   = n_total / odr_hz
elapsed  = 0.0
chunk    = 0.5
deadline = time.monotonic() + SESSION_TIMEOUT_S
found    = False

while time.monotonic() < deadline:
    try:
        monitor.send(f'emulation RunFor "{chunk}"')
    except Exception as exc:
        print(f"    [Renode] RunFor chunk failed: {exc}")
        break
    elapsed += chunk
    if sentinel.exists():
        found = True
        break
    time.sleep(POLL_INTERVAL_S)
    if elapsed > walk_s + 10.0:
        break

# Stop Renode
try:
    monitor.send("quit")
except Exception:
    pass
monitor.close()
try:
    proc.terminate()
    proc.wait(timeout=5)
except Exception:
    pass

wall_elapsed = time.monotonic() - wall_start

for f in tmp_files:
    try: os.unlink(f)
    except Exception: pass
sentinel.unlink(missing_ok=True)

if not found:
    print(f"\n[ESCALATION] SESSION_END sentinel not seen after {elapsed:.1f}s simulated.")
    if uart_path.exists():
        uart_text = uart_path.read_text(encoding="utf-8", errors="replace")
        print(f"UART log ({len(uart_text)} bytes):\n{uart_text}")
    if renode_log.exists():
        print(f"\n[Renode log tail]\n{renode_log.read_text(errors='replace')[-2000:]}\n[/Renode log]")
    renode_log.unlink(missing_ok=True)
    sys.exit(1)

renode_log.unlink(missing_ok=True)
print(f"\n[3/5] Renode run complete — wall time: {wall_elapsed:.1f}s, "
      f"simulated: {elapsed:.1f}s, samples: {n_total}")

# ── Step 4: uart-reader — print UART output to terminal ─────────────────────
uart_text = uart_path.read_text(encoding="utf-8", errors="replace") if uart_path.exists() else ""

print("\n[4/5] uart-reader: UART log capture")
print("-" * 60)
print(uart_text)
print("-" * 60)
print(f"    Total UART bytes: {len(uart_text)}")
print(f"    UART lines: {len(uart_text.splitlines())}")

# ── Step 5: Parse ALERT events and extract dp_ratio ─────────────────────────
print("\n[5/5] Parsing ALERT events...")
events, session_ends = PARSER.parse_log(uart_text)

alert_events = [e for e in events if e.name == "alert"]
print(f"    Total parsed events: {len(events)}")
print(f"    ALERT events: {len(alert_events)}")
print(f"    SESSION_END markers: {len(session_ends)}")

if len(alert_events) == 0:
    print("\n[ESCALATION] Path B produced 0 ALERT events.")
    print("Full UART log is printed above. Halting per Standing Order.")
    sys.exit(1)

# ── Results comparison ───────────────────────────────────────────────────────
dp_ratios    = [e.fields["dp_ratio"] for e in alert_events]
firmware_dp  = dp_ratios[-1]  # last fully-populated window
path_a_dp    = path_a_result["filter_dp_ratio"]
path_a_vib_dp = path_a_result["diagnostics"]["dp_ratio_vib"]

# Firmware uses vibration-only (no CT in Renode sim path).
# Compare against Path A vibration-only dp_ratio_vib.
TOLERANCE    = 0.05
abs_diff_vib = abs(firmware_dp - path_a_vib_dp)
rel_diff_vib = abs_diff_vib / path_a_vib_dp if path_a_vib_dp > 0 else float("inf")
verdict      = "MATCH" if rel_diff_vib <= TOLERANCE else "MISMATCH"

print("\n" + "=" * 70)
print(f"SIMULATION RUN — {time.strftime('%Y-%m-%d %H:%M:%S')}")
print(f"Path: Renode (thorough) — Path B")
print(f"Wall time: {wall_elapsed:.1f}s")
print("=" * 70)
print(f"{'Profile':<22} {'Steps':>6}  {'FW dp_ratio':>12}  {'A vib dp':>10}  {'A fused dp':>12}  {'Status':<8}")
print(f"{PROFILE:<22} {N_STEPS:>6}  {firmware_dp:>12.4f}  {path_a_vib_dp:>10.4f}  {path_a_dp:>12.4f}  {verdict:<8}")
print("=" * 70)
print(f"Pass criteria: relative diff (firmware vs Path A vib-only) <= {TOLERANCE*100:.0f}%")
print(f"Relative diff: {rel_diff_vib*100:.2f}%  |  Absolute diff: {abs_diff_vib:.4f}")
print("=" * 70)
print(f"\nPATH COMPARISON — firmware dp_ratio | Path A vib dp_ratio | match verdict")
print(f"  Firmware  dp_ratio : {firmware_dp:.4f}  (regime={alert_events[-1].fields['regime']}, "
      f"alert={alert_events[-1].fields['alert']})")
if len(dp_ratios) > 1:
    print(f"  All ALERT dp_ratios: {[round(x,4) for x in dp_ratios]}")
print(f"  Path A vib dp_ratio: {path_a_vib_dp:.4f}")
print(f"  Path A fused dp    : {path_a_dp:.4f}  (includes CT fusion — not directly comparable)")
print(f"  VERDICT            : {verdict}")
if verdict == "MISMATCH":
    print("\n[FINDING] Paths diverge beyond tolerance. Reporting to human per Standing Order.")
    print("  The Justice decides whether the Python model or the firmware is wrong.")
    sys.exit(2)
else:
    print("\n[PASS] Path B dp_ratio matches Path A vibration model within tolerance.")
    print("  Stage 1 Renode gate criterion satisfied.")
