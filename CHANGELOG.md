# Changelog

All significant changes to the Crucible framework are recorded here. Format: [version] — [date] — [summary].

Changes are classified as:
- **Governance** — changes to Articles, Amendments, or the Bill/Hearing/Ratification process
- **Agent** — changes to slash commands or agent definitions
- **Docs** — new or updated documentation
- **Example** — new or updated device examples
- **Fix** — corrections to incorrect content

---

## [0.1.0] — 2026-04-10 — Initial public release

### Governance
- CONSTITUTION.md: Article I (Signal First) and Article II (Human in the Loop) defined
- Four-branch governance model documented: Legislature, Judiciary, Ratification, Bureaucracy
- Bill format, Judicial hearing procedure, Amendment ratification process defined
- hw-advisor role defined: reads existing circuit/BOM, suggests from test results, does not redesign

### Agent
- `/session` — 5-stage pipeline orchestrator (Stage 0 HIL-first)
- `/hear` — 7-step judicial hearing with attorney agents
- `/toolchain` — hardware, pin, library, repository gatekeeper and RAG setter
- `/hw-advisor` — design suggestion agent grounded in test results (stub — full implementation pending)
- `/plot-evidence` — signal and simulation evidence collection
- `/plot-profile` — single-profile signal diagnostic plot

### Docs
- README.md — framework overview, the five failure modes, pipeline map
- ONBOARDING.md — 30-minute start guide, reading order, first session checklist
- CONTRIBUTING.md — Bill-based contribution process, device example format
- KNOWN_LIMITATIONS.md — honest disclosure of what is not validated in 0.1.0
- SECURITY.md — BLE open posture, firmware signing roadmap, field data handling
- docs/governance/adoption_guide.md — how to fork and adapt for any device domain
- docs/governance/bill_template.md — complete Bill format with guidance notes
- docs/testing/hil_testing_guide.md — HIL-first principle, four-smoke-test sequence, failure modes

### Example
- examples/gait_wearable/ — pointer to GaitSense reference implementation (nRF52840 + LSM6DS3TR-C)
- examples/smart_home_sensor/ — skeleton for PIR occupancy sensor (in progress)

---

## [0.2.0] — 2026-05-19 — KiCad MCP server + Python module

### Agent
- `hw-advisor` — updated to call KiCad MCP tools when a schematic is present;
  `read_bom` is now authoritative over Markdown BOM (overrides if both present)

### Infrastructure
- `crucible/hw/sexpr.py` — pure-Python S-expression parser for KiCad file format
  (tokenizer, recursive descent parser, serializer, navigation helpers)
- `crucible/hw/kicad.py` — public API: `read_bom`, `read_netlist`, `read_power_rails`,
  `find_component`, `list_project_files`, `detect_kicad_cli`, plus kicad-cli bridge
  for `export_svg`, `export_pdf`, `run_erc`, `export_pcb_image`, `run_drc`
- `src/kicad_integration.py` — ComfortSense net→signal mapping; `check_signal_inventory`
  and `bom_vs_device_context` for hw-advisor use
- `.claude/mcp/kicad/server.py` — MCP stdio server exposing 10 tools (6 read-only,
  4 kicad-cli-dependent); registered in `.mcp.json`
- `hardware/` — placeholder directory for `.kicad_sch` and `.kicad_pcb` files

### Docs
- `KNOWN_LIMITATIONS.md` — updated KiCad limitation; kicad-cli export needs KiCad 7.0+
- `.claude/mcp/kicad/README.md` — tool table, registration, upgrade instructions

---

## Roadmap (not yet released)

- [ ] CI server integration guide
- [ ] Generic field data replay pipeline (simulation feedback loop tooling)
- [x] KiCad schematic parser for hw-advisor (0.2.0)
- [ ] Smart home sensor complete example
- [ ] docs/simulation/simulation_guide.md
- [ ] docs/firmware/integration_guide.md
- [ ] docs/field-test/field_test_protocol.md
- [ ] docs/integration/smart_home_integration.md
- [ ] Automated stage gate CI check templates
- [ ] Multi-team governance exercise documentation
