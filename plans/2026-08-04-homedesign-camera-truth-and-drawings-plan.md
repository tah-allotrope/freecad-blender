---
title: "homedesign: Camera Truth, EEVEE Next, and the Full Drawing Set"
date: "2026-08-04"
status: "complete"
request: "Implement the roadmap from research/2026-08-04-homedesign-second-pass-brainstorm.md — Sprint 1 (camera truth), Sprint 2 (Blender 4.5 LTS + EEVEE Next, geometric realism), Sprint 3 (elevations/sections, wall inset, artifact provenance, glTF viewer, hygiene)."
plan_type: "multi-phase"
research_inputs:
  - "research/2026-08-04-homedesign-second-pass-brainstorm.md"
  - "research/2026-07-30-homedesign-next-level-brainstorm.md"
---

# Plan: homedesign: Camera Truth, EEVEE Next, and the Full Drawing Set

## Objective

`homedesign` compiles a JSON home spec into 2D plans, a headless Blender scene, a
render gallery and an A3 architect brief. The geometry is correct, but the **depiction
is not**: the exterior camera crops the building out of frame, every interior camera is
placed outside the building, the framing regression test cannot fail on either, the
only validation warning that ever fires is unsatisfiable noise, and the shipped PDF
embeds renders of a model state that no longer exists. This plan fixes depiction first,
then unlocks affordable render quality by moving to Blender 4.5 LTS / EEVEE Next, then
completes the drawing set (elevations and sections) that an architect asks for after
plans.

## Context Snapshot

- **Current state:** 90 tests pass in ~6.5 s; `ruff check src tests` clean; skill-mirror
  CI gate green; EEVEE preview build of `spec/examples/tubehouse-mini.json` completes in
  ~17 s. Despite that, `output/png/tubehouse-mini_exterior.png` shows a featureless wall
  with the building cropped off the top and bottom of frame, and
  `output/png/tubehouse-mini_interior.png` shows the *outside* of the house from 5.26 m
  out on the lawn.
- **Desired state:** every render shows the subject it names; a strengthened framing
  test fails on today's images and passes on the fixed ones; a full-quality gallery
  costs minutes rather than 11.3 hours; balconies have parapets and stairs have
  balustrades; the deliverable set includes four elevations and two sections; artifacts
  carry the identity of the model they were built from; the validation warning channel
  carries signal.
- **Key repo surfaces:**
  - `src/homedesign/camera_fit.py` — pure analytic camera framing (no `bpy`).
  - `src/homedesign/blender/build_scene.py` — headless scene build, cameras, render.
  - `src/homedesign/compiler.py` — spec → `CompiledModel`; wall derivation.
  - `src/homedesign/model.py` — dataclasses for the compiled model.
  - `src/homedesign/checks.py` — validation rule registry.
  - `src/homedesign/plan2d.py` — SVG + DXF writers.
  - `src/homedesign/pdf.py` — A3 brief assembly.
  - `src/homedesign/orchestrator.py` — Blender discovery and subprocess legs.
  - `src/homedesign/__main__.py` — CLI (`compile|plans|build|render|pdf`).
  - `tests/test_framing.py`, `tests/test_camera_fit.py` — the two tests that failed to
    catch the camera defects.
- **Out of scope:** curved or diagonal geometry; split levels; structural or
  code-compliance certification; cost estimation; MEP routing; cloud/multi-user
  service; site-survey or photogrammetry import; reinstating FreeCAD; PBR textures and
  a photoreal furniture asset library (explicitly deferred — see ALT-003).

## Environment & Conventions

- **Stack:** Python 3.11 (`requires-python = ">=3.11"`; the verified local interpreter
  is 3.11.15). Dependencies: `jsonschema>=4.0`, `ezdxf>=1.0`, `pillow>=10.0`. Dev
  extra: `pytest>=8.0`, `ruff==0.15.7` (pinned exactly). Rendering runs in **Blender**
  via subprocess — Blender is not a Python dependency and `bpy` is never importable
  from the test suite.
- **Setup:** `pip install -e ".[dev]"` — this is what CI runs and it installs the
  package editable, so `python -m homedesign ...` works from anywhere in the repo
  **without** `PYTHONPATH=src`. (Existing docs still prescribe the `PYTHONPATH=src`
  prefix; it is harmless but unnecessary. PHASE-06 corrects the docs.)
- **Build / Run:**
  ```bash
  python -m homedesign compile designs/tubehouse-dream.json
  python -m homedesign plans   designs/tubehouse-dream.json
  python -m homedesign build   spec/examples/tubehouse-mini.json      # ~17 s, EEVEE preview
  python -m homedesign render  designs/tubehouse-dream.json --profile final --detach
  python -m homedesign pdf     designs/tubehouse-dream.json
  ```
  Blender is located by `orchestrator.find_blender()` in this order: `$BLENDER_CMD`,
  then `blender`/`blender.exe` on `PATH`, then a hardcoded candidate list. The verified
  local install is `C:/Users/tukum/Blender/blender-4.1.1-windows-x64/blender.exe`
  (Blender **4.1.1**, build date 2024-04-15).
- **Test:** full suite `python -m pytest tests -q` (expect `90 passed` before this plan
  begins) — single test:
  `python -m pytest "tests/test_camera_fit.py::test_fit_distance_2m_cube_margin_1" -v`.
  `pyproject.toml` sets `pythonpath = ["src"]` under `[tool.pytest.ini_options]`, so
  pytest resolves the package without any environment variable.
- **Lint:** `ruff check src tests` must print `All checks passed!`. `ruff.toml` sets
  only `line-length = 120`.
- **Skill mirror gate:** `.claude/skills/homedesign/SKILL.md` is authoritative;
  `.agents/skills/homedesign/SKILL.md` is a generated copy. After editing the
  authoritative file run `python scripts/sync_skill.py` to regenerate the mirror. CI
  runs `python scripts/sync_skill.py --check`, which exits non-zero when they differ.
- **CI:** `.github/workflows/ci.yml`, job `test` on `ubuntu-latest` / Python 3.11, runs
  in order: `pip install -e ".[dev]"`, `ruff check src tests`, `python -m pytest tests -q`,
  `python scripts/sync_skill.py --check`. Blender is **not** available in CI, so any
  Blender-dependent test must skip cleanly when `orchestrator.find_blender()` raises
  `FileNotFoundError` (see the existing guard at `tests/test_framing.py:13-21`).
- **Conventions & traps:**
  - **Units: millimetres everywhere on the pure-Python side, metres everywhere on the
    Blender side.** The `/ 1000` conversion happens exactly once, at the boundary
    inside `src/homedesign/blender/`. Never mix.
  - **Never import `bpy` outside `src/homedesign/blender/.`** Files under that
    directory execute as top-level Blender scripts (`blender --background --python
    <file>`), so they must use **absolute** imports (`from homedesign.camera_fit import
    ...`), never relative ones (`from ..camera_fit import ...`) — relative imports fail
    at runtime there.
  - Cardinal convention: **north = min-y, south = max-y, west = min-x, east = max-x.**
    SVG y grows downward; DXF/CAD y grows upward; `plan2d._dxf_pt` is the single place
    that flip happens.
  - Geometry math lives in pure helpers so it is unit-testable without Blender;
    `src/homedesign/blender/` holds only the `bpy`-facing layer. Preserve this split —
    it is what makes this plan's tests possible.
  - `output/` is git-ignored and treated as reproducible; never hand-edit files there.
- **Repo map:**
  ```
  src/homedesign/            pure Python: compiler, model, checks, validate, stairs,
                             rects, placement, camera_fit, plan2d, pdf, orchestrator,
                             errors, __main__
  src/homedesign/blender/    bpy-only: build_scene, materials, geom, joinery, roof,
                             furnish, procedural_furniture
  src/ifc_export_utils.py    ORPHANED (276 LOC, no importers, targets a retired spec
                             format, its `ifcopenshell` dependency is gone)
  designs/                   user-authored specs (tubehouse-dream.json)
  spec/examples/             fixtures: tubehouse-mini, demo-3br-2storey, courtyard-fixture
  spec/homespec.schema.json  authoritative spec schema
  spec/briefs/               PDF brief copy, one JSON per design
  tests/                     12 pytest files, 90 tests
  scripts/sync_skill.py      skill-mirror sync + --check gate
  output/                    git-ignored artifacts: svg/ dxf/ png/ blend/ pdf/ compiled/ logs/
  ```

## Research Inputs

- From `research/2026-08-04-homedesign-second-pass-brainstorm.md`:
  - `camera_fit.fit_distance` (`src/homedesign/camera_fit.py:62-63`) adds the depth term
    when it must subtract it. The camera is placed at `centre - dist * forward`, so
    camera-to-corner distance along the view axis is `dist + dot(v, forward)`; the
    constraint `|lateral| <= tan * (dist + dot(v, f))` rearranges to
    `dist >= |lateral|/tan - dot(v, f)`. All four existing `fit_distance` tests fit a
    box **centred on** the passed `centre`, where both signs return the identical
    maximum — the defect is mathematically invisible to the suite.
  - Reproduced on `spec/examples/tubehouse-mini.json` (4 × 12 m plot, 9.2 m tall,
    35 mm lens): `fit_distance` returns 10.693, camera lands at y = −4.693, giving a
    real camera-to-facade distance of **4.69 m** where **15.90 m** is required — the
    facade overflows the frame **3.4×**. Flipping the sign yields 23.7 → camera at
    y = −17.7 → 17.7 m clearance, correct with margin.
  - Every interior camera lands outside the building: `_build_room_camera`
    (`build_scene.py:222-254`) places the camera at `min_y - dist`, i.e. beyond the near
    wall. Measured on `tubehouse-mini`, **0 of 6 room cameras are inside their room**
    (the `living` camera sits at y = −5.26 m for a room spanning y ∈ [0, 5]). This is
    *not* fixed by the sign correction — the room bbox is centred on the passed centre,
    so the sign cancels there; the sign fix actually pushes the camera further out.
  - `tests/test_framing.py::test_tubehouse_mini_exterior_framed` asserts only that the
    non-sky bounding box occupies 30–95% of the frame, scanning the top 55% of the
    image. A building that *overflows* the frame produces a bbox from row 0 to the scan
    limit — comfortably inside 30–95%. It **passes** on the broken render.
  - Across all four specs in the repo every emitted warning is `wall_outside_plot`
    (63 on `designs/tubehouse-dream.json`, 24 / 23 / 14 on the fixtures; no other code
    has ever fired). The rule is unsatisfiable by construction — exterior walls are
    centred on the room edge, so a 200 mm wall always projects 100 mm past the plot
    line — which both destroys the warning channel and leaves a real fact undisclosed:
    the "4.0 m" tube house is built 4.2 m wide.
  - `output/pdf/tubehouse-dream-brief.pdf` (Aug 1 16:52) combines SVG plans regenerated
    Aug 1 16:43 with PNG renders dated **Jul 6**, produced before buildable stairs,
    floor voids and the opening-overlap fix. No artifact records the identity of the
    model it came from, so `pdf` silently assembles whatever is on disk.
  - Blender is **4.1.1** — legacy EEVEE, no ray-traced GI, no AgX view transform.
    Blender 4.2+ ships EEVEE Next with real-time ray tracing.
    `build_scene._set_engine` already tries `BLENDER_EEVEE_NEXT` before
    `BLENDER_EEVEE`, so the code is ready and only the runtime is behind.
  - Missing physical elements that read as wrong before textures do: no railings or
    parapets on `balcony` rooms (`designs/tubehouse-dream.json` has a 5-storey open roof
    terrace with no edge protection), no stair balustrade, no ceiling on the top storey,
    no window reveals or sills, no neighbouring party walls for a house that is by
    definition sandwiched.
  - No elevations and no sections exist. The retired FreeCAD pipeline produced
    `front_facade_elevation.dxf` (the stale file is still in `output/dxf/`); the
    replacement pipeline never has. Both are fully derivable from `CompiledModel` in
    pure Python.
  - `src/ifc_export_utils.py` is 276 LOC with zero importers, targets the retired spec
    format, and its `ifcopenshell` dependency has been removed from `pyproject.toml`, so
    it cannot execute. Recommendation adopted: delete it.
- From `research/2026-07-30-homedesign-next-level-brainstorm.md`:
  - The pure/`bpy` split (`src/homedesign/` vs `src/homedesign/blender/`) is the repo's
    strongest structural asset and is what makes camera and drawing logic unit-testable
    without Blender. Preserve it.
  - Rectilinear, axis-aligned geometry is a deliberate constraint: it is what makes the
    sweep-line wall derivation deterministic. Do not generalise it.
  - Backwards compatibility is required for every spec under `spec/` and `designs/`;
    schema growth must be additive with defaults preserved.
  - On this hardware Cycles has **no GPU backend** (Intel UHD 620 offers no
    CUDA/OPTIX/HIP path), and the last full Cycles gallery cost **11.3 hours**. Render
    strategy must not assume a GPU appears.

## Assumptions and Constraints

- **DEC-001:** Interior and exterior cameras use **different algorithms**. Pull-back
  framing ("move back until the subject fits") has no solution indoors because a wall
  occupies the pull-back position. Interior cameras are constrained inside the room and
  choose a focal length to suit; exterior cameras keep the analytic pull-back fit.
- **DEC-002:** `src/ifc_export_utils.py` is **deleted**, not rewired. It is recoverable
  from git history; IFC export deserves a clean implementation against `CompiledModel`
  when it is actually scheduled, and is out of scope here.
- **DEC-003:** Backwards compatibility is mandatory. Every spec under `spec/examples/`
  and `designs/` must still compile after every phase. New spec fields are additive with
  defaults that reproduce current behaviour.
- **DEC-004:** Textures, HDRI environment maps and a photoreal furniture asset library
  are deferred out of this plan. The geometric realism items in PHASE-03 change what the
  drawing *says*; textures only change how it looks, and they are gated on PHASE-02's
  engine outcome anyway.
- **ASM-001:** Blender 4.5 LTS can be installed alongside the existing 4.1.1 without
  removing it. — **BINDING DEFAULT:** install 4.5 LTS to a sibling directory and select
  it per-run with the `BLENDER_CMD` environment variable; never uninstall or overwrite
  4.1.1, so any phase can be re-verified against the old runtime.
- **ASM-002:** If EEVEE Next output is judged unacceptable for the `final` profile after
  the PHASE-02 benchmark. — **BINDING DEFAULT:** keep EEVEE Next as `final` anyway and
  retain Cycles as the explicit `--profile cycles` path; do not block later phases on
  this judgement. Record the benchmark numbers in `docs/lessons-learned.md` either way.
- **ASM-003:** The interior-camera eye height and wall inset are not specified anywhere
  in the repo. — **BINDING DEFAULT:** eye height **1.5 m** above the storey floor, wall
  inset **0.35 m** from the interior face of the near wall, focal length clamped to the
  range **[12.0, 24.0] mm**.
- **ASM-004:** Which sides get elevations and where sections are cut is unspecified. —
  **BINDING DEFAULT:** emit all four elevations (`north`, `south`, `east`, `west`) plus
  two sections — a **long** section on the plane `x = plot_width_mm / 2` and a **cross**
  section on the plane `y = plot_depth_mm / 2`.
- **ASM-005:** Whether neighbouring party-wall massing should be built for every design
  is unspecified. — **BINDING DEFAULT:** add an optional `site.context` object; when it
  is absent, build neighbour massing **only** when `site.plot_width_mm <= 6000` (the
  sandwiched-urban-lot case), and never otherwise.
- **ASM-006:** Whether exterior walls should be centred on room edges or inset inside
  them is a real modelling choice with different correct answers per project. —
  **BINDING DEFAULT:** add `site.wall_alignment` with values `"centre"` (default,
  reproduces today's geometry exactly) and `"inside"` (exterior walls moved inward so
  their outer face lands on the plot line). Set `"inside"` on
  `designs/tubehouse-dream.json` only.
- **ASM-007:** The provenance identifier format is unspecified. — **BINDING DEFAULT:**
  the SHA-256 hex digest of `json.dumps(model.to_dict(), sort_keys=True,
  separators=(",", ":")).encode("utf-8")`, truncated to the first 12 hex characters.
- **CON-001:** No Cycles GPU backend exists on the target machine (Intel UHD 620: no
  CUDA/OPTIX/HIP; oneAPI requires Arc). All render-economics work must assume CPU-only
  Cycles, which is why EEVEE Next is the strategy.
- **CON-002:** Blender is unavailable in CI. Every Blender-dependent test must skip
  cleanly when `orchestrator.find_blender()` raises `FileNotFoundError`, matching the
  existing guard in `tests/test_framing.py`.
- **CON-003:** Files under `src/homedesign/blender/` run as top-level Blender scripts.
  Absolute imports only; `bpy` must never be imported from anywhere else in the tree.
- **CON-004:** Geometry stays rectilinear and axis-aligned throughout. Parapets,
  balustrades, elevations and sections are all axis-aligned box or line work.

## Specification

### S1 — Corrected fit distance (PHASE-01)

The camera sits at `P = C − d·F`, where `C` is the fit centre, `F` the unit forward
vector and `d` the distance being solved for. For a subject corner `X`, let
`v = X − C`. Decompose `v` onto the camera basis `(R, U, F)` (right, up, forward — all
unit, mutually orthogonal):

```
lateral_x = |v · R|          horizontal offset of the corner from the view axis, metres
lateral_y = |v · U|          vertical   offset of the corner from the view axis, metres
depth     =  v · F           signed offset along the view axis, metres
                             (positive = farther from the camera than C)
```

The corner's distance from the camera measured along the view axis is `d + depth`. It
stays inside the frustum when:

```
lateral_x <= tan_x · (d + depth)        and        lateral_y <= tan_y · (d + depth)
```

Solving each for `d` gives the required pull-back for that corner:

```
d_x = lateral_x / tan_x − depth
d_y = lateral_y / tan_y − depth
```

**The minus sign is the whole fix.** The current code writes `+ depth`
(`src/homedesign/camera_fit.py:62-63`). The final distance is
`max(MIN_DISTANCE, margin · max over all corners of max(d_x, d_y))`.

Half-FOV tangents, with `sensor_fit = "HORIZONTAL"` and sensor width `S = 36.0 mm`:

```
tan_x = S / (2 · f)                       f = focal length, millimetres
tan_y = (S · res_y) / (2 · f · res_x)     res_x, res_y = render resolution, pixels
```

Sanity check the fix must reproduce: a 2 × 2 × 2 m cube centred on `C`, `f = 50 mm`,
1920 × 1080, `margin = 1.0` → `d = 1/tan_y + 1 = 5.93827160493827`. This is unchanged
by the sign fix (symmetric box), which is exactly why a new off-centre test is required.

### S2 — Interior camera placement (PHASE-01)

Given a storey and a room, all lengths in metres:

1. `base_z = storey.base_z_mm / 1000` — the storey's floor elevation.
2. `ceil_z = base_z + min(storey.height_mm / 1000, 2.4)` — visible ceiling height, capped
   at 2.4 m so a tall storey does not force an absurdly wide lens.
3. Room interior rect: the room rect shrunk by `wall_inset_m` on all four sides.
   `long_is_depth = (room.d >= room.w)`.
4. View axis: `F = (0, 1, 0)` when `long_is_depth`, else `F = (1, 0, 0)`.
5. Camera position `P`: on the room's centre line of the short axis, `wall_inset_m`
   inside the near face along the long axis, at `z = min(base_z + eye_height_m,
   ceil_z − 0.15)`.
   - `long_is_depth`: `P = (x + w/2, y + wall_inset_m, z)`
   - otherwise:       `P = (x + wall_inset_m, y + d/2, z)`
6. Available depth `L = long_dimension − 2 · wall_inset_m` — the distance from the
   camera to the far interior face, metres. Clamp to a minimum of 0.5.
7. Half-extents that must fit at distance `L`:
   ```
   hw = short_dimension / 2 − wall_inset_m      clamped to a minimum of 0.3
   hv = max(z − base_z, ceil_z − z)             the larger of floor-drop and head-room
   ```
8. Focal length: the largest `f` that fits **both**, then clamped:
   ```
   f_x = (S · L) / (2 · hw)
   f_y = (S · res_y · L) / (2 · res_x · hv)
   f   = clamp(min(f_x, f_y), lens_min_mm, lens_max_mm)
   ```
   with `S = 36.0` mm, `lens_min_mm = 12.0`, `lens_max_mm = 24.0` (ASM-003).
9. Look-at target `T`: the far end of the room's centre line, 0.2 m below eye height, so
   the shot tilts slightly down onto the floor and furniture.
   - `long_is_depth`: `T = (x + w/2, y + d − wall_inset_m, z − 0.2)`
   - otherwise:       `T = (x + w − wall_inset_m, y + d/2, z − 0.2)`

**Invariant this must satisfy, asserted by test:** `P` lies strictly inside the room
rect in both x and y, for every room of every spec in the repo.

### S3 — Elevation projection (PHASE-04)

An elevation of side `s ∈ {north, south, east, west}` projects the model onto a vertical
plane. Define, per side, the horizontal axis `h` taken from the model and the depth
ordering used to decide what is in front:

| side | horizontal axis | plane | depth key (nearer first) |
|---|---|---|---|
| `north` | model x | y = 0 | ascending y |
| `south` | model x | y = plot_depth_mm | descending y |
| `west` | model y | x = 0 | ascending x |
| `east` | model y | x = plot_width_mm | descending x |

For every storey and every wall on that storey whose **outer face lies on the elevation
plane** (within 1 mm), emit a filled rectangle spanning `[h_start, h_end]` horizontally
and `[storey.base_z, storey.base_z + storey.height_mm]` vertically. For every opening on
such a wall, emit a rectangle at `[wall_h_start + offset_mm, + width_mm]` horizontally
and `[storey.base_z + sill_mm, storey.base_z + head_mm]` vertically. Add a horizontal
ground line at `z = 0` and a light storey-level line with its label at each
`storey.base_z`. Elevation drawings use **z increasing upward**, so the SVG writer maps
`svg_y = total_height_mm − z` and the DXF writer writes `z` directly.

### S4 — Section cut (PHASE-04)

A section on axis `a ∈ {x, y}` at position `p` millimetres cuts the model with the plane
`a = p`. For every storey:

- Every wall whose extent **contains** `p` on axis `a` is **cut**: draw it as a filled
  rectangle spanning its extent on the other horizontal axis and the storey height, with
  a heavy outline (cut poché).
- Every floor slab (each room rect containing `p` on axis `a`, minus that storey's
  `floor_voids`) is cut: draw a 200 mm-deep band at `z = storey.base_z`.
- Every stair tread on a storey whose stair room contains `p` is drawn in outline at its
  own `z`.
- Rooms whose rect contains `p` are labelled at the midpoint of their cut extent.

Everything else is omitted — no behind-the-cut projection in this plan (see ALT-002).

### S5 — Wall alignment (PHASE-05)

`site.wall_alignment` selects how an **exterior** wall sits relative to the room edge it
derives from. Partitions are always centred and are unaffected. Let `coord` be the edge
coordinate and `t` the wall thickness (200 mm exterior, 100 mm partition):

- `"centre"` (default, today's behaviour): the wall spans `[coord − t/2, coord + t/2]`.
- `"inside"`: the wall lies wholly on the room side of `coord`. For a vertical wall
  covered by exactly one room `r`: if `coord ≈ r.rect.x` (room lies east of the wall)
  the wall spans `[coord, coord + t]`; if `coord ≈ r.rect.x2` (room lies west) it spans
  `[coord − t, coord]`. Horizontal walls follow the same rule on y with `r.rect.y` /
  `r.rect.y2`.

Under `"inside"`, a room's **net interior** is its rect shrunk by the full thickness of
each exterior wall on its boundary and half the thickness of each partition. Under
`"centre"` it is the rect shrunk by half the thickness on every side. This net rect is
what furniture placement, interior lights and interior cameras must consume; the room
**schedule keeps reporting the gross rect area**, which is the standard convention and
keeps existing PDF numbers stable.

## Phase Summary

| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Renders depict the building they name | None | Corrected `fit_distance`; pure camera-placement functions; interior cameras inside rooms; tests that fail on today's artifacts |
| PHASE-02 | Affordable full-quality renders | PHASE-01 | Blender 4.5 LTS; EEVEE Next `final` profile; AgX; `--profile cycles`; benchmark record |
| PHASE-03 | Geometry stops reading as wrong | PHASE-02 | Parapets, stair balustrades, top-storey ceilings, window reveals/sills, neighbour massing |
| PHASE-04 | The full drawing set | PHASE-01 | `elevation.py`; 4 elevations + 2 sections in SVG/DXF; new PDF pages; CLI wiring |
| PHASE-05 | Honest plot geometry and a signal-carrying warning channel | PHASE-03, PHASE-04 | `site.wall_alignment`; `Room.interior`; `wall_outside_plot` promoted to error |
| PHASE-06 | Artifacts that know what they are, and a clean tree | PHASE-02, PHASE-05 | Model-hash provenance; glTF + web viewer; IFC deleted; console script; docs corrected |

## Detailed Phases

### PHASE-01 - Camera Truth

**Goal**
Make every render depict its named subject, and make the test suite capable of failing
when it does not. All logic lands in pure Python (`src/homedesign/camera_fit.py`) so it
is unit-testable without Blender; `build_scene.py` keeps only thin `bpy` wrappers.

**Tasks**
- [ ] TASK-01-01: In `src/homedesign/camera_fit.py`, change `fit_distance` lines 62-63
      from `+ _dot(v, forward)` to `- _dot(v, forward)` per S1. Update the docstring to
      state that the binding corner is the **nearest** one and that the depth term is
      subtracted because the camera sits at `centre − dist·forward`.
- [ ] TASK-01-02: Add `exterior_front_camera(model, res_x, res_y, lens_mm)` to
      `camera_fit.py`. It must fit `facade_bbox(model)` using **that box's own centre**
      (`(plot_w/2, 0.0, total_h/2)`) as both the fit centre and the camera anchor —
      never the plot centroid. Returns `(position, target, lens_mm)`.
- [ ] TASK-01-03: Add `exterior_aerial_camera(model, res_x, res_y, lens_mm)` to
      `camera_fit.py`, moving the existing 45°-descent placement out of
      `build_scene.py`. Derive the fit centre from `building_bbox(model)` rather than
      recomputing a centroid, so centre and box can never diverge again.
- [ ] TASK-01-04: Add `interior_camera(storey, room, res_x, res_y, ...)` to
      `camera_fit.py` implementing S2 exactly, including the focal-length solve and the
      clamps.
- [ ] TASK-01-05: Rewrite `_build_exterior_front_camera`, `_build_exterior_aerial_camera`
      and `_build_room_camera` in `src/homedesign/blender/build_scene.py` as thin
      wrappers: call the corresponding pure function, create the `bpy` camera, set
      `lens`, set `sensor_fit = "HORIZONTAL"`, set `location`, call `_point_at(cam,
      target)`, link and return. No arithmetic may remain in these three functions.
      Delete the now-unused `plot_w`, `plot_d`, `total_height`, `centroid` parameters
      from their signatures and update `add_cameras` accordingly.
- [ ] TASK-01-06: Add the off-centre regression test that the current suite lacks (see
      Test Specs) — it must fail with the old `+` sign and pass with the new `−` sign.
- [ ] TASK-01-07: Add `tests/test_camera_placement.py` asserting, for every room of every
      spec in `spec/examples/` and `designs/`, that `interior_camera` returns a position
      strictly inside the room rect, and that `exterior_front_camera` stands off the
      facade plane by at least the distance required to fit the facade height.
- [ ] TASK-01-08: Strengthen `tests/test_framing.py` per Test Specs: assert the non-sky
      bbox does not touch any frame edge, and build the render itself instead of
      skipping when it is absent.
- [ ] TASK-01-09: Rebuild and visually confirm:
      `python -m homedesign build spec/examples/tubehouse-mini.json`, then open
      `output/png/tubehouse-mini_exterior.png` and `_interior.png`.

**File Changes**
- `src/homedesign/camera_fit.py` (modify): fix the sign in `fit_distance`; add
  `exterior_front_camera`, `exterior_aerial_camera`, `interior_camera` and the module
  constants `EYE_HEIGHT_M = 1.5`, `WALL_INSET_M = 0.35`, `INTERIOR_LENS_MIN_MM = 12.0`,
  `INTERIOR_LENS_MAX_MM = 24.0`, `CEILING_CAP_M = 2.4`. Leave `basis_from_direction`,
  `corners_of`, `building_bbox`, `facade_bbox`, `room_subject_bbox`, `_unit`, `_cross`,
  `_dot`, `MARGIN`, `MIN_DISTANCE` and `SENSOR_WIDTH_MM` unchanged.
- `src/homedesign/blender/build_scene.py` (modify): replace the bodies of the three
  camera builders with wrappers; update `add_cameras` (lines 257-282) to the new
  signatures. Leave `build_walls`, `build_floors_and_stairs`, `build_environment`,
  `add_interior_lights`, `_point_at`, `_set_engine`, `_configure_cycles_device`,
  `render` and `main` untouched in this phase.
- `tests/test_camera_fit.py` (modify): add the off-centre test; leave the four existing
  tests unchanged so the symmetric-box behaviour is proven stable.
- `tests/test_camera_placement.py` (create): camera-containment and stand-off tests over
  every spec in the repo.
- `tests/test_framing.py` (modify): tighten the assertions and build the render on
  demand; keep the `blender_available` skip guard exactly as it is (CON-002).

**Function Signatures**
- `fit_distance(corners: Iterable[Vec3], centre: Vec3, forward: Vec3, right: Vec3, up: Vec3, lens_mm: float, res_x: int, res_y: int, margin: float = MARGIN) -> float` — camera distance from `centre` along `−forward` that keeps every corner inside the frustum, clamped to `MIN_DISTANCE`; signature unchanged, behaviour corrected per S1.
- `exterior_front_camera(model: dict, res_x: int, res_y: int, lens_mm: float = 35.0) -> tuple[Vec3, Vec3, float]` — `(position, target, lens_mm)` in metres for a camera south of the plot looking north at the street facade.
- `exterior_aerial_camera(model: dict, res_x: int, res_y: int, lens_mm: float = 35.0) -> tuple[Vec3, Vec3, float]` — `(position, target, lens_mm)` for the 45° south-east descent framing the whole building box.
- `interior_camera(storey: dict, room: dict, res_x: int, res_y: int, eye_height_m: float = EYE_HEIGHT_M, wall_inset_m: float = WALL_INSET_M, lens_min_mm: float = INTERIOR_LENS_MIN_MM, lens_max_mm: float = INTERIOR_LENS_MAX_MM) -> tuple[Vec3, Vec3, float]` — `(position, target, lens_mm)` for a camera standing **inside** the room per S2; position is guaranteed within the room rect.
- `_build_exterior_front_camera(name: str, model: dict) -> "bpy.types.Object"` — the linked Blender camera object for the front view.
- `_build_exterior_aerial_camera(name: str, model: dict) -> "bpy.types.Object"` — the linked Blender camera object for the aerial view.
- `_build_room_camera(name: str, storey: dict, room: dict) -> "bpy.types.Object"` — the linked Blender camera object for an interior view.

**Test Specs**
- `fit_distance(corners_of(((-1,-1,-1),(1,1,1))), (0,0,0), (0,1,0), (1,0,0), (0,0,1), lens_mm=50, res_x=1920, res_y=1080, margin=1.0)` → `5.93827160493827` (± 1e-3). Unchanged by the fix; proves the symmetric case did not regress.
- **New off-centre test** — `fit_distance(corners_of(((-1,-1,-1),(1,1,1))), centre=(0,-3,0), forward=(0,1,0), right=(1,0,0), up=(0,0,1), lens_mm=50, res_x=1920, res_y=1080, margin=1.0)`. Worked through: `tan_y = 36·1080/(2·50·1920) = 0.2025`, so `1/tan_y = 4.938271604938272`. The box spans y ∈ [−1, 1] while the centre sits at y = −3, so each corner's `depth = v·F` is either `2` (near face, y = −1) or `4` (far face, y = 1). The corrected formula `d_y = 1/tan_y − depth` binds on the **near** corner: `4.938271604938272 − 2`. Expected result **`2.938271604938272`** (± 1e-3). Under the old `+` sign the maximum instead binds on the far corner and the same call returns `8.938271604938272`, so this test fails before the fix and passes after it. Note the centre is chosen at y = −3 rather than further out so the result clears `MIN_DISTANCE = 1.0` and is not masked by the clamp.
- `exterior_front_camera(model_of("spec/examples/tubehouse-mini.json"), 1920, 1080)` → position `(2.0, y_cam, 4.6)` with `y_cam <= -15.90`, i.e. the camera stands at least 15.90 m from the facade plane at y = 0. Under the current code `y_cam == -4.693` and the assertion fails.
- `interior_camera(storey, room, 1920, 1080)` for the `living` room on **storey 0** of `spec/examples/tubehouse-mini.json` (a 4.0 × 5.0 m room spanning x ∈ [0, 4], y ∈ [0, 5], `base_z = 0`) → position with `0.0 < x < 4.0` and `0.0 < y < 5.0` (strictly inside the room), `z == 1.5`, and `12.0 <= lens_mm <= 24.0`. Under the current `_build_room_camera` the equivalent position is `(2.0, -5.26)` — outside the building.
- **Containment sweep:** for each of `spec/examples/tubehouse-mini.json`,
  `spec/examples/demo-3br-2storey.json`, `spec/examples/courtyard-fixture.json` and
  `designs/tubehouse-dream.json`, and for every room on every storey,
  `interior_camera(...)` position satisfies `rect.x < px < rect.x2` and
  `rect.y < py < rect.y2` (metres vs. the rect converted to metres). Currently 0 of 6
  rooms in `tubehouse-mini` pass.
- **Degenerate room:** a room of 700 × 700 mm (below the practical minimum but above the
  600 mm `room_too_small` threshold) → `interior_camera` still returns a position inside
  the rect and `lens_mm == 12.0` (clamped to the wide end), never raising.
- **Framing test, tightened:** for `output/png/tubehouse-mini_exterior.png` at 960 × 540,
  the non-sky bbox `(min_x, min_y, max_x, max_y)` must satisfy `min_x > 0.02 * 960`,
  `max_x < 0.98 * 960`, `min_y > 0.02 * 540` (sky visible above the roof), and
  `0.30 < (max_x - min_x)/960 < 0.95`. On today's render `min_y == 0`, so the test fails
  before the fix.

**Dependencies**
- None. Everything in this phase is pure Python plus three `bpy` wrapper rewrites;
  Blender is needed only for TASK-01-09's visual confirmation and the tightened
  `test_framing.py`, both of which skip cleanly without it.

**Exit Criteria**
- [ ] `python -m pytest tests -q` passes with at least 97 tests (90 existing + the new
      off-centre, containment-sweep, degenerate-room, stand-off and framing tests).
- [ ] The teeth check in TEST-004 has been run: with `- _dot(v, forward)` temporarily
      reverted to `+ _dot(v, forward)` in `src/homedesign/camera_fit.py`,
      `python -m pytest tests/test_camera_fit.py tests/test_camera_placement.py -q`
      **fails**; with the fix restored it passes. New tests that cannot fail on the old
      code do not satisfy this criterion.
- [ ] `python -m homedesign build spec/examples/tubehouse-mini.json` completes and
      `output/png/tubehouse-mini_exterior.png` shows the entire building with sky above
      and ground below it.
- [ ] `output/png/tubehouse-mini_interior.png` shows a room interior — walls, floor,
      ceiling and furniture — not an exterior wall.
- [ ] `ruff check src tests` prints `All checks passed!`.

**Phase Risks**
- **RISK-01-01:** A 12 mm lens in a 4 m-wide room produces noticeable barrel-style
  perspective stretch at the frame edges. Mitigation: the clamp floor of 12 mm is
  deliberate; if a specific room looks distorted, raise `lens_min_mm` for that render
  rather than reverting to pull-back framing, which cannot work indoors.
- **RISK-01-02:** The tightened framing test needs a render to exist and Blender to be
  present, so it is skipped in CI (CON-002). Mitigation: the containment sweep in
  `tests/test_camera_placement.py` is pure Python and runs everywhere — it is the real
  CI guard; the pixel test is a local backstop.

### PHASE-02 - Blender 4.5 LTS and EEVEE Next

**Goal**
Replace an 11.3-hour CPU-Cycles gallery with a full-quality EEVEE Next gallery measured
in minutes, and make the engine choice explicit rather than implicit.

**Tasks**
- [ ] TASK-02-01: Download and install Blender **4.5 LTS** alongside the existing 4.1.1
      (ASM-001). Verify with
      `"<path>/blender.exe" --version` → the first non-warning line reads `Blender 4.5`.
- [ ] TASK-02-02: Add the 4.5 install paths to `orchestrator._CANDIDATES`, ordered
      **before** the 4.1.1 entry so a bare invocation prefers the newer runtime. Keep
      `$BLENDER_CMD` and `PATH` lookup ahead of the candidate list exactly as they are.
- [ ] TASK-02-03: Replace the two module-level dicts `PREVIEW` and `FINAL` in
      `build_scene.py` with a single `RENDER_PROFILES` mapping with three entries:
      `preview` (`EEVEE`, 32 samples, 960 × 540), `final` (`EEVEE`, 256 samples,
      1920 × 1080, `raytracing: True`), `cycles` (`CYCLES`, 512 samples, 1920 × 1080).
      Update `render()` to read from it and to accept `"cycles"` as a profile.
- [ ] TASK-02-04: In `render()`, when the engine family is EEVEE and the profile
      requests raytracing, set `scene.eevee.use_raytracing = True` guarded by
      `hasattr(scene.eevee, "use_raytracing")` so 4.1.1 keeps working, and print
      `eevee raytracing: on|unavailable` so the runtime capability is never silently
      assumed. Mirror the existing `cycles device: ...` reporting style.
- [ ] TASK-02-05: Change the view-transform selection to try `"AgX"`, then `"Filmic"`,
      then `"Standard"`, replacing the current two-step try/except at
      `build_scene.py:365-368`. Print the transform that was accepted.
- [ ] TASK-02-06: Add `"cycles"` to the `--profile` choices of the `render` subcommand
      in `src/homedesign/__main__.py:207` and to `build`'s behaviour: keep `--final`
      meaning the `final` profile, and add `--profile` to `build` with the same three
      choices, defaulting to `preview`.
- [ ] TASK-02-07: Benchmark. With `BLENDER_CMD` pointed at 4.5, run
      `python -m homedesign render designs/tubehouse-dream.json --profile final` and
      record wall-clock time per view; repeat one exterior and one interior view with
      `--profile cycles`. Write both numbers, and a one-paragraph quality comparison,
      into `docs/lessons-learned.md` under a new dated lesson.
- [ ] TASK-02-08: Update `.claude/skills/homedesign/SKILL.md` to describe the three
      profiles and the new expected timings, then run `python scripts/sync_skill.py`.

**File Changes**
- `src/homedesign/blender/build_scene.py` (modify): replace `PREVIEW`/`FINAL` (lines
  28-29) with `RENDER_PROFILES`; extend `render()` (lines 346-388) for the third profile,
  raytracing and AgX; extend `parse_args()` `--profile` choices to include `cycles`.
  Leave `_set_engine` and `_configure_cycles_device` logic unchanged — both are already
  version-tolerant and correct.
- `src/homedesign/orchestrator.py` (modify): add Blender 4.5 paths at the head of
  `_CANDIDATES` (line 17-29); widen the `profile` parameter documentation of
  `build_scene()` and `render_only()` to the three values. Leave the detached-launch and
  streaming logic untouched.
- `src/homedesign/__main__.py` (modify): add `cycles` to `--profile` choices on `render`;
  add `--profile` to `build`. Keep `--final` working as an alias for `--profile final`
  so existing documented commands do not break (DEC-003).
- `docs/lessons-learned.md` (modify): append a dated lesson recording the benchmark.
- `.claude/skills/homedesign/SKILL.md` (modify): document the three profiles; correct the
  "Known limitations" bullet that still claims previews are low-sample Cycles.
- `.agents/skills/homedesign/SKILL.md` (modify): regenerated by `scripts/sync_skill.py`
  — never edit by hand.

**Function Signatures**
- `render(model_name: str, cams: list, out_dir: str | Path, profile: str, views: list[str] | None = None, skip_existing: bool = False) -> list[Path]` — the PNG paths written; `profile` now accepts `"preview" | "final" | "cycles"`.
- `build_scene(model_path: Path, out_dir: Path, final: bool = False, profile: str | None = None, views: list[str] | None = None, skip_existing: bool = False, reuse_blend: bool = False) -> list[Path]` — `[blend_path, *png_paths]`; `profile` overrides `final` when given.

**Test Specs**
- `RENDER_PROFILES["final"]` → `{"engine": "EEVEE", "samples": 256, "res": (1920, 1080), "raytracing": True}` and `RENDER_PROFILES["cycles"]["engine"]` → `"CYCLES"`.
- `python -m homedesign render spec/examples/tubehouse-mini.json --profile cycles --view exterior` → exits 0 and prints a line beginning `cycles device:`.
- `python -m homedesign render spec/examples/tubehouse-mini.json --profile final --view exterior` → exits 0 and prints `eevee raytracing: on` when run against Blender 4.5, `eevee raytracing: unavailable` against 4.1.1.
- Argument-parsing test in `tests/test_orchestrator.py` using the existing `stub_blender` fixture: `orchestrator.build_scene(model, out, profile="cycles")` → the assembled argv contains `--profile cycles`.
- Backwards compatibility: `python -m homedesign build spec/examples/tubehouse-mini.json --final` still selects the `final` profile and exits 0.

**Dependencies**
- Blender 4.5 LTS installed locally (TASK-02-01). All code changes remain valid against
  4.1.1 thanks to the `hasattr` guards, so the phase is not blocked if installation is
  delayed — only the benchmark is.

**Exit Criteria**
- [ ] `"<blender-4.5-path>/blender.exe" --version` reports `Blender 4.5`.
- [ ] A full `--profile final` gallery of `designs/tubehouse-dream.json` completes in
      **under 30 minutes** wall clock (against 11.3 hours previously). If it does not,
      record the actual figure and proceed per ASM-002.
- [ ] `python -m pytest tests -q` passes.
- [ ] `python scripts/sync_skill.py --check` prints `ok: skill copies match`.
- [ ] `docs/lessons-learned.md` contains the dated benchmark lesson with both engines'
      per-view timings.

**Phase Risks**
- **RISK-02-01:** Blender 4.5 changes Python API names used by `build_scene.py` (for
  example `scene.eevee` attribute names). Mitigation: 4.1.1 stays installed (ASM-001);
  run the full `build` against both runtimes by switching `BLENDER_CMD` and fix any
  `AttributeError` with `hasattr` guards in the same style as `_set_engine`.
- **RISK-02-02:** EEVEE Next renders glass and window openings differently from Cycles,
  so interiors may need light-energy retuning. Mitigation: retune only
  `add_interior_lights` energies; do not reintroduce the removed high-energy fill light,
  which is what blew out interiors previously.

### PHASE-03 - Geometric Realism

**Goal**
Add the physical elements whose absence makes a correct model read as wrong: edge
protection, ceilings, window detail and urban context.

**Tasks**
- [ ] TASK-03-01: Create `src/homedesign/blender/railings.py` with `build_parapet` and
      `build_balustrade`, both pure `make_box` compositions (CON-004).
- [ ] TASK-03-02: In `build_scene.build_floors_and_stairs`, for every room of type
      `balcony`, build a 1100 mm-high, 100 mm-thick parapet along each edge of the room
      rect that is **not** shared with another room on the same storey. Reuse the
      existing `_wall_touches_room`-style adjacency logic rather than inventing a new
      one: an edge is open when no other room on that storey has a rect edge coincident
      with it within 1 mm.
- [ ] TASK-03-03: In `build_scene.build_floors_and_stairs`, for each storey with stairs,
      build a 900 mm-high balustrade along the open long side of each flight, derived
      from the tread rectangles already present in `storey["stairs"]["treads"]`. The
      open side is the one not coincident with the stairwell room's rect edge.
- [ ] TASK-03-04: Add a ceiling slab for every room on the **topmost** storey that is
      not covered by that storey's `roof` rect, at `z = base_z + height_mm/1000`,
      thickness `FLOOR_SLAB_THICKNESS`, subtracting the storey's `floor_voids` exactly as
      the floor path already does via `rects.subtract_rects`. Skip rooms of type
      `balcony`.
- [ ] TASK-03-05: In `src/homedesign/blender/joinery.py`, add a head lintel and a sill
      board to every opening: a `FRAME_WIDTH`-deep box across the opening head, and for
      windows a 25 mm-thick sill projecting 30 mm past the wall face on the exterior
      side. Leave the existing jamb and glass/leaf construction alone.
- [ ] TASK-03-06: Add an optional `site.context` object to `spec/homespec.schema.json`:
      `{"neighbours": boolean, "street_depth_mm": number}` with
      `additionalProperties: false`. Defaults per ASM-005.
- [ ] TASK-03-07: In `build_scene.build_environment`, when neighbour massing is enabled,
      build two grey blocks flanking the plot — each `plot_depth_mm` deep,
      3000 mm wide, and as tall as the building — placed immediately west and east of
      the plot, plus a 6000 mm-deep street strip south of the plot (`y < 0`) using the
      `ground` material darkened. Add a `neighbour` and a `street` entry to
      `materials.PALETTES["modern-minimal"]`.
- [ ] TASK-03-08: Rebuild `designs/tubehouse-dream.json` and confirm the roof terrace has
      a parapet in the aerial render.

**File Changes**
- `src/homedesign/blender/railings.py` (create): `build_parapet`, `build_balustrade`, and
  a private `_open_edges(room_rect, sibling_rects)` helper.
- `src/homedesign/rects.py` (modify): add `open_edges(rect, others, eps=1.0)` returning
  which of `("north","south","east","west")` are not shared with any rect in `others`, so
  the adjacency logic is pure and unit-testable. Leave `subtract_rect` and
  `subtract_rects` unchanged.
- `src/homedesign/blender/build_scene.py` (modify): call the parapet, balustrade and
  ceiling builders from `build_floors_and_stairs`; extend `build_environment` with
  neighbour and street massing. Leave the wall/opening boolean path untouched.
- `src/homedesign/blender/joinery.py` (modify): add lintel and sill boxes.
- `src/homedesign/blender/materials.py` (modify): add `neighbour` and `street` palette
  entries.
- `spec/homespec.schema.json` (modify): add `site.context`; keep
  `"additionalProperties": false` on `site` and add the new key to its `properties`.
- `tests/test_rects.py` (modify): add `open_edges` cases.

**Function Signatures**
- `open_edges(rect: Rect, others: list[Rect], eps: float = 1.0) -> set[str]` — the subset of `{"north","south","east","west"}` whose edge of `rect` is not coincident with an edge of any rect in `others`.
- `build_parapet(rect_mm: tuple[float, float, float, float], top_z_m: float, sides: set[str], height_m: float, thickness_m: float, collection, material) -> list` — the created parapet box objects.
- `build_balustrade(treads: list[dict], open_side: str, height_m: float, collection, material) -> list` — the created balustrade box objects, one rake per flight.

**Test Specs**
- `open_edges(Rect(x=0, y=0, w=4000, d=3000), [Rect(x=0, y=3000, w=4000, d=2000)])` → `{"north", "east", "west"}` (the south edge is shared).
- `open_edges(Rect(x=0, y=0, w=4000, d=3000), [])` → `{"north", "south", "east", "west"}`.
- `open_edges(Rect(x=0, y=0, w=4000, d=3000), [Rect(x=0, y=3001, w=4000, d=2000)])` → all four edges open (a 1 mm gap is outside the `eps` tolerance for coincidence).
- Schema acceptance: a spec with `"site": {"plot_width_mm": 4000, "plot_depth_mm": 25000, "context": {"neighbours": true, "street_depth_mm": 6000}}` → `validate_schema` returns `[]`.
- Schema rejection: `"site": {..., "context": {"neighbors": true}}` (US spelling) →
  `validate_schema` returns exactly one `SpecError` with `code == "schema_error"`.
- Backwards compatibility: all four existing specs still return `[]` from
  `validate_schema` with no `site.context` key present.

**Dependencies**
- PHASE-02 (the realism work is only worth rendering once a full gallery is affordable).

**Exit Criteria**
- [ ] `python -m pytest tests -q` passes.
- [ ] `python -m homedesign build designs/tubehouse-dream.json` succeeds and the aerial
      render shows a parapet around `terrace_f4`.
- [ ] No storey-4 room other than `terrace_f4` is open to the sky in the render.
- [ ] All four existing specs compile with no new error-severity output.

**Phase Risks**
- **RISK-03-01:** Parapets on balconies that abut the plot edge may extend past it and
  trip `wall_outside_plot`. Mitigation: parapets are placed **inside** the room rect
  (their outer face on the rect edge), which keeps them within the plot regardless of the
  wall-alignment setting resolved in PHASE-05.
- **RISK-03-02:** Neighbour massing blocks the exterior_front camera's view or casts the
  facade into shadow. Mitigation: neighbours flank west and east only, never south (the
  street side the front camera shoots from); verify the front render after TASK-03-07.

### PHASE-04 - Elevations and Sections

**Goal**
Produce the two drawing types the pipeline is missing, in both SVG and DXF, and add them
to the architect brief.

**Tasks**
- [ ] TASK-04-01: Create `src/homedesign/elevation.py` implementing S3 and S4 as pure
      functions over `CompiledModel`, producing a neutral draw model (a list of typed
      primitives) so SVG and DXF are two renderers over one source — never two
      independent implementations.
- [ ] TASK-04-02: Implement `build_elevation(model, side)` per S3, returning the draw
      model: wall rectangles, opening rectangles, storey level lines with labels, ground
      line, and the overall building outline.
- [ ] TASK-04-03: Implement `build_section(model, axis, position_mm)` per S4, returning
      cut wall poché, cut floor bands, stair outlines and room labels.
- [ ] TASK-04-04: Implement `write_elevations(model, out_dir)` and
      `write_sections(model, out_dir)` writing
      `output/svg/<name>_elev_<side>.svg`, `output/dxf/<name>_elev_<side>.dxf`,
      `output/svg/<name>_section_<axis>.svg`, `output/dxf/<name>_section_<axis>.dxf`.
      Reuse `plan2d`'s title block, north arrow and scale bar by extracting them into
      shared helpers rather than copying them.
- [ ] TASK-04-05: Extend `plan2d.write_plans` to also call `write_elevations` and
      `write_sections`, so `python -m homedesign plans <spec>` emits the complete set.
      Return every written path, preserving the existing return type (`list[Path]`).
- [ ] TASK-04-06: Add elevation and section pages to `src/homedesign/pdf.py`, inserted
      **after** the per-storey plan pages and before the render gallery: one page per
      elevation (4) and one per section (2), each an inline SVG using the existing
      `.plan-page` CSS class so the one-page-per-sheet cap applies unchanged.
- [ ] TASK-04-07: Add DXF layers `ELEV`, `SECTION` and `LEVELS` to the layer list created
      in `_render_dxf`-style setup for the new drawings, following the existing colour
      convention (`WALLS 7, DOORS 1, WINDOWS 5, STAIRS 3, TEXT 2, DIMS 8`).
- [ ] TASK-04-08: Update `.claude/skills/homedesign/SKILL.md` to list the new outputs,
      then run `python scripts/sync_skill.py`.

**File Changes**
- `src/homedesign/elevation.py` (create): `build_elevation`, `build_section`,
  `write_elevations`, `write_sections`, plus the draw-model primitives.
- `src/homedesign/plan2d.py` (modify): extract `_north_arrow`, `_scale_bar` and
  `_title_block` into module-level helpers that accept an explicit drawing title so
  `elevation.py` can reuse them; extend `write_plans` to call the new writers. Leave
  `_render_svg`, `_svg_opening`, `_dxf_pt` and `_render_dxf` behaviour unchanged for the
  plan drawings.
- `src/homedesign/pdf.py` (modify): add `_elevation_pages(model, svg_dir)` and
  `_section_pages(model, svg_dir)` and insert their output into the `body` list in
  `render_brief_html` between `_plan_pages(...)` and `_gallery_pages(...)`.
- `tests/test_elevation.py` (create): unit tests for the draw model and the writers.
- `tests/test_pdf.py` (modify): assert the new pages appear in the generated HTML.
- `.claude/skills/homedesign/SKILL.md` (modify) and `.agents/skills/homedesign/SKILL.md`
  (regenerated).

**Function Signatures**
- `build_elevation(model: CompiledModel, side: str) -> list[dict]` — draw-model primitives for one elevation; each item is `{"kind": "wall"|"opening"|"level"|"ground"|"outline", "x": float, "z": float, "w": float, "h": float, "label": str | None}` with x in millimetres along the elevation's horizontal axis and z in millimetres above ground.
- `build_section(model: CompiledModel, axis: str, position_mm: float) -> list[dict]` — draw-model primitives for one section, same item shape, with `"kind"` extended by `"cut_wall"`, `"cut_slab"`, `"tread"` and `"room_label"`.
- `write_elevations(model: CompiledModel, out_dir: Path, sides: tuple[str, ...] = ("north", "south", "east", "west")) -> list[Path]` — the SVG and DXF paths written, in that order per side.
- `write_sections(model: CompiledModel, out_dir: Path) -> list[Path]` — the SVG and DXF paths written for the long (`x`) and cross (`y`) sections per ASM-004.

**Test Specs**
- `build_elevation(model_of("spec/examples/tubehouse-mini.json"), "north")` → contains at least one `{"kind": "wall"}` item per storey, and the maximum `z + h` across all items equals the model's total storey height in millimetres (`9200.0` for tubehouse-mini: 3 storeys — verify against the compiled model rather than hardcoding if the fixture changes).
- `build_elevation(model, "north")` → every `{"kind": "opening"}` item has `sill_mm <= z` and `z + h <= head_mm + storey base`, i.e. no opening escapes its wall vertically.
- `build_elevation(model, "east")` items all satisfy `0 <= x <= plot_depth_mm` (the east elevation's horizontal axis is model **y**, not x — the classic axis-swap trap).
- `build_section(model_of("spec/examples/demo-3br-2storey.json"), "x", 5000.0)` → contains a `{"kind": "cut_slab"}` item for every storey, and every `{"kind": "cut_wall"}` item comes from a wall whose x extent contains 5000.0.
- `build_section(model, "x", -1.0)` (a cut plane outside the plot) → returns a list containing only `{"kind": "ground"}`; never raises.
- `write_elevations(model, tmp_path)` → writes exactly 8 files (4 SVG + 4 DXF); every SVG parses as XML and every DXF opens with `ezdxf.readfile`.
- `render_brief_html(...)` for `tubehouse-mini` → the returned HTML contains the substrings `North Elevation`, `South Elevation`, `East Elevation`, `West Elevation`, `Long Section` and `Cross Section`.
- Page-count check: the `tubehouse-dream` brief grows from 17 pages to 23 (4 elevations + 2 sections).

**Dependencies**
- PHASE-01 only (this phase touches no camera or render code and can run in parallel with
  PHASE-02/03 if desired).

**Exit Criteria**
- [ ] `python -m homedesign plans designs/tubehouse-dream.json` writes 5 plan SVG/DXF
      pairs, 4 elevation pairs and 2 section pairs — 22 files total.
- [ ] `python -m pytest tests -q` passes.
- [ ] `python -m homedesign pdf designs/tubehouse-dream.json` produces a 23-page PDF that
      opens without error.
- [ ] Every generated DXF opens with `python -c "import ezdxf,glob;[ezdxf.readfile(f) for f in glob.glob('output/dxf/tubehouse-dream_*.dxf')]"` without raising.

**Phase Risks**
- **RISK-04-01:** The east/west elevations use model **y** as their horizontal axis; a
  copy-paste from the north/south path silently produces a drawing of the wrong
  dimension. Mitigation: the axis-bound test spec above exists precisely to catch it, and
  the per-side table in S3 is the single source of truth.
- **RISK-04-02:** Elevation z grows upward while SVG y grows downward — the same class of
  bug that once mirrored the plan DXF against the plan SVG. Mitigation: exactly one
  helper performs the `svg_y = total_height_mm − z` flip, mirroring how `plan2d._dxf_pt`
  is the single flip point for plans.

### PHASE-05 - Wall Alignment and Honest Validation

**Goal**
Let a spec declare that exterior walls must sit inside the plot line, give every room a
net interior rect that furniture, lights and cameras consume, and turn
`wall_outside_plot` from unfalsifiable noise into a real error.

**Tasks**
- [ ] TASK-05-01: Add `site.wall_alignment` to `spec/homespec.schema.json`:
      `{"type": "string", "enum": ["centre", "inside"], "default": "centre"}`.
- [ ] TASK-05-02: Implement S5 in `compiler._derive_walls`. Pass the alignment through
      from `compile_spec`. Partitions keep the centred branch untouched; only the
      `kind == "exterior"` branch gains the inset placement, which needs the covering
      room's rect to decide which side is interior.
- [ ] TASK-05-03: Add `interior: Rect` to the `Room` dataclass in `model.py`, populated
      by the compiler per S5, defaulting to a copy of `rect` when it cannot be derived.
      Extend `CompiledModel.from_dict` to round-trip it.
- [ ] TASK-05-04: Consume `room.interior` in `blender/furnish.py` (furniture origin and
      size), `build_scene.add_interior_lights` (light position) and
      `camera_fit.interior_camera` (camera containment). Where `interior` is absent from
      an older compiled-model JSON, fall back to `rect` so stale files still load.
- [ ] TASK-05-05: Rewrite `checks.check_walls_within_plot`: the tolerance becomes
      `thickness / 2` under `"centre"` alignment and `1.0` mm under `"inside"`, and the
      severity becomes the default (error), not `"warning"`. `CompiledModel` must
      therefore carry the alignment — add `wall_alignment: str = "centre"` to it.
- [ ] TASK-05-06: Add `wall_alignment: "inside"` to `designs/tubehouse-dream.json` and
      re-verify it compiles with zero errors and zero warnings.
- [ ] TASK-05-07: Add a `built_envelope_mm` row to the quantity take-off in
      `pdf.build_takeoff` reporting the actual outer dimensions of the building
      (`max wall x2 − min wall x`, same for y), so the gross-vs-plot fact is disclosed on
      the drawing set regardless of alignment mode.

**File Changes**
- `spec/homespec.schema.json` (modify): add `site.wall_alignment`.
- `src/homedesign/compiler.py` (modify): thread `wall_alignment` from
  `spec["site"]` into `_derive_walls`; implement the inset branch; compute
  `Room.interior`. Leave the sweep-line breakpoint/merge logic itself unchanged — only
  the final rectangle placement per merged piece changes.
- `src/homedesign/model.py` (modify): add `Room.interior: Optional[Rect] = None` and
  `CompiledModel.wall_alignment: str = "centre"`; extend `from_dict` for both.
- `src/homedesign/checks.py` (modify): rewrite `check_walls_within_plot` per TASK-05-05.
- `src/homedesign/blender/furnish.py` (modify): use `room["interior"]` when present.
- `src/homedesign/blender/build_scene.py` (modify): `add_interior_lights` uses the
  interior rect centre.
- `src/homedesign/camera_fit.py` (modify): `interior_camera` prefers `room["interior"]`.
- `src/homedesign/pdf.py` (modify): add the built-envelope row to `build_takeoff`.
- `designs/tubehouse-dream.json` (modify): set `site.wall_alignment` to `"inside"`.
- `tests/test_compiler.py`, `tests/test_checks.py` (modify): add alignment cases.

**Function Signatures**
- `_derive_walls(rooms: list[Room], plot_w: float, plot_d: float, level: int, wall_alignment: str = "centre") -> list[Wall]` — the derived wall segments; exterior walls are inset per S5 when `wall_alignment == "inside"`.
- `check_walls_within_plot(model: CompiledModel) -> list[SpecError]` — error-severity `SpecError`s for walls exceeding the plot beyond the alignment-appropriate tolerance; empty list when compliant.
- `Room(id: str, type: str, rect: Rect, name: Optional[str] = None, interior: Optional[Rect] = None)` — a compiled room; `interior` is the net usable rect after wall thickness.

**Test Specs**
- Single room `rect = {x: 0, y: 0, w: 4000, d: 5000}` on a 4000 × 5000 plot, `wall_alignment = "centre"` → the west exterior wall spans `x ∈ [-100, 100]`. With `wall_alignment = "inside"` → it spans `x ∈ [0, 200]`.
- Same room, `"inside"` → `check_walls_within_plot(model)` returns `[]`. With `"centre"` → also `[]` (the 100 mm overhang is within the `thickness/2` tolerance).
- A room deliberately placed at `x = -300` on a `"centre"` plot → `check_walls_within_plot` returns at least one `SpecError` whose `severity` is **not** `"warning"`.
- `compile_spec` on all four existing specs with no `wall_alignment` key → produces byte-identical wall geometry to the pre-change compiler (capture `json.dumps(model.to_dict()["storeys"][0]["walls"], sort_keys=True)` before and after; they must match exactly). This is the backwards-compatibility guarantee of DEC-003.
- `designs/tubehouse-dream.json` with `"inside"` → `python -m homedesign compile designs/tubehouse-dream.json` exits 0 and prints **zero** lines to stderr (down from 63 warning lines).
- `Room` interior under `"inside"`: a 4000 × 5000 room bounded by exterior walls on all four sides → `interior == Rect(x=200, y=200, w=3600, d=4600)`.
- Partition-bounded room under `"centre"`: a room with a partition on its east edge → `interior` is inset by 50 mm (half of `INT_THICKNESS`) on that edge only.

**Dependencies**
- PHASE-03 (parapets must already sit inside room rects so they are unaffected by the
  inset) and PHASE-04 (elevations read wall outer faces, so they must exist before the
  outer faces move, to make the change visually verifiable).

**Exit Criteria**
- [ ] `python -m homedesign compile designs/tubehouse-dream.json 2>&1 >/dev/null | wc -l`
      prints `0` (was `63`).
- [ ] `python -m homedesign compile spec/examples/tubehouse-mini.json` produces geometry
      identical to before the change (the byte-identity test above passes).
- [ ] `python -m pytest tests -q` passes.
- [ ] The `tubehouse-dream` north elevation shows a building 4000 mm wide, not 4200 mm.
- [ ] Furniture in the rebuilt `tubehouse-dream` renders does not intersect any wall.

**Phase Risks**
- **RISK-05-01:** Under `"inside"`, walls move into the room footprint, so furniture
  placed from the gross rect would clip into them. Mitigation: TASK-05-04 is not
  optional — furniture, lights and cameras must all switch to `room.interior` in the same
  change, and the "furniture does not intersect any wall" exit criterion verifies it.
- **RISK-05-02:** Promoting `wall_outside_plot` to error severity could block a build
  that previously succeeded with warnings. Mitigation: the tolerance is alignment-aware
  precisely so no currently-valid spec becomes invalid; the byte-identity test proves it.

### PHASE-06 - Provenance, Web Viewer, and Hygiene

**Goal**
Make every artifact declare which compiled model produced it, add an interactive
deliverable that does not depend on render time at all, and remove the accumulated dead
weight and documentation drift.

**Tasks**
- [ ] TASK-06-01: Add `model_hash(model: CompiledModel) -> str` to
      `src/homedesign/model.py` implementing ASM-007.
- [ ] TASK-06-02: Write a sidecar `output/png/<name>_<view>.png.json` next to every render
      containing `{"model_hash": ..., "view": ..., "profile": ..., "rendered_at": ...}`
      (ISO-8601 UTC timestamp). Write the same hash into
      `output/compiled/<name>.model.json` as a top-level `"model_hash"` key and into
      `output/blend/<name>.blend.json`.
- [ ] TASK-06-03: In `pdf.render_brief_html`, compare each gallery image's sidecar hash
      against the current model hash. On mismatch, print a `warning: stale render` line to
      stderr naming the view, and stamp `STALE` in the image caption on the page. On a
      missing sidecar, treat it as stale.
- [ ] TASK-06-04: Add `--require-fresh` to the `pdf` subcommand: when passed, a stale or
      missing-sidecar image is a hard error (exit 1) instead of a warning.
- [ ] TASK-06-05: Export glTF from the same headless Blender run: add
      `--export-gltf` to `build_scene.py` and call
      `bpy.ops.export_scene.gltf(filepath=str(out_dir/"gltf"/f"{name}.glb"), export_format="GLB")`
      after the `.blend` is saved. Wire a `--gltf` flag through `orchestrator.build_scene`
      and the `build` subcommand.
- [ ] TASK-06-06: Add `src/homedesign/viewer.py` writing a single self-contained HTML
      file at `output/viewer/<name>.html` that loads the GLB. Inline the viewer script
      and embed the GLB as a base64 data URI so the file works offline with no external
      requests.
- [ ] TASK-06-07: Delete `src/ifc_export_utils.py` (DEC-002). Remove the IFC caveat from
      `.claude/skills/homedesign/SKILL.md` "Known limitations" and regenerate the mirror.
- [ ] TASK-06-08: Add `[project.scripts]` to `pyproject.toml`:
      `homedesign = "homedesign.__main__:main"`.
- [ ] TASK-06-09: Documentation accuracy pass:
      - `AGENTS.md`: "Start Here" currently recommends
        `plans/home-design-to-architect-workflow.md`, whose own frontmatter reads
        `status: superseded` and which describes the deleted FreeCAD pipeline (`run.sh`,
        `opencode.json`, `freecad-mcp-guide.md`, `spec/floorplan-spec.json` — none of
        which exist). Move that file to `docs/archive/` and point "Start Here" at
        `.claude/skills/homedesign/SKILL.md`.
      - `AGENTS.md`, `designs/README.md`, `.claude/skills/homedesign/SKILL.md`: drop the
        `PYTHONPATH=src` prefix from every command now that the console script exists.
      - `.claude/skills/homedesign/SKILL.md` "Known limitations": the bullet claiming
        "Preview renders are low-sample Cycles for speed" contradicts the same file's
        step 2 and has been wrong since the EEVEE preview landed — correct it.
- [ ] TASK-06-10: Remove the small dead code: the tautology at `compiler.py:368`
      (`2100.0 if o["type"] == "door" else 2100.0` — collapse to a single constant with a
      comment explaining that doors and windows deliberately share a 2100 mm head line);
      the user-specific first entry of `orchestrator._CANDIDATES`; and the `"master"`
      entry in `build_scene._find_default_interior_room`'s priority list, which is not a
      member of the room-type enum and can only ever match by room id.
- [ ] TASK-06-11: Create `deliverables/README.md` documenting that `output/` is
      git-ignored and disposable while a full render gallery costs an overnight run, and
      that finals worth keeping are copied to `deliverables/<slug>/` and committed.

**File Changes**
- `src/homedesign/model.py` (modify): add `model_hash`.
- `src/homedesign/blender/build_scene.py` (modify): write render sidecars; add
  `--export-gltf` and the glTF export call in `main()`.
- `src/homedesign/orchestrator.py` (modify): thread a `gltf: bool` argument through
  `_build_command` and `build_scene`; remove the hardcoded user path from `_CANDIDATES`.
- `src/homedesign/pdf.py` (modify): staleness comparison, caption stamp, `require_fresh`
  parameter on `build_brief`.
- `src/homedesign/__main__.py` (modify): `--require-fresh` on `pdf`, `--gltf` on `build`.
- `src/homedesign/viewer.py` (create): the self-contained viewer writer.
- `src/homedesign/compiler.py` (modify): collapse the `default_head` tautology.
- `src/ifc_export_utils.py` (delete).
- `pyproject.toml` (modify): add `[project.scripts]`.
- `AGENTS.md`, `designs/README.md`, `.claude/skills/homedesign/SKILL.md` (modify);
  `.agents/skills/homedesign/SKILL.md` (regenerated).
- `plans/home-design-to-architect-workflow.md` → `docs/archive/home-design-to-architect-workflow.md` (move).
- `deliverables/README.md` (create).
- `tests/test_provenance.py` (create), `tests/test_pdf.py` (modify).

**Function Signatures**
- `model_hash(model: CompiledModel) -> str` — the first 12 hex characters of the SHA-256 digest of the model's canonical JSON serialisation (ASM-007).
- `write_render_sidecar(png_path: Path, model_hash: str, view: str, profile: str) -> Path` — the sidecar JSON path written next to the PNG.
- `read_render_sidecar(png_path: Path) -> dict | None` — the parsed sidecar, or `None` when absent or unparseable.
- `write_viewer(model_name: str, glb_path: Path, out_dir: Path) -> Path` — the self-contained HTML viewer path written.
- `build_brief(model: CompiledModel, brief: dict, out_dir: Path, spec_path: Path, hero_view: str | None = None, embed_images: bool = False, require_fresh: bool = False) -> Path` — the written PDF path; raises `RuntimeError` when `require_fresh` is set and any gallery image is stale.

**Test Specs**
- `model_hash(model)` → a 12-character lowercase hex string; calling it twice on the same model returns the same value; changing `model.storeys[0].height_mm` by 1.0 changes it.
- `model_hash` is insensitive to dict ordering: two `CompiledModel`s built from the same data with different room insertion orders in the source spec produce different hashes only if the compiled order differs — assert that recompiling the same spec file twice yields identical hashes.
- `read_render_sidecar(Path("missing.png"))` → `None`, no exception.
- `build_brief(..., require_fresh=True)` with one gallery PNG whose sidecar hash differs from the model → raises `RuntimeError` naming the offending view.
- `build_brief(..., require_fresh=False)` with the same setup → returns the PDF path and the generated HTML contains the substring `STALE`.
- `python -m homedesign pdf designs/tubehouse-dream.json --require-fresh` against today's Jul-6 renders → exits 1. After a fresh `--profile final` gallery → exits 0.
- Console script: `homedesign --help` (with no `python -m` prefix and no `PYTHONPATH`) → prints the usage line `usage: homedesign [-h] {compile,plans,build,render,pdf} ...`.
- `python -c "import homedesign, glob; assert not glob.glob('src/ifc_export_utils.py')"` → exits 0 after the deletion.

**Dependencies**
- PHASE-02 (glTF export runs in the same Blender invocation) and PHASE-05 (the model
  hash must be stable, so the wall-alignment change must already be in).

**Exit Criteria**
- [ ] `python -m pytest tests -q` passes.
- [ ] `ruff check src tests` prints `All checks passed!`.
- [ ] `python scripts/sync_skill.py --check` prints `ok: skill copies match`.
- [ ] `homedesign --help` works without `python -m` and without `PYTHONPATH`.
- [ ] `python -m homedesign build designs/tubehouse-dream.json --gltf` writes
      `output/gltf/tubehouse-dream.glb` and `output/viewer/tubehouse-dream.html`; opening
      the HTML in a browser shows an orbitable model with no network requests.
- [ ] `python -m homedesign pdf designs/tubehouse-dream.json --require-fresh` exits 0
      against a gallery rendered from the current model.
- [ ] `grep -rn "PYTHONPATH=src" AGENTS.md designs/README.md .claude/skills/homedesign/SKILL.md`
      returns no matches.
- [ ] `grep -rn "home-design-to-architect-workflow" AGENTS.md` returns no matches.

**Phase Risks**
- **RISK-06-01:** Embedding a GLB as a base64 data URI can produce a very large HTML file
  for a five-storey model. Mitigation: if `output/gltf/<name>.glb` exceeds 8 MB, write
  the GLB as a sibling file and reference it relatively instead of inlining, and say so
  in `deliverables/README.md`. The viewer must still work from the local filesystem.
- **RISK-06-02:** Deleting `src/ifc_export_utils.py` loses work if anyone still wants IFC.
  Mitigation: it is fully recoverable with
  `git show HEAD:src/ifc_export_utils.py > src/ifc_export_utils.py`; note that command in
  the commit message.

## Gotchas

- **The sign fix is invisible to symmetric boxes.** Every existing `fit_distance` test
  fits a box centred on the passed `centre`, where `+depth` and `−depth` select different
  binding corners but return the identical maximum. Do not conclude the fix is a no-op
  because the old tests still pass — that is expected, and it is exactly why TASK-01-06
  requires a deliberately off-centre case.
- **The sign fix makes interior cameras worse, not better.** The room bbox is centred on
  the passed centre, so the sign cancels there; the corrected formula returns a slightly
  larger distance and pushes the camera further outside the room. PHASE-01 must land the
  sign fix and the interior-camera rewrite together — shipping only the first regresses
  interiors.
- **Millimetres versus metres.** The compiler, checks, plan2d, pdf and elevation modules
  all work in millimetres. Everything under `src/homedesign/blender/` works in metres.
  `camera_fit` is the exception that proves the rule: it consumes the compiled model dict
  and converts to metres internally (`/ 1000`), because its consumers are Blender-side.
  Any new function there must follow that convention.
- **Absolute imports only under `src/homedesign/blender/`.** Those files execute as
  top-level Blender scripts, so `from ..camera_fit import ...` fails at runtime even
  though it looks correct to a linter. Use `from homedesign.camera_fit import ...` —
  see the existing `# noqa: E402` imports at `build_scene.py:22-25`.
- **North is min-y.** The cardinal convention throughout is north = min-y, south = max-y,
  west = min-x, east = max-x. The front/street facade is the **north** face at y = 0, and
  the exterior_front camera sits at negative y looking in the +y direction.
- **The east and west elevations use model y as their horizontal axis.** Copying the
  north/south elevation code without swapping the axis produces a drawing that is the
  wrong dimension and still looks plausible. The per-side table in S3 is authoritative.
- **SVG y grows downward; DXF and elevation z grow upward.** Plans already handle this in
  exactly one place (`plan2d._dxf_pt`). Elevations and sections must each have exactly
  one flip point too, or they will mirror against each other the way the plan SVG and DXF
  once did.
- **`stairs.py` emits `n − 1` treads for `n` risers,** because the top riser lands on the
  floor above and needs no tread object. Any balustrade derived from tread rectangles
  must not assume tread count equals riser count.
- **`output/` is git-ignored.** Nothing written there survives `git clean -xdf`, including
  a gallery that costs an overnight run. This is the reason PHASE-06 adds
  `deliverables/`.
- **Room schedule areas are gross, not net.** After PHASE-05 introduces `Room.interior`,
  do not switch `pdf.build_room_schedule` to the interior rect — the PDF's published
  numbers would silently change. Gross area is the convention and the intended output.
- **The skill mirror is generated.** Never hand-edit `.agents/skills/homedesign/SKILL.md`;
  edit `.claude/skills/homedesign/SKILL.md` and run `python scripts/sync_skill.py`. CI
  fails otherwise.
- **Blender is absent in CI.** Any test that shells out to Blender must reuse the
  `find_blender()` / `pytest.mark.skipif` guard from `tests/test_framing.py:13-21`, or CI
  goes red on a machine that can never pass it.

## Verification Strategy

- **TEST-001:** `python -m pytest tests -q` → all tests pass; the count grows from `90`
  to at least `120` across the six phases.
- **TEST-002:** `ruff check src tests` → `All checks passed!`
- **TEST-003:** `python scripts/sync_skill.py --check` → `ok: skill copies match`
- **TEST-004 (PHASE-01 teeth check):**
  ```bash
  python -m pytest tests/test_camera_fit.py tests/test_camera_placement.py -q
  ```
  → passes with the fix in place. Then temporarily restore `+ _dot(v, forward)` in
  `src/homedesign/camera_fit.py` and re-run → **must fail**. Restore the fix.
- **TEST-005 (PHASE-01 depiction):**
  ```bash
  python -m homedesign build spec/examples/tubehouse-mini.json
  ```
  → exits 0 in under 60 s and writes `output/png/tubehouse-mini_exterior.png` and
  `output/png/tubehouse-mini_interior.png`.
- **TEST-006 (PHASE-02 engine):**
  ```bash
  BLENDER_CMD="<path-to-blender-4.5>/blender.exe" \
    python -m homedesign render spec/examples/tubehouse-mini.json --profile final --view exterior
  ```
  → prints `eevee raytracing: on` and exits 0.
- **TEST-007 (PHASE-04 drawing set):**
  ```bash
  python -m homedesign plans designs/tubehouse-dream.json
  ls output/svg/tubehouse-dream_elev_*.svg output/svg/tubehouse-dream_section_*.svg | wc -l
  ```
  → prints `6`.
- **TEST-008 (PHASE-04 DXF validity):**
  ```bash
  python -c "import ezdxf, glob; [ezdxf.readfile(f) for f in glob.glob('output/dxf/tubehouse-dream_*.dxf')]; print('ok')"
  ```
  → prints `ok`.
- **TEST-009 (PHASE-05 warning channel):**
  ```bash
  python -m homedesign compile designs/tubehouse-dream.json 2>&1 >/dev/null | wc -l
  ```
  → prints `0` (currently prints `63`).
- **TEST-010 (PHASE-05 backwards compatibility):**
  ```bash
  python -m homedesign compile spec/examples/demo-3br-2storey.json
  python -m homedesign compile spec/examples/courtyard-fixture.json
  python -m homedesign compile spec/examples/tubehouse-mini.json
  ```
  → all three exit 0, and their emitted wall geometry is byte-identical to the
  pre-PHASE-05 output (captured by the test in PHASE-05's Test Specs).
- **TEST-011 (PHASE-06 provenance):**
  ```bash
  python -m homedesign pdf designs/tubehouse-dream.json --require-fresh
  ```
  → exits **1** against stale renders naming the offending view; exits **0** after a
  fresh gallery.
- **TEST-012 (PHASE-06 console script):** `homedesign --help` → prints
  `usage: homedesign [-h] {compile,plans,build,render,pdf} ...`
- **MANUAL-001 (PHASE-01):** Open `output/png/tubehouse-mini_exterior.png`. The whole
  building must be visible with sky above the roofline and ground below the base. Today
  it shows a featureless wall cropped at both the top and bottom of frame.
- **MANUAL-002 (PHASE-01):** Open `output/png/tubehouse-mini_interior.png`. It must show
  a room interior with walls, floor, ceiling and furniture. Today it shows the outside of
  the house on a lawn.
- **MANUAL-003 (PHASE-02):** Compare one interior view rendered with `--profile final`
  (EEVEE Next) against the same view with `--profile cycles`. Record both wall-clock
  times and a one-paragraph quality judgement in `docs/lessons-learned.md`.
- **MANUAL-004 (PHASE-03):** In the aerial render of `designs/tubehouse-dream.json`,
  confirm `terrace_f4` has a continuous parapet on every open edge and that the stair
  flights have balustrades.
- **MANUAL-005 (PHASE-04):** Open the north elevation SVG. Storey lines must be evenly
  spaced at the declared heights (4000, 3400, 3400, 3400, 3400 mm for
  `tubehouse-dream`), openings must sit within their walls, and the ground line must be
  at the bottom.
- **MANUAL-006 (PHASE-06):** Open `output/viewer/tubehouse-dream.html` in a browser with
  the network disconnected. The model must load and orbit.
- **OBS-001:** Every render invocation prints its engine line (`cycles device: ...` or
  `eevee raytracing: ...`) and its accepted view transform, so no run is ever ambiguous
  about which path produced it. Verify these lines appear in
  `output/logs/render-*.log` after a detached run.

## Risks and Alternatives

- **RISK-001:** The six phases touch the camera, render, geometry, drawing, compiler and
  packaging layers in turn, so a late phase can silently regress an early one.
  Mitigation: `python -m pytest tests -q` and `ruff check src tests` are exit criteria for
  every phase, and TEST-010's byte-identity check specifically guards the compiler
  against the most invasive change (PHASE-05).
- **RISK-002:** PHASE-02 depends on a Blender upgrade that could introduce API breaks
  across the whole `blender/` directory at once. Mitigation: ASM-001 keeps 4.1.1
  installed, so every phase can be re-verified against the known-good runtime by
  switching one environment variable.
- **RISK-003:** PHASE-05 changes compiled geometry for any spec that opts into
  `"inside"` alignment, which invalidates previously rendered galleries for that design.
  Mitigation: this is precisely what PHASE-06's provenance hashing exists to detect — and
  the ordering is deliberate, so the first gallery rendered after the geometry change is
  the one the hash certifies.
- **ALT-001:** *Let Blender place the cameras* via `camera_to_view_selected` instead of
  fixing the analytic fit. Rejected: it would move camera logic inside `bpy`, where it
  cannot be unit-tested, and this plan's entire ability to prove the fix (the containment
  sweep, the stand-off assertion) depends on the math staying in pure Python.
- **ALT-002:** *Draw everything behind the section cut* in projection, as a full
  architectural section normally does. Rejected for this plan: it requires depth sorting
  and occlusion, which is a large increase in scope for a first section drawing. S4
  deliberately emits cut elements only; projection behind the cut is a clean follow-on.
- **ALT-003:** *Do textures, HDRI and an asset library instead of geometric realism*
  (PHASE-03). Rejected: textures cannot fix a five-storey terrace with no parapet or a
  stair with no handrail, both of which an architect notices before any material does,
  and the texture work is gated on PHASE-02's engine outcome regardless.
- **ALT-004:** *Author camera positions per view in the spec* rather than deriving them.
  Rejected: it trades a bug for a permanent authoring burden, and it would have hidden
  this class of defect indefinitely — the spec author would simply have compensated for
  the wrong math by hand.

## Suggested Next Step

Execute **PHASE-01**. It is the smallest phase, it is almost entirely pure Python, and
its teeth check (TEST-004) proves the new tests actually fail on the current code before
anything else is built on top. Do not begin PHASE-02 until every PHASE-01 exit criterion
is verified — in particular MANUAL-001 and MANUAL-002, which are the two observations
that motivated this entire plan.
