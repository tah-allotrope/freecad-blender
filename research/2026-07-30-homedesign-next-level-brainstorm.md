---
title: "homedesign — Taking the Spec→Plans→Renders→Brief Pipeline to the Next Level"
date: "2026-07-30"
type: "brainstorm"
depth: "deep"
source_request: "Analyze the project's current state, codebase, docs and architecture; brainstorm what improvements, features, refactors, architectural changes or optimizations would take it to the next level."
slug: "homedesign-next-level"
mode: "unattended (no interview — recommended answers adopted and recorded under Assumptions Adopted)"
---

# Brainstorm: homedesign — Taking the Spec→Plans→Renders→Brief Pipeline to the Next Level

## Problem & Why Now

`/homedesign` works end-to-end today: a JSON spec compiles to per-storey SVG/DXF plans, a
headless Blender Cycles scene, a 9-view render gallery, and a 21-page A3 architect brief.
The last plan (`plans/2026-07-06-tubehouse-dream-home-plan.md`) closed all five phases and
produced a real deliverable for a real house.

That's exactly the moment the pipeline stops being judged on "does it run" and starts being
judged on "is the output *right*, is it *fast enough to iterate*, and does it *look like an
architect made it*." On all three, this session found concrete, verifiable gaps — including
several where the tool silently emits geometry that could never be built.

This brainstorm is grounded: every claim below was checked against the code, the compiled
model, the rendered PNGs, or the test suite in this session. Line references are to the
current working tree (`bdef10d` + untracked `.agents/`).

## Current State

- **~2,800 LOC Python**, cleanly split: pure/testable (`compiler`, `model`, `placement`,
  `plan2d`, `validate`, `pdf`, `orchestrator`) vs. bpy-only (`blender/`). The separation is
  genuinely good and is what makes everything below tractable.
- **Compiler** (`compiler.py`, 384 LOC) is the strongest module: a sweep-line wall
  derivation that correctly handles mismatched room rows, relative placement resolution
  with cycle detection, structured `SpecError` output.
- **Tests**: 5 files, 44 tests, all pure-Python. Zero coverage of the ~600 LOC under
  `blender/`.
- **Delivery**: SVG + DXF + PNG gallery + A3 PDF brief. No IFC/BIM, no web viewer.
- **Hardware reality**: Intel i5-8250U (4c/8t, 2017 laptop) + Intel UHD 620. This is the
  binding constraint on everything render-related and it is not going to change by tuning.

### Evidence gathered this session

| Check | Result |
|---|---|
| `PYTHONPATH=src python -m pytest tests -q` | **collection error** — `ModuleNotFoundError: ezdxf` |
| same, `--ignore=tests/test_plan2d.py` | 39 passed in 0.37s |
| `python -m unittest discover -s tests` (per AGENTS.md:27) | **FAILED (errors=1)**, same cause |
| Stair going, `tubehouse-dream` L0–L4 | **57–68 mm per tread** (code minimum ≈ 250 mm) |
| Openings sharing one wall | `F0_W019` carries 2, both centred → **overlapping cuts** |
| Wall segments crossing the plot boundary | **63** |
| `output/pdf/tubehouse-dream-brief.*` | **27 MB HTML / 13.6 MB PDF** |
| GPU backend available to Cycles | **none** (UHD 620: no CUDA/OPTIX/HIP; oneAPI needs Arc) |
| Visual check of `_exterior_front.png` / `_exterior_aerial.png` | **building cropped out of frame** in both |
| CI / pyproject / lockfile / ruff config | none (`.ruff_cache/` exists, config doesn't) |

---

## Findings, Ranked

### Tier 0 — Correctness defects (the tool is confidently wrong today)

**T0-1 — Every staircase the tool has ever generated is unbuildable.**
`compiler.py:347-364` sizes treads as `stairwell_long_dimension / n_risers`. For
`tubehouse-dream` that is a ~1.3 m deep shaft divided by 19–23 risers → a **57–68 mm going**.
A 19-riser straight flight physically needs ~5.3 m of run. `validate_compiled`
(`validate.py:34-45`) checks only that the shaft is ≥ 900 mm *wide*, so nothing catches it.
The plans, the renders and the PDF all show a ladder presented as a staircase.
*Fix:* a real stair generator — pick straight / L / U-return with landings from the shaft
aspect ratio — plus validation rules (going ≥ 250 mm, riser ≤ 190 mm, 600 ≤ 2R+G ≤ 640,
headroom ≥ 2000 mm). Pure Python, fully unit-testable.

**T0-2 — There is no hole in the floor for the stair or the lift.**
`build_scene.py:78-91` emits a floor slab for *every* room on *every* storey, including
`stair` and `elevator`. The flight from L0 therefore terminates against L1's slab, and the
lift shaft is a stack of sealed boxes. The compiled model has no concept of a floor void.
*Fix:* add `floor_voids` to `Storey` (stair/lift footprints + any spec-declared void) and
subtract them from the slab above — reuse `roof.py:44-77`'s `_subtract_rects`, which already
does exactly this, deterministically and without booleans.

**T0-3 — Openings on a shared wall silently overlap; position can't be specified.**
`compiler.py:330` hardcodes `offset = (span - width) / 2` — every opening is centred, and
there is no overlap check. Verified on `tubehouse-dream` L0: a 3000 mm garage door
(offset 500–3500, head 2100) and a 1000 mm transom window (offset 1500–2500, sill 1800)
land on the same wall — the window is cut *inside* the door hole, glass pane floating in
the void. This also makes "two windows on the street facade" inexpressible.
*Fix:* spec-level `offset_mm` / `align: center|start|end`, plus an overlap rule in both
plan and elevation (X-span × Z-span) per wall.

**T0-4 — `rot_deg` is a loaded gun pointed at the door-leaf bug that was already fixed
once.** `placement.py` emits `rot_deg=0` for every item, so the branch at
`procedural_furniture.py:21-23` never fires. When it does, it rotates via
`obj.rotation_euler` on a mesh whose world position is baked into its vertices with the
object origin at `(0,0,0)` — the precise failure that flung 32 door leaves across the scene
(`activeContext.md`, "Bugs found and fixed mid-plan" #1). The fix exists as
`geom.make_hinged_box`; the furniture path doesn't use it.
*Fix:* route all furniture rotation through baked-vertex rotation (or set object origins
properly everywhere and stop baking world position into meshes — the cleaner refactor).

**T0-5 — The test suite is red on a clean checkout.**
`ezdxf` isn't installed in the active interpreter, so pytest aborts collection and
`unittest discover` errors — a new contributor's first command fails. Compounding it:
tests import `src.homedesign.*` while the CLI requires `PYTHONPATH=src python -m homedesign`,
so the same package has two import identities. There is no `pyproject.toml`, no lockfile,
and `requirements.txt` ships `ifcopenshell` (heavy, unreachable from the CLI) but not
`pytest`.
*Fix:* `pyproject.toml` + editable install + one import root; dev extras; a GitHub Actions
job that runs the suite on push.

### Tier 1 — Highest leverage

**T1-1 — Render economics are the project's real bottleneck, and the current GPU line is a
no-op.** The 9-view final gallery took **11.3 h**. `build_scene.py:271-274` sets
`scene.cycles.device = "GPU"` inside a bare `try/except` — without setting
`preferences.addons["cycles"].preferences.compute_device_type` and enabling devices, this
does nothing at all, and it swallows the evidence. On UHD 620 there is no Cycles GPU
backend to enable, so the `activeContext.md` follow-up "investigate enabling actual GPU
rendering" is a dead end on this hardware. The levers that *do* exist, in impact order:
  1. **EEVEE for the preview profile** — seconds per view instead of minutes. This is the
     single biggest improvement to the `/homedesign` iteration loop, which currently
     burns Cycles at 24 samples just to check "did the room compile."
  2. **Split render from build**: a `homedesign render <name> [--view X]` subcommand that
     reuses the saved `.blend`. Today any re-render re-does boolean cuts on ~150 walls.
  3. **Per-view subprocess + resumability** (skip views whose PNG exists) so an 11-hour
     batch can't be lost wholesale — which already happened twice
     (`activeContext.md`, follow-up #2).
  4. **Detached long-render mode** with a log file and a poll command. The team learned
     this the hard way; encode it in the tool instead of tribal knowledge.
  5. **Cycles knobs never touched**: adaptive sampling + noise threshold, persistent data,
     explicit thread count, render-at-lower-res + denoise.
  6. **Instancing**: every box is a unique mesh — treads, chair legs, table legs, frames.
     Linked duplicates cut BVH build time and memory on a 5-storey model.
  7. `orchestrator.py:52` uses `capture_output=True`, buffering an 11-hour render's entire
     stdout and showing the user nothing until it ends. Stream it.

**T1-2 — Camera framing is the largest gap between "geometrically correct" and "looks
good."** Inspected directly: `tubehouse-dream_exterior_front.png` shows the building as a
cropped sliver with its top and bottom outside the frame and ~70% of the image empty
ground and sky; `_exterior_aerial.png` cuts the base off. `_build_exterior_front_camera`
(`build_scene.py:163-177`) is a stack of hand-tuned magic multipliers
(`plot_w * 3.0 + total_height * 1.2 + 6`, `-plot_w * 0.3`, `* 0.55`…) with a three-sentence
comment explaining why each was tweaked — a strong smell that the underlying method is
wrong, not the constants.
*Fix:* compute the scene bounding box and solve camera distance from sensor size and focal
length with a margin (the analytic equivalent of `camera_to_view_selected`). Deterministic,
no magic numbers, correct for any plot. The same applies to `_build_room_camera`
(`build_scene.py:190-220`): fit the room's *furnished* bounding box. Verified consequence
of not doing so — in `tubehouse-dream_living.png` the dining table and four chairs that
`placement._plan_living` genuinely placed sit behind the camera, which is why the shot
reads as a near-empty room.

**T1-3 — Realism has a hard ceiling: no textures, no HDRI, no context.**
`materials.py` is 12 flat Principled BSDF colours in a single style, no UVs, no maps.
Renders read as untextured massing studies. Meanwhile the repo *already* has BlenderMCP
wired with PolyHaven/Sketchfab tools (`.claude/mcp.json`, `AGENTS.md:35-64`) and it is not
connected to the pipeline at all.
*Fix (offline asset cache, so nothing breaks without a network):* HDRI world lighting —
which would let the fake "Fill" light be deleted outright rather than nursed at 25 W; PBR
textures with proper UV projection on floors/walls/roof; **parapets and railings on
`balcony` rooms** (the aerial shows a 5-storey open roof terrace with no edge protection);
**neighbour party-wall massing + a street strip**, since a sandwiched tube house rendered
free-standing in a green field is architecturally misleading; a real furniture asset
library keyed by `FurnitureItem.kind`, with the procedural blocks kept as fallback.

**T1-4 — The spec can't express what people actually ask for.**
No `name` on rooms (plans and the PDF schedule label rooms `master_f3`, not "Master
Bedroom"); no per-room ceiling height, floor finish, or furniture override; no opening
position (T0-3); no window/door style. Wall thicknesses, storey height and stair geometry
are module constants (`compiler.py:20-24`), so a 150 mm partition or a brick wall is
unspecifiable. `meta.style` is an enum with exactly one member — it is decoration.
*Fix:* an additive schema v2 with a version field, all current defaults preserved so every
existing spec still compiles.

**T1-5 — Validation doesn't enforce the rules the skill doc promises.**
`.claude/skills/homedesign/SKILL.md:41-50` states that every room must be reachable via a
chain of doors from an exterior door, "or the design will look right but not compile as a
livable home" — **nothing checks this.** Also unchecked, all cheaply computable from
`CompiledModel`:
  - habitable rooms (bedroom/living/kitchen/office) with no window → daylight failure;
  - bathrooms/kitchens with no door at all;
  - upper-storey rooms cantilevered over an untiled void (unsupported floor);
  - stair/lift shafts that don't stack vertically across storeys;
  - storeys listed out of level order — `base_z` accumulates in *list* order
    (`compiler.py:36-59`) and `validate.py:56-67` slices `storeys[:-1]` assuming sorted
    input; nothing sorts or checks;
  - the 63 wall segments crossing the plot boundary — rooms are bounds-checked, walls are
    not, so a "4.0 m" tube house is really 4.2 m wide. On a sandwiched urban lot that is
    the difference between legal and not.
*Fix:* a `checks.py` rule registry, each rule returning `SpecError`s, wired into
`validate_compiled`; add `--json` error output so the agent self-correction loop in
SKILL.md step 3 can consume it structurally instead of parsing prose.

### Tier 2 — Deliverable quality

**T2-1 — The 2D output is a diagram, not an architectural drawing.**
Missing: door swing arcs, window symbols, wall hatching, room *name* labels, per-room
dimension strings, north arrow, scale bar, title block / sheet frame, furniture in plan.
Separately, the SVG and DXF are **vertically mirrored relative to each other** — SVG y grows
downward while CAD y grows upward, and `plan2d.py:129-158` writes model mm straight into
DXF. Also `msp.add_text(...).set_placement((cx, cy))` doesn't centre the label.
*Fix:* one shared draw model → two renderers, so symbols are authored once; flip the DXF
y-axis (or document the convention loudly); add a sheet/title-block layer.

**T2-2 — The PDF is 13.6 MB and paginates wrong.**
`_img_data_uri` (`pdf.py:57-59`) base64-inlines every full-resolution PNG into the HTML,
producing a **27 MB** intermediate. Plan pages spill onto a second A3 sheet
(`activeContext.md` #3) because the generated SVG carries hardcoded pixel `width`/`height`
attributes that CSS `max-width` doesn't beat in print — dropping them and keeping only
`viewBox` fixes it directly.
*Fix, plus real additions:* downscale gallery images for print; a **door and window
schedule** table (fully derivable, and standard architect deliverable); **quantity
take-off** — GFA per storey, wall lengths by type, opening counts; page numbers and a
footer; and a shareable HTML variant with images as sibling files.

**T2-3 — Deliverable formats stop short of what an architect wants.**
IFC4 is the interchange format for anyone downstream (structural, MEP, BIM). It exists in
the repo as `src/ifc_export_utils.py` (276 LOC) — but it targets the *retired* spec format,
is unreachable from the CLI, and drags `ifcopenshell` into `requirements.txt` for nothing.
*Recommendation: rewire it to `CompiledModel`* (IfcWall / IfcSlab / IfcDoor / IfcWindow /
IfcSpace / IfcStair). It's the one thing DXF fundamentally cannot carry, and the model
already holds everything needed. If that's not wanted, delete the file and the dependency —
the current state is the worst of both.
*Also cheap and high-impact:* export glTF/GLB from the same Blender run and ship a
self-contained three.js walkthrough page. An interactive model beats nine static stills,
and it's a publishable Artifact.

### Tier 3 — Platform and hygiene

**T3-1 — Documentation has drifted badly from the code.**
  - `AGENTS.md:4` describes the retired FreeCAD pipeline and `spec/floorplan-spec.json`
    (gone); `:18` points at `run.sh` (**deleted**); `:33` points at `freecad-mcp-guide.md`
    (**doesn't exist**); `:27` prescribes `unittest` for what is a pytest suite.
  - `plans/PROGRESS.md` is a March-2026 FreeCAD status report presented as current.
  - `docs/HOW_TO_RUN.txt`, `docs/plan-floor-1.md` and lessons 1–6 of
    `docs/lessons-learned.md` are all FreeCAD-era; only the final lesson applies today.
  - **`.agents/skills/homedesign/SKILL.md` is a stale fork** of the `.claude/` copy — it has
    already lost `meta.views`, roof `rect`/`voids`, the opening `side` hint, and the entire
    PDF section. It's untracked (`?? .agents/` in git status). Two copies of a spec
    cheat-sheet is a correctness hazard for whichever agent reads the wrong one.
  - **SKILL.md:57-64 sends user designs to `output/specs/<slug>.json`** — a directory that
    doesn't exist, under a tree that is **gitignored**. Every design a user authors would
    be untracked and disposable; the one real design lives at `designs/tubehouse-dream.json`
    instead. This is a live data-loss path.
  - `output/` still carries ~50 FreeCAD-era artifacts (`fcstd/`, `obj/`, `ifc/`, `stl/`,
    `test.ifc`, `architect_package_manifest.json`).
  - `orchestrator.py:17-21` hardcodes `C:/Users/tukum/...`; `geom.py:61` has a dead
    `evaluated_depsgraph_get()` call.

**T3-2 — Zero test coverage of the Blender half, and there's a ready way to get it.**
The `bpy` PyPI wheel runs Blender headless as a plain Python module, so `blender/` becomes
CI-testable: build from a fixture model and assert object counts, assert **every mesh bbox
lies inside the plot ± tolerance** (this is exactly the ad-hoc debug script that caught the
32 flung door leaves — make it a permanent regression test), assert no slab covers a stair
void, assert each camera actually frames the building. Add golden-file tests for SVG/DXF
and one compile→plans→PDF smoke test.

---

## Approaches Considered

The ranking above depends on what this project is *for*. Three readings:

- **(A) A personal tool for one house.** Then polish `tubehouse-dream`, fix the stairs so
  the brief isn't embarrassing, and stop. Cheapest; caps the project's value at one PDF.
- **(B) A general "idea → architect brief" product.** Justifies validation rules, an asset
  library, IFC, and a web viewer. Highest ceiling, largest investment.
- **(C) An agent-facing design DSL** — the thing `/homedesign` is literally written to be.
  Prioritises machine-readable errors, expressive spec, and a *fast* preview loop over
  photorealism.

**Adopted: a B/C hybrid.** The skill file is written for agent consumption (C), while the
PDF brief is a human product deliverable (B) — and both are blocked by the same Tier 0
correctness defects. The roadmap below front-loads what serves both, and defers
photorealism (pure B) to last.

Rejected: a from-scratch rewrite onto an existing BIM kernel (IfcOpenShell geometry,
FreeCAD Arch). The compiler is the best-tested part of this repo and its rectilinear
constraint is what makes everything deterministic; re-platforming would trade that for
generality nobody has asked for. This repo already deleted FreeCAD once, deliberately.

## Suggested Roadmap

**Sprint 1 — Correctness and a green suite** (all pure Python, all unit-testable, no
Blender needed): T0-5 packaging/imports/CI → T0-1 real stairs → T0-2 floor voids → T0-3
opening placement + overlap rules → T0-4 furniture rotation → T1-5 validation rule
registry. Exit criterion: `tubehouse-dream` recompiles with a buildable stair, a stair
void, non-overlapping openings, and every validation rule green — or with honest errors.

**Sprint 2 — Iteration speed and framing** (the two things that make everything after it
cheaper): EEVEE preview profile → `render` subcommand reusing the `.blend` → per-view
resumable/detached rendering with streamed progress → analytic camera fit for exterior and
room views. Exit criterion: a preview loop measured in seconds, and every gallery image
containing the whole building.

**Sprint 3 — Deliverable** : plan2d drawing symbols + title block + DXF axis fix → PDF size,
pagination, schedules and take-off → IFC4 from `CompiledModel` → glTF + web viewer → docs
consolidation (single SKILL.md source, AGENTS.md rewrite, archive the FreeCAD-era files,
tracked `designs/` directory).

Realism (T1-3: HDRI, textures, assets, neighbours, parapets) rides alongside Sprint 3 —
it's the most visible change but the least dependency for anything else, and on this
hardware it is gated by Sprint 2's render economics regardless.

## Assumptions Adopted

Recorded per the unattended-mode instruction — each is the answer I would have recommended
had I been able to ask:

1. **Product direction: B/C hybrid** (agent-facing DSL + human-facing brief), not a
   single-house personal tool. Justification above.
2. **GPU rendering is off the table on this machine** — UHD 620 has no Cycles backend.
   Treat `activeContext.md` follow-up #1 as answered "no" and pursue EEVEE + workflow
   changes instead. If the user later moves to an NVIDIA/AMD machine, T1-1 item 1 becomes
   optional rather than essential.
3. **Rectilinear geometry stays.** Curved/diagonal walls and split levels remain out of
   scope; they'd invalidate the sweep-line wall derivation.
4. **`src/ifc_export_utils.py` should be rewired, not deleted** — IFC is the highest-value
   format the pipeline doesn't yet produce. Deleting it is the acceptable alternative;
   leaving it as-is is not.
5. **Backwards compatibility is required** for every existing spec in `spec/`. Schema
   changes are additive with preserved defaults.
6. **`.claude/skills/homedesign/SKILL.md` is the source of truth**; `.agents/` mirrors it
   (symlink or generated copy), never the reverse.
7. **User-authored specs belong in a tracked `designs/` directory**, not gitignored
   `output/specs/`.
8. This document does not modify any code — it is analysis only, per the brainstorm brief.

## Out of Scope

Curved/organic geometry; structural analysis or code compliance certification; cost
estimation; MEP routing; multi-user/cloud service; real-time collaborative editing;
photogrammetry or site-survey import; anything requiring FreeCAD's return.

## Open Questions

1. **Is a real stair worth its complexity?** A U-return flight with a landing changes the
   plan drawing, the floor void, and the room-area schedule. The alternative — validate and
   *reject* impossible stairwells, forcing the spec author to allocate a bigger shaft — is
   far cheaper and arguably more honest. Recommendation: ship the rejection rule in Sprint 1
   and the generator in Sprint 3, so no design is ever silently wrong in the meantime.
2. **How photoreal does this need to be?** The brief's job is to persuade an architect, and
   architects read massing studies fluently. Textures may matter less than parapets,
   neighbours and correct framing — which are cheap. Worth confirming before investing in
   an asset pipeline.
3. **Should `homedesign` own a `designs/` registry** (metadata, versioning, render history)
   or stay a stateless CLI over loose JSON files?
4. **Does the user want the web viewer as an Artifact**, or is the PDF the only artefact
   that matters to the audience?

## Suggested Next Step

Run `/plan` on **Sprint 1** — it is self-contained, entirely pure-Python, unblocks a green
CI signal, and eliminates every case where the tool currently produces confidently
unbuildable geometry. Suggested plan title: *"homedesign correctness pass: buildable stairs,
floor voids, opening placement, validation registry, packaged + green tests."*
