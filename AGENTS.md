# AGENTS.md

## Scope
- This repo generates a 4 m x 25 m five-storey tube-house package from `spec/floorplan-spec.json` using FreeCAD Python scripts.
- Search the repo before assuming file locations beyond the high-level entry points below.

## Start Here
- Read `activeContext.md` for the current plan, blockers, and session results.
- Read `docs/lessons-learned.md` before changing FreeCAD automation.
- Use `plans/home-design-to-architect-workflow.md` for the end-to-end user workflow.

## Key Entry Points
- `src/homedesign/` — Python package for the full spec-to-render pipeline (compiler, plan2d, Blender scene build, PDF export). Run via `python -m homedesign`.
- `src/homedesign/blender/` — Blender Python API scripts (build_scene, materials, joinery, roof, etc.), executed headlessly via `blender --background --python ...`.
- `spec/` — JSON source-of-truth specs for floor plans and material configs.
- `output/png/` — Generated render gallery.
- `.claude/mcp.json` — Claude Code MCP config for BlenderMCP interactive mode (see setup below).
- `run.sh` executes the FreeCAD pipeline (legacy, being phased out).

## Working Rules
- Prefer minimal, spec-driven changes; do not redesign floors unless the task explicitly asks for it.
- Keep the core zone and rear light well aligned across floors unless the user explicitly changes that rule.
- Put non-FreeCAD logic in pure helpers so it can be covered by `unittest`.
- Treat generated files in `output/` as reproducible artifacts; do not hand-edit them.

## Verification
- For pure Python changes, run `python -m unittest discover -s tests -v`.
- For script edits, also run `python -m py_compile src/*.py` when possible.
- If FreeCAD is unavailable locally, report that runtime limitation clearly instead of guessing.

## Progressive Docs
- Workflow/status details: `plans/PROGRESS.md`, `plans/tubehouse-freecad-mcp-workflow.md`
- Runtime/setup details: `freecad-mcp-guide.md`, `docs/HOW_TO_RUN.txt`

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
