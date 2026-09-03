---
title: "Render Fidelity for the Construction Set"
date: "2026-08-29"
status: "complete — all 49 tasks done. Phase 5 viewer tooling (labels, ruler, section sliders, layer toggles), the slatted parapet, elevation divisions and the rev.4 ledger landed 2026-09-03; final-profile build of all 12 views published with an 18.1 MB full GLB and a 5.8 MiB light build."
request: "Enhance the 3D render of designs/contractor-as-drawn.json for best accuracy and visual fidelity against the contractor's drawing set, and deliver it to the construction team."
plan_type: "multi-phase"
research_inputs:
  - "research/2026-08-29_render-fidelity-construction-set-brainstorm.md"
  - "research/2026-08-13_contractor-scheme-3d-render-brainstorm.md"
---

# Plan: Render Fidelity for the Construction Set

## Objective

Raise the 3D render of `designs/contractor-as-drawn.json` from a white massing study to a
construction-grade set that survives being placed beside the contractor's own elevation
sheet and beside a photograph of a real Ho Chi Minh City tube house. Deliver it through
three channels the construction crew actually uses: an interactive GLB viewer on a phone,
images pasted into a chat app, and printed A3 plates. Close the biggest untested hole in
the repository along the way — there is currently no 2D-to-3D parity test and no
render-fidelity test of any kind.

## Context Snapshot

- **Current state:**
  - `designs/contractor-as-drawn.json` is a validated 7-storey spec (plot 3960 × 25000 mm,
    total height 23800 mm) that compiles, renders 12 views, exports a 449 KB GLB and is
    published to `deliverables/contractor-as-drawn/` and `docs/`.
  - The render is not usable as a construction document.
    `deliverables/contractor-as-drawn/png/contractor-as-drawn_exterior_front.png` shows a
    white tower standing alone on a green lawn: no street, no neighbours, no facade
    articulation, flat untextured surfaces, the building filling roughly 8% of the frame.
    `deliverables/contractor-as-drawn/png/contractor-as-drawn_khach.png` shows a door leaf
    detached from its frame and clipping through the sofa, box furniture, no skirting, no
    reveals, walls blown out to white.
  - The direct cause of the missing neighbours is in the data:
    `designs/contractor-as-drawn.json` sets `site.context.neighbours: false`, so
    `build_scene._add_neighbour_massing` never runs.
  - There is no material vocabulary anywhere in `spec/homespec.schema.json`. All appearance
    comes from a single hardcoded 20-entry flat Principled-BSDF palette,
    `PALETTES["modern-minimal"]` in `src/homedesign/blender/materials.py`, keyed by element
    kind. No textures, no UVs, no image maps, no per-design override.
  - Openings are undivided rectangles (no mullions or transoms); balcony railings are a
    plain 1100 mm solid parapet; facade fins, cornice bands and framed panels drawn on the
    elevation sheet are entirely unmodelled.
  - Lighting is one fixed sun at azimuth 55° / elevation 35° with energy 2.0, one weak area
    fill at energy 25, and one area light per room sized `clamp(area_m2 * 2.2, 20, 90)`.
  - The 226-test suite asserts on compiled-model values, SVG/DXF text content and camera
    mathematics only. `tests/test_blender_geometry.py` is gated behind
    `pytest.importorskip("bpy")` and never runs in CI.
  - `docs/` is the GitHub Pages root and is synchronised by hand; the only workflow,
    `.github/workflows/ci.yml`, runs ruff, pytest and a skill-sync check.
- **Desired state:** an articulated facade authored from the contractor's elevation, real
  party walls and an alley, a finish schedule expressed in the spec and rendered
  procedurally, credible furnished interiors, a viewer with room labels, measurement,
  section slider and layer toggles in two size-targeted builds, and a single final build
  that publishes all three channels plus a self-contained HTML report — with a millimetre
  elevation-overlay parity test guarding accuracy the whole way.
- **Key repo surfaces:**
  - `spec/homespec.schema.json` — closed contract, `additionalProperties: false` on every
    object; top-level properties are exactly `meta`, `site`, `storeys`; there are no
    `$defs`; `meta.style` is a single-value enum (`modern-minimal`).
  - `src/homedesign/model.py` — dataclasses `Rect, Room, Wall, Opening, Tread, Stairs, Roof,
    View, Storey, CompiledModel`; `model_hash`, `write_render_sidecar`, `read_render_sidecar`.
  - `src/homedesign/compiler.py` — `compile_spec`, wall derivation, `_derive_floor_voids`.
  - `src/homedesign/blender/build_scene.py` (628 lines) — `build_walls`,
    `build_floors_and_stairs`, `_add_balcony_parapets`, `_add_stair_balustrades`,
    `_add_top_storey_ceilings`, `_build_roof_structures`, `_neighbours_enabled`,
    `_add_neighbour_massing`, `build_environment`, `add_interior_lights`, `add_cameras`,
    `_set_engine`, `_configure_cycles_device`, `render`, `main`.
  - `src/homedesign/blender/materials.py` — `PALETTES`, `get_material`, `ROOM_FLOOR_KEY`,
    `floor_material_key`, `FURNITURE_MATERIAL_KEY`, `furniture_material_key`.
  - `src/homedesign/blender/joinery.py` — `FRAME_DEPTH = 0.06`, `FRAME_WIDTH = 0.06`,
    `GLASS_THICKNESS = 0.012`, `DOOR_LEAF_THICKNESS = 0.045`, `build_opening_furniture`.
  - `src/homedesign/blender/railings.py` — `build_parapet`, `build_balustrade`.
  - `src/homedesign/blender/geom.py` — `make_box`, `make_hinged_box`.
  - `src/homedesign/blender/furnish.py` — `furnish_storey`;
    `src/homedesign/blender/procedural_furniture.py` — `build_item` and twelve `_build_*`
    box-primitive builders.
  - `src/homedesign/placement.py` — `FurnitureItem`, `plan_room` and the per-room-type
    planners; shared by 2D and 3D.
  - `src/homedesign/elevation.py` — `build_elevation`, `build_section`, `_svg`, `_dxf`,
    `write_elevations`, `write_sections`.
  - `src/homedesign/plan2d.py` — `write_plans` and its SVG/DXF helpers.
  - `src/homedesign/viewer.py` — `INLINE_GLB_LIMIT_BYTES = 8 * 1024 * 1024`, `optimize_glb`,
    `_load_call`, `write_viewer`, `write_floor_viewer`.
  - `src/homedesign/assets/viewer_template.html`, `src/homedesign/assets/floor_viewer_template.html`.
  - `src/homedesign/render_profiles.py` — `RENDER_PROFILES` with keys `preview`, `final`,
    `cycles`.
  - `src/homedesign/orchestrator.py` — `_CANDIDATES`, `find_blender`, `_build_command`,
    `build_scene`, `render_only`.
  - `src/homedesign/publish.py` — `verify_fresh`, `publish`.
  - `src/homedesign/__main__.py` — subcommands `compile`, `plans`, `build`, `render`, `pdf`,
    `brief`, `publish`.
  - `designs/contractor-as-drawn.json`, `designs/contractor-as-drawn.measurements.md` (rev.3),
    `designs/contractor-as-drawn.fidelity.md` (rev.3).
  - `contractor/` — five vector PDFs (`MB 1-LUNG`, `MB 2-3-4`, `MB 5- MAI`, `MB MAI - MD`,
    `MC A- A`) plus `approval drawing.jpg`; rasterisations in `output/contractor_pdf_png/`.
  - `tests/test_plan2d.py` from line 451 — the codified contractor-parity block, the pattern
    every new fidelity test must follow.
- **Out of scope:**
  - Upgrading Blender, or using EEVEE Next or Cycles in any form.
  - Any solar or daylight analysis, sun-path study, or setting `site.north_deg`.
  - Re-rendering or modifying `designs/tubehouse-dream.json` and its deliverables.
  - Street entourage: motorbikes, overhead cables, signage, planting.
  - Re-opening the three accepted drawing deviations recorded in
    `designs/contractor-as-drawn.fidelity.md`: the orthogonal collapse of the ~7.2° skewed
    plot boundary (item a), the inferred lift shaft (item c), and the 4000 mm stair depth
    against the drawn 3200 mm (item g).
  - Structural, mechanical, electrical or code-compliance interpretation.

## Environment & Conventions

- **Stack:** Python ≥ 3.11 (CI pins 3.11), setuptools build backend, package `homedesign`
  under `src/`. Runtime dependencies: `jsonschema>=4.0`, `ezdxf>=1.0`, `pillow>=10.0`. Dev
  extra: `pytest>=8.0`, `ruff==0.15.7`. Optional extra `bpy` pins `bpy==4.1.0` (~1 GB wheel).
  Rendering shells out to a separate installed Blender application, not to the `bpy` wheel.
- **Setup:**
  ```
  python -m pip install -e ".[dev]"
  ```
  To run the Blender-gated geometry tests locally as well:
  ```
  python -m pip install -e ".[dev,bpy]"
  ```
- **Build / Run:**
  ```
  homedesign compile designs/contractor-as-drawn.json
  homedesign plans   designs/contractor-as-drawn.json
  homedesign build   designs/contractor-as-drawn.json --profile final --gltf
  homedesign render  designs/contractor-as-drawn.json --profile final
  homedesign publish designs/contractor-as-drawn.json
  ```
  Outputs land in `output/{compiled,svg,dxf,blend,png,gltf,viewer,pdf,logs}/`. `output/` is
  gitignored and disposable; published finals live in `deliverables/<slug>/`.
- **Test:** full suite —
  ```
  python -m pytest tests -q
  ```
  (226 tests collected before this plan's work). Single test —
  ```
  python -m pytest tests/test_plan2d.py::test_setback_lines_rendered_in_svg_and_dxf -q
  ```
  Lint gate, exactly as CI runs it —
  ```
  ruff check src tests
  python scripts/sync_skill.py --check
  ```
- **Conventions & traps:**
  - Line length 120 (`ruff.toml`). Flat function-style tests, no `conftest.py`, no fixtures
    directory. Test files are `tests/test_<area>.py`.
  - **All dimensions in the spec and compiled model are millimetres**, with the suffix
    `_mm` on every field. Blender works in **metres**; every `build_scene` helper divides by
    1000 at the boundary and local variables carry an `_m` suffix. Never mix the two.
  - `bpy` may only be imported from modules under `src/homedesign/blender/`. Everything else
    must be pure Python, because CI never installs `bpy`.
  - Pure logic goes in `src/homedesign/` and is unit-tested there; only the `bpy` binding
    lives in `src/homedesign/blender/`. `src/homedesign/camera_fit.py` with
    `tests/test_camera_fit.py` is the reference example.
  - Every JSON file under `designs/` contains Vietnamese text. **Always open them with an
    explicit encoding**: `open(path, encoding="utf-8")`. On Windows the default `cp1252`
    codec raises `UnicodeDecodeError` on these files.
  - Room names and labels stay in Vietnamese, spelled exactly as printed on the contractor's
    sheets (`P.KHÁCH`, `P.NGỦ 1`, `P.THỜ`, `BẾP`, `SÂN THƯỢNG`).
  - Geometry shared between the 2D and 3D pipelines must be produced by one pure helper both
    call — `plan2d._svg_furniture` and `blender/furnish` already share `placement.plan_room`.
    Duplicating logic re-opens a divergence that was closed on 2026-08-17.
- **Repo map:**
  ```
  spec/homespec.schema.json     the closed JSON Schema contract
  spec/examples/                small fixture specs used by tests
  spec/briefs/                  brief copies keyed by design slug
  designs/                      real design specs + measurement/fidelity sidecars
  contractor/                   source PDFs of the contractor's issued drawing set
  src/homedesign/               pure Python: compiler, checks, plan2d, elevation,
                                camera_fit, placement, viewer, publish, orchestrator
  src/homedesign/blender/       the only modules allowed to import bpy
  src/homedesign/assets/        viewer HTML templates + inlined three.js bundles
  tests/                        226 flat pytest functions, 18 files
  reports/                      review and parity-checklist markdown/HTML
  deliverables/<slug>/          published png/gltf/viewer/pdf
  docs/                         GitHub Pages root, currently hand-synced
  scripts/                      sync_skill.py, regen_viewer.py and helpers
  ```

## Research Inputs

- From `research/2026-08-29_render-fidelity-construction-set-brainstorm.md`:
  - The driving problem is **visual credibility**, not a suspected drawing error. The render
    reads as massing and that is what disqualifies it. Accuracy is therefore the constraint
    on the work, not its goal: every realism gain must be traceable to the contractor's
    sheets rather than invented.
  - The quality bar is **dual**. Geometric half: the render overlaid on the contractor's
    `MẶT ĐỨNG CHÍNH` elevation at identical scale, with the deviation stated in millimetres.
    Visual half: Vo Trong Nghia's "Stacking Green", Ho Chi Minh City — a professionally
    photographed ~4 m-wide Saigon tube house with the same light-well problem. Its planted
    facade is deliberately atypical; the comparison judges material, light and scale, not
    styling.
  - Full scope is authorised: the Blender layer, the schema and compiler, and the spec data
    itself. This reverses the previous pass's "no schema or compiler changes" decision. The
    fidelity ledger is now the backlog.
  - Finishes enter through a `finishes` block in the schema driven by **procedural** PBR node
    groups, not image textures — keeping the GLB small and yielding a printable finish
    schedule the crew can read.
  - The work is cut into seven independently judged pieces: interior joinery defects,
    materials and finish schedule, opening subdivision, facade elements, party walls and
    alley, interior realism and furniture, viewer crew tools.
  - The measurable exit gate is elevation-overlay parity in millimetres — which also closes
    the repository's largest test hole.
  - The sun stays decorative and is only lit better; no solar model, no `north_deg`.
  - Two viewer builds — a decimated light build for a phone on mobile data, a full-detail
    build for a laptop — which removes the 8 MiB inline ceiling as a design constraint.
- From `research/2026-08-13_contractor-scheme-3d-render-brainstorm.md`:
  - Blender 4.1 legacy EEVEE is the only working render path on the target machine. EEVEE
    Next (Blender 4.2+) renders every lit surface blood red on its Intel UHD 620 (a white
    wall comes out RGB 194,34,53) and Cycles enumerates zero GPU devices, leaving CPU-only
    rendering at roughly 169 s per view against roughly 30 s per view on legacy EEVEE.
  - The printed dimension chains on the contractor's sheets are the authoritative source,
    read at 8–24× zoom; vector measurement is only a cross-check. Every departure from the
    sheets is recorded in `designs/contractor-as-drawn.fidelity.md`.
  - Every schema object sets `additionalProperties: false`, so no provenance, annotation or
    drawing reference can live inside the spec — hence the two markdown sidecars.
  - Storey heights come from Section A-A's level tags: 3800 / 3200 / 3400 / 3400 / 3400 /
    3400 / 3200 mm, totalling 23800 mm, matching the sheet's `+23.800`.

## Assumptions and Constraints

- **ASM-001:** The `MẶT ĐỨNG CHÍNH` elevation sheet (`contractor/MB MAI - MD.pdf`,
  rasterised in `output/contractor_pdf_png/MB_MAI_-_MD-Model.png`) carries resolvable facade
  detail — fin positions, band heights, panel divisions, railing pattern. — **BINDING
  DEFAULT:** read what is resolvable at 8–24× zoom and author only that. Any facade element
  that cannot be read to within ±50 mm is **not** modelled; it is added as a new open item in
  `designs/contractor-as-drawn.fidelity.md`. Do not invent facade detail.
- **ASM-002:** The plot's street address and true north are unknown, and the compass glyph on
  `contractor/approval drawing.jpg` is unreadable. — **BINDING DEFAULT:** do not set
  `site.north_deg`. Model the alley from the site plan on the contractor's sheets; where the
  sheets do not give a figure, use alley carriageway width 4000 mm, kerb height 150 mm,
  kerb width 300 mm, and opposite-side massing 12000 mm high × 8000 mm deep running the full
  frontage. Record all four figures as an approximation in the fidelity ledger.
- **ASM-003:** Neighbour massing heights are not given on the sheets. — **BINDING DEFAULT:**
  west neighbour 14000 mm high, east neighbour 10500 mm high, both 4000 mm wide (matching
  the existing `NEIGHBOUR_WIDTH_MM = 3000.0` is *not* required; widen it to 4000 mm) and
  20000 mm deep, both hard against the plot boundary with zero gap so the party-wall
  condition is visible. Ledger as an approximation.
- **ASM-004:** The elevation-overlay parity tolerance is not fixed by any existing document.
  — **BINDING DEFAULT:** ±50 mm on silhouette edges and on opening edge positions, measured
  at sheet scale. Known deliberate deviations are excluded by name inside the test, never by
  widening the tolerance.
- **ASM-005:** Furniture asset sourcing is unspecified. — **BINDING DEFAULT:** improve the
  existing procedural builders in `src/homedesign/blender/procedural_furniture.py` only. Do
  **not** download or import third-party 3D assets: they carry licence terms, unbounded
  polygon counts and image textures, all three of which the procedural-materials decision was
  arranged to avoid.
- **ASM-006:** GLB size budgets are not currently enforced anywhere. — **BINDING DEFAULT:**
  the light build must be ≤ 6 MiB and the full build ≤ 25 MiB, both asserted by an automated
  test. The 6 MiB figure leaves headroom under the 8 MiB base64 inline ceiling, because
  base64url encoding inflates the payload by roughly 4/3.
- **ASM-007:** Whether the viewer receives baked lighting is unresolved. — **BINDING
  DEFAULT:** bake ambient occlusion into **vertex colours** (not textures) for both builds,
  and export them in the GLB. Vertex colours cost bytes proportional to vertex count rather
  than to texture resolution, so the budgets in ASM-006 remain achievable.
- **ASM-008:** The target branch for the final commit is unspecified. — **BINDING DEFAULT:**
  commit and push to `master`, which is this repository's established pattern — every recent
  commit including `254dccf`, `db913c5` and `8e79dff` landed there directly.
- **ASM-009:** The chat channel used to share images imposes an unknown size limit. —
  **BINDING DEFAULT:** generate the image pack at 1600 px on the long edge, JPEG quality 85,
  each file under 1 MB, with the view name and the level tag burned into a caption bar at the
  foot of the image.
- **CON-001:** **Blender 4.1 legacy EEVEE only.** `orchestrator._CANDIDATES` deliberately
  orders Blender 4.1 ahead of 4.2+, and `tests/test_blender_candidates_prefer_legacy_eevee_build`
  pins that ordering. Do not modify `_CANDIDATES`. No EEVEE Next, no ray tracing, no
  screen-space global illumination, no GPU Cycles.
- **CON-002:** `additionalProperties: false` on every object in `spec/homespec.schema.json`.
  Nothing can be annotated or referenced back to a sheet from inside a spec; provenance lives
  in `designs/contractor-as-drawn.measurements.md` and `designs/contractor-as-drawn.fidelity.md`.
- **CON-003:** Any schema addition changes `model_hash`, which makes every existing render
  sidecar stale and causes `publish.verify_fresh` to block. A full re-render and re-publish is
  mandatory, not optional, and is scheduled as PHASE-06.
- **CON-004:** `viewer._load_call` inlines the GLB as base64url only up to
  `INLINE_GLB_LIMIT_BYTES = 8 * 1024 * 1024`, and then **silently** falls back to a relative
  file reference that breaks in a published single-file artifact. The silence is the hazard.
- **CON-005:** CI never installs `bpy`. Every fidelity assertion that must run in CI has to be
  expressible against the compiled model or against SVG/DXF text, not against a rendered scene.
- **CON-006:** The compiled model is consumed identically by `plan2d.py`, `elevation.py`,
  `pdf.py` and `blender/build_scene.py`. That single source is the 2D/3D parity guarantee;
  new geometry must enter through it.
- **CON-007:** Closed room-type enum, rectangular plot, axis-aligned walls only, the
  `check_room_support` cantilever limit, one stair object per storey, and roof `voids` valid
  only on `type: "flat"`.
- **DEC-001:** The dual bar is fixed: the contractor's `MẶT ĐỨNG CHÍNH` elevation for
  geometry, and the published photography of Vo Trong Nghia's "Stacking Green", Ho Chi Minh
  City, for material, light and scale.
- **DEC-002:** Finishes are procedural node groups driven by a new `finishes` block in the
  schema. No image textures.
- **DEC-003:** Facade elements become a first-class `facade_elements[]` construct authored
  from the elevation sheet, so that `elevation.py` can draw them too and 2D/3D parity holds.
  They are not a per-design Blender hook script.
- **DEC-004:** The sun stays decorative. Re-tune angle, energy and interior fill only; renders
  must continue to carry the ledger's statement that shadows are not a daylight analysis.
- **DEC-005:** Party walls and the alley are built; street entourage is not.
- **DEC-006:** Two viewer builds, light and full, each labelled unmistakably in the viewer
  chrome so the crew cannot mistake one for the other.
- **DEC-007:** The viewer gains all four crew tools: Vietnamese room labels with level tags in
  3D, a two-point measurement readout, a section/clipping-plane slider, and layer toggles for
  structure, walls, openings and furniture.
- **DEC-008:** EEVEE only, at the `final` profile, for every image that reaches the crew.

## Specification

### S1 — Elevation-overlay parity metric

The parity test compares two silhouettes of the same building, both expressed in millimetres
in the elevation's own 2D coordinate system, and never renders anything.

Let the south elevation produced by `elevation.build_elevation(model, "south")` be the
reference set `R`, and the orthographic projection of the compiled 3D geometry onto the same
plane be the candidate set `C`. Both are sets of axis-aligned rectangles
`(x_mm, y_mm, w_mm, h_mm)`.

1. **Silhouette bounds.** For a set `S`, define

   `bounds(S) = (min_x, min_y, max_x, max_y)` where
   `min_x = min over s in S of s.x_mm`,
   `min_y = min over s in S of s.y_mm`,
   `max_x = max over s in S of (s.x_mm + s.w_mm)`,
   `max_y = max over s in S of (s.y_mm + s.h_mm)`.

   Plain English: the tightest box that contains every rectangle in the set.

2. **Silhouette deviation.**

   `dev_silhouette = max( |min_x_R - min_x_C|, |min_y_R - min_y_C|, |max_x_R - max_x_C|, |max_y_R - max_y_C| )`

   Plain English: the largest single-edge disagreement, in millimetres, between the two
   outlines. It must be ≤ `TOLERANCE_MM` (50, per ASM-004).

3. **Opening-edge deviation.** For every opening `o` on a south-facing wall, take its
   projected left edge `x_l`, right edge `x_r`, sill `y_s` and head `y_h` from each set,
   matched by the opening's stable identifier `(wall_id, offset_mm)`. Then

   `dev_opening = max over all matched openings o of max( |x_l_R - x_l_C|, |x_r_R - x_r_C|, |y_s_R - y_s_C|, |y_h_R - y_h_C| )`

   Plain English: the worst disagreement, in millimetres, on any window or door edge. It must
   be ≤ `TOLERANCE_MM`.

4. **Coverage.** `count(R_openings)` must equal `count(C_openings)`. An unmatched opening on
   either side is a failure regardless of deviation — it means one pipeline knows about an
   opening the other does not.

5. **Excluded deviations.** The three accepted drawing deviations are excluded by name inside
   the test body, as an explicit list of opening or wall identifiers with a comment naming the
   fidelity-ledger item (a, c, g). They are never accommodated by raising `TOLERANCE_MM`.

### S2 — Facade element placement

A `facade_elements[]` entry is resolved to geometry by these numbered steps. All inputs are
millimetres; the Blender layer divides by 1000 at the boundary.

1. Read `side` (one of `north`, `south`, `east`, `west`). This selects the wall plane, using
   the same axis convention as `elevation._view_axes`.
2. Read `kind`: `fin` (vertical projecting blade), `band` (horizontal projecting course),
   `panel` (recessed or proud rectangular field), or `awning` (sloped projecting plane).
3. Read `x_mm` and `z_mm` as the element's origin, measured from the plot origin along the
   facade and from ground datum `0.000` upward respectively.
4. Read `w_mm`, `h_mm`, `projection_mm` — width along the facade, height, and how far the
   element stands proud of the wall face. A `panel` with negative `projection_mm` is recessed.
5. Read optional `storey_level`. When present the element's `z_mm` is interpreted as relative
   to that storey's `base_z`; when absent it is absolute from ground datum.
6. Read optional `finish` — a key into the `finishes` block (S3). When absent, `kind`
   determines the default finish key: `fin` and `band` use `facade_trim`, `panel` uses
   `facade_field`, `awning` uses `metal_sheet`.
7. Emit one box per element in 3D, and one filled rectangle per element in the elevation SVG
   and DXF, both derived from the same pure resolver so the two cannot disagree.

### S3 — Finish resolution order

For any surface, the finish key is resolved by taking the **first** rule that matches:

1. An explicit `finish` field on the individual object (an opening, a facade element, a room).
2. `finishes.overrides[<object_id>]` — an explicit per-object override in the spec.
3. `finishes.by_room_type[<room_type>]` for floors and wall faces inside a room.
4. `finishes.by_element[<element_kind>]` — the element-kind default (`wall`, `floor`,
   `ceiling`, `parapet`, `frame`, `glass`, `leaf`, `neighbour`, `street`, `ground`).
5. The existing hardcoded `PALETTES["modern-minimal"]` entry for that key.

Rule 5 guarantees that a spec with no `finishes` block renders exactly as it does today, so
`designs/tubehouse-dream.json` and every fixture in `spec/examples/` are unaffected.

## Phase Summary

| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Fix the joinery and furniture-clipping defects; build the elevation-overlay parity harness | None | `src/homedesign/parity.py`, `tests/test_parity.py`, corrected `joinery.py` and `placement.py` |
| PHASE-02 | Add the `finishes` schema block and procedural PBR materials; emit a finish schedule | PHASE-01 | Schema `finishes` block, `src/homedesign/finishes.py`, `blender/materials.py` node groups, finish-schedule SVG |
| PHASE-03 | Subdivide openings, pattern the railings, and add the `facade_elements[]` construct | PHASE-02 | Schema `openings.divisions` and `facade_elements[]`, `src/homedesign/facade.py`, updated `joinery.py`, `railings.py`, `elevation.py` |
| PHASE-04 | Build party walls and the alley; re-tune the light rig | PHASE-01 | `site.context` extensions, rewritten `_add_neighbour_massing` and `build_environment`, retuned `add_interior_lights` |
| PHASE-05 | Credible interiors and the two-build viewer with crew tools | PHASE-02, PHASE-04 | Upgraded `procedural_furniture.py`, `viewer.py` dual builds, viewer template with labels/measure/section/layers |
| PHASE-06 | Final build, three-channel delivery, HTML report, commit and push | PHASE-03, PHASE-05 | Re-rendered gallery, republished `deliverables/` and `docs/`, Pages workflow, A3 plates, image pack, `reports/2026-08-29-render-fidelity-report.html`, pushed commit |

## Detailed Phases

### PHASE-01 - Defect Fixes and the Parity Harness

**Goal**
Eliminate the two visible correctness bugs, and build the millimetre parity measurement that
every later phase is gated on. Nothing in this phase changes how the building looks by design
— it changes how wrong it is allowed to be.

**Tasks**
- [x] TASK-01-01: Reproduce the detached door leaf. Open
  `deliverables/contractor-as-drawn/png/contractor-as-drawn_khach.png` and confirm the leaf
  renders separated from its frame. Then read
  `src/homedesign/blender/joinery.py::build_opening_furniture` and determine whether the leaf
  origin is placed on the wall centreline while the frame is placed on the wall face, or vice
  versa. The wall thickness is available from the `wall_mm` argument.
- [x] TASK-01-02: Fix the leaf placement so the hinge edge coincides with the frame's inner
  jamb face on the hinge side, and the leaf plane sits within the frame depth
  (`FRAME_DEPTH = 0.06` m). Keep `DOOR_LEAF_THICKNESS = 0.045` m unchanged.
- [x] TASK-01-03: Fix furniture interpenetration. In `src/homedesign/placement.py`, add a
  post-placement pass that rejects or shifts any `FurnitureItem` whose footprint rectangle
  overlaps another item's footprint, or whose footprint overlaps the swing arc of a door in
  that room. Preserve the existing `CLEARANCE_M = 0.6` walkway rule.
- [x] TASK-01-04: Create `src/homedesign/parity.py` implementing the S1 metric as pure
  functions over the compiled model. It must not import `bpy`.
- [x] TASK-01-05: Create `tests/test_parity.py` asserting the S1 metric against
  `designs/contractor-as-drawn.json`, with `TOLERANCE_MM = 50.0` and the three excluded
  deviations listed by identifier with a comment naming their fidelity-ledger item.
- [x] TASK-01-06: Add furniture-overlap and door-swing-clearance assertions to
  `tests/test_placement.py` (create the file if it does not exist).

**File Changes**
- `src/homedesign/blender/joinery.py` (modify): correct the door-leaf origin so the leaf sits
  inside the frame. Leave `FRAME_DEPTH`, `FRAME_WIDTH`, `GLASS_THICKNESS` and
  `DOOR_LEAF_THICKNESS` at their current values; leave the window path untouched.
- `src/homedesign/placement.py` (modify): add `resolve_collisions` and call it at the end of
  `plan_room` before returning. Leave the per-room-type planners' layout intent unchanged —
  they may shift items, never delete a bed, sofa, kitchen run or car.
- `src/homedesign/parity.py` (create): the S1 metric.
- `tests/test_parity.py` (create): the parity assertions.
- `tests/test_placement.py` (create): furniture-overlap assertions.

**Function Signatures**
- `silhouette_bounds(rects: list[dict]) -> tuple[float, float, float, float]` — returns
  `(min_x_mm, min_y_mm, max_x_mm, max_y_mm)` covering every rectangle in the list.
- `silhouette_deviation(reference: list[dict], candidate: list[dict]) -> float` — returns the
  largest single-edge disagreement in millimetres between the two silhouettes.
- `opening_deviation(reference: list[dict], candidate: list[dict], exclude: set[str]) -> tuple[float, list[str]]`
  — returns `(worst_deviation_mm, unmatched_opening_ids)`; identifiers in `exclude` are
  skipped entirely.
- `elevation_parity_report(model: CompiledModel, side: str, tolerance_mm: float = 50.0, exclude: set[str] | None = None) -> dict`
  — returns `{"side": str, "silhouette_mm": float, "opening_mm": float, "unmatched": list[str], "passed": bool}`.
- `resolve_collisions(items: list[FurnitureItem], room_w_m: float, room_d_m: float, door_swings: list[tuple[float, float, float, float]]) -> list[FurnitureItem]`
  — returns the same items with overlapping footprints shifted apart, preserving list order
  and length.

**Test Specs**
- `silhouette_bounds([{"x_mm": 0, "y_mm": 0, "w_mm": 3960, "h_mm": 23800}])` → `(0.0, 0.0, 3960.0, 23800.0)`.
- `silhouette_deviation(R, R)` for any non-empty `R` → `0.0`.
- `silhouette_deviation([{"x_mm": 0, "y_mm": 0, "w_mm": 1000, "h_mm": 1000}], [{"x_mm": 0, "y_mm": 0, "w_mm": 1040, "h_mm": 1000}])` → `40.0`.
- `elevation_parity_report(compile("designs/contractor-as-drawn.json"), "south")` →
  `passed` is `True`, `silhouette_mm` ≤ `50.0`, `opening_mm` ≤ `50.0`, `unmatched` is `[]`.
- Empty candidate set → raises `ValueError` with a message naming the side, rather than
  returning a passing report.
- An opening present in the reference but absent from the candidate → `passed` is `False` and
  its identifier appears in `unmatched`, even when both deviation figures are `0.0`.
- For a 3000 mm × 3000 mm living room, `plan_room("living", 3.0, 3.0)` → every returned
  `FurnitureItem` footprint is pairwise non-overlapping, and the returned list length equals
  the length returned before `resolve_collisions` was introduced.
- A room too small to place its planned items without overlap → items are shifted to touch but
  not overlap; the function never returns fewer items than it was given.

**Dependencies**
- None.

**Exit Criteria**
- [ ] `python -m pytest tests/test_parity.py tests/test_placement.py -q` passes.
- [ ] `python -m pytest tests -q` passes with no fewer tests than before and no new failures.
- [ ] `ruff check src tests` reports no findings.
- [ ] A re-render of the single view `khach` shows the door leaf inside its frame and no
  furniture interpenetration.

**Phase Risks**
- **RISK-01-01:** The parity metric fails on first run because of a pre-existing 2D/3D
  disagreement rather than a defect introduced here. Mitigation: run
  `elevation_parity_report` before changing anything, record the baseline figures in the
  commit message, and treat any pre-existing failure as a new fidelity-ledger item rather than
  silently widening the tolerance.
- **RISK-01-02:** Shifting furniture changes the 2D plan drawings, because
  `plan2d._svg_furniture` and `blender/furnish` share `placement.plan_room`. Mitigation: this
  is intended — but re-run `python -m pytest tests/test_plan2d.py -q` and expect furniture
  coordinate assertions to need updating in step with the fix.

### PHASE-02 - Finish Schedule and Procedural Materials

**Goal**
Give the spec a vocabulary for what surfaces are made of, render it with procedural PBR node
groups, and print it as a finish schedule the crew can read.

**Tasks**
- [x] TASK-02-01: Add a `finishes` object to `spec/homespec.schema.json` as a fourth
  top-level property alongside `meta`, `site` and `storeys`, with
  `additionalProperties: false` and sub-objects `by_element`, `by_room_type` and `overrides`,
  each mapping a string key to a finish name. Add an optional `finish` string property to the
  opening object and to the room object.
- [x] TASK-02-02: Create `src/homedesign/finishes.py` implementing the S3 resolution order as
  pure functions. It must not import `bpy`.
- [x] TASK-02-03: Extend `src/homedesign/model.py` so `CompiledModel` carries the resolved
  finish map. Confirm `model_hash` changes as a result — that is expected and is handled in
  PHASE-06.
- [x] TASK-02-04: In `src/homedesign/blender/materials.py`, add procedural node-group builders
  for the finish families: `plaster_painted`, `ceramic_tile`, `stone_slab`, `wood_board`,
  `metal_brushed`, `glass_clear`, `concrete_formed`. Each takes a base colour, a roughness and
  a scale in millimetres, and builds nodes producing surface variation — grout grids for tile,
  noise for plaster and concrete, anisotropic streaking for metal, grain for wood.
- [x] TASK-02-05: Rewire `get_material(style, key)` to consult the resolved finish map first
  and fall back to `PALETTES` (S3 rule 5) so specs without a `finishes` block are unchanged.
- [x] TASK-02-06: Author the `finishes` block in `designs/contractor-as-drawn.json` using
  ordinary Vietnamese domestic construction finishes: painted plaster walls, ceramic floor
  tile in habitable rooms, non-slip tile in wet rooms, aluminium-framed glazing, painted metal
  railings, formed concrete for the stair and parapet edges.
- [x] TASK-02-07: Emit a finish schedule as an SVG sheet from the same resolved map, written
  to `output/svg/<model>_finishes.svg`, listing element, location, finish name and colour swatch.
- [x] TASK-02-08: Verify the procedural materials survive glTF export by exporting and
  re-reading the GLB, confirming the material count and that no material has an image texture.

**File Changes**
- `spec/homespec.schema.json` (modify): add the top-level `finishes` object and the optional
  `finish` field on openings and rooms. Leave `meta.style` as a single-value enum, and leave
  every existing `additionalProperties: false` in place.
- `src/homedesign/finishes.py` (create): S3 resolution.
- `src/homedesign/model.py` (modify): add the finish map to `CompiledModel` and include it in
  `model_hash`. Leave the existing dataclass field names untouched.
- `src/homedesign/compiler.py` (modify): resolve finishes during `compile_spec`. Leave wall
  derivation and `_derive_floor_voids` untouched.
- `src/homedesign/blender/materials.py` (modify): add the procedural node-group builders and
  the finish-map lookup in `get_material`. Keep `PALETTES` as the fallback.
- `src/homedesign/plan2d.py` (modify): add the finish-schedule SVG writer. Leave every
  existing plan-drawing helper untouched.
- `designs/contractor-as-drawn.json` (modify): add the `finishes` block. Change nothing else.
- `tests/test_finishes.py` (create): resolution-order assertions.
- `tests/test_validate.py` (modify): assert the amended schema accepts a spec with a
  `finishes` block and rejects an unknown key inside it.

**Function Signatures**
- `resolve_finish(object_id: str, element_kind: str, room_type: str | None, explicit: str | None, finishes: dict) -> str`
  — returns the finish name selected by the S3 order, falling back to `element_kind`.
- `build_finish_map(spec: dict) -> dict[str, str]` — returns a mapping from stable object
  identifier to resolved finish name for every surface-bearing object in the spec.
- `finish_schedule_rows(model: CompiledModel) -> list[dict]` — returns one row per distinct
  (finish, element kind, location) triple, sorted by element kind then location.
- `make_procedural_material(name: str, family: str, base_color: tuple[float, float, float], roughness: float, scale_mm: float) -> "bpy.types.Material"`
  — returns a Blender material whose node tree implements the named procedural family.

**Test Specs**
- `resolve_finish("room_khach", "floor", "living", None, {"by_room_type": {"living": "wood_board"}, "by_element": {"floor": "ceramic_tile"}})` → `"wood_board"` (rule 3 beats rule 4).
- `resolve_finish("room_khach", "floor", "living", "stone_slab", {...})` → `"stone_slab"` (rule 1 beats everything).
- `resolve_finish("room_wc", "floor", "bathroom", None, {})` → `"floor"`, the element-kind key,
  which `PALETTES` then resolves exactly as today (rule 5).
- `build_finish_map(json.load(open("spec/examples/tubehouse-mini.json", encoding="utf-8")))` →
  every value equals its element-kind key, proving a spec with no `finishes` block is unchanged.
- Compiling a spec with `finishes.by_element.wall = "not_a_family"` → raises a validation error
  naming the unknown finish family, not a `KeyError` at render time.
- `model_hash` of `designs/contractor-as-drawn.json` before and after adding the `finishes`
  block → differs. Record both values in the commit message.
- Exported GLB → material count ≥ 7 and no material references an image texture.

**Dependencies**
- PHASE-01 (the parity harness must be green before the model hash moves).

**Exit Criteria**
- [ ] `python -m pytest tests -q` passes.
- [ ] `homedesign compile designs/contractor-as-drawn.json` succeeds and the compiled model
  contains a non-empty finish map.
- [ ] `output/svg/contractor-as-drawn_finishes.svg` exists and lists at least one row per
  finish family used.
- [ ] `python -m pytest tests/test_parity.py -q` still passes — materials must not move geometry.

**Phase Risks**
- **RISK-02-01:** Procedural node groups have no glTF representation and will export as flat
  base colours, silently undoing the work in the viewer channel. Mitigation: TASK-02-08 tests
  this explicitly in this phase rather than discovering it in PHASE-06; if variation is lost,
  bake each procedural material to a single small texture at export time only, keeping the
  Blender-side node group as the source of truth.
- **RISK-02-02:** `model_hash` changes, so `homedesign publish` will refuse to run until
  PHASE-06 re-renders. Mitigation: expected and scheduled; do not work around it with a force
  flag mid-plan.

### PHASE-03 - Facade Articulation

**Goal**
Make the building read as *this* building rather than as a rectangular prism: subdivided
openings, the drawn railing pattern, and the fins, bands and panels on the contractor's
elevation. Treat "openings read as real windows" and "the facade reads as this building" as
two separately judged pieces — get the first fully right before starting the second.

**Tasks**
- [x] TASK-03-01: Add an optional `divisions` object to the opening schema with integer
  `columns` (default 1), integer `rows` (default 1), `mullion_mm` (default 50) and
  `transom_mm` (default 50).
- [x] TASK-03-02: Extend `src/homedesign/blender/joinery.py::build_opening_furniture` to emit
  mullions and transoms subdividing the glazed area according to `divisions`. A 1 × 1 division
  must produce byte-identical geometry to today's output.
- [x] TASK-03-03: Extend `src/homedesign/elevation.py::build_elevation` to draw the same
  subdivision lines, driven by the same pure resolver as the 3D path.
- [x] TASK-03-04: Add a `pattern` field to the balcony parapet path with values `solid`
  (today's behaviour, the default) and `slatted` (vertical bars at a stated pitch). Implement
  `slatted` in `src/homedesign/blender/railings.py::build_parapet`.
- [x] TASK-03-05: Read `output/contractor_pdf_png/MB_MAI_-_MD-Model.png` at 8–24× zoom and
  record every resolvable facade element — fins, bands, panels, awnings — with its `x_mm`,
  `z_mm`, `w_mm`, `h_mm` and `projection_mm`, appending the readings to
  `designs/contractor-as-drawn.measurements.md` as rev.4 with the sheet name and zoom level
  for each figure. Apply ASM-001 to anything unreadable.
- [x] TASK-03-06: Add the `facade_elements[]` array to the storey schema object per S2, and
  create `src/homedesign/facade.py` resolving entries to rectangles in both the 3D and
  elevation coordinate systems.
- [x] TASK-03-07: Emit facade elements in `build_scene.py` and in `elevation.py` from the same
  resolver.
- [x] TASK-03-08: Author the measured facade elements into `designs/contractor-as-drawn.json`
  and the opening `divisions` read from the same sheet.
- [x] TASK-03-09: Update `designs/contractor-as-drawn.fidelity.md` to rev.4, closing ledger
  items k (facade articulation), l (undivided openings) and m (plain parapets), and adding any
  new open item created by ASM-001.

**File Changes**
- `spec/homespec.schema.json` (modify): add `openings[].divisions`, the parapet `pattern`
  field, and `storeys[].facade_elements[]`. Preserve every `additionalProperties: false`.
- `src/homedesign/facade.py` (create): the S2 resolver.
- `src/homedesign/blender/joinery.py` (modify): mullion and transom emission. Leave the frame
  and leaf geometry from PHASE-01 untouched.
- `src/homedesign/blender/railings.py` (modify): the `slatted` pattern in `build_parapet`.
  Leave `build_balustrade` untouched.
- `src/homedesign/blender/build_scene.py` (modify): call the facade resolver and emit boxes.
  Leave `build_walls`, `build_floors_and_stairs` and the camera functions untouched.
- `src/homedesign/elevation.py` (modify): draw facade elements and opening subdivisions in
  `build_elevation`, and include them in `_svg` and `_dxf` output. Leave `build_section`
  untouched.
- `designs/contractor-as-drawn.json` (modify): add `facade_elements[]` and opening `divisions`.
- `designs/contractor-as-drawn.measurements.md` (modify): rev.4 with the facade readings.
- `designs/contractor-as-drawn.fidelity.md` (modify): rev.4 closing items k, l and m.
- `tests/test_facade.py` (create): resolver assertions.
- `tests/test_elevation.py` (modify): assert facade elements and subdivisions appear in the
  elevation SVG.

**Function Signatures**
- `resolve_facade_element(element: dict, storey_base_z_mm: float, plot_width_mm: float, plot_depth_mm: float) -> dict`
  — returns `{"x_mm", "y_mm", "z_mm", "w_mm", "d_mm", "h_mm", "finish"}` in the 3D coordinate
  system.
- `facade_element_elevation_rect(element: dict, side: str, storey_base_z_mm: float) -> dict | None`
  — returns `{"x_mm", "y_mm", "w_mm", "h_mm", "finish"}` for the elevation drawing, or `None`
  when the element does not face `side`.
- `opening_division_lines(opening_w_mm: float, opening_h_mm: float, divisions: dict) -> list[dict]`
  — returns one rectangle per mullion and transom, in opening-local millimetre coordinates.

**Test Specs**
- `opening_division_lines(2000.0, 1400.0, {"columns": 1, "rows": 1, "mullion_mm": 50, "transom_mm": 50})` → `[]`.
- `opening_division_lines(2000.0, 1400.0, {"columns": 2, "rows": 1, "mullion_mm": 50, "transom_mm": 50})` →
  one rectangle, centred, `x_mm == 975.0`, `w_mm == 50.0`, `h_mm == 1400.0`.
- `opening_division_lines(2000.0, 1400.0, {"columns": 3, "rows": 2, "mullion_mm": 50, "transom_mm": 50})` →
  three rectangles: two vertical mullions and one horizontal transom.
- `resolve_facade_element({"kind": "fin", "side": "south", "x_mm": 500, "z_mm": 3800, "w_mm": 200, "h_mm": 3400, "projection_mm": 300}, 0.0, 3960.0, 25000.0)`
  → `d_mm == 300.0` and the element's `y_mm` places it proud of the south wall face, outside
  the plot depth range.
- `facade_element_elevation_rect(<a south fin>, "north", 0.0)` → `None`.
- A spec whose `facade_elements[]` is absent → the elevation SVG is byte-identical to the one
  produced before this phase.
- `python -m pytest tests/test_parity.py -q` → still passes after facade elements are authored,
  because both pipelines draw them from the same resolver.

**Dependencies**
- PHASE-02 (facade elements carry a `finish`).

**Exit Criteria**
- [ ] `python -m pytest tests -q` passes.
- [ ] The rendered `exterior_front` view shows fins, bands and panels matching the positions
  recorded in `designs/contractor-as-drawn.measurements.md` rev.4.
- [ ] The south elevation SVG shows the same elements at the same coordinates.
- [ ] `python -m pytest tests/test_parity.py -q` passes with the tolerance unchanged at 50 mm.
- [ ] `designs/contractor-as-drawn.fidelity.md` is at rev.4 with items k, l and m closed.

**Phase Risks**
- **RISK-03-01:** Facade elements projecting beyond the plot boundary may trip
  `check_room_support` or a setback check. Mitigation: facade elements are not rooms; keep them
  out of the room-support computation entirely, and add an explicit test that a 300 mm fin does
  not alter any check result.
- **RISK-03-02:** Reading the elevation sheet is the slowest task in the plan and is easy to
  rush. Mitigation: ASM-001 is binding — an unreadable element is ledgered, never guessed.

### PHASE-04 - Site Context and Lighting

**Goal**
Put the building on its actual street. Party walls hard against both flanks, a real alley in
front, no lawn — and an interior light rig that gives rooms modelling instead of white blowout.

**Tasks**
- [x] TASK-04-01: Set `site.context.neighbours` to `true` in `designs/contractor-as-drawn.json`.
  It is currently `false`, which is the direct reason no neighbours appear in the published
  render.
- [x] TASK-04-02: Extend the `site.context` schema object with `alley_width_mm`,
  `kerb_height_mm`, `kerb_width_mm`, `opposite_height_mm`, `opposite_depth_mm`,
  `neighbour_west_height_mm`, `neighbour_east_height_mm`, `neighbour_width_mm` and
  `neighbour_depth_mm`, all optional numbers. Preserve `additionalProperties: false`.
- [x] TASK-04-03: Rewrite `build_scene._add_neighbour_massing` to use those fields with the
  ASM-002 and ASM-003 defaults, replacing the current behaviour of two blocks whose height is
  the full building height and whose width is the fixed `NEIGHBOUR_WIDTH_MM = 3000.0`.
- [x] TASK-04-04: Rewrite `build_scene.build_environment` so the ground is an alley section
  rather than a green pad: carriageway, kerb, and opposite-side massing, all using finishes
  resolved through PHASE-02. Remove the 15 m green pad.
- [x] TASK-04-05: Re-tune the sun in `build_environment`: keep the fixed 55° / 35° angle per
  DEC-004, but adjust energy and add a sky-facing gradient so the facade receives directional
  modelling. Do not add a solar model.
- [x] TASK-04-06: Re-tune `add_interior_lights`. The current formula
  `clamp(area_m2 * 2.2, 20, 90)` blows walls to white. Replace it with a formula that scales
  with room area and room height, and add a low-energy bounce plane so ceilings are not black.
- [x] TASK-04-07: Author the alley figures into `designs/contractor-as-drawn.json` from the
  site plan on the contractor's sheets, falling back to the ASM-002 defaults where the sheets
  are silent, and record which figures were defaults in `designs/contractor-as-drawn.fidelity.md`.

**File Changes**
- `spec/homespec.schema.json` (modify): extend `site.context` with the nine optional fields.
- `src/homedesign/blender/build_scene.py` (modify): rewrite `_add_neighbour_massing` and
  `build_environment`, and re-tune `add_interior_lights`. Leave `_neighbours_enabled`'s
  fallback rule (`plot_width_mm <= 6000`) intact, and leave every camera function untouched.
- `src/homedesign/site_context.py` (create): pure resolution of context figures to boxes, so
  the values are testable without `bpy`.
- `designs/contractor-as-drawn.json` (modify): set `neighbours: true` and add the alley figures.
- `designs/contractor-as-drawn.fidelity.md` (modify): record which context figures are defaults.
- `tests/test_site_context.py` (create): context resolution assertions.

**Function Signatures**
- `resolve_context_boxes(site: dict, total_height_mm: float) -> list[dict]` — returns one
  dictionary per context solid (`neighbour_west`, `neighbour_east`, `carriageway`, `kerb`,
  `opposite`), each with `{"name", "x_mm", "y_mm", "z_mm", "w_mm", "d_mm", "h_mm", "finish"}`.
- `interior_light_energy(area_m2: float, height_m: float) -> float` — returns the area-light
  energy in watts for a room of that floor area and storey height.

**Test Specs**
- `resolve_context_boxes({"plot_width_mm": 3960, "plot_depth_mm": 25000, "context": {"neighbours": True}}, 23800.0)`
  → contains a box named `neighbour_west` with `h_mm == 14000.0` and `w_mm == 4000.0`, and one
  named `neighbour_east` with `h_mm == 10500.0` (the ASM-003 defaults).
- Both neighbour boxes are flush against the plot: `neighbour_west.x_mm + neighbour_west.w_mm == 0.0`
  and `neighbour_east.x_mm == 3960.0`.
- `resolve_context_boxes` with `context.neighbours` set to `False` → returns only the
  carriageway and kerb, no neighbour boxes.
- No returned box has a name containing `ground` or a finish resolving to a green colour — the
  lawn must be gone.
- `interior_light_energy(12.0, 3.4)` → a value strictly less than the current formula's
  `clamp(12.0 * 2.2, 20, 90) == 26.4` is *not* required, but the function must be monotonic:
  `interior_light_energy(24.0, 3.4) > interior_light_energy(12.0, 3.4)`.
- `interior_light_energy(2.0, 3.4)` → at least 8.0, so a small WC is never unlit.

**Dependencies**
- PHASE-01. Runs independently of PHASE-03 and may proceed in parallel with it.

**Exit Criteria**
- [ ] `python -m pytest tests -q` passes.
- [ ] The rendered `exterior_front` view shows the building hard against party walls on both
  flanks, standing on an alley, with no green ground anywhere in frame.
- [ ] The rendered `khach` view shows walls with visible tonal variation rather than a
  uniform white field.
- [ ] `python -m pytest tests/test_parity.py -q` still passes — context must not move the
  building.

**Phase Risks**
- **RISK-04-01:** Party walls flush against both flanks will occlude the exterior cameras.
  Mitigation: `_add_neighbour_massing` already deliberately omits the south side, which is
  where the front camera shoots from; verify the aerial camera still clears the neighbours
  after their heights change, and adjust `camera_fit` inputs rather than shrinking the
  neighbours.
- **RISK-04-02:** Re-tuning interior lights risks the opposite failure — rooms too dark to
  read. Mitigation: judge every one of the ten interior views, not one, before accepting the
  new formula.

### PHASE-05 - Interiors and the Two-Build Viewer

**Goal**
Make the interiors credible, and turn the viewer from a navigation toy into an instrument the
crew can measure, section and label with — in two builds sized for two very different devices.

**Tasks**
- [x] TASK-05-01: Upgrade the twelve builders in
  `src/homedesign/blender/procedural_furniture.py` from box primitives to credible geometry:
  bevelled edges, separated cushions and frames on seating, panelled doors on cabinetry, taps
  and cisterns on sanitaryware. Use procedural geometry only — do not import third-party assets
  (ASM-005).
- [x] TASK-05-02: Add architectural interior detail in `build_scene.py`: skirting, opening
  reveals following actual wall thickness, and a ceiling plane in every enclosed room rather
  than only on the top storey.
- [x] TASK-05-03: Bake ambient occlusion to vertex colours before glTF export and include the
  colour attribute in the export (ASM-007).
- [x] TASK-05-04: Add two build targets to `src/homedesign/viewer.py`: `light` (decimated,
  furniture excluded from the mesh budget where necessary, target ≤ 6 MiB) and `full`
  (everything, target ≤ 25 MiB). Make `optimize_glb`'s dependence on `npx` an explicit checked
  precondition that raises a clear error rather than silently returning `False`.
- [x] TASK-05-05: Add a visible build badge to both viewer templates reading `PHIÊN BẢN NHẸ —
  ĐIỆN THOẠI` for the light build and `PHIÊN BẢN ĐẦY ĐỦ — MÁY TÍNH` for the full build, so the
  two cannot be confused.
- [x] TASK-05-06: Add Vietnamese room labels and storey level tags as 3D sprites in the viewer,
  reading the room name and `+X.XXX` level string straight from the compiled model.
- [x] TASK-05-07: Add a two-point measurement tool: tap two surfaces, draw a line, display the
  distance in millimetres to the nearest 1 mm.
- [x] TASK-05-08: Add a section slider cutting the model on the Y axis (along the 25 m depth)
  and a second cutting on Z (height), implemented with three.js clipping planes.
- [x] TASK-05-09: Add layer toggles for structure, walls, openings and furniture, driven by
  object-name prefixes already emitted by `build_scene.py`.
- [x] TASK-05-10: Add a GLB size-budget test enforcing ASM-006.

**File Changes**
- `src/homedesign/blender/procedural_furniture.py` (modify): upgrade all twelve `_build_*`
  builders. Keep the `_BUILDERS` dictionary keys and the `build_item` signature unchanged.
- `src/homedesign/blender/build_scene.py` (modify): add skirting, reveals and per-room
  ceilings; add the vertex-colour AO bake before export. Leave the camera and render functions
  untouched.
- `src/homedesign/viewer.py` (modify): add the `light` and `full` build targets; make the `npx`
  dependency explicit. Keep `INLINE_GLB_LIMIT_BYTES` at its current value.
- `src/homedesign/assets/viewer_template.html` (modify): build badge, room labels, level tags,
  measurement tool, section sliders, layer toggles.
- `src/homedesign/assets/floor_viewer_template.html` (modify): build badge and layer toggles;
  the floor tabs already provide sectioning, so no section slider here.
- `tests/test_viewer.py` (modify, or create if absent): size-budget and build-target assertions.

**Function Signatures**
- `write_viewer(model_name: str, glb_path: Path, out_dir: Path, build: str = "full") -> Path`
  — returns the written HTML path; `build` is `"light"` or `"full"` and selects the badge text
  and the size budget.
- `glb_size_budget(build: str) -> int` — returns the byte budget: `6 * 1024 * 1024` for
  `"light"`, `25 * 1024 * 1024` for `"full"`.
- `assert_within_budget(glb_path: Path, build: str) -> None` — raises `ValueError` naming the
  actual and budgeted sizes when the file exceeds its budget; returns `None` otherwise.
- `room_label_data(model: CompiledModel) -> list[dict]` — returns
  `[{"text": str, "level_tag": str, "x_m": float, "y_m": float, "z_m": float}]`, one entry per
  room, with `text` the Vietnamese room name verbatim and `level_tag` formatted `+%.3f`.

**Test Specs**
- `glb_size_budget("light")` → `6291456`; `glb_size_budget("full")` → `26214400`.
- `assert_within_budget(<a 7 MiB file>, "light")` → raises `ValueError` whose message contains
  both `7` and `6`.
- `assert_within_budget(<a 7 MiB file>, "full")` → returns `None`.
- `room_label_data(compile("designs/contractor-as-drawn.json"))` → contains an entry with
  `text == "P.KHÁCH"`, and every `level_tag` matches the regular expression `^\+\d+\.\d{3}$`.
- A room at `base_z` 3800 mm → its `level_tag` is exactly `"+3.800"`.
- `write_viewer(..., build="light")` → the written HTML contains the string
  `PHIÊN BẢN NHẸ — ĐIỆN THOẠI`; with `build="full"` it contains `PHIÊN BẢN ĐẦY ĐỦ — MÁY TÍNH`.
- `optimize_glb` when `npx` is unavailable → raises an error naming `npx`, rather than
  returning `False`.

**Dependencies**
- PHASE-02 (materials must exist before AO baking is meaningful) and PHASE-04 (context
  geometry is part of the exported scene).

**Exit Criteria**
- [ ] `python -m pytest tests -q` passes.
- [ ] `output/viewer/contractor-as-drawn-light.html` is under 8 MiB on disk and its GLB is
  inlined, not referenced.
- [ ] `output/viewer/contractor-as-drawn-full.html` exists with the full-detail model.
- [ ] Opening either viewer file in a browser shows room labels, a working measurement readout,
  both section sliders, and four working layer toggles.
- [ ] `python -m pytest tests/test_parity.py -q` still passes.

**Phase Risks**
- **RISK-05-01:** Upgraded furniture geometry blows the light build's 6 MiB budget.
  Mitigation: the budget test fails the build rather than letting `_load_call` silently fall
  back to a broken relative reference; drop furniture from the light build before dropping the
  budget.
- **RISK-05-02:** Vietnamese diacritics may not render in the three.js sprite labels if the
  inlined font lacks the glyphs. Mitigation: verify `P.NGỦ`, `P.THỜ` and `SÂN THƯỢNG` render
  correctly before considering TASK-05-06 done; if glyphs are missing, render labels as HTML
  overlays positioned by projection rather than as texture sprites.

### PHASE-06 - Final Build, Delivery, Report and Push

**Goal**
Produce the final artifacts in one run, get them to the crew through all three channels, record
what was done in a self-contained HTML report, and land the work in version control.

**Tasks**
- [x] TASK-06-01: Run a clean full build of every view at the `final` profile with glTF export.
- [x] TASK-06-02: Run `homedesign publish` and confirm it no longer blocks — every render
  sidecar hash must match the new `model_hash`.
- [x] TASK-06-03: Copy the published viewer HTML files into `docs/` and update
  `docs/viewers.html` to link the light and full builds separately, labelled in Vietnamese.
- [x] TASK-06-04: Create `.github/workflows/pages.yml` deploying `docs/` to GitHub Pages on
  push to `master`, so the viewer link stops being a manual copy.
- [x] TASK-06-05: Generate the A3 plate set — the exterior views, the light-well view and the
  south elevation at A3 landscape, 300 dpi, each with a title block naming the model, the
  source sheet and the render date.
- [x] TASK-06-06: Generate the chat image pack per ASM-009 into
  `deliverables/contractor-as-drawn/share/`.
- [x] TASK-06-07: Write `reports/2026-08-29-render-fidelity-report.html` — a self-contained
  single file with all CSS and images inlined as data URIs, containing: before-and-after image
  pairs for the exterior and for at least three interiors; the parity report figures for every
  elevation side; the finish schedule; the list of fidelity-ledger items closed and opened; the
  GLB sizes against their budgets; and the render time.
- [x] TASK-06-08: Update `designs/contractor-as-drawn.fidelity.md` to its final revision and
  `activeContext.md` with a review section recording what shipped.
- [x] TASK-06-09: Commit and push per ASM-008.

**File Changes**
- `deliverables/contractor-as-drawn/` (modify): republished `png`, `gltf`, `viewer` and `pdf`.
- `deliverables/contractor-as-drawn/share/` (create): the chat image pack.
- `deliverables/contractor-as-drawn/a3/` (create): the A3 plate set.
- `docs/` (modify): synchronised viewer HTML files.
- `docs/viewers.html` (modify): links to both builds, labelled in Vietnamese.
- `.github/workflows/pages.yml` (create): the Pages deploy workflow.
- `reports/2026-08-29-render-fidelity-report.html` (create): the self-contained report.
- `designs/contractor-as-drawn.fidelity.md` (modify): final revision.
- `activeContext.md` (modify): append a review section.
- `scripts/make_share_pack.py` (create): generates the A3 plates and the chat image pack from
  `deliverables/contractor-as-drawn/png/` using Pillow, which is already a runtime dependency.

**Function Signatures**
- `make_a3_plate(png_path: Path, title: str, source_sheet: str, rendered_at: str, out_path: Path) -> Path`
  — returns the written A3 landscape plate path at 300 dpi (3508 × 2480 px).
- `make_share_image(png_path: Path, caption: str, out_path: Path, long_edge_px: int = 1600, quality: int = 85) -> Path`
  — returns the written JPEG path with the caption burned into a footer bar.

**Test Specs**
- `make_share_image(<a 1920x1080 png>, "P.KHÁCH +3.800", tmp_path / "out.jpg")` → the output
  file exists, its long edge is exactly 1600 px, and its size is under 1048576 bytes.
- `make_a3_plate(<any png>, "contractor-as-drawn", "MẶT ĐỨNG CHÍNH", "2026-08-29", tmp_path / "p.png")`
  → the output image is exactly 3508 × 2480 px.
- `reports/2026-08-29-render-fidelity-report.html` → contains no `src="http` and no
  `href="http` for any stylesheet or image, proving it is self-contained.
- `homedesign publish designs/contractor-as-drawn.json` → exits 0 and reports no stale sidecars.

**Dependencies**
- PHASE-03 and PHASE-05, both complete and green.

**Exit Criteria**
- [ ] `python -m pytest tests -q` passes and `ruff check src tests` reports no findings.
- [ ] `python scripts/sync_skill.py --check` exits 0.
- [ ] `homedesign publish designs/contractor-as-drawn.json` exits 0.
- [ ] `reports/2026-08-29-render-fidelity-report.html` opens standalone with every image
  visible and no network requests.
- [ ] `.github/workflows/pages.yml` exists and its YAML parses.
- [ ] The work is committed and pushed to `master`, and `git status` is clean.

**Phase Risks**
- **RISK-06-01:** `publish.verify_fresh` blocks because one view was rendered before a later
  schema change. Mitigation: render every view in a single run after all schema changes are
  final; never pass a force flag.
- **RISK-06-02:** Inlining before-and-after images as data URIs makes the HTML report very
  large. Mitigation: downscale report images to 1200 px on the long edge and encode as JPEG
  quality 80 before inlining; the report is a document, not a gallery.
- **RISK-06-03:** Adding a Pages workflow changes how `docs/` is deployed and could take the
  existing published links offline if the workflow is misconfigured. Mitigation: keep the
  hand-copied files in `docs/` exactly as they are so the existing Pages source still works if
  the workflow is disabled.

## Gotchas

- **Millimetres everywhere except Blender.** Every spec and compiled-model field ends in `_mm`
  and is millimetres. Blender is metres. Every conversion happens at the `build_scene` boundary
  by dividing by 1000, and local Blender variables carry an `_m` suffix. A single missed
  division puts the building a kilometre away.
- **Open every file under `designs/` with `encoding="utf-8"`.** These files contain Vietnamese
  text. On Windows the default `cp1252` codec raises
  `UnicodeDecodeError: 'charmap' codec can't decode byte 0x90` partway through the file.
- **`site.context.neighbours` is currently `false`** in `designs/contractor-as-drawn.json`.
  That single boolean, not a code bug, is why the published render shows a building alone on a
  lawn. Do not go looking for a fault in `_add_neighbour_massing` before checking the data.
- **`_neighbours_enabled` has a fallback**: when `context.neighbours` is absent it returns
  `plot_width_mm <= 6000`, which is `True` for this 3960 mm plot. Setting the key explicitly to
  `false` is what disabled it.
- **Never modify `orchestrator._CANDIDATES`.** Blender 4.1 is first on purpose. EEVEE Next on
  the target hardware renders a white wall as RGB 194,34,53. A test pins the ordering.
- **`bpy` imports are confined to `src/homedesign/blender/`.** CI never installs `bpy`. Any
  logic that needs a CI-visible test must live outside that directory as a pure function.
- **Changing the schema changes `model_hash`, which invalidates every render sidecar** and makes
  `homedesign publish` refuse to run. This is by design. The answer is a full re-render in
  PHASE-06, not a force flag.
- **`viewer._load_call` fails silently.** Above 8 MiB it emits a relative file reference instead
  of inlined base64url, which works when opened locally and breaks when published. The size
  budget test in PHASE-05 exists specifically because the failure is invisible.
- **base64url, not standard base64.** `viewer.py` encodes with the URL-safe alphabet
  deliberately; do not "fix" it to standard base64.
- **`optimize_glb` currently returns `False` and continues when `npx` is missing.** Every size
  budget in this plan assumes gltf-transform actually ran.
- **2D and 3D must share one resolver.** `plan2d._svg_furniture` and `blender/furnish` both call
  `placement.plan_room`. New geometry — facade elements, opening subdivisions — must follow the
  same rule or the parity test will start failing for reasons that are not accuracy problems.
- **Shadows are decorative.** The sun is fixed at 55° / 35° and `site.north_deg` is unset. No
  render produced by this plan may be presented as a daylight or heat-gain study, and the report
  in PHASE-06 must say so explicitly.
- **Three fidelity-ledger items are deliberate and must not be "fixed":** the orthogonal collapse
  of the ~7.2° skewed plot boundary (item a), the inferred lift shaft (item c), and the 4000 mm
  stair depth against the drawn 3200 mm (item g). The parity test excludes them by name.
- **Room names are Vietnamese, verbatim from the sheets.** `P.KHÁCH`, `P.NGỦ 1`, `P.THỜ`, `BẾP`,
  `SÂN THƯỢNG`. Do not translate them in labels, schedules, plates or the report — traceability
  to the drawing set depends on the exact strings.
- **Ruff line length is 120**, not 88. Running a differently-configured formatter will produce a
  large spurious diff.

## Verification Strategy

- **TEST-001:** `python -m pytest tests -q` → all tests pass; the collected count is at least
  226 plus the tests added by this plan.
- **TEST-002:** `ruff check src tests` → `All checks passed!`.
- **TEST-003:** `python scripts/sync_skill.py --check` → exits 0 with no diff reported.
- **TEST-004:** `python -m pytest tests/test_parity.py -q` → passes with `TOLERANCE_MM = 50.0`
  and no widened tolerance anywhere in the file.
- **TEST-005:** `python -m pytest tests/test_viewer.py -q` → the light build asserts ≤ 6291456
  bytes and the full build ≤ 26214400 bytes.
- **TEST-006:** `homedesign compile designs/contractor-as-drawn.json` → exits 0 and writes
  `output/compiled/contractor-as-drawn.model.json`.
- **TEST-007:** `homedesign build designs/contractor-as-drawn.json --profile final --gltf` →
  exits 0 and writes 12 PNG files into `output/png/` plus `output/gltf/contractor-as-drawn.glb`.
- **TEST-008:** `homedesign publish designs/contractor-as-drawn.json` → exits 0 and reports no
  stale sidecar hashes.
- **TEST-009:** `python -c "import pathlib,sys; h=pathlib.Path('reports/2026-08-29-render-fidelity-report.html').read_text(encoding='utf-8'); sys.exit(1 if 'src=\"http' in h or 'href=\"http' in h else 0)"`
  → exits 0, proving the report is self-contained.
- **TEST-010:** `python -c "import yaml,sys; yaml.safe_load(open('.github/workflows/pages.yml'))"`
  → exits 0. If PyYAML is unavailable, substitute
  `python -c "import pathlib; print(pathlib.Path('.github/workflows/pages.yml').read_text(encoding='utf-8'))"`
  and inspect the output by eye.
- **MANUAL-001:** Open `deliverables/contractor-as-drawn/png/contractor-as-drawn_exterior_front.png`
  beside `output/contractor_pdf_png/MB_MAI_-_MD-Model.png`. The storey lines, opening positions,
  fins, bands and parapets must correspond. No green ground may appear anywhere in frame, and
  the building must be hard against neighbours on both flanks.
- **MANUAL-002:** Open `deliverables/contractor-as-drawn/png/contractor-as-drawn_khach.png`. The
  door leaf sits inside its frame, no furniture interpenetrates, walls show tonal variation
  rather than a uniform white field, and skirting and reveals are visible.
- **MANUAL-003:** Open `deliverables/contractor-as-drawn/viewer/contractor-as-drawn-light.html`
  in a mobile browser with the network disabled after load. Room labels show Vietnamese
  diacritics correctly, the measurement tool returns a millimetre figure, both section sliders
  cut the model, and all four layer toggles work.
- **MANUAL-004:** Put the finished exterior render beside the published photography of Vo Trong
  Nghia's "Stacking Green", Ho Chi Minh City, with the labels stripped, and judge which reads
  as a photograph of a building. Judge material, light and scale — not styling.
- **OBS-001:** Record the wall-clock render time of the full 12-view `final` build in the
  PHASE-06 report. A figure above 20 minutes indicates the geometry added by this plan has
  outgrown the EEVEE budget and should be investigated before the next design uses these
  features.

## Risks and Alternatives

- **RISK-001:** The scope spans the schema, the compiler, both drawing pipelines, the Blender
  layer, the viewer and the delivery path, and any schema change invalidates every render. If
  phases interleave, the model hash moves under a half-finished render set. Mitigation: the
  phase order puts all schema changes in PHASE-02, PHASE-03 and PHASE-04, and confines every
  render-and-publish action to PHASE-06.
- **RISK-002:** Realism work drifts away from the drawings — the render becomes convincing and
  wrong, which is worse than unconvincing and right. Mitigation: the elevation-overlay parity
  test runs as an exit criterion of every single phase, not only at the end.
- **RISK-003:** Procedural materials may not survive glTF export, leaving the viewer flat while
  the stills improve. Mitigation: tested explicitly in PHASE-02 rather than discovered in
  PHASE-06, with a per-material bake as the fallback.
- **RISK-004:** The light viewer build silently exceeds the inline ceiling and the published
  page breaks for exactly the audience it was built for. Mitigation: an automated size budget,
  and making `optimize_glb`'s missing-`npx` path raise instead of returning `False`.
- **RISK-005:** Reading facade detail off a rasterised PDF is slow and tempting to guess at.
  Mitigation: ASM-001 makes an unreadable element a ledger entry, never an invention.
- **ALT-001:** Two passes — drive parity to green with no material work, then make it
  convincing on frozen geometry. Not chosen: cleanly separated, but it leaves the exterior
  unconvincing for a long time, and being unconvincing is the problem this plan exists to fix.
- **ALT-002:** Photographed PBR image textures instead of procedural node groups. Not chosen:
  a far higher photorealism ceiling, but it costs UV unwrapping and texture memory on an Intel
  UHD 620 and would blow the inline budget for the phone build. Reconsider only if the
  procedural materials lose MANUAL-004.
- **ALT-003:** A Cycles pass for the two or three hero images. Not chosen: real global
  illumination would genuinely show, but two engines in one deliverable means explaining why
  the cover image looks unlike the gallery, and CPU-only Cycles costs roughly 169 s per view.
- **ALT-004:** Ship the GLB as a sibling file on GitHub Pages instead of splitting into two
  builds. Not chosen: it removes the size ceiling entirely and works on Pages, but forfeits the
  single-file artifact path and still requires the deploy workflow.
- **ALT-005:** Import third-party furniture models. Not chosen: licence terms, unbounded
  polygon counts and image textures, all three of which the procedural-materials decision was
  arranged to avoid.

## Suggested Next Step

Execute PHASE-01. Capture the baseline `elevation_parity_report` figures for all four elevation
sides *before* changing any code, and record them in the phase's commit message — every later
phase is measured against that baseline. Each phase's exit criteria must be verified before the
next begins.
