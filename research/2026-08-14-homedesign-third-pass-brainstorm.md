---
title: "homedesign — Third Pass: The Drawing Set Is Blank, the Room Names Never Arrive, and the Spec Cannot Say 'Void'"
date: "2026-08-14"
type: "brainstorm"
depth: "deep"
source_request: "Thoroughly analyze this project's current state, codebase, documentation and architecture; brainstorm what improvements, features, refactors, architectural changes or optimizations would take it to the next level."
slug: "homedesign-third-pass"
mode: "unattended (no interview — recommended answers adopted and recorded under Assumptions Adopted)"
supersedes_context: "research/2026-08-04-homedesign-second-pass-brainstorm.md (its Sprints 1–3 shipped as plans/2026-08-04-homedesign-camera-truth-and-drawings-plan.md); carries forward its unclosed T1-3, T1-5 and T3-5"
---

# Brainstorm: homedesign — Third Pass

## Problem & Why Now

The last two passes worked. Cameras point at the building, stairs are Blondel-compliant,
balconies open instead of sealing themselves into boxes, renders are neutral rather than
blood red, provenance hashes tie every PNG to the model that produced it, and the repo is
green: **134 tests in 9.95 s, `ruff check src tests` clean, `sync_skill.py --check` ok**.
Two real designs compile with **zero** errors and **zero** warnings.

That clean bill of health is exactly why this pass had to look somewhere new. The last
brainstorm's theme was *the renders do not depict the model*. This one's theme is:

> **The 3D half of the pipeline is now trustworthy. The 2D half — the half an architect
> and a contractor actually build from — is silently producing blank and unlabelled
> drawings, and nothing in 134 tests notices.**

Three findings below are not opinions about polish. They are defects reproduced this
session from `HEAD` against the two shipped designs:

1. Every room's authored name is **dropped by the compiler**, so every plan label, DXF
   text entity, section label and PDF schedule row shows `bep_an` where the design says
   `BẾP & ĂN`.
2. The **north and south elevations of the flagship `contractor-as-drawn` are empty** —
   a ground line, an outline rectangle and seven level lines, no walls, no openings.
   These are the street facade and the rear facade of a tube house: the two drawings the
   whole design is about.
3. The PDF's `STALE` badge is computed per image but rendered per page, **last image
   wins** — so a gallery page holding one stale and one fresh render displays no warning
   at all, which is precisely the case the provenance feature exists to catch.

Beyond the defects, the flagship design's own fidelity ledger (`designs/contractor-as-drawn.fidelity.md`)
is the most honest gap analysis in the repo, and it names the ceiling this tool has hit:
the spec language cannot say **void**, so the mezzanine's double-height space — "the
drawing's own reason for showing it at all" — is modelled as a fake slab named
`SÀN GIẢ` to get past `check_room_support`.

Every claim below was verified this session against the code, a fresh compile, or
arithmetic reproduced in a script. Nothing was changed.

## Current State

- **4,370 LOC Python** under `src/homedesign/`, split pure (`compiler`, `checks`,
  `plan2d`, `elevation`, `camera_fit`, `placement`, `stairs`, `rects`, `pdf`, `viewer`)
  vs. bpy-only (`blender/`, ~1,000 LOC). The separation is still the repo's best
  structural asset and has now survived four sprints of change without leaking.
- **Tests**: 15 files, **134 tests, 9.95 s, all green**. 1,784 test LOC against 4,370
  source LOC. Coverage of `blender/` is still **zero**; `viewer.py`, `render_profiles.py`
  and `errors.py` have no direct tests either.
- **Two real designs**: `tubehouse-dream` (5 storeys, 41 rooms, 51 openings) and
  `contractor-as-drawn` (7 storeys, 62 rooms, 101 openings, 193 walls). Both compile with
  0 errors, 0 warnings.
- **The pure pipeline is effectively free**: compile + validate of the 62-room model is
  **0.03 s**; the full 22-file drawing set is **0.35 s**. Every second of cost is Blender.
- **Render reality, unchanged and correctly pinned**: Blender 4.1 legacy EEVEE, ~30 s/view
  at 1080p; Cycles CPU-only at ~170 s/view; EEVEE Next unusable on this iGPU. The
  12-view `contractor-as-drawn` final gallery + scene build + glTF was **1,450 s**.
- **Delivery**: per-storey SVG+DXF, four elevations, two sections, 12-view gallery, GLB +
  self-contained offline viewer, 23-page A3 PDF brief, tracked `deliverables/<slug>/`.

### Evidence gathered this session

| Check | Result |
|---|---|
| `python -m pytest tests -q` | **134 passed in 9.95 s** |
| `ruff check src tests` / `sync_skill.py --check` | clean / `ok: skill copies match` |
| `compile_spec` → `Room.name` for all 8 ground-floor rooms of `contractor-as-drawn` | **`None` for every one** (spec authors `NƠI ĐỂ XE`, `P.KHÁCH`, `BẾP & ĂN`, …) |
| `build_elevation(contractor, "north")` | **`{ground: 1, outline: 1, level: 7}` — zero walls, zero openings** |
| `build_elevation(contractor, "south")` | **identical — zero walls, zero openings** |
| `build_elevation(contractor, "east"/"west")` | 45 walls each, **1 opening across both** (101 exist in the model) |
| `build_elevation(tubehouse-dream, "south")` | 8 walls, **0 openings** |
| Building extent vs. plot, `contractor-as-drawn` | walls span y ∈ [3500, 23800] on a 25000 mm plot → **3500 mm front setback, 1200 mm rear**; the elevation planes at y=0 and y=25000 touch nothing |
| Rooms furnished, `contractor-as-drawn` | **19 of 62** (43 empty), 53 items total, **all one `furniture` tan** |
| Rooms furnished, `tubehouse-dream` | **16 of 41** (25 empty), 41 items |
| `spec/briefs/` contents | **`tubehouse-dream.json` only** → `homedesign pdf designs/contractor-as-drawn.json` exits 1, "brief copy not found" |
| `deliverables/contractor-as-drawn/` | `gltf/`, `png/`, `viewer/` — **no `pdf/`** |
| `meta.views` entry `gieng_troi` ("light well") | maps to `room_id: hall_stair` — a **955 mm corridor with a floor slab on every level**; no light well is modelled |
| Roof spec `{"pitch_deg": 20}` with no `type` | **passes schema validation**, then `compile_spec` raises raw **`KeyError: 'type'`** instead of a `SpecError` |
| `homedesign build --floor N` | argument parsed, **never read** by `cmd_build` |
| `render_profiles.py` docstring | still claims "**`final` promotes EEVEE Next**" — reverted 2026-08-08 |
| Walls cut by boolean modifier, `contractor-as-drawn` | **101 EXACT-solver boolean applies** per scene build, while `rects.py`'s own docstring reads "no booleans — deterministic, artifact-free geometry" |

---

## Findings, Ranked

### Tier 0 — The 2D deliverables are silently wrong

**T0-1 — The compiler drops every room name. All of them.**

`spec/homespec.schema.json` documents `rooms[].name`: *"Optional human-readable room
label, e.g. 'Master bedroom'. Plan labels and the PDF schedule use name when present,
else id."* `model.Room` carries the field. Four consumers read it —
`plan2d._render_svg` (SVG label), `plan2d._render_dxf` (TEXT entity),
`elevation.build_section` (room label), `pdf.build_opening_schedule` (schedule rows) —
all via `room.name or room.id`.

And `compiler._resolve_rooms` constructs rooms like this:

```python
resolved[r["id"]] = Room(id=r["id"], type=r["type"], rect=Rect(**r["rect"]))
```

`name` is never passed. Both the `rect` and the `relative` branch omit it. So
`room.name` is `None` for every room in every design, the `or room.id` fallback always
fires, and the entire naming feature is dead on arrival — schema, model field, four
consumers and all.

The cost is concentrated exactly where it hurts most. `contractor-as-drawn` is a
Vietnamese contractor's scheme whose 62 rooms are carefully labelled `NƠI ĐỂ XE`,
`P.KHÁCH`, `P.NGỦ CHÍNH`, `BẾP & ĂN`, `SÂN THƯỢNG`. Every drawing and every schedule
row in the deliverable instead reads `gara`, `khach`, `ngu_truoc_f2`, `bep_an`,
`san_thuong_sau`. The plan sheets are unreadable to the person they were reconstructed
for.

The fix in `_resolve_rooms` is one keyword argument in two places. But it must ship
**with** its companion:

**T0-1b — Once names arrive, they will break the SVG.** `plan2d` and `elevation`
interpolate labels straight into XML with no escaping:

```python
parts.append(f'<text …>{label}</text>')
```

`BẾP & ĂN` contains a bare `&`. Today's SVGs parse only because the name is discarded
and `bep_an` is emitted instead — verified this session (`ElementTree.fromstring` on the
current ground-floor SVG: OK). Fix `name` alone and the flagship design starts writing
invalid XML into the SVG, the inlined PDF and the DXF TEXT entity on the same commit.
A single `xml.sax.saxutils.escape` helper used by both writers closes it, and a test
with an `&`-bearing room name pins it.

**T0-2 — Two of the four elevations of the flagship design are blank sheets.**

`elevation._wall_on_plane` decides which walls appear on an elevation by testing
whether a wall's exterior face *or* centre line lies within 1 mm of a **plot boundary**
plane — `y=0` for north, `y=plot_depth` for south, `x=0` for west, `x=plot_width` for
east.

This silently assumes the building fills its plot. `contractor-as-drawn` does not: its
walls span y ∈ [3500, 23800] on a 25,000 mm plot — a 3,500 mm front setback and a
1,200 mm rear. Nothing sits on y=0 or y=25000. Measured this session:

| side | primitives produced |
|---|---|
| north | ground 1, outline 1, level 7 — **no wall, no opening** |
| south | ground 1, outline 1, level 7 — **no wall, no opening** |
| east | 45 walls, 0 openings |
| west | 45 walls, 1 opening |

So the north (street) and south (rear) elevations of a 7-storey tube house — the two
sheets the design exists to communicate — are an empty rectangle with seven dashed lines
in it. And across all four sides, **1 of the model's 101 openings** is drawn.

This is not solely a setback bug. Even `tubehouse-dream`, which does fill its plot,
yields a south elevation with 8 walls and **zero openings**, because the coplanarity
test admits the rearmost wall but not the openings' host walls one room inboard.

The real defect is conceptual: an elevation is not "the walls that happen to be coplanar
with the plot line." It is an **orthographic projection of everything visible from one
direction**. The fix is a rewrite of `build_elevation` around that definition:

- derive the plane from the *building's* bounding box per side, not the plot's;
- project **every** wall, opening, balcony parapet, roof, stair and railing onto the
  plane;
- painter-sort by distance from the viewer so nearer geometry overpaints farther;
- draw the outermost silhouette as the outline instead of assuming the plot rectangle.

The draw-model/renderer split (`build_*` → `_svg`/`_dxf`) that PHASE-04 established is
the right shape and survives this change untouched — only the producer is replaced.

**T0-3 — The PDF's staleness badge is last-image-wins, so mixed pages show nothing.**

`pdf._gallery_pages` builds two-up gallery pages. Inside the per-image loop:

```python
for p in chunk:
    caption = ""
    if current_hash is not None:
        sidecar = read_render_sidecar(p)
        if sidecar is None or sidecar.get("model_hash") != current_hash:
            caption = " <span …>STALE</span>"
```

…and then, outside the loop, `caption` is interpolated **once** into the page heading.
`caption` is reassigned every iteration, so only the last image of the pair decides the
heading. A page holding a stale render followed by a fresh one renders **no warning**.

The stale case that leaks through is the common one: re-render a few views after a
change, ship the brief without `--require-fresh`, and every page whose second image
happens to be fresh loses its badge. The per-image `warning:` line still prints on
stderr, so the failure is invisible in the artifact and quiet in the log. Fix: badge the
`<img>`, not the page.

---

### Tier 1 — Capability ceilings the flagship design had to work around

The fidelity ledger for `contractor-as-drawn` is unusually candid, and everything in
this tier is drawn from a deviation it was forced to record. These are not hypotheticals;
they are documented concessions in a shipped deliverable.

**T1-1 — The spec cannot say "void". This is the single largest fidelity concession in
the repo.**

Ledger section (h), quoted:

> A placeholder `storage`-typed room named "SÀN GIẢ (Ô THÔNG TẦNG THEO BẢN VẼ)" ("false
> floor — the double-height opening per the drawing") fills the void on level 1 only so
> the model compiles. … **the real building has an open, light-filled double-height
> space here (the drawing's own reason for showing it at all), and this render shows an
> enclosed mezzanine floor instead.**

The mechanism is `checks.check_room_support`, which requires every room on level ≥ 1 to
be ≥ 80 % covered by rooms below. Levels 2–4's front bedroom and balcony sit over the
mezzanine void at 0 % coverage. There is no way to say "this is spanned by a beam, not
a slab," so a fake room is authored to satisfy the checker — and the checker's whole
purpose (catching genuinely unsupported floors) is defeated in the same stroke, because
a `storage` room is indistinguishable from a real one.

`_derive_floor_voids` already punches slab voids — but only for `stairwell` and
`elevator` rooms, automatically, with no authoring surface. The generalisation is small
and mostly reuses machinery that exists:

- a `void` room type (or, cleaner, `storeys[].voids: [{x,y,w,d}]` alongside `roof.voids`
  — the roof already has exactly this shape);
- fed into `Storey.floor_voids`, which `build_floors_and_stairs`, `_add_top_storey_ceilings`
  and `build_section` already consume correctly;
- `check_room_support` counts a declared void as *supported by design* and instead
  checks that the void's span is within a plausible beam span, converting a workaround
  into a real check;
- `plan2d` draws it with the diagonal hatch the contractor's own sheets use.

**T1-2 — There is no light well, only a corridor with a floor in it.**

`meta.views` includes `{"name": "gieng_troi", "room_id": "hall_stair"}` — the light-well
view. `hall_stair` is a 955 × 4000 mm `hall` beside the stair, and it receives a floor
slab on all seven levels like any other room. The published "light well" render is a
corridor. `roof.voids` can open the *sky* above it, but nothing opens the *floors*
through it, so the shaft the whole core is organised around does not exist in the model.

T1-1's `voids` construct solves this too: a light well is a void repeated on every
level. Worth calling out separately because it is the design motif of both shipped
designs, and because the SKILL.md currently advises the opposite workaround — *"rooms
simply aren't tiled over that footprint on any storey"* — which forfeits floor, wall and
section geometry around the shaft rather than modelling it.

**T1-3 — Nothing can exist above the topmost roof.** Ledger (i): the rooftop lift plant
room (`Ô KỸ THUẬT THANG MÁY`, +23.800 → +25.800) "is a structure on top of the roof,
which the schema cannot represent (there is no level above the topmost roof)." Modelled
by roofing over the lift shaft instead. Same class of problem as T1-1: the storey model
is a strict stack of full-plot slabs.

**T1-4 — The 12-value room-type enum collapses meaning the drawings depend on.** The
ledger carries an entire approximation table: altar room (`P.THỜ`) → `living`; roof
terrace (`SÂN THƯỢNG`) → `balcony`; corridor (`HÀNH LANG`) → `hall`; combined kitchen +
dining → `kitchen`. `type` is not cosmetic — it drives floor material
(`floor_material_key`), furniture (`plan_room`), the daylight check
(`HABITABLE_TYPES`), plan fill colour (`ROOM_FILL`), balcony parapets, ceiling
suppression and interior camera selection. Collapsing five real programmes into `hall`
means 21 of the contractor model's 62 rooms are one undifferentiated grey.
`contractor-as-drawn` needs at minimum `terrace`, `wc`, `utility`/`laundry`,
`circulation` and `void`; the enum should grow, with each new value stating explicitly
which of those six behaviours it selects.

**T1-5 — No site orientation, so every shadow in every deliverable is fiction.** The sun
rig is hardcoded at `(55°, 0, 35°)` in `build_environment`, the north arrow is hardcoded
to −y in `_north_arrow`, and the schema has no north angle. The ledger has to carry a
standing disclaimer: *"Shadows in these renders are decorative and must not be read as
daylight or solar analysis."* A `site.north_deg` field feeding the sun rotation, the
north arrow and (eventually) a real solar position for a date/latitude is a small change
that converts a permanent disclaimer into a feature — and for a 4 × 25 m tube house
where daylight is *the* design problem, it is the difference between a picture and an
analysis.

**T1-6 — Two thirds of the rooms are empty and every object is the same tan.**
`placement.plan_room` handles six of twelve room types. Measured: **19 of 62** rooms
furnished in `contractor-as-drawn` (53 items), **16 of 41** in `tubehouse-dream`.
`procedural_furniture.build_item` fetches `get_material(style, "furniture")` once and
paints beds, sofas, tables, chairs, counters and WCs with it. Two independent fixes,
both cheap: (a) plan the missing types (`hall`, `storage`, `garage`, `balcony` — a
console, shelving, a car block, a planter and two chairs each), (b) key the material off
`item.kind` so a mattress, a timber top and a porcelain WC are not the same colour.
This was flagged in the 2026-08-08 review as open and remains open.

**T1-7 — Carried forward, still unclosed from the second pass.** Per-room ceiling
height; wall-thickness overrides (`EXT_THICKNESS`/`INT_THICKNESS` are still module
constants, so a 150 mm partition is unsayable); floor/wall finishes; per-room furniture
override or suppression; `meta.style` still an enum with exactly one member; no
textures, no UVs, no HDRI world (the sky is a flat colour propped up by a 25 W fill
light).

---

### Tier 2 — What separates a brief from a construction set

**T2-1 — There is not one dimension on any drawing.** The plans carry two dimension
lines: overall plot width and overall plot depth. No room dimensions, no wall-to-wall
chains, no opening positions along a wall, no sill/head heights annotated on elevations,
no level heights on sections (the level lines are labelled with the storey *name*, not
its elevation). `title_block` says "Scale 1:100 @ A3" but the SVG carries only a
`viewBox` and is stretched to fit the PDF page, so the printed scale is whatever the
page gives it — the stated scale is not true.

Everything needed is already in `CompiledModel`. A dimension-chain generator over
each storey's wall coordinates, plus per-opening offset dimensions and numeric level
annotations on elevations/sections, is pure Python over data that already exists, and it
is the single largest step from "brief" to "buildable."

**T2-2 — Sections cut at the plot centreline, always.** `write_sections` hardcodes
`x = plot_width/2` and `y = plot_depth/2`. For `contractor-as-drawn` the long section
lands at x=1980 inside the 3005 mm stair shaft — which happens to be informative, by
luck rather than choice. The cut position (and the ability to emit more than two
sections) should be spec-driven, the same way `meta.views` drives the render gallery.
`build_section(model, axis, position_mm)` already takes the parameter; only the caller
and a schema field are missing.

**T2-3 — Elevations project walls and openings only.** No roof, no balcony parapets, no
railings, no stairs, no neighbour context. On a tube house whose facade *is* six stacked
balconies, the elevation omits the balconies. Folded into T0-2's rewrite, since a
correct projection has to consume all of them anyway.

**T2-4 — The flagship design has no PDF.** `spec/briefs/` holds only
`tubehouse-dream.json`, so `homedesign pdf designs/contractor-as-drawn.json` exits 1
with "brief copy not found," and `deliverables/contractor-as-drawn/` has `png/`, `gltf/`
and `viewer/` but no `pdf/`. The brief copy is hand-authored JSON with no generator, no
template and no schema. A `homedesign brief --init <spec>` that scaffolds
title/subtitle/narrative/requirements from the compiled model would remove the manual
step that is currently the reason the deliverable is incomplete.

**T2-5 — Still no IFC.** Deliberately deferred twice, and still the one format DXF
cannot carry. `CompiledModel` holds everything IfcWall/IfcSlab/IfcDoor/IfcWindow/
IfcSpace/IfcStair need. Not urgent, but it is the difference between "drawings someone
retypes" and "a model someone opens."

---

### Tier 3 — Pipeline, platform, hygiene

**T3-1 — Replace 101 boolean modifiers with the rectangle subtraction the repo already
wrote.** `build_walls` creates a cutter box per opening and applies an EXACT-solver
boolean per opening — 101 of them for `contractor-as-drawn`, inside the ~18 minutes of
non-render scene-build time in that 1,450 s run. Meanwhile `rects.py` opens with:

> *"Pure axis-aligned rectangle subtraction. … No booleans — deterministic,
> artifact-free geometry."*

…and is already used for floor slabs, roof voids and section slabs. A wall with openings
is exactly the same problem in (span, height) space: `subtract_rects` over the wall's 2D
face yields up to four boxes per opening (under-sill, over-head, and the two jamb
piers), each a `make_box`. That removes the boolean solver from the build entirely,
makes wall geometry deterministic and unit-testable **outside Blender** for the first
time, and applies the codebase's own stated principle to the one place that still
violates it. This is the highest-leverage refactor in the repo: faster, simpler, more
testable, and more consistent, all at once.

**T3-2 — One shared `output/`, and publishing is a manual copy.** Every design writes
into `REPO_ROOT/output`; there is no `--out` on any subcommand. Filenames are prefixed
by model name so artifacts do not collide, but `output/pdf/img/` is shared, two designs
cannot build concurrently, and moving finals into `deliverables/<slug>/` is a hand copy
that `activeContext.md` has logged as an open item on two separate sprints ("still holds
the red PDF/GLB — manual copy step, left for a deliberate publish"). Add `--out`, and a
`homedesign publish <spec>` that verifies every artifact's sidecar hash matches the
current model before copying — turning the provenance machinery already built into a
guarantee that a deliverable is internally consistent.

**T3-3 — `blender/` still has zero automated coverage (~1,000 LOC), and the last two
sessions show exactly which assertions matter.** Both the balcony fix and the camera fix
were verified by hand-written throwaway scripts. The `bpy` PyPI wheel makes these
CI-able. The invariants worth pinning are the ones that were checked manually and then
thrown away:

- the set of suppressed balcony walls equals `open_edges()` for every balcony;
- every mesh's bounding box lies within the plot ± tolerance;
- no floor slab covers a declared floor void;
- every camera position lies inside the room it claims to depict;
- object count for a fixture model is stable.

Plus golden-file tests for SVG/DXF — pure text, essentially free, and they would have
caught T0-1 and T0-2 the day they shipped.

**T3-4 — The check registry is geometric, not code-compliance.** Five rules exist and
fire correctly, but:
- `check_habitable_daylight` accepts *any* window on *any* touching wall — a window onto
  an interior hall counts as daylight. There is no window-area-to-floor-area ratio (most
  codes want ≥ 1/8 to 1/10), and no distinction between direct and borrowed light.
- **No stair headroom check.** A U-return under a 3,200 mm mezzanine can hold a Blondel
  flight and still have a beam in your forehead; the model has treads, storey heights and
  floor voids, so 2,000 mm clear headroom over every tread is directly computable. This
  is a genuine buildability risk in both shipped designs.
- No minimum corridor width, no WC ventilation rule, no balcony parapet height check
  against the model (the 1,100 mm is a Blender-side constant, unvalidated).

Since the registry makes adding a rule a two-line change, this tier is unusually cheap
per unit of value.

**T3-5 — Small, real, and each a one-liner:**
- A `roof` without `type` **passes schema validation** (the roof object has no `required`
  list) and then raises a bare `KeyError: 'type'` from `_derive_roof` — the one place
  where a malformed spec escapes the structured-error path. Add `"required": ["type"]`.
- `homedesign build --floor N` is declared and **never read** by `cmd_build`. Remove it
  or implement it.
- `cmd_compile` creates `output/compiled` and then never uses the variable
  (`_write_model_json` makes its own).
- `render_profiles.py`'s module docstring still says *"`final` promotes EEVEE Next … as
  the full-quality path"* — reverted on 2026-08-08 and contradicted by `AGENTS.md`, the
  orchestrator comment and a regression test. The one remaining place where a reader is
  told the wrong engine.
- `orchestrator._CANDIDATES` hardcodes `C:/Users/tukum/Blender/...` as the first two
  entries. Harmless (`BLENDER_CMD` and PATH win), but it pins shared source to one
  machine; a `BLENDER_SEARCH_PATH` or a small `blender.paths` config would generalise it
  without losing the deliberate 4.1-before-4.5 ordering, which must stay.

---

## Approaches Considered

**(A) Fix the three Tier-0 defects and re-publish.** ~1 day. Room names + XML escaping,
the elevation projection rewrite, the STALE badge. Makes the existing deliverables
honest. Does not add a single capability.

**(B) Tier 0 + the `voids` construct (T1-1/T1-2/T1-3).** ~2–3 days. Closes the largest
documented fidelity concession, lets `contractor-as-drawn` be re-authored without
`SÀN GIẢ`, and makes the light well real. The drawings become correct *and* depict the
right building.

**(C) B + dimensioning and the brief generator (T2-1, T2-2, T2-4).** ~1 week. Takes the
output from "a nice brief" to "a set someone can build from," and completes the
contractor deliverable.

**(D) Go wide on realism first** — assets, textures, HDRI, furniture coverage (T1-6,
T1-7). Most visible per hour, but it makes prettier pictures of drawings that are
currently blank. Wrong order.

**(E) Refactor-first: booleans → rectangle subtraction (T3-1), then `bpy`-wheel tests
(T3-3).** Genuinely valuable and unusually clean, but it fixes nothing a user sees.
Best carried *alongside* (B), since the voids work touches `build_floors_and_stairs`
and `build_walls` anyway.

**Recommendation: (C), sequenced as three sprints, with (E) folded into Sprint 2.**

## Suggested Roadmap

**Sprint 1 — Make the drawings tell the truth.** (Tier 0, ~1 day, pure Python, fully
testable without Blender.)
1. `_resolve_rooms` passes `name`; XML-escape helper in `plan2d`/`elevation`; test with
   an `&`-bearing room name.
2. Rewrite `build_elevation` as a real orthographic projection: building-derived plane,
   all wall/opening/parapet/roof/stair primitives, painter-sorted, silhouette outline.
   Regression test asserting the north elevation of `contractor-as-drawn` contains
   > 0 walls and > 0 openings — it fails on today's code.
3. Badge `STALE` per image in `_gallery_pages`; test a mixed fresh/stale page.
4. Sweep T3-5's one-liners.

**Sprint 2 — Teach the spec to say "void", and drop the boolean solver.**
5. `storeys[].voids[]` → `Storey.floor_voids`; `check_room_support` treats a declared
   void as supported and range-checks its span; hatch it in plan; re-author
   `contractor-as-drawn` without `SÀN GIẢ` and make the light well a real shaft.
6. Rooftop structures (T1-3): a storey above the topmost roof, or an explicit
   `roof.structures[]`.
7. Room-type enum growth (T1-4) with each value's six behaviours stated.
8. `build_walls` via `rects.subtract_rects` (T3-1); first pure unit tests of wall
   geometry.
9. First `bpy`-wheel tests (T3-3), starting with the balcony/void/camera invariants that
   were verified by hand this month.

**Sprint 3 — From brief to construction set.**
10. Dimension chains on plans; numeric levels and opening heights on elevations/sections
    (T2-1); make the stated 1:100 either true or unstated.
11. Spec-driven section cuts (T2-2).
12. `homedesign brief --init` + the `contractor-as-drawn` PDF (T2-4).
13. `--out` and `homedesign publish` with hash verification (T3-2).
14. `site.north_deg` (T1-5); furniture coverage and per-kind materials (T1-6).

IFC (T2-5), textures/HDRI and the asset library (T1-7) ride behind this, on their own
merits.

## Assumptions Adopted

Recorded per the unattended-mode instruction; each is the answer I would have
recommended had I been able to ask.

1. **A drawing that is blank is worse than a drawing that is ugly.** Tier 0 outranks
   every realism and performance item, even though the renders are the visible half of
   the product.
2. **Elevations get rewritten, not patched.** Widening the coplanarity tolerance would
   make the setback case *look* fixed while still omitting every opening one room
   inboard. The definition is wrong, so the producer is replaced.
3. **Voids belong on the storey, not as a room type.** `storeys[].voids[]` mirrors
   `roof.voids` exactly, keeps a void out of the room schedule and the area take-off
   (where a fake room currently inflates GFA), and needs no new enum value.
4. **`check_room_support` stays, and gets stricter.** A declared void is supported by
   design; an *undeclared* 0 %-coverage room stays an error. The check is not weakened,
   it is given the vocabulary it was missing.
5. **The boolean → rectangle-subtraction refactor is in scope for Sprint 2**, because
   the voids work already touches the same two functions and because it moves wall
   geometry into the pure, testable half.
6. **Blender 4.1 legacy EEVEE stays pinned.** Nothing here revisits the engine decision;
   `_CANDIDATES` ordering and its regression test are untouchable without new hardware.
7. **Backwards compatibility remains required.** Every spec in `spec/` and `designs/`
   must keep compiling; schema growth is additive with preserved defaults. Output will
   change — elevations gain content, plans gain real labels — and that is the point.
8. **`contractor-as-drawn` is re-authored, not re-measured.** Removing `SÀN GIẢ` and
   modelling the light well are spec edits against the existing measured envelope; no
   claim about the drawings' dimensions changes, and the fidelity ledger is updated to
   mark (h) and (i) resolved rather than rewritten.
9. **This document changed no code.** The only writes this session were a temporary
   drawing set into a throwaway temp directory for timing.

## Out of Scope

Curved, diagonal or non-orthogonal geometry; structural or code certification; MEP
routing; cost estimation; multi-user or cloud service; site survey / photogrammetry
import; GPU rendering on this machine; FreeCAD's return.

## Open Questions

1. **Should a void be a storey-level rectangle or a first-class multi-storey volume?**
   Rectangles reuse everything that exists today and cover both shipped designs. A
   volume spanning levels is the more honest model (a light well is one object, not
   seven) and would carry its own walls and glazing. Recommendation: rectangles now,
   volumes only if a design needs the shaft's own envelope.
2. **Should the elevation projection hide or outline what is behind?** Painter-sorted
   solid fill is simplest and matches the existing section convention ("everything behind
   the cut is omitted by design"). Architects usually want the *hidden* profile dashed.
   Recommendation: solid now, dashed hidden lines as a later flag.
3. **Does the printed 1:100 need to become true?** Making it true means fixed-size SVG
   output and a PDF page layout that respects it, which conflicts with today's
   fit-to-page behaviour. Recommendation: emit a true-scale variant for the DXF/print
   path and drop the scale text from the fit-to-page SVG rather than print a false claim.
4. **Is the audience the architect, the contractor, or the owner?** Sprint 3's ordering
   turns on it: dimensions serve the contractor, the brief PDF serves the architect, the
   web viewer serves the owner. All three are currently half-served.
5. **Should `homedesign` gain a `verify` subcommand?** Same question the last brainstorm
   asked and it is now overdue — three sessions running have hand-written throwaway
   scripts to check name propagation, elevation content, camera containment and mesh
   containment. Promoting them into the tool would have surfaced T0-1 and T0-2 without a
   brainstorm.

## Suggested Next Step

Run `/plan` on **Sprint 1**. It is three pure-Python fixes plus a one-liner sweep, none
of it needs Blender, all of it is testable to a standard that provably fails on today's
code, and it stops the tool shipping blank sheets and machine-readable IDs to a human
audience. Suggested plan title: *"homedesign drawing truth: land the room names, project
real elevations, and badge staleness per render."*
