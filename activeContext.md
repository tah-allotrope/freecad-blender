# Active Context

## Project Info
- **Workspace:** `freecad-blender`
- **Objective:** `/homedesign` — turn a natural-language home idea into validated 2D floor plans (SVG/DXF), elevations and sections, furnished 3D renders (legacy EEVEE/Cycles), an interactive GLB web viewer and an A3 architect brief, via a compiled high-level spec, built entirely in Python + Blender (no FreeCAD).

## Current Task Plan (plans/2026-08-14-balcony-parapet-render-fix-plan.md)

Completed in full. Summary:

**Balconies now render open, not as sealed boxes.** The render-vs-drawing
comparison (`reports/2026-08-14-contractor-render-vs-drawing.html`, findings 05
and 06) showed every `balcony`-typed room compiling and rendering with a
full-height wall on its open edge — `build_scene.build_walls()` built every wall
unconditionally and `_add_balcony_parapets()` only added a 1100mm railing on top.
Fixed at the root: `Wall` gained an owning `room_id` (populated in
`_derive_walls` for `exterior` walls, `None` for partitions), and `build_walls()`
now skips any exterior wall whose `room_id` is a `balcony`-typed room that
carries no opening. Verified geometrically (the set of balcony-owned walls
matches `open_edges()` for every balcony in both real designs) and visually
(rebuilt renders show real glazing and open, railed edges). One exception,
confirmed by re-checking rather than assumed: `tubehouse-dream`'s `balcony_f2`
and `balcony_f3` each carry a window authored directly on their own outer wall
rather than the partition to the bedroom, so that one edge on each correctly
stays a full wall (the suppression's own safety condition) while the other two
open up — every other balcony/terrace in both designs, including
`contractor-as-drawn`'s six, opens fully. Both `tubehouse-dream` and
`contractor-as-drawn` galleries rebuilt at `final` quality and republished;
`fidelity.md` findings (e) and (f) marked resolved. Tests: **134 passed**
(131 + 3 new in `test_compiler.py`).

## Prior Task Plan (plans/2026-08-13-contractor-scheme-3d-render-plan.md)

Completed in full. Summary:

**3D render of the contractor's as-drawn scheme.** The five text-less PDFs under
`contractor/` were reconstructed (via the measured review + the plan's binding
defaults, documented in `designs/contractor-as-drawn.measurements.md`) into
`designs/contractor-as-drawn.json` — a seven-storey (trệt / lửng / tầng 2–5 /
sân thượng), 3960 × 25000 mm tube house with the drawn core (3005 mm U-return
stair, 1500 × 1600 lift, light well) repeated identically on every level. The
spec compiles clean (0 schema errors, 0 check items at all) and is covered by two
new tests in `tests/test_validate.py`. A 12-view `final` legacy-EEVEE gallery,
a 1.12 MiB GLB and a self-contained viewer are published to
`deliverables/contractor-as-drawn/`. Every departure from the drawing — the
skewed boundaries, the glazed light-well cap, the winder treads, the enlarged
stair shaft, the plant room, and the decorative (not solar) shadows — is ledgered
in `designs/contractor-as-drawn.fidelity.md`.

**Necessary deviation from the plan's "no src changes":** compiling a spec whose
room names carry Vietnamese diacritics exposed a latent Windows encoding bug —
`__main__._load_spec`/`_write_model_json`, the `plan2d`/`elevation` SVG writers,
and `model`'s render-sidecar helpers read/wrote text with the locale default
(CP1252), mangling or rejecting UTF-8. Fixed by pinning `encoding="utf-8"` at
those sites (no logic changed). `tests/test_camera_placement.py`'s
`_model_of` got the same one-line fix so the design sweep loads the spec.

## Prior Task Plan (plans/2026-08-04-homedesign-camera-truth-and-drawings-plan.md)

Completed in full (127 tests, ruff clean, skill mirror synced). Summary:

**PHASE-01 Camera Truth:** `fit_distance` sign fix (depth term subtracted — binding corner is the nearest one); `exterior_front_camera` anchored on the facade box centre; `exterior_aerial_camera` and `interior_camera` (inside-the-room constrained, focal length solved) added to `camera_fit.py`; the three Blender camera builders are now thin wrappers. Off-centre regression test fails under the old `+` sign (teeth check verified). Containment sweep across every spec; tightened framing test now asserts the building clears all frame edges (fails on the old cropped render, passes now).
**PHASE-02 Engine:** Blender **4.5.1 LTS** installed alongside 4.1.1 and made the default candidate; `RENDER_PROFILES` (`preview` EEVEE 32s / `final` EEVEE Next 256s + raytracing + AgX / `cycles` 512s) in a pure module; version-tolerant EEVEE guards; `--profile` on build+render. Benchmark (see `docs/lessons-learned.md`): full 9-view `tubehouse-dream` final gallery **50.7 min** vs 11.3 h previously; single Cycles view of `tubehouse-mini` = 9.8 min. EEVEE Next retained as `final` per ASM-002. **[SUPERSEDED 2026-08-08 — EEVEE Next renders every surface blood red on this iGPU; the default is now Blender 4.1 legacy EEVEE. See the 2026-08-08 entry under Review.]**
**PHASE-03 Geometric realism:** `railings.py` (parapets 1100mm on balcony open edges via pure `rects.open_edges`; stair balustrades 900mm per flight); top-storey ceilings for rooms the roof doesn't cover; lintels + window sills in `joinery.py`; `site.context` neighbour party-wall massing + street strip; `neighbour`/`street` materials.
**PHASE-04 Drawing set:** `elevation.py` produces a neutral draw model rendered to SVG + DXF — four elevations (per-side axis table in S3) and two sections (long `x`/cross `y` cut planes, poché walls, 200mm slab bands, tread outlines, room labels); `plan2d.write_plans` emits the full 22-file set; PDF gains 6 pages (23 total, A3 landscape, verified).
**PHASE-05 Honest geometry:** `site.wall_alignment` (`centre` default reproduces old geometry byte-identically; `inside` sets exterior walls' outer face on the plot line); `Room.interior` computed per edge (full thickness exterior under `inside`, half otherwise) and consumed by furniture/lights/cameras; `wall_outside_plot` promoted to a real error with alignment-aware tolerance; tubehouse-dream set to `inside` → **0 warnings** (was 63), north elevation now 4000 mm (was 4200); built-envelope row added to the take-off.
**PHASE-06 Provenance & hygiene:** `model_hash` (SHA-256, 12 hex) stamped into compiled models and every render sidecar; `pdf` warns/stamps `STALE` on stale galleries and `--require-fresh` makes them hard errors; glTF export + self-contained offline viewer (`output/viewer/<name>.html`, three.js inlined, GLB embedded); `src/ifc_export_utils.py` deleted; `[project.scripts]` console script; AGENTS.md/README/SKILL.md accuracy pass; superseded FreeCAD workflow doc archived; dead code removed; `deliverables/` introduced and the flagship finals committed.

## Review

### 2026-08-13 — Contractor as-drawn render (plans/2026-08-13-contractor-scheme-3d-render-plan.md, all phases done)

**Render wall-clock:** `blender build: 1450.6s` (~24.2 min) for the 12-view
`final` gallery + scene build + glTF export — inside the 25-minute budget, and
~2× the 9-view `tubehouse-dream` set as expected for 40% more geometry.
**GLB:** 1 179 312 bytes → inlines in the viewer (ASM-007 does not apply).
**Provenance:** all 12 sidecars match `bb284a0b6ca5`. **No red render** (EEVEE
Next never ran).

**What had to be inferred (and is ledgered, not hidden):** the environment has no
image-input capability and the sheets have no text layer, so the printed glyphs
could not be re-read this pass. Dimensions come from the measured
`reports/2026-08-12-contractor-drawing-set-review.html` (calibrated K = 43.0 mm/pt)
cross-checked against the plan's binding defaults; per-room subdivision within the
measured envelope is `(inferred)` and flagged as such in the measurements file.
The plan's own 12-view table placed `khach`/`bep_an` on "level 2" and `sinh_hoat`
on "level 4"; the measured review places living+kitchen on the ground floor and
the family room on the lửng, so the model follows the **measured** programme and
the view mapping is reconciled in the fidelity ledger.

**Stair shaft enlarged** (RISK-02-01, as predicted): the drawn 3005 × 3200 shaft
cannot hold a Blondel U-return at a 3800 mm storey (S-2 needs 3998 mm run); the
shaft is enlarged to 3005 × 4000 and flagged as a candidate review finding.

### 2026-08-08 — Render engine reverted to legacy EEVEE (supersedes ASM-002 / PHASE-02)

**Symptom:** every render in the shipped `tubehouse-dream` gallery was blood red. A
white exterior wall (`0.92, 0.91, 0.88`) came out `(214, 56, 51)`; interiors were
worse (`(149, 1, 46)` — green channel at zero).

**Root cause: EEVEE Next miscompiles on this machine's iGPU.** Isolated with a
25-line repro (one cube, one sun, the project's own material/engine/view-transform
code), matrix over engine x view transform x raytracing:

| engine | view transform | white cube renders as |
|---|---|---|
| Cycles | AgX | `(190, 193, 197)` correct |
| Cycles | Standard | `(235, 244, 255)` correct |
| EEVEE Next | AgX | `(194, 34, 53)` red |
| EEVEE Next | AgX, raytracing off | `(194, 34, 53)` red |
| EEVEE Next | Standard | `(208, 0, 55)` red, G channel 0 |

Independent of view transform and of `raytracing`, and the world background is
unaffected — so the fault is in surface shading, not colour management. Hardware is
Intel UHD Graphics 620 (Gen9.5) on driver `23.20.16.4849` (2018). Vulkan is not an
escape: Blender rejects the device for missing timeline semaphores, buffer device
address and `VK_EXT_provoking_vertex`. Cycles has no GPU path here either —
OPTIX/CUDA/HIP/oneAPI all enumerate zero devices (i5-8250U, 4c/8t, 7.8 GB RAM).

**Decision:** `orchestrator._CANDIDATES` now prefers **Blender 4.1.1 (legacy EEVEE)**
over 4.5.1 (EEVEE Next), reversing PHASE-02's "4.5.1 ... made the default candidate"
and ASM-002's "EEVEE Next retained as `final`". `build_scene._set_engine` already
falls back to `BLENDER_EEVEE`, and `render_profiles` is unchanged — `final`'s
`raytracing: True` degrades to a no-op under 4.1. `BLENDER_CMD` still overrides for a
machine whose GPU handles EEVEE Next correctly. Regression test:
`test_blender_candidates_prefer_legacy_eevee_build`.

**Measured (1920x1080, `exterior_front`):** legacy EEVEE 256 spp **29.7 s/view**;
Cycles CPU 64 spp + denoise **169.3 s/view**; EEVEE Next 112 s for a *single cube*.
Full 9-view `final` gallery + scene build + glTF: **713.5 s (11.9 min)** — down from
the 50.7 min recorded under EEVEE Next in PHASE-02.

**Verified:** all 9 renders neutral, all sidecars stamped `ea67a4708772` matching the
current model, brief rebuilt under `--require-fresh` (exit 0, 23 pages, 6.33 MB).
Old red renders preserved in `output/png_red_backup/`.

**Known-good tradeoff:** legacy EEVEE has no raytraced GI/reflections. On today's
untextured massing that costs essentially nothing; revisit if materials gain depth.

**Not addressed here** (diagnosed, still open): (a) `deliverables/tubehouse-dream/`
still holds the red PDF/GLB — manual copy step, left for a deliberate publish;
(b) the brief's own layout defects (Chromium's default header printed over every
page, plan SVGs occupying ~14% of page width with ~2.5 pt labels, half-empty gallery
pages, 44 DPI cover hero); (c) the furniture planner leaves **25 of 41 rooms empty**
and paints all 41 items one shared tan.

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
