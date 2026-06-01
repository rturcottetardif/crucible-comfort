"""
crucible.hw — hardware file reading utilities (infrastructure).

Submodules:
    crucible.hw.kicad   — KiCad .kicad_sch / .kicad_pcb reader and kicad-cli bridge
    crucible.hw.sexpr   — pure-Python S-expression parser (KiCad file format)

No domain knowledge lives here. Project-specific integration (net → signal mapping,
BOM cross-reference against device_context.md) lives in src/kicad_integration.py.

Submodules:
    crucible.hw.review  — Finding dataclass + load/save/merge/bill-stub utilities
"""
