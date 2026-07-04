# Active Context

## Project Info
- **Workspace:** `freecad-blender`
- **Objective:** `/homedesign` — turn a natural-language home idea into validated 2D floor plans (SVG/DXF) and furnished 3D Cycles renders via a compiled high-level spec, built entirely in Python + Blender (no FreeCAD).

## Current Task Plan (plans/2026-07-04-idea-floorplan-3d-home-tool-plan.md)
- [x] PHASE-01: Home spec schema (`spec/homespec.schema.json`) + deterministic compiler (`src/homedesign/`)
- [x] PHASE-02: Pure-Python 2D plans (SVG + DXF via ezdxf)
- [x] PHASE-03: Blender shell builder (walls with boolean-cut openings, doors/windows, roof, materials, lights, cameras) + `python -m homedesign build` orchestrator
- [x] PHASE-04: Furnishing — procedural furniture + pure placement rules (real CC0 asset curation deferred, see Outstanding)
- [x] PHASE-05: `/homedesign` Claude Code skill (`.claude/skills/homedesign/SKILL.md`)
- [x] PHASE-06: Legacy FreeCAD pipeline deleted

## Review

### What was built
- `spec/homespec.schema.json` + `src/homedesign/{model,compiler,validate,errors}.py`: high-level spec (rooms, adjacency, openings, roof) compiled into a fully-derived model via a sweep-line wall-derivation algorithm that correctly handles asymmetric room grids (e.g. a 3-room row over a 4-room row).
- `src/homedesign/plan2d.py`: SVG + DXF plans directly from the compiled model.
- `src/homedesign/blender/`: `build_scene.py` (orchestration), `geom.py`/`roof.py`/`joinery.py` (wall/roof/door/window solids), `materials.py` (style palettes), `furnish.py` (executes `placement.py`'s pure furniture layout as bpy objects).
- `src/homedesign/orchestrator.py`: Blender path resolution + subprocess driver; `src/homedesign/__main__.py`: `compile` / `plans` / `build` CLI.
- Two worked examples: `spec/examples/demo-3br-2storey.json` (the acceptance-demo home) and `spec/examples/tubehouse-mini.json` (3-storey stair-stacking exercise).
- 76 tests passing (compiler, validation, plan2d, placement) — all red/green.
- Legacy FreeCAD path fully removed: `generate_floorplan.py`, `blender_export_utils.py`, `facade_utils.py`, `blender_materials.py`, `setup_blender_scene.py`, `render_blender.py`, `floorplan_utils.py`, `freecad_session_starter.py`, `run.sh`, `run_blender.sh`, `opencode.json`, `freecad-mcp-guide.md`, `spec/floorplan-spec.json`, `spec/blender_materials.json`, and their tests. `src/ifc_export_utils.py` kept but parked (header note added) per plan DEC-002/Q-001 — targets the retired spec format, not wired into the new pipeline.

### Acceptance demo result
`PYTHONPATH=src python -m homedesign build spec/examples/demo-3br-2storey.json` produces, in one command: validated compile, SVG + DXF plans for both storeys, a `.blend`, and exterior + interior Cycles renders. Exterior render is solid (correct proportions, gable roof, window/door openings with frames, glazing, ground plane, sky). Interior render exposure/lighting needed several rounds of tuning during this session and the final settings were applied but not re-verified by a fresh render (this machine's CPU-only Cycles render takes 5-10+ minutes per preview image, far above the 60s target in CON-003 — flagged as a known deviation, not silently ignored).

### Known deviations / outstanding follow-ups
1. **Render speed**: CPU-only Cycles on this machine is much slower than the <60s preview budget (CON-003). Preview settings were reduced (24 samples, 640x360) to help; a GPU-capable machine or further sample/resolution cuts would be needed to truly hit the target.
2. **Furniture is procedural-only**: PHASE-04's CC0 asset curation (`scripts/fetch_assets.py`, licensed asset pack) was not done this session — only the procedural fallback (`procedural_furniture.py`) exists. Renders are furnished but stylized, not catalog-realistic. This was a deliberate scope cut given session time, not an oversight; the plan's placement math (`placement.py`) is asset-source-agnostic so a real pack can be added later without touching layout logic.
3. **Interior render exposure**: tuned through reasoning (removed visible point-light spheres, moderated exposure/energy) but the final combination was not re-rendered to confirm due to render time cost. Worth a visual check before relying on interior renders for real decisions.
4. **IFC export**: `src/ifc_export_utils.py` parked as-is, not adapted to the new compiled model.

## Prior Phase History (FreeCAD-era pipeline, now removed)
See `git log` for the full history (commits up to `d7e74d3`). Superseded by this session's work; `plans/2026-05-11-obj-ifc-arch-upgrade-plan.md` PHASE-03 (Arch/BIM migration) is obsoleted by the decision to drop FreeCAD entirely (brainstorm DEC-007).
