---
title: "homedesign: Drawing Truth, Real Elevations, Declared Voids, and a Construction-Grade Set"
date: "2026-08-14"
status: "complete"
request: "Implement the Sprint 1–3 roadmap from research/2026-08-14-homedesign-third-pass-brainstorm.md."
plan_type: "multi-phase"
research_inputs:
  - "research/2026-08-14-homedesign-third-pass-brainstorm.md"
  - "research/2026-08-04-homedesign-second-pass-brainstorm.md"
  - "designs/contractor-as-drawn.fidelity.md"
---

# Plan: homedesign — Drawing Truth, Real Elevations, Declared Voids, and a Construction-Grade Set

## Objective

The `homedesign` pipeline compiles a JSON home spec into 2D plans, elevations, sections,
3D renders, a GLB viewer and an A3 architect brief. Its 3D half is trustworthy; its 2D
half is silently producing blank and unlabelled drawings that ship to real users. This
plan fixes three reproduced defects (room names are dropped by the compiler, two of four
elevations are empty sheets, the PDF staleness badge is last-image-wins), then removes
the largest modelling workaround in the repo (the spec cannot express a floor void, so a
fake room is authored to pass a checker), replaces 101 per-build boolean modifiers with
the deterministic rectangle subtraction the codebase already owns, and finishes by
adding the dimensions, brief scaffolding and publish step that separate "a nice brief"
from "a set someone can build from".

## Context Snapshot

- **Current state:** 4,370 LOC of Python in `src/homedesign/`, 134 passing tests, `ruff`
  clean. Two real designs (`designs/tubehouse-dream.json`, 5 storeys / 41 rooms;
  `designs/contractor-as-drawn.json`, 7 storeys / 62 rooms / 101 openings / 193 walls)
  compile with zero errors and zero warnings. Verified defects on this codebase:
  - `compiler._resolve_rooms` never passes `name` to `Room(...)`, so `Room.name` is
    `None` for every room in every design and all four consumers fall back to the room
    `id`. A design authored with `BẾP & ĂN` produces drawings reading `bep_an`.
  - `elevation._wall_on_plane` tests coplanarity with the **plot** boundary.
    `contractor-as-drawn` has a 3,500 mm front setback (walls span y ∈ [3500, 23800] on
    a 25,000 mm plot), so `build_elevation(model, "north")` and `("south")` each return
    only `{ground: 1, outline: 1, level: 7}` — zero walls, zero openings. Across all four
    sides exactly 1 of the model's 101 openings is drawn. Even the plot-filling
    `tubehouse-dream` yields 0 openings on its south elevation.
  - `pdf._gallery_pages` reassigns `caption` inside the per-image loop but interpolates
    it once per page, so a page holding one stale and one fresh render shows no `STALE`
    badge.
  - `designs/contractor-as-drawn.json` carries a fake `storage` room `void_fill` named
    `SÀN GIẢ (Ô THÔNG TẦNG THEO BẢN VẾ)` whose only purpose is to satisfy
    `checks.check_room_support`, replacing the drawing's double-height mezzanine void
    with an enclosed slab.
  - `blender/build_scene.build_walls` applies one EXACT-solver boolean modifier per
    opening (101 per build for `contractor-as-drawn`), while `src/homedesign/rects.py`
    opens with "No booleans — deterministic, artifact-free geometry" and is already used
    for floor slabs, roof voids and section slabs.
- **Desired state:** every drawing carries the authored room names; all four elevations
  project the real building including its openings, parapets and roof; the PDF badges
  staleness per image; the spec can declare floor voids and rooftop structures; wall
  geometry is built by pure rectangle subtraction and unit-tested outside Blender; plans
  carry dimension chains, elevations and sections carry numeric levels, section cut
  positions are spec-driven; `homedesign` can scaffold a brief, target an arbitrary
  output directory, and publish a hash-verified deliverable.
- **Key repo surfaces:** `src/homedesign/compiler.py`, `checks.py`, `plan2d.py`,
  `elevation.py`, `pdf.py`, `validate.py`, `model.py`, `__main__.py`, `placement.py`,
  `rects.py`; `src/homedesign/blender/build_scene.py`, `railings.py`, `materials.py`,
  `procedural_furniture.py`; `spec/homespec.schema.json`; `spec/examples/*.json`;
  `designs/*.json`; `tests/`; `.claude/skills/homedesign/SKILL.md` (mirrored to
  `.agents/skills/homedesign/SKILL.md`); `.github/workflows/ci.yml`.
- **Out of scope:** curved, diagonal or non-orthogonal geometry; split levels; IFC
  export; textures, UV maps, HDRI worlds or a downloaded asset library; structural or
  code certification; MEP routing; cost estimation; GPU rendering; changing the Blender
  version or render-engine selection; redesigning either shipped house's room layout.

## Environment & Conventions

- **Stack:** Python **3.11** (`requires-python = ">=3.11"`; CI pins `3.11`). Runtime
  dependencies: `jsonschema>=4.0`, `ezdxf>=1.0`, `pillow>=10.0`. Dev extra: `pytest>=8.0`,
  `ruff==0.15.7` (exact pin). Packaging is setuptools with a `src/` layout and a console
  script `homedesign = "homedesign.__main__:main"`. Blender is invoked as an external
  subprocess and is **not** a Python dependency.
- **Setup:** `python -m pip install -e ".[dev]"`
- **Build / Run:** the product commands are
  - `homedesign compile designs/<slug>.json`
  - `homedesign plans designs/<slug>.json`
  - `homedesign build designs/<slug>.json [--profile preview|final|cycles] [--gltf]`
  - `homedesign render designs/<slug>.json --view <name> [--profile ...] [--skip-existing] [--detach]`
  - `homedesign pdf designs/<slug>.json [--require-fresh] [--hero <view>] [--brief <path>]`

  `python -m homedesign <subcommand> ...` is equivalent and works without installing.
- **Shell:** every command in this plan is written for a **POSIX shell** (`bash`/`sh`).
  The reference machine is Windows, where Git Bash provides one; on PowerShell the
  heredoc (`python - <<'PY' … PY`) and `for … do … done` forms will not parse — run those
  blocks from Git Bash, or paste their Python bodies into a file and run
  `python thatfile.py`.
- **Test:** full suite `python -m pytest tests -q` (expect `134 passed` before this plan
  begins). Single test: `python -m pytest tests/test_compiler.py::test_demo_compiles_two_storeys -q`.
  Lint: `ruff check src tests` (expect `All checks passed!`). Skill mirror gate:
  `python scripts/sync_skill.py --check` (expect `ok: skill copies match`); regenerate the
  mirror with `python scripts/sync_skill.py`. CI (`.github/workflows/ci.yml`) runs, in
  order: `ruff check src tests`, `python -m pytest tests -q`, `python scripts/sync_skill.py --check`
  on `ubuntu-latest` with Python 3.11. **CI has no Blender and no GPU**, so every test
  added by this plan must run in pure Python or skip cleanly when `bpy` is unimportable.
- **Conventions & traps:**
  - **Units: millimetres everywhere on the pure-Python side, metres everywhere on the
    Blender side. The `/ 1000` conversion happens exactly once, at the boundary** (inside
    `src/homedesign/blender/`). Never introduce a second conversion point.
  - Cardinal convention, used identically by the compiler, plans, elevations and the
    `relative` room placement: **north = min-y, south = max-y, west = min-x, east = max-x**.
    Model `+y` therefore runs from the north edge of the plot toward the south edge.
  - `src/homedesign/blender/**` is the only place `bpy`, `bmesh` or `mathutils` may be
    imported. Those files execute as top-level Blender scripts, so they use **absolute**
    imports (`from homedesign.blender import ...`) except for sibling modules already
    using `from .geom import ...`; follow the existing pattern in each file.
  - Geometry math lives in pure modules under `src/homedesign/` so it is unit-testable
    without Blender.
  - Line length 120 (`ruff.toml`). No other ruff rules are configured; default rule set.
  - All file reads and writes of text must pass `encoding="utf-8"` explicitly — the repo
    hit a real CP1252 mangling bug on Windows with Vietnamese room names, and every text
    I/O site was pinned as the fix. Do not add an unqualified `read_text()`/`write_text()`.
  - Files in `output/` are git-ignored, reproducible artifacts; never hand-edit them.
    Files in `deliverables/` are tracked finals.
  - `activeContext.md` at the repo root records plan status; `lessons.md` records
    correction patterns. Update `activeContext.md` when this plan completes.
- **Repo map:**
  ```
  src/homedesign/            pure Python: compiler, checks, validate, plan2d, elevation,
                             camera_fit, placement, stairs, rects, pdf, viewer, model,
                             errors, render_profiles, orchestrator (subprocess driver), __main__ (CLI)
  src/homedesign/blender/    bpy-only: build_scene (entry point), geom, materials, joinery,
                             railings, roof, furnish, procedural_furniture
  src/homedesign/assets/     three.js, GLTFLoader, OrbitControls, viewer_template.html
  spec/homespec.schema.json  authoritative JSON Schema (Draft 2020-12) for the spec
  spec/examples/             courtyard-fixture, demo-3br-2storey, tubehouse-mini (test fixtures)
  spec/briefs/               hand-authored brief copy JSON, one per design
  designs/                   user-authored real designs + fidelity/measurement ledgers
  tests/                     15 pure-Python pytest files, 134 tests
  scripts/sync_skill.py      mirrors .claude/skills/... -> .agents/skills/... (CI-gated)
  output/                    git-ignored generated artifacts (compiled, svg, dxf, png, blend, gltf, viewer, pdf)
  deliverables/<slug>/       tracked finals (png/, gltf/, viewer/, pdf/)
  ```

## Research Inputs

- From `research/2026-08-14-homedesign-third-pass-brainstorm.md`:
  - The compiler drops `rooms[].name`; the schema documents the field, `model.Room`
    declares it, and four consumers read `room.name or room.id` — but
    `compiler._resolve_rooms` never passes it, so the fallback always fires. Fixing it
    alone is unsafe: `plan2d` and `elevation` interpolate labels into XML unescaped, and
    the real design contains `BẾP & ĂN`, whose bare `&` makes the SVG invalid XML.
  - `elevation._wall_on_plane` selects walls by coplanarity with the plot boundary, which
    silently assumes the building fills its plot. Measured: `contractor-as-drawn` north
    and south elevations each contain zero walls and zero openings. The correct
    definition is an orthographic projection of everything visible from one direction,
    painter-sorted by depth, with the silhouette derived from the projected geometry.
  - `pdf._gallery_pages` computes the `STALE` caption per image and renders it per page;
    a mixed stale/fresh page shows nothing.
  - The spec has no way to declare a floor void, so the flagship design authors a fake
    `storage` room to pass `check_room_support`. Generalising `Storey.floor_voids` (which
    `build_floors_and_stairs`, `_add_top_storey_ceilings` and `build_section` already
    consume correctly) to accept authored rectangles closes the largest fidelity
    concession in the repo and makes the checker stricter rather than weaker.
  - `build_walls` applies one EXACT boolean per opening; the equivalent problem in
    (span, height) space is exactly `rects.subtract_rects`, which the repo already uses
    for slabs and roofs. Converting removes the boolean solver from the build and moves
    wall geometry into the pure, unit-testable half.
  - Measured furniture coverage: 19 of 62 rooms in `contractor-as-drawn` and 16 of 41 in
    `tubehouse-dream`, 53 and 41 items respectively, every item painted with the single
    `furniture` material.
  - No drawing carries any dimension except overall plot width and depth; the title block
    claims "Scale 1:100 @ A3" while the SVG carries only a `viewBox` and is stretched to
    fit the PDF page, so the printed scale is false.
- From `research/2026-08-04-homedesign-second-pass-brainstorm.md` (carried forward,
  still unclosed):
  - `meta.style` remains an enum with exactly one member; wall thicknesses are module
    constants (`EXT_THICKNESS`, `INT_THICKNESS`), so a 150 mm partition is unsayable.
  - `blender/` has zero automated coverage; the `bpy` PyPI wheel makes it CI-able, and
    the highest-value invariants are the ones repeatedly verified by hand: every mesh
    inside the plot, no slab over a declared void, every camera inside its own room.
- From `designs/contractor-as-drawn.fidelity.md`:
  - Section (h): the `SÀN GIẢ` placeholder is "the model's single largest concession to
    the schema: the real building has an open, light-filled double-height space here …
    and this render shows an enclosed mezzanine floor instead."
  - Section (i): the rooftop lift plant room (`Ô KỸ THUẬT THANG MÁY`, +23.800 → +25.800)
    "is a structure on top of the roof, which the schema cannot represent (there is no
    level above the topmost roof)."
  - The room-type approximation table collapses altar room, roof terrace, corridor and
    combined kitchen+dining into `living`/`balcony`/`hall`/`kitchen`; `type` drives floor
    material, furniture, the daylight check, plan fill colour, parapets, ceiling
    suppression and camera selection.
  - The `meta.views` entry named `gieng_troi` ("light well") maps to `room_id: hall_stair`,
    a 955 mm corridor with a floor slab on every level — no light well is modelled.

## Assumptions and Constraints

- **ASM-001:** Elevation horizontal axes are mirrored for the two far sides so each
  elevation reads as if the viewer stands on that side. — **BINDING DEFAULT:** north uses
  `h = x`; **south uses `h = plot_width_mm − x − w`**; west uses `h = y`; **east uses
  `h = plot_depth_mm − y − d`**. Drawing canvas width stays the plot dimension
  (`plot_width_mm` for north/south, `plot_depth_mm` for east/west) so all four elevations
  share one scale.
- **ASM-002:** The elevation silhouette outline is the axis-aligned bounding box of the
  projected primitives, not a true concave silhouette polygon. — **BINDING DEFAULT:**
  emit one `outline` item spanning `h ∈ [min h, max h]` and `z ∈ [0, max(z+h)]` over all
  projected wall/roof/parapet items; if no such item exists, fall back to the plot
  rectangle and the full storey-height sum, matching today's behaviour.
- **ASM-003:** Hidden geometry behind nearer geometry is overpainted, not dashed. —
  **BINDING DEFAULT:** solid painter's-algorithm fill only. No hidden-line rendering.
- **ASM-004:** The maximum unsupported span of a declared floor void before it is flagged
  is not specified anywhere in the repo. — **BINDING DEFAULT:** `min(w, d) > 6000` mm
  emits a **warning**-severity `SpecError` with code `void_span_large`; it never blocks a
  build. `contractor-as-drawn`'s mezzanine void is 3,960 × 8,800 mm, whose `min` is
  3,960 mm, so it does not trip this.
- **ASM-005:** Re-authoring `contractor-as-drawn` to use a declared void is a fidelity
  fix; re-cutting a real light well through its floor plates would be a **design change**
  to a contractor's building. — **BINDING DEFAULT:** PHASE-03 removes the `void_fill`
  placeholder only. The misleading `meta.views` entry named `gieng_troi` is **renamed to
  `hanh_lang_thang`** (stair corridor) so no artifact claims a light well exists; no
  floor plate is cut. Record this in `designs/contractor-as-drawn.fidelity.md`.
- **ASM-006:** Room-type enum growth is bounded to values the shipped designs actually
  need. — **BINDING DEFAULT:** add exactly four values — `terrace`, `wc`, `utility`,
  `courtyard`. Do not add an altar-room or dining-kitchen value; those remain `living`
  and `kitchen`.
- **ASM-007:** The `bpy` PyPI wheel is roughly 1 GB and would dominate CI time. —
  **BINDING DEFAULT:** add an optional extra `[project.optional-dependencies] bpy = ["bpy==4.1.0"]`,
  put Blender-side tests in `tests/test_blender_geometry.py` guarded by
  `pytest.importorskip("bpy")`, and **do not** install the extra in `.github/workflows/ci.yml`.
  The tests skip in CI and run locally via `python -m pip install -e ".[dev,bpy]"`.
- **ASM-008:** Removing `void_fill` changes the compiled model hash of
  `contractor-as-drawn`, invalidating all 12 committed renders. — **BINDING DEFAULT:**
  PHASE-03 re-renders the gallery with `--profile final` (a ~24-minute Blender run on the
  reference machine). If Blender is unavailable on the executing machine, complete every
  other task, leave the stale renders in place, and state the runtime limitation
  explicitly in the phase hand-off rather than guessing or faking artifacts.
- **CON-001:** Renders must run on **Blender 4.1's legacy EEVEE**.
  `orchestrator._CANDIDATES` lists Blender 4.1 ahead of 4.5 deliberately: EEVEE Next
  (Blender 4.2+) miscompiles on the target Intel UHD 620 iGPU and renders every lit
  surface blood red (a white `0.92/0.91/0.88` wall comes out `(194, 34, 53)`, independent
  of view transform and of `raytracing`). This ordering is pinned by
  `tests/test_orchestrator.py::test_blender_candidates_prefer_legacy_eevee_build`. **Do
  not reorder `_CANDIDATES` and do not "upgrade to the newest Blender."** There is no GPU
  path at all on that machine: Cycles enumerates zero OPTIX/CUDA/HIP/oneAPI devices, so
  `--profile cycles` is CPU-only at roughly 170 s/view; `--profile final` (legacy EEVEE)
  is roughly 30 s/view at 1920×1080. Override discovery with the `BLENDER_CMD`
  environment variable.
- **CON-002:** Every spec currently in `spec/examples/` and `designs/` must keep
  compiling. Schema growth is strictly additive with preserved defaults. The one
  deliberate exception is `designs/contractor-as-drawn.json`, which PHASE-03 edits.
- **CON-003:** `spec/homespec.schema.json` sets `"additionalProperties": false` at every
  object level. Any new spec field must be added to the schema in the same commit as the
  code that reads it, or previously valid specs using it will be rejected.
- **CON-004:** CI has no Blender, no GPU and no display. Nothing added by this plan may
  make `python -m pytest tests -q` require Blender.
- **DEC-001:** Floor voids are declared **on the storey**, as `storeys[].voids[]`, not as
  a new room type. This mirrors the existing `roof.voids` shape exactly, keeps a void out
  of the room schedule and the quantity take-off (where the current fake room inflates
  GFA), and needs no enum change.
- **DEC-002:** `check_room_support` is **not** weakened. A declared void on the storey
  below counts toward a room's support; an *undeclared* 0 %-coverage room remains a hard
  error.
- **DEC-003:** `elevation.build_elevation` is rewritten, not patched. Widening the
  coplanarity tolerance would make the setback case look fixed while still omitting every
  opening one room inboard. The draw-model/renderer split (`build_*` produces a list of
  typed primitive dicts; `_svg` and `_dxf` render them) is correct and is preserved.
- **DEC-004:** Shared magic dimensions move into one pure module,
  `src/homedesign/constants.py`, in millimetres. The Blender side derives its metre
  values from it by dividing by 1000, preserving the single-conversion-point rule.

## Specification

### S1 — Elevation projection (PHASE-02)

For elevation side `S`, define the viewing setup:

| S | viewer at | depth coordinate `p` of a primitive | horizontal map `h` | canvas width |
|---|---|---|---|---|
| north | y = −∞, looking toward +y | `y_min` | `h = x`, `w_h = w` | `plot_width_mm` |
| south | y = +∞, looking toward −y | `−y_max` | `h = plot_width_mm − (x + w)`, `w_h = w` | `plot_width_mm` |
| west | x = −∞, looking toward +x | `x_min` | `h = y`, `w_h = h_extent` | `plot_depth_mm` |
| east | x = +∞, looking toward −x | `−x_max` | `h = plot_depth_mm − (y + d)`, `w_h = d` | `plot_depth_mm` |

Symbols: `x`, `y` are the primitive's model minimum corner in millimetres; `w` is its
model extent along x; `d`/`h_extent` is its extent along y; `x_max = x + w`;
`y_max = y + d`. `h` is the primitive's left edge on the drawing in millimetres, `w_h`
its drawn width. Negating the depth for south and east makes "smaller `p` is nearer" true
for all four sides.

**Painter's order.** Emit primitives sorted by `p` **descending** (largest `p` first =
farthest first), so nearer geometry is emitted later and overpaints. Ties are broken by
the emission order listed in S1.2, then by `h`, so output is deterministic.

**S1.1 — Vertical placement.** Every primitive keeps its model `z` (millimetres, growing
upward from ground `z = 0`) and `h_z` (its vertical extent). The existing `_svg` flip
`(MARGIN_MM + total_h_mm − (z + h)) / MM_PER_PX` is unchanged.

**S1.2 — What is projected, in emission order within an equal-depth group:**
1. `wall` — every wall of every storey, both `exterior` and `partition` kinds.
   `z = storey.base_z`, `h_z = storey.height_mm`, `p` from the wall's own model box.
2. `opening` — every opening, emitted **immediately after its host wall** regardless of
   sort key, so it always paints on top of the wall it pierces. `h` is the host wall's
   `h` plus `offset_mm` for north and west, and the host wall's `h` plus
   `(wall_span − offset_mm − width_mm)` for the mirrored sides south and east, where
   `wall_span` is `wall.w` for a horizontal wall and `wall.h` for a vertical wall.
   `z = storey.base_z + sill_mm`, `h_z = head_mm − sill_mm`.
3. `parapet` — for every room whose `type` is in `OPEN_ROOM_TYPES`, one band per side
   returned by `rects.open_edges(room.rect, [other room rects on the same storey])`.
   `z = storey.base_z`, `h_z = PARAPET_HEIGHT_MM` (1100). The band's model box is the
   `PARAPET_THICKNESS_MM`-wide (100) strip inside the room rect on that side, matching
   `blender/railings.build_parapet`.
4. `tread` — every stair tread, drawn as a horizontal line at
   `z = storey.base_z + tread.z`, `h_z = 0`.
5. `roof` — one item per roof, carrying an explicit `points` polygon (see S2).
6. `structure` — one item per `roof.structures[]` entry (see S3), `z = roof.base_z + FLAT_ROOF_THICKNESS_MM`,
   `h_z = structure.height_mm`.

**S1.3 — Non-projected frame items**, emitted first so everything paints over them:
`ground` (a line at `z = 0` spanning the full canvas), `outline` (per ASM-002), and one
`level` line per storey at `z = storey.base_z`.

**S1.4 — Elimination rule.** No visibility culling is performed. Correctness comes from
depth ordering alone: a partition deep inside the plan is emitted, then overpainted by
the nearer exterior wall in front of it. Where no wall stands in front (an open balcony
edge), the partition correctly remains visible.

### S2 — Roof projection polygons (PHASE-02)

Let `x0 = roof.x`, `y0 = roof.y`, `w = roof.w`, `d = roof.d`, `z0 = roof.base_z`, all in
millimetres, and let `FLAT_ROOF_THICKNESS_MM = 200`.

- **flat**: rectangle. `points = [(h0, z0), (h0 + w_h, z0), (h0 + w_h, z0 + 200), (h0, z0 + 200)]`
  where `h0`/`w_h` come from S1's horizontal map. When `roof.voids` is non-empty, emit one
  polygon per fragment of `rects.subtract_rects(x0, y0, w, d, voids)` instead of one for
  the whole rectangle.
- **gable**: the ridge runs along the model **y** axis; `rise = (w / 2) · tan(pitch_deg · π / 180)`.
  - Viewed from north or south (the **gable end**, horizontal axis = model x): a
    pentagon `[(h0, z0), (h0 + w_h, z0), (h0 + w_h, z0), (h_apex, z0 + rise), (h0, z0)]`
    reduced to the triangle `[(h0, z0), (h0 + w_h, z0), (h_apex, z0 + rise)]`, where
    `h_apex = h0 + w_h / 2`.
  - Viewed from east or west (the **eave side**, horizontal axis = model y): the
    rectangle `[(h0, z0), (h0 + w_h, z0), (h0 + w_h, z0 + rise), (h0, z0 + rise)]`.
- **shed**: `rise = w · tan(pitch_deg · π / 180)`, rising toward increasing model x.
  - Viewed from north: `[(h0, z0), (h0 + w_h, z0), (h0 + w_h, z0 + rise), (h0, z0)]`.
  - Viewed from south (mirrored): `[(h0, z0), (h0 + w_h, z0), (h0 + w_h, z0), (h0, z0 + rise)]`
    — i.e. the high edge is drawn at the mirrored horizontal position of model `x = x0 + w`.
  - Viewed from east or west: the rectangle `[(h0, z0), (h0 + w_h, z0), (h0 + w_h, z0 + rise), (h0, z0 + rise)]`.

Symbols: `pitch_deg` is `roof.pitch_deg` in degrees; `rise` is the vertical height in
millimetres from the roof base plane to the ridge (gable) or the high eave (shed);
`h_apex` is the ridge's horizontal position on the drawing in millimetres.

### S3 — Declared floor voids (PHASE-03)

Let `A(r)` be the plan area of rectangle `r` in square millimetres and `O(a, b)` the area
of the axis-aligned overlap of `a` and `b`.

`Storey.floor_voids` after compilation is the **deduplicated union** of:
1. authored `storeys[].voids[]` on **this** storey, and
2. the existing derived voids: every `elevator` room on this storey, plus every
   `elevator` room on the storey below, plus the `stairwell` room on the storey below
   when that storey generated stairs.

Deduplication is unchanged: two rectangles are the same when all four of
`|Δx|, |Δy|, |Δw|, |Δd|` are `≤ 1` mm.

`check_room_support` for a room `R` on storey level `L > L_min`, with `B` the storey at
the next lower level:

```
coverage(R) = ( Σ_{r ∈ B.rooms} O(R.rect, r.rect) + Σ_{v ∈ B.authored_voids} O(R.rect, v) ) / A(R.rect)
```

An error `room_unsupported` is emitted when `coverage(R) < 0.8`. Only **authored** voids
count, never derived ones — a lift shaft is not a beam-spanned opening. This requires
`Storey` to retain the authored voids separately from the merged `floor_voids`.

### S4 — Wall face subtraction (PHASE-04)

For a wall `W` on a storey with base elevation `base_z` and height `H` (millimetres),
define its **face coordinate system**: axis `s` runs along the wall's long axis,
axis `t` runs vertically.

- `span = W.h` when `W.orientation == "vertical"`, else `span = W.w`.
- Each opening `O` on `W` contributes the hole `(O.offset_mm, O.sill_mm, O.width_mm, O.head_mm − O.sill_mm)`.
- `fragments = rects.subtract_rects(0, 0, span, H, holes)`.

Each fragment `(fs, ft, fw, fh)` becomes one solid box in **metres**:

| `W.orientation` | box min corner (m) | box extents (m) |
|---|---|---|
| `vertical` | `(W.x/1000, (W.y + fs)/1000, (base_z + ft)/1000)` | `(W.thickness/1000, fw/1000, fh/1000)` |
| `horizontal` | `((W.x + fs)/1000, W.y/1000, (base_z + ft)/1000)` | `(fw/1000, W.thickness/1000, fh/1000)` |

Symbols: `fs` is the fragment's offset along the wall from its start in millimetres;
`ft` is the fragment's height above the storey floor in millimetres; `fw` and `fh` are
the fragment's extents along `s` and `t` in millimetres.

The area identity that must hold, and is the phase's primary test:
`Σ fragment areas = span · H − Σ (O.width_mm · (O.head_mm − O.sill_mm))` for every wall
whose openings do not overlap (which `compiler._check_opening_overlaps` already
guarantees).

## Phase Summary

| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Land room names safely, badge staleness per image, sweep one-line defects | None | Correct labels on every drawing and schedule; XML-safe writers; honest STALE badges |
| PHASE-02 | Replace the elevation plane test with a real orthographic projection | PHASE-01 | Four non-empty, depth-sorted elevations including openings, parapets and roofs |
| PHASE-03 | Let the spec declare floor voids, rooftop structures and four new room types | PHASE-01 | `storeys[].voids[]`, `roof.structures[]`, stricter `check_room_support`, re-authored flagship design |
| PHASE-04 | Build walls by pure rectangle subtraction instead of boolean modifiers | PHASE-03 | Boolean-free wall geometry, first pure wall-geometry tests, optional `bpy` test suite |
| PHASE-05 | Add dimension chains, numeric levels and spec-driven section cuts | PHASE-02, PHASE-03 | Dimensioned plans, annotated elevations/sections, `meta.sections[]`, honest scale text |
| PHASE-06 | Complete the deliverable path | PHASE-05 | `brief --init`, `--out`, `publish` with hash verification, `site.north_deg`, furniture coverage |

## Detailed Phases

### PHASE-01 - Drawing Truth

**Goal**

Every authored room name reaches every drawing and schedule, without producing invalid
XML; the PDF's staleness badge tells the truth on mixed pages; five one-line defects are
removed.

**Tasks**

- [ ] TASK-01-01: In `src/homedesign/compiler.py`, function `_resolve_rooms`, pass
      `name=r.get("name")` to the `Room(...)` constructor in **both** branches — the
      `"rect" in r` branch and the `relative` branch. Change nothing else in that
      function.
- [ ] TASK-01-02: Create `src/homedesign/xmltext.py` with a single `escape_text` helper
      (see Function Signatures). It must use `xml.sax.saxutils.escape` with the quote
      entity map so `&`, `<`, `>`, `"` and `'` are all escaped, making the output safe in
      both element content and attribute values.
- [ ] TASK-01-03: In `src/homedesign/plan2d.py`, wrap every value interpolated into SVG
      text content with `escape_text`: the room label and area label in `_render_svg`, the
      dimension-line `label` in `_dim_line`, and each `line` in `_title_block`. Leave the
      numeric coordinate formatting untouched.
- [ ] TASK-01-04: In `src/homedesign/elevation.py`, wrap the interpolated `item["label"]`
      in the `level` and `room_label` branches of `_svg` with `escape_text`, and wrap the
      `title` passed to `_title_block`. Import `escape_text` from `.xmltext`.
- [ ] TASK-01-05: In `src/homedesign/pdf.py`, wrap every brief-supplied and model-supplied
      string interpolated into HTML with `escape_text`: `brief['title']` and
      `brief.get('subtitle')` in `_cover_page`, each paragraph in `_narrative_page`, each
      requirement in `_requirements_page`, the storey name / room id / room type cells in
      `_schedule_page`, the room labels in `_opening_schedule_page`, the storey name in
      `_takeoff_page`, and the `<title>` in `render_brief_html`. Do **not** escape
      `_svg_inline` output — it is already-valid XML being inlined deliberately.
- [ ] TASK-01-06: In `src/homedesign/pdf.py`, function `_gallery_pages`, move the `STALE`
      marker from the page heading onto the individual image. Build each image's HTML as
      a `<figure>` containing the `<img>` plus, when stale, a
      `<figcaption class="stale">STALE</figcaption>`. Remove the page-level `caption`
      variable entirely and change the heading back to a plain `<h2>Renders</h2>`. Add a
      `.stale` rule to `PAGE_CSS`: `color:#b00020; font-weight:bold; font-size:10pt;`.
- [ ] TASK-01-07: In `spec/homespec.schema.json`, add `"required": ["type"]` to the
      `storeys.items.properties.roof` object so a roof without a `type` is rejected by
      schema validation instead of raising a bare `KeyError: 'type'` from
      `compiler._derive_roof`.
- [ ] TASK-01-08: In `src/homedesign/__main__.py`, delete the dead
      `p_build.add_argument("--floor", ...)` line and remove `[--floor N]` from the module
      docstring on line 1. In `cmd_compile`, delete the two dead lines that assign
      `out_dir = REPO_ROOT / "output" / "compiled"` and call `out_dir.mkdir(...)` — the
      following `_write_model_json` call creates its own directory.
- [ ] TASK-01-09: Rewrite the module docstring of `src/homedesign/render_profiles.py`. It
      currently claims `final` promotes EEVEE Next; the project reverted to Blender 4.1
      legacy EEVEE. Replace it with: `final` is 256-sample EEVEE at 1920×1080 and its
      `raytracing: True` flag degrades to a harmless no-op under Blender 4.1's legacy
      EEVEE; `cycles` remains an explicit CPU-only opt-in. Change no values in
      `RENDER_PROFILES`.
- [ ] TASK-01-10: Update `.claude/skills/homedesign/SKILL.md` to state that `rooms[].name`
      now appears on plans, sections, DXF text and the PDF room schedule, then run
      `python scripts/sync_skill.py` to regenerate the `.agents/` mirror.

**File Changes**

- `src/homedesign/compiler.py` (modify): add `name=r.get("name")` to the two `Room(...)`
  constructions inside `_resolve_rooms`. Leave `_derive_walls`, `_derive_interiors`,
  `_place_openings` and every other function untouched.
- `src/homedesign/xmltext.py` (create): the `escape_text` helper; no imports beyond
  `xml.sax.saxutils`.
- `src/homedesign/plan2d.py` (modify): import `escape_text`; escape the four text sites
  named in TASK-01-03. Leave `_render_dxf` unchanged — `ezdxf` handles its own encoding.
- `src/homedesign/elevation.py` (modify): import `escape_text`; escape the three text
  sites named in TASK-01-04.
- `src/homedesign/pdf.py` (modify): import `escape_text`; escape the sites in TASK-01-05;
  rework `_gallery_pages` per TASK-01-06; add the `.stale` CSS rule to `PAGE_CSS`.
- `src/homedesign/__main__.py` (modify): the two deletions in TASK-01-08.
- `src/homedesign/render_profiles.py` (modify): docstring only.
- `spec/homespec.schema.json` (modify): add `"required": ["type"]` under the `roof` object
  only. Do not add `required` anywhere else.
- `.claude/skills/homedesign/SKILL.md` (modify) and `.agents/skills/homedesign/SKILL.md`
  (modify, generated): the room-name note.
- `tests/test_compiler.py` (modify): add the name-propagation tests.
- `tests/test_plan2d.py` (modify): add the XML-validity and label tests.
- `tests/test_pdf.py` (modify): add the per-image STALE tests and the HTML-escaping test.
- `tests/test_validate.py` (modify): add the roof-missing-`type` schema test.

**Function Signatures**

- `escape_text(value: object) -> str` — returns `str(value)` with `&`, `<`, `>`, `"` and
  `'` replaced by their XML entities (`&amp;`, `&lt;`, `&gt;`, `&quot;`, `&apos;`); returns
  the empty string when `value` is `None`.

**Test Specs**

- `compile_spec(spec)` where a room is authored as
  `{"id": "bep_an", "type": "kitchen", "name": "BẾP & ĂN", "rect": {...}}` → the compiled
  `Room` has `.name == "BẾP & ĂN"` and `.id == "bep_an"`.
- `compile_spec(spec)` where a room uses `relative` placement **and** carries a `name` →
  the compiled `Room.name` equals the authored name (proves both constructor branches were
  fixed).
- `compile_spec(spec)` where a room carries no `name` → `Room.name is None`.
- `escape_text("BẾP & ĂN")` → `"BẾP &amp; ĂN"`.
- `escape_text(None)` → `""`.
- `escape_text('a<b>"c"')` → `"a&lt;b&gt;&quot;c&quot;"`.
- `plan2d.write_plans(model, tmp_path)` on a model containing a room named `"A & B <x>"`,
  then `xml.etree.ElementTree.fromstring(svg_text)` on every produced `.svg` → parses
  without raising, and `"A &amp; B &lt;x&gt;"` appears in the ground-floor SVG text.
- `plan2d.write_plans(model, tmp_path)` on `spec/examples/demo-3br-2storey.json` with
  every room given a `name` → the ground-floor SVG contains each room's `name` and the
  DXF contains it as a TEXT entity.
- `pdf._gallery_pages([stale_png, fresh_png], embed_images=False, img_dir=tmp, current_hash="abc123")`
  where `stale_png`'s sidecar holds `{"model_hash": "999999"}` and `fresh_png`'s holds
  `{"model_hash": "abc123"}` → the returned HTML contains **exactly one** occurrence of
  `>STALE<`, and that occurrence is inside the same `<figure>` element as
  `stale_png.name`.
- Same call with **both** sidecars stale → **two** occurrences of `>STALE<`.
- Same call with both sidecars fresh → **zero** occurrences of `>STALE<`.
- `pdf.render_brief_html(model, brief, ...)` with `brief["title"] = 'Nhà & Sân'` → the
  HTML contains `Nhà &amp; Sân` and does not contain the raw `Nhà & Sân`.
- `validate_schema({... "roof": {"pitch_deg": 20} ...})` → returns a non-empty list whose
  first `SpecError.code` is `"schema_error"` and whose `message` mentions `'type'`
  (today this returns `[]` and the compiler then raises `KeyError`).

**Dependencies**

- None. All changes are pure Python plus a JSON Schema edit; no Blender required.

**Exit Criteria**

- [ ] `python -m pytest tests -q` reports at least `145 passed` (134 existing + at least
      11 new) and no failures.
- [ ] `ruff check src tests` prints `All checks passed!`.
- [ ] `python scripts/sync_skill.py --check` prints `ok: skill copies match`.
- [ ] `python -m homedesign plans designs/contractor-as-drawn.json` exits 0, and
      `output/svg/contractor-as-drawn_f0.svg` contains the string `BẾP &amp; ĂN`.
- [ ] Every file under `output/svg/` produced by the previous command parses with
      `xml.etree.ElementTree.parse`.

**Phase Risks**

- **RISK-01-01:** Escaping `pdf` output could double-escape the inlined SVG and render
  raw markup as visible text in the brief. Mitigation: `_svg_inline`'s return value is
  explicitly excluded from escaping in TASK-01-05; add an assertion to the PDF test that
  the produced HTML still contains a literal `<svg` substring.
- **RISK-01-02:** Landing room names changes the visible content of every existing plan
  SVG and DXF, so any golden-file expectations elsewhere may fail. Mitigation: the current
  suite has no golden files; run the full suite immediately after TASK-01-01 and before
  the escaping work, so a failure is attributable to one change.

---

### PHASE-02 - Real Elevations

**Goal**

Replace the plot-coplanarity wall filter with a true orthographic projection so all four
elevations depict the actual building, including its openings, balcony parapets, roof and
stairs, correctly ordered front-to-back.

**Tasks**

- [ ] TASK-02-01: Create `src/homedesign/constants.py` holding, in millimetres:
      `PARAPET_HEIGHT_MM = 1100.0`, `PARAPET_THICKNESS_MM = 100.0`,
      `BALUSTRADE_HEIGHT_MM = 900.0`, `RAIL_THICKNESS_MM = 60.0`,
      `FLOOR_SLAB_THICKNESS_MM = 50.0`, `FLAT_ROOF_THICKNESS_MM = 200.0`,
      `SLAB_BAND_MM = 200.0`, and the sets `OPEN_ROOM_TYPES = {"balcony"}` and
      `HABITABLE_TYPES = {"bedroom", "living", "kitchen", "dining", "office"}`. The module
      must import nothing.
- [ ] TASK-02-02: Rewire the existing constants to the new module without changing any
      value: `src/homedesign/blender/railings.py` derives `PARAPET_HEIGHT_M`,
      `PARAPET_THICKNESS_M`, `BALUSTRADE_HEIGHT_M`, `RAIL_THICKNESS_M` by dividing the
      millimetre constants by 1000; `src/homedesign/blender/build_scene.py` derives
      `FLOOR_SLAB_THICKNESS` the same way; `src/homedesign/blender/roof.py` derives
      `FLAT_THICKNESS`; `src/homedesign/elevation.py` imports `SLAB_BAND_MM`;
      `src/homedesign/checks.py` imports `HABITABLE_TYPES` instead of defining it.
- [ ] TASK-02-03: In `src/homedesign/elevation.py`, add the projection helpers described
      in S1: `_view_axes(side, model)` returning the horizontal mapping and depth sign,
      and `_project_box(side, model, x, y, w, d)` returning `(h, w_h, depth)`.
- [ ] TASK-02-04: Rewrite `build_elevation` per S1. Delete `_wall_on_plane`, `_plane_value`,
      `_wall_h_extent` and the `_ELEV` table's `plane`/`value`/`orient`/`ext` keys — they
      encode the wrong definition. Keep the function's signature and its return type (a
      list of primitive dicts) exactly as they are so `_svg`, `_dxf` and every caller are
      unaffected.
- [ ] TASK-02-05: Add roof polygon emission per S2. Extend the primitive dict with an
      optional `"points"` key holding a list of `(h_mm, z_mm)` tuples. Every existing
      primitive keeps its `x`/`z`/`w`/`h` rectangle form; only `roof` uses `points`.
- [ ] TASK-02-06: Add parapet emission per S1.2 item 3, using `rects.open_edges` and
      `constants.OPEN_ROOM_TYPES` so the elevation agrees with what
      `blender/build_scene._add_balcony_parapets` actually builds.
- [ ] TASK-02-07: In `_svg`, add a `points` branch rendering `<polygon points="..." fill="#444"/>`
      and a `parapet` branch rendering a `#666` filled rectangle, and change `outline` to
      use the ASM-002 bounding box. In `_dxf`, add a `points` branch calling
      `msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "ELEV"})` and map
      `parapet` to the `ELEV` layer.
- [ ] TASK-02-08: Update `.claude/skills/homedesign/SKILL.md` — the "Known limitations"
      section should no longer imply elevations only show plot-boundary walls — then run
      `python scripts/sync_skill.py`.

**File Changes**

- `src/homedesign/constants.py` (create): the pure millimetre constants and type sets.
- `src/homedesign/elevation.py` (modify): rewrite `build_elevation`; delete
  `_wall_on_plane`, `_plane_value` and `_wall_h_extent`; add `_view_axes` and
  `_project_box`; extend `_svg` and `_dxf` with `points` and `parapet` branches; replace
  the hardcoded `SLAB_BAND_MM` with the import. **Leave `build_section`, `write_sections`
  and `write_elevations` signatures unchanged.**
- `src/homedesign/blender/railings.py` (modify): derive the four metre constants from
  `homedesign.constants`. Leave `build_parapet` and `build_balustrade` bodies unchanged.
- `src/homedesign/blender/build_scene.py` (modify): derive `FLOOR_SLAB_THICKNESS` from
  `constants.FLOOR_SLAB_THICKNESS_MM`; replace the literal `"balcony"` comparisons in
  `build_walls`, `_add_balcony_parapets` and `_add_top_storey_ceilings` with membership in
  `constants.OPEN_ROOM_TYPES`. Change no other logic.
- `src/homedesign/blender/roof.py` (modify): derive `FLAT_THICKNESS` from
  `constants.FLAT_ROOF_THICKNESS_MM`.
- `src/homedesign/checks.py` (modify): import `HABITABLE_TYPES` from `.constants` and
  delete the local definition. Leave every rule body unchanged.
- `tests/test_elevation.py` (modify): add the projection tests below; keep the three
  existing tests, which must still pass.

**Function Signatures**

- `_view_axes(side: str, model: CompiledModel) -> tuple[str, float, float]` — returns
  `(horizontal_model_axis, canvas_width_mm, mirror_flag)` where `horizontal_model_axis` is
  `"x"` for north/south and `"y"` for east/west, `canvas_width_mm` is `plot_width_mm` or
  `plot_depth_mm`, and `mirror_flag` is `1.0` for north/west and `-1.0` for south/east.
- `_project_box(side: str, model: CompiledModel, x: float, y: float, w: float, d: float) -> tuple[float, float, float]`
  — returns `(h_mm, width_mm, depth_mm)`: the box's left edge on the drawing, its drawn
  width, and its depth key where **smaller is nearer to the viewer**.
- `build_elevation(model: CompiledModel, side: str) -> list[dict]` — unchanged signature;
  now returns frame items followed by every projected primitive in painter's order
  (farthest first). Each dict always carries `kind`, `x`, `z`, `w`, `h`, `label`, `type`,
  and optionally `points`.

**Test Specs**

- `build_elevation(compile_spec(designs/contractor-as-drawn.json), "north")` →
  `len([i for i in items if i["kind"] == "wall"]) > 0` **and**
  `len([i for i in items if i["kind"] == "opening"]) > 0`. This test **fails on the
  current code**, which returns exactly `{ground: 1, outline: 1, level: 7}`.
- Same for `"south"`, `"east"` and `"west"` on the same model → each has `> 0` walls.
- Sum over all four sides of `contractor-as-drawn` of the `opening` primitives → `>= 101`
  (each of the model's 101 openings appears on at least one elevation; openings on
  interior partitions may appear on more than one).
- `build_elevation(compile_spec(spec/examples/tubehouse-mini.json), "south")` →
  `len([i for i in items if i["kind"] == "opening"]) > 0` (currently `0`).
- Painter's order: for `build_elevation(model, "north")`, the list of `wall` items is
  non-increasing in the internal depth key — assert by checking that for every adjacent
  pair of `wall` items `a`, `b` in emission order, `a`'s model `y_min >= b`'s model
  `y_min` minus a 1 mm tolerance. Expose the depth on the primitive as `"depth"` to make
  this assertable.
- Mirroring: for `demo-3br-2storey.json`, take a wall whose model `x ∈ [0, 3000]`; its
  `h` on the **north** elevation is in `[0, 3000]`, and on the **south** elevation is in
  `[7000, 10000]` (plot width 10,000 mm).
- Openings stay inside their host wall on every side: for each `opening` item, there
  exists a `wall` item with `wall.x <= opening.x` and
  `opening.x + opening.w <= wall.x + wall.w + 1`.
- `build_elevation(compile_spec(spec/examples/demo-3br-2storey.json), "north")` → contains
  exactly one `roof` item, it carries a `points` key of length `3` (gable end triangle),
  and `max(z for h, z in points) == roof.base_z + rise` where
  `rise = (roof.w / 2) * tan(radians(20))`.
- `build_elevation(same model, "east")` → the single `roof` item's `points` has length
  `4` (eave-side rectangle).
- `build_elevation(compile_spec(designs/tubehouse-dream.json), "north")` → contains at
  least one `parapet` item with `h == 1100.0`.
- `write_elevations(model, tmp_path)` for all three example specs → every produced `.svg`
  parses with `xml.etree.ElementTree.parse`, and every `.dxf` opens with
  `ezdxf.readfile`.
- Every `outline` item satisfies `x >= 0` and `x + w <= canvas_width_mm + 1` for all four
  sides and all five specs.

**Dependencies**

- PHASE-01 (the `escape_text` import in `elevation.py` must already exist).

**Exit Criteria**

- [ ] `python -m pytest tests -q` passes with at least `156 passed` and no failures,
      including the three pre-existing `test_elevation.py` tests.
- [ ] `ruff check src tests` prints `All checks passed!`.
- [ ] `python - <<'PY'` block below prints `north 45 …` style output with a non-zero wall
      **and** opening count on all four sides:
      ```bash
      python - <<'PY'
      import json, sys, collections
      sys.path.insert(0, "src")
      from homedesign.compiler import compile_spec
      from homedesign.elevation import build_elevation
      m = compile_spec(json.load(open("designs/contractor-as-drawn.json", encoding="utf-8")))
      for side in ("north", "south", "east", "west"):
          c = collections.Counter(i["kind"] for i in build_elevation(m, side))
          print(side, "walls", c["wall"], "openings", c["opening"], "parapets", c["parapet"])
          assert c["wall"] > 0 and c["opening"] > 0, side
      print("OK")
      PY
      ```
- [ ] `python -m homedesign plans designs/contractor-as-drawn.json` exits 0 and
      `output/svg/contractor-as-drawn_elev_north.svg` is larger than 8 KB (today's blank
      sheet is well under that).

**Phase Risks**

- **RISK-02-01:** Emitting every wall of every storey, including partitions, multiplies
  the primitive count on a 7-storey model (193 walls plus 101 openings plus parapets per
  side). Mitigation: the pure drawing pipeline currently runs in 0.35 s for the full
  22-file set; assert in the exit criteria that
  `python -m homedesign plans designs/contractor-as-drawn.json` still completes in under
  10 seconds (`time python -m homedesign plans designs/contractor-as-drawn.json`).
- **RISK-02-02:** SVG files grow substantially, and the PDF inlines them, so the brief's
  HTML could exceed its ~200 KB budget. Mitigation: check
  `wc -c output/pdf/tubehouse-dream-brief.html` after regenerating and, if it exceeds
  400 KB, drop `partition` walls whose projected box is fully covered by an already-emitted
  nearer wall on the same side (a simple interval-coverage test on `h`), which changes no
  visible output.
- **RISK-02-03:** The mirrored horizontal map for south and east is easy to get wrong by
  one wall width. Mitigation: the explicit mirroring test above pins a wall at a known
  model coordinate on both the mirrored and unmirrored side.

---

### PHASE-03 - Declared Voids, Rooftop Structures and Room Types

**Goal**

Make the spec able to express a beam-spanned floor void, a structure standing on the
roof, and four room programmes it currently has to approximate — then remove the fake
`SÀN GIẢ` room from the flagship design.

**Tasks**

- [ ] TASK-03-01: In `spec/homespec.schema.json`, add `storeys.items.properties.voids`: an
      array of objects with `"required": ["x", "y", "w", "d"]`,
      `"additionalProperties": false`, numeric `x`/`y` (`minimum: 0`) and `w`/`d`
      (`exclusiveMinimum: 0`), plus an optional string `reason`. Mirror the shape of the
      existing `roof.voids` definition exactly.
- [ ] TASK-03-02: In `spec/homespec.schema.json`, add `storeys.items.properties.roof.properties.structures`:
      an array of objects with `"required": ["x", "y", "w", "d", "height_mm"]`,
      `"additionalProperties": false`, numeric `x`/`y` (`minimum: 0`), `w`/`d`/`height_mm`
      (`exclusiveMinimum: 0`), plus an optional string `name`.
- [ ] TASK-03-03: In `spec/homespec.schema.json`, extend `rooms.items.properties.type.enum`
      with `"terrace"`, `"wc"`, `"utility"`, `"courtyard"` (ASM-006). Keep all twelve
      existing values.
- [ ] TASK-03-04: In `src/homedesign/model.py`, add `authored_voids: list[Rect]` to the
      `Storey` dataclass (default empty list) and to `CompiledModel.from_dict`, and add
      `structures: list[dict]` to the `Roof` dataclass (default empty list) with matching
      `from_dict` handling. `to_dict` uses `dataclasses.asdict` and needs no change.
- [ ] TASK-03-05: In `src/homedesign/compiler.py`, parse `s.get("voids", [])` into
      `Storey.authored_voids`, and change `_derive_floor_voids` to seed each storey's
      `rects` list with that storey's authored voids before adding the derived
      stairwell/elevator rectangles, keeping the existing 1 mm deduplication (S3).
- [ ] TASK-03-06: In `src/homedesign/compiler.py`, function `_derive_roof`, parse
      `roof_spec.get("structures", [])` into `Roof.structures` unchanged (list of dicts).
- [ ] TASK-03-07: In `src/homedesign/checks.py`, function `check_room_support`, add the
      authored voids of the storey below to the coverage numerator per S3. Add a new rule
      `check_void_spans` emitting warning-severity `void_span_large` when an authored
      void's `min(w, d) > 6000` mm (ASM-004), and register it in `RULES` after
      `room_support`.
- [ ] TASK-03-08: In `src/homedesign/constants.py`, set
      `OPEN_ROOM_TYPES = {"balcony", "terrace", "courtyard"}` and add
      `WET_ROOM_TYPES = {"bathroom", "wc"}`. `HABITABLE_TYPES` is unchanged — none of the
      four new types are habitable.
- [ ] TASK-03-09: In `src/homedesign/plan2d.py`, add `ROOM_FILL` entries: `terrace`
      `#d9e8d0`, `wc` `#cfe3e8`, `utility` `#dcdcdc`, `courtyard` `#e8f0e0`.
- [ ] TASK-03-10: In `src/homedesign/plan2d.py`, draw each storey's authored voids as a
      diagonal-hatched region (an SVG `<pattern>` with 45° lines defined once in `<defs>`,
      referenced by a `<rect fill="url(#voidhatch)">`), plus the void's `reason` string as
      a centred label when present. Add the same rectangle to the DXF on a new `VOIDS`
      layer with colour `4`.
- [ ] TASK-03-11: In `src/homedesign/blender/materials.py`, add `ROOM_FLOOR_KEY` entries
      mapping `wc` → `floor_bathroom`, `utility` → `floor_garage`, `courtyard` →
      `floor_garage`, `terrace` → `floor_default`.
- [ ] TASK-03-12: In `src/homedesign/blender/build_scene.py`, build each
      `roof["structures"]` entry as a `make_box` at
      `z = roof.base_z/1000 + FLAT_ROOF_THICKNESS_MM/1000` with the `roof` material, named
      `structure_<index>`. Also exclude `courtyard` rooms from `_add_top_storey_ceilings`
      (they are open to the sky) — `OPEN_ROOM_TYPES` from TASK-03-08 already does this if
      the function uses the set.
- [ ] TASK-03-13: In `src/homedesign/elevation.py`, emit `roof.structures` as `structure`
      primitives per S1.2 item 6, rendered in `_svg` as a `#333` rectangle and in `_dxf`
      on the `ELEV` layer.
- [ ] TASK-03-14: Edit `designs/contractor-as-drawn.json`: delete the room object with
      `"id": "void_fill"` from `storeys[1]`; add
      `"voids": [{"x": 0, "y": 3500, "w": 3960, "d": 8800, "reason": "Ô THÔNG TẦNG (double-height void per drawing)"}]`
      to `storeys[1]`; retype the two `san_thuong_*` rooms on `storeys[6]` from `balcony`
      to `terrace`; retype every `wc_*` room from `bathroom` to `wc`; add
      `"structures": [{"x": 1960, "y": 16300, "w": 2000, "d": 1800, "height_mm": 2000, "name": "Ô KỸ THUẬT THANG MÁY"}]`
      to `storeys[6].roof`; and rename the `meta.views` entry `"name": "gieng_troi"` to
      `"name": "hanh_lang_thang"` (ASM-005). Leave every rect coordinate unchanged.
- [ ] TASK-03-15: Update `designs/contractor-as-drawn.fidelity.md`: mark section (h)
      **resolved** (the void is now declared, not faked) and section (i) **resolved** (the
      plant room is now a `roof.structures` entry); add a note under the enum table that
      `SÂN THƯỢNG` is now `terrace` and `WC` is now `wc`; and record under ASM-005's
      reasoning that the light well remains unmodelled and the view was renamed rather
      than a floor plate cut.
- [ ] TASK-03-16: Re-render the flagship gallery (ASM-008):
      `python -m homedesign build designs/contractor-as-drawn.json --profile final --gltf`,
      then copy `output/png/contractor-as-drawn_*.png`, `output/png/contractor-as-drawn_*.png.json`,
      `output/gltf/contractor-as-drawn.glb` and `output/viewer/contractor-as-drawn.html`
      into `deliverables/contractor-as-drawn/`. If Blender is unavailable, skip this task
      and state the limitation explicitly.
- [ ] TASK-03-17: Update `.claude/skills/homedesign/SKILL.md` — document `storeys[].voids[]`,
      `roof.structures[]` and the four new room types, and **replace** the current advice
      that a light well is made by leaving a footprint untiled with the recommendation to
      declare a void on each storey. Run `python scripts/sync_skill.py`.

**File Changes**

- `spec/homespec.schema.json` (modify): three additive schema changes (TASK-03-01/02/03).
  Do not relax `additionalProperties` anywhere.
- `src/homedesign/model.py` (modify): `Storey.authored_voids`, `Roof.structures`, and the
  matching `from_dict` parsing. Leave `model_hash`, `write_render_sidecar` and
  `read_render_sidecar` untouched.
- `src/homedesign/compiler.py` (modify): parse voids and structures; seed
  `_derive_floor_voids` with authored voids.
- `src/homedesign/checks.py` (modify): void-aware `check_room_support`; new
  `check_void_spans`; register it in `RULES`.
- `src/homedesign/constants.py` (modify): widen `OPEN_ROOM_TYPES`, add `WET_ROOM_TYPES`.
- `src/homedesign/plan2d.py` (modify): four `ROOM_FILL` entries; void hatch in SVG and a
  `VOIDS` layer in DXF.
- `src/homedesign/elevation.py` (modify): `structure` primitive emission and rendering.
- `src/homedesign/blender/materials.py` (modify): four `ROOM_FLOOR_KEY` entries.
- `src/homedesign/blender/build_scene.py` (modify): build roof structures; use
  `OPEN_ROOM_TYPES` in the ceiling-suppression test.
- `designs/contractor-as-drawn.json` (modify): the six edits in TASK-03-14.
- `designs/contractor-as-drawn.fidelity.md` (modify): resolution notes.
- `spec/examples/courtyard-fixture.json` (modify): add a `storeys[0].voids` entry over the
  existing untiled courtyard gap (`{"x": 0, "y": 4000, "w": 3000, "d": 2000}`) so the new
  construct has a small permanent fixture exercising it.
- `tests/test_compiler.py`, `tests/test_checks.py`, `tests/test_validate.py`,
  `tests/test_plan2d.py` (modify): the tests below.
- `.claude/skills/homedesign/SKILL.md` / `.agents/skills/homedesign/SKILL.md` (modify).

**Function Signatures**

- `check_void_spans(model: CompiledModel) -> list[SpecError]` — returns one
  warning-severity `SpecError` with code `void_span_large` for each authored void whose
  shorter plan dimension exceeds 6000 mm; empty list otherwise.
- `check_room_support(model: CompiledModel) -> list[SpecError]` — unchanged signature; the
  coverage numerator now includes the overlap with the authored voids of the storey below.

**Test Specs**

- A two-storey spec where the upper storey's only room sits entirely over a declared void
  on the lower storey (`voids: [{"x":0,"y":0,"w":4000,"d":4000}]`, no rooms there) →
  `validate_compiled(model)` returns **no** `room_unsupported` error.
- The same spec with the `voids` entry **removed** → `validate_compiled(model)` returns
  exactly one `room_unsupported` error whose message contains `0%` (proves DEC-002: the
  check is not weakened).
- A spec whose lower storey declares `voids: [{"x":0,"y":0,"w":7000,"d":9000}]` →
  `validate_compiled(model)` includes one `SpecError` with `code == "void_span_large"` and
  `severity == "warning"`; `_split_errors` places it in warnings, so
  `python -m homedesign compile <spec>` still exits `0`.
- A spec declaring `voids: [{"x":1000,"y":1000,"w":2000,"d":2000}]` on a storey whose
  `elevator` room occupies `{"x":1000,"y":1000,"w":2000,"d":2000}` → the compiled
  `Storey.floor_voids` has length `1` (the 1 mm deduplication collapsed them), while
  `Storey.authored_voids` has length `1`.
- `compile_spec(designs/contractor-as-drawn.json)` after TASK-03-14 → succeeds;
  `validate_compiled(model)` returns `[]`; no room has `id == "void_fill"`;
  `model.storeys[1].authored_voids` has length `1` with `w == 3960` and `d == 8800`.
- `compile_spec(designs/contractor-as-drawn.json)` → `model.storeys[6].roof.structures`
  has length `1` with `height_mm == 2000`.
- `validate_schema` of a spec using `"type": "terrace"` → `[]`; of a spec using
  `"type": "playroom"` → one `schema_error`.
- `plan2d.write_plans(model, tmp_path)` on the amended `courtyard-fixture.json` → the
  ground-floor SVG contains `url(#voidhatch)` and the ground-floor DXF contains a `VOIDS`
  layer (`ezdxf.readfile(path).layers` contains `"VOIDS"`).
- `build_elevation(compile_spec(designs/contractor-as-drawn.json), "west")` → contains
  exactly one `structure` primitive with `h == 2000.0`.

**Dependencies**

- PHASE-01 (schema edits build on TASK-01-07's `required` addition).
- Blender 4.1 for TASK-03-16 only; every other task is pure Python.

**Exit Criteria**

- [ ] `python -m pytest tests -q` passes with at least `165 passed`.
- [ ] `ruff check src tests` prints `All checks passed!` and
      `python scripts/sync_skill.py --check` prints `ok: skill copies match`.
- [ ] `python -m homedesign compile designs/contractor-as-drawn.json` exits `0` and prints
      no warnings.
- [ ] `python -m homedesign compile designs/tubehouse-dream.json`,
      `spec/examples/demo-3br-2storey.json`, `spec/examples/tubehouse-mini.json` and
      `spec/examples/courtyard-fixture.json` all exit `0` (CON-002).
- [ ] `grep -c void_fill designs/contractor-as-drawn.json` returns `0`.
- [ ] TASK-03-16 complete, or the Blender-unavailable limitation stated explicitly in the
      hand-off.

**Phase Risks**

- **RISK-03-01:** Removing `void_fill` leaves levels 2–4's front bedroom and balcony over
  a declared void, and any error in the S3 coverage change turns a clean design into a
  failing one. Mitigation: the two paired tests above (void present → no error, void
  removed → exactly one error) pin both directions before the design is edited.
- **RISK-03-02:** Retyping `wc_*` rooms from `bathroom` to `wc` changes the compiled model
  and could change furniture and floor materials. Mitigation: TASK-03-11 maps `wc` to the
  same `floor_bathroom` material, and `placement.plan_room` has no `wc` branch so those
  rooms stay unfurnished exactly as they are today; PHASE-06 adds the furniture.
- **RISK-03-03:** The model hash changes, so the committed `deliverables/` renders and
  every sidecar go stale. Mitigation: ASM-008's re-render task, plus PHASE-06's `publish`
  command which makes the mismatch a hard error rather than a silent one.

---

### PHASE-04 - Wall Geometry Without Booleans

**Goal**

Build walls with openings as sets of solid boxes derived by pure rectangle subtraction,
removing every boolean modifier from the scene build and making wall geometry testable
without Blender for the first time.

**Tasks**

- [ ] TASK-04-01: In `src/homedesign/rects.py`, add `wall_face_fragments` (see Function
      Signatures) implementing S4 in millimetres. It must call the existing
      `subtract_rects` rather than re-implementing subtraction.
- [ ] TASK-04-02: In `src/homedesign/blender/build_scene.py`, rewrite `build_walls` to
      call `wall_face_fragments` and emit one `make_box` per fragment, named
      `wall_<wall_id>_<index>`. Delete the per-opening cutter box and the
      `boolean_difference` call. **Keep** the balcony/terrace open-edge suppression at the
      top of the loop and **keep** the `joinery.build_opening_furniture(...)` call for
      every opening — the frames, lintels, sills, glass and door leaves are unchanged.
- [ ] TASK-04-03: In `src/homedesign/blender/geom.py`, delete `boolean_difference` if it
      has no remaining callers after TASK-04-02 (verify with
      `grep -rn boolean_difference src tests`). Leave `make_box` and `make_hinged_box`
      untouched.
- [ ] TASK-04-04: Create `tests/test_wall_fragments.py` with the pure tests below.
- [ ] TASK-04-05: Add an optional dependency group to `pyproject.toml`:
      `[project.optional-dependencies]` gains `bpy = ["bpy==4.1.0"]` (ASM-007). Do **not**
      add it to `.github/workflows/ci.yml`.
- [ ] TASK-04-06: Create `tests/test_blender_geometry.py` opening with
      `bpy = pytest.importorskip("bpy")` so it skips cleanly wherever `bpy` is absent,
      containing the four invariants below.
- [ ] TASK-04-07: Add a `## Blender-side tests` subsection to `AGENTS.md` documenting that
      `python -m pip install -e ".[dev,bpy]"` enables `tests/test_blender_geometry.py`,
      that the suite skips without it, and that CI deliberately does not install it.

**File Changes**

- `src/homedesign/rects.py` (modify): add `wall_face_fragments`. Leave `subtract_rect`,
  `subtract_rects` and `open_edges` byte-identical.
- `src/homedesign/blender/build_scene.py` (modify): rewrite `build_walls` only.
- `src/homedesign/blender/geom.py` (modify): remove `boolean_difference` once unreferenced.
- `pyproject.toml` (modify): add the `bpy` optional-dependency group.
- `tests/test_wall_fragments.py` (create): pure fragment tests.
- `tests/test_blender_geometry.py` (create): `importorskip`-guarded Blender tests.
- `AGENTS.md` (modify): the Blender-side-tests note.

**Function Signatures**

- `wall_face_fragments(span_mm: float, height_mm: float, openings: list[tuple[float, float, float, float]]) -> list[tuple[float, float, float, float]]`
  — returns the solid fragments of a wall face as `(offset_mm, z_mm, width_mm, height_mm)`
  tuples in face coordinates, where each opening is given as
  `(offset_mm, sill_mm, width_mm, head_mm − sill_mm)`. Returns `[(0.0, 0.0, span_mm, height_mm)]`
  when `openings` is empty.

**Test Specs**

- `wall_face_fragments(4000, 3000, [])` → `[(0.0, 0.0, 4000.0, 3000.0)]`.
- `wall_face_fragments(4000, 3000, [(1000, 900, 1200, 1200)])` → four fragments; their
  areas sum to `4000*3000 − 1200*1200 = 10_560_000` mm²; the set of fragments contains one
  with `z == 0.0` and `height == 900.0` spanning the full 4000 mm (the under-sill band) and
  one with `z == 2100.0` and `height == 900.0` spanning the full 4000 mm (the over-head
  band).
- A door at the floor: `wall_face_fragments(4000, 3000, [(1000, 0, 900, 2100)])` → **no**
  fragment has `z == 0.0` with full 4000 mm width; the area sum is
  `4000*3000 − 900*2100 = 10_110_000` mm².
- A full-height full-width opening: `wall_face_fragments(4000, 3000, [(0, 0, 4000, 3000)])`
  → `[]` (the wall is entirely void).
- Two non-overlapping windows: `wall_face_fragments(6000, 3000, [(500, 900, 1000, 1200), (3000, 900, 1000, 1200)])`
  → area sum `6000*3000 − 2*(1000*1200) = 15_600_000` mm²; every returned fragment has
  positive width and height.
- Property test over both shipped designs: for every wall in
  `compile_spec(designs/contractor-as-drawn.json)` and `designs/tubehouse-dream.json`,
  `sum(w*h for _, _, w, h in wall_face_fragments(span, height, holes))` equals
  `span*height − sum(o.width_mm * (o.head_mm − o.sill_mm) for o in openings_on_wall)`
  within `1.0` mm².
- Property test: no two fragments returned for the same wall overlap by more than 1 mm² in
  face coordinates.
- `tests/test_blender_geometry.py` (skips without `bpy`):
  - After building `spec/examples/tubehouse-mini.json`, every mesh object's world bounding
    box lies within `[-0.2, plot_width_m + 0.2] × [-0.2, plot_depth_m + 0.2]`, excluding
    objects whose names start with `ground`, `neighbour` or `street`.
  - No object whose name starts with `floor_` has a bounding box overlapping any declared
    `floor_voids` rectangle by more than 1 % of that rectangle's area.
  - For every `room`-kind view, the camera's world position lies strictly inside its
    room's `interior` (or `rect`) footprint.
  - The set of exterior walls suppressed for open-edge rooms equals, for every such room,
    the set returned by `rects.open_edges(room.rect, other_rects)`.

**Dependencies**

- PHASE-03 (`OPEN_ROOM_TYPES` must already cover `terrace` and `courtyard` so the
  suppression test is meaningful).
- Blender 4.1 or the `bpy==4.1.0` wheel for `tests/test_blender_geometry.py` only.

**Exit Criteria**

- [ ] `python -m pytest tests -q` passes with at least `173 passed` and reports the
      Blender tests as skipped when `bpy` is absent (`python -m pytest tests -q -rs` shows
      `SKIPPED` lines naming `test_blender_geometry.py`).
- [ ] `grep -rn "boolean_difference\|type=\"BOOLEAN\"" src/` returns no matches.
- [ ] `ruff check src tests` prints `All checks passed!`.
- [ ] A full rebuild of the flagship design succeeds and is faster than the previous run:
      `time python -m homedesign build designs/contractor-as-drawn.json --profile preview`
      exits `0`. Record the printed `blender build: <N>s` line and compare it against a
      pre-change run of the same command; the post-change value must not be larger.
      (Skip if Blender is unavailable and state the limitation.)
- [ ] Visual check: `output/png/contractor-as-drawn_khach.png` shows window and door
      openings pierced through the walls exactly as before the change.

**Phase Risks**

- **RISK-04-01:** An off-by-one in the face coordinate mapping puts jamb piers on the
  wrong side of a wall, which the area identity would not catch. Mitigation: the area
  identity test is paired with the non-overlap test and with an explicit assertion that
  the under-sill band spans the full wall; plus the manual visual check in the exit
  criteria.
- **RISK-04-02:** Removing the 20 mm boolean `pad` could expose Z-fighting where a
  fragment meets a joinery frame. Mitigation: the joinery frames sit inside the opening
  void, not coplanar with a fragment face; confirm on the interior render named in the
  exit criteria.
- **RISK-04-03:** The `bpy==4.1.0` wheel is roughly 1 GB and requires Python 3.11 exactly.
  Mitigation: ASM-007 keeps it out of CI entirely; the tests skip when it is missing.

---

### PHASE-05 - Construction-Set Annotation

**Goal**

Put dimensions on the plans, numeric levels on the elevations and sections, let the spec
choose section cut positions, and stop the title block printing a scale that is not true.

**Tasks**

- [ ] TASK-05-01: In `src/homedesign/plan2d.py`, add `_dimension_chain` (see Function
      Signatures) and draw two chains per storey plan: a horizontal chain above the plan at
      every distinct vertical-wall centreline x-coordinate, and a vertical chain left of
      the plan at every distinct horizontal-wall centreline y-coordinate. Each segment is
      labelled with its length in millimetres as an integer. Add an overall dimension
      outside each chain.
- [ ] TASK-05-02: In `src/homedesign/plan2d.py`, replicate both chains into the DXF on a
      `DIMS` layer (the layer already exists) using `msp.add_line` for the witness and
      dimension lines and `msp.add_text` for the values, applying `_dxf_pt` for the y-flip.
- [ ] TASK-05-03: In `src/homedesign/elevation.py`, change the `level` primitive's label
      from the storey name alone to `"<storey name>  +<z in metres to 3 decimal places>"`,
      e.g. `Mezzanine  +3.800`. Add a right-hand overall height dimension line spanning
      `z = 0` to the maximum projected `z`, labelled in metres to 3 decimal places.
- [ ] TASK-05-04: In `src/homedesign/elevation.py`, add opening head and sill annotations
      to sections only (not elevations, where they would collide): for each `cut_wall`
      pierced by an opening, a small `+x.xxx` label at the head. Keep it off the elevation
      to avoid clutter.
- [ ] TASK-05-05: Add `meta.sections` to `spec/homespec.schema.json`: an array of objects
      with `"required": ["name", "axis", "position_mm"]`, `"additionalProperties": false`,
      string `name`, `axis` enum `["x", "y"]`, numeric `position_mm` (`minimum: 0`).
- [ ] TASK-05-06: In `src/homedesign/model.py`, add `sections: list[dict]` to
      `CompiledModel` (default empty) and parse it in `from_dict`; in
      `src/homedesign/compiler.py`, populate it from `spec["meta"].get("sections", [])`,
      emitting a `SpecError` with code `section_out_of_plot` when `position_mm` falls
      outside the plot on the given axis.
- [ ] TASK-05-07: In `src/homedesign/elevation.py`, change `write_sections` to iterate
      `model.sections` when non-empty, writing
      `<name>_section_<section name>.svg`/`.dxf`; when empty, keep today's exact behaviour
      (long `x` at `plot_width_mm / 2` and cross `y` at `plot_depth_mm / 2`, filenames
      `_section_x` and `_section_y`) so existing specs and `pdf._section_pages` are
      unaffected.
- [ ] TASK-05-08: In `src/homedesign/pdf.py`, function `_section_pages`, iterate
      `model.sections` when non-empty (using each section's `name` for both the filename
      and the page heading) and fall back to today's two hardcoded axes otherwise.
- [ ] TASK-05-09: In `src/homedesign/plan2d.py`, function `_title_block`, replace the
      literal `"Scale 1:100 @ A3"` line in every caller with
      `"Scale: use the graphic bar"`. The graphic scale bar drawn by `_scale_bar` scales
      with the drawing and therefore stays truthful at any page size; the numeric claim
      does not. Apply the same change to the `_title_block` call in `elevation._svg`.
- [ ] TASK-05-10: Add `"sections"` documentation to `.claude/skills/homedesign/SKILL.md`,
      note that plans are now dimensioned, and run `python scripts/sync_skill.py`.

**File Changes**

- `src/homedesign/plan2d.py` (modify): `_dimension_chain`; SVG and DXF chains; title-block
  scale text. Leave `_north_arrow`, `_scale_bar` and `_svg_opening` unchanged.
- `src/homedesign/elevation.py` (modify): numeric level labels, overall height dimension,
  section head annotations, `write_sections` iteration over `model.sections`,
  title-block scale text.
- `src/homedesign/model.py` (modify): `CompiledModel.sections` plus `from_dict` parsing.
- `src/homedesign/compiler.py` (modify): populate `sections`; add the
  `section_out_of_plot` error.
- `src/homedesign/pdf.py` (modify): `_section_pages` iteration.
- `spec/homespec.schema.json` (modify): `meta.sections`.
- `designs/contractor-as-drawn.json` (modify): add two named sections —
  `{"name": "long", "axis": "x", "position_mm": 1500}` (through the stair core) and
  `{"name": "cross_bed", "axis": "y", "position_mm": 6900}` (through the front bedroom).
- `tests/test_plan2d.py`, `tests/test_elevation.py`, `tests/test_compiler.py`,
  `tests/test_pdf.py` (modify): the tests below.
- `.claude/skills/homedesign/SKILL.md` / `.agents/skills/homedesign/SKILL.md` (modify).

**Function Signatures**

- `_dimension_chain(coords_mm: list[float], axis: str, offset_px: float, extent_mm: float) -> str`
  — returns the SVG fragment for one dimension chain: a run line, a tick at each
  coordinate, and a millimetre integer label centred between consecutive coordinates.
  `axis` is `"h"` for a horizontal chain drawn above the plan or `"v"` for a vertical
  chain drawn to its left; `offset_px` is the chain's distance from the plan edge in SVG
  pixels; `extent_mm` is the overall plot dimension along that axis.
- `write_sections(model: CompiledModel, out_dir: Path) -> list[Path]` — unchanged
  signature; now emits one SVG and one DXF per entry in `model.sections`, or the two
  legacy centreline sections when `model.sections` is empty.

**Test Specs**

- `_dimension_chain([0.0, 3005.0, 3960.0], "h", 40.0, 3960.0)` → the returned string
  contains `>3005<` and `>955<` (the two segment lengths in millimetres) and exactly three
  tick `<line` elements.
- `_dimension_chain([], "h", 40.0, 3960.0)` → returns a string containing only the overall
  dimension `>3960<` and no tick lines (degenerate input must not raise).
- `plan2d.write_plans(model, tmp_path)` on `designs/contractor-as-drawn.json` → the
  ground-floor SVG contains `>3005<`, and `ezdxf.readfile` on the ground-floor DXF finds at
  least four entities on the `DIMS` layer.
- `build_elevation(model, "north")` on `designs/contractor-as-drawn.json` → every `level`
  primitive's `label` matches the regular expression `^.+\s\+\d+\.\d{3}$`, and the label
  for the storey with `base_z == 3800.0` ends with `+3.800`.
- `compile_spec(spec)` with `meta.sections = [{"name": "long", "axis": "x", "position_mm": 1500}]`
  → `model.sections == [{"name": "long", "axis": "x", "position_mm": 1500}]`.
- `compile_spec(spec)` with `meta.sections = [{"name": "bad", "axis": "x", "position_mm": 99999}]`
  on a 3,960 mm-wide plot → raises `SpecValidationError` containing one error with
  `code == "section_out_of_plot"`.
- `write_sections(model_with_two_named_sections, tmp_path)` → produces
  `svg/<name>_section_long.svg`, `svg/<name>_section_cross_bed.svg` and the two matching
  `.dxf` files; returns four paths.
- `write_sections(model_with_no_sections, tmp_path)` → produces exactly
  `_section_x` and `_section_y` in both formats (today's behaviour, unchanged).
- `plan2d.write_plans(model, tmp_path)` → no produced SVG contains the string
  `Scale 1:100`.

**Dependencies**

- PHASE-02 (the elevation primitives being annotated must already be the projected set).
- PHASE-03 (the flagship design's section positions are chosen against its post-void
  geometry).

**Exit Criteria**

- [ ] `python -m pytest tests -q` passes with at least `182 passed`.
- [ ] `ruff check src tests` prints `All checks passed!` and
      `python scripts/sync_skill.py --check` prints `ok: skill copies match`.
- [ ] `python -m homedesign plans designs/contractor-as-drawn.json` exits `0` and produces
      `output/svg/contractor-as-drawn_section_long.svg` and
      `output/svg/contractor-as-drawn_section_cross_bed.svg`.
- [ ] `grep -rl "Scale 1:100" output/svg/` returns no matches.
- [ ] Every SVG under `output/svg/` still parses with `xml.etree.ElementTree.parse`.

**Phase Risks**

- **RISK-05-01:** Dimension chains drawn at the current `MM_PER_PX = 10.0` scale can
  collide with the north arrow (at SVG 70, 60) and the scale bar (bottom-left). Mitigation:
  place the horizontal chain at `offset_px = 40` above the plan area and the vertical chain
  at `offset_px = 40` left of it, both inside the existing `MARGIN_MM / MM_PER_PX = 100 px`
  margin but outside the plot rectangle; add a test asserting no chain tick has a
  coordinate within 30 px of `(70, 60)`.
- **RISK-05-02:** Renaming section output files breaks `pdf._section_pages`, which
  currently hardcodes `_section_x` and `_section_y`. Mitigation: TASK-05-08 updates it in
  the same phase, and the fallback branch preserves the legacy names for every spec that
  does not declare `meta.sections`.

---

### PHASE-06 - Complete the Deliverable Path

**Goal**

Remove the manual steps between a compiled design and a shippable, internally consistent
deliverable: scaffold the brief, target an arbitrary output directory, publish with hash
verification, make the sun follow a declared north angle, and furnish the room types that
are currently left empty.

**Tasks**

- [ ] TASK-06-01: Add a `brief` subcommand to `src/homedesign/__main__.py` with an
      `--init` flag: `homedesign brief --init designs/<slug>.json` writes
      `spec/briefs/<model name>.json` containing `title` (the model name title-cased),
      `subtitle` (`"<n> storeys, <total GFA> m² on a <W> × <D> m plot"` computed from the
      compiled model), an empty-but-present `narrative` list with one placeholder
      paragraph, and a `requirements` list seeded with three placeholders. Refuse to
      overwrite an existing file unless `--force` is given.
- [ ] TASK-06-02: Add `--out <dir>` to the `compile`, `plans`, `build`, `render` and `pdf`
      subcommands, defaulting to `REPO_ROOT / "output"` so every current invocation
      behaves identically. Thread it through `cmd_compile`, `cmd_plans`, `cmd_build`,
      `cmd_render` and `cmd_pdf` in place of the hardcoded `REPO_ROOT / "output"`.
- [ ] TASK-06-03: Add a `publish` subcommand: `homedesign publish designs/<slug>.json`
      compiles the spec, computes `model_hash`, verifies that **every** PNG in
      `<out>/png/<name>_*.png` has a sidecar whose `model_hash` matches, and only then
      copies `png/`, `gltf/`, `viewer/` and `pdf/` artifacts for that model into
      `deliverables/<name>/`. On any mismatch it prints each offending file and exits `1`
      without copying. Add `--force` to copy anyway (printing a warning per stale file).
- [ ] TASK-06-04: Add `site.north_deg` to `spec/homespec.schema.json`: a number with
      `minimum: 0`, `exclusiveMaximum: 360`, `default: 0`, described as the compass bearing
      in degrees clockwise from model `−y` toward model `+x`. Parse it into
      `CompiledModel.north_deg` in `model.py` and `compiler.py`.
- [ ] TASK-06-05: In `src/homedesign/blender/build_scene.py`, function
      `build_environment`, rotate the sun's Z euler by `north_deg`: replace the hardcoded
      `math.radians(35)` with `math.radians(35 + model.get("north_deg", 0.0))`. Leave the
      55° altitude alone.
- [ ] TASK-06-06: In `src/homedesign/plan2d.py`, function `_north_arrow`, accept a
      `north_deg` argument and add `rotate(<north_deg>)` to the existing `<g transform>`
      so the arrow points at the declared bearing. Pass `model.north_deg` from
      `_render_svg`.
- [ ] TASK-06-07: In `src/homedesign/placement.py`, add planners for the empty room types:
      `hall` → a 0.35 m-deep console along the longest wall when the room is wider than
      1.2 m; `storage`/`utility` → a 0.6 m-deep shelving run along the longest wall;
      `garage` → a 4.5 × 1.8 × 1.4 m `car` block centred when the room fits it;
      `balcony`/`terrace` → two `chair` items and one 0.5 × 0.5 m `planter` when the room
      is at least 1.5 × 1.5 m; `wc` → the existing `wc` and `basin` items from
      `_plan_bathroom` without the shower. Register each in `plan_room`.
- [ ] TASK-06-08: In `src/homedesign/blender/materials.py`, add a `FURNITURE_MATERIAL_KEY`
      dict mapping furniture kinds to palette keys and add the corresponding palette
      entries: `bed`/`sofa` → a new `upholstery` (`0.42, 0.44, 0.48`), `dining_table`/
      `coffee_table`/`desk`/`chair`/`wardrobe`/`shelving`/`console` → the existing
      `furniture` tan, `kitchen_run` → a new `cabinetry` (`0.30, 0.32, 0.34`),
      `wc`/`basin`/`shower` → a new `porcelain` (`0.94, 0.95, 0.96`), `fridge` → the
      existing `frame`, `car` → a new `vehicle` (`0.18, 0.20, 0.26`), `planter` → the
      existing `ground`. Add `furniture_material_key(kind: str) -> str` alongside
      `floor_material_key`.
- [ ] TASK-06-09: In `src/homedesign/blender/procedural_furniture.py`, function
      `build_item`, replace the single `get_material(style, "furniture")` lookup with
      `get_material(style, furniture_material_key(item.kind))`. Add `_build_shelving`,
      `_build_console`, `_build_car` and `_build_planter` builders to `_BUILDERS`; each may
      be a single `place.box`.
- [ ] TASK-06-10: Run `python -m homedesign brief --init designs/contractor-as-drawn.json`,
      fill the generated `spec/briefs/contractor-as-drawn.json` narrative and requirements
      with content drawn from `designs/contractor-as-drawn.fidelity.md` (programme summary
      and the departures list), then run
      `python -m homedesign pdf designs/contractor-as-drawn.json --require-fresh` and
      `python -m homedesign publish designs/contractor-as-drawn.json`.
- [ ] TASK-06-11: Update `.claude/skills/homedesign/SKILL.md` with the `brief --init`,
      `--out` and `publish` commands and the `site.north_deg` field; run
      `python scripts/sync_skill.py`. Update `AGENTS.md`'s Commands block with the two new
      subcommands. Add a completion entry to `activeContext.md` summarising all six phases.

**File Changes**

- `src/homedesign/__main__.py` (modify): `brief` and `publish` subcommands; `--out` on the
  five existing subcommands; thread the directory through every handler.
- `src/homedesign/publish.py` (create): the hash-verification and copy logic used by
  `cmd_publish`, kept out of the CLI module so it is unit-testable.
- `src/homedesign/brief.py` (create): `scaffold_brief` used by `cmd_brief`.
- `src/homedesign/model.py` (modify): `CompiledModel.north_deg` (default `0.0`) plus
  `from_dict` parsing.
- `src/homedesign/compiler.py` (modify): populate `north_deg` from
  `spec["site"].get("north_deg", 0.0)`.
- `src/homedesign/plan2d.py` (modify): rotate the north arrow.
- `src/homedesign/placement.py` (modify): five new planners plus `plan_room` dispatch.
- `src/homedesign/blender/build_scene.py` (modify): sun bearing.
- `src/homedesign/blender/materials.py` (modify): four new palette entries plus
  `furniture_material_key`.
- `src/homedesign/blender/procedural_furniture.py` (modify): per-kind material lookup plus
  four new builders.
- `spec/homespec.schema.json` (modify): `site.north_deg`.
- `spec/briefs/contractor-as-drawn.json` (create): the generated and filled brief copy.
- `tests/test_placement.py`, `tests/test_provenance.py`, `tests/test_compiler.py`
  (modify) and `tests/test_publish.py` (create): the tests below.
- `.claude/skills/homedesign/SKILL.md` / `.agents/skills/homedesign/SKILL.md`,
  `AGENTS.md`, `activeContext.md` (modify).

**Function Signatures**

- `scaffold_brief(model: CompiledModel) -> dict` — returns the brief-copy dictionary with
  keys `title` (str), `subtitle` (str), `narrative` (list[str]) and `requirements`
  (list[str]), derived from the compiled model's name, storey count, total gross floor
  area in square metres and plot dimensions in metres.
- `verify_fresh(model: CompiledModel, out_dir: Path) -> list[tuple[Path, str | None]]` —
  returns one `(png_path, sidecar_hash_or_None)` tuple for every render of this model whose
  sidecar hash does not equal `model_hash(model)`; an empty list means the gallery is
  fully fresh.
- `publish(model: CompiledModel, out_dir: Path, deliverables_dir: Path, force: bool = False) -> list[Path]`
  — copies this model's `png/`, `gltf/`, `viewer/` and `pdf/` artifacts into
  `deliverables_dir / model.name / <subdir>/` and returns the written paths; raises
  `RuntimeError` listing every stale file when `verify_fresh` is non-empty and `force` is
  `False`.
- `furniture_material_key(kind: str) -> str` — returns the palette key for a furniture
  kind, falling back to `"furniture"` for unknown kinds.
- `plan_room(room_type: str, w_m: float, d_m: float) -> list[FurnitureItem]` — unchanged
  signature; now returns a non-empty list for `hall`, `storage`, `utility`, `garage`,
  `balcony`, `terrace` and `wc` in addition to today's six types.

**Test Specs**

- `scaffold_brief(compile_spec(designs/contractor-as-drawn.json))` → the returned dict has
  all four keys; `subtitle` contains `"7 storeys"` and `"3.96"`; `narrative` and
  `requirements` are non-empty lists of strings.
- `verify_fresh(model, out_dir)` with one PNG whose sidecar holds a different hash and one
  whose sidecar matches → a one-element list naming the mismatched PNG.
- `verify_fresh(model, out_dir)` with a PNG that has **no** sidecar file → a one-element
  list whose second tuple element is `None`.
- `publish(model, out_dir, tmp_deliverables)` when `verify_fresh` is non-empty and
  `force=False` → raises `RuntimeError` whose message names the stale file, and
  `tmp_deliverables` is left empty.
- `publish(model, out_dir, tmp_deliverables, force=True)` in the same situation → copies
  the files and returns their paths.
- `publish(model, out_dir, tmp_deliverables)` with an all-fresh gallery → creates
  `tmp_deliverables/<name>/png/`, `/gltf/`, `/viewer/` and `/pdf/` for whichever source
  subdirectories exist, and returns one path per copied file.
- `plan_room("garage", 4.0, 6.0)` → a list containing exactly one item with `kind == "car"`
  whose `w <= 4.0` and `d <= 6.0`.
- `plan_room("garage", 2.0, 2.0)` → `[]` (too small for a car; must not emit an item
  larger than the room).
- `plan_room("hall", 0.9, 4.0)` → `[]` (narrower than the 1.2 m threshold).
- `plan_room("hall", 2.0, 4.0)` → exactly one item with `kind == "console"`.
- `plan_room("terrace", 3.0, 3.0)` → three items: two `chair` and one `planter`.
- `plan_room("wc", 1.6, 2.0)` → two items, `kind`s `{"wc", "basin"}`, and **no** `shower`.
- Every item returned by `plan_room` for every type at every size in
  `{(1.0,1.0), (2.0,3.0), (4.0,6.0), (8.0,10.0)}` satisfies
  `item.x >= 0 and item.y >= 0 and item.x + item.w <= w_m + 1e-9 and item.y + item.d <= d_m + 1e-9`.
- `furniture_material_key("bed")` → `"upholstery"`; `furniture_material_key("nightstand")`
  → `"furniture"` (unknown-kind fallback).
- `compile_spec(spec)` with `site.north_deg = 90` → `model.north_deg == 90.0`; with the
  field absent → `model.north_deg == 0.0`.
- `plan2d.write_plans(model_with_north_deg_90, tmp_path)` → the ground-floor SVG contains
  `rotate(90` inside the north-arrow group.

**Dependencies**

- PHASE-05 (the published PDF should carry the dimensioned drawings).
- Blender 4.1 for TASK-06-10's render freshness only; a headless Chromium (Edge or Chrome,
  auto-detected, overridable with `PDF_BROWSER_CMD`) for the PDF step.

**Exit Criteria**

- [ ] `python -m pytest tests -q` passes with at least `198 passed`.
- [ ] `ruff check src tests` prints `All checks passed!` and
      `python scripts/sync_skill.py --check` prints `ok: skill copies match`.
- [ ] `python -m homedesign brief --init designs/tubehouse-dream.json` exits `1` with a
      "refusing to overwrite" message (the file already exists), and the same command with
      `--force` exits `0`.
- [ ] `python -m homedesign publish designs/contractor-as-drawn.json` exits `0` and
      `deliverables/contractor-as-drawn/pdf/contractor-as-drawn-brief.pdf` exists.
- [ ] `python -m homedesign plans designs/tubehouse-dream.json --out ./.tmp-out` exits
      `0` and writes into `./.tmp-out/svg/`, leaving `output/` untouched. Remove the
      directory afterwards with `rm -rf ./.tmp-out`.
- [ ] Furniture coverage measured with the snippet in TEST-006 below reports at least
      **55 of 62** rooms furnished for `contractor-as-drawn`.

**Phase Risks**

- **RISK-06-01:** `--out` threading can miss a call site and silently split artifacts
  across two directories. Mitigation: after the change,
  `grep -n 'REPO_ROOT / "output"' src/homedesign/__main__.py` must return exactly one
  match — the argparse default.
- **RISK-06-02:** `publish` copying `pdf/img/` would drag in every design's downscaled
  gallery images. Mitigation: copy only files matching `<model name>*` from each source
  subdirectory, and never recurse into `pdf/img/`.
- **RISK-06-03:** Furnishing 36 additional rooms adds objects to the scene and lengthens
  the Blender build. Mitigation: the new builders are one or two boxes each; verify the
  printed `blender build: <N>s` for the flagship preview build has not grown by more than
  20 % over the PHASE-04 measurement.

---

## Gotchas

- **Units.** Millimetres on the pure-Python side, metres inside `src/homedesign/blender/`.
  Every new constant added to `src/homedesign/constants.py` is in millimetres and the
  Blender modules divide by 1000 at the point of use. Do not introduce a second conversion
  site — this is an explicit project rule recorded in `AGENTS.md`.
- **Cardinal directions are y-inverted relative to intuition.** north = min-y, south =
  max-y, west = min-x, east = max-x. Model `+y` runs from the north edge toward the south
  edge. The front camera stands at negative y looking toward `+y`. Getting this backwards
  mirrors every elevation.
- **The SVG y axis grows downward; the DXF and elevation z axes grow upward.** There are
  exactly two flip points in the codebase — `plan2d._dxf_pt` and `elevation._svg`'s
  `px_y_top` — and both are documented as the single place the flip happens. Do not add a
  third.
- **Text encoding.** Both real designs carry Vietnamese diacritics. Every `read_text` and
  `write_text` in this repo passes `encoding="utf-8"` because the locale default (CP1252
  on Windows) previously mangled them. Any new file I/O must do the same.
- **`additionalProperties: false` everywhere in the schema.** A new spec field that is not
  added to `spec/homespec.schema.json` will be rejected by `validate_schema` before the
  compiler ever sees it, and the error will look like an unrelated schema failure.
- **Warnings do not block a build.** `__main__._handle_errors` returns a non-`None` exit
  code only when at least one error has `severity != "warning"`. A rule intended to advise
  (like `void_span_large`) must set `severity="warning"`; a rule intended to block must
  not.
- **A flight of `n` risers has `n − 1` treads** — the top riser lands on the floor above
  and needs no tread object. Any code counting treads (balustrades, section tread lines)
  must not assume the counts are equal. This is documented at the top of
  `src/homedesign/stairs.py`.
- **All meshes bake their world position into their vertices and leave the object origin
  at `(0, 0, 0)`.** Rotating via `obj.rotation_euler` therefore pivots around the world
  origin and flings the mesh away — this shipped once as 32 scattered door leaves. All
  rotation must go through `geom.make_hinged_box`, which rotates vertices about an explicit
  pivot line before the object is created.
- **Changing any compiled geometry changes `model_hash`,** which marks every existing
  render stale and makes `homedesign pdf --require-fresh` exit `1`. PHASE-03 and PHASE-04
  both do this deliberately; budget the re-render.
- **`opening.offset_mm` is measured from the wall segment's start**, which is the wall's
  minimum coordinate along its long axis — not from the room's corner and not from the
  plot origin. On a mirrored elevation side the drawn position is
  `wall_span − offset_mm − width_mm`, not `offset_mm`.
- **`subtract_rect` returns full-width north/south strips first, then middle-band west/east
  strips.** When reusing it for wall faces (S4), the first axis is the wall span and the
  second is height, so the "north strip" is the under-sill band and the "west strip" is the
  left jamb pier. Do not assume the names describe compass directions in that context.
- **Do not reorder `orchestrator._CANDIDATES`.** Blender 4.1 is listed before 4.5 because
  EEVEE Next miscompiles on the target iGPU and renders every lit surface blood red. The
  ordering is pinned by a regression test whose docstring carries the reason.
- **If renders look miscoloured, check which Blender ran before suspecting the design.**
  Re-render one view with `--profile cycles` to confirm the scene data is good. Override
  the executable with the `BLENDER_CMD` environment variable.
- **The `.agents/skills/homedesign/SKILL.md` mirror is CI-gated.** Any edit to
  `.claude/skills/homedesign/SKILL.md` must be followed by `python scripts/sync_skill.py`
  or CI fails on the third step.

## Verification Strategy

- **TEST-001:** `python -m pip install -e ".[dev]" && python -m pytest tests -q` → at least
  `198 passed` after PHASE-06, with no failures and no errors. Per-phase minimums: 145
  (PHASE-01), 156 (PHASE-02), 165 (PHASE-03), 173 (PHASE-04), 182 (PHASE-05), 198
  (PHASE-06). These are floors, not targets — more tests than the minimum is fine, fewer
  means a phase's Test Specs were not all implemented.
- **TEST-002:** `ruff check src tests` → `All checks passed!` after every phase.
- **TEST-003:** `python scripts/sync_skill.py --check` → `ok: skill copies match` after
  every phase that edits the skill document.
- **TEST-004:** All five specs still compile (CON-002):
  ```bash
  for f in spec/examples/courtyard-fixture.json spec/examples/demo-3br-2storey.json \
           spec/examples/tubehouse-mini.json designs/tubehouse-dream.json \
           designs/contractor-as-drawn.json; do
    python -m homedesign compile "$f" >/dev/null || echo "FAILED: $f"
  done
  ```
  → prints nothing.
- **TEST-005:** Elevations are non-empty on every side of every spec (the PHASE-02 gate):
  ```bash
  python - <<'PY'
  import json, sys, collections, glob
  sys.path.insert(0, "src")
  from homedesign.compiler import compile_spec
  from homedesign.elevation import build_elevation
  for f in glob.glob("spec/examples/*.json") + glob.glob("designs/*.json"):
      m = compile_spec(json.load(open(f, encoding="utf-8")))
      for side in ("north", "south", "east", "west"):
          c = collections.Counter(i["kind"] for i in build_elevation(m, side))
          assert c["wall"] > 0, f"{f} {side} has no walls"
      print("ok", f)
  PY
  ```
  → one `ok <path>` line per spec and no assertion error.
- **TEST-006:** Furniture coverage (the PHASE-06 gate):
  ```bash
  python - <<'PY'
  import json, sys
  sys.path.insert(0, "src")
  from homedesign.compiler import compile_spec
  from homedesign.placement import plan_room
  for f in ("designs/contractor-as-drawn.json", "designs/tubehouse-dream.json"):
      m = compile_spec(json.load(open(f, encoding="utf-8")))
      total = furnished = 0
      for s in m.storeys:
          for r in s.rooms:
              total += 1
              rect = r.interior or r.rect
              if plan_room(r.type, rect.w / 1000, rect.d / 1000):
                  furnished += 1
      print(f, furnished, "/", total)
  PY
  ```
  → `designs/contractor-as-drawn.json 55 / 62` or better, and
  `designs/tubehouse-dream.json 33 / 41` or better. Baseline before this plan: `19 / 62`
  and `16 / 41`.
- **TEST-007:** Every generated SVG is valid XML:
  ```bash
  python -m homedesign plans designs/contractor-as-drawn.json >/dev/null
  python - <<'PY'
  import glob, xml.etree.ElementTree as ET
  for p in glob.glob("output/svg/*.svg"):
      ET.parse(p)
  print("all svg parse")
  PY
  ```
  → `all svg parse`.
- **TEST-008:** No boolean modifiers remain (the PHASE-04 gate):
  `grep -rn 'boolean_difference\|type="BOOLEAN"' src/` → no output, exit status 1.
- **TEST-009:** No stale-hash artifacts are publishable:
  `python -m homedesign publish designs/contractor-as-drawn.json` → exit `0` after a fresh
  render; deliberately touching one sidecar's `model_hash` and re-running → exit `1` with
  that file named.
- **MANUAL-001:** Open `output/svg/contractor-as-drawn_elev_north.svg` in a browser after
  PHASE-02. It must show a seven-storey facade with visible window and door openings and
  balcony parapets — not an empty rectangle with dashed lines. Compare against the same
  file generated before the phase.
- **MANUAL-002:** Open `output/svg/contractor-as-drawn_f0.svg` after PHASE-01 and PHASE-05.
  Room labels must read `BẾP & ĂN`, `P.KHÁCH`, `NƠI ĐỂ XE` (not `bep_an`, `khach`, `gara`),
  and dimension chains must run along the top and left edges without overlapping the north
  arrow or the scale bar.
- **MANUAL-003:** After PHASE-04, open `output/png/contractor-as-drawn_khach.png` and
  confirm window and door openings are pierced cleanly through the walls with no visible
  seams, gaps or Z-fighting where the wall meets a window frame.
- **MANUAL-004:** After PHASE-06, open `deliverables/contractor-as-drawn/pdf/contractor-as-drawn-brief.pdf`
  and confirm: no page carries a `STALE` badge; the four elevation pages are not blank; the
  room schedule lists Vietnamese names; and the two section pages are titled `long` and
  `cross_bed`.
- **OBS-001:** Record the `blender build: <N>s` line printed by
  `python -m homedesign build designs/contractor-as-drawn.json --profile preview` before
  PHASE-04 and after it. The post-change value must be less than or equal to the
  pre-change value; note both numbers in `activeContext.md`.

## Risks and Alternatives

- **RISK-001:** PHASE-02 and PHASE-04 both change output that has no golden-file coverage,
  so a regression can pass the suite and only surface visually. Mitigation: MANUAL-001,
  MANUAL-003 and the byte-size / entity-count assertions in the phase exit criteria; each
  phase is independently verifiable before the next begins.
- **RISK-002:** PHASE-03 and PHASE-04 each invalidate the committed render gallery, and the
  reference machine needs roughly 24 minutes per full flagship gallery on CPU-only legacy
  EEVEE. Mitigation: re-render once, at the end of PHASE-04, rather than after each phase;
  ASM-008 permits deferring it with an explicit statement when Blender is unavailable.
- **RISK-003:** The schema gains four new fields (`storeys[].voids`, `roof.structures`,
  `meta.sections`, `site.north_deg`) and four new room-type enum values across three
  phases. A field added to the code but not the schema is rejected before the compiler runs
  (CON-003). Mitigation: every schema task is listed first within its phase, and TEST-004
  compiles all five specs after every phase.
- **RISK-004:** The elevation rewrite emits far more primitives, which could bloat the
  inlined SVG in the PDF past its size budget. Mitigation: RISK-02-02's coverage-culling
  fallback, gated on a measured `wc -c` of the brief HTML.
- **ALT-001:** *Widen the coplanarity tolerance in `_wall_on_plane` instead of rewriting
  `build_elevation`.* Rejected: it would admit the outermost wall on a set-back building
  while still omitting every opening one room inboard, and would leave the south elevation
  of `tubehouse-dream` at zero openings. The definition is wrong, not the tolerance.
- **ALT-002:** *Model voids as a `void` room type rather than `storeys[].voids[]`.*
  Rejected per DEC-001: a void-typed room would appear in the room schedule and inflate the
  gross-floor-area take-off exactly as the current `SÀN GIẢ` placeholder does, and it would
  need special-casing in six consumers that switch on `room.type`.
- **ALT-003:** *Keep boolean modifiers and simply cache the built `.blend`.* Rejected: the
  `.blend` is already cached via `--reuse-blend`, so caching does not help the first build,
  and it would leave wall geometry untestable outside Blender — which is where two of the
  last three defects were found.
- **ALT-004:** *Install the `bpy` wheel in CI so Blender-side tests always run.* Rejected
  per ASM-007: the wheel is roughly 1 GB and would dominate a workflow that currently
  completes in well under a minute. The tests skip cleanly and run locally on demand.

## Suggested Next Step

Execute **PHASE-01**. It is four pure-Python edits, one new 10-line module, one JSON Schema
addition and a documentation sweep; none of it needs Blender; and its test specs — the
name-propagation assertions and the `>STALE<` occurrence counts — provably fail on the
current code. Verify its exit criteria (`python -m pytest tests -q`, `ruff check src tests`,
`python scripts/sync_skill.py --check`, and the `BẾP &amp; ĂN` grep against a freshly
generated `output/svg/contractor-as-drawn_f0.svg`) before beginning PHASE-02.
