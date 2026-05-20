# -*- coding: ascii -*-
# Renode Python peripheral -- simulation-mode USBD (USB device) no-op stub.
# Python 2 (IronPython) compatible: no f-strings, no non-ASCII.
#
# Registered at sysbus 0x40027000 (size 0x1000), replacing the SVD-backed USBD.
#
# Purpose: The nRF52840 TinyUSB stack in the Arduino core boots and launches a
# usb_device_task FreeRTOS thread even when CONFIG_CRUCIBLE_RENODE_SIM is set.
# In Renode 1.16.1 the nrf52840.repl does not include a USBD peripheral model.
# The SVD-based fallback returns 0 for reads but the USBD IRQ (nRF52840 IRQ 39)
# fires spuriously, corrupting the firmware stack and halting simulation.
#
# This stub implements the minimum nRF52840 USBD register behavior needed to
# keep TinyUSB quiescent during Renode simulation:
#
#   EVENTCAUSE (0x400):  bit 0 (ISOOUTCRC) = 0; all others = 0
#                        On write: clear the event.
#   EVENTS_USBEVENT (0x138): always 0 (no USB events)
#   EVENTS_EP0SETUP (0x114): always 0
#   EVENTS_EP0DATADONE (0x110): always 0
#   ENABLE (0x500): read 0 (USB disabled in sim)
#   All other reads: return 0
#   All writes: silently accepted
#
# With no USB host detected and no events firing, the TinyUSB task spins
# harmlessly in its host-wait loop without crashing.
#
# nRF52840 USBD base: 0x40027000. Registered via REPL3 in RenoneBridge.
# See crucible/sim/renode.py _configure_renode for registration sequence.

if request.IsInit:
    self.NoisyLog("sim_usbd_stub: initialized (USB no-op for Renode sim)")

elif request.IsRead:
    # Return 0 for all registers (USB disabled, no events, no host).
    request.Value = 0

elif request.IsWrite:
    # Accept all writes silently -- TinyUSB will write ENABLE, INTENSET, etc.
    pass
