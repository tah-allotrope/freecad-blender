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
- BlenderMCP interactive mode has no config file in this repo; the server is
  registered at Claude Code's *local* scope in `~/.claude.json` (see setup below).

## Commands
```bash
homedesign build  designs/<slug>.json                # compile + plans/elevations/sections + Blender scene + EEVEE preview render
homedesign render designs/<slug>.json --view exterior --view interior [--profile final|cycles] [--skip-existing]
homedesign build  designs/<slug>.json --gltf         # also export a GLB + self-contained web viewer
homedesign pdf    designs/<slug>.json --require-fresh   # architect-brief PDF (A3 landscape); fails on stale renders
homedesign brief  designs/<slug>.json --init [--force]  # scaffold spec/briefs/<slug>.json
homedesign publish designs/<slug>.json [--force]        # hash-verified copy into deliverables/<slug>/
# every subcommand accepts --out <dir> to override the output/ directory
```

## Render engine (do not change without reading this)
- Renders **must** run on **Blender 4.1's legacy EEVEE**.
  `orchestrator._CANDIDATES` already selects 4.1 ahead of 4.5 — leave that
  order alone, and do not "upgrade to the newest Blender".
- EEVEE **Next** (4.2+) miscompiles on this machine's Intel UHD 620 iGPU and
  renders every lit surface blood red (a white `0.92/0.91/0.88` wall comes out
  `(194, 34, 53)`), regardless of view transform or `raytracing`. Pinned by
  `test_blender_candidates_prefer_legacy_eevee_build`; full diagnosis in
  `docs/lessons-learned.md` (2026-08-08).
- There is **no GPU render path at all** here: Cycles enumerates zero
  OPTIX/CUDA/HIP/oneAPI devices, so `--profile cycles` is CPU-only
  (~3 min/view at 1080p). `--profile final` (legacy EEVEE) is ~30 s/view.
- **If renders look miscoloured, check which Blender ran before suspecting the
  design.** Re-render one view with `--profile cycles` to confirm the scene
  data is good. Override discovery with `BLENDER_CMD`.

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

## Blender-side tests
- `tests/test_blender_geometry.py` requires the `bpy` PyPI wheel (roughly
  1 GB). Install it with `python -m pip install -e ".[dev,bpy]"` to enable
  those tests; without `bpy` they skip cleanly (`pytest.importorskip`).
- CI deliberately does **not** install `bpy` (the wheel would dominate the
  workflow), so the full suite must pass with the Blender tests skipped.
  `python -m pytest tests -q -rs` shows the `SKIPPED` lines.

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
| **Blender Addon** | Installed + enabled in prefs | `C:\Users\tukum\Blender\blender-4.1.1-windows-x64\4.1\scripts\addons\blender_mcp_addon.py` |
| **MCP Server** | `uvx blender-mcp` (1.8.0, managed by uv) | local scope in `~/.claude.json` |
| **Enabled-addon state** | `userpref.blend` | `%APPDATA%\Blender Foundation\Blender\4.1\config\` |

The MCP server is registered at Claude Code's **local** scope — private to this
machine, not committed. There is no `.mcp.json` in the repo, and a file at
`.claude/mcp.json` would do nothing: Claude Code reads project MCP config from
`.mcp.json` at the repo root only. Inspect the live entry with `claude mcp get blender`.

### The addon is a local fork — do not replace it from upstream

The installed `blender_mcp_addon.py` reports upstream `bl_info` version `(1, 2)` but
carries two local patches that upstream does not have:

- `register()` auto-starts the socket server, so no one has to click *Connect to
  Claude* in the View3D sidebar.
- It refuses to bind the port under `blender --background`, where queued commands
  would never execute.

Re-downloading the addon from https://github.com/ahujasid/blender-mcp silently reverts
both. If you must update it, re-apply the patches.

### Workflow

1. **Start Blender** — open the Blender 4.1 GUI; the addon auto-starts the MCP socket
   server on port 9876. Background/headless Blender will **not** serve MCP by design.
2. **Use Claude Code** — `claude` in this project directory loads the Blender MCP tools
3. **Interact** — ask Claude to create/modify objects, apply materials, set up lighting, render

Verify the whole chain rather than trusting the server's "connected" status — the stdio
server starts fine whether or not Blender is reachable:

```bash
# port up?
powershell -c "Get-NetTCPConnection -LocalPort 9876"
# real proof: call get_scene_info via MCP and expect a scene payload
```

### Re-enabling the addon (one-time, e.g. after a Blender reinstall)

Headless, no GUI interaction needed:

```bash
"C:/Users/tukum/Blender/blender-4.1.1-windows-x64/blender.exe" --background \
  --python-expr "import bpy; bpy.ops.preferences.addon_enable(module='blender_mcp_addon'); bpy.ops.wm.save_userpref()"
```

Expect `BlenderMCP addon registered` plus `Preferences saved`. (The "cannot start server
in background mode" line on that run is the guard above doing its job, not an error.)
Fallback: Blender → Edit → Preferences → Add-ons → search "Blender MCP" → tick the box.

### Environment Variables

- `BLENDER_HOST` — default `localhost`
- `BLENDER_PORT` — default `9876`
- `DISABLE_TELEMETRY=true` — set in config to opt out of anonymous usage data
