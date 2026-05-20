# Known Limitations

This document is honest about what Crucible does not yet do, what has not been validated, and where the framework may not apply. It is updated with each release.

**Current version:** 0.1.0 (initial public release, 2026-04-10)

---

## Framework Limitations

### Single-engineer reference implementation only

The GaitSense reference implementation was developed by a single engineer with a single AI assistant (Claude Code). The multi-team governance features — >60% supermajority Amendment ratification, cross-team Bill debate — have not been exercised in a real multi-team context. These rules are derived from how they *should* work; they have not been stress-tested by teams with genuinely conflicting priorities.

**Impact:** Teams adopting Crucible should expect to adapt the governance rules for their team dynamics. The framework will tell you *that* you need to decide; it cannot tell you *how* your team makes that decision.

### No automated gate enforcement

Stage gate passage currently requires a human to explicitly confirm exit criteria are met. There is no automated CI check that blocks a branch merge if Stage 1 simulation has not passed. This is intentional (Article II — human in the loop), but it means the gates are only as strong as the discipline of the team using them.

A CI integration that enforces "simulation must pass before firmware branch merges" is on the roadmap. See `docs/integration/ci_server_guide.md` (planned, not yet written).

### Agent workflow requires Claude Code

The slash commands (`/session`, `/hear`, `/toolchain`, `/hw-advisor`) are written for Claude Code (Anthropic's CLI/IDE agent). They will not run in other AI environments without adaptation. The governance framework itself is tool-agnostic — the agent commands are one implementation of it.

---

## Simulation Limitations

### Physics models are device-specific and not provided

Crucible provides the governance structure for simulation; it does not provide physics models. You must build your own simulation layer. The GaitSense reference provides a walker biomechanics model (`simulator/walker_model.py`) as an example, but a thermostat simulator, a glucose optical model, or a soil moisture model are entirely your responsibility.

**What Crucible does provide:** the rules for how simulation evidence is collected, reviewed, and used to make decisions. What you simulate is up to you.

### Field data replay requires format standardisation

The simulation feedback loop (field measurement data → simulation) is described architecturally but not yet implemented as a generic pipeline. Each device domain will need its own data ingestion path. The gait_device reference implementation accepts Renode UART log format; a general-purpose replay tool does not yet exist.

---

## Toolchain Limitations

### Toolchain janitor covers software toolchains only

`/toolchain` manages build tools, libraries, firmware environments, and repository registry. It does not yet manage:
- Bench instrument calibration (oscilloscope calibration dates, PPK2 firmware version)
- PCB fab versions (which revision of a board is currently on the bench)
- Mechanical fixtures (enclosure revision, mounting strap specification)

These are on the roadmap. For now, document them manually in your project's `toolchain_config.md`.

### UF2 sparse builder is nRF52840-specific

`scripts/make_sparse_uf2.py` in the GaitSense reference is specific to Seeed XIAO nRF52840 Sense with SoftDevice S140 v7.3.0. The sparse UF2 concept generalises to any device with a protected bootloader region, but the script is not yet generic.

---

## hw-advisor Limitations

### KiCad schematic parsing available; kicad-cli export requires upgrade

hw-advisor can now parse KiCad `.kicad_sch` files directly via the `kicad` MCP
server (`.claude/mcp/kicad/`). BOM, netlist, power rail, and component lookup
work without any external tools — place your `.kicad_sch` file in `hardware/`.

Export (SVG/PDF), ERC, PCB image, and DRC require kicad-cli (KiCad 7.0+). The
macOS KiCad 6.x does not include kicad-cli. Upgrade: `brew install --cask kicad`.

Altium and Eagle formats are not supported.

### Suggestions are grounded in test results — not datasheet analysis

hw-advisor provides suggestions based on correlating your test failures with your component choices. It is not a component selection tool and does not perform datasheet cross-referencing, thermal analysis, or EMC prediction. It identifies patterns like "enclosure stiffness below spec → signal attenuated below threshold" when test data shows that pattern — it does not predict failures before they manifest.

### No multi-device interaction modelling

If your device interacts with other devices on a network (Zigbee mesh, CAN bus, I²C multi-drop), hw-advisor does not model those interactions. Single-device signal integrity only.

---

## Field Test Limitations

### No standardised field test data format

There is no universal schema for field test output. The gait_device reference uses a specific BLE NUS line format; a different device will use a different format. Generic field test data collection, annotation, and analysis tools are not yet provided.

### No regulatory compliance guidance

Crucible does not address regulatory requirements (FCC, CE, FDA 510(k), EU MDR, IEC 60601). The governance framework is consistent with good regulatory practice (traceability, evidence-based decisions, change control) but has not been formally mapped to any regulatory standard. Do not use Crucible as a substitute for regulatory compliance guidance for medical or safety-critical devices.

---

## What the 0.1.0 Release Does Not Include

| Planned feature | Status |
|----------------|--------|
| CI server integration guide | Not written |
| Generic field data replay pipeline | Not written |
| KiCad schematic parser for hw-advisor | IMPLEMENTED (0.2.0) — see `.claude/mcp/kicad/` |
| Multi-team governance exercise results | Not validated |
| Second device example (smart home sensor) | Skeleton only |
| Bench instrument calibration tracking | Not implemented |
| PCB revision tracking | Not implemented |
| Automated stage gate CI checks | Not implemented |

These will be addressed in future releases based on feedback from early adopters.
