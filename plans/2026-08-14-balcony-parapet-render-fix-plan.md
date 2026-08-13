---
title: "Fix Balconies and Terraces Rendering as Sealed Boxes Instead of Open, Railed Edges"
date: "2026-08-14"
status: "complete"
request: "Close the gap identified in the render-vs-drawing comparison: balcony and terrace rooms compile and render with a full-height wall on their open edge, so every balcony in the pipeline's output looks like an enclosed room instead of an open terrace with a railing."
plan_type: "multi-phase"
research_inputs:
  - "reports/2026-08-14-contractor-render-vs-drawing.html"
  - "designs/contractor-as-drawn.fidelity.md"
---

# Plan: Fix Balconies and Terraces Rendering as Sealed Boxes

## Objective

Make every `balcony`-typed room in this pipeline render as an open, railed edge —
matching what every one of this repo's floor plans actually draws — instead of a
fully enclosed volume. The defect is confirmed and root-caused: the Blender scene
builder constructs a full-height wall on every room edge not shared with another
room, including balcony edges, and the existing auto-parapet feature only adds a
1100mm railing on top of that wall without ever removing it. This affects every
design in the repo that has a balcony, not just one.

## Context Snapshot

- **Current state:** `src/homedesign/blender/build_scene.py::build_walls()`
  constructs a full-height wall for every entry in `storey["walls"]`
  unconditionally. `src/homedesign/blender/build_scene.py::_add_balcony_parapets()`
  runs afterward and adds a 1100mm parapet panel (via
  `src/homedesign/blender/railings.py::build_parapet()`) on each balcony edge not
  shared with another room — but it adds this parapet *in addition to* the full
  wall already built, never in place of it. The result, confirmed by rendering
  `designs/contractor-as-drawn.json` and inspecting the output: every balcony
  and terrace (`ban_công` on floors 2–5, `sân thượng` front and rear on the roof
  level) renders as a sealed box with no visible opening, and the front
  elevation shows no glazing anywhere above the ground floor even though the
  spec correctly authors windows onto every front bedroom's balcony wall — the
  window exists in the geometry, but an opaque balcony wall stands in front of
  it from the exterior camera's point of view. The same defect affects
  `designs/tubehouse-dream.json`'s balconies.
- **Desired state:** A `balcony`-typed room's own open edges (the edges not
  shared with another room, which is exactly where `_add_balcony_parapets`
  already places a parapet) are never built as full-height walls by
  `build_walls()`. Any edge of a balcony that *is* shared with another room
  (e.g. the partition wall between a bedroom and its balcony, which carries the
  door and window that make the balcony reachable and daylit) is built exactly
  as it is today — unaffected by this change. Both `designs/tubehouse-dream.json`
  and `designs/contractor-as-drawn.json` are rebuilt and their `deliverables/`
  galleries show balconies with visible open railings and the front facades
  show real glazing.
- **Key repo surfaces:**
  - `src/homedesign/model.py` — the `Wall` dataclass (currently has no way to
    say which room an exterior wall belongs to)
  - `src/homedesign/compiler.py::_derive_walls` — already computes, then
    discards, exactly the information needed (`covering`, the set of room ids
    an edge piece belongs to)
  - `src/homedesign/blender/build_scene.py` — `build_walls()`,
    `_add_balcony_parapets()`
  - `src/homedesign/blender/railings.py` — `build_parapet()` (unaffected, reused as-is)
  - `src/homedesign/rects.py::open_edges` — already used by
    `_add_balcony_parapets` to compute which sides get a parapet; not modified,
    but its semantics (edge not shared with another room in the same storey)
    are the same semantics this fix needs for wall suppression
  - `tests/test_compiler.py` — where wall-derivation behaviour is tested today
    (`test_demo_walls_include_exterior_and_partition`,
    `test_wall_alignment_inside_lies_on_room_side`, and the `_single_room_spec`
    helper pattern to copy)
  - `designs/tubehouse-dream.json`, `designs/contractor-as-drawn.json` — the two
    real designs with balconies, used as the smoke-test/rebuild targets
  - `designs/contractor-as-drawn.fidelity.md` — findings (e) and (f), which this
    fix directly resolves and which must be updated to say so
- **Out of scope:** Adding a kerb/upstand slab to balcony edges (the existing
  1100mm parapet is sufficient edge protection on its own). Changing
  `railings.py::build_parapet`'s geometry, height, or thickness. Any change to
  `checks.py` (the compiled model still contains every wall entry; this fix
  only changes which entries the *Blender renderer* turns into geometry, not
  what the compiler emits or what the checker validates). Re-deriving
  `open_edges` logic inside `build_walls` — the fix reuses the ownership data
  added to `Wall` in PHASE-01, not a second geometric computation. The stair
  core depth, the elevator inference, and the mezzanine-void placeholder
  (findings 07, 08, 10 in the render-vs-drawing report) — those are separate,
  unrelated gaps and are not touched here. Any change to
  `spec/homespec.schema.json` (no new spec field is needed — `room_id` is
  computed, not authored).

## Environment & Conventions

- **Stack:** Python ≥ 3.11 (`pyproject.toml`), setuptools build backend, plain
  `pip`. Runtime deps: `jsonschema>=4.0`, `ezdxf>=1.0`, `pillow>=10.0`. Dev deps:
  `pytest>=8.0`, `ruff==0.15.7` (pinned exactly). Rendering requires
  **Blender 4.1.1** installed externally — it is not a Python dependency.
- **Setup:**
  ```bash
  pip install -e ".[dev]"
  ```
- **Build / Run:**
  ```bash
  homedesign compile designs/contractor-as-drawn.json
  homedesign build   designs/contractor-as-drawn.json --profile preview
  homedesign build   designs/tubehouse-dream.json --profile final --gltf
  ```
  `homedesign` is a console script (`pyproject.toml`:
  `homedesign = "homedesign.__main__:main"`). `python -m homedesign <args>` is
  equivalent. All output paths are hardcoded to `<repo root>/output/`.
- **Test:** full suite:
  ```bash
  python -m pytest tests -q
  ```
  single test:
  ```bash
  python -m pytest tests/test_compiler.py::test_balcony_exterior_wall_carries_its_room_id -q
  ```
  Lint (must be clean before any commit; CI runs it):
  ```bash
  ruff check src tests
  python scripts/sync_skill.py --check
  ```
  `pyproject.toml` sets `pythonpath = ["src"]`, so no install is required for
  tests to import `homedesign`. Baseline as of this plan: **131 tests pass**
  (`python -m pytest tests -q`); this plan must leave that count at 131 plus the
  new tests added in PHASE-01, all passing.
- **Conventions & traps:**
  - **Millimetres everywhere on the Python side, metres everywhere on the
    Blender side.** The `/ 1000` conversion happens exactly once, at the
    `src/homedesign/blender/` boundary. `build_walls()` already does this
    conversion for `x, y, w, h` — the new suppression check operates on the
    raw millimetre dict before that conversion, so no new unit-conversion code
    is needed.
  - `Wall` is a `@dataclass`; `CompiledModel.to_dict()` calls `dataclasses.asdict(self)`
    and `CompiledModel.from_dict()` calls `Wall(**w)`. A new **optional,
    default-valued** field on `Wall` round-trips through both automatically —
    no serialization code to touch, and any `.model.json` cached from before
    this change (missing the new key) still loads because the field has a
    default.
  - Only `src/homedesign/blender/` may import `bpy`; `build_scene.py` runs as a
    top-level Blender script (absolute imports only, never imported by tests).
  - `output/` is git-ignored and disposable; `deliverables/` is tracked — copy
    finals there explicitly, never edit `output/` by hand.
  - Ruff is pinned to `0.15.7`.
  - Room `type` is a closed 12-value enum (`bedroom, bathroom, kitchen, living,
    dining, hall, stairwell, garage, balcony, office, storage, elevator`); this
    fix keys off `"balcony"` specifically, exactly matching
    `_add_balcony_parapets`' own existing check (`room["type"] != "balcony"`).
- **Repo map:**
  ```
  src/homedesign/model.py           Wall, Storey, CompiledModel dataclasses (PHASE-01 touches Wall)
  src/homedesign/compiler.py        _derive_walls (PHASE-01 touches this function only)
  src/homedesign/blender/build_scene.py   build_walls, _add_balcony_parapets (PHASE-02)
  src/homedesign/blender/railings.py      build_parapet (read-only reference, unchanged)
  src/homedesign/rects.py           open_edges (read-only reference, unchanged)
  tests/test_compiler.py            wall-derivation tests; _single_room_spec() helper pattern (PHASE-01 tests go here)
  designs/tubehouse-dream.json      real design with balconies (PHASE-03 rebuild target)
  designs/contractor-as-drawn.json  real design with balconies (PHASE-03 rebuild target)
  designs/contractor-as-drawn.fidelity.md   findings (e)/(f) to update in PHASE-03
  deliverables/tubehouse-dream/, deliverables/contractor-as-drawn/   tracked finals to republish
  ```

## Research Inputs

- From `reports/2026-08-14-contractor-render-vs-drawing.html` (render-vs-drawing
  comparison built this session):
  - Finding 05 ("The front facade has no glazing," classified Departure): the
    spec correctly authors a door and a 1400mm window on every front bedroom's
    wall to its balcony, but the renderer builds a full-height wall on the
    balcony's own street-facing edge regardless, so no glazing is visible from
    outside on any of the seven storeys.
  - Finding 06 ("Balconies and terraces render enclosed, not open," Departure):
    the roof plan hatches both `SÂN THƯỢNG` zones to mean "no roof, open to
    sky"; the corresponding render shows a fully closed room with no railing.
    Root cause confirmed by reading `build_scene.py`: `_add_balcony_parapets`
    adds a railing on top of the existing wall, it never suppresses it.
  - Both findings explicitly note this is a pipeline behaviour, not specific to
    the contractor design — `designs/tubehouse-dream.json`'s balconies have the
    identical defect.
- From `designs/contractor-as-drawn.fidelity.md`:
  - Finding (e) records the same root cause in the model's own departure
    ledger and states plainly that it is "out of scope" for that prior pass
    because `src/homedesign/blender/` changes were excluded from it. This plan
    is the follow-up that lifts that exclusion and fixes the root cause.
  - Finding (f) depends on (e): the bedroom-to-balcony glazing was modelled
    correctly specifically so that fixing (e) would make it visible; until this
    plan, that glazing has never been visible in any rendered output.

## Assumptions and Constraints

- **ASM-001:** No spec in the repo authors a door or window whose `between`
  list includes a `balcony`-typed room's own street/exterior-facing side (as
  opposed to the partition side shared with the room behind it) — both real
  designs put the door/window on the shared partition wall (e.g.
  `["ngu_truoc_f2", "ban_cong_f2"]`), never on the balcony's own free edge.
  — **BINDING DEFAULT:** the wall-suppression check in PHASE-02 must still
  explicitly verify no opening references the wall it is about to skip
  (`wall["id"] not in {o["wall_id"] for o in storey["openings"]}`) and fall
  back to building the wall normally if one does, so a future design that
  *does* author an opening there loses nothing — it simply doesn't benefit
  from the suppression on that one edge.
- **ASM-002:** A `partition`-kind wall (shared between two or more rooms) never
  needs a `room_id`, because suppression only ever applies to a balcony's own
  free edge, which is by construction an `exterior`-kind wall (an edge covered
  by exactly one room). — **BINDING DEFAULT:** populate `room_id` only when
  `kind == "exterior"` (i.e. `len(covering) == 1`); leave it `None` for
  `partition`-kind walls. This also keeps the change unambiguous — a
  `partition` wall by definition serves two rooms, so a single `room_id` would
  be misleading if populated.
- **CON-001:** `Wall` is a `@dataclass` consumed by `dataclasses.asdict()` and
  reconstructed via `Wall(**w)`; the new field must have a default value
  (`Optional[str] = None`) so both directions stay backward-compatible with
  any already-cached `output/compiled/*.model.json` from before this change.
- **CON-002:** `src/homedesign/blender/build_scene.py` cannot be exercised by
  `pytest` (it requires `bpy`, which is not installed in the test environment;
  the repo's own convention, confirmed in `AGENTS.md`, is to smoke-test
  Blender-side changes by running an actual build). PHASE-02's verification is
  therefore a real `homedesign build` run plus visual inspection of the
  rendered PNGs, not a pytest assertion.
- **CON-003:** Renders **must** run on Blender 4.1's legacy EEVEE.
  `orchestrator._CANDIDATES` already orders 4.1 ahead of 4.5/4.2 — do not
  reorder it. EEVEE Next (4.2+) miscompiles on Intel UHD 620 iGPUs and renders
  every lit surface blood red, independent of this fix. If a render looks red,
  the wrong Blender ran — check with `BLENDER_CMD` before suspecting this
  change.
- **DEC-001:** Fix the root cause in the compiled-model schema (give walls an
  owning `room_id`) rather than re-deriving room/wall adjacency geometrically
  inside `build_scene.py`. The compiler already computes this exact
  information (`covering`) during `_derive_walls` and currently discards it;
  adding one field is less code and less risk than reconstructing the same
  fact from raw coordinates a second time in the Blender-side script, and it
  is available to any future feature that needs to know which room a wall
  belongs to (per-room wall material overrides, per-room wall-thickness
  overrides, etc. — not built here, just no longer blocked).

## Specification

### Wall ownership rule

For every wall segment `w` produced by `_derive_walls`, with `covering` the
tuple of room ids whose rect edge contributed to that segment (already computed
inside the function, at the point where `kind = "partition" if len(covering) >= 2 else "exterior"`
is decided):

```
w.room_id = covering[0]  if len(covering) == 1   (kind == "exterior")
w.room_id = None         if len(covering) >= 2   (kind == "partition")
```

- `covering` — the room id(s) whose edge produced this wall segment; already a
  local variable in `_derive_walls`, not something to recompute.
- This is exhaustive: every wall segment has `len(covering) >= 1` by
  construction (a wall only exists where the sweep-line found at least one
  covering room), so every wall gets a defined `room_id` value (either a real
  id or `None`), never an unset/missing case.

### Suppression rule (Blender-side)

For every wall `w` in `storey["walls"]` (the compiled-model dict form, keys in
millimetres), let `room_types = {r["id"]: r["type"] for r in storey["rooms"]}`
and `opening_wall_ids = {o["wall_id"] for o in storey["openings"]}`. Build the
wall (as today) **unless all three** hold:

1. `w["room_id"]` is not `None`
2. `room_types.get(w["room_id"]) == "balcony"`
3. `w["id"] not in opening_wall_ids`

When all three hold, skip constructing that wall entirely (no `make_box` call,
no opening-cutting loop for it — there are no openings on it per condition 3).
`_add_balcony_parapets`, which already runs later in the same function and
already recomputes "which edges are open" via `open_edges()`, is untouched and
continues to add the 1100mm parapet on exactly the edges this rule just left
unbuilt — this is what makes the interaction between the two functions
correct without either one needing to know about the other's internals.

## Phase Summary

| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Give every derived exterior wall an owning `room_id` | None | Modified `model.py`, `compiler.py`; new tests in `test_compiler.py`; full suite green |
| PHASE-02 | Suppress the full wall on a balcony's own open edges in the Blender builder | PHASE-01 | Modified `build_scene.py`; a preview-quality smoke render showing an open balcony |
| PHASE-03 | Rebuild both real galleries, verify, update the fidelity ledger, republish | PHASE-01, PHASE-02 | Rebuilt `deliverables/tubehouse-dream/`, `deliverables/contractor-as-drawn/`; updated `fidelity.md` |

## Detailed Phases

### PHASE-01 - Give Derived Walls an Owning Room

**Goal**
Add a `room_id` field to the `Wall` dataclass and populate it during wall
derivation, so downstream consumers (the Blender builder in PHASE-02) can tell
which single room an `exterior`-kind wall belongs to, without recomputing
adjacency from raw coordinates.

**Tasks**
- [ ] TASK-01-01: Open `src/homedesign/model.py` and add `room_id: Optional[str] = None`
      to the `Wall` dataclass, immediately after the existing `orientation` field.
      `Optional` is already imported (`from typing import Literal, Optional`).
- [ ] TASK-01-02: Open `src/homedesign/compiler.py`, locate `_derive_walls`
      (the loop over `merged` starting at `for start, end, covering in merged:`,
      around line 250). Add `room_id=covering[0] if len(covering) == 1 else None`
      as a new keyword argument to the `Wall(...)` constructor call at the end
      of that loop body (around line 284–296). Leave every other field and the
      rest of the function's logic (centred vs. inside alignment, thickness
      selection) completely unchanged.
- [ ] TASK-01-03: Add a `_balcony_spec()` helper function to
      `tests/test_compiler.py`, modelled directly on the existing
      `_single_room_spec()` helper (same file, ~line 282): a two-room storey —
      room id `"bed"` (`type: "bedroom"`, `rect: {"x":0,"y":0,"w":4000,"d":4000}`)
      and room id `"balc"` (`type: "balcony"`, `rect: {"x":0,"y":4000,"w":4000,"d":1500}`),
      `site: {"plot_width_mm": 4000, "plot_depth_mm": 5500}`. `balc`'s north
      edge at y=4000 is shared with `bed`'s south edge (becomes a `partition`
      wall); `balc`'s south edge at y=5500, west edge at x=0, and east edge at
      x=4000 are free (each becomes an `exterior` wall owned by `"balc"`).
- [ ] TASK-01-04: Add `test_balcony_exterior_wall_carries_its_room_id` to
      `tests/test_compiler.py`: compile `_balcony_spec()`, find the wall whose
      geometry is the balcony's south edge (`orientation == "horizontal"` and
      `y >= 4000`, i.e. the wall nearest the plot's south boundary — use the
      same `next(w for w in ...)` pattern as
      `test_wall_alignment_inside_lies_on_room_side`), assert
      `wall.kind == "exterior"` and `wall.room_id == "balc"`.
- [ ] TASK-01-05: Add `test_partition_wall_has_no_room_id` to
      `tests/test_compiler.py`: using the same `_balcony_spec()` fixture, find
      the shared wall between `"bed"` and `"balc"` (`orientation == "horizontal"`
      and `y` nearest `4000`, `wall.kind == "partition"`), assert
      `wall.room_id is None`.
- [ ] TASK-01-06: Add `test_existing_designs_still_compile_with_wall_room_id`
      to `tests/test_compiler.py`: for both `demo-3br-2storey.json` and
      `tubehouse-mini.json` (loaded via the existing `load_example` helper),
      compile and assert every wall's `room_id` is either `None` or a string
      that is a real room id on that storey
      (`w.room_id is None or w.room_id in {r.id for r in storey.rooms}`) — a
      cheap sanity check that the new field never points at a nonexistent room.
- [ ] TASK-01-07: Run `python -m pytest tests -q` and confirm all 131 previously
      passing tests still pass plus the 3 new ones (134 total). Run
      `ruff check src tests` and confirm it reports no issues.

**File Changes**
- `src/homedesign/model.py` (modify): add one field to the `Wall` dataclass.
  Do not change `to_dict`/`from_dict` — `asdict()` and `Wall(**w)` already
  handle the new field automatically because it has a default value.
- `src/homedesign/compiler.py` (modify): add one keyword argument to the single
  `Wall(...)` constructor call inside `_derive_walls`. No other function in
  this file changes.
- `tests/test_compiler.py` (modify): add `_balcony_spec()` helper and three new
  test functions, appended near the existing wall-alignment tests
  (after `test_interior_centre_partition_bounded_inset_half` or at end of
  file — exact position does not matter, pytest discovers by name). Do not
  modify any existing test function.

**Function Signatures**
- `Wall.room_id: Optional[str]` — new dataclass field (not a function); default
  `None`. For an `exterior`-kind wall, the single room id whose rect edge
  produced it. For a `partition`-kind wall, always `None`.
- `_derive_walls(rooms: list[Room], plot_w: float, plot_d: float, level: int, wall_alignment: str = "centre") -> list[Wall]`
  — unchanged signature and return type; each returned `Wall` now additionally
  carries `room_id`.

**Test Specs**
- `compile_spec(_balcony_spec())` → the wall covering the balcony's south edge
  (the one whose `y` is nearest `5500` under `"inside"` alignment, or nearest
  `5500 ± thickness/2` under `"centre"`) has `.kind == "exterior"` and
  `.room_id == "balc"` (or whichever id `_balcony_spec()` assigns the balcony
  room).
- Same compile → the wall shared between the bedroom and balcony rooms (at
  `y` near `4000`) has `.kind == "partition"` and `.room_id is None`.
- `compile_spec(load_example("demo-3br-2storey.json"))` → every wall on every
  storey has `.room_id in (None,) or .room_id` equal to some room's `.id` on
  that same storey; no wall's `room_id` references a room on a different
  storey or a nonexistent id.
- Edge case: a wall covering **zero** rooms cannot occur — `_derive_walls`'s
  sweep-line only emits a `merged` piece when `covering` is non-empty
  (`if covering: pieces.append(...)`), so `len(covering) == 1` vs. `>= 2` is
  the only branch; no third case needs a test.

**Dependencies**
- None.

**Exit Criteria**
- [ ] `python -m pytest tests -q` reports 134 passed (131 baseline + 3 new),
      zero failures.
- [ ] `ruff check src tests` reports `All checks passed!`.
- [ ] `python -m homedesign compile designs/contractor-as-drawn.json` and
      `python -m homedesign compile designs/tubehouse-dream.json` both still
      exit 0 with no new errors or warnings (confirms the schema-level change
      doesn't break either real design's compile step before PHASE-02 touches
      any rendering code).

**Phase Risks**
- **RISK-01-01:** A future contributor might assume `room_id` is populated for
  `partition` walls too and rely on it there. Mitigated by ASM-002's explicit
  binding default and by TASK-01-05's test asserting `None` for partitions,
  which will fail loudly if that invariant is ever violated by a later change.

### PHASE-02 - Suppress the Wall on a Balcony's Own Open Edges

**Goal**
Stop `build_walls()` from constructing a full-height wall on any balcony edge
that `_add_balcony_parapets()` is already going to give a parapet, using the
`room_id` added in PHASE-01 — with no change to which edges get a parapet, no
change to `_add_balcony_parapets` itself, and no change to any wall that
carries an opening.

**Tasks**
- [ ] TASK-02-01: Open `src/homedesign/blender/build_scene.py`, locate
      `build_walls(storey, style, structure)` (top of file, ~line 56). Before
      the `for wall in storey["walls"]:` loop, add two local lookups:
      `room_types = {r["id"]: r["type"] for r in storey["rooms"]}` and
      `opening_wall_ids = {o["wall_id"] for o in storey["openings"]}`.
- [ ] TASK-02-02: Inside the loop, immediately after `for wall in storey["walls"]:`
      and before the existing `x, y = wall["x"] / 1000, wall["y"] / 1000` line,
      add the suppression check from the Specification's "Suppression rule"
      section: if `wall.get("room_id")` is truthy, `room_types.get(wall["room_id"]) == "balcony"`,
      and `wall["id"] not in opening_wall_ids`, then `continue` to the next
      wall without building anything for this one.
- [ ] TASK-02-03: Do not touch `_add_balcony_parapets`, `railings.py`, or any
      other function in `build_scene.py`. This is a single, localized addition
      to `build_walls()`.
- [ ] TASK-02-04: Smoke-test with a fast preview build before spending time on
      a full render:
      ```bash
      homedesign build designs/contractor-as-drawn.json --profile preview
      ```
      Confirm it completes without a Python traceback from the Blender-side
      script (a `KeyError` on `wall["room_id"]` for an old cached `.model.json`
      would surface here — see RISK-02-01).
- [ ] TASK-02-05: Open `output/png/contractor-as-drawn_exterior_front.png` and
      `output/png/contractor-as-drawn_san_thuong.png` (or view them with an
      image viewer). Confirm: the balconies no longer show a solid wall on
      their street/open-sky-facing edge; a thin parapet element is visible
      instead; the window that was previously modelled but invisible (on the
      bedroom-to-balcony partition wall) is now visible from the exterior
      camera. If a balcony still looks fully enclosed, re-check TASK-02-01/02
      against the exact field names in the compiled model JSON
      (`output/compiled/contractor-as-drawn.model.json`) before assuming the
      renderer is at fault.
- [ ] TASK-02-06: Repeat TASK-02-04/05 for `designs/tubehouse-dream.json`
      (`homedesign build designs/tubehouse-dream.json --profile preview`),
      confirming the same fix applies there without any design-specific code.

**File Changes**
- `src/homedesign/blender/build_scene.py` (modify): `build_walls()` gains two
  local dict comprehensions and one `if`/`continue` guard, as specified above.
  No other function in this file changes. No new imports are needed — the
  function already has `storey` (a plain dict) in scope.

**Function Signatures**
- `build_walls(storey: dict, style: str, structure: bpy.types.Collection) -> None`
  — unchanged signature; now skips a subset of `storey["walls"]` entries
  instead of building all of them.

**Test Specs**
None — no automated test exists or is added here (`build_scene.py` requires
`bpy`, which this repo's test environment does not have; see CON-002). The
smoke-test steps in TASK-02-04/05/06 are the verification for this phase and
are re-stated as shell commands in `## Verification Strategy` below.

**Dependencies**
- PHASE-01 complete (`Wall.room_id` must exist and be populated before this
  phase's check can read it from the compiled model JSON).

**Exit Criteria**
- [ ] `homedesign build designs/contractor-as-drawn.json --profile preview`
      exits 0 with no traceback.
- [ ] `homedesign build designs/tubehouse-dream.json --profile preview`
      exits 0 with no traceback.
- [ ] Visual inspection of at least one exterior render and one balcony/terrace
      render from each design confirms an open edge (parapet visible, no solid
      wall) where the drawing shows one.
- [ ] `python -m pytest tests -q` still reports the same pass count as
      PHASE-01's exit criteria (this phase touches no test-covered code path,
      so the count must not change).

**Phase Risks**
- **RISK-02-01:** A `.model.json` cached under `output/compiled/` from before
  PHASE-01 lacks the `room_id` key entirely. `wall.get("room_id")` (not
  `wall["room_id"]`) is used specifically to make this safe — `.get()` returns
  `None` on a missing key, which fails the suppression check's first condition
  and falls through to building the wall exactly as before. Do not change this
  to bracket access. If in doubt, delete `output/compiled/*.model.json` before
  the smoke test to force a fresh compile — `output/` is disposable by
  convention.
- **RISK-02-02:** Suppressing a wall that turns out to carry an opening this
  plan's audit missed would silently delete a door or window from the render.
  Mitigated structurally by condition 3 of the suppression rule
  (`wall["id"] not in opening_wall_ids`), computed fresh from the same
  compiled model on every run — not by a one-time audit of today's two
  designs.

### PHASE-03 - Rebuild, Verify, and Republish Both Galleries

**Goal**
Produce final-quality renders for both real designs with the fix applied,
confirm freshness and correctness, update `contractor-as-drawn.fidelity.md` to
record findings (e) and (f) as resolved, and republish the tracked
deliverables.

**Tasks**
- [ ] TASK-03-01: Confirm which Blender will run:
      ```bash
      python -c "from homedesign import orchestrator; print(orchestrator.find_blender())"
      ```
      Must resolve to a Blender **4.1** executable (CON-003). Set `BLENDER_CMD`
      if it does not.
- [ ] TASK-03-02: Full rebuild for `contractor-as-drawn`:
      ```bash
      homedesign build designs/contractor-as-drawn.json --profile final --gltf
      ```
      If this exceeds a ~10-minute execution window in whatever environment
      runs it, fall back to the chunked pattern already proven to work in this
      repo: render 3–4 views at a time with
      `homedesign render designs/contractor-as-drawn.json --profile final --view <name> --view <name> ...`
      (repeated until all 12 views in `designs/contractor-as-drawn.json`'s
      `meta.views` are rendered), then export the GLB separately by reusing the
      saved `.blend`:
      ```bash
      python -c "
      from pathlib import Path
      from homedesign import orchestrator
      orchestrator.build_scene(Path('output/compiled/contractor-as-drawn.model.json'), Path('output'), profile='final', skip_existing=True, reuse_blend=True, gltf=True)
      "
      ```
- [ ] TASK-03-03: Full rebuild for `tubehouse-dream`, same pattern:
      ```bash
      homedesign build designs/tubehouse-dream.json --profile final --gltf
      ```
- [ ] TASK-03-04: Verify freshness and absence of red-render corruption for
      both designs (see `## Verification Strategy` for the exact commands).
- [ ] TASK-03-05: Republish `deliverables/contractor-as-drawn/` and
      `deliverables/tubehouse-dream/`:
      ```bash
      cp output/png/contractor-as-drawn_*.png deliverables/contractor-as-drawn/png/
      cp output/gltf/contractor-as-drawn.glb  deliverables/contractor-as-drawn/gltf/
      cp output/viewer/contractor-as-drawn.html deliverables/contractor-as-drawn/viewer/
      cp output/png/tubehouse-dream_*.png deliverables/tubehouse-dream/png/
      cp output/gltf/tubehouse-dream.glb  deliverables/tubehouse-dream/gltf/
      cp output/viewer/tubehouse-dream.html deliverables/tubehouse-dream/viewer/
      ```
      Do not copy `.png.json` provenance sidecars into `deliverables/` — the
      existing convention there is bare PNGs only (confirm with
      `ls deliverables/contractor-as-drawn/png/*.json 2>/dev/null | wc -l`
      → must print `0`).
- [ ] TASK-03-06: Edit `designs/contractor-as-drawn.fidelity.md`, finding (e)
      ("Balcony/terrace rooms render as fully enclosed volumes, not open
      railings"): append a note that this is fixed as of this plan, naming the
      mechanism (`Wall.room_id` + the `build_walls()` suppression check) and
      the commit it lands in. Do the same for finding (f) ("Front-facing
      daylight is modelled as bedroom-to-balcony glazing... not visible from
      outside... because of (e)"): note that the glazing is now visible,
      since the blocking cause is resolved. Do not delete either finding's
      original text — append a resolution note below each so the ledger keeps
      its history.
- [ ] TASK-03-07: Regenerate `reports/2026-08-14-contractor-render-vs-drawing.html`'s
      findings 05 and 06 (or produce a short follow-up note) is **not**
      required by this plan — the HTML report is a point-in-time snapshot: leave
      it as-is and let the fidelity ledger (TASK-03-06) be the durable record
      of the fix. Do not edit the HTML report file.

**File Changes**
- `output/**` (create, generated, git-ignored): full rebuild artifacts for
  both designs.
- `deliverables/contractor-as-drawn/png/*.png`,
  `deliverables/contractor-as-drawn/gltf/contractor-as-drawn.glb`,
  `deliverables/contractor-as-drawn/viewer/contractor-as-drawn.html` (modify,
  overwritten with fresh renders).
- `deliverables/tubehouse-dream/png/*.png`,
  `deliverables/tubehouse-dream/gltf/tubehouse-dream.glb`,
  `deliverables/tubehouse-dream/viewer/tubehouse-dream.html` (modify,
  overwritten with fresh renders).
- `designs/contractor-as-drawn.fidelity.md` (modify): append resolution notes
  to findings (e) and (f); no other section changes.
- `reports/2026-08-14-contractor-render-vs-drawing.html` (leave alone, per
  TASK-03-07).
- `designs/tubehouse-dream.json`, `designs/contractor-as-drawn.json` (leave
  alone): no spec changes in this plan, only the renderer and the compiled
  model schema changed.

**Function Signatures**
None — no code interfaces change in this phase.

**Test Specs**
None — no testable behavior changes in this phase; verification is the
freshness/redness checks in `## Verification Strategy`.

**Dependencies**
- PHASE-01 and PHASE-02 complete.
- Blender 4.1.1 installed and discoverable, or `BLENDER_CMD` pointing at it.

**Exit Criteria**
- [ ] Both designs' `output/png/` galleries are complete (12 files for
      `contractor-as-drawn`, matching the count in its `meta.views`; 9 files
      for `tubehouse-dream`, matching its `meta.views`) and every `.png.json`
      sidecar's `model_hash` matches the corresponding `output/compiled/*.model.json`.
- [ ] No rendered PNG samples as blood-red at its centre pixel (CON-003 guard).
- [ ] `deliverables/contractor-as-drawn/` and `deliverables/tubehouse-dream/`
      contain the refreshed PNGs, GLB, and viewer HTML, and
      `git status --porcelain` shows them as modified (tracked), not untracked
      or ignored.
- [ ] `designs/contractor-as-drawn.fidelity.md` findings (e) and (f) each carry
      a resolution note.

**Phase Risks**
- **RISK-03-01:** A full final-quality build (scene rebuild + render all views
  + GLB export) has, in this repo's own recent history, exceeded a 10-minute
  single-command execution window and been killed mid-render. TASK-03-02
  states the exact chunked fallback (proven to work: render in batches of 3–4
  views with `--view`, then export the GLB separately via
  `orchestrator.build_scene(..., skip_existing=True, reuse_blend=True, gltf=True)`)
  so this is not a blocking failure if it recurs.
- **RISK-03-02:** Copying stale PNGs left over from a previous view-naming
  scheme into `deliverables/` (this has happened before in this repo's
  history). Mitigated by TASK-03-05's glob pattern only matching the current
  `meta.views` names and by checking `ls deliverables/.../png/*.png | wc -l`
  against the expected count before considering the phase done.

## Gotchas

- **`wall.get("room_id")`, never `wall["room_id"]`, on the Blender side.** The
  compiled-model JSON is read from disk as a plain dict in `build_scene.py`; a
  `.model.json` cached before PHASE-01 lands has no `room_id` key at all, and
  bracket access would raise `KeyError` and abort the entire render. `.get()`
  degrades safely to "build the wall as before."
- **`room_id` is `None` for every `partition` wall by design (ASM-002), not a
  bug to "complete."** Do not extend population to partition walls — a shared
  wall genuinely has no single owning room, and the suppression rule only ever
  needs to ask about `exterior` walls (a balcony's own free edges are always
  `exterior`-kind, never `partition`).
- **The suppression check must run before the openings-cutting loop inside
  `build_walls()`, via `continue`,** not after — the existing per-opening loop
  (`for opening in openings: ... boolean_difference(...)`) assumes `wall_obj`
  was already created; skipping the wall must skip that loop too, which
  `continue` does for free since it's the same `for wall in storey["walls"]:`
  iteration.
- **Millimetres vs. metres:** `wall["room_id"]`, `wall["id"]`, and
  `room_types`/`opening_wall_ids` are all identifiers or dicts, not
  measurements — they need no `/ 1000` conversion. Only `x, y, w, h` (already
  handled by the existing code, untouched by this fix) are in millimetres in
  the JSON and metres in Blender.
- **`orchestrator._CANDIDATES` order is load-bearing and pinned by a test**
  (`tests/test_orchestrator.py::test_blender_candidates_prefer_legacy_eevee_build`).
  Nothing in this plan touches it, but PHASE-03's rebuilds will silently
  produce blood-red renders if anyone "helpfully" reorders it first — see
  CON-003.
- **`deliverables/` finals are copied by hand, not generated in place.** A
  `homedesign build ... --gltf` run only ever writes to `output/`; forgetting
  TASK-03-05's `cp` step leaves the tracked deliverables stale even though
  `output/` itself is correct.

## Verification Strategy

- **TEST-001:** `python -m pytest tests -q` → `134 passed` (131 baseline + 3
  new from PHASE-01), zero failures, after PHASE-01. Re-run after PHASE-02 and
  PHASE-03 and confirm the count is unchanged (neither phase touches
  test-covered code).
- **TEST-002:** `ruff check src tests` → `All checks passed!`
- **TEST-003:** `python scripts/sync_skill.py --check` → `ok: skill copies match`
  (CI runs this; this plan changes no skill docs, so it must still pass).
- **TEST-004 (PHASE-01):**
  ```bash
  python -c "
  import json
  from homedesign.compiler import compile_spec
  spec = json.loads(open('designs/contractor-as-drawn.json', encoding='utf-8').read())
  model = compile_spec(spec)
  storey = next(s for s in model.storeys if s.level == 2)
  balc = next(r for r in storey.rooms if r.type == 'balcony')
  owned = [w for w in storey.walls if w.room_id == balc.id]
  print('balcony', balc.id, 'owns', len(owned), 'exterior walls')
  assert len(owned) >= 1
  assert all(w.kind == 'exterior' for w in owned)
  "
  ```
  → prints a count ≥ 1 and both assertions pass, confirming the real design's
  compiled model now carries wall ownership for at least one balcony.
- **TEST-005 (PHASE-02, manual):** Open
  `output/png/contractor-as-drawn_exterior_front.png` after the preview build
  in TASK-02-04/05. Expected: window openings visible on at least one storey
  between ground and roof (before this fix, zero were visible on any storey).
- **TEST-006 (PHASE-02, manual):** Open
  `output/png/contractor-as-drawn_san_thuong.png`. Expected: an open edge with
  a visible parapet rail, not a solid wall on all four sides.
- **TEST-007 (PHASE-03):**
  ```bash
  python -c "
  import json,glob,pathlib
  for name in ['contractor-as-drawn','tubehouse-dream']:
      m = json.load(open(f'output/compiled/{name}.model.json'))['model_hash']
      files = sorted(glob.glob(f'output/png/{name}_*.png.json'))
      bad = [pathlib.Path(p).name for p in files if json.load(open(p))['model_hash'] != m]
      print(name, 'views:', len(files), 'stale:', bad)
  "
  ```
  → for `contractor-as-drawn`: `views: 12 stale: []`. For `tubehouse-dream`:
  `views: 9 stale: []`.
- **TEST-008 (PHASE-03):**
  ```bash
  python -c "
  from PIL import Image
  for f in ['output/png/contractor-as-drawn_exterior_front.png','output/png/tubehouse-dream_exterior_front.png']:
      im = Image.open(f).convert('RGB')
      w,h = im.size
      print(f, im.getpixel((w//2, h//2)))
  "
  ```
  → neither printed pixel is within ±10 of `(194, 34, 53)` (the known EEVEE
  Next red-corruption signature).
- **MANUAL-001:** Compare `output/png/contractor-as-drawn_exterior_front.png`
  side by side with `contractor/MB MAI - MD-Model.pdf`'s front elevation.
  Expected: window bands are now visible at multiple storeys in the render,
  closing (or substantially narrowing) finding 05 from
  `reports/2026-08-14-contractor-render-vs-drawing.html`.
- **MANUAL-002:** Same comparison for `output/png/contractor-as-drawn_san_thuong.png`
  against the roof plan's `SÂN THƯỢNG` hatched zones. Expected: an open,
  railed edge rather than a sealed room, closing finding 06.

## Risks and Alternatives

- **RISK-001:** This fix changes rendered output for every existing design
  with a balcony, which means both `deliverables/tubehouse-dream/` and
  `deliverables/contractor-as-drawn/` change simultaneously. Mitigation:
  PHASE-03 explicitly rebuilds and republishes both, so neither is left
  showing the old, wrong geometry while the other shows the new, correct
  geometry.
- **RISK-002:** A wall suppressed for one balcony edge might, in some future
  design, coincide with a structural expectation elsewhere in the pipeline
  (e.g. a ceiling or floor slab computation that assumes every room boundary
  has a wall). Audited during PHASE-01/02 planning: `build_floors_and_stairs`
  (floor slabs), `_add_top_storey_ceilings`, and the DXF/SVG plan writers in
  `src/homedesign/plan2d.py`/`elevation.py` all consume the compiled model's
  `walls` list directly (unmodified by this fix — PHASE-02 only changes what
  `build_scene.py` *draws* from that list, not the list itself), so 2D plans,
  DXF exports, and floor/ceiling geometry are all unaffected.
- **ALT-001: Re-derive wall/room adjacency geometrically inside `build_scene.py`**,
  reusing `homedesign.rects.open_edges` a second time instead of adding
  `Wall.room_id`. Rejected: `_derive_walls` already computes the exact
  ownership fact needed and currently throws it away; recomputing it from raw
  coordinates a second time, in a different module, using wall-alignment-aware
  geometry that would have to be reimplemented or imported, is more code and
  more risk of the two computations silently disagreeing on an edge case than
  adding one field.
- **ALT-002: Give balconies a short kerb/upstand instead of no wall at all**
  on their open edges, closer to real construction (a balcony floor usually
  has a small raised lip even with open railings above it). Deferred, not
  rejected: it is a real refinement worth doing later, but it adds a new
  geometric parameter (kerb height) with no drawn dimension to source it from
  in either real design, and the parapet alone already closes the two
  findings this plan targets. Worth reconsidering only if a future review
  finds the fully-open edge reads wrong in a render.
- **ALT-003: Suppress the wall in the compiler instead of the Blender builder**
  (i.e. never emit an `exterior` wall for a balcony's open edge in the
  compiled model at all). Rejected: the compiled model's `walls` list is
  consumed by more than the Blender renderer (2D plan/elevation/section
  writers, DXF export, `check_walls_within_plot`), and those surfaces
  correctly want to know a balcony has a boundary there (a floor plan still
  draws a line at a balcony's edge, whether or not it's built as a load-bearing
  wall in 3D). Suppressing at the point of *3D construction* rather than at
  the point of *derivation* keeps every other consumer of the compiled model
  unchanged.

## Suggested Next Step

Execute PHASE-01. It is a two-line production change (one dataclass field, one
constructor keyword argument) plus three new tests, fully verifiable by
`python -m pytest tests -q` and `ruff check src tests` with no Blender
required — the fastest phase to get to a verified, committable state, and
PHASE-02 cannot begin until `Wall.room_id` exists.
