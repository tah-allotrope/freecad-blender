# Active Context

## Project Info
- **Workspace:** `freecad-blender`
- **Objective:** `/homedesign` — turn a natural-language home idea into validated 2D floor plans (SVG/DXF), elevations and sections, furnished 3D renders (EEVEE/EEVEE Next/Cycles), an interactive GLB web viewer and an A3 architect brief, via a compiled high-level spec, built entirely in Python + Blender (no FreeCAD).

## Current Task Plan (plans/2026-08-04-homedesign-camera-truth-and-drawings-plan.md)

Completed in full (127 tests, ruff clean, skill mirror synced). Summary:

**PHASE-01 Camera Truth:** `fit_distance` sign fix (depth term subtracted — binding corner is the nearest one); `exterior_front_camera` anchored on the facade box centre; `exterior_aerial_camera` and `interior_camera` (inside-the-room constrained, focal length solved) added to `camera_fit.py`; the three Blender camera builders are now thin wrappers. Off-centre regression test fails under the old `+` sign (teeth check verified). Containment sweep across every spec; tightened framing test now asserts the building clears all frame edges (fails on the old cropped render, passes now).
**PHASE-02 Engine:** Blender **4.5.1 LTS** installed alongside 4.1.1 and made the default candidate; `RENDER_PROFILES` (`preview` EEVEE 32s / `final` EEVEE Next 256s + raytracing + AgX / `cycles` 512s) in a pure module; version-tolerant EEVEE guards; `--profile` on build+render. Benchmark (see `docs/lessons-learned.md`): full 9-view `tubehouse-dream` final gallery **50.7 min** vs 11.3 h previously; single Cycles view of `tubehouse-mini` = 9.8 min. EEVEE Next retained as `final` per ASM-002.
**PHASE-03 Geometric realism:** `railings.py` (parapets 1100mm on balcony open edges via pure `rects.open_edges`; stair balustrades 900mm per flight); top-storey ceilings for rooms the roof doesn't cover; lintels + window sills in `joinery.py`; `site.context` neighbour party-wall massing + street strip; `neighbour`/`street` materials.
**PHASE-04 Drawing set:** `elevation.py` produces a neutral draw model rendered to SVG + DXF — four elevations (per-side axis table in S3) and two sections (long `x`/cross `y` cut planes, poché walls, 200mm slab bands, tread outlines, room labels); `plan2d.write_plans` emits the full 22-file set; PDF gains 6 pages (23 total, A3 landscape, verified).
**PHASE-05 Honest geometry:** `site.wall_alignment` (`centre` default reproduces old geometry byte-identically; `inside` sets exterior walls' outer face on the plot line); `Room.interior` computed per edge (full thickness exterior under `inside`, half otherwise) and consumed by furniture/lights/cameras; `wall_outside_plot` promoted to a real error with alignment-aware tolerance; tubehouse-dream set to `inside` → **0 warnings** (was 63), north elevation now 4000 mm (was 4200); built-envelope row added to the take-off.
**PHASE-06 Provenance & hygiene:** `model_hash` (SHA-256, 12 hex) stamped into compiled models and every render sidecar; `pdf` warns/stamps `STALE` on stale galleries and `--require-fresh` makes them hard errors; glTF export + self-contained offline viewer (`output/viewer/<name>.html`, three.js inlined, GLB embedded); `src/ifc_export_utils.py` deleted; `[project.scripts]` console script; AGENTS.md/README/SKILL.md accuracy pass; superseded FreeCAD workflow doc archived; dead code removed; `deliverables/` introduced and the flagship finals committed.

## Review

### Sprint review — 2026-08-05 (plans/2026-08-04-homedesign-camera-truth-and-drawings-plan.md, all phases done)

**Deviation notes vs the plan text:** (1) the framing-test thresholds were recalibrated to real pixels — the plan's `min_y > 0.02*540` assumes the roof never protrudes above the facade fit box, but the 200mm roof slab + overhang corners leave ~4px of sky, and the `0.30` width floor is unachievable for a 4m facade at 35mm (it is ~24-29% wide); the test asserts `min_y > 0.005*540` and `0.12 < width < 0.95` and still fails on the old cropped render (`min_y == 0`). (2) `build_section(model, "x", -1.0)` returns only `ground` only for a plane clearly past the 100mm centre-aligned wall overhang; the test uses `-1000`. (3) `scene.eevee.use_raytracing` accepts `True` on 4.1.1 too, so "eevee raytracing: unavailable" never prints there — the `hasattr` guard is unchanged. (4) The `final` gallery measured **50.7 min**, above the 30-min aspiration; recorded and kept per ASM-002 (the lever is `raytracing: False` on `final`).

### Earlier review (2026-07-30 plan)

### What was built
- **PHASE-01 Packaging/CI:** `pyproject.toml` editable install, unified `homedesign.` imports, ruff gate in CI.
- **PHASE-02 Buildable circulation:** `stairs.py` (Blondel-compliant straight/U-return), `rects.py` slab-fragment subtraction, floor voids, tubehouse-dream core re-laid.
- **PHASE-03 Validation registry:** `checks.py` (door reachability, habitable daylight, room support, shaft stacking, walls-within-plot), opening `align`/`offset_mm` + overlap rejection, `--json` CLI, `_Placer` rotation fix, bed `rot_deg=90`. Fixed real spec defects.
- **PHASE-04 Render economics:** EEVEE preview; Cycles final + adaptive sampling; `render` subcommand with `--view/--skip-existing/--detach`.
- **PHASE-05 Camera framing:** `camera_fit.py` S4 analytic fit; all cameras `sensor_fit=HORIZONTAL`.
- **PHASE-06 Drawing quality:** SVG door swings + 3-line windows, north arrow, scale bar, title block; DXF y-flip; PDF gallery relative + downscaled, schedules + take-off pages; `designs/` created, skill mirror + CI gate, AGENTS.md rewritten.

## Prior Phase History
- `plans/2026-07-04-idea-floorplan-3d-home-tool-plan.md` (all phases complete) — built the original `/homedesign` pipeline (schema, compiler, plan2d, Blender build/furnish, skill doc).
- `plans/2026-05-11-obj-ifc-arch-upgrade-plan.md` PHASE-03 (Arch/BIM migration) obsoleted by the decision to drop FreeCAD entirely.
