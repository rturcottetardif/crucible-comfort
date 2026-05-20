# KiCad MCP Server

Provides read access to KiCad schematic and PCB files for Claude Code and Crucible agents.

## What it provides

| Tool | CLI required | When to use |
|------|-------------|-------------|
| `kicad_cli_status` | No | First call — reports which tools are available |
| `list_kicad_files` | No | Discover .kicad_sch / .kicad_pcb in the project |
| `read_bom` | No | Extract BOM from a schematic (authoritative over Markdown) |
| `read_netlist` | No | Get net connectivity for signal path tracing |
| `read_power_rails` | No | Get power rails and what's on them |
| `find_component` | No | Look up one component by ref (e.g. U1) |
| `export_schematic` | Yes (7.0+) | Export schematic as SVG or PDF for viewing |
| `run_erc` | Yes (7.0+) | Run Electrical Rules Check |
| `export_pcb_image` | Yes (7.0+) | Export PCB copper/silkscreen as SVG |
| `run_drc` | Yes (7.0+) | Run Design Rules Check |

The six read-only tools work immediately with no external dependencies.
Export and validation tools require kicad-cli (KiCad 7.0+).

## Registration

Add to `.mcp.json` at the project root (already done — see `.mcp.json`):

```json
{
  "mcpServers": {
    "kicad": {
      "command": "python3",
      "args": [".claude/mcp/kicad/server.py"]
    }
  }
}
```

## kicad-cli upgrade

The installed macOS KiCad 6.x does not include kicad-cli (introduced in 7.0).

```
brew install --cask kicad   # installs KiCad 10.0.2 with kicad-cli
```

After upgrading, `kicad_cli_status` will report all 10 tools available.

## How it fits Crucible

This server is **read-only evidence infrastructure**. It does not make decisions.

- `hw-advisor` calls `read_bom` and `read_netlist` to ground hardware suggestions
  in verified schematic data (stronger Article I evidence than a Markdown BOM table).
- `bill-drafter` can call `read_bom` to confirm component refs when drafting a Bill.
- Export tools let engineers view schematics and PCBs without opening KiCad GUI.

**What this server cannot do (by design — Article II):**
- Modify schematics or PCB files
- Flash firmware
- Make any decision that changes the physical or algorithmic direction of the project

Schematic edits require a Bill. The human uses the KiCad GUI; this server reads the result.

## Schematic files

Place `.kicad_sch` and `.kicad_pcb` files in the `hardware/` directory:

```
hardware/
  comfortsense.kicad_sch
  comfortsense.kicad_pcb
  comfortsense.kicad_pro
```

Update `docs/device_context.md` → Circuit Notes → Schematic revision field with
the file path and the git commit hash when the schematic is first committed.
