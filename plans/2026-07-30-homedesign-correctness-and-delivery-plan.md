---
title: "homedesign: Correctness Pass, Render Economics, and Deliverable Quality"
date: "2026-07-30"
status: "draft"
request: "Turn research/2026-07-30-homedesign-next-level-brainstorm.md into a multi-phase implementation plan for the homedesign pipeline (correctness pass, render economics + framing, deliverable quality)."
plan_type: "multi-phase"
research_inputs:
  - "research/2026-07-30-homedesign-next-level-brainstorm.md"
---

# Plan: homedesign — Correctness Pass, Render Economics, and Deliverable Quality

## Objective

The `homedesign` pipeline (JSON spec → 2D SVG/DXF plans → Blender Cycles renders → A3 architect-brief
PDF) runs end to end, but it silently emits geometry that could never be built: staircases with a
57–68 mm tread depth, stairs and lift shafts sealed by the floor slab above, and overlapping window/door
cuts in the same wall. It also takes 11.3 hours to render a 9-view gallery and crops the building out of
frame in every exterior shot. This plan fixes the correctness defects first, then the render loop, then
the drawing and document quality — so the tool's output can be handed to a real architect without
caveats.

## Context Snapshot

- **Current state:** A deterministic Python compiler turns a high-level JSON spec into a fully-derived
  `CompiledModel`, which feeds a pure-Python 2D plan writer (SVG + DXF) and a headless Blender scene
  builder. 44 pure-Python tests exist; the ~600 LOC under `src/homedesign/blender/` has zero coverage.
  There is no `pyproject.toml`, no CI, no lint gate, and the test suite fails on a clean checkout because
  `ezdxf` is not installed. Stair geometry, floor/ceiling penetrations, opening placement and camera
  framing are all wrong in ways the tool does not detect.
- **Desired state:** Every spec in the repo compiles to buildable geometry or fails with a precise,
  actionable error; a preview render completes in seconds rather than minutes; long final renders are
  resumable and survive a disconnected terminal; every gallery image contains the whole building; the 2D
  plans carry real architectural symbols and a title block; the PDF brief is a few megabytes rather than
  13.6 MB and paginates one storey per sheet.
- **Key repo surfaces:** `src/homedesign/compiler.py`, `model.py`, `validate.py`, `errors.py`,
  `placement.py`, `plan2d.py`, `pdf.py`, `orchestrator.py`, `__main__.py`;
  `src/homedesign/blender/build_scene.py`, `geom.py`, `roof.py`, `joinery.py`,
  `procedural_furniture.py`, `furnish.py`, `materials.py`; `spec/homespec.schema.json`,
  `spec/tubehouse-dream.json`, `spec/examples/*.json`; `tests/*.py`;
  `.claude/skills/homedesign/SKILL.md`; `AGENTS.md`.
- **Out of scope:** IFC/BIM export (`src/ifc_export_utils.py` stays parked); glTF export and a web 3D
  viewer; PBR textures, HDRI lighting and external asset libraries; neighbour/street context massing;
  curved or diagonal geometry; split levels; cost estimation; structural or MEP analysis. These are
  deliberate follow-ups, not omissions — see `## Risks and Alternatives`.

## Environment & Conventions

- **Stack:** Python 3.11 (3.11.15 verified present; 3.12 also acceptable). Blender **4.1.1** at
  `C:/Users/tukum/Blender/blender-4.1.1-windows-x64/blender.exe`, driven headlessly as a subprocess —
  the project never imports `bpy` in system Python. `uv` 0.11.x is available for running tools.
  Primary development platform is Windows 11; shell examples below are POSIX-style and run under Git
  Bash, which is present. Third-party runtime deps today: `jsonschema`, `ezdxf`, `ifcopenshell`
  (declared but unused by the active pipeline).
- **Setup:** There is **no** `pyproject.toml` today — PHASE-01 creates it. Until then:
  `python -m pip install -r requirements.txt`. After PHASE-01: `python -m pip install -e ".[dev]"`.
- **Build / Run:** No compile step. The pipeline is invoked as:
  - `PYTHONPATH=src python -m homedesign compile spec/tubehouse-dream.json`
  - `PYTHONPATH=src python -m homedesign plans spec/tubehouse-dream.json`
  - `PYTHONPATH=src python -m homedesign build spec/tubehouse-dream.json [--final]`
  - `PYTHONPATH=src python -m homedesign pdf spec/tubehouse-dream.json`
  After PHASE-01's editable install the `PYTHONPATH=src` prefix becomes unnecessary, but it must keep
  working — the Blender-side scripts rely on the same layout.
- **Test:** Full suite: `python -m pytest tests -q` run from the repo root. Single test:
  `python -m pytest tests/test_compiler.py::test_demo_compiles_two_storeys -q`.
  **Trap:** the suite currently only works via `python -m pytest` (which puts the repo root on
  `sys.path`), not bare `pytest`. PHASE-01 removes this trap.
- **Conventions & traps:**
  - **All spec and compiled-model lengths are millimetres.** Blender-side code divides by 1000 at the
    boundary and works in metres. Never mix the two; every new field must state its unit in its name
    (`_mm`) or be metres-only inside `src/homedesign/blender/`.
  - Plan coordinates: origin at the plot's front-left corner, `+x` to the east, `+y` to the south
    (increasing depth away from the street). Cardinal convention used throughout the compiler:
    **north = min-y, south = max-y, west = min-x, east = max-x.**
  - Angles are degrees in specs and dataclasses (`pitch_deg`, `rot_deg`), radians only inside Blender
    calls.
  - Pure/impure split is load-bearing: anything importable without `bpy` lives in `src/homedesign/`;
    anything importing `bpy` lives in `src/homedesign/blender/`. Keep new geometry math on the pure side
    so it is unit-testable.
  - Tests are **pytest** (they use `pytest.raises`), despite `AGENTS.md` prescribing `unittest`.
  - `output/` is gitignored and every file in it is a regenerable artifact — never hand-edit.
  - Lint: `ruff` 0.15.7 (a `.ruff_cache/` exists but no config). Default rules currently report exactly
    5 errors, all unused imports.
- **Repo map:**
  ```
  src/homedesign/            pure Python: compiler, model, validate, errors, placement,
                             plan2d, pdf, orchestrator, __main__ (CLI)
  src/homedesign/blender/    bpy-only: build_scene (entry point), geom, roof, joinery,
                             materials, furnish, procedural_furniture
  src/ifc_export_utils.py    PARKED dead code, targets a retired spec format — do not touch
  spec/homespec.schema.json  JSON Schema (draft 2020-12) for the input spec
  spec/tubehouse-dream.json  the flagship 5-storey 4m x 25m design
  spec/examples/*.json       demo-3br-2storey, tubehouse-mini, courtyard-fixture (test fixtures)
  spec/briefs/*.json         PDF cover/narrative/requirements copy, keyed by meta.name
  tests/                     pytest suite, pure Python only
  output/                    gitignored artifacts: svg/ dxf/ png/ blend/ compiled/ pdf/
  ```

## Research Inputs

- From `research/2026-07-30-homedesign-next-level-brainstorm.md`:
  - **Stairs are unbuildable in every spec in the repo.** `compiler._derive_stairs` sizes treads as
    `stairwell_long_dimension / n_risers`. Measured going: `tubehouse-dream` 57–68 mm,
    `demo-3br-2storey` 147 mm, `tubehouse-mini` 111–118 mm. Code minimum is ~250 mm. The only stair
    validation today is a 900 mm minimum shaft *width*.
  - **No floor void for vertical circulation.** `build_scene.build_floors_and_stairs` emits a slab for
    every room on every storey, including `stairwell` and `elevator`, so each flight terminates against
    the ceiling and the lift is a stack of sealed boxes.
  - **Openings silently overlap.** `compiler._place_openings` hardcodes `offset = (span - width) / 2`.
    Verified on `tubehouse-dream` level 0, wall `F0_W019`: a 3000 mm garage door (offset 500–3500,
    head 2100) and a 1000 mm window (offset 1500–2500, sill 1800) are cut into the same hole.
  - **`rot_deg` is a latent repeat of an already-fixed bug.** `placement.py` always emits `rot_deg=0`, so
    `procedural_furniture.py`'s `obj.rotation_euler` branch never fires. All meshes bake world position
    into vertices with the object origin left at `(0,0,0)`, so object-level rotation pivots around the
    world origin — the exact failure that previously flung 32 door leaves across the scene. The fix
    already exists as `geom.make_hinged_box` (bakes rotation into vertices about a real pivot).
  - **The test suite is red on a clean checkout** (`ModuleNotFoundError: ezdxf` aborts pytest
    collection); 39 of 44 pass when `tests/test_plan2d.py` is excluded. Tests import `src.homedesign.*`
    while the CLI and the Blender scripts import `homedesign.*` — two import identities for one package.
  - **`scene.cycles.device = "GPU"` is a silent no-op** — it requires
    `preferences.addons["cycles"].preferences.compute_device_type` plus device enablement, and it sits
    inside a bare `try/except`. The target machine (Intel i5-8250U, Intel UHD 620) has **no Cycles GPU
    backend at all**, so GPU rendering is not an available lever; EEVEE previews and workflow changes are.
  - **Camera framing crops the building out of frame** in both `tubehouse-dream_exterior_front.png` and
    `_exterior_aerial.png`. `_build_exterior_front_camera` is a stack of hand-tuned magic multipliers.
    In `tubehouse-dream_living.png` the dining table and four chairs that `placement._plan_living`
    genuinely placed sit *behind* the camera.
  - **The PDF brief is 13.6 MB from a 27 MB HTML** because `pdf._img_data_uri` base64-inlines every
    full-resolution PNG. Plan pages spill onto a second A3 sheet because the generated SVG carries
    hardcoded pixel `width`/`height` attributes that CSS `max-width` cannot override in print.
  - **63 wall segments cross the plot boundary** in `tubehouse-dream` — rooms are bounds-checked, walls
    are not, because exterior walls are centred on the room edge and so extend 100 mm beyond it.
  - **Documentation has drifted:** `AGENTS.md` points at `run.sh` (deleted), `freecad-mcp-guide.md`
    (nonexistent) and `spec/floorplan-spec.json` (retired), and prescribes `unittest` for a pytest suite.
    `.claude/skills/homedesign/SKILL.md` directs user designs to `output/specs/<slug>.json` — a directory
    that does not exist, under a gitignored tree.

## Assumptions and Constraints

- **DEC-001:** Geometry stays strictly rectilinear and axis-aligned. No curved or diagonal walls, no
  split levels. The sweep-line wall derivation in `compiler._derive_walls` depends on this.
- **DEC-002:** The pure/impure split is preserved: all new geometry math goes in `src/homedesign/`
  (importable without `bpy`); `src/homedesign/blender/` only consumes it.
- **DEC-003:** All schema changes are **additive with preserved defaults** — every spec currently in
  `spec/` and `spec/examples/` must still validate against the schema after each phase (their *content*
  may be edited by PHASE-02, but no previously-legal spec shape becomes illegal).
- **DEC-004:** GPU rendering is not pursued as a performance lever; the target hardware has no Cycles GPU
  backend. Speed comes from EEVEE previews, render/build separation, resumability and Cycles tuning.
- **CON-001:** Blender is 4.1.1. Its EEVEE engine identifier is `BLENDER_EEVEE`; Blender 4.2+ renamed it
  to `BLENDER_EEVEE_NEXT`. Engine selection must try both and fall back, never hardcode one.
- **CON-002:** The Blender-side scripts run under Blender's bundled Python, which cannot see an editable
  install in system Python. The `sys.path.insert` of the `src/` directory at the top of
  `blender/build_scene.py` and `blender/furnish.py` must remain.
- **CON-003:** A full-quality (`--final`) Cycles render of the 9-view `tubehouse-dream` gallery takes
  ~11.3 hours on the target machine. Do not run one as part of routine verification; the phases below
  verify with preview renders and single-view final renders only.
- **ASM-001:** Target stair comfort rule is the Blondel relation. **BINDING DEFAULT:** riser `R` and
  going `G` in millimetres must satisfy `600 <= 2R + G <= 640`, with `G >= 250` and `R <= 190`.
- **ASM-002:** Minimum clear stair flight width. **BINDING DEFAULT:** 900 mm per flight; a two-flight
  U-return shaft therefore needs `2 x 900 + 100` = 1900 mm minimum clear width, where 100 mm is the
  stairwell well (gap) between flights.
- **ASM-003:** How to resolve `tubehouse-dream`'s undersized 1100 x 1300 mm stair shaft.
  **BINDING DEFAULT:** keep the authored storey heights (ground 4000 mm, upper 3400 mm) and enlarge the
  shaft to a uniform 1900 x 3700 mm on all five storeys, re-laying the circulation core exactly as
  specified in TASK-02-07. Do **not** reduce the ground storey height.
- **ASM-004:** Whether walls crossing the plot boundary are an error or a warning. **BINDING DEFAULT:**
  a **warning** (`severity="warning"`), not an error — it affects all four existing specs and blocking
  them adds no safety. Warnings print to stderr but do not fail the command.
- **ASM-005:** Preview render engine settings. **BINDING DEFAULT:** EEVEE at 32 TAA render samples,
  960x540, soft shadows on. Cycles is used only for `--profile final`.
- **ASM-006:** Where user-authored designs live. **BINDING DEFAULT:** a new git-tracked `designs/`
  directory at the repo root, replacing the gitignored `output/specs/` path in the skill documentation.
- **ASM-007:** Gallery image downscaling for the PDF. **BINDING DEFAULT:** downscale to 1400 px wide
  using Pillow, added as a runtime dependency; skip downscaling with a warning if Pillow is absent.
- **ASM-008:** Python version floor. **BINDING DEFAULT:** `requires-python = ">=3.11"` (the code uses
  `X | None` union syntax and `from __future__ import annotations` throughout).

## Specification

### S1. Stair sizing (used by PHASE-02)

All symbols are millimetres unless stated. Given storey height `H` and stair shaft rectangle
`w` x `d`:

```
n      = max(2, round(H / 175))          # number of risers; 175 is the target riser height
R      = H / n                           # actual riser height
G      = max(250, 600 - 2R)              # going (tread depth), from the Blondel relation
LONG   = max(w, d)                       # axis the flights run along
SHORT  = min(w, d)                       # axis across the flights
```

- `n` — riser count. Every riser lifts the walker by `R`; the topmost riser lands on the floor above, so
  a flight of `n` risers contains `n - 1` physical treads.
- `R` — riser height. Reject with code `stair_riser_too_tall` if `R > 190`.
- `G` — going, i.e. the horizontal depth of one tread. The `max(250, ...)` floor guarantees a usable
  tread even when `2R` is already large. Assert `600 <= 2R + G <= 640`; a value outside that band after
  applying the formula indicates `R > 190` and is covered by the rejection above.

**Straight flight feasibility**

```
treads       = n - 1
run_required = treads * G
fits         = (LONG >= run_required) and (SHORT >= 900)
```

**U-return (two flights with a half-landing) feasibility**

```
flight_w      = (SHORT - 100) / 2        # 100 = stairwell well between the two flights
n_a           = ceil(n / 2)              # risers climbed before the landing
treads_a      = n_a - 1                  # treads in the lower flight
treads_b      = n - n_a - 1              # treads in the upper flight
landing_depth = max(900, flight_w)
run_required  = max(treads_a, treads_b) * G + landing_depth
fits          = (SHORT >= 1900) and (LONG >= run_required)
```

**Mode selection** (`stairs.mode`, default `"auto"`):

1. `"none"` → generate no treads. The shaft still contributes a floor void (S2).
2. `"auto"` → use `"straight"` if it fits; else `"u_return"` if it fits; else emit
   `stair_shaft_too_small`.
3. `"straight"` / `"u_return"` explicitly → if it does not fit, emit `stair_shaft_too_small`.
4. The `stair_shaft_too_small` message must name both minimums verbatim, e.g.
   `stair shaft 'stair' is 1100x1300mm; a straight flight needs 900x4500mm and a U-return needs 1900x3150mm at a 3400mm storey height`.

**Reference values** (computed for the specs in this repo; the executor should reproduce these exactly):

| Spec | H (mm) | n | R (mm) | G (mm) | Straight min (W x D) | U-return min (W x D) | Current shaft |
|---|---|---|---|---|---|---|---|
| `demo-3br-2storey` | 3000 | 17 | 176.5 | 250.0 | 900 x 4000 | 1900 x 2900 | 2000 x 2500 |
| `tubehouse-mini` L0 | 3200 | 18 | 177.8 | 250.0 | 900 x 4250 | 1900 x 2900 | 1500 x 2000 |
| `tubehouse-mini` L1 | 3000 | 17 | 176.5 | 250.0 | 900 x 4000 | 1900 x 2900 | 1500 x 2000 |
| `tubehouse-dream` L0 | 4000 | 23 | 173.9 | 252.2 | 900 x 5548 | 1900 x 3674 | 1100 x 1300 |
| `tubehouse-dream` L1-L4 | 3400 | 19 | 178.9 | 250.0 | 900 x 4500 | 1900 x 3150 | 1100 x 1300 |

**Tread geometry.** `Tread.z` is redefined as the elevation of the tread's **walking surface (top
face)**, measured from the storey's own floor level — not the bottom of the tread box. Blender draws
each tread as a slab occupying `[z - 0.05, z]` metres. Straight flight running along `+y`
(`long_is_depth` true), for `i` in `0 .. treads-1`:

```
tread_i = Rect(x = shaft.x, y = shaft.y + i * G, w = SHORT, d = G),  z = (i + 1) * R
```

U-return running along `+y`, lower flight on the west half, upper flight on the east half:

```
lower_i  (i = 0 .. treads_a-1): x = shaft.x,                        w = flight_w, y = shaft.y + i * G,        d = G, z = (i + 1) * R
landing:                        x = shaft.x,                        w = SHORT,    y = shaft.y + treads_a * G, d = landing_depth, z = n_a * R
upper_j  (j = 0 .. treads_b-1): x = shaft.x + flight_w + 100,       w = flight_w,
                                y = landing.y - (j + 1) * G,        d = G,        z = (n_a + j + 1) * R
```

When `long_is_depth` is false, swap the roles of `x`/`w` and `y`/`d` throughout. The landing is emitted
as an ordinary `Tread` so no new dataclass is needed.

### S2. Floor voids (used by PHASE-02)

For storey at level `L`, `floor_voids` is the list of rectangles that must be punched out of that
storey's floor slabs:

1. If `L` is the lowest level in the model, `floor_voids = []`.
2. Otherwise, let `P` be the storey at level `L - 1`. `floor_voids` contains the rectangle of every room
   in `P` that is either (a) of type `stairwell` and whose storey has generated stairs
   (`mode != "none"`), or (b) of type `elevator`.
3. Additionally, for **every** level including the lowest, the rectangle of every `elevator` room on that
   same storey is included — a lift shaft is open at every level it passes through.
4. Duplicate rectangles (identical within 1 mm) are collapsed to one entry.

The Blender floor builder subtracts these rectangles from each room's slab using the existing
rectangle-subtraction algorithm, which is moved to a shared pure module in TASK-02-01.

### S3. Opening placement (used by PHASE-03)

Given a wall segment of span `S` (its length along its long axis) and an opening of width `W`:

```
align = "center" -> offset = (S - W) / 2
align = "start"  -> offset = 0
align = "end"    -> offset = S - W
offset_mm present -> offset = offset_mm            # overrides `align` entirely
```

`offset` is measured from the wall segment's start (its minimum `y` for a vertical wall, minimum `x` for
a horizontal wall). Reject with `opening_out_of_wall` when `offset < 0` or `offset + W > S + 1`
(1 mm tolerance).

Two openings `a` and `b` on the same wall **overlap** when both are true:

```
plan overlap:      min(a.offset + a.width, b.offset + b.width) - max(a.offset, b.offset) > 1
elevation overlap: min(a.head, b.head) - max(a.sill, b.sill) > 1
```

Overlap emits `opening_overlap` naming both opening ids and the wall id. The 1 mm slack lets two
openings sit exactly edge-to-edge without tripping the rule.

### S4. Camera framing (used by PHASE-05)

Fit an axis-aligned bounding box in the camera frame. Inputs: box corners `C = {c_1..c_8}` (metres),
box centre `p`, unit view direction `f` (from camera toward the subject), camera right `r` and up `u`
(orthonormal with `f`), focal length `lens` (mm), sensor width `sw = 36.0` mm with
`sensor_fit = 'HORIZONTAL'`, render resolution `res_x` x `res_y`, and margin factor `m = 1.08`.

```
half_fov_x = atan( sw / (2 * lens) )
half_fov_y = atan( (sw * res_y) / (2 * lens * res_x) )

for each corner c:
    v   = c - p                                     # corner offset from the box centre
    d_x = |v . r| / tan(half_fov_x) + (v . f)       # distance needed so this corner fits horizontally
    d_y = |v . u| / tan(half_fov_y) + (v . f)       # ... and vertically

distance = m * max over all corners of max(d_x, d_y)
eye      = p - f * distance
```

- `v . r`, `v . u`, `v . f` are dot products — the corner's offset resolved onto the camera's right, up
  and forward axes respectively.
- Adding `(v . f)` accounts for corners nearer the camera than the centre needing more pull-back.
- `m = 1.08` leaves an 8% margin so the subject never touches the frame edge.
- Clamp `distance` to a minimum of 1.0 m so degenerate boxes cannot put the camera inside the geometry.

Applied per view kind:
- `exterior_front` — subject box is the whole building (plot footprint x total height, excluding the
  ground plane). `f` points from the street toward the building: azimuth along `+y`, elevation `-15°`.
- `exterior_aerial` — same subject box; `f` at azimuth 45° from the front-left, elevation `-40°`.
- `room` — subject box is the room's interior volume **unioned with every furniture item placed in it**
  (from `placement.plan_room`), from floor to a 2.4 m ceiling. `f` points along the room's long axis from
  the near end, at the eye height of 1.5 m above the storey floor, elevation `-5°`.

## Phase Summary

| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Packaged project, one import root, green test + lint gate in CI | None | `pyproject.toml`, unified imports, `.github/workflows/ci.yml`, `ruff.toml` |
| PHASE-02 | Buildable vertical circulation: real stairs + floor voids | PHASE-01 | `stairs.py`, `rects.py`, `Storey.floor_voids`, resized shafts in all 4 specs |
| PHASE-03 | Correct openings, safe furniture rotation, validation rule registry | PHASE-02 | `checks.py`, opening `align`/`offset_mm`, `--json` errors, rotation fix |
| PHASE-04 | Fast preview loop and survivable final renders | PHASE-01 | EEVEE preview profile, `render` subcommand, resumable + detached rendering |
| PHASE-05 | Every render frames its subject | PHASE-04 | `camera_fit.py`, rebuilt exterior and room cameras |
| PHASE-06 | Drawing and document quality; docs consolidation | PHASE-03, PHASE-05 | Plan symbols + title block, DXF axis fix, PDF slimming + schedules, rewritten docs |

## Detailed Phases

### PHASE-01 - Packaging, Imports, and a Green Gate

**Goal**
Make `python -m pytest tests -q` pass from a clean checkout, collapse the two import identities of the
package into one, and add automated test and lint gates so every later phase has a trustworthy signal.

**Tasks**
- [x] TASK-01-01: Create `pyproject.toml` declaring a `src`-layout package named `homedesign`, with
      `requires-python = ">=3.11"`, runtime dependencies `jsonschema>=4.0`, `ezdxf>=1.0`, `pillow>=10.0`,
      and a `dev` extra containing `pytest>=8.0` and `ruff==0.15.7`. Do **not** declare `ifcopenshell` —
      it is only used by the parked `src/ifc_export_utils.py`, which is excluded from the package.
- [x] TASK-01-02: Add `[tool.pytest.ini_options]` with `testpaths = ["tests"]` and
      `pythonpath = ["src"]` so bare `pytest` works as well as `python -m pytest`.
- [x] TASK-01-03: Rewrite the imports in all five test modules from `src.homedesign.*` to `homedesign.*`.
      This is the only change to their bodies.
- [x] TASK-01-04: Delete `requirements.txt` and replace every reference to it in documentation with the
      editable-install command. Confirm no script reads it.
- [x] TASK-01-05: Add `ruff.toml` with `line-length = 120` and ruff's default rule selection, then fix
      the exact 5 existing violations, which are:
      - `src/homedesign/blender/furnish.py:13` `E402` module-level import not at top of file — add
        `# noqa: E402` to that line, matching the convention already used in
        `src/homedesign/blender/build_scene.py`. The import genuinely must follow the `sys.path`
        bootstrap above it (CON-002); do not move it.
      - `src/homedesign/blender/geom.py:61` `F841` unused local `dg` — handled by TASK-01-06.
      - `src/homedesign/blender/joinery.py:2` `F401` unused `import bpy` — delete the import.
      - `src/homedesign/blender/procedural_furniture.py:5` `F401` unused `import bpy` — delete the
        import.
      - `src/homedesign/plan2d.py:8` `F401` unused `import math` — delete the import.
      Do not reformat unrelated code.
- [x] TASK-01-06: Remove the dead `dg = bpy.context.evaluated_depsgraph_get()` line in
      `src/homedesign/blender/geom.py` (inside `boolean_difference`) — its result is never used.
- [x] TASK-01-07: Create `.github/workflows/ci.yml` running on push and pull request: checkout,
      set up Python 3.11, `python -m pip install -e ".[dev]"`, `ruff check src tests`,
      `python -m pytest tests -q`. Blender is not available in CI, so no render step.

**File Changes**
- `pyproject.toml` (create): package metadata, `[build-system]` using setuptools, `[project]` with deps
  and the `dev` extra, `[tool.setuptools.packages.find]` with `where = ["src"]`,
  `[tool.pytest.ini_options]`.
- `ruff.toml` (create): `line-length = 120`; leave rule selection at ruff's default.
- `.github/workflows/ci.yml` (create): the lint + test job described in TASK-01-07.
- `requirements.txt` (delete): superseded by `pyproject.toml`.
- `tests/test_compiler.py`, `tests/test_validate.py`, `tests/test_plan2d.py`, `tests/test_pdf.py`,
  `tests/test_placement.py` (modify): change `from src.homedesign...` to `from homedesign...`. Leave all
  test logic untouched.
- `src/homedesign/blender/geom.py` (modify): remove only the dead `dg = bpy.context.evaluated_depsgraph_get()`
  line inside `boolean_difference`. `import bpy` is used elsewhere in this file — keep it. Keep
  `make_box`, `make_hinged_box` and `boolean_difference` behaviour identical.
- `src/homedesign/blender/joinery.py` (modify): remove the unused `import bpy` (line 2). Change nothing
  else.
- `src/homedesign/blender/procedural_furniture.py` (modify): remove the unused `import bpy` (line 5).
  Note `build_item` still does a local `import math` inside the rotation branch — leave it; PHASE-03
  removes that branch entirely.
- `src/homedesign/blender/furnish.py` (modify): add `# noqa: E402` to the `from . import
  procedural_furniture as pf` import on line 13. Change nothing else.
- `src/homedesign/plan2d.py` (modify): remove the unused `import math`. Change nothing else.

**Function Signatures**
None — no code interfaces change in this phase.

**Test Specs**
- `python -m pytest tests -q` from a clean checkout after `python -m pip install -e ".[dev]"` → **44
  passed**, 0 errors, 0 skipped. (Today: collection error; 39 passed when `test_plan2d.py` is excluded.)
- `pytest -q` (bare, no `python -m`) → same 44 passed, proving the `pythonpath` setting works.
- `PYTHONPATH=src python -m homedesign compile spec/examples/tubehouse-mini.json` → exit code 0 and
  prints a path ending `output/compiled/tubehouse-mini.model.json`. This proves CON-002's import path
  still functions.
- `ruff check src tests` → `All checks passed!`.

**Dependencies**
- None.

**Exit Criteria**
- [x] `python -m pytest tests -q` reports 44 passed from a clean checkout.
- [x] `ruff check src tests` exits 0.
- [x] `grep -rn "src\.homedesign" tests/` returns no matches.
- [x] `PYTHONPATH=src python -m homedesign build spec/examples/tubehouse-mini.json` still completes
      (preview render), proving the Blender-side `sys.path` bootstrap is intact.

**Phase Risks**
- **RISK-01-01:** An editable install can shadow the `PYTHONPATH=src` path and cause `homedesign` to
  resolve twice, duplicating module-level caches such as `materials._cache`. Mitigation: both routes
  resolve to the same `src/homedesign` directory, so `sys.modules` keys collide correctly; verify with
  `python -c "import homedesign, sys; print(homedesign.__file__)"` from the repo root and confirm it
  points inside `src/`.

---

### PHASE-02 - Buildable Vertical Circulation

**Goal**
Replace the tread-slicing stair with a real straight/U-return generator governed by S1, punch stair and
lift voids through the floor slabs per S2, and resize the stair shafts in all four repo specs so they
compile against the new rules.

**Tasks**
- [ ] TASK-02-01: Create `src/homedesign/rects.py` holding the pure rectangle-subtraction algorithm,
      moved verbatim from `src/homedesign/blender/roof.py` (`_subtract_rect`, `_subtract_rects`) and
      renamed to the public `subtract_rect` / `subtract_rects`. Update `roof.py` to import them. This
      makes the algorithm unit-testable outside Blender and reusable for floor voids.
- [ ] TASK-02-02: Create `src/homedesign/stairs.py` implementing S1: sizing, feasibility for both modes,
      mode selection, and tread/landing generation. It must not import `bpy`.
- [ ] TASK-02-03: Add `mode` to the `stairs` object in `spec/homespec.schema.json` as
      `{"type": "string", "enum": ["auto", "straight", "u_return", "none"], "default": "auto"}`. Leave
      `room` and `direction` unchanged.
- [ ] TASK-02-04: Replace `compiler._derive_stairs` with a call into `stairs.derive_stairs`, propagating
      `stair_shaft_too_small` and `stair_riser_too_tall` into the compiler's `errors` list (so they
      surface via `SpecValidationError` exactly like existing compile errors).
- [ ] TASK-02-05: Add `floor_voids: list[Rect]` to the `Storey` dataclass in
      `src/homedesign/model.py` (default `field(default_factory=list)`), populate it in `compile_spec`
      per S2, and round-trip it in `CompiledModel.from_dict`.
- [ ] TASK-02-06: Update `blender/build_scene.build_floors_and_stairs` to (a) subtract
      `storey["floor_voids"]` from each room's floor slab using `rects.subtract_rects`, emitting one box
      per surviving fragment, and (b) draw treads as slabs occupying `[z - 0.05, z]` metres per S1's
      redefinition of `Tread.z`.
- [ ] TASK-02-07: Re-lay the `tubehouse-dream` circulation core on **all five storeys** to the following
      identical rectangles (per ASM-003), replacing the current `elevator` / `hall` / `stair` entries:
      - `stair` (`stairwell`): `{"x": 0, "y": 11000, "w": 1900, "d": 3700}`
      - `hall` (`hall`): `{"x": 1900, "y": 11000, "w": 1100, "d": 3700}`
      - `elevator` (`elevator`): `{"x": 3000, "y": 11000, "w": 1000, "d": 1400}`
      - The rectangle `{"x": 3000, "y": 12400, "w": 1000, "d": 2300}` is left **untiled** on every
        storey — this is the relocated light well.
      Then update the level-4 `roof.voids` entry to `{"x": 3000, "y": 12400, "w": 1000, "d": 2300}` to
      match, keeping `roof.rect` otherwise as authored.
- [ ] TASK-02-08: Absorb the resulting +1200 mm core depth on each `tubehouse-dream` storey: shift every
      room with `rect.y >= 13500` by `+1200`, then reduce the depth of the storey's largest such room by
      1200 so that the rearmost room still ends at `y = 25000`. Concretely:
      - L0: `lease_gf` → `{"y": 14700, "d": 10300}`.
      - L1: `lease_f1_rear` → `{"y": 14700, "d": 8800}`; `wc_f1` and `storage_f1` keep `y = 23500`.
      - L2: `kitchen_f2` → `{"y": 14700, "d": 4500}`; `dining_f2` → `{"y": 19200, "d": 3800}`;
        `wc_f2` and `utility_f2` keep `y = 23000`.
      - L3: `kid_bed_f3` → `{"y": 14700, "d": 6800}`; `bath_f3` → `{"y": 14700, "d": 3000}`;
        `laundry_f3` → `{"y": 17700, "d": 3800}`; `flex_lounge_f3` keeps `y = 21500`.
      - L4: `office_f4` → `{"y": 14700, "d": 5000}`; `guestbed_f4` → `{"y": 19700, "d": 3800}`;
        `guestbath_f4` and `storage_f4` keep `y = 23500`.
- [ ] TASK-02-09: Resize the stair shafts in the three example specs to satisfy the U-return minimum
      (1900 x 2900 mm), absorbing the change from the adjacent hall or corridor room so no room overlaps
      and no room leaves the plot: `spec/examples/demo-3br-2storey.json` (currently 2000 x 2500) and
      `spec/examples/tubehouse-mini.json` (currently 1500 x 2000). `spec/examples/courtyard-fixture.json`
      declares no stairs and needs no change. Re-run compilation after each edit and fix any
      `opening_no_wall` errors the geometry shift produces, using the error messages as the guide.
- [ ] TASK-02-10: Update `.claude/skills/homedesign/SKILL.md` to document `stairs.mode`, the shaft-size
      rule, and the fact that an undersized shaft is now a hard compile error naming the required size.

**File Changes**
- `src/homedesign/rects.py` (create): `subtract_rect`, `subtract_rects` — pure, no imports beyond
  typing. Behaviour identical to the current private functions in `roof.py`.
- `src/homedesign/stairs.py` (create): S1 in code — sizing, feasibility, mode selection, tread emission.
- `src/homedesign/blender/roof.py` (modify): delete `_subtract_rect`/`_subtract_rects`, import from
  `homedesign.rects` instead. Leave `build_roof`, `_build_gable`, `_build_shed`, `_build_mesh` unchanged.
- `src/homedesign/compiler.py` (modify): replace `_derive_stairs` (lines ~347-364) with a delegation to
  `stairs.derive_stairs`; add floor-void derivation per S2 after the storey loop (it needs the previous
  storey, so compute it in a second pass once all storeys exist). Leave wall derivation, opening
  placement and roof derivation untouched.
- `src/homedesign/model.py` (modify): add `floor_voids: list[Rect]` to `Storey`; handle it in
  `CompiledModel.from_dict` alongside the existing `roof["voids"]` handling. Leave every other dataclass
  alone.
- `src/homedesign/blender/build_scene.py` (modify): rewrite `build_floors_and_stairs` per TASK-02-06.
  Leave `build_walls`, `build_environment`, `add_interior_lights` and the camera functions untouched in
  this phase.
- `spec/homespec.schema.json` (modify): add `mode` to the `stairs` object only.
- `spec/tubehouse-dream.json` (modify): core rectangles per TASK-02-07, rear-room shifts per TASK-02-08,
  roof void per TASK-02-07.
- `spec/examples/demo-3br-2storey.json`, `spec/examples/tubehouse-mini.json` (modify): stair shaft
  resize per TASK-02-09.
- `tests/test_stairs.py` (create): the Test Specs below.
- `tests/test_rects.py` (create): rectangle-subtraction cases.
- `.claude/skills/homedesign/SKILL.md` (modify): document `stairs.mode` and the shaft rule.

**Function Signatures**
- `subtract_rect(box: tuple[float, float, float, float], hole: tuple[float, float, float, float]) -> list[tuple[float, float, float, float]]`
  — the `(x, y, w, d)` fragments of `box` remaining after removing `hole`; returns `[box]` unchanged when
  they do not intersect.
- `subtract_rects(x: float, y: float, w: float, d: float, holes: list[tuple[float, float, float, float]]) -> list[tuple[float, float, float, float]]`
  — the fragments of one rectangle after removing every hole in turn.
- `stair_sizing(storey_height_mm: float) -> tuple[int, float, float]` — `(n_risers, riser_mm, going_mm)`
  per S1.
- `straight_minimum(storey_height_mm: float) -> tuple[float, float]` — `(min_width_mm, min_depth_mm)`
  for a straight flight.
- `u_return_minimum(storey_height_mm: float, short_mm: float = 1900.0) -> tuple[float, float]` —
  `(min_width_mm, min_depth_mm)` for a U-return.
- `derive_stairs(stairs_spec: dict | None, rooms: list[Room], storey_height_mm: float, level: int, path: str, errors: list[SpecError]) -> Stairs | None`
  — the compiled `Stairs` with treads and landing, or `None` when there is no stair or the shaft is too
  small (in which case a `SpecError` is appended to `errors`).

**Test Specs**
- `stair_sizing(3400)` → `(19, 178.94736842105263, 250.0)`; assert `600 <= 2*R + G <= 640`.
- `stair_sizing(4000)` → `(23, 173.91304347826087, 252.17391304347825)`; assert `2*R + G` is
  `600.0` within 1e-6.
- `straight_minimum(3400)` → `(900.0, 4500.0)`. `u_return_minimum(3400)` → `(1900.0, 3150.0)`.
- `u_return_minimum(4000)` → `(1900.0, 3673.913...)` — assert `3674.0` within 0.5.
- `derive_stairs` on a shaft of `1100 x 1300` at `H = 3400` with `mode = "auto"` → returns `None` and
  appends exactly one error with `code == "stair_shaft_too_small"` whose message contains both
  `900x4500` and `1900x3150`.
- `derive_stairs` on a shaft of `900 x 4600` at `H = 3400` with `mode = "auto"` → straight flight with
  **18** treads; `treads[0].z == 178.947...`; `treads[-1].z == 3400.0` within 1e-6;
  every tread has `d == 250.0` and `w == 900.0`.
- `derive_stairs` on a shaft of `1900 x 3200` at `H = 3400` with `mode = "auto"` → U-return with
  `9 + 1 + 9 = 19` emitted rectangles (9 lower treads, 1 landing, 9 upper treads); the landing has
  `w == 1900.0` and `d == 950.0`; the lower flight's rectangles have `x == shaft.x` and `w == 900.0`;
  the upper flight's have `x == shaft.x + 1000.0` and `w == 900.0`; `treads[-1].z == 3400.0` within 1e-6.
- `derive_stairs` with `mode = "none"` on any shaft → returns `None` and appends **no** error.
- `derive_stairs` with `mode = "straight"` on a `1900 x 3200` shaft at `H = 3400` → error
  `stair_shaft_too_small` (the shaft fits a U-return but not a straight flight, and the explicit mode
  must not silently fall back).
- `subtract_rects(0, 0, 4000, 4000, [(1000, 1000, 1000, 1000)])` → 4 fragments whose areas sum to
  `4000*4000 - 1000*1000 = 15_000_000`.
- `subtract_rects(0, 0, 4000, 4000, [])` → exactly `[(0, 0, 4000, 4000)]`.
- `subtract_rects(0, 0, 1000, 1000, [(5000, 5000, 100, 100)])` → exactly `[(0, 0, 1000, 1000)]`
  (non-intersecting hole leaves the box whole).
- `compile_spec(spec/tubehouse-dream.json)` → `storeys[1].floor_voids` contains the level-0 `stair`
  rectangle `{x: 0, y: 11000, w: 1900, d: 3700}` and an `elevator` rectangle; `storeys[0].floor_voids`
  contains the level-0 `elevator` rectangle only (per S2 rule 3) and **not** the stair.
- `compile_spec` on every file in `spec/` and `spec/examples/` → no `SpecValidationError`.

**Dependencies**
- PHASE-01 (packaged imports and a green baseline).

**Exit Criteria**
- [ ] `PYTHONPATH=src python -m homedesign compile spec/tubehouse-dream.json` exits 0.
- [ ] `python - <<'EOF'` script reading `output/compiled/tubehouse-dream.model.json` reports a minimum
      tread depth of `>= 250` mm on every storey (today: 57–68 mm).
- [ ] Every spec in `spec/` and `spec/examples/` compiles without error.
- [ ] `python -m pytest tests -q` passes, including the new `tests/test_stairs.py` and
      `tests/test_rects.py`.
- [ ] `PYTHONPATH=src python -m homedesign build spec/examples/tubehouse-mini.json` completes and the
      saved `.blend` contains more floor-slab fragments than rooms on levels above the ground (proof the
      voids were punched).

**Phase Risks**
- **RISK-02-01:** Enlarging `tubehouse-dream`'s core shifts room adjacencies, so existing `openings`
  entries may lose their shared wall and raise `opening_no_wall`. Mitigation: the core layout in
  TASK-02-07 deliberately keeps `hall` adjacent to both `stair` (shared wall at `x = 1900`, full
  `y` overlap) and `elevator` (shared wall at `x = 3000`), and keeps `hall` spanning the full core depth
  so front and rear rooms still meet it. Re-compile after each storey edit rather than all five at once.
- **RISK-02-02:** Redefining `Tread.z` as the top face silently changes any consumer reading it.
  Mitigation: the only consumers are `build_scene.build_floors_and_stairs` (updated here) and
  `plan2d`, which uses only `x/y/w/d`. Compiled JSON in `output/` is gitignored and regenerable.
- **RISK-02-03:** The relocated light well is 2.3 m² rather than 5.0 m², weakening the design's defining
  daylight feature. Mitigation: this is the accepted cost of ASM-003; record it in `activeContext.md`
  when the phase closes so the trade-off is visible to the design's owner.

---

### PHASE-03 - Openings, Furniture Rotation, and a Validation Registry

**Goal**
Let specs position openings along a wall, reject overlapping ones, remove the latent world-origin
rotation bug from the furniture path, and enforce the design rules the skill documentation already
promises.

**Tasks**
- [ ] TASK-03-01: Add `severity: str = "error"` to the `SpecError` dataclass in
      `src/homedesign/errors.py` and include it in `to_dict()`. Existing call sites keep the default.
- [ ] TASK-03-02: Add `offset_mm` (`{"type": "number", "minimum": 0}`) and `align`
      (`{"type": "string", "enum": ["center", "start", "end"], "default": "center"}`) to the opening
      object in `spec/homespec.schema.json`.
- [ ] TASK-03-03: Implement S3's offset resolution in `compiler._place_openings`, replacing the
      hardcoded `offset = (span - width) / 2`, and emit `opening_out_of_wall` when the resolved opening
      leaves the wall.
- [ ] TASK-03-04: Create `src/homedesign/checks.py` with a rule registry: a module-level list of
      `(code, callable)` pairs, each callable taking a `CompiledModel` and returning `list[SpecError]`.
      Implement the rules listed under Function Signatures below.
- [ ] TASK-03-05: Rewrite `validate.validate_compiled` to run the registry and concatenate results,
      preserving the two existing checks (`stairwell_too_narrow`, `room_too_small`) as registry entries.
      Replace the `missing_stair_continuity` check with the registry's `shaft_stacking` rule, which is
      strictly more accurate.
- [ ] TASK-03-06: Sort `spec["storeys"]` by `level` at the top of `compile_spec` before accumulating
      `base_z`, and add a `storeys_out_of_order` rule that reports (as a warning) when the authored
      order differed from the sorted order. This removes the current silent dependence on list order.
- [ ] TASK-03-07: Split error output by severity in `src/homedesign/__main__.py`: errors go to stderr
      and force exit code 1; warnings go to stderr prefixed `warning:` and do not affect the exit code.
      Add a global `--json` flag that emits `{"errors": [...], "warnings": [...]}` to stdout instead,
      using `SpecError.to_dict()`.
- [ ] TASK-03-08: Fix the furniture rotation mechanism. Add a `_Placer` helper to
      `src/homedesign/blender/procedural_furniture.py` holding `(pivot_x, pivot_y, angle_rad)` with a
      `.box(...)` method that calls `geom.make_hinged_box` when `angle_rad != 0` and `geom.make_box`
      otherwise. Change every `_build_*` function to take the placer and call `place.box(...)` instead
      of `make_box(...)`. Delete the `obj.rotation_euler` branch in `build_item` entirely.
- [ ] TASK-03-09: Make `placement._plan_bedroom` emit `rot_deg = 90` for a bed in a shallow room instead
      of swapping `bed_w`/`bed_d`, and account for the rotated footprint in the fit check. This gives the
      rotation mechanism a real user and a pure-Python test.

**File Changes**
- `src/homedesign/errors.py` (modify): add the `severity` field and include it in `to_dict()`.
- `spec/homespec.schema.json` (modify): add `offset_mm` and `align` to openings only.
- `src/homedesign/compiler.py` (modify): S3 offset resolution and `opening_out_of_wall` in
  `_place_openings`; storey sort in `compile_spec`. Leave wall derivation untouched.
- `src/homedesign/checks.py` (create): the rule registry and every rule function.
- `src/homedesign/validate.py` (modify): `validate_compiled` delegates to the registry;
  `validate_schema` unchanged.
- `src/homedesign/__main__.py` (modify): severity-aware printing, `--json` flag. Leave the subcommand
  structure alone.
- `src/homedesign/blender/procedural_furniture.py` (modify): `_Placer`, threaded through all eight
  `_build_*` builders and `_default_block`; remove `obj.rotation_euler`.
- `src/homedesign/placement.py` (modify): `_plan_bedroom` rotation. Leave the other planners alone.
- `tests/test_checks.py` (create), `tests/test_openings.py` (create): the Test Specs below.
- `tests/test_placement.py` (modify): add the shallow-bedroom rotation case.

**Function Signatures**
- `resolve_opening_offset(span_mm: float, width_mm: float, align: str, offset_mm: float | None) -> float`
  — the opening's distance from the wall segment's start, per S3.
- `check_door_reachability(model: CompiledModel) -> list[SpecError]` — `room_unreachable` for every room
  not connected by a chain of `door` openings to an exterior door (on level 0) or to a `stairwell` /
  `elevator` room (on upper levels); `no_entrance` when level 0 has no exterior door at all.
- `check_habitable_daylight(model: CompiledModel) -> list[SpecError]` — `room_no_daylight` for every
  room of type `bedroom`, `living`, `kitchen`, `dining` or `office` with no `window` opening on any wall
  touching it.
- `check_room_support(model: CompiledModel) -> list[SpecError]` — `room_unsupported` for every room above
  the lowest level whose footprint is less than 80% covered by the union of the rooms on the level below.
- `check_shaft_stacking(model: CompiledModel) -> list[SpecError]` — `shaft_misaligned` when a
  `stairwell` or `elevator` room id appears on two levels with rectangles differing by more than 1 mm;
  `shaft_discontinuous` when a storey with generated stairs has no matching shaft on the storey above.
- `check_walls_within_plot(model: CompiledModel) -> list[SpecError]` — `wall_outside_plot` with
  `severity="warning"` for every wall segment extending beyond the plot rectangle.
- `check_storey_order(spec_levels: list[int]) -> list[SpecError]` — `storeys_out_of_order`
  (`severity="warning"`) when the authored levels are not already ascending.

**Test Specs**
- `resolve_opening_offset(3000, 900, "center", None)` → `1050.0`.
- `resolve_opening_offset(3000, 900, "start", None)` → `0.0`.
- `resolve_opening_offset(3000, 900, "end", None)` → `2100.0`.
- `resolve_opening_offset(3000, 900, "center", 250)` → `250.0` (explicit offset wins over align).
- A spec placing a 3000 mm door at `offset_mm: 500` and a 1000 mm window at `offset_mm: 1500`,
  `sill_mm: 1800`, `head_mm: 2100` on the same wall → `SpecValidationError` containing
  `opening_overlap`. (This is the exact real defect in today's `tubehouse-dream` level 0.)
- The same pair with the window moved to `offset_mm: 3600` → compiles with no error.
- A door at `offset_mm: 500` (`head_mm: 2100`) and a window at `offset_mm: 1500`, `sill_mm: 2100`,
  `head_mm: 2400` → compiles: they overlap in plan but only touch in elevation, and the 1 mm slack
  permits it.
- An opening with `offset_mm: 3500` and `width_mm: 900` on a 3000 mm wall → `opening_out_of_wall`.
- A two-storey spec whose level-1 `bedroom` has no door in `openings` → `room_unreachable` naming that
  room.
- `spec/examples/demo-3br-2storey.json` after PHASE-02 → `check_door_reachability` returns `[]`.
- A spec whose level-1 room sits entirely over an untiled void on level 0 → `room_unsupported`.
- A spec whose `stair` room is `{x:0,y:0,w:1900,d:3200}` on level 0 and `{x:100,y:0,w:1900,d:3200}` on
  level 1 → `shaft_misaligned`.
- `check_walls_within_plot` on `spec/tubehouse-dream.json` → a non-empty list where **every** entry has
  `severity == "warning"`.
- A spec with `storeys` authored as levels `[1, 0]` → compiles successfully with `base_z` of `0` for
  level 0 and the level-0 height for level 1, plus one `storeys_out_of_order` warning.
- `placement.plan_room("bedroom", 4.0, 2.2)` → the returned bed item has `rot_deg == 90` and
  `w == 1.6`, `d == 2.0` (dimensions kept semantic; orientation carried by the angle).
- `PYTHONPATH=src python -m homedesign compile spec/tubehouse-dream.json --json` → valid JSON on stdout
  with `errors` and `warnings` keys.

**Dependencies**
- PHASE-02 (the specs must already compile with real stairs before reachability and stacking rules can
  be expected to pass).

**Exit Criteria**
- [ ] `PYTHONPATH=src python -m homedesign compile spec/tubehouse-dream.json` exits 0 with only
      `wall_outside_plot` warnings.
- [ ] The `tubehouse-dream` level-0 garage door and transom window no longer share a wall footprint —
      verified by a script asserting no two openings on one wall satisfy S3's overlap predicate.
- [ ] `grep -n "rotation_euler" src/homedesign/blender/procedural_furniture.py` returns no matches.
- [ ] All four specs pass `check_door_reachability` with an empty result.
- [ ] `python -m pytest tests -q` passes with the new test modules.

**Phase Risks**
- **RISK-03-01:** The reachability and daylight rules may fail existing specs that were authored without
  them, blocking the build. Mitigation: run the rules in report-only mode first
  (`python -m homedesign compile <spec> --json`), fix the specs, then wire the rules into the failing
  path. Daylight failures on `storage`, `bathroom`, `hall`, `garage`, `stairwell` and `elevator` are
  excluded by design — only the five habitable types are checked.
- **RISK-03-02:** Threading `_Placer` through eight builders is mechanical but touches every furniture
  shape; a missed `make_box` call leaves that piece unrotated while its siblings rotate, splitting a
  single item apart. Mitigation: after the refactor, `grep -n "make_box" src/homedesign/blender/procedural_furniture.py`
  must return zero matches outside the `_Placer` class itself.

---

### PHASE-04 - Render Economics

**Goal**
Cut the preview render from minutes to seconds, separate rendering from scene building so a re-render is
cheap, and make long final renders resumable, observable, and able to survive a closed terminal.

**Tasks**
- [ ] TASK-04-01: Add an engine-selection helper to `blender/build_scene.py` that sets the render engine
      by trying identifiers in order and falling back: for EEVEE try `BLENDER_EEVEE_NEXT` then
      `BLENDER_EEVEE`; for Cycles use `CYCLES`. Raise a clear `RuntimeError` naming the attempted
      identifiers if none is accepted (CON-001).
- [ ] TASK-04-02: Redefine the render profiles: `PREVIEW = {"engine": "EEVEE", "samples": 32,
      "res": (960, 540)}` and `FINAL = {"engine": "CYCLES", "samples": 512, "res": (1920, 1080)}`
      (ASM-005). Apply samples to `scene.eevee.taa_render_samples` for EEVEE and `scene.cycles.samples`
      for Cycles. Keep the `Filmic` view transform and its existing fallback for both engines.
- [ ] TASK-04-03: Replace the silent `try: scene.cycles.device = "GPU"` block with
      `_configure_cycles_device()`, which sets
      `bpy.context.preferences.addons["cycles"].preferences.compute_device_type` by trying `OPTIX`,
      `CUDA`, `HIP`, `ONEAPI`, `METAL` in order, enables every returned device, sets
      `scene.cycles.device = "GPU"` only when at least one device was enabled, and **prints** the
      outcome (`cycles device: CPU (no GPU backend available)` or `cycles device: GPU via CUDA (1
      device)`). No bare excepts.
- [ ] TASK-04-04: Enable Cycles adaptive sampling (`scene.cycles.use_adaptive_sampling = True`,
      `adaptive_threshold = 0.01`) and `scene.render.use_persistent_data = True` for the final profile.
- [ ] TASK-04-05: Add `--views` (comma-separated view names, default all) and `--skip-existing` flags to
      `blender/build_scene.py`'s argument parser, and honour them in `render()`: skip any view whose
      target PNG already exists when `--skip-existing` is set.
- [ ] TASK-04-06: Add a `--reuse-blend` flag to `build_scene.py` that, when the target `.blend` exists,
      opens it with `bpy.ops.wm.open_mainfile` and skips all geometry construction, going straight to
      rendering.
- [ ] TASK-04-07: Change `orchestrator.build_scene` to stream Blender's output line by line to stderr
      via `subprocess.Popen` with `stdout=PIPE, stderr=STDOUT`, instead of `subprocess.run(capture_output=True)`.
      Preserve the non-zero-exit `RuntimeError`, including the last 50 streamed lines in its message.
- [ ] TASK-04-08: Add `orchestrator.render_only(model_path, out_dir, profile, views, skip_existing,
      detach, log_path)`. When `detach` is true, launch Blender with `subprocess.Popen`, redirect
      stdout/stderr to `log_path`, use `creationflags=subprocess.DETACHED_PROCESS | subprocess.CREATE_NEW_PROCESS_GROUP`
      on Windows and `start_new_session=True` elsewhere, and return the PID immediately without waiting.
- [ ] TASK-04-09: Add a `render` subcommand to `src/homedesign/__main__.py`:
      `python -m homedesign render <spec.json> [--view NAME]... [--profile preview|final]
      [--skip-existing] [--detach]`. It compiles the spec, writes the model JSON, then calls
      `render_only`. With `--detach` it prints the PID and the log path and exits 0 immediately.
- [ ] TASK-04-10: Create `output/logs/` on demand in `orchestrator` and add `output/` is already
      gitignored, so no `.gitignore` change is needed — verify this rather than assuming.

**File Changes**
- `src/homedesign/blender/build_scene.py` (modify): engine helper, new profile dicts,
  `_configure_cycles_device`, adaptive sampling, `--views` / `--skip-existing` / `--reuse-blend` flags,
  and the `render()` changes. Leave all geometry-building functions untouched in this phase.
- `src/homedesign/orchestrator.py` (modify): streamed output, `render_only`, detached launch. Keep
  `find_blender` as-is except for replacing the hardcoded `C:/Users/tukum/...` candidate with a
  `BLENDER_CMD` environment lookup first (already present) plus generic Windows, macOS and Linux
  candidate paths.
- `src/homedesign/__main__.py` (modify): add the `render` subcommand and its flags.
- `tests/test_orchestrator.py` (create): the pure-Python parts — argument assembly and detach-mode
  command construction, exercised with a stub executable.
- `.claude/skills/homedesign/SKILL.md` (modify): document the `render` subcommand, the EEVEE preview /
  Cycles final split, and the detached long-render workflow.

**Function Signatures**
- `_set_engine(scene: "bpy.types.Scene", family: str) -> str` — sets and returns the accepted engine
  identifier for `family` in `{"EEVEE", "CYCLES"}`; raises `RuntimeError` when none is accepted.
- `_configure_cycles_device() -> str` — configures Cycles compute devices and returns a human-readable
  description of what was selected, e.g. `"CPU (no GPU backend available)"`.
- `render_only(model_path: Path, out_dir: Path, profile: str, views: list[str] | None, skip_existing: bool, detach: bool, log_path: Path | None) -> list[Path] | int`
  — the rendered PNG paths when running synchronously, or the launched process PID when `detach` is true.

**Test Specs**
- `PYTHONPATH=src python -m homedesign build spec/examples/tubehouse-mini.json` → completes and prints
  `blender build: <N>s` where `N` is **under 120** (today this is a Cycles preview taking materially
  longer; EEVEE at 960x540 should be a few seconds of render plus scene build).
- `PYTHONPATH=src python -m homedesign render spec/examples/tubehouse-mini.json --view interior` →
  writes only `output/png/tubehouse-mini_interior.png`, leaving `output/png/tubehouse-mini_exterior.png`
  untouched (compare file modification times before and after).
- Re-running the same command with `--skip-existing` → prints a skip notice and writes no file
  (modification time unchanged).
- `PYTHONPATH=src python -m homedesign render spec/examples/tubehouse-mini.json --profile final --detach`
  → exits 0 within 5 seconds, prints a PID and a path under `output/logs/`, and the log file grows
  while the render proceeds.
- `_configure_cycles_device()` on the target machine → returns a string containing `CPU`, and the
  message is printed to stdout during a `--profile final` render.
- Stub-executable test: `orchestrator.build_scene` with `BLENDER_CMD` pointing at a script that writes
  three lines to stdout and exits 0 → all three lines appear on stderr.
- Stub-executable test: the same stub exiting 1 → `RuntimeError` whose message contains the stub's
  output lines.

**Dependencies**
- PHASE-01. Independent of PHASE-02 and PHASE-03; may be executed in parallel with them if desired.

**Exit Criteria**
- [ ] A preview build of `spec/examples/tubehouse-mini.json` completes in under 120 seconds wall clock.
- [ ] `python -m homedesign render <spec> --view <name>` renders exactly one view and does not rebuild
      geometry when `--reuse-blend` is in effect.
- [ ] `--detach` returns control immediately and the render continues after the launching shell exits.
- [ ] The Cycles device selection prints an explicit line naming CPU or GPU; no bare `except` remains in
      the render path (`grep -n "except Exception" src/homedesign/blender/build_scene.py` returns no
      matches in `render`/device code).
- [ ] `python -m pytest tests -q` passes.

**Phase Risks**
- **RISK-04-01:** EEVEE handles the `transmission` glass material and the boolean-cut wall openings
  differently from Cycles; previews may look materially different from finals. Mitigation: accept it —
  previews exist to check layout, not lighting. Document the difference in the skill file so the
  visual self-correction loop does not chase EEVEE artifacts.
- **RISK-04-02:** Detached processes on Windows are not tracked by the launching shell, so a runaway
  render must be killed manually. Mitigation: print the PID and the exact kill command
  (`taskkill /PID <pid> /F` on Windows, `kill <pid>` elsewhere) alongside the log path.

---

### PHASE-05 - Camera Framing

**Goal**
Replace the hand-tuned camera multipliers with the analytic bounding-box fit in S4, so every exterior
render contains the whole building and every room render contains the furniture actually placed in it.

**Tasks**
- [ ] TASK-05-01: Create `src/homedesign/camera_fit.py` implementing S4 as pure math over plain tuples —
      no `bpy` import, so it is unit-testable.
- [ ] TASK-05-02: Add a helper that computes the building's world bounding box in metres from a
      `CompiledModel` dict (plot footprint by total storey height), excluding the ground plane and roof
      overhang.
- [ ] TASK-05-03: Add a helper that computes a room's subject bounding box: the room's interior volume
      from the storey floor to `min(storey_height, 2.4)` metres, unioned with the world-space footprint
      of every item returned by `placement.plan_room` for that room.
- [ ] TASK-05-04: Rewrite `_build_exterior_front_camera` to use the fit: direction from the street
      (azimuth along `+y`, elevation `-15°`), lens left at Blender's 50 mm default. Delete the
      `plot_w * 3.0 + total_height * 1.2 + 6` distance heuristic and the `0.3` / `0.55` offset factors
      along with their explanatory comments, which no longer apply.
- [ ] TASK-05-05: Rewrite `_build_exterior_aerial_camera` to use the fit at azimuth 45°, elevation
      `-40°`.
- [ ] TASK-05-06: Rewrite `_build_room_camera` to place the camera at the near end of the room's long
      axis at 1.5 m eye height, aim `-5°` downward along that axis, and set the **lens** (not the
      distance, which is constrained by the walls) to the widest value in `[12, 15, 18, 20, 24]` that
      still fits the subject box per S4. This keeps the camera inside the room while guaranteeing the
      furniture is in frame.
- [ ] TASK-05-07: Set `cam_data.sensor_fit = 'HORIZONTAL'` and `cam_data.sensor_width = 36.0` on every
      camera so the S4 field-of-view math matches Blender's actual projection.

**File Changes**
- `src/homedesign/camera_fit.py` (create): S4 math plus the two bounding-box helpers.
- `src/homedesign/blender/build_scene.py` (modify): rewrite the three `_build_*_camera` functions to
  call into `camera_fit`; set `sensor_fit`/`sensor_width`. Leave `add_cameras`' view dispatch,
  `_point_at`, and every geometry function unchanged.
- `tests/test_camera_fit.py` (create): the Test Specs below.

**Function Signatures**
- `fit_distance(corners: list[tuple[float, float, float]], centre: tuple[float, float, float], forward: tuple[float, float, float], right: tuple[float, float, float], up: tuple[float, float, float], lens_mm: float, res_x: int, res_y: int, margin: float = 1.08) -> float`
  — the camera distance from `centre` along `-forward` that fits every corner in frame, per S4, clamped
  to a minimum of 1.0.
- `basis_from_direction(forward: tuple[float, float, float]) -> tuple[tuple[float, float, float], tuple[float, float, float]]`
  — the orthonormal `(right, up)` pair for a given forward vector, using world `+Z` as the up reference.
- `building_bbox(model: dict) -> tuple[tuple[float, float, float], tuple[float, float, float]]`
  — `(min_corner, max_corner)` of the building in metres.
- `room_subject_bbox(storey: dict, room: dict) -> tuple[tuple[float, float, float], tuple[float, float, float]]`
  — `(min_corner, max_corner)` in metres of the room interior unioned with its furniture.
- `corners_of(bbox: tuple[tuple[float, float, float], tuple[float, float, float]]) -> list[tuple[float, float, float]]`
  — the 8 corners of an axis-aligned box.

**Test Specs**
- `fit_distance` for a 2x2x2 m cube centred at the origin, `forward = (0, 1, 0)`, `lens_mm = 50`,
  `res_x = 1920`, `res_y = 1080`, `margin = 1.0` → the horizontal half-FOV is
  `atan(36/(2*50)) = 0.34844 rad`, so the required distance is `1/tan(0.34844) + 1 = 3.7735`; assert the
  result is `3.7735` within 1e-3.
- The same call with `margin = 1.08` → `4.0754` within 1e-3.
- The same call with `res_y = 1920` (square frame, so vertical becomes binding) → strictly greater than
  the 1080 result.
- A degenerate zero-size box → returns exactly `1.0` (the clamp).
- `building_bbox` for `tubehouse-dream` → `min == (0.0, 0.0, 0.0)` and
  `max == (4.0, 25.0, 17.6)` (4000 mm x 25000 mm; heights 4000 + 4 x 3400 = 17600 mm), within 1e-6.
- `room_subject_bbox` for `tubehouse-mini`'s `living` room → its `x`/`y` extent is at least as large as
  the room rectangle and its `z` maximum is `storey.base_z / 1000 + 2.4`.
- `basis_from_direction((0, 1, 0))` → `right` and `up` are unit vectors, mutually perpendicular, and
  each perpendicular to `forward` (all dot products within 1e-9 of 0).
- **Visual check after rendering:** in `output/png/tubehouse-dream_exterior_front.png` the topmost and
  bottommost non-background pixel rows are strictly inside the image bounds (the building is not
  clipped). Assert programmatically by loading the PNG with Pillow and checking that row 0 and the last
  row contain only sky/ground colours, not wall colour.

**Dependencies**
- PHASE-04 (so the verification renders are fast enough to iterate on).

**Exit Criteria**
- [ ] `PYTHONPATH=src python -m homedesign render spec/tubehouse-dream.json --view exterior_front`
      produces an image in which the building is fully within frame (the Pillow check above passes).
- [ ] The same for `--view exterior_aerial`.
- [ ] A room view of `tubehouse-dream`'s `living_f2` shows the dining table and chairs that
      `placement._plan_living` places — verified by confirming the camera's subject box includes the
      furniture footprint and the camera is positioned outside it along the view axis.
- [ ] `grep -n "plot_w \* 3.0" src/homedesign/blender/build_scene.py` returns no matches.
- [ ] `python -m pytest tests -q` passes with `tests/test_camera_fit.py`.

**Phase Risks**
- **RISK-05-01:** For `room` views the camera must stay inside the room, so distance is not free — a
  small room may not fit its own furniture at any sane lens. Mitigation: TASK-05-06 varies the lens
  rather than the distance and accepts the widest option (12 mm) as a floor; a room that still does not
  fit is rendered anyway rather than failing the build.
- **RISK-05-02:** Blender's `sensor_fit = 'AUTO'` maps `sensor_width` to whichever image dimension is
  larger, which would silently break the S4 math for portrait resolutions. Mitigation: TASK-05-07 pins
  `sensor_fit = 'HORIZONTAL'` on every camera.

---

### PHASE-06 - Drawing, Document, and Documentation Quality

**Goal**
Turn the 2D output into a readable architectural drawing, shrink and correct the PDF brief, add the
schedules an architect expects, and bring the repo's documentation back in line with the code.

**Tasks**
- [ ] TASK-06-01: Add an optional `name` string to the room object in `spec/homespec.schema.json` and to
      the `Room` dataclass in `src/homedesign/model.py` (default `None`), round-tripped in
      `CompiledModel.from_dict`. Plan labels and the PDF schedule use `room.name or room.id`.
- [ ] TASK-06-02: In `src/homedesign/plan2d.py`, emit the SVG root with **only** a `viewBox` and
      `preserveAspectRatio="xMidYMid meet"` — remove the fixed `width` and `height` attributes. This is
      what makes the PDF's per-storey plan pages fit one A3 sheet.
- [ ] TASK-06-03: Add door swing arcs to the SVG (a quarter-circle path of radius `width_mm` from the
      hinge jamb, plus the leaf line) and a three-line window symbol, replacing the current flat coloured
      rectangles. Keep the existing colour coding (`#c0392b` doors, `#3a7bd5` windows).
- [ ] TASK-06-04: Add a north arrow (pointing toward `-y`, i.e. up-screen, per the repo's cardinal
      convention), a graphic scale bar in metres, and a title-block rectangle in the lower-right of each
      SVG carrying the design name, storey name, plot dimensions, and a `1:100 @ A3` scale note.
- [ ] TASK-06-05: Fix the DXF vertical mirroring: add a `_dxf_pt(x_mm, y_mm, plot_depth_mm)` helper
      returning `(x_mm, plot_depth_mm - y_mm)` and route every DXF coordinate through it, so the CAD
      output matches the SVG orientation. Centre the room labels with
      `set_placement((cx, cy), align="MIDDLE_CENTER")`.
- [ ] TASK-06-06: Add door swing arcs (`msp.add_arc`) and window symbols to the DXF on their existing
      `DOORS` / `WINDOWS` layers, mirroring the SVG symbols.
- [ ] TASK-06-07: In `src/homedesign/pdf.py`, reference gallery images by relative path
      (`../png/<file>.png`) instead of base64 data URIs, and downscale each to 1400 px wide with Pillow
      into `output/pdf/img/` first (ASM-007). Keep the cover hero as a data URI so the cover survives
      being moved. Add an `--embed-images` CLI flag that restores full data-URI embedding for a
      self-contained HTML.
- [ ] TASK-06-08: Add two new PDF sections: a **door and window schedule** (one row per opening: id,
      storey, type, width, sill, head, the two rooms it connects) and a **quantity take-off** (per
      storey: gross floor area in m², exterior wall length in m, partition wall length in m, door count,
      window count; plus a whole-building total row).
- [ ] TASK-06-09: Add a page footer with the design name and a page number to `PAGE_CSS` using
      `@page { @bottom-right { content: counter(page) } }`, falling back gracefully if the headless
      browser ignores it.
- [ ] TASK-06-10: Create a git-tracked `designs/` directory with a `README.md` explaining that
      user-authored specs live there (ASM-006), and move `spec/tubehouse-dream.json` to
      `designs/tubehouse-dream.json`. Update `.claude/skills/homedesign/SKILL.md` to reference
      `designs/<slug>.json` everywhere it currently says `output/specs/<slug>.json`. Leave
      `spec/examples/` and `spec/homespec.schema.json` where they are.
- [ ] TASK-06-11: Rewrite `AGENTS.md`: remove the FreeCAD scope paragraph, the `run.sh` reference, the
      `freecad-mcp-guide.md` reference and the `spec/floorplan-spec.json` reference; correct the
      verification section to the pytest and ruff commands from PHASE-01; document the `designs/`
      directory and the `render` subcommand.
- [ ] TASK-06-12: Move `plans/PROGRESS.md`, `docs/HOW_TO_RUN.txt` and `docs/plan-floor-1.md` into
      `docs/archive/` with a one-line header in each stating it describes the retired FreeCAD pipeline.
      Split `docs/lessons-learned.md`: keep the Blender lesson in place, move lessons 1-6 to
      `docs/archive/freecad-lessons-learned.md`.
- [ ] TASK-06-13: Replace `.agents/skills/homedesign/SKILL.md` (a stale divergent copy) with a generated
      duplicate: add `scripts/sync_skill.py` that copies `.claude/skills/homedesign/SKILL.md` to
      `.agents/skills/homedesign/SKILL.md` and fails with a non-zero exit if they differ, then add that
      check to the CI workflow from PHASE-01.
- [ ] TASK-06-14: Delete the retired FreeCAD-era artifact directories `output/fcstd/`, `output/obj/`,
      `output/ifc/`, `output/stl/`, `output/test.ifc` and `output/architect_package_manifest.json`. These
      are gitignored, so this is a local-workspace cleanup with no repository effect.

**File Changes**
- `spec/homespec.schema.json` (modify): add the optional room `name`.
- `src/homedesign/model.py` (modify): `Room.name: str | None = None` plus `from_dict` handling.
- `src/homedesign/plan2d.py` (modify): SVG root attributes, door/window symbols, north arrow, scale bar,
  title block, `_dxf_pt` and its use throughout `_render_dxf`, DXF arcs and centred text.
- `src/homedesign/pdf.py` (modify): relative image paths and Pillow downscaling, `--embed-images`
  support, the two new schedule sections, page footer CSS. Leave `build_room_schedule`'s existing
  behaviour intact and add the new builders alongside it.
- `src/homedesign/__main__.py` (modify): add `--embed-images` to the `pdf` subcommand.
- `designs/README.md` (create), `designs/tubehouse-dream.json` (create — moved from `spec/`),
  `spec/tubehouse-dream.json` (delete).
- `scripts/sync_skill.py` (create): copy-or-verify the skill file.
- `.github/workflows/ci.yml` (modify): add a `python scripts/sync_skill.py --check` step.
- `AGENTS.md` (modify): full rewrite per TASK-06-11.
- `docs/archive/` (create) and the file moves in TASK-06-12.
- `.claude/skills/homedesign/SKILL.md` (modify): `designs/` paths, the new PDF sections, the room `name`
  field.
- `tests/test_plan2d.py` (modify): add symbol and DXF-orientation assertions.
- `tests/test_pdf.py` (modify): add schedule and take-off assertions.

**Function Signatures**
- `_dxf_pt(x_mm: float, y_mm: float, plot_depth_mm: float) -> tuple[float, float]` — the model point
  converted to DXF/CAD coordinates with the y axis flipped.
- `build_opening_schedule(model: CompiledModel) -> list[dict]` — one dict per opening with keys `id`,
  `storey`, `type`, `width_mm`, `sill_mm`, `head_mm`, `rooms` (a two-element list of room labels).
- `build_takeoff(model: CompiledModel) -> list[dict]` — one dict per storey with keys `level`, `name`,
  `gfa_m2`, `exterior_wall_m`, `partition_wall_m`, `door_count`, `window_count`, plus a final dict with
  `level = None` holding whole-building totals.
- `downscale_png(src: Path, dst: Path, max_width_px: int = 1400) -> Path` — the written path; returns
  `src` unchanged and warns on stderr when Pillow is unavailable.

**Test Specs**
- `plan2d._render_svg(model, storey)` output → contains `viewBox=` and does **not** contain
  `width="` or `height="` on the root `<svg>` element.
- The same output → contains at least one `<path` element with an `A` (arc) command for a storey that
  has at least one door.
- `_dxf_pt(0, 0, 25000)` → `(0, 25000)`. `_dxf_pt(4000, 25000, 25000)` → `(4000, 0)`.
- A DXF written for `tubehouse-mini` storey 0 → the wall polyline nearest the street (model `y = 0`)
  has the **largest** DXF y coordinate, confirming the flip.
- `build_opening_schedule(compile_spec(tubehouse-mini))` → length equals the total opening count across
  all storeys; every entry's `rooms` list has exactly 2 elements.
- `build_takeoff(compile_spec(tubehouse-mini))` → the last entry has `level is None`; its `gfa_m2`
  equals the sum of the per-storey `gfa_m2` values within 0.1.
- `render_brief_html(...)` with default flags → contains `src="../png/` and does **not** contain
  `data:image/png;base64` except for the single cover-hero occurrence.
- `render_brief_html(..., embed_images=True)` → contains one `data:image/png;base64` occurrence per
  gallery image plus the cover.
- `python scripts/sync_skill.py --check` with the two skill files identical → exit 0; with them
  differing → exit 1 and a diff summary on stderr.
- `output/pdf/tubehouse-dream-brief.html` after a rebuild → file size under **200 KB** (today: 27 MB).

**Dependencies**
- PHASE-03 (the room `name` field and the schedules describe the corrected model) and PHASE-05 (the
  gallery images the PDF embeds must be correctly framed first).

**Exit Criteria**
- [ ] `PYTHONPATH=src python -m homedesign pdf designs/tubehouse-dream.json` produces a PDF whose page
      count equals `2 (cover + narrative) + 1 (schedule) + 5 (one per storey) + ceil(views/2) + 1
      (requirements) + 1 (openings) + 1 (take-off) + 1 (appendix)` — i.e. **exactly one page per
      storey**, verified by inspecting the PDF page count.
- [ ] `output/pdf/tubehouse-dream-brief.html` is under 200 KB.
- [ ] Each generated SVG contains a north arrow, a scale bar, a title block and door swing arcs.
- [ ] `python scripts/sync_skill.py --check` exits 0 and runs in CI.
- [ ] `grep -rn "run.sh\|freecad-mcp-guide\|floorplan-spec.json" AGENTS.md` returns no matches.
- [ ] `grep -rn "output/specs" .claude/skills/homedesign/SKILL.md` returns no matches.
- [ ] `python -m pytest tests -q` passes.

**Phase Risks**
- **RISK-06-01:** Removing the SVG's `width`/`height` attributes changes how the file renders when
  opened standalone in a browser (it will scale to the container rather than to a fixed pixel size).
  Mitigation: this is the intended behaviour and is what fixes A3 pagination; the `viewBox` preserves
  the aspect ratio and true dimensions, and the added scale bar makes the drawing self-describing.
- **RISK-06-02:** Chrome's headless `--print-to-pdf` may not resolve relative image paths depending on
  version and sandboxing. Mitigation: verify immediately after TASK-06-07; if images are missing from
  the PDF, fall back to data URIs for the gallery but keep the Pillow downscaling, which still cuts the
  HTML by roughly an order of magnitude.
- **RISK-06-03:** Moving `spec/tubehouse-dream.json` to `designs/` breaks any path a person has
  memorised. Mitigation: the move is a single commit; update every in-repo reference in the same commit
  (`grep -rn "spec/tubehouse-dream.json" --include='*.md' --include='*.py' .`).

## Gotchas

- **Millimetres everywhere on the pure side, metres everywhere on the Blender side.** The conversion
  happens exactly once, at the boundary, by dividing by 1000. Stair goings, floor voids, opening offsets
  and bounding boxes all cross that boundary in this plan — a missed division is a 1000x error that will
  look like the model vanished.
- **`north = min-y`, `south = max-y`, `west = min-x`, `east = max-x`.** This is the opposite of the
  intuitive "north is up on a map means larger y". It is used consistently by `_wall_side`,
  `_place_relative` and the opening `side` hint; keep it.
- **SVG y grows downward, DXF/CAD y grows upward.** This is exactly why the two outputs are currently
  mirrored. Fix it in one helper (TASK-06-05), not per call site.
- **Every mesh in `blender/` bakes its world position into its vertices and leaves the object origin at
  `(0, 0, 0)`.** Therefore `obj.rotation_euler` and `obj.location` pivot around the world origin, not
  the object. Any rotation must be baked into the vertices about an explicit pivot — that is what
  `geom.make_hinged_box` exists for. This bug has already shipped once (32 door leaves scattered across
  the scene) and PHASE-03 removes the last remaining path to it.
- **A flight of `n` risers has `n - 1` treads.** The final riser lands on the floor above. Off-by-one
  here produces a stair that either overshoots the ceiling or leaves a step-height gap.
- **`Tread.z` changes meaning in PHASE-02** from "bottom of the tread box" to "top walking surface".
  Any code reading it must be updated in the same change; `plan2d` only reads `x/y/w/d` and is safe.
- **Blender 4.1's EEVEE identifier is `BLENDER_EEVEE`**, renamed to `BLENDER_EEVEE_NEXT` in 4.2+.
  Setting `scene.render.engine` to an unknown identifier raises `TypeError`, not a silent no-op.
- **`scene.cycles.device = "GPU"` alone does nothing.** Device selection lives in
  `bpy.context.preferences.addons["cycles"].preferences`, and devices must be individually enabled.
- **Do not run a full `--final` gallery render as a verification step.** It takes ~11.3 hours on the
  target machine. Verify with previews and single-view final renders.
- **`output/` is gitignored.** Never store anything there that cannot be regenerated from a spec —
  which is precisely why user designs move to `designs/` in PHASE-06.
- **The compiler treats any room edge not exactly shared with another room as an exterior wall.** This
  is deliberate: it is how untiled light wells get walls. Do not "fix" it into an error.
- **Exterior walls are centred on the room edge**, so a 200 mm exterior wall extends 100 mm outside the
  plot rectangle. This is why 63 wall segments trip `check_walls_within_plot`, and why that rule is a
  warning rather than an error (ASM-004).

## Verification Strategy

- **TEST-001:** `python -m pip install -e ".[dev]" && python -m pytest tests -q` → all tests pass
  (44 at the end of PHASE-01, growing with each phase); exit code 0.
- **TEST-002:** `ruff check src tests` → `All checks passed!`; exit code 0.
- **TEST-003:** `PYTHONPATH=src python -m homedesign compile spec/examples/demo-3br-2storey.json &&
  PYTHONPATH=src python -m homedesign compile spec/examples/tubehouse-mini.json &&
  PYTHONPATH=src python -m homedesign compile spec/examples/courtyard-fixture.json &&
  PYTHONPATH=src python -m homedesign compile designs/tubehouse-dream.json` → all four exit 0.
- **TEST-004:** Minimum-going check after PHASE-02:
  ```
  python - <<'EOF'
  import json, pathlib
  m = json.loads(pathlib.Path("output/compiled/tubehouse-dream.model.json").read_text())
  goings = [min(t["w"], t["d"]) for s in m["storeys"] if s.get("stairs")
            for t in s["stairs"]["treads"]]
  print("min going mm:", min(goings))
  assert min(goings) >= 250, "stair going below the 250mm minimum"
  EOF
  ```
  → prints a value of at least 250 and exits 0. Before this plan it prints `57.0`.
- **TEST-005:** Opening-overlap check after PHASE-03:
  ```
  python - <<'EOF'
  import json, pathlib, itertools
  m = json.loads(pathlib.Path("output/compiled/tubehouse-dream.model.json").read_text())
  bad = []
  for s in m["storeys"]:
      by_wall = {}
      for o in s["openings"]:
          by_wall.setdefault(o["wall_id"], []).append(o)
      for wid, ops in by_wall.items():
          for a, b in itertools.combinations(ops, 2):
              plan = min(a["offset_mm"] + a["width_mm"], b["offset_mm"] + b["width_mm"]) - max(a["offset_mm"], b["offset_mm"])
              elev = min(a["head_mm"], b["head_mm"]) - max(a["sill_mm"], b["sill_mm"])
              if plan > 1 and elev > 1:
                  bad.append((wid, a["id"], b["id"]))
  print("overlapping opening pairs:", bad)
  assert not bad
  EOF
  ```
  → prints an empty list and exits 0. Before this plan it reports `('F0_W019', 'F0_O002', 'F0_O008')`.
- **TEST-006:** Preview speed after PHASE-04:
  `time PYTHONPATH=src python -m homedesign build spec/examples/tubehouse-mini.json` → completes in under
  120 seconds wall clock.
- **TEST-007:** Single-view render after PHASE-04:
  `PYTHONPATH=src python -m homedesign render spec/examples/tubehouse-mini.json --view interior` → writes
  only `output/png/tubehouse-mini_interior.png`; `output/png/tubehouse-mini_exterior.png` keeps its
  previous modification time.
- **TEST-008:** Framing check after PHASE-05:
  ```
  python - <<'EOF'
  from PIL import Image
  im = Image.open("output/png/tubehouse-dream_exterior_front.png").convert("RGB")
  w, h = im.size
  top = [im.getpixel((x, 0)) for x in range(0, w, 20)]
  bot = [im.getpixel((x, h - 1)) for x in range(0, w, 20)]
  wallish = lambda p: p[0] > 200 and p[1] > 200 and p[2] > 200 and abs(p[0] - p[2]) < 12
  print("wall pixels on top row:", sum(map(wallish, top)), "bottom row:", sum(map(wallish, bot)))
  EOF
  ```
  → both counts are 0, meaning the building touches neither the top nor the bottom edge. Before this
  plan the building is clipped at both.
- **TEST-009:** PDF size and pagination after PHASE-06:
  `PYTHONPATH=src python -m homedesign pdf designs/tubehouse-dream.json && ls -l output/pdf/` → the
  `.html` is under 200 KB (today 27 MB); opening the `.pdf` shows exactly one page per storey in the
  plan section (today each storey spills onto two).
- **TEST-010:** Skill-file sync after PHASE-06: `python scripts/sync_skill.py --check` → exit 0.
- **MANUAL-001:** After PHASE-02, open `output/blend/tubehouse-dream.blend` in Blender and confirm
  visually that the staircase is a two-flight U-return with a landing, and that the floor slab above it
  has a matching hole.
- **MANUAL-002:** After PHASE-05, view all nine `tubehouse-dream` preview renders and confirm each
  contains its intended subject entirely within frame.
- **MANUAL-003:** After PHASE-06, open a generated DXF in a CAD viewer (LibreCAD, or
  https://sharecad.org) and confirm the plan is oriented the same way as the corresponding SVG, with the
  street frontage at the top.
- **OBS-001:** After PHASE-04, confirm that a `--profile final` render prints an explicit
  `cycles device: ...` line naming CPU or GPU, and that `--detach` writes a continuously growing log
  under `output/logs/`.

## Risks and Alternatives

- **RISK-001:** PHASE-02 changes the `tubehouse-dream` design itself — a deeper circulation core and a
  smaller light well — and the design belongs to a person, not the toolchain. Mitigation: the change is
  forced by physics (a 1100 x 1300 mm shaft cannot contain a 3.4 m rise), the layout in TASK-02-07
  preserves every existing adjacency and the light well's existence, and ASM-003 is written to be edited
  before hand-off if its owner prefers reducing the ground-storey height instead.
- **RISK-002:** PHASE-03's new validation rules may reject specs that previously compiled, which is the
  point but is still disruptive. Mitigation: `wall_outside_plot` and `storeys_out_of_order` ship as
  warnings; every error-severity rule is verified against all four repo specs before the phase closes.
- **RISK-003:** Six phases touching overlapping files invites merge pain if executed in parallel.
  Mitigation: the dependency column in `## Phase Summary` is authoritative; only PHASE-04 is genuinely
  independent of PHASE-02/03 and can run alongside them, and it touches a disjoint set of functions
  (render and orchestration, not geometry).
- **RISK-004:** No amount of tuning makes Cycles fast on this hardware, so `--final` galleries remain an
  overnight operation. Mitigation: PHASE-04 makes them resumable and detachable rather than faster —
  the goal is that an interrupted 11-hour run costs minutes, not hours.
- **ALT-001:** *Reject undersized stair shafts without building a stair generator.* Cheaper, and it would
  stop the tool lying — but it leaves every existing design without a stair, which is unacceptable for a
  five-storey house. Rejected in favour of doing both: PHASE-02 ships the generator and the rejection
  rule together.
- **ALT-002:** *Keep Cycles for previews and simply lower the sample count.* Rejected: at 24 samples the
  preview is already noisy and still minutes long, because Cycles' cost on this CPU is dominated by BVH
  construction and path tracing setup, not sample count. EEVEE changes the order of magnitude.
- **ALT-003:** *Adopt an existing BIM kernel (IfcOpenShell geometry, or FreeCAD's Arch workbench) instead
  of extending the bespoke compiler.* Rejected: the compiler is the best-tested component in the repo and
  its rectilinear constraint is what makes the output deterministic; this project already removed FreeCAD
  once, deliberately.
- **ALT-004:** *Fix camera framing by hand-tuning the existing multipliers further.* Rejected: the
  current constants already carry three paragraphs of comments explaining previous tuning rounds, which
  is evidence that the method — not the numbers — is wrong.

## Suggested Next Step

Execute PHASE-01. It is self-contained, touches no geometry, and converts the test suite from "fails on
checkout" into the trustworthy signal that every subsequent phase depends on. Verify its exit criteria
(44 tests passing, `ruff check` clean, the Blender bootstrap intact) before starting PHASE-02.
