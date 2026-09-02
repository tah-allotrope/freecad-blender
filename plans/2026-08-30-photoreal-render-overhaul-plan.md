---
title: "Photoreal Render Overhaul"
date: "2026-08-30"
status: "open — phases 1 and 4 are fully wired (6afcbc4) and the facade is authored and published (a40b6a2), but the CC0 texture/HDRI/furniture cache is 64x64 and 412-byte placeholders, materials never take the texture-first path, all six phase-5 viewer tasks are unbuilt (full build still inlines base64, no lightmap bake, no KTX2), and the overnight Cycles bake and rev.4 fidelity ledger were never done."
request: "Improve the contractor-as-drawn 3D render: it still reads as rudimentary massing, does not resemble the contractor drawing (the front-facing pillar is missing), and is not impressive enough to share. Produce a visually impressive result; no previously accepted limitation applies."
plan_type: "multi-phase"
research_inputs:
  - "research/2026-08-30_photoreal-render-overhaul-brainstorm.md"
  - "research/2026-08-29_render-fidelity-construction-set-brainstorm.md"
---

# Plan: Photoreal Render Overhaul

## Objective

Make the `contractor-as-drawn` interior stills and the GLB web viewer read as photographs
of a built Saigon tube house rather than as a CG massing study, and make the front facade
actually carry the articulation drawn on `MẶT ĐỨNG CHÍNH` — including the front pillar
that is currently absent from every output.

This matters now because the previous pass (commit `07f9c24`) shipped the *plumbing* for
facade articulation and finishes and never connected it. The result is a set of renders
that the audience — a construction crew reading them on phones and off A3 plates — cannot
take seriously, which forfeits the authority that the measurement and validation work
bought.

## Context Snapshot

- **Current state:** A JSON spec compiles to a `CompiledModel`, which drives four
  consumers (`plan2d`, `elevation`, `pdf`, `blender/build_scene`). The 2D side is at
  parity and well tested (231 tests pass). The 3D side produces:
  - `deliverables/contractor-as-drawn/png/contractor-as-drawn_exterior_front.png`: the
    building occupies roughly 8% of the frame, neighbour massing blocks stand in front of
    and hide the lower five storeys, and no facade articulation of any kind is visible.
  - `deliverables/contractor-as-drawn/png/contractor-as-drawn_khach.png`: the door leaf is
    rendered swung 0.35 rad open so it appears detached from its frame and passes through
    the sofa; furniture is untextured box primitives; walls are blown to near-white.

  **The facade pipeline is severed end to end.** This is the central finding and it was
  verified directly against the repo, not inferred:
  - `spec/homespec.schema.json` defines `storeys[].facade_elements` with
    `kind ∈ {fin, band, panel, awning}` — there is no `column`.
  - `designs/contractor-as-drawn.json` contains exactly **one** facade element (a `fin` on
    storey 0, `Ground`). Storeys 1–6 have none.
  - `src/homedesign/model.py` — the `Storey` dataclass has **no `facade_elements` field**
    and the `Opening` dataclass has **no `divisions` field**, so `compile_spec` silently
    discards both.
  - `src/homedesign/facade.py` (74 lines: `resolve_facade_element`,
    `facade_element_elevation_rect`, `opening_division_lines`) has **zero callers** in
    `src/` or `tests/` — verified with `grep -rn`. It is dead code.
  - `src/homedesign/blender/build_scene.py` never mentions `facade` outside comments.
  - `src/homedesign/blender/railings.py` builds only a solid parapet; there is no slatted
    or patterned variant despite the commit message claiming one.
  - `src/homedesign/blender/joinery.py` contains no mullion or transom code despite the
    commit message claiming "joinery mullions".
  - `tests/test_facade_utils.py` does not exist; only a stale
    `tests/__pycache__/test_facade_utils.*.pyc` remains, so it was written, executed once,
    and never committed.

  Consequently the single authored fin renders nothing, and adding `column` to the enum
  alone would also render nothing.

- **Desired state:** `facade_elements` (including `column`) and opening `divisions` flow
  spec → compiler → model → Blender scene → elevation SVG; the front facade of
  `contractor-as-drawn` is authored from the contractor sheets across all seven storeys;
  interior surfaces use image-based PBR materials and an HDRI environment; furniture is
  real cached meshes with procedural fallback; hero frames render on Cycles CPU with
  global illumination; and the web viewer serves an external, texture-carrying,
  lightmapped GLB from `docs/` instead of an 8 MiB inlined base64 blob.

- **Key repo surfaces:**
  - `spec/homespec.schema.json` — closed contract, `additionalProperties: false`
    throughout
  - `src/homedesign/model.py` — `Storey`, `Opening`, `CompiledModel`, `model_hash`
  - `src/homedesign/compiler.py` (603 lines) — `compile_spec`
  - `src/homedesign/facade.py` — dead resolver module to be wired in
  - `src/homedesign/finishes.py` — `build_finish_map`, `resolve_finish` (already wired
    into `compiler.py:121`)
  - `src/homedesign/blender/build_scene.py` (831 lines) — scene assembly, environment,
    lighting, cameras, render
  - `src/homedesign/blender/materials.py` (647 lines) — `get_material`,
    `make_procedural_material`, `prepare_for_gltf_export`, `add_vertex_color_ao`
  - `src/homedesign/blender/joinery.py`, `railings.py`, `geom.py`, `furnish.py`,
    `procedural_furniture.py`
  - `src/homedesign/placement.py` — `plan_room`, `FurnitureItem`
  - `src/homedesign/camera_fit.py` — `exterior_front_camera`
  - `src/homedesign/viewer.py` — `INLINE_GLB_LIMIT_BYTES`, `_load_call`, `write_viewer`
  - `src/homedesign/render_profiles.py`, `orchestrator.py`, `publish.py`
  - `designs/contractor-as-drawn.json`, `.measurements.md`, `.fidelity.md`
  - `contractor/` (source PDFs), `output/contractor_pdf_png/` (rasterisations)

- **Out of scope:**
  - Exterior hero-still art direction beyond the three defect fixes named in PHASE-01.
  - A3 print plate layout (plates re-render from new output; their layout is untouched).
  - The 2D SVG/DXF drawing set beyond adding facade elements to the elevation.
  - Re-measuring the building; `designs/contractor-as-drawn.measurements.md` rev.3 is
    input, not subject.
  - Changing `orchestrator._CANDIDATES` or the Blender 4.1 pin.
  - Cloud or remote GPU rendering.

## Environment & Conventions

- **Stack:** Python >= 3.11 (CI pins 3.11), setuptools, plain `pip` (no uv/poetry).
  Runtime deps: `jsonschema>=4.0`, `ezdxf>=1.0`, `pillow>=10.0`. Dev extras: `pytest>=8.0`,
  `ruff==0.15.7`. Optional extra `bpy==4.1.0`.
  Rendering runs through a **separately installed Blender 4.1 binary** invoked as
  `blender --background --python ...`, not through the `bpy` wheel.
- **Setup:** `python -m pip install -e ".[dev]"`
- **Build / Run:** the console script is `homedesign` (entry point
  `homedesign.__main__:main`); `python -m homedesign` is equivalent. Key commands:
  ```bash
  homedesign build   designs/contractor-as-drawn.json
  homedesign build   designs/contractor-as-drawn.json --gltf
  homedesign render  designs/contractor-as-drawn.json --view khach --profile cycles
  homedesign pdf     designs/contractor-as-drawn.json --require-fresh
  homedesign publish designs/contractor-as-drawn.json
  ```
  Every subcommand accepts `--out <dir>` to override `output/`.
- **Test:** full suite `python -m pytest tests -q` (baseline: **231 passed**, ~26 s).
  Single test: `python -m pytest tests/test_compiler.py::test_name -q`.
  Lint: `ruff check src tests` (line-length 120, configured in `ruff.toml`).
  Skill sync check: `python scripts/sync_skill.py --check`.
  CI (`.github/workflows/ci.yml`) runs exactly: `ruff check src tests`,
  `python -m pytest tests -q`, `python scripts/sync_skill.py --check`.
  Pytest config lives in `pyproject.toml`: `testpaths = ["tests"]`, `pythonpath = ["src"]`.
- **Conventions & traps:**
  - **Units: millimetres everywhere on the pure-Python side; metres only inside
    `src/homedesign/blender/`.** The conversion happens at exactly one point per value, by
    dividing by 1000 at point of use. Never introduce a second conversion point. Field
    names carry the unit: `*_mm` for millimetres, `*_m` for metres.
  - **Never import `bpy` outside `src/homedesign/blender/`.** Scripts in that directory run
    as top-level Blender scripts, so they must use **absolute imports** for
    `homedesign.*` modules and relative imports only for siblings inside `blender/`.
  - Shared dimensional constants live in `src/homedesign/constants.py` (e.g.
    `PARAPET_HEIGHT_MM = 1100.0`, `PARAPET_THICKNESS_MM = 100.0`,
    `BALUSTRADE_HEIGHT_MM = 900.0`, `RAIL_THICKNESS_MM = 60.0`). Add new magic dimensions
    there, not inline.
  - `spec/homespec.schema.json` sets `additionalProperties: false` at every level. Any new
    spec field must be added to the schema in the same change, or every design fails
    validation.
  - `model_hash(model)` is the first 12 hex chars of SHA-256 over the canonical JSON of
    `CompiledModel.to_dict()` plus `finish_map`. **Adding a field to `Storey`, `Opening`,
    or `CompiledModel` changes the hash for every design**, which invalidates every render
    sidecar (`*.png.json`) and makes `publish.verify_fresh` and `homedesign pdf
    --require-fresh` fail until the full set is re-rendered.
  - Geometry primitives: `make_box(name, x, y, z, w, d, h, collection, material=None)` and
    `make_hinged_box(name, x, y, z, w, d, h, hinge_x, hinge_y, angle_rad, collection,
    material=None)` in `src/homedesign/blender/geom.py`. All arguments in metres.
  - Site axis convention (used by `facade.py` and the `side` enum): `north` = min-y,
    `south` = max-y, `west` = min-x, `east` = max-x. The **street facade faces south**
    (max-y), and `exterior_front_camera` stands at negative y looking toward +y.
  - Renders **must** run on Blender 4.1 legacy EEVEE for the EEVEE profiles.
    `orchestrator._CANDIDATES` selects 4.1 ahead of 4.5; this order is pinned by
    `tests/test_orchestrator.py::test_blender_candidates_prefer_legacy_eevee_build`.
    EEVEE **Next** (Blender 4.2+) miscompiles on this machine's Intel UHD 620 iGPU and
    renders every lit surface blood red. Cycles is independent of that defect and is
    CPU-only here (zero OPTIX/CUDA/HIP/oneAPI devices enumerate).
  - `scripts/sync_skill.py` mirrors `.claude/skills/homedesign/SKILL.md` to
    `.agents/skills/homedesign/SKILL.md`. If you change documented CLI behaviour, run
    `python scripts/sync_skill.py` or CI fails on `--check`.
  - Vietnamese room ids and names are used throughout `designs/contractor-as-drawn.json`
    (`khach`, `bep_an`, `hanh_lang_thang`, `san_thuong_sau`, `ngu_truoc_f2`). Preserve them
    verbatim; all design/spec files are read and written as UTF-8 explicitly
    (`encoding="utf-8"`), because the default Windows codepage is cp1252 and will raise
    `UnicodeDecodeError` on these files.
- **Repo map:**
  ```
  src/homedesign/            pure-Python pipeline (mm units, no bpy)
    compiler.py              spec dict -> CompiledModel
    model.py                 dataclasses + model_hash + render sidecars
    facade.py                facade/division resolvers (currently unreferenced)
    finishes.py              finish family resolution -> finish_map
    placement.py             plan_room -> list[FurnitureItem]
    camera_fit.py            pure camera maths
    plan2d.py elevation.py pdf.py    2D consumers
    viewer.py                GLB optimisation + HTML viewer emission
    orchestrator.py          locates Blender, builds the CLI command
    render_profiles.py       preview / final / cycles settings
  src/homedesign/blender/    executed inside Blender (metre units, bpy allowed)
    build_scene.py materials.py joinery.py railings.py roof.py geom.py
    furnish.py procedural_furniture.py
  src/homedesign/assets/     viewer_template.html, floor_viewer_template.html
  designs/                   authored specs, incl. contractor-as-drawn.json
  spec/homespec.schema.json  the closed spec contract
  contractor/                source PDFs + approval drawing.jpg
  output/                    generated artifacts (png, svg, dxf, pdf, blend, gltf, viewer)
  deliverables/<slug>/       hash-verified published copies
  docs/                      GitHub Pages root (deployed by .github/workflows/pages.yml)
  tests/                     20 pytest modules, 231 tests
  ```

## Research Inputs

- From `research/2026-08-30_photoreal-render-overhaul-brainstorm.md`:
  - The judging bar is **photo-match against real Saigon tube-house photography**, not
    millimetre accuracy against the elevation. Drawing accuracy stays a hard constraint:
    every realism gain must be traceable to the contractor sheets, never invented.
  - Investment concentrates on **interior stills and the GLB web viewer**. Exterior hero
    stills are not the priority surface, but the missing front pillar and the
    8%-of-frame camera are corrected anyway as accuracy and correctness defects.
  - Three previously accepted limits are lifted by decision: EEVEE-only rendering (Cycles
    CPU is now allowed for hero output), procedural-only assets (external PBR textures,
    HDRIs and furniture meshes are now allowed, cached in-repo), and the 8 MiB inline-GLB
    viewer cap (which existed only to satisfy a hosting constraint that does not apply to
    the GitHub Pages delivery actually in use).
  - Neighbour massing is dropped from hero stills but retained behind a render-time
    toggle defaulting off, rather than deleted.
  - No new *render-quality* tests; judging is a separate blind-critic review logged to
    `reports/`. Geometry and schema correctness are still tested normally.
  - Render budget: an overnight full-set bake of roughly 6–10 hours unattended, with fast
    preview iteration on 2–3 hero frames in between.
- From `research/2026-08-29_render-fidelity-construction-set-brainstorm.md`:
  - `designs/contractor-as-drawn.fidelity.md` item **(k)** states that absent facade
    articulation is "the single biggest visual departure… the reason the 3D reads as
    massing rather than as this building". Items **(l)** undivided openings, **(m)** plain
    parapet railings and **(n)** absent finish information are also still open.
  - `MẶT ĐỨNG CHÍNH` (main elevation, top-left of `contractor/approval drawing.jpg`, and
    vector source `contractor/MB MAI - MD-Model.pdf`) carries vertical fins/pilasters
    running the height of the middle storeys, a cornice/coping band at the parapet, and
    framed panel treatments around the openings.
  - Delivery is to three channels: a phone/tablet GLB viewer on site, images pasted into
    a chat app, and printed A3 plates.

## Assumptions and Constraints

- **DEC-001:** The bar is photo-match against real Saigon tube-house photography;
  drawing accuracy is a constraint on it, not the judge.
- **DEC-002:** Interior stills and the GLB viewer are the priority surfaces. The exterior
  receives only the three defect fixes in PHASE-01.
- **DEC-003:** Cycles CPU is the hero render path. EEVEE remains the fast iteration loop.
  The Blender 4.1 pin is untouched.
- **DEC-004:** External PBR textures and HDRIs are used, cached in-repo so builds are
  reproducible offline.
- **DEC-005:** Furniture becomes curated real meshes placed from the existing
  `FurnitureItem` coordinates, with the procedural builders retained as fallback.
- **DEC-006:** The 8 MiB inline-GLB cap is lifted for the `full` and `floors` viewer
  builds; the `light` build keeps inlining for offline sharing.
- **DEC-007:** `column` is added to `facade_elements.kind`, and `divisions` is added to
  openings, in a single schema migration.
- **DEC-008:** Facade content is authored from the contractor sheets for all seven
  storeys, not just Ground.
- **DEC-009:** Neighbour massing defaults off for hero stills, behind a toggle.
- **DEC-011:** No new render-quality assertions in pytest. Geometry and schema
  correctness are tested normally.
- **DEC-012:** Final output is an overnight full-set Cycles bake across all 12 views.
- **ASM-001:** Reference photographs for the photo-match judgement are supplied by the
  repo owner. — **BINDING DEFAULT:** if
  `research/sources/reference-photos/` is absent or empty when PHASE-06 runs, the executor
  proceeds using the written rubric in PHASE-06 TASK-06-04 and records in
  `reports/2026-08-30-photoreal-critic.md` that the photoset gate was not applied. The
  executor must **not** block waiting for photographs.
- **ASM-002:** Licence policy for downloaded furniture and texture assets. —
  **BINDING DEFAULT:** CC0 only. Reject any asset whose licence is not CC0. Record every
  downloaded asset in `assets/cache/ATTRIBUTION.md` with source URL, asset name, licence
  string, and SHA-256 of the downloaded file, even for CC0.
- **ASM-003:** Exact dimensions of the front pillar and other facade elements on
  `MẶT ĐỨNG CHÍNH`. — **BINDING DEFAULT:** scale them off
  `output/contractor_pdf_png/MB_MAI_-_MD-Model.png` using the dimension chain printed on
  that sheet, round every derived dimension to the nearest 50 mm, and record each derived
  value with its source in a new `## Facade elements` section of
  `designs/contractor-as-drawn.measurements.md`. Do not invent an element that cannot be
  pointed at on the sheet.
- **ASM-004:** Which storeys the vertical fins span. — **BINDING DEFAULT:** storeys 2, 3
  and 4 (`Floor 2`, `Floor 3`, `Floor 4`), which are the "middle storeys" named in the
  fidelity ledger; adjust only if the sheet plainly shows otherwise.
- **ASM-005:** Whether a network connection is available when assets are fetched. —
  **BINDING DEFAULT:** all asset downloads happen once, in PHASE-02 TASK-02-01 and
  PHASE-03 TASK-03-01, and are committed under `assets/cache/`. Every later phase and
  every test must run offline from that cache. A missing cache entry is a hard error at
  build time, never a silent network fetch.
- **CON-001:** `orchestrator._CANDIDATES` must keep Blender 4.1 ahead of 4.5; the order is
  pinned by an existing test. EEVEE Next renders every lit surface red on this machine's
  Intel UHD 620.
- **CON-002:** No GPU render path exists; Cycles enumerates zero compute devices, so all
  Cycles renders are CPU-only. This is why DEC-012 budgets an overnight bake.
- **CON-003:** Every realism addition must be traceable to `contractor/` or
  `output/contractor_pdf_png/`.
- **CON-004:** Any change to `Storey`, `Opening`, or `CompiledModel` changes `model_hash`
  for every design and invalidates every `*.png.json` render sidecar. `publish.py` and
  `homedesign pdf --require-fresh` will refuse to run until the full set is re-rendered.
  Schedule the full re-render in PHASE-06 accordingly.
- **CON-005:** Millimetres on the pure-Python side, metres only inside
  `src/homedesign/blender/`, one conversion point per value.

## Specification

### S1. Facade element placement (mm)

`resolve_facade_element` in `src/homedesign/facade.py` already implements the following
for `fin`, `band`, `panel` and `awning`. `column` uses the identical placement rule; it
differs only in default finish and in that PHASE-01 requires `w_mm`, `h_mm` and
`projection_mm` to be strictly positive for it.

Given an element `E` on a storey whose base height is `B` (mm), a plot of width `W` (mm)
and depth `D` (mm):

```
abs_z = E.z_mm + (B if E.storey_level is not None else 0)
```

- `abs_z` — absolute height of the element's bottom edge above site datum, in mm.
- `E.z_mm` — the element's height above its storey base when `storey_level` is set,
  otherwise an absolute height.
- `B` — `storey.base_z`, the storey's floor level above site datum, in mm.

For `side == "south"` (the street facade, at `y = D`):

```
y_mm = D + E.projection_mm   if E.projection_mm < 0   (recessed into the facade)
y_mm = D                     if E.projection_mm >= 0  (proud of the facade)
d_mm = |E.projection_mm|     if E.projection_mm != 0
d_mm = 10                    if E.projection_mm == 0  (minimum readable depth)
```

- `y_mm` — the element box's minimum-y corner, in mm.
- `d_mm` — the element box's depth along y, in mm.
- A positive `projection_mm` means the element stands proud of the facade plane; a
  negative one means it is recessed into it.

For `side == "east"` and `side == "west"`, `E.x_mm` is reinterpreted as a distance along
the **depth** axis, and `w_mm`/`d_mm` swap roles. This is existing behaviour in
`facade.py` and must not be changed.

### S2. Opening subdivision (mm)

`opening_division_lines(opening_w_mm, opening_h_mm, divisions)` in
`src/homedesign/facade.py` returns the mullion and transom bars for one opening. Given
`c` columns, `r` rows, mullion width `m` (mm) and transom height `t` (mm) for an opening
`w` × `h` (mm):

```
glass_w = (w - (c - 1) * m) / c
glass_h = (h - (r - 1) * t) / r
```

- `glass_w` — width of one glazed pane, in mm.
- `glass_h` — height of one glazed pane, in mm.
- `c`, `r` — number of panes across and up. `c <= 1 and r <= 1` yields an empty list
  (an undivided opening).

Vertical mullion `i` (for `i` in `1 .. c-1`) is placed at:

```
x_i = i * (glass_w + m) - m
```

Horizontal transom `j` (for `j` in `1 .. r-1`) is placed at:

```
y_j = j * (glass_h + t) - t
```

- `x_i`, `y_j` — offsets from the opening's own bottom-left corner, in mm.

**Off-by-one trap:** the `- m` and `- t` terms are what place the bar's *near* edge at the
pane boundary rather than its far edge. A `c`-column opening has exactly `c - 1` mullions.
Do not "fix" these expressions.

### S3. Exterior front camera framing

`exterior_front_camera` in `src/homedesign/camera_fit.py` currently fits
`facade_bbox(model)`, whose extent includes context geometry, which is why the building
occupies roughly 8% of the frame. Change it to fit `building_bbox(model)` — the same
function `exterior_aerial_camera` already uses — while keeping the existing fit centre:

```
centre = (plot_width_mm / 2000, 0.0, sum(storey.height_mm for storey in storeys) / 2000)
```

- Division by 2000 converts millimetres to metres *and* halves, giving the mid-point in
  metres in one step. This is intentional and matches the existing code.
- `forward = (0.0, 1.0, 0.0)` — the camera looks north (+y) at the street facade.
- `position = (centre.x, centre.y - dist, centre.z)` — the camera stands south of the
  facade plane at the solved fit distance `dist`.

### S4. Interior render configuration decision logic

For each requested view, the render profile is chosen as follows:

1. If `--profile` is given on the command line, use it verbatim.
2. Otherwise use `preview`.
3. If the resolved profile is `cycles`, set `scene.cycles.device = 'CPU'` unconditionally
   (CON-002), enable the OpenImageDenoise denoiser, and set `use_adaptive_sampling = True`
   with `adaptive_threshold = 0.01`.
4. If the resolved profile is `preview` or `final`, keep the existing legacy-EEVEE
   configuration exactly as it is today.
5. Interior lighting is applied identically for all profiles so that a `preview` frame is
   a faithful low-sample proxy for the `cycles` frame it approximates. Never make lighting
   conditional on the engine.

## Phase Summary

| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Connect the severed facade/divisions pipeline end to end, add `column`, and fix the three named geometry defects | None | Schema + compiler + model + build_scene + elevation wired; door leaf, framing and context defects fixed; new tests |
| PHASE-02 | Image-based PBR materials and HDRI environment from a committed offline asset cache | PHASE-01 | `assets/cache/`, `asset_cache.py`, textured `get_material`, HDRI world |
| PHASE-03 | Real furniture meshes with procedural fallback | PHASE-02 | `assets/cache/furniture/`, `asset_library.py`, mesh-backed `build_item` |
| PHASE-04 | Cycles CPU hero render path and reworked interior lighting | PHASE-02 | `cycles` profile promoted, lighting rework, hero frames |
| PHASE-05 | External, textured, lightmapped GLB viewer served from `docs/` | PHASE-02, PHASE-04 | Lifted inline cap, KTX2 textures, baked lightmap, updated viewer template |
| PHASE-06 | Author the facade from the sheets, run the full overnight bake, judge, and publish | PHASE-01..05 | Populated design, full render set, critic report, published deliverables |

## Detailed Phases

### PHASE-01 - Connect the Facade Pipeline and Fix Geometry Defects

**Goal**
Make `facade_elements` and opening `divisions` survive compilation and reach both the
Blender scene and the elevation SVG; add the `column` kind that the missing front pillar
needs; and fix the door-leaf, camera-framing and neighbour-occlusion defects. After this
phase the pipeline can *express* the drawing even though the drawing content is not yet
authored (that is PHASE-06).

**Tasks**
- [x] TASK-01-01: Add `"column"` to the `kind` enum at
      `/properties/storeys/items/properties/facade_elements/items/properties/kind` in
      `spec/homespec.schema.json`. The enum becomes
      `["fin", "band", "panel", "awning", "column"]`.
- [x] TASK-01-02: Add an optional `id` property (type `string`) to the `facade_elements`
      item schema. `finishes.build_finish_map` already reads `fe.get("id", ...)` with a
      synthesised fallback, but `additionalProperties: false` currently rejects an
      authored `id`.
- [x] TASK-01-03: Add a `divisions` property to
      `/properties/storeys/items/properties/openings/items/properties` with
      `type: "object"`, `additionalProperties: false`, and properties
      `columns` (integer, minimum 1, default 1), `rows` (integer, minimum 1, default 1),
      `mullion_mm` (number, exclusiveMinimum 0, default 50),
      `transom_mm` (number, exclusiveMinimum 0, default 50).
- [x] TASK-01-04: Add `facade_elements: list[dict] = field(default_factory=list)` to the
      `Storey` dataclass in `src/homedesign/model.py`, and
      `divisions: Optional[dict] = None` to the `Opening` dataclass. Extend
      `CompiledModel.from_dict` to read both back (`s.get("facade_elements", [])` and
      `o.get("divisions")`) so round-tripping a compiled model preserves them.
- [x] TASK-01-05: In `src/homedesign/compiler.py`, populate `Storey.facade_elements` from
      `storey.get("facade_elements", [])` by calling
      `facade.resolve_facade_element(element, storey_base_z_mm, plot_width_mm,
      plot_depth_mm)` for each entry, and carry the resolved dict plus the original `kind`
      and `side`. Populate `Opening.divisions` from the spec opening's `divisions` key.
      Add `from .facade import resolve_facade_element` to the imports beside the existing
      `from .finishes import build_finish_map` at line 18.
- [x] TASK-01-06: Add `build_facade_elements(storey_mm, style, collection)` to
      `src/homedesign/blender/build_scene.py` and call it from the storey loop, next to
      the existing `_add_balcony_parapets` call. Each element becomes one `make_box` in
      metres, using the resolved `x_mm/y_mm/z_mm/w_mm/d_mm/h_mm` divided by 1000, with the
      material resolved via `get_material(style, element["finish"])`.
- [x] TASK-01-07: Add mullion and transom bars to
      `src/homedesign/blender/joinery.py::build_opening_furniture`. When
      `opening_mm.get("divisions")` is truthy, call
      `homedesign.facade.opening_division_lines(width_mm, height_mm, divisions)` and emit
      one `make_box` per returned bar, using `frame_mat` and a depth equal to the existing
      `GLASS_THICKNESS * 2` so bars read from both faces. Leave the existing frame, lintel,
      sill, glass and leaf code untouched.
- [x] TASK-01-08: Fix the detached door leaf. In
      `src/homedesign/blender/joinery.py::build_opening_furniture`, change the
      `make_hinged_box` swing angle for interior doors from `0.35` / `-0.35` radians to
      `0.0`, so the leaf sits flush in its frame. Introduce a module constant
      `DOOR_SWING_RAD = 0.0` and use it in both branches rather than repeating the
      literal. This removes both the "detached leaf" read and the sofa interpenetration in
      the `khach` view.
- [x] TASK-01-09: Fix exterior framing per S3. In
      `src/homedesign/camera_fit.py::exterior_front_camera`, replace
      `bbox = facade_bbox(model)` with `bbox = building_bbox(model)`. Leave the `centre`
      expression, `forward`, and the returned `lens_mm` exactly as they are.
- [x] TASK-01-10: Remove the neighbour-massing short-circuit. In
      `src/homedesign/blender/build_scene.py` at approximately line 408, replace
      `if _neighbours_enabled(model) or True:` with
      `if _neighbours_enabled(model) and model.get("show_neighbours", False):` and delete
      the now-dead `else:` branch comment claiming unreachability — the `else` branch
      (which builds the plain ground plane) becomes live and must be kept.
- [x] TASK-01-11: Add a `--show-neighbours` flag to the `build` and `render` subcommands
      in `src/homedesign/__main__.py`, defaulting to `False`, and thread it through
      `orchestrator._build_command` as `--show-neighbours` so `build_scene` can read it.
      Default off satisfies DEC-009 while keeping the context geometry available.
- [x] TASK-01-12: Add `tests/test_facade_utils.py` and extend
      `tests/test_compiler.py` and `tests/test_openings.py` per the Test Specs below.
- [x] TASK-01-13: Run `python scripts/sync_skill.py` after adding the CLI flag, so
      `.agents/skills/homedesign/SKILL.md` stays in sync and CI's `--check` passes.

**File Changes**
- `spec/homespec.schema.json` (modify): add `"column"` to the `facade_elements.kind` enum;
  add optional `id` to the `facade_elements` item; add the `divisions` object to the
  opening item. Do not relax `additionalProperties: false` anywhere.
- `src/homedesign/model.py` (modify): add `facade_elements` to `Storey` and `divisions` to
  `Opening`; extend `CompiledModel.from_dict`. Leave `model_hash` untouched — it picks the
  new fields up automatically through `to_dict()`.
- `src/homedesign/compiler.py` (modify): import and call `resolve_facade_element`;
  populate the two new model fields. Leave all existing wall/opening/stair generation
  untouched.
- `src/homedesign/facade.py` (modify): no behaviour change to the three existing
  functions; add `"column": "facade_trim"` to the `defaults` dict inside
  `resolve_facade_element` so a column without an explicit finish resolves sensibly.
- `src/homedesign/blender/build_scene.py` (modify): add `build_facade_elements` and call
  it per storey; fix the `or True` short-circuit; read `--show-neighbours`.
- `src/homedesign/blender/joinery.py` (modify): add `DOOR_SWING_RAD = 0.0`; use it in both
  `make_hinged_box` calls; add mullion/transom emission.
- `src/homedesign/camera_fit.py` (modify): one-line bbox swap in `exterior_front_camera`.
- `src/homedesign/elevation.py` (modify): draw facade elements on the matching elevation
  by calling `facade.facade_element_elevation_rect(element, side, storey_base_z_mm)` for
  each element and emitting an SVG `<rect>` in the existing elevation coordinate system.
- `src/homedesign/__main__.py` (modify): add the `--show-neighbours` flag to `build` and
  `render`.
- `src/homedesign/orchestrator.py` (modify): pass `--show-neighbours` through
  `_build_command` when set.
- `tests/test_facade_utils.py` (create): unit tests for the three `facade.py` functions.
- `tests/test_compiler.py` (modify): add compile-through tests for the two new fields.
- `tests/test_openings.py` (modify): add the divisions schema-validation test.

**Function Signatures**
- `resolve_facade_element(element: dict, storey_base_z_mm: float, plot_width_mm: float, plot_depth_mm: float) -> dict` —
  existing; returns `{"x_mm", "y_mm", "z_mm", "w_mm", "d_mm", "h_mm", "finish"}` in
  millimetres for one facade element.
- `opening_division_lines(opening_w_mm: float, opening_h_mm: float, divisions: dict) -> list[dict]` —
  existing; returns one dict per mullion/transom bar with keys `x_mm`, `y_mm`, `w_mm`,
  `h_mm`, offsets relative to the opening's bottom-left corner.
- `facade_element_elevation_rect(element: dict, side: str, storey_base_z_mm: float) -> dict | None` —
  existing; returns `{"x_mm", "y_mm", "w_mm", "h_mm", "finish"}` for elements on `side`,
  else `None`.
- `build_facade_elements(storey_mm: dict, style: str, collection) -> list` — new, in
  `src/homedesign/blender/build_scene.py`; creates one Blender box object per resolved
  facade element on the storey and returns the created objects.

**Test Specs**
- `opening_division_lines(2000, 1400, {"columns": 3, "rows": 1, "mullion_mm": 50, "transom_mm": 50})`
  → a list of length 2. `glass_w = (2000 - 2*50) / 3 = 633.333…`, so the bars are at
  `x_mm ≈ 633.333` and `x_mm ≈ 1316.667`, each with `w_mm == 50.0`, `y_mm == 0.0`,
  `h_mm == 1400`.
- `opening_division_lines(2000, 1400, {"columns": 1, "rows": 1})` → `[]` (an undivided
  opening produces no bars).
- `opening_division_lines(1200, 2400, {"columns": 2, "rows": 2, "mullion_mm": 60, "transom_mm": 40})`
  → length 2: one vertical bar at `x_mm == 570.0`, `w_mm == 60.0`, `h_mm == 2400`; one
  horizontal bar at `y_mm == 1180.0`, `h_mm == 40.0`, `w_mm == 1200`, `x_mm == 0.0`.
- `resolve_facade_element({"kind": "column", "side": "south", "x_mm": 500, "z_mm": 0, "w_mm": 300, "h_mm": 3400, "projection_mm": 300, "storey_level": 0}, 0.0, 4000.0, 20000.0)`
  → `{"x_mm": 500, "y_mm": 20000, "z_mm": 0.0, "w_mm": 300, "d_mm": 300, "h_mm": 3400, "finish": "facade_trim"}`.
- `resolve_facade_element({"kind": "panel", "side": "south", "x_mm": 0, "z_mm": 100, "w_mm": 1000, "h_mm": 500, "projection_mm": -80, "storey_level": 2}, 7200.0, 4000.0, 20000.0)`
  → `y_mm == 19920` (recessed: `20000 + (-80)`), `d_mm == 80`, `z_mm == 7300.0`
  (`100 + 7200`), `finish == "facade_field"`.
- `resolve_facade_element({..., "projection_mm": 0, ...})` → `d_mm == 10` (the minimum
  readable depth substituted for a zero projection).
- Compiling a spec whose storey 0 carries one `column` facade element and whose storey 2
  carries none → `compile_spec(spec).storeys[0].facade_elements` has length 1 and
  `.storeys[2].facade_elements == []`.
- Compiling a spec whose opening carries `{"columns": 3, "rows": 2}` →
  `compile_spec(spec).storeys[0].openings[0].divisions == {"columns": 3, "rows": 2}`.
- Schema validation of a spec containing
  `facade_elements: [{"kind": "column", "side": "south", "x_mm": 0, "z_mm": 0, "w_mm": 300, "h_mm": 3000, "projection_mm": 200}]`
  → `validate_schema(spec) == []` (no errors).
- Schema validation of a spec containing `facade_elements: [{"kind": "buttress", ...}]` →
  `validate_schema(spec)` returns at least one error (the enum rejects unknown kinds).
- Schema validation of an opening containing `divisions: {"columns": 3, "panes": 4}` →
  at least one error (`additionalProperties: false` rejects `panes`).
- `exterior_front_camera(model, 1920, 1080)` for a model whose building is 4 m wide and
  21 m tall with 4 m of context on each side → the returned `dist` is strictly smaller
  than the value returned before the change; assert the solved distance fits
  `building_bbox`, not `facade_bbox`, by checking that the building's projected width
  exceeds 60% of the frame width.
- `tests/test_orchestrator.py::test_blender_candidates_prefer_legacy_eevee_build` → still
  passes unchanged (CON-001 guard).

**Dependencies**
- None. This phase touches only existing modules and the schema.

**Exit Criteria**
- [ ] `ruff check src tests` exits 0.
- [ ] `python -m pytest tests -q` reports at least 231 passed plus the new tests, 0 failed.
- [ ] `python scripts/sync_skill.py --check` exits 0.
- [ ] `grep -rn "resolve_facade_element" src/ --include=*.py` shows a caller in
      `src/homedesign/compiler.py` (the module is no longer dead).
- [ ] `grep -n "or True" src/homedesign/blender/build_scene.py` returns no matches.
- [ ] `homedesign build designs/contractor-as-drawn.json` completes and the newly rendered
      `output/png/contractor-as-drawn_khach.png` shows the door leaf flush in its frame
      with no intersection with the sofa.
- [ ] `output/png/contractor-as-drawn_exterior_front.png` shows the building occupying
      well over half the frame width, with no neighbour blocks in front of it.

**Phase Risks**
- **RISK-01-01:** Adding fields to `Storey` and `Opening` changes `model_hash` for every
  design, so `homedesign pdf --require-fresh` and `homedesign publish` will fail against
  the existing render set. Mitigation: this is expected and accounted for; the full
  re-render happens in PHASE-06. Do not attempt to publish between PHASE-01 and PHASE-06.
- **RISK-01-02:** `facade.py`'s east/west branches reinterpret `x_mm` as a depth-axis
  distance, which is easy to misread as a bug and "fix". Mitigation: the Test Specs cover
  only `south` elements (all authored content is on the street facade); leave the
  east/west branches exactly as written.
- **RISK-01-03:** Setting `DOOR_SWING_RAD = 0.0` makes `make_hinged_box` degenerate to an
  unrotated box; confirm it does not divide by the angle anywhere. Mitigation: read
  `src/homedesign/blender/geom.py:25` before changing the value.

### PHASE-02 - Image-Based PBR Materials and HDRI Environment

**Goal**
Replace the procedural-noise material graphs with image-based PBR maps drawn from a
committed offline asset cache, and light the scene from an HDRI instead of a colour
gradient. This is the largest realism gain per unit of effort for interiors.

**Tasks**
- [ ] TASK-02-01: Create `assets/cache/` and download, once, a CC0 texture set for each of
      the seven finish families already used by `finishes.ALLOWED_FAMILIES` and
      `materials._FAMILY_FOR_KEY`: `plaster_painted`, `ceramic_tile`, `stone_slab`,
      `wood_board`, `metal_brushed`, `glass_clear`, `concrete_formed`. For each family
      store `diffuse.jpg`, `rough.jpg`, `normal.jpg` (and `ao.jpg` when available) under
      `assets/cache/textures/<family>/` at 2K resolution. Also download one interior HDRI
      and one exterior HDRI to `assets/cache/hdri/interior.hdr` and
      `assets/cache/hdri/exterior.hdr`.
- [ ] TASK-02-02: Write `assets/cache/ATTRIBUTION.md` recording, for every downloaded
      file: source URL, asset name, licence string (must be CC0 per ASM-002), and the
      SHA-256 of the file. Generate the hashes with:
      `find assets/cache -type f ! -name ATTRIBUTION.md -exec sha256sum {} \;`
- [x] TASK-02-03: Create `src/homedesign/asset_cache.py` (pure Python, no `bpy`) exposing
      the cache root and lookup helpers, so both the pure side and the Blender side
      resolve paths identically and a missing entry raises rather than silently falling
      back to network access (ASM-005).
- [ ] TASK-02-04: Extend `src/homedesign/blender/materials.py::make_procedural_material`
      into a texture-first path: when `asset_cache.texture_set(family)` returns a set,
      build an Image Texture → Normal Map → Principled BSDF graph with a Mapping node
      driven by `scale_mm`; otherwise fall back to the existing procedural graph
      unchanged. Keep `get_material`'s signature and cache behaviour exactly as they are.
- [x] TASK-02-05: Ensure every mesh that receives a textured material has a UV map. Add a
      `_ensure_uv(obj)` helper in `src/homedesign/blender/geom.py` that runs a Smart UV
      Project on objects with no UV layer, and call it from `make_box` and
      `make_hinged_box` after mesh creation.
- [x] TASK-02-06: Replace the sky gradient in
      `src/homedesign/blender/build_scene.py::build_environment` with an Environment
      Texture node loading `assets/cache/hdri/exterior.hdr`, with strength exposed as a
      module constant. Keep the existing sun lamp — the HDRI supplies ambient and
      reflection, the sun supplies the directional key.
- [x] TASK-02-07: Verify `prepare_for_gltf_export` still produces a valid export. It
      currently flattens procedural graphs to base colours; extend it so an image-textured
      material exports its diffuse map rather than a flat colour, since PHASE-05 depends
      on textures reaching the GLB.

**File Changes**
- `assets/cache/textures/<family>/*.jpg` (create): seven texture sets, 2K.
- `assets/cache/hdri/interior.hdr`, `assets/cache/hdri/exterior.hdr` (create).
- `assets/cache/ATTRIBUTION.md` (create): per-file source, licence, SHA-256.
- `src/homedesign/asset_cache.py` (create): pure-Python cache path resolution.
- `src/homedesign/blender/materials.py` (modify): texture-first material construction in
  `make_procedural_material`; extend `prepare_for_gltf_export`. Leave `PALETTES`,
  `_FAMILY_FOR_KEY`, `floor_material_key` and `furniture_material_key` unchanged — the
  palette base colours remain the fallback and the glTF colour source.
- `src/homedesign/blender/geom.py` (modify): add `_ensure_uv` and call it from both box
  builders.
- `src/homedesign/blender/build_scene.py` (modify): HDRI world in `build_environment`.
- `.gitignore` (modify): confirm `assets/cache/` is **not** ignored; the cache is
  committed deliberately (ASM-005).
- `tests/test_asset_cache.py` (create): offline cache-resolution tests.

**Function Signatures**
- `asset_cache.cache_root() -> pathlib.Path` — absolute path to `assets/cache/`.
- `asset_cache.texture_set(family: str) -> dict[str, pathlib.Path] | None` — mapping of
  `{"diffuse", "rough", "normal", "ao"}` to existing files for `family`, or `None` when
  the family has no cached set.
- `asset_cache.hdri(name: str) -> pathlib.Path` — path to `assets/cache/hdri/<name>.hdr`;
  raises `FileNotFoundError` when absent.
- `make_procedural_material(name: str, family: str, base_color: tuple[float, float, float], roughness: float, scale_mm: float)` —
  existing signature preserved; returns a `bpy.types.Material` built from cached textures
  when available, else from the existing procedural graph.
- `_ensure_uv(obj) -> None` — gives `obj` a UV layer if it has none; no-op otherwise.

**Test Specs**
- `asset_cache.texture_set("ceramic_tile")` → a dict whose `"diffuse"` value is an
  existing file under `assets/cache/textures/ceramic_tile/`.
- `asset_cache.texture_set("not_a_family")` → `None`.
- `asset_cache.hdri("exterior")` → an existing path ending in `exterior.hdr`.
- `asset_cache.hdri("missing")` → raises `FileNotFoundError`.
- Every family in `finishes.ALLOWED_FAMILIES` that also appears as a value in
  `materials._FAMILY_FOR_KEY` → `asset_cache.texture_set(family) is not None`.
- `assets/cache/ATTRIBUTION.md` contains a line for every file under `assets/cache/`
  except `ATTRIBUTION.md` itself, and every such line contains the string `CC0`.

**Dependencies**
- PHASE-01 (so the facade boxes created there also receive UVs and textures).
- One-time network access for TASK-02-01 only. Every later step and every test runs
  offline from the committed cache.

**Exit Criteria**
- [ ] `python -m pytest tests -q` passes with the new `tests/test_asset_cache.py`.
- [ ] `ruff check src tests` exits 0.
- [ ] `python -c "import homedesign.asset_cache as a; print(a.texture_set('wood_board'))"`
      prints a dict of four existing paths.
- [ ] `homedesign build designs/contractor-as-drawn.json` completes and
      `output/png/contractor-as-drawn_khach.png` shows visible tile grout on the floor and
      surface variation on the walls rather than flat fills.
- [ ] `homedesign build designs/contractor-as-drawn.json --gltf` completes and the
      exported GLB in `output/gltf/` is larger than the pre-phase GLB, confirming textures
      are embedded.

**Phase Risks**
- **RISK-02-01:** Smart UV Project runs per object and is slow on a scene with thousands
  of boxes. Mitigation: `_ensure_uv` must early-return when a UV layer already exists, and
  `make_box` should apply a cheap cube projection rather than a full unwrap for
  axis-aligned boxes.
- **RISK-02-02:** 2K textures across seven families plus two HDRIs will add roughly
  100–300 MB to the repository. Mitigation: store JPEGs (not PNGs) for the SDR maps, and
  downsample to 2K maximum; if the total exceeds 300 MB, drop to 1K for
  `neighbour`/`street`-only families.
- **RISK-02-03:** `prepare_for_gltf_export` currently guarantees a flat base colour in the
  export; changing it risks breaking the existing viewer. Mitigation: PHASE-05 re-verifies
  the viewer end to end; keep the flat-colour path as the fallback branch.

### PHASE-03 - Real Furniture Meshes with Procedural Fallback

**Goal**
Replace box-primitive furniture with cached real meshes, placed from the existing
`FurnitureItem` coordinates, without changing the placement maths or removing the
procedural builders.

**Tasks**
- [ ] TASK-03-01: Download, once, a CC0 mesh (`.glb`) for each furniture kind that
      `src/homedesign/placement.py` can emit — read the `_BUILDERS` dict in
      `src/homedesign/blender/procedural_furniture.py` for the authoritative list
      (`bed`, `sofa`, `table`, `chair`, `kitchen_run`, `wc`, `shelving`, `console`, `car`,
      `planter`, plus any others present). Store as
      `assets/cache/furniture/<kind>.glb`. Append each to
      `assets/cache/ATTRIBUTION.md`.
- [x] TASK-03-02: Create `src/homedesign/blender/asset_library.py` with a single entry
      point that imports a cached GLB, scales it to the `FurnitureItem`'s `w`/`d`/`h`
      bounding box, rotates it by `rot_deg` about Z, and positions it at the item's
      origin. Scaling must be **non-uniform per axis** so the mesh occupies exactly the
      footprint the collision-resolved placement reserved.
- [x] TASK-03-03: Modify `src/homedesign/blender/procedural_furniture.py::build_item` to
      try `asset_library.build_from_asset(...)` first and fall back to the existing
      `_BUILDERS` dispatch when the kind has no cached asset. Do not delete any existing
      builder.
- [ ] TASK-03-04: Cache imported meshes per kind and instance them with linked object data
      so a scene with twelve chairs holds one mesh datablock, not twelve.

**File Changes**
- `assets/cache/furniture/<kind>.glb` (create): one CC0 mesh per furniture kind.
- `assets/cache/ATTRIBUTION.md` (modify): append the furniture entries.
- `src/homedesign/asset_cache.py` (modify): add `furniture(kind)` lookup.
- `src/homedesign/blender/asset_library.py` (create): GLB import, fit, place, instance.
- `src/homedesign/blender/procedural_furniture.py` (modify): asset-first dispatch in
  `build_item`; leave `_placer_for`, `_default_block` and all `_build_*` functions intact.
- `tests/test_asset_cache.py` (modify): add furniture lookup tests.

**Function Signatures**
- `asset_cache.furniture(kind: str) -> pathlib.Path | None` — path to
  `assets/cache/furniture/<kind>.glb`, or `None` when absent.
- `asset_library.build_from_asset(item, room_x: float, room_y: float, base_z: float, collection) -> object | None` —
  imports, fits and places the cached mesh for `item.kind`; returns the created object, or
  `None` when no cached asset exists so the caller falls back to the procedural builder.
  All positional arguments are in metres.

**Test Specs**
- `asset_cache.furniture("sofa")` → an existing path ending `furniture/sofa.glb`.
- `asset_cache.furniture("not_a_kind")` → `None`.
- Every key in `procedural_furniture._BUILDERS` → `asset_cache.furniture(key)` is either a
  path to an existing file or `None`; the test asserts the union is exhaustive, so a newly
  added builder cannot silently lack a cache entry check.
- `placement.plan_room("living", 4.0, 6.0)` → unchanged from its current output; assert
  the existing test in `tests/test_placement.py` still passes, proving PHASE-03 changed no
  placement maths.

**Dependencies**
- PHASE-02 (cache infrastructure and `asset_cache.py` must exist first).
- One-time network access for TASK-03-01 only.

**Exit Criteria**
- [ ] `python -m pytest tests -q` passes; `tests/test_placement.py` is unchanged and green.
- [ ] `ruff check src tests` exits 0.
- [ ] `homedesign render designs/contractor-as-drawn.json --view khach --profile preview`
      completes and the output shows a recognisable sofa mesh rather than a box.
- [ ] Deleting `assets/cache/furniture/sofa.glb` and re-running the same command still
      completes, producing the procedural box — proving the fallback works.

**Phase Risks**
- **RISK-03-01:** Downloaded meshes may be high-poly enough to make Cycles CPU renders and
  the GLB export impractical. Mitigation: cap each asset at 50,000 triangles; apply a
  Decimate modifier at import when the imported mesh exceeds that.
- **RISK-03-02:** Non-uniform scaling to the reserved footprint will visibly distort a
  mesh whose native proportions differ from the placement box. Mitigation: prefer assets
  whose native aspect ratio is within 20% of the placement box; where it is not, scale
  uniformly to fit the largest constrained axis and centre the result inside the box.

### PHASE-04 - Cycles CPU Hero Path and Interior Lighting Rework

**Goal**
Make `--profile cycles` the hero output path with correct CPU configuration and
denoising, and rework interior lighting so rooms read with real bounce light instead of
blown-out white walls.

**Tasks**
- [x] TASK-04-01: In `src/homedesign/render_profiles.py`, keep the three existing profile
      names and their public shape, and add the Cycles-specific keys the build script
      needs: `device: "CPU"`, `denoise: True`, `adaptive_threshold: 0.01`. Leave the
      `preview` and `final` entries byte-for-byte unchanged so
      `tests/test_orchestrator.py` continues to pass.
- [x] TASK-04-02: In `src/homedesign/blender/build_scene.py::_set_engine`, implement S4
      steps 3 and 4: when the profile is `cycles`, set `scene.cycles.device = 'CPU'`,
      `scene.cycles.use_denoising = True`, `scene.cycles.use_adaptive_sampling = True`,
      `scene.cycles.adaptive_threshold = 0.01`, and leave the EEVEE branch untouched.
- [x] TASK-04-03: Rework `add_interior_lights`. Replace the single
      `clamp(area_m2 * 2.2, 20, 90)` area lamp per room with: (a) a window portal on every
      exterior opening so the HDRI drives daylight through the aperture, and (b) a much
      weaker practical lamp per room, sized `clamp(area_m2 * 0.6, 5, 25)` watts, placed at
      ceiling height. The current wattage is the direct cause of the blown-out walls.
- [x] TASK-04-04: Set the scene's view transform to `Filmic` (Blender 4.1's default is
      `Filmic`; assert rather than assume) and expose exposure as a module constant.
      Verify no lit white wall clips: the `khach` render's 99th-percentile luminance must
      stay below pure white.
- [x] TASK-04-05: Add ceiling geometry and skirting to interior rooms so the camera does
      not see an open top edge. `_add_top_storey_ceilings` already exists; extend it to
      every storey, not only the top one, and add a 100 mm skirting box at the base of
      each interior wall using `make_box`.

**File Changes**
- `src/homedesign/render_profiles.py` (modify): add Cycles keys to the `cycles` entry
  only.
- `src/homedesign/blender/build_scene.py` (modify): `_set_engine` Cycles branch;
  `add_interior_lights` rework; extend `_add_top_storey_ceilings`; add skirting.
- `src/homedesign/constants.py` (modify): add `SKIRTING_HEIGHT_MM = 100.0` and
  `SKIRTING_PROJECTION_MM = 15.0`.
- `tests/test_orchestrator.py` (modify): add a profile-shape assertion for the new Cycles
  keys.

**Function Signatures**
- `_set_engine(profile: dict) -> None` — existing; now additionally applies the CPU,
  denoising and adaptive-sampling settings when `profile["engine"] == "CYCLES"`.
- `add_interior_lights(model: dict, collection) -> list` — existing signature; now emits
  one portal per exterior opening plus one reduced-wattage practical per room.

**Test Specs**
- `render_profiles.RENDER_PROFILES["cycles"]` → contains `engine == "CYCLES"`,
  `samples == 512`, `res == (1920, 1080)`, `device == "CPU"`, `denoise is True`,
  `adaptive_threshold == 0.01`.
- `render_profiles.RENDER_PROFILES["preview"]` → unchanged:
  `{"engine": "EEVEE", "samples": 32, "res": (960, 540), "raytracing": False}`.
- `render_profiles.RENDER_PROFILES["final"]` → unchanged:
  `{"engine": "EEVEE", "samples": 256, "res": (1920, 1080), "raytracing": True}`.
- `tests/test_orchestrator.py::test_blender_candidates_prefer_legacy_eevee_build` → still
  passes (CON-001).

**Dependencies**
- PHASE-02 (the HDRI must exist before portals are meaningful).

**Exit Criteria**
- [ ] `python -m pytest tests -q` passes.
- [ ] `ruff check src tests` exits 0.
- [ ] `time homedesign render designs/contractor-as-drawn.json --view khach --profile cycles`
      completes without error and reports a wall-clock time; record it, since DEC-012's
      6–10 hour budget assumes roughly 30–50 minutes per frame across 12 views.
- [ ] The resulting `khach` render shows a visible ceiling, skirting at the wall base,
      soft contact shadows under furniture, and no pure-white wall regions.

**Phase Risks**
- **RISK-04-01:** A Cycles CPU frame at 512 samples and 1920×1080 may exceed 50 minutes,
  pushing 12 views past the 10-hour budget. Mitigation: measure one frame first
  (TASK-04-05 exit criterion). If a frame exceeds 50 minutes, reduce `samples` to 256 and
  rely on adaptive sampling plus OpenImageDenoise rather than extending the budget.
- **RISK-04-02:** Light portals require the world to be an HDRI; with a solid-colour world
  they do nothing and merely cost time. Mitigation: PHASE-02 TASK-02-06 is a hard
  prerequisite; assert the world uses an Environment Texture before emitting portals.
- **RISK-04-03:** Extending ceilings to every storey will make the exterior aerial view
  opaque from above. Mitigation: exclude ceilings from the `exterior_aerial` camera's view
  layer rather than not building them.

### PHASE-05 - External, Textured, Lightmapped GLB Viewer

**Goal**
Serve the web viewer's GLB as a real file from `docs/` with compressed PBR textures and a
baked lighting pass, so the viewer shows the same lighting as the stills instead of a flat
ambient-occlusion look.

**Tasks**
- [ ] TASK-05-01: In `src/homedesign/viewer.py`, change `_load_call` so the `full` and
      `floors` builds emit a `fetch`/`GLTFLoader.load` against a sibling `.glb` file
      instead of a base64 data URI. Keep the `light` build's inline base64url path exactly
      as it is — including the base64url (not standard base64) encoding, which is
      deliberate and documented at lines 100–110.
- [ ] TASK-05-02: Raise `INLINE_GLB_LIMIT_BYTES` handling so it applies only to the
      `light` build. Leave the constant's value at `8 * 1024 * 1024` and gate its
      enforcement on `build == "light"`, so the existing error message and the light-build
      contract are preserved.
- [ ] TASK-05-03: Make `write_viewer` copy the `.glb` next to the emitted HTML and return
      both paths, so `docs/` receives `contractor-as-drawn.glb` alongside
      `contractor-as-drawn.html`.
- [ ] TASK-05-04: Bake a combined diffuse+indirect lighting pass from the Cycles scene to
      a per-object image texture, and include it in the GLB export as an emissive or
      base-colour multiply. Add `bake_lightmap(resolution: int)` to
      `src/homedesign/blender/materials.py`.
- [ ] TASK-05-05: Add an HDRI environment to the viewer template so reflective and glossy
      materials have something to reflect. Edit
      `src/homedesign/assets/viewer_template.html` and
      `src/homedesign/assets/floor_viewer_template.html` to load an equirectangular
      environment map and set it as the scene environment.
- [ ] TASK-05-06: Compress GLB textures with KTX2/Basis in `optimize_glb` when a
      compressor is available on `PATH`, and pass through uncompressed when it is not —
      never fail the build on a missing optional compressor.

**File Changes**
- `src/homedesign/viewer.py` (modify): `_load_call` build-conditional loading;
  `INLINE_GLB_LIMIT_BYTES` enforcement gated on the `light` build; `write_viewer` copies
  the GLB; `optimize_glb` optional KTX2 pass.
- `src/homedesign/assets/viewer_template.html` (modify): external GLB URL placeholder and
  environment map.
- `src/homedesign/assets/floor_viewer_template.html` (modify): same.
- `src/homedesign/blender/materials.py` (modify): add `bake_lightmap`.
- `docs/contractor-as-drawn.glb` (create): the served model, written by PHASE-06.
- `tests/test_viewer.py` (create): build-conditional loading tests.

**Function Signatures**
- `_load_call(glb: pathlib.Path, viewer_dir: pathlib.Path, build: str | None = None) -> str` —
  existing signature; returns inline base64url JavaScript for `build == "light"` and an
  external-URL loader call for `"full"` and `"floors"`.
- `write_viewer(model_name: str, glb_path: pathlib.Path, out_dir: pathlib.Path, build: str = "full") -> pathlib.Path` —
  existing signature and return value (the HTML path); now additionally copies `glb_path`
  into `out_dir` for non-`light` builds.
- `bake_lightmap(resolution: int = 1024) -> None` — bakes combined diffuse and indirect
  lighting to a per-object image texture on every mesh in the scene.

**Test Specs**
- `_load_call(glb, viewer_dir, build="light")` → the returned string contains
  `"data:"` and does not contain a bare `.glb` URL.
- `_load_call(glb, viewer_dir, build="full")` → the returned string contains the GLB's
  basename and does not contain `"data:"`.
- `_load_call(glb, viewer_dir, build="light")` where `glb` is 9 MiB → raises with a
  message containing `"exceeds inline limit"`.
- `_load_call(glb, viewer_dir, build="full")` where `glb` is 9 MiB → succeeds, producing an
  external-URL loader call (this is the lifted cap, DEC-006).
- `write_viewer("contractor-as-drawn", glb, out_dir, build="full")` → `out_dir` afterwards
  contains both `contractor-as-drawn.html` and `contractor-as-drawn.glb`.
- `write_viewer("contractor-as-drawn", glb, out_dir, build="light")` → `out_dir` contains
  the HTML only; no `.glb` is copied.
- `optimize_glb(path)` with no compressor on `PATH` → returns without raising and leaves
  the file readable.

**Dependencies**
- PHASE-02 (textures must be in the GLB) and PHASE-04 (the Cycles scene must exist to bake
  from).

**Exit Criteria**
- [ ] `python -m pytest tests -q` passes with the new `tests/test_viewer.py`.
- [ ] `ruff check src tests` exits 0.
- [ ] `homedesign build designs/contractor-as-drawn.json --gltf` produces both an HTML and
      a `.glb` in `output/viewer/`.
- [ ] Serving `docs/` locally with `python -m http.server 8000 --directory docs` and
      opening `http://localhost:8000/contractor-as-drawn.html` shows a textured, lit model
      that orbits, with the floor tabs and plan pane still functioning.
- [ ] `docs/contractor-as-drawn-light.html` still opens correctly as a single
      self-contained file with no sibling `.glb`.

**Phase Risks**
- **RISK-05-01:** GitHub Pages must serve `.glb` with a usable content type and the viewer
  must fetch it same-origin. Mitigation: the GLB sits beside the HTML in `docs/`, so the
  fetch is same-origin and no CORS configuration is needed.
- **RISK-05-02:** A large textured GLB may exceed what a phone GPU can hold, which is the
  stated on-site delivery channel. Mitigation: keep the `light` build as the phone target
  and treat the `full` build as the desktop target; state which is which in
  `docs/index.html`.
- **RISK-05-03:** Lightmap baking on CPU across a whole building is slow and may rival the
  render budget. Mitigation: bake at 1024 px per object and only for the `floors` and
  `full` builds; skip baking for `light`.

### PHASE-06 - Author the Facade, Bake the Full Set, Judge, and Publish

**Goal**
Populate `designs/contractor-as-drawn.json` with the facade content read off the
contractor sheets, run the overnight full-set Cycles bake, judge the result against the
photo-match bar, and publish.

**Tasks**
- [x] TASK-06-01: Read the front pillar and other facade elements off
      `output/contractor_pdf_png/MB_MAI_-_MD-Model.png` (the `MẶT ĐỨNG CHÍNH` sheet) per
      ASM-003. Record each derived dimension, with the sheet feature it came from, in a new
      `## Facade elements` section of `designs/contractor-as-drawn.measurements.md`.
- [x] TASK-06-02: Author the elements into `designs/contractor-as-drawn.json`. At minimum:
      the front pillar as a `column` on `side: "south"`; vertical fins spanning storeys 2,
      3 and 4 per ASM-004; a `band` at the parapet coping; and `panel` treatments around
      the street-facing openings. Keep the existing single Ground fin or replace it with a
      measured one — do not leave it unexamined.
- [x] TASK-06-03: Add `divisions` to every street-facing window in the design, matching the
      pane counts visible on the sheet. Ground-floor entrance doors take a panelled
      division.
- [ ] TASK-06-04: Update `designs/contractor-as-drawn.fidelity.md` — mark items (k), (l),
      (m) and (n) with their new status and state precisely what is now modelled and what
      remains approximate.
- [ ] TASK-06-05: Run the full overnight bake:
      `homedesign render designs/contractor-as-drawn.json --profile cycles` for all 12
      views defined in `meta.views`. Because PHASE-01 changed `model_hash`, every render
      sidecar is stale and the whole set must be regenerated — do not use
      `--skip-existing`.
- [x] TASK-06-06: Judge the result and write `reports/2026-08-30-photoreal-critic.md`. If
      `research/sources/reference-photos/` contains images, compare each interior render
      against the closest reference and score it. If the directory is absent or empty,
      apply ASM-001's binding default: judge against this written rubric and record that
      the photoset gate was not applied. Rubric — each item is pass/fail per frame:
      1. No pure-white or pure-black clipped regions on any lit surface.
      2. Visible surface texture (grain, grout, or weave) on floor, wall and at least one
         furniture item.
      3. Contact shadows present where every object meets the floor.
      4. Visible colour bleed from at least one coloured surface onto an adjacent one.
      5. No object interpenetrating another.
      6. A ceiling is visible or correctly out of frame — never an open top edge.
      7. Furniture reads as furniture, not as boxes.
      Record per-frame pass/fail and re-render any frame failing three or more items.
- [x] TASK-06-07: Regenerate the 2D set and the PDF so the elevation now shows the facade
      elements: `homedesign build designs/contractor-as-drawn.json --gltf` then
      `homedesign pdf designs/contractor-as-drawn.json --require-fresh`.
- [x] TASK-06-08: Publish: `homedesign publish designs/contractor-as-drawn.json`, then
      copy the viewer HTML and its `.glb` into `docs/` and confirm
      `.github/workflows/pages.yml` deploys them.

**File Changes**
- `designs/contractor-as-drawn.json` (modify): facade elements across storeys 0–6;
  `divisions` on street-facing openings. Preserve every existing Vietnamese room id and
  name verbatim, and read/write the file as UTF-8.
- `designs/contractor-as-drawn.measurements.md` (modify): add `## Facade elements` with
  every derived dimension and its sheet source.
- `designs/contractor-as-drawn.fidelity.md` (modify): update items (k), (l), (m), (n).
- `reports/2026-08-30-photoreal-critic.md` (create): per-frame judgement.
- `deliverables/contractor-as-drawn/**` (modify): regenerated by `homedesign publish`.
- `docs/contractor-as-drawn.html`, `docs/contractor-as-drawn.glb`,
  `docs/contractor-as-drawn-floors.html`, `docs/contractor-as-drawn-light.html` (modify):
  republished viewers.

**Function Signatures**
None — no code interfaces change in this phase.

**Test Specs**
- `python -c "import json,io; d=json.load(io.open('designs/contractor-as-drawn.json',encoding='utf-8')); print(sum(len(s.get('facade_elements',[])) for s in d['storeys']))"`
  → prints an integer of at least 12 (the current value is 1).
- `python -c "import json,io; d=json.load(io.open('designs/contractor-as-drawn.json',encoding='utf-8')); print(any(f.get('kind')=='column' for s in d['storeys'] for f in s.get('facade_elements',[])))"`
  → prints `True` (the front pillar now exists).
- `homedesign build designs/contractor-as-drawn.json` → exits 0 with no schema errors,
  proving the authored content validates against the PHASE-01 schema.
- Every `*.png.json` sidecar under `deliverables/contractor-as-drawn/png/` → carries the
  same `model_hash` as `output/compiled/contractor-as-drawn.model.json`.

**Dependencies**
- PHASE-01 through PHASE-05, all complete.
- `output/contractor_pdf_png/MB_MAI_-_MD-Model.png` must exist; it is already committed.

**Exit Criteria**
- [ ] `python -m pytest tests -q` passes.
- [ ] `ruff check src tests` exits 0.
- [ ] `homedesign pdf designs/contractor-as-drawn.json --require-fresh` exits 0 — proving
      no stale renders remain after the `model_hash` change.
- [ ] `homedesign publish designs/contractor-as-drawn.json` exits 0.
- [ ] The regenerated south elevation SVG in `output/svg/` shows the pillar and fins.
- [ ] `reports/2026-08-30-photoreal-critic.md` exists and records a per-frame verdict for
      all 12 views.
- [ ] No interior frame fails three or more rubric items.

**Phase Risks**
- **RISK-06-01:** The overnight bake may fail partway and leave a half-updated set that
  `publish.verify_fresh` rejects. Mitigation: render views one at a time in a loop that
  logs each completion, so a failure can be resumed per view rather than from the start.
- **RISK-06-02:** Authoring facade elements risks inventing articulation the sheet does not
  show, which violates CON-003. Mitigation: TASK-06-01 requires every dimension to be
  recorded with its sheet source *before* authoring; an element with no recorded source is
  not authored.
- **RISK-06-03:** `MẶT ĐỨNG CHÍNH` on `contractor/approval drawing.jpg` is a photograph of
  a folded sheet and is not reliably scalable. Mitigation: measure from the vector
  rasterisation `output/contractor_pdf_png/MB_MAI_-_MD-Model.png`, not from the photograph.

## Gotchas

- **`facade.py` is dead code today.** Do not assume any of it is exercised. It has no
  callers and no committed tests; a stale `tests/__pycache__/test_facade_utils.*.pyc`
  exists but the source test file was never committed. Treat every function in it as
  unverified until PHASE-01 TASK-01-12 covers it.
- **The previous pass's commit message overstates what landed.** Commit `07f9c24` claims
  "facade_elements, divisions, parapet slatted, facade.py resolver, joinery mullions".
  Of those, only `facade.py` itself exists. `divisions` never reached the schema, there is
  no slatted parapet in `railings.py`, and there is no mullion code in `joinery.py`. Verify
  against the source, not the log.
- **Unit boundary.** Millimetres on the pure-Python side, metres only inside
  `src/homedesign/blender/`. `resolve_facade_element` returns millimetres;
  `build_facade_elements` divides by 1000 exactly once per value. A second division is the
  most likely bug in PHASE-01.
- **`plot_width_mm / 2000` is deliberate** in `camera_fit.py` — it converts mm to m and
  halves in one step. It is not a typo for `/ 2` or `/ 1000`.
- **Division-line off-by-one.** `x_i = i * (glass_w + m) - m` places the bar's near edge at
  the pane boundary. A 3-column opening has 2 mullions. Do not "correct" the `- m`.
- **Schema is closed.** `additionalProperties: false` appears at every level of
  `spec/homespec.schema.json`. Any spec field added without a matching schema entry makes
  every design fail validation, including the fixtures in `spec/examples/`.
- **`model_hash` invalidation is expected, once.** PHASE-01 changes it for every design.
  Between PHASE-01 and PHASE-06, `homedesign pdf --require-fresh` and `homedesign publish`
  will correctly refuse to run. Do not work around this by weakening `verify_fresh`.
- **Encoding.** `designs/contractor-as-drawn.json` contains Vietnamese text and is not
  cp1252-decodable. Always pass `encoding="utf-8"` explicitly when reading or writing it;
  the bare `json.load(open(path))` idiom raises `UnicodeDecodeError` on Windows.
- **Never import `bpy` outside `src/homedesign/blender/`,** and inside that directory use
  absolute imports for `homedesign.*` and relative imports only for siblings — those files
  run as top-level Blender scripts, not as package members.
- **The street facade is `south` (max-y).** `north` is min-y. Getting this backwards puts
  the pillar on the rear wall where no camera will ever see it, which will look like the
  feature simply failed to build.
- **Blender version.** EEVEE profiles must run on Blender 4.1 legacy EEVEE; 4.2+ EEVEE
  Next renders every lit surface red on this hardware. Cycles is unaffected but is
  CPU-only — Cycles enumerates zero GPU devices here, so never add a GPU device-selection
  branch that silently no-ops.
- **`scripts/sync_skill.py`.** Changing documented CLI behaviour without running it makes
  CI fail on `--check`, not on the tests.

## Verification Strategy

- **TEST-001:** `python -m pip install -e ".[dev]"` → exits 0.
- **TEST-002:** `ruff check src tests` → exits 0, no output.
- **TEST-003:** `python -m pytest tests -q` → at least `231 passed`, `0 failed`. The
  baseline before this plan is exactly `231 passed in ~26s`.
- **TEST-004:** `python scripts/sync_skill.py --check` → exits 0.
- **TEST-005:** `grep -rn "resolve_facade_element" src/ --include=*.py` → at least two
  matches, one of them in `src/homedesign/compiler.py` (proves PHASE-01 connected the
  module).
- **TEST-006:** `grep -n "or True" src/homedesign/blender/build_scene.py` → no output
  (proves the neighbour short-circuit is gone).
- **TEST-007:**
  `python -c "import json,io; d=json.load(io.open('spec/homespec.schema.json',encoding='utf-8')); print('column' in d['properties']['storeys']['items']['properties']['facade_elements']['items']['properties']['kind']['enum'])"`
  → prints `True`.
- **TEST-008:**
  `python -c "import json,io; d=json.load(io.open('spec/homespec.schema.json',encoding='utf-8')); print('divisions' in d['properties']['storeys']['items']['properties']['openings']['items']['properties'])"`
  → prints `True`.
- **TEST-009:**
  `python -c "import json,io; d=json.load(io.open('designs/contractor-as-drawn.json',encoding='utf-8')); print(sum(len(s.get('facade_elements',[])) for s in d['storeys']))"`
  → prints at least `12` after PHASE-06 (it prints `1` today).
- **TEST-010:** `python -c "import homedesign.asset_cache as a; print(all(a.texture_set(f) for f in ['plaster_painted','ceramic_tile','stone_slab','wood_board','metal_brushed','glass_clear','concrete_formed']))"`
  → prints `True`.
- **TEST-011:** `homedesign build designs/contractor-as-drawn.json` → exits 0 with no
  schema or geometry errors on stderr.
- **TEST-012:** `homedesign pdf designs/contractor-as-drawn.json --require-fresh` → exits
  0 after PHASE-06's full re-render; expected to exit non-zero between PHASE-01 and
  PHASE-06, which is correct behaviour, not a regression.
- **TEST-013:** `homedesign publish designs/contractor-as-drawn.json` → exits 0.
- **MANUAL-001:** Open `output/png/contractor-as-drawn_khach.png` and confirm: the door
  leaf sits flush in its frame and does not intersect the sofa; the sofa is a recognisable
  mesh; the floor shows tile or board texture; a ceiling is present; skirting is visible at
  the wall base; no wall region is pure white.
- **MANUAL-002:** Open `output/png/contractor-as-drawn_exterior_front.png` and confirm the
  building fills well over half the frame width, no neighbour blocks stand in front of it,
  and the front pillar and vertical fins are visible on the street facade.
- **MANUAL-003:** Open the regenerated south elevation SVG in `output/svg/` beside
  `output/contractor_pdf_png/MB_MAI_-_MD-Model.png` and confirm the pillar and fins appear
  at the same relative positions.
- **MANUAL-004:** Run `python -m http.server 8000 --directory docs`, open
  `http://localhost:8000/contractor-as-drawn.html`, and confirm the model loads from the
  external `.glb`, is textured and lit, orbits smoothly, and the floor tabs still switch
  storeys with the plan pane in sync.
- **MANUAL-005:** Open `docs/contractor-as-drawn-light.html` directly from the filesystem
  (no server) and confirm it still renders — proving the inline `light` build is intact.
- **OBS-001:** Record the wall-clock duration of one `--profile cycles` frame before
  starting the full bake. If it exceeds 50 minutes, reduce `cycles.samples` from 512 to
  256 rather than extending the overnight budget past 10 hours (DEC-012).
- **OBS-002:** After PHASE-06, confirm every `*.png.json` sidecar under
  `deliverables/contractor-as-drawn/png/` carries the same `model_hash` as
  `output/compiled/contractor-as-drawn.model.json`.

## Risks and Alternatives

- **RISK-001:** The plan adds roughly 100–300 MB of binary assets to the repository, which
  is irreversible in git history. Mitigation: commit the cache in a single, clearly
  labelled commit; prefer 2K JPEG over 4K PNG; if the total exceeds 300 MB, drop
  peripheral families to 1K before committing rather than after.
- **RISK-002:** The `model_hash` change invalidates every existing render sidecar for
  *every* design in `designs/`, not just `contractor-as-drawn`. Mitigation: `tubehouse-dream`
  and the other designs will show as stale until re-rendered; this is correct behaviour.
  Re-render them, or accept that their published deliverables are pinned to the old hash
  and note it.
- **RISK-003:** Six sequential phases each ending in a full re-render is slow, and PHASE-06
  alone is an overnight job. Mitigation: PHASE-02 through PHASE-05 verify against single
  preview frames (`--profile preview --view khach`), never the full set; only PHASE-06
  runs the complete bake.
- **RISK-004:** DEC-011 forgoes render-quality regression tests, so a later change can
  silently undo this work. Mitigation: PHASE-06's rubric is written into
  `reports/2026-08-30-photoreal-critic.md` so a future pass can re-apply the same
  judgement by hand. Converting the rubric's objectively measurable items (clipped-pixel
  fraction, distinct-material count, mesh interpenetration) into pytest assertions remains
  available as a follow-up.
- **ALT-001:** *Hand-tune this one scene without touching the pipeline.* Fastest route to
  one impressive image; not chosen because the facade pipeline would stay severed, the next
  design would start from massing again, and the missing pillar would recur.
- **ALT-002:** *Stay on EEVEE and buy realism through lighting craft alone* (irradiance
  volumes, portals, tuned exposure). Cheap and fast; not chosen because without global
  illumination the interiors keep the flat, blown-out read that is the primary complaint.
- **ALT-003:** *Golden-image perceptual diff testing.* Catches every regression precisely;
  not chosen under DEC-011, since any lighting change would redden the whole suite and the
  committed PNGs would bloat the repository further on top of RISK-001.
- **ALT-004:** *Cloud or remote GPU rendering.* Would cut the overnight bake to minutes;
  not chosen because it adds credentials, cost, and a moving part the pipeline cannot test
  offline. Revisit if OBS-001 shows the 6–10 hour budget is unworkable.
- **ALT-005:** *Upgrade Blender past 4.1 for EEVEE Next's screen-space GI.* Would give
  cheap approximate bounce light; not chosen because EEVEE Next renders every lit surface
  red on this machine's Intel UHD 620, and the 4.1 candidate order is pinned by an existing
  test (CON-001).

## Suggested Next Step

Execute PHASE-01. It is self-contained, depends on nothing, and its exit criteria are
verifiable without any rendering beyond a single `homedesign build`. Confirm every PHASE-01
exit criterion — in particular that `grep -rn "resolve_facade_element" src/ --include=*.py`
now shows a caller in `compiler.py` — before beginning PHASE-02.
