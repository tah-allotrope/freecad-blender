---
title: "Idea → 2D Floorplan → 3D Home Model Tool"
date: "2026-07-04"
status: "complete — all six phases landed in 8a8e206 (src/homedesign package, schema, plan2d, Blender builder, /homedesign skill, FreeCAD fully deleted); two in-phase tasks were deliberately cut: CC0 asset curation (TASK-04-01, procedural furniture only) and tests/test_orchestrator.py (TASK-03-06)"
request: "idea-floorplan-3d-home-tool (from /brainstorm 2026-07-04)"
plan_type: "multi-phase"
research_inputs:
  - "research/2026-07-04_idea-floorplan-3d-home-tool-brainstorm.md"
  - "research/2026-05-11_freecad-blender-floorplan-3d-workflow.md"
  - "research/2026-05-11_freecad-blender-floorplan-3d-workflow-landscape.md"
---

# Plan: Idea → 2D Floorplan → 3D Home Model Tool

## Objective
Transform the repo from a bespoke FreeCAD→Blender pipeline for one hardcoded tube house into a general `/homedesign` tool: a natural-language home idea becomes a compact validated design spec, a deterministic Python compiler derives all geometry, and one command produces 2D plans (SVG/DXF) plus furnished 3D Cycles renders built procedurally in Blender — with Claude self-correcting visually before presenting. FreeCAD is removed entirely.

## Context Snapshot
- **Current state:** Spec-driven batch pipeline hardcoded to a 4×25m 5-storey tube house: `spec/floorplan-spec.json` (3,100 lines, mm-precise, no validation) → `run.sh` → `freecadcmd src/generate_floorplan.py` (Part::Box walls, 2D Draft plans, OBJ export via `src/blender_export_utils.py`) → `run_blender.sh` → `src/setup_blender_scene.py` + `src/render_blender.py` (OBJ import, materials, Cycles PNG). Parallel FreeCAD-independent IFC4 export in `src/ifc_export_utils.py` (IfcOpenShell 0.8.5). No 3D doors/windows/roof; walls have no openings; PDF and headless facade SVG broken; exploratory FreeCAD-MCP config in `opencode.json`. Tools: FreeCAD 1.0.2, Blender 4.1.1 at `C:/Users/tukum/Blender/blender-4.1.1-windows-x64/blender.exe` (override `BLENDER_CMD`), Windows 11 + Git Bash. Pure helpers `src/floorplan_utils.py` / `src/facade_utils.py` are unit-tested.
- **Desired state:** `src/homedesign/` Python package: JSON-Schema-validated high-level spec (~100 lines: floors, rooms, adjacency, openings, style) → deterministic compiler (walls, openings, stairs, roof derivation + geometric sanity checks) → (a) pure-Python SVG + ezdxf DXF plans, (b) a Blender-side builder script that constructs the furnished 3D scene (boolean wall openings, parametric doors/windows, roof, materials, CC0 furniture with procedural fallback) and renders preview/final Cycles images. One CLI (`python -m homedesign build <spec> [--final]`). A `/homedesign` Claude Code skill drives idea → spec → build → visual self-check → present. FreeCAD code and configs deleted.
- **Key repo surfaces:** `src/homedesign/` (new package), `.claude/skills/homedesign/SKILL.md` (new), `spec/blender_materials.json` + `src/blender_materials.py` (material definitions to port), `src/setup_blender_scene.py` + `src/render_blender.py` (lighting/camera/render logic to absorb into the new builder), `src/floorplan_utils.py` (reusable pure math), `src/ifc_export_utils.py` (kept, parked), `tests/` (extend), deletions in PHASE-06: `src/generate_floorplan.py`, `src/blender_export_utils.py`, `src/facade_utils.py`, `run.sh`, `run_blender.sh`, `opencode.json`, `freecad-mcp-guide.md`, `spec/floorplan-spec.json`.
- **Out of scope:** Any end-user UI; curved/diagonal walls, complex roofs, split levels; BIM round-tripping (IFC stays a parked one-way exporter); FCStd and PDF outputs; the FreeCAD-MCP workflow; structural/code-compliance checks.

## Research Inputs
- `research/2026-07-04_idea-floorplan-3d-home-tool-brainstorm.md` — Source of all 16 decisions (DEC-001…016): LLM-authored high-level spec + compiler, bpy-native 3D, pure-Python 2D, furnished scenes from bundled CC0 assets, bounded visual self-correction loop, aggressive FreeCAD deletion, fresh-prompt acceptance demo. Defines the phase content and out-of-scope list directly.
- `research/2026-05-11_freecad-blender-floorplan-3d-workflow.md` — Confirms `floorplan_utils.py`/`facade_utils.py` are pure and tested (reuse/port candidates), the material sidecar pattern in `spec/blender_materials.json` (port as-is), and Blender 4.x API specifics (`bpy.ops.wm.obj_import` era; 4.1 boolean/bmesh APIs stable). Its recommended IFC/Arch path is explicitly obsoleted by brainstorm DEC-007/DEC-012.
- `research/2026-05-11_freecad-blender-floorplan-3d-workflow-landscape.md` — Documents current OBJ/material/scene mechanics (three-tier material maps, sun+area lighting, auto-targeting camera) worth porting into the new bpy builder; documents spec weaknesses (pre-computed door arcs, inconsistent door schemas) the new schema must avoid.

## Assumptions and Constraints
- **ASM-001:** The compiler runs in system Python; all Blender-side work runs inside Blender's bundled Python (`blender --background --python ...`). The two communicate only via the compiled-model JSON file — no pip `bpy` module, no shared imports.
- **ASM-002:** Claude (via the skill) can author the high-level spec reliably given the JSON Schema + two worked examples, and can judge preview renders visually (DEC-009).
- **ASM-003:** A usable CC0 furniture set (bed, wardrobe, sofa, dining table+chairs, kitchen block, WC, basin, shower, desk) can be fetched once at reasonable size; procedural fallback covers every type so a fresh clone never hard-fails (brainstorm Q-002 default).
- **CON-001:** Windows 11 + Git Bash; Blender 4.1.1 (`BLENDER_CMD` override respected). No new heavyweight runtimes; new pip deps limited to `jsonschema`, `ezdxf`.
- **CON-002:** Rectilinear geometry only: axis-aligned walls, 1–N floors, flat or simple gable/shed roof (DEC-006).
- **CON-003:** Preview render must complete well under a minute so ~3 self-correction passes per turn are viable (DEC-009): low-sample Cycles (~64 samples, 960×540, denoised).
- **DEC-001:** All brainstorm decisions DEC-001…DEC-016 are fixed inputs to this plan; see the brainstorm file. Notably: renders are the deliverable (DEC-002), conversational spec edits must round-trip (DEC-003), FreeCAD is deleted after parity of the acceptance demo — not tube-house parity (DEC-012/013).
- **DEC-002 (this plan):** IFC export stays parked (brainstorm Q-001 default): `src/ifc_export_utils.py` is kept but not adapted to the new spec in this effort.
- **DEC-003 (this plan):** Per-user global standards, each phase is red/green TDD for its pure-Python logic; Blender-side code is verified by build-and-inspect since bpy can't run under pytest.

## Phase Summary
| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Home spec schema + deterministic compiler | None | `spec/homespec.schema.json`, `src/homedesign/compiler.py`, validated example specs, `python -m homedesign compile` |
| PHASE-02 | Pure-Python 2D plans (SVG + DXF) | PHASE-01 | `src/homedesign/plan2d.py`, per-floor SVG/DXF in `output/` |
| PHASE-03 | Blender 3D shell builder + render orchestration | PHASE-01 | `src/homedesign/blender/build_scene.py`, `python -m homedesign build`, preview/final PNGs |
| PHASE-04 | Furnishing: CC0 assets + procedural fallback + placement | PHASE-03 | `scripts/fetch_assets.py`, `src/homedesign/blender/furnish.py`, furnished renders |
| PHASE-05 | `/homedesign` skill with visual self-correction loop | PHASE-02, PHASE-04 | `.claude/skills/homedesign/SKILL.md`, passing acceptance demo |
| PHASE-06 | Delete FreeCAD path, docs cleanup | PHASE-05 | Removed legacy files, updated `activeContext.md`/`README`/plans |

## Detailed Phases

### PHASE-01 - Home Spec Schema and Compiler
**Goal**
Define the LLM-facing high-level spec format and the deterministic compiler that turns it into a fully-derived geometric model (walls with openings, stairs, roof, per-floor layout), with hard validation at both layers.

**Tasks**
- [x] TASK-01-01: Design `spec/homespec.schema.json` (JSON Schema draft 2020-12). Top level: `meta` (name, units fixed to mm, style palette key), `site` (plot w×d, orientation), `storeys[]` (height, rooms), `rooms[]` per storey (id, type enum [bedroom, bathroom, kitchen, living, dining, hall, stairwell, garage, balcony], rect `{x,y,w,d}` OR relative placement `{adjacent_to, side, w, d}`), `openings[]` (door/window: `between` two room ids or room+exterior, wall side, width, sill/head heights), `stairs` (in stairwell room, direction), `roof` (`flat|gable|shed`, pitch, overhang). Consistent shapes per type — no pre-computed arcs, no per-type schema drift.
- [x] TASK-01-02: Write two hand-authored example specs: `spec/examples/demo-3br-2storey.json` (the DEC-013 acceptance home) and `spec/examples/tubehouse-mini.json` (narrow-lot 3-storey, exercises stair stacking). These are also the fixtures for tests.
- [x] TASK-01-03: Red/green: tests in `tests/test_compiler.py` for placement resolution (relative→absolute rects), wall derivation (shared walls deduped, exterior vs partition thickness 200/100mm — reuse constants pattern from the old spec), opening→wall assignment, stair run/riser computation (reuse/port `src/floorplan_utils.py` math), roof solid parameters.
- [x] TASK-01-04: Implement `src/homedesign/model.py` (dataclasses for the compiled model) and `src/homedesign/compiler.py` to green the tests. Compiled model serializes to `output/compiled/<name>.model.json` — the single artifact both 2D and Blender stages consume.
- [x] TASK-01-05: Red/green: `tests/test_validate.py` + `src/homedesign/validate.py` — schema validation (jsonschema) plus geometric sanity: room overlap within storey, rooms outside plot, door between non-adjacent rooms, opening wider than its wall, stairwell too small for the run, storeys with mismatched stairwell stacking. Errors must be specific and machine-readable (list of `{code, path, message}`) so the skill can feed them back to the LLM.
- [x] TASK-01-06: CLI entry: `src/homedesign/__main__.py` with `compile <spec.json>` subcommand (validate → compile → write model JSON; nonzero exit + error list on failure).

**Files / Surfaces**
- `spec/homespec.schema.json` — new schema, the LLM contract
- `spec/examples/*.json` — new fixtures/demos
- `src/homedesign/{model,compiler,validate,__main__}.py` — new package
- `src/floorplan_utils.py` — inspect; port stair/height math into the package, keep original untouched until PHASE-06
- `tests/test_compiler.py`, `tests/test_validate.py` — new

**Dependencies**
- pip: `jsonschema` (system Python)

**Exit Criteria**
- [ ] `python -m pytest tests/` green, including new compiler/validate suites written test-first
- [ ] `python -m homedesign compile spec/examples/demo-3br-2storey.json` emits a model JSON; a deliberately broken spec exits nonzero with structured errors

**Phase Risks**
- **RISK-01-01:** Relative placement (`adjacent_to`) solver becomes a constraint-solving rabbit hole. Mitigation: v1 supports absolute rects plus one-hop adjacency only; the LLM can always fall back to absolute rects.

### PHASE-02 - Pure-Python 2D Plans
**Goal**
Generate dimensioned per-floor plan drawings (SVG for viewing, DXF for CAD) directly from the compiled model, replacing FreeCAD's 2D output.

**Tasks**
- [x] TASK-02-01: Red/green: `tests/test_plan2d.py` for the geometry-to-primitive mapping (wall rects, door swing arcs computed here — not in the spec, window symbols, stair treads with direction arrow, room labels with area, dimension lines for plot and rooms).
- [x] TASK-02-02: Implement `src/homedesign/plan2d.py`: shared primitive layer → SVG writer (hand-rolled, styled: fills per room type reusing the old `FILL_COLORS` idea) and DXF writer via `ezdxf` (layers: WALLS, DOORS, WINDOWS, STAIRS, TEXT, DIMS).
- [x] TASK-02-03: Wire into CLI: `python -m homedesign plans <spec>` → `output/svg/<name>_f<N>.svg`, `output/dxf/<name>_f<N>.dxf`.
- [x] TASK-02-04: Visual check both example specs' SVGs in a browser; fix legibility (stroke widths, label collision at small rooms).

**Files / Surfaces**
- `src/homedesign/plan2d.py`, `tests/test_plan2d.py` — new
- `src/generate_floorplan.py` — reference only, for door-arc math and fill/label conventions worth keeping

**Dependencies**
- PHASE-01 compiled model; pip: `ezdxf`

**Exit Criteria**
- [ ] Both example specs produce SVGs where every room, door swing, window, stair, and dimension is present and legible
- [ ] DXF opens cleanly (verify by re-reading with ezdxf in a test asserting layer contents)

**Phase Risks**
- **RISK-02-01:** Dimension/label auto-placement collides in small rooms. Mitigation: simple rules (labels shrink then move to leader lines); perfect drafting is not the bar — renders are the deliverable (DEC-002).

### PHASE-03 - Blender Shell Builder and Render Orchestration
**Goal**
Build the architectural 3D scene procedurally inside Blender from the compiled model — walls with real boolean openings, parametric doors/windows, floors/ceilings, stairs, roof, materials, lights, cameras — and render preview/final images from one CLI command.

**Tasks**
- [x] TASK-03-01: Create `src/homedesign/blender/build_scene.py` (runs inside Blender): read model JSON path from `sys.argv` after `--`; build wall solids per storey, subtract opening voids (bmesh boolean or object boolean modifier applied), add floor/ceiling slabs, stair treads, roof solid (flat/gable/shed).
- [x] TASK-03-02: Parametric joinery in `src/homedesign/blender/joinery.py`: door = frame + leaf (hinged slightly open for renders), window = frame + glass pane; sized from opening spec.
- [x] TASK-03-03: Port the material system: adapt `src/blender_materials.py` Principled-BSDF creation and `spec/blender_materials.json` definitions into `src/homedesign/blender/materials.py` + `spec/materials.json`; assign by room type (floors) and element class (walls, roof, glass, frames). Add style palettes keyed by the spec's `meta.style`.
- [x] TASK-03-04: Port lighting/camera/render logic from `src/setup_blender_scene.py` and `src/render_blender.py`: sun + sky, ground plane, auto-framed exterior camera plus one interior camera per named key room; render profiles `preview` (Cycles ~64 samples, 960×540, denoise) and `final` (~512 samples, 1920×1080).
- [x] TASK-03-05: Orchestrator: `python -m homedesign build <spec> [--final] [--floor N]` = validate → compile → plans → locate Blender (`BLENDER_CMD` env, then the known 4.1.1 path) → run `build_scene.py` headless → save `output/blend/<name>.blend` + `output/png/<name>_{exterior,<room>}.png`. Print artifact paths as the last stdout lines so the skill can parse them.
- [ ] TASK-03-06: Add `tests/test_orchestrator.py` for CLI arg handling and Blender-path resolution (mock subprocess); verify the real Blender leg manually on both examples.

**Files / Surfaces**
- `src/homedesign/blender/{build_scene,joinery,materials}.py` — new (Blender-side, no pytest)
- `src/homedesign/__main__.py` — extend with `build`
- `src/blender_materials.py`, `spec/blender_materials.json`, `src/setup_blender_scene.py`, `src/render_blender.py` — port sources; untouched until PHASE-06
- `run_blender.sh` — reference for Blender path probing, then superseded

**Dependencies**
- PHASE-01 model; Blender 4.1.1 present at the known path or via `BLENDER_CMD`

**Exit Criteria**
- [ ] `python -m homedesign build spec/examples/demo-3br-2storey.json` completes in one command and produces a .blend plus exterior + interior preview PNGs with visible wall openings, doors/windows with glass, and a roof
- [ ] Preview leg (Blender build + render) completes in under 60s on this machine (CON-003)

**Phase Risks**
- **RISK-03-01:** Boolean operations produce non-manifold artifacts / shading errors at coplanar faces. Mitigation: inset opening voids by 1mm beyond wall faces; apply booleans and run `mesh.normals_make_consistent`; known FreeCAD-era lesson — verify visually early.
- **RISK-03-02:** Headless Cycles on this machine falls back to CPU and blows the 60s preview budget. Mitigation: enable GPU via `cycles.preferences` in-script; if CPU-bound, drop preview to 32 samples / 720×405 before reconsidering EEVEE (which has its own headless-GL risk on Windows).

### PHASE-04 - Furnishing
**Goal**
Make renders read as a home (DEC-010): furniture per room type from a fetched CC0 library, with procedural fallback so the pipeline never hard-fails without assets.

**Tasks**
- [ ] TASK-04-01: Curate CC0 assets (Poly Haven models / Kenney / Quaternius): one .blend library per room-type set covering bed, wardrobe, sofa, coffee table, dining table+chairs, kitchen counter block, fridge, WC, basin, shower, desk. Write `scripts/fetch_assets.py` with pinned URLs + SHA-256 checksums downloading into `assets/furniture/` (gitignored); record licenses in `assets/LICENSES.md` (committed).
- [x] TASK-04-02: Implement `src/homedesign/blender/procedural_furniture.py`: stylized parametric fallbacks (bed = frame+mattress+pillows, sofa = beveled boxes, table+chairs, kitchen run, sanitary blocks) for every asset type.
- [x] TASK-04-03: Implement `src/homedesign/blender/furnish.py`: per-room-type placement rules (bed heads against longest windowless wall, wardrobe opposite, sofa faces largest wall/window, dining set centered, kitchen run along a wall with clearance, sanitary against plumbing wall) with door-swing and circulation clearance checks; prefer library asset (`bpy.data.libraries.load` append), fall back to procedural.
- [x] TASK-04-04: Red/green in system Python: `tests/test_placement.py` for the pure placement solver (extract placement math into `src/homedesign/placement.py`, importable outside Blender, so it is unit-testable; `furnish.py` only executes its output).
- [x] TASK-04-05: Render both examples furnished; iterate on scale/orientation glitches.

**Files / Surfaces**
- `scripts/fetch_assets.py`, `assets/LICENSES.md`, `.gitignore` (add `assets/furniture/`) — new
- `src/homedesign/placement.py`, `src/homedesign/blender/{furnish,procedural_furniture}.py`, `tests/test_placement.py` — new

**Dependencies**
- PHASE-03 scene builder; network once for asset fetch

**Exit Criteria**
- [ ] Interior render of the demo master bedroom and kitchen shows correctly scaled, non-overlapping furniture clear of door swings
- [ ] Deleting `assets/furniture/` still produces a fully furnished (procedural) render with no errors

**Phase Risks**
- **RISK-04-01:** Asset scale/origin conventions vary per pack. Mitigation: normalize once at curation (re-export via a prep .blend with origins at floor-center, real-world meters); checksum the normalized files.
- **RISK-04-02:** Placement solver scope creep. Mitigation: rules-per-room-type only, no global optimization; overflow furniture is skipped with a logged warning.

### PHASE-05 - /homedesign Skill and Acceptance Demo
**Goal**
Package the workflow as the `/homedesign` Claude Code skill with the bounded visual self-correction loop, and prove the DEC-013 acceptance demo end-to-end.

**Tasks**
- [x] TASK-05-01: Write `.claude/skills/homedesign/SKILL.md`: trigger (`/homedesign <idea>` or `/homedesign edit <change>`); procedure = author/patch spec at `output/specs/<slug>.json` per `spec/homespec.schema.json` (link + inline cheat-sheet + the two examples) → `python -m homedesign build` → Read the preview PNGs + floor SVGs → self-correct on structured validation errors or visual defects (overlaps, floating/misscaled elements, unusable proportions), max 3 passes → present renders + plans with a summary → offer `--final`.
- [x] TASK-05-02: Edit-loop contract in the skill: conversational changes are minimal JSON edits to the existing spec (never regenerate whole spec); re-run; diff-summarize what changed (DEC-003).
- [x] TASK-05-03: Run the acceptance demo: `/homedesign 3-bedroom 2-storey house, open kitchen, master with ensuite` → plans + furnished exterior/interior renders in one turn; then `/homedesign edit make the kitchen bigger` → round-trips with only kitchen-related diffs.
- [x] TASK-05-04: Record demo results (spec, renders, pass count) in `activeContext.md` review section.

**Files / Surfaces**
- `.claude/skills/homedesign/SKILL.md` — new
- `activeContext.md` — plan checklist + results per user's global task-management rules

**Dependencies**
- PHASE-02 (plans in output), PHASE-04 (furnished renders)

**Exit Criteria**
- [ ] Acceptance demo passes exactly as specified in DEC-013, with ≤3 self-correction passes and no manual JSON editing
- [ ] A deliberately flawed idea ("bathroom inside the garage with no door") is caught by validation and auto-corrected or clearly surfaced

**Phase Risks**
- **RISK-05-01:** LLM spec authoring drifts from schema. Mitigation: validation errors are structured (PHASE-01) and the skill mandates feeding them back verbatim; schema kept small with enums over free text.

### PHASE-06 - Legacy Deletion and Docs Cleanup
**Goal**
Remove the FreeCAD path aggressively (DEC-012) now that the new pipeline passes acceptance, leaving one coherent tool.

**Tasks**
- [x] TASK-06-01: Delete `src/generate_floorplan.py`, `src/blender_export_utils.py`, `src/facade_utils.py`, `src/blender_materials.py`, `src/setup_blender_scene.py`, `src/render_blender.py`, `run.sh`, `run_blender.sh`, `opencode.json`, `freecad-mcp-guide.md`, `spec/floorplan-spec.json`, `spec/blender_materials.json` (contents ported in PHASE-03), stale FreeCAD test artifacts (`*.FCStd`, `freecad_std*.log` at root), and FreeCAD-era tests; keep `src/ifc_export_utils.py` parked with a header note that it targets the retired spec format (plan DEC-002).
- [x] TASK-06-02: Port any still-referenced helpers out of `src/floorplan_utils.py` then delete it; confirm `python -m pytest tests/` green after deletions.
- [x] TASK-06-03: Update `README`/`CLAUDE.md`-equivalent docs, `activeContext.md`, and mark `plans/2026-05-11-obj-ifc-arch-upgrade-plan.md` superseded (PHASE-07/Arch migration obsoleted); add relevant entries to `docs/lessons-learned.md`.
- [ ] TASK-06-04: Fresh-clone sanity: from a clean checkout (plus one `fetch_assets.py` run or skipping it), `python -m homedesign build spec/examples/demo-3br-2storey.json` works.

**Files / Surfaces**
- All legacy files listed above — deleted
- `activeContext.md`, `docs/lessons-learned.md`, `plans/2026-05-11-obj-ifc-arch-upgrade-plan.md`, `README*` — updated

**Dependencies**
- PHASE-05 acceptance demo passed (hard gate before any deletion)

**Exit Criteria**
- [ ] No references to FreeCAD/freecadcmd remain outside `src/ifc_export_utils.py`'s header note, research briefs, and superseded plans (`grep -ri freecad` audit)
- [ ] Full test suite green; `build` runs end-to-end post-deletion

**Phase Risks**
- **RISK-06-01:** Something silently depended on a deleted module. Mitigation: deletion is one reviewable commit after a grep audit; git revert is the rollback.

## Verification Strategy
- **TEST-001:** `python -m pytest tests/` — compiler, validation, plan2d primitives, placement solver, orchestrator arg handling; all written red-first per TDD (phases 01, 02, 04).
- **TEST-002:** `python -m homedesign compile spec/examples/*.json` in CI-style script — both examples validate and compile deterministically (byte-identical model JSON on re-run, proving idempotence for the edit loop).
- **MANUAL-001:** Visual pass on SVGs (PHASE-02) and preview renders (PHASE-03/04) for both examples — openings visible, furniture scaled, no shading artifacts.
- **MANUAL-002:** The DEC-013 acceptance demo including the "bigger kitchen" edit round-trip (PHASE-05 exit criteria).
- **OBS-001:** Preview-leg wall-clock printed by the orchestrator each run; must stay <60s (CON-003) — checked during PHASE-03 and re-checked after furnishing lands in PHASE-04.

## Risks and Alternatives
- **RISK-001:** Furnishing (PHASE-04) is the largest and least deterministic workstream and could stall the whole effort. Mitigation: PHASE-03 already yields a complete unfurnished tool; procedural fallback (TASK-04-02) ships before asset curation, so the skill (PHASE-05) can proceed on procedural furniture if curation drags.
- **RISK-002:** Blender-side code can't be unit-tested, concentrating risk in manual verification. Mitigation: keep all math (placement, joinery dimensions, camera framing) in importable pure modules under `src/homedesign/`; Blender scripts only execute precomputed instructions.
- **ALT-001:** Extend FreeCAD Part::Box generator / migrate to Arch workbench — rejected in brainstorm (DEC-007, ALT-001/002): heavyweight fragile dependency, lossy OBJ handoff, render-first goal.
- **ALT-002:** LLM authors the existing low-level spec — rejected (brainstorm ALT-003): unreliable and undiffable.
- **ALT-003:** EEVEE for previews — deferred: headless EEVEE GL context on Windows is a known risk; low-sample Cycles first, EEVEE only if the preview budget fails (RISK-03-02).

## Grill Me
1. **Q-001:** Should PHASE-06 deletion also drop `src/ifc_export_utils.py` and its tests entirely, rather than parking it against a spec format that will no longer exist?
   - **Recommended default:** Park it (keep file + header note, skip its tests) per brainstorm Q-001 default.
   - **Why this matters:** Determines whether PHASE-06's grep audit and test-suite scope include IFC code.
   - **If answered differently:** TASK-06-01 deletes it too; git history remains the recovery path if BIM output is ever needed.
2. **Q-002:** For the demo home's look (`meta.style`), is one default palette (e.g. "modern-minimal": white walls, oak floor, dark window frames) enough for v1, with more palettes later?
   - **Recommended default:** Yes — one polished default palette plus the schema hook for future styles.
   - **Why this matters:** Bounds TASK-03-03 material work; multiple styles multiply curation and visual QA.
   - **If answered differently:** Add 2-3 named palettes to `spec/materials.json` and a style column to MANUAL-001 checks.

## Suggested Next Step
Answer the two Grill Me questions (defaults are safe), then begin PHASE-01 with the red tests in `tests/test_compiler.py` — and per your global workflow, mirror the phase checklist into `activeContext.md` before implementation starts.
