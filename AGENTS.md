# AGENTS.md

## Scope
- This repo is a pure-Python + headless-Blender home-design tool: a JSON
  spec is compiled into a geometric model, then turned into 2D plans,
  elevations and sections (SVG/DXF), a Blender scene, renders, an interactive
  GLB web viewer, and an architect-brief PDF.
- The old FreeCAD pipeline is retired. Its launcher script and legacy spec
  format are gone (archived under `docs/archive/`) — do not look for them.
- Search the repo before assuming file locations beyond the entry points
  below.

## Start Here
- Read `activeContext.md` for the current plan, blockers, and session
  results.
- Read `docs/lessons-learned.md` before changing the Blender automation.
- Read `.claude/skills/homedesign/SKILL.md` for the end-to-end workflow.

## Key Entry Points
- `src/homedesign/` — Python package for the full spec-to-render pipeline
  (compiler, checks, plan2d, elevation, camera_fit, Blender scene build, PDF
  export). Run via `homedesign` (console script) or `python -m homedesign`.
- `src/homedesign/blender/` — Blender Python API scripts (build_scene,
  materials, joinery, railings, roof, procedural_furniture), executed
  headlessly via `blender --background --python ...`. Never import `bpy`
  outside this directory; these scripts run as top-level Blender scripts, so
  use absolute imports only.
- `designs/` — user-authored home specs (`designs/<slug>.json`).
- `spec/examples/` — small reproducible fixture specs; `spec/homespec.schema.json`
  is the spec schema.
- `output/png/` — generated render gallery; `output/svg|dxf|pdf|blend|gltf|viewer`
  hold the other artifacts.
- `.claude/skills/homedesign/SKILL.md` — the homedesign skill (mirrored to
  `.agents/skills/homedesign/SKILL.md` by `scripts/sync_skill.py`; keep in
  sync via `python scripts/sync_skill.py`).
- `.claude/mcp.json` — Claude Code MCP config for BlenderMCP interactive
  mode (see setup below).

## Commands
```bash
homedesign build  designs/<slug>.json                # compile + plans/elevations/sections + Blender scene + EEVEE preview render
homedesign render designs/<slug>.json --view exterior --view interior [--profile final|cycles] [--skip-existing]
homedesign build  designs/<slug>.json --gltf         # also export a GLB + self-contained web viewer
homedesign pdf    designs/<slug>.json --require-fresh   # architect-brief PDF (A3 landscape); fails on stale renders
```

## Working Rules
- Prefer minimal, spec-driven changes; do not redesign rooms unless the
  task explicitly asks for it.
- Keep the core zone and rear light well aligned across floors unless the
  user explicitly changes that rule.
- Keep geometry math in pure helpers (`src/homedesign/`) so it is
  unit-testable without Blender; `src/homedesign/blender/` contains only
  the bpy-facing layer.
- Treat generated files in `output/` as reproducible artifacts; do not
  hand-edit them.
- Millimetres everywhere on the pure side, metres everywhere on the Blender
  side; the `/ 1000` conversion happens exactly once at the boundary.

## Verification
- Run `python -m pytest tests -q` and `ruff check src tests` before
  committing; CI runs both plus `python scripts/sync_skill.py --check`.
- For Blender-side changes, smoke-test with
  `homedesign build spec/examples/tubehouse-mini.json`
  (EEVEE preview).
- If Blender is unavailable locally, report that runtime limitation clearly
  instead of guessing.

## Progressive Docs
- Workflow/status details: `activeContext.md`, `plans/`
- Retired FreeCAD-era docs: `docs/archive/` (PROGRESS.md, HOW_TO_RUN.txt,
  plan-floor-1.md, freecad-lessons-learned.md,
  home-design-to-architect-workflow.md)

## Blender MCP Setup

[BlenderMCP](https://github.com/ahujasid/blender-mcp) connects Claude AI to Blender via the Model Context Protocol, enabling interactive 3D modelling and scene manipulation through natural language.

### Components

| Component | Status | Location |
|-----------|--------|----------|
| **Blender Addon** | ✅ Installed | `C:\Users\tukum\Blender\blender-4.1.1-windows-x64\4.1\scripts\addons\blender_mcp_addon.py` |
| **MCP Server** | ✅ Available | `uvx blender-mcp` (managed by uv) |
| **Claude Code Config** | ✅ Active | `.claude/mcp.json` + global `~/.claude.json` |

### Workflow

1. **Start Blender** — open Blender GUI, the addon auto-starts the MCP socket server (port 9876)
2. **Use Claude Code** — `claude` in this project directory auto-loads the Blender MCP tools
3. **Interact** — ask Claude to create/modify objects, apply materials, set up lighting, render

### Manual Addon Enable (one-time)

If the addon isn't showing in Blender:
1. Open Blender → Edit → Preferences → Add-ons
2. Search "Blender MCP" or locate `blender_mcp_addon.py`
3. Check the box to enable

### Environment Variables

- `BLENDER_HOST` — default `localhost`
- `BLENDER_PORT` — default `9876`
- `DISABLE_TELEMETRY=true` — set in config to opt out of anonymous usage data
