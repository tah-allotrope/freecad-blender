---
title: "3D Render of the Contractor's As-Drawn Scheme"
date: "2026-08-13"
status: "complete"
request: "Produce a family-facing 3D render of the contractor's newly-delivered drawing set, modelled exactly as drawn, using the existing homedesign pipeline."
plan_type: "multi-phase"
research_inputs:
  - "research/2026-08-13_contractor-scheme-3d-render-brainstorm.md"
  - "research/2026-08-12_tubehouse-lift-comparison.md"
---

# Plan: 3D Render of the Contractor's As-Drawn Scheme

## Objective

Encode the seven-level tube house drawn in the five contractor PDFs under `contractor/`
as a new `designs/contractor-as-drawn.json` spec, render a 12-view gallery plus an
interactive GLB web viewer, and commit the finals to `deliverables/contractor-as-drawn/`.
The audience is the client family, who have so far seen only 2D sheets and a written
review; the model must depict **the building the contractor actually drew**, not the
building the client's brief asked for, so the render carries evidentiary weight in the
programme discussion that follows.

## Context Snapshot

- **Current state:** `contractor/` holds five vector PDF sheets with no machine-extractable
  text. A prose review of them exists at `reports/2026-08-12-contractor-drawing-set-review.html`.
  `designs/tubehouse-dream.json` is the *client brief's* five-storey scheme — already
  compiled, rendered (9 views), exported to GLB and published to
  `deliverables/tubehouse-dream/`. The contractor's seven-level scheme exists only on paper.
  The `homedesign` pipeline has never ingested a real-world drawing set.
- **Desired state:** `designs/contractor-as-drawn.json` compiles clean and passes the check
  registry; `designs/contractor-as-drawn.measurements.md` records every dimension and the
  sheet it came from; `designs/contractor-as-drawn.fidelity.md` records every place the
  model departs from the drawing; a 12-view `final` EEVEE gallery, a GLB and a
  self-contained viewer exist; the finals are copied into
  `deliverables/contractor-as-drawn/`; `python -m pytest tests -q` and
  `ruff check src tests` both pass.
- **Key repo surfaces:**
  - `contractor/` — the five source PDFs (input, read-only)
  - `spec/homespec.schema.json` — the authoritative spec contract
  - `designs/tubehouse-dream.json` — structural exemplar to imitate (**not** to copy values from)
  - `src/homedesign/compiler.py` — wall derivation, floor voids, room-overlap/plot checks
  - `src/homedesign/checks.py` — the five-rule post-compile registry
  - `src/homedesign/stairs.py` — Blondel sizing; `straight` and `u_return` only
  - `src/homedesign/validate.py` — schema validation + inline stairwell/min-dimension checks
  - `src/homedesign/__main__.py` — the CLI (`compile`, `plans`, `build`, `render`, `pdf`)
  - `src/homedesign/orchestrator.py` — Blender discovery and launch
  - `src/homedesign/viewer.py` — `INLINE_GLB_LIMIT_BYTES = 8 * 1024 * 1024`
  - `tests/test_validate.py`, `tests/test_camera_placement.py`
  - `deliverables/README.md` — the finals layout contract
- **Out of scope:** any change to `spec/homespec.schema.json`, `src/homedesign/compiler.py`,
  `src/homedesign/checks.py`, `src/homedesign/stairs.py`, or anything under
  `src/homedesign/blender/`. No new render engine, camera kind, or view type. No A3 PDF
  brief and no `spec/briefs/contractor-as-drawn.json`. No second "brief-restored" variant
  spec. No modification or re-render of `tubehouse-dream`. No revision of
  `research/2026-08-12_tubehouse-lift-comparison.md`. No interpretation of setback, height
  or permit compliance — that stays in the existing review report. No `git commit` or
  `git push` unless the plan's owner asks for one.

## Environment & Conventions

- **Stack:** Python ≥ 3.11 (`pyproject.toml`), setuptools build backend, plain `pip`.
  Runtime deps: `jsonschema>=4.0`, `ezdxf>=1.0`, `pillow>=10.0`. Dev deps: `pytest>=8.0`,
  `ruff==0.15.7` (pinned exactly). Rendering requires **Blender 4.1.1** installed
  externally — it is not a Python dependency.
- **Setup:**
  ```bash
  pip install -e ".[dev]"
  ```
  PHASE-01 additionally needs a PDF library that is **deliberately not a project
  dependency** — install it into the environment but do **not** add it to `pyproject.toml`:
  ```bash
  pip install pymupdf
  ```
- **Build / Run:**
  ```bash
  homedesign compile designs/contractor-as-drawn.json
  homedesign plans   designs/contractor-as-drawn.json
  homedesign build   designs/contractor-as-drawn.json --profile final --gltf
  homedesign render  designs/contractor-as-drawn.json --profile final --view exterior_front
  ```
  `homedesign` is a console script declared in `pyproject.toml`
  (`homedesign = "homedesign.__main__:main"`). `python -m homedesign <args>` is equivalent.
  All output paths are hardcoded to `<repo root>/output/` — the command's working directory
  does not change where files land.
- **Test:** full suite:
  ```bash
  python -m pytest tests -q
  ```
  single test:
  ```bash
  python -m pytest tests/test_validate.py::test_contractor_as_drawn_passes_schema_validation -q
  ```
  Lint (must be clean before any commit; CI runs it):
  ```bash
  ruff check src tests
  python scripts/sync_skill.py --check
  ```
  `pyproject.toml` sets `pythonpath = ["src"]`, so no install is required for tests to import
  `homedesign`.
- **Conventions & traps:**
  - **Units: millimetres everywhere on the Python side, metres everywhere on the Blender
    side.** The `/ 1000` conversion happens exactly once, at the `src/homedesign/blender/`
    boundary. Every number written into the spec is an integer millimetre.
  - Design specs live at `designs/<slug>.json`, lower-case kebab-case slug. `meta.name` must
    equal the filename stem — every output filename derives from `meta.name`, not from the path.
  - `output/` is git-ignored and disposable; never hand-edit anything in it. `deliverables/`
    is tracked and is where finals are kept.
  - Geometry math stays in pure modules under `src/homedesign/`; only
    `src/homedesign/blender/` may import `bpy`. This plan adds no code to either.
  - Room `id` values and `meta.views[].name` values must be **ASCII, no diacritics** — ids are
    used as identifiers and view names become PNG filenames (`<meta.name>_<view name>.png`).
    Only the free-text `name` field carries Vietnamese diacritics.
  - JSON files must be written **UTF-8 without a BOM**. On Windows PowerShell,
    `Set-Content`/`Out-File` default to the system ANSI codepage or add a BOM; use
    `Set-Content -Encoding utf8NoBOM`, or write the file with Python
    (`Path(...).write_text(data, encoding="utf-8")`), or use a text editor set to UTF-8.
    A mis-encoded file makes `json.loads` fail or silently mangles every Vietnamese room name.
  - Ruff is pinned to `0.15.7`; a different version may disagree about formatting.
- **Repo map:**
  ```
  contractor/          the five source PDFs (input for PHASE-01)
  designs/             user-authored specs; the new spec + its two sidecar .md files go here
  spec/                homespec.schema.json (contract), examples/ (fixtures), briefs/ (PDF copy)
  src/homedesign/      pure Python: compiler, checks, stairs, validate, plan2d, elevation,
                       camera_fit, orchestrator, viewer, pdf, render_profiles, __main__
  src/homedesign/blender/  bpy-only layer: build_scene, materials, joinery, railings, roof,
                       procedural_furniture — launched headlessly, never imported by tests
  tests/               15 pytest files; test_validate.py and test_camera_placement.py matter here
  output/              git-ignored build artifacts: compiled/ svg/ dxf/ blend/ png/ gltf/ viewer/ logs/
  deliverables/        tracked finals, one folder per design (see deliverables/README.md)
  reports/             dated HTML review documents
  research/            dated markdown briefs
  plans/               dated markdown plans (this file)
  ```

## Research Inputs

- From `research/2026-08-13_contractor-scheme-3d-render-brainstorm.md`:
  - The contractor's set exercises almost exactly the features the compiler cannot express:
    a ~7.2° skewed rear boundary, a glazed cap over the light well, winder treads, and a
    rooftop lift plant room. The agreed response is to **approximate within today's schema and
    record every departure in a sidecar ledger** — no schema or compiler changes.
  - The `lửng` (mezzanine) needs no special construct: `height_mm` is per-storey and `base_z`
    accumulates, so it is simply `level: 1` with its own height. It satisfies
    `check_room_support` because level-0 rooms tile the full footprint beneath it.
  - The glass cap over the light well **must be modelled as a roof `void`, not as solid roof**.
    The renderer has no glass: a solid cap turns the shaft into an unlit slot and renders the
    core shot black. The void departs from the drawing in geometry to stay truthful in depiction.
  - Dimensions come from **reading the contractor's printed dimension chains at 8–16× zoom**,
    with vector measurement used only to fill gaps and cross-check. The printed figures are
    authoritative regardless of the sheets' plot scale.
  - Room names are **Vietnamese only**, exactly the strings on the sheets, for traceability
    back to the drawing set.
  - Deliverable is a 12-view `final` EEVEE gallery plus GLB plus self-contained viewer.
    Interiors accept the existing wide-lens camera; no cutaway view kind is to be built.
  - There is no north angle anywhere in the schema and no north point on the sheets, so the
    sun rig is fixed and **shadows in this render are decorative, not solar**. This must be
    stated in the ledger and must not be presented as daylight analysis.
- From `research/2026-08-12_tubehouse-lift-comparison.md`:
  - That brief was written against a 1000 × 1400 mm (1.4 m²) lift shaft and five stops. The
    contractor's drawn shaft measures roughly 1500 × 1600 mm (2.4 m²) across seven stops, and
    the roof carries a machine room, contradicting the brief's machine-room-less
    recommendation. The premise change is **noted in the ledger only**; revising that research
    document is explicitly out of scope for this plan.

## Assumptions and Constraints

- **ASM-001:** The plot is treated as an axis-aligned rectangle with the **front (street)
  boundary at `y = 0`** and `y` increasing toward the rear, `x = 0` at the west party wall.
  This matches `designs/tubehouse-dream.json`, whose front terrace occupies `y` 0–11000 and
  whose core sits at `y` 11000–14700.
- **ASM-002:** Plot dimensions. — **BINDING DEFAULT:** `plot_width_mm: 3960`,
  `plot_depth_mm: 25000`. The 25000 figure is the head of the drawn chain 25000 / 22500 /
  19500 and matches `designs/tubehouse-dream.json` exactly; 3960 is the measured frontage.
  If PHASE-01 reads different printed figures, use the printed figures and record the change
  in the measurements file.
- **ASM-003:** Storey count and identity. — **BINDING DEFAULT:** seven storeys, `level` 0
  through 6: `0` = trệt (ground), `1` = lửng (mezzanine), `2`–`5` = tầng 2–5, `6` = sân thượng
  (roof terrace, carrying the lift plant room and the stair/lift overrun). The single `roof`
  object goes on level 6 only.
- **ASM-004:** Storey heights come from Section A-A's level tags, read in PHASE-01. — **BINDING
  DEFAULT:** if a tag cannot be read, use 3400 mm for a residential storey and 2000 mm for
  level 6. The tags already read are `+17.200 / +20.600 / +23.800 / +25.800`, giving 3400 /
  3200 / 2000 mm for the top three intervals.
- **ASM-005:** Vietnamese room labels not legible on a sheet. — **BINDING DEFAULT:** use the
  nearest legible label from the equivalent room on another level, and mark the row
  `(inferred)` in `designs/contractor-as-drawn.measurements.md`.
- **ASM-006:** A dimension chain that does not close (parts do not sum to the stated overall).
  — **BINDING DEFAULT:** take the room-side (individual) figures, absorb the residual into the
  circulation/hall room so the level still tiles exactly, and record the residual in the
  measurements file. Never leave a sliver — a 30 mm gap becomes `room_overlap` or an unwanted
  floor void across seven levels.
- **ASM-007:** GLB exceeds `INLINE_GLB_LIMIT_BYTES = 8 * 1024 * 1024` in
  `src/homedesign/viewer.py`, so the viewer stops inlining it and emits a relative file
  reference instead. Seven levels is ~40% more geometry than the five-level
  `tubehouse-dream`, so this is likely. — **BINDING DEFAULT:** keep the viewer and ship
  `deliverables/contractor-as-drawn/viewer/contractor-as-drawn.html` alongside
  `deliverables/contractor-as-drawn/gltf/contractor-as-drawn.glb`, documenting in the ledger
  that the HTML must sit next to the GLB to work. Do not modify `viewer.py` to raise the limit.
- **ASM-008:** The published artifact's framing. — **BINDING DEFAULT:** purely presentational
  — a clean walkthrough for the family, with one sentence linking to
  `reports/2026-08-12-contractor-drawing-set-review.html` for the findings. Do not interleave
  review findings with the renders.
- **CON-001:** Renders **must** run on Blender 4.1's legacy EEVEE. `orchestrator._CANDIDATES`
  already orders 4.1 ahead of 4.5/4.2 and this ordering is pinned by
  `tests/test_orchestrator.py::test_blender_candidates_prefer_legacy_eevee_build`. Do not
  reorder it and do not "upgrade to the newest Blender". EEVEE Next (4.2+) miscompiles on this
  machine's Intel UHD 620 iGPU and renders every lit surface blood red — a white
  `0.92/0.91/0.88` wall comes out `(194, 34, 53)` regardless of view transform. Override
  discovery with the `BLENDER_CMD` environment variable if the wrong build is picked up.
- **CON-002:** There is **no GPU render path** on this machine. Cycles enumerates zero
  OPTIX/CUDA/HIP/oneAPI devices, so `--profile cycles` is CPU-only at ~169 s/view.
  `--profile final` (legacy EEVEE, 1920×1080, 256 samples) is ~30 s/view.
- **CON-003:** Every object in `spec/homespec.schema.json` sets
  `"additionalProperties": false`. There is no field anywhere in the spec for provenance,
  annotations, drawing references or notes. All such material must live in the two sidecar
  markdown files.
- **CON-004:** The room `type` enum is closed at 12 values: `bedroom, bathroom, kitchen,
  living, dining, hall, stairwell, garage, balcony, office, storage, elevator`. There is no
  altar room, plant room, terrace, shop or void type.
- **CON-005:** `site` accepts only `plot_width_mm` and `plot_depth_mm` — the plot is a
  rectangle. Walls are derived, never authored, and are always axis-aligned.
- **CON-006:** Roof `voids` are valid only on `"type": "flat"`; any other roof type raises
  `NotImplementedError` from `src/homedesign/blender/roof.py`.
- **CON-007:** One `stairs` object per storey (not an array), and it must reference a
  `stairwell`-typed room. Only `straight` and `u_return` flights exist.
- **CON-008:** `check_room_support` is a hard error, not a warning: every room above level 0
  must be ≥ 80% covered by the union of rooms on the level below.
- **DEC-001:** Model the scheme **exactly as drawn** — single-family throughout, no leased
  floors, no lockable second-floor lobby, rooftop plant room present.
- **DEC-002:** Approximate inexpressible geometry within today's schema; record every
  departure in `designs/contractor-as-drawn.fidelity.md`. No code changes.
- **DEC-003:** The light well is expressed **by omission** — leave its footprint untiled on
  every level. Floor slabs are emitted per-room, so an untiled footprint is automatically open.
- **DEC-004:** Punch a roof `void` over the light well; ledger the fact that the drawing shows
  a glazed cap (`ô kính lấy sáng`).
- **DEC-005:** The ~7.2° skewed boundaries collapse to the orthogonal plot rectangle; the
  tapering rear yard becomes untiled plot. Ledger entry.
- **DEC-006:** Winder treads become `"mode": "u_return"`. Tread count and riser are re-derived
  per storey height, so the model will not reproduce the drawing's copy-pasted stair block —
  itself a ledger entry.
- **DEC-007:** Room names are Vietnamese only; room ids and view names are ASCII.
- **DEC-008:** `--profile final`, legacy EEVEE, all 12 views. No Cycles pass.
- **DEC-009:** Accept the existing wide-lens interior camera. Build no cutaway view kind.
- **DEC-010:** Set `site.context: {"neighbours": true, "street_depth_mm": 6000}`. A tube house
  rendered free-standing in an open field is architecturally misleading.
- **DEC-011:** The spec must compile clean. Where a check fires, adjust the model minimally
  and record the adjustment in the ledger **and** flag it as a candidate review finding — a
  check failure on an as-drawn model is information about the drawing, not merely an obstacle.

## Specification

### S-1. PDF scale calibration

The sheets are labelled `TL : 1/100` but do not plot at that scale. Convert a measured PDF
point distance to real millimetres with:

```
mm_real = pt_measured × K
K = 43.0        (millimetres of real building per PDF point)
```

- `pt_measured` — a distance in PDF user-space points taken from the vector geometry.
- `K` — the calibration constant, established from two independent known dimensions on the
  sheets: 3950 mm printed across 91.8 pt, and 20900 mm printed across 485.6 pt; both give
  43.0 ± 0.1.
- A true 1:100 sheet would have `K = 25.4 / 72 × 100 = 35.28`. Since `43.0 / 35.28 = 1.219`,
  the sheets actually plot at about **1:122**, and anything scaled off the issued PDFs with a
  1:100 rule reads ~18% short. This is why **printed dimension strings are authoritative and
  `K` is only a cross-check**.
- Accept a vector-derived figure only when it agrees with a printed figure to within 1%.
  Otherwise take the printed figure.

### S-2. Stair fit — will the drawn shaft compile?

`src/homedesign/stairs.py` sizes every flight from the storey height. For storey height `H`
in millimetres:

```
n = max(2, round(H / 175))              number of risers
r = H / n                               riser height, mm      -> hard error if r > 190
g = max(250, 600 - 2r)                  going (tread depth), mm
```

- `n` — riser count; `175` is `TARGET_RISER_MM`.
- `r` — riser height; `stair_riser_too_tall` is raised when `r > 190`.
- `g` — going, from the Blondel relation `2r + g = 600` with a 250 mm floor.

Let `short = min(w, d)` and `long = max(w, d)` of the stairwell room's rect, in millimetres.
A U-return fits if and only if **both**:

```
short >= 1900
long  >= max(ceil(n/2) - 1, n - ceil(n/2) - 1) × g + max(900, (short - 100) / 2)
```

- `1900` is `MIN_URETURN_SHORT_MM`; `100` is `URETURN_WELL_MM` (the gap between flights);
  `900` is `MIN_FLIGHT_WIDTH_MM`.
- The two `ceil` terms are the tread counts of the lower and upper flights; the trailing term
  is the landing depth.

Worked example at `H = 3800`: `n = 22`, `r = 172.7` (passes ≤ 190), `g = 254.6`,
`ceil(22/2) - 1 = 10`, `22 - 11 - 1 = 10`. With `short = 3005`:
`long >= 10 × 254.6 + max(900, 1452.5) = 2546 + 1452.5 = 3998.5 mm`.
So a 3005 mm-wide stairwell needs at least **3999 mm** of run depth at a 3800 mm storey.
This is the single most likely compile failure in PHASE-02 — see RISK-02-01.

### S-3. Check-satisfaction procedure

Apply in this order when authoring each storey:

1. **Tile the level exactly.** Every room rect must be axis-aligned, non-overlapping, and
   inside `0 ≤ x ≤ plot_width_mm`, `0 ≤ y ≤ plot_depth_mm`. Leave exactly one deliberate
   untiled footprint: the light well.
2. **Stack the shafts.** The `stairwell` room and the `elevator` room must have byte-identical
   rects on all seven levels — `check_shaft_stacking` errors on any axis differing by more
   than 1 mm.
3. **Support every room.** Each room on level `L ≥ 1` must be ≥ 80% covered by the union of
   level `L-1` rooms. Since every level tiles its full footprint, this passes automatically
   unless a room overhangs the untiled light well.
4. **Daylight every habitable room.** `check_habitable_daylight` requires at least one
   `"type": "window"` opening on a wall touching each room of type `bedroom, living, kitchen,
   dining, office`. For an interior room, place the window against the light well:
   `{"type": "window", "between": ["<room id>", "exterior"], "side": "<n|s|e|w>"}`. A room
   edge not shared with another room is classified `exterior` by `_derive_walls`, which is
   what makes a light-well window authorable at all.
5. **Reach every room.** Level 0 needs at least one `door` with `"exterior"` in `between`.
   On every level, every room must be connected by a door chain back to the `stairwell` or
   `elevator` room. `bathroom` and `storage` rooms need doors too — they are checked for
   reachability even though they are not checked for daylight.
6. **Minimum dimension.** No room edge shorter than 600 mm (enforced in
   `src/homedesign/validate.py`).

## Phase Summary

| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Read every dimension off the five PDFs into a traceable measurement table | None | `designs/contractor-as-drawn.measurements.md` |
| PHASE-02 | Author the spec so it compiles clean and passes all checks | PHASE-01 | `designs/contractor-as-drawn.json`, updated `tests/test_validate.py` |
| PHASE-03 | Record every departure from the drawing | PHASE-02 | `designs/contractor-as-drawn.fidelity.md` |
| PHASE-04 | Build the scene, render 12 views, export GLB + viewer | PHASE-02 | `output/png/*.png`, `output/gltf/*.glb`, `output/viewer/*.html` |
| PHASE-05 | Commit the finals to the tracked deliverables tree | PHASE-03, PHASE-04 | `deliverables/contractor-as-drawn/**` |

## Detailed Phases

### PHASE-01 - Measure the Drawing Set

**Goal**
Produce a single traceable table of every dimension needed to author the spec, sourced from
the contractor's own printed dimension strings, with vector measurement as a cross-check.
This is the bulk of the work in the whole plan.

**Tasks**
- [ ] TASK-01-01: Install the scratch PDF library — `pip install pymupdf` — and confirm it is
      **not** added to `pyproject.toml`.
- [ ] TASK-01-02: Confirm the five sheets and their contents. Filenames contain spaces (and
      one contains a double space), so always quote them:
      `contractor/MB 1-LUNG-Model.pdf` (level 0 trệt + level 1 lửng),
      `contractor/MB 2-3-4-Model.pdf` (levels 2, 3, 4),
      `contractor/MB 5- MAI-Model.pdf` (level 5 + sân thượng),
      `contractor/MB MAI - MD-Model.pdf` (mái/roof plan + front elevation),
      `contractor/MC  A- A-Model.pdf` (Section A-A).
- [ ] TASK-01-03: Verify that the sheets carry no extractable text, so that raster reading is
      justified rather than assumed:
      ```bash
      python -c "import fitz,glob; [print(f, len(fitz.open(f)[0].get_text().strip()), len(fitz.open(f)[0].get_drawings())) for f in sorted(glob.glob('contractor/*.pdf'))]"
      ```
      Expect a text length of `0` and a drawing-op count in the 17,000–26,000 range for each.
- [ ] TASK-01-04: Render high-zoom crops of every dimension chain into the scratch directory
      and read the printed figures visually. Use zoom 8 for overall chains and 12–16 for
      dense internal chains. Section A-A is plotted rotated, so apply `set_rotation(270)`
      before rasterising it — `90` renders it upside-down and mirrored.
- [ ] TASK-01-05: Read Section A-A's level tags and derive the seven storey heights as the
      differences between consecutive tags. Tags already read: `+17.200 / +20.600 / +23.800 /
      +25.800`. Read the remaining lower tags in the same pass.
- [ ] TASK-01-06: Read the front elevation's level tags and confirm they agree with the
      section. (They were verified to agree at `+23.800` and `+25.800`; confirm the rest.)
- [ ] TASK-01-07: For each of the seven levels, record every room: Vietnamese label, proposed
      ASCII id, `x`, `y`, `w`, `d` in integer millimetres under the ASM-001 coordinate
      convention, and which sheet and chain the figures came from.
- [ ] TASK-01-08: Record the core separately and precisely — stairwell rect, elevator rect,
      hall rect, and the light-well footprint — since these must be byte-identical on all
      seven levels (S-3 step 2).
- [ ] TASK-01-09: Cross-check every overall dimension against vector measurement using
      `K = 43.0` (S-1). Flag any disagreement over 1% in the table.
- [ ] TASK-01-10: Verify each level's room rects tile the plot footprint exactly, leaving only
      the light well untiled. Apply ASM-006 to any chain that does not close.
- [ ] TASK-01-11: Write `designs/contractor-as-drawn.measurements.md`.

**File Changes**
- `designs/contractor-as-drawn.measurements.md` (create): one `##` section per level (0–6),
  each with a table of `id | nhãn (label) | x | y | w | d | source sheet | chain read |
  cross-check`. Plus a `## Storey heights` table (`level | height_mm | from tags`), a
  `## Core (identical on all levels)` block, and a `## Discrepancies` section listing every
  chain that did not close and how ASM-006 was applied.
- `contractor/*.pdf` (leave alone): read-only inputs, never modified.
- `pyproject.toml` (leave alone): `pymupdf` is a scratch tool, not a project dependency.

**Function Signatures**
None — no code interfaces change in this phase. All PDF work is throwaway scripting in a
scratch directory outside the repo.

**Test Specs**
- Per-level tiling check: for each level, `sum(w × d for all rooms on that level)` +
  `light_well_w × light_well_d` → exactly `plot_width_mm × plot_depth_mm` (3960 × 25000 =
  99,000,000 mm²). Any residual means a chain did not close; apply ASM-006.
- Core identity check: the stairwell rect recorded for level 0 → byte-identical to the
  stairwell rect recorded for levels 1–6. Same for the elevator rect.
- Storey-height sum check: `sum(height_mm for levels 0..6)` → equal to the topmost section
  tag in millimetres (`+25.800` → 25800) within ±50 mm. A larger gap means a tag was misread.
- Calibration cross-check: measure the plot depth in points and multiply by 43.0 → within 1%
  of the printed 25000.

**Dependencies**
- `pymupdf` installed in the environment.
- The five PDFs present under `contractor/`.

**Exit Criteria**
- [ ] `designs/contractor-as-drawn.measurements.md` exists and has a table for all seven levels.
- [ ] Every level's rooms plus the light well tile the plot footprint exactly.
- [ ] The seven storey heights sum to the topmost section tag within ±50 mm.
- [ ] The core rects are identical across all seven levels.
- [ ] Every row cites the sheet it came from.

**Phase Risks**
- **RISK-01-01:** A dimension chain is illegible even at 16× zoom. Mitigation: fall back to
  vector measurement via `K = 43.0`, mark the row `(measured, not printed)` in the table, and
  add a ledger row in PHASE-03. Do not silently mix sources.
- **RISK-01-02:** Passing a Git-Bash POSIX path (`/c/Users/...`) to PyMuPDF's `save()` fails
  with `FzErrorSystem: code=2: cannot open file`. Mitigation: use Windows-style forward-slash
  paths (`C:/Users/...`) and create the output directory first with
  `os.makedirs(out, exist_ok=True)`.

### PHASE-02 - Author and Validate the Spec

**Goal**
Turn the measurement table into `designs/contractor-as-drawn.json` that passes schema
validation, compiles without error, and emits no error-severity items from the check registry.

**Tasks**
- [ ] TASK-02-01: Read `spec/homespec.schema.json` in full before writing anything. Every
      object sets `"additionalProperties": false`, so a single stray key fails validation.
- [ ] TASK-02-02: Open `designs/tubehouse-dream.json` and imitate its **structure** — key
      order, room/opening shapes, how the core repeats per level. Do not copy its dimensions,
      room ids or programme; those describe a different building (DEC-001).
- [ ] TASK-02-03: Write `meta`: `"name": "contractor-as-drawn"`, `"style": "modern-minimal"`
      (the only permitted value), and the 12 `views` listed in File Changes below.
- [ ] TASK-02-04: Write `site`: `plot_width_mm` and `plot_depth_mm` per ASM-002,
      `"wall_alignment": "inside"`, and `"context": {"neighbours": true, "street_depth_mm": 6000}`.
- [ ] TASK-02-05: Author all seven storeys from the measurement table, applying the S-3
      procedure step by step to each.
- [ ] TASK-02-06: Map every Vietnamese label to a `type` from the closed 12-value enum using
      this table, keeping the Vietnamese string in `name`:

      | Sheet label | `type` |
      |---|---|
      | `P.KHÁCH` | `living` |
      | `P.NGỦ …` | `bedroom` |
      | `P.SINH HOẠT` | `living` |
      | `P.THỜ` | `living` |
      | `BẾP` | `kitchen` |
      | `ĂN` / `P.ĂN` | `dining` |
      | `WC` | `bathroom` |
      | `KHO` | `storage` |
      | `NƠI ĐỂ XE` | `garage` |
      | `HÀNH LANG` / `SẢNH` | `hall` |
      | `THANG` | `stairwell` |
      | `THANG MÁY` | `elevator` |
      | `LÔ GIA` / `BAN CÔNG` / `SÂN THƯỢNG` / `SÂN SAU` | `balcony` |
      | `Ô KỸ THUẬT THANG MÁY` | `storage` |

- [ ] TASK-02-07: Declare `stairs` on levels 0–5 as
      `{"room": "<stairwell id>", "direction": "up"}` on level 0 and
      `{"room": "<stairwell id>", "direction": "up_and_down"}` on levels 1–5. On level 6
      declare `{"room": "<stairwell id>", "direction": "down", "mode": "none"}` so no flight
      is emitted above the topmost floor.
- [ ] TASK-02-08: Verify the stairwell rect against S-2 **before** running the compiler. If it
      does not fit, enlarge the shaft by the smallest amount that satisfies the inequality,
      and record the enlargement in PHASE-03 as both a fidelity departure and a candidate
      review finding (DEC-011).
- [ ] TASK-02-09: Add the roof to level 6 only:
      `{"type": "flat", "overhang_mm": 300, "rect": {...covered rear portion...},
      "voids": [{...light-well footprint...}]}`. `voids` is legal only on `"type": "flat"`
      (CON-006).
- [ ] TASK-02-10: Add `openings` per level: exterior doors and windows to the street and rear,
      internal doors linking every room back to the core, and light-well windows for every
      interior habitable room (S-3 steps 4 and 5).
- [ ] TASK-02-11: Write the file as **UTF-8 without a BOM** (see Conventions & traps).
- [ ] TASK-02-12: Run `homedesign compile designs/contractor-as-drawn.json` and iterate until
      it exits `0`. Warnings on stderr are acceptable and do not block; error-severity lines
      (printed as `[code] path: message`) must all be gone.
- [ ] TASK-02-13: Add two tests to `tests/test_validate.py` so the new spec is covered by CI.
      Note that `tests/test_camera_placement.py` already sweeps `designs/*.json` and will pick
      the spec up with no change.
- [ ] TASK-02-14: Run `python -m pytest tests -q` and `ruff check src tests`; both must pass.

**File Changes**
- `designs/contractor-as-drawn.json` (create): the full spec. `meta.views` must be exactly
  these 12 entries, in this order, with these ASCII names (they become PNG filenames):

  | # | `name` | `kind` | subject |
  |---|---|---|---|
  | 1 | `exterior_front` | `exterior_front` | street elevation |
  | 2 | `exterior_aerial` | `exterior_aerial` | 45° aerial |
  | 3 | `gara` | `room` | level 0 `garage` (nơi để xe) |
  | 4 | `lung` | `room` | level 1 mezzanine main room |
  | 5 | `khach` | `room` | level 2 `living` (P.KHÁCH) |
  | 6 | `bep_an` | `room` | level 2 `kitchen` (BẾP) |
  | 7 | `ngu_chinh` | `room` | level 3 master `bedroom` |
  | 8 | `ngu_2` | `room` | level 3 second `bedroom` |
  | 9 | `sinh_hoat` | `room` | level 4 `living` (P.SINH HOẠT) |
  | 10 | `tho` | `room` | level 5 `living` (P.THỜ) |
  | 11 | `gieng_troi` | `room` | the core `hall` beside the light well |
  | 12 | `san_thuong` | `room` | level 6 `balcony` (SÂN THƯỢNG) |

  Every `kind: "room"` entry requires a `room_id` naming a room that exists on that level.
- `tests/test_validate.py` (modify): append two new test functions at the end of the file.
  Add a `DESIGNS = REPO_ROOT / "designs"` constant and a `load_design(name)` helper beside the
  existing `EXAMPLES` / `load_example`. **Do not modify** the existing tests — in particular
  leave `test_example_specs_pass_schema_validation` and
  `test_example_specs_pass_geometric_validation` operating on their current two fixtures only.
- `spec/homespec.schema.json` (leave alone): no schema change in this plan.
- `src/homedesign/**` (leave alone): no code change in this plan.

**Function Signatures**
- `load_design(name: str) -> dict` — reads `designs/<name>` and returns the parsed spec dict;
  a sibling of the existing `load_example` helper in `tests/test_validate.py`.
- `test_contractor_as_drawn_passes_schema_validation() -> None` — asserts
  `validate_schema(load_design("contractor-as-drawn.json")) == []`.
- `test_contractor_as_drawn_passes_geometric_validation() -> None` — asserts every item
  returned by `validate_compiled(compile_spec(load_design("contractor-as-drawn.json")))` has
  `severity == "warning"`.

**Test Specs**
- `validate_schema(load_design("contractor-as-drawn.json"))` → `[]` (empty list; any element
  means a schema violation, and its `.code` will be `"schema_error"`).
- `validate_compiled(compile_spec(load_design("contractor-as-drawn.json")))` → a list in which
  every element has `severity == "warning"`. Any element with `severity == "error"` fails.
- Shaft stacking: the compiled model's `elevator` room rect on level 0 → identical within
  1 mm to the same room's rect on level 6. A mismatch surfaces as code `shaft_misaligned`.
- Riser ceiling: for every storey height authored, `H / max(2, round(H / 175))` → ≤ 190.0.
  At `H = 3800` this is `172.7`; at `H = 3200` it is `177.8`; at `H = 3400` it is `178.9`.
  A value above 190 raises `stair_riser_too_tall` and blocks the compile.
- Daylight: compiling a variant with the light-well window deleted from an interior bedroom
  → produces an error with code `room_no_daylight`. This confirms the windows are load-bearing
  rather than decorative; revert the variant afterwards.
- `python -m pytest tests -q` → all tests pass, including the two new ones and the
  automatically-swept `tests/test_camera_placement.py` case for the new design.
- `ruff check src tests` → `All checks passed!`

**Dependencies**
- PHASE-01 complete (`designs/contractor-as-drawn.measurements.md` exists).
- `pip install -e ".[dev]"` has been run.

**Exit Criteria**
- [ ] `homedesign compile designs/contractor-as-drawn.json` exits `0` and prints
      `output/compiled/contractor-as-drawn.model.json`.
- [ ] No error-severity lines on stderr (warnings are acceptable).
- [ ] `python -m pytest tests -q` passes with the two new tests present.
- [ ] `ruff check src tests` reports no issues.
- [ ] The spec file loads as UTF-8 and every Vietnamese room name renders with correct
      diacritics: `python -c "import json;print([r.get('name') for r in json.load(open('designs/contractor-as-drawn.json',encoding='utf-8'))['storeys'][2]['rooms']])"`

**Phase Risks**
- **RISK-02-01:** The drawn stairwell is too small for a U-return at the drawn storey height,
  raising `stair_shaft_too_small`. This is the most likely blocker. Mitigation: apply S-2 to
  get the exact minimum run depth, enlarge the shaft by the smallest amount that satisfies it,
  ledger the enlargement, and flag it as a candidate review finding — a shaft that cannot hold
  a compliant flight is a real defect in the drawing, not a modelling inconvenience.
- **RISK-02-02:** `check_habitable_daylight` fires on interior rooms if the light-well wall is
  not classified `exterior`. Mitigation: confirm the room edge facing the well is not shared
  with any other room, then author the window as `"between": ["<room>", "exterior"]`. If the
  compiler still rejects it with `opening_no_wall`, widen the light well by 100 mm so the edge
  is unambiguously free, and ledger the change.
- **RISK-02-03:** Vietnamese diacritics corrupted by an ANSI-encoded write, producing either a
  `json.loads` failure or silently mangled names that then propagate into every SVG, PNG
  filename-adjacent label and the viewer. Mitigation: the UTF-8 exit-criteria check above.
- **RISK-02-04:** `ezdxf` may not round-trip Vietnamese diacritics into DXF depending on the
  DXF version written by `src/homedesign/plan2d.py`. This affects only `output/dxf/`, which is
  not a deliverable of this plan. Note it in the ledger and move on.

### PHASE-03 - Write the Fidelity Ledger

**Goal**
Record every place the model departs from the contractor's drawing, so the render can be shown
to the family without anyone mistaking an approximation for the design.

**Tasks**
- [ ] TASK-03-01: Create `designs/contractor-as-drawn.fidelity.md` with one row per departure
      under the columns: **what the drawing shows | what the model does | why | does it change
      what the render says?**
- [ ] TASK-03-02: Enter the departures known in advance:
      (a) skewed ~7.2° boundaries → orthogonal plot rectangle, tapering rear yard becomes
      untiled plot (DEC-005);
      (b) glazed light-well cap `ô kính lấy sáng` → open roof void, because the renderer has no
      glass and a solid cap renders the core black (DEC-004);
      (c) ~8 winder treads → `u_return` flight (DEC-006);
      (d) one stair block repeated across differing storey heights on the drawing → risers
      re-derived per storey by `src/homedesign/stairs.py`, so the model's stairs differ from
      the drawing's;
      (e) rooftop lift plant room `ô kỹ thuật thang máy` → `storage` room, since the type enum
      has no plant room (CON-004);
      (f) `P.THỜ` → `living`, `SÂN THƯỢNG` → `balcony`, and every other enum approximation from
      TASK-02-06;
      (g) no lift pit or overhead is modelled — the schema has no construct for either;
      (h) **shadows are decorative, not solar**: the schema has no north angle, the sheets have
      no north point, and the sun rig is fixed at 55°/35°. This render is not daylight analysis.
- [ ] TASK-03-03: Add every departure introduced during PHASE-01 and PHASE-02 — measured rather
      than printed dimensions (RISK-01-01), chains that did not close (ASM-006), and any shaft
      enlargement (RISK-02-01) or light-well widening (RISK-02-02).
- [ ] TASK-03-04: Add a short `## Premise changes for other documents` section noting that the
      drawn lift shaft (~1500 × 1600 mm, ~2.4 m², seven stops, rooftop machine room)
      supersedes the 1000 × 1400 mm / 1.4 m² / five-stop / machine-room-less premise in
      `research/2026-08-12_tubehouse-lift-comparison.md`. Do not edit that document.
- [ ] TASK-03-05: Add a `## Provenance` line stating that the spec's dimensions come from the
      five PDFs under `contractor/` as recorded in `designs/contractor-as-drawn.measurements.md`,
      and that the schema has no field for this (CON-003), which is why the sidecar exists.

**File Changes**
- `designs/contractor-as-drawn.fidelity.md` (create): the ledger described above.
- `research/2026-08-12_tubehouse-lift-comparison.md` (leave alone): explicitly out of scope.
- `reports/2026-08-12-contractor-drawing-set-review.html` (leave alone): the review stands.

**Function Signatures**
None — no code interfaces change in this phase.

**Test Specs**
None — no testable behavior changes in this phase. Verification is the completeness check in
Exit Criteria.

**Dependencies**
- PHASE-02 complete, so that compile-driven departures are known.

**Exit Criteria**
- [ ] `designs/contractor-as-drawn.fidelity.md` exists.
- [ ] Every item (a) through (h) in TASK-03-02 has a row.
- [ ] Every `(inferred)`, `(measured, not printed)` and discrepancy row from
      `designs/contractor-as-drawn.measurements.md` has a corresponding ledger row.
- [ ] The ledger states plainly that shadows are decorative and the render is not daylight
      analysis.

**Phase Risks**
- **RISK-03-01:** The ledger drifts out of date if PHASE-04 forces a spec change (for example
  a camera lands badly and a room is resized). Mitigation: treat the ledger as the last file
  updated before PHASE-05, and re-read it after PHASE-04 completes.

### PHASE-04 - Build, Render, and Export

**Goal**
Produce the 12-view `final` EEVEE gallery, the GLB, and the self-contained web viewer.

**Tasks**
- [ ] TASK-04-01: Confirm which Blender will be used before spending render time:
      ```bash
      python -c "from homedesign import orchestrator; print(orchestrator.find_blender())"
      ```
      It must resolve to a **Blender 4.1** executable. If it does not, set `BLENDER_CMD` to the
      4.1 binary path and re-check. Do not edit `orchestrator._CANDIDATES` (CON-001). If
      `find_blender` is not the exported name in this build of the module, read
      `src/homedesign/orchestrator.py` and call the equivalent discovery function.
- [ ] TASK-04-02: Run a cheap preview pass first, to catch a bad camera before spending the
      full budget:
      ```bash
      homedesign build designs/contractor-as-drawn.json --profile preview
      ```
      Expect roughly 1–2 minutes total at 960×540 / 32 samples.
- [ ] TASK-04-03: Open all 12 preview PNGs in `output/png/` and confirm each depicts its
      subject — an exterior shot must show the whole building with sky above and ground below;
      a room shot must show a room interior, not a wall or a lawn. If a shot fails, change the
      `room_id` in `meta.views` to a better room rather than altering camera code (DEC-009).
- [ ] TASK-04-04: Run the full build:
      ```bash
      homedesign build designs/contractor-as-drawn.json --profile final --gltf
      ```
      Expect roughly 15 minutes total (~30 s/view × 12, plus scene build and glTF export;
      the 9-view `tubehouse-dream` set takes ~12 minutes). The command prints
      `blender build: <N>s` followed by every artifact path.
- [ ] TASK-04-05: Confirm no render is red. Sample the centre pixel of the exterior shot:
      ```bash
      python -c "from PIL import Image; im=Image.open('output/png/contractor-as-drawn_exterior_front.png').convert('RGB'); print(im.size, im.getpixel((im.size[0]//2, im.size[1]//2)))"
      ```
      A value near `(194, 34, 53)` on what should be a pale wall means EEVEE Next ran; go back
      to TASK-04-01 and force Blender 4.1 via `BLENDER_CMD`.
- [ ] TASK-04-06: Confirm every render is fresh against the current model by checking the
      provenance sidecars:
      ```bash
      python -c "import json,glob,pathlib; m=json.load(open('output/compiled/contractor-as-drawn.model.json'))['model_hash']; print([(pathlib.Path(p).name, json.load(open(p))['model_hash']==m) for p in sorted(glob.glob('output/png/contractor-as-drawn_*.png.json'))])"
      ```
      Every tuple must report `True`.
- [ ] TASK-04-07: Check the GLB size against the viewer's inlining limit:
      ```bash
      python -c "import os; n=os.path.getsize('output/gltf/contractor-as-drawn.glb'); print(n, n <= 8*1024*1024)"
      ```
      If `False`, apply ASM-007 — keep the viewer and ship the GLB beside it. Do not edit
      `src/homedesign/viewer.py`.
- [ ] TASK-04-08: Open `output/viewer/contractor-as-drawn.html` in a browser and confirm the
      model loads and orbits.

**File Changes**
- `output/**` (create, generated): `output/compiled/contractor-as-drawn.model.json`,
  `output/svg/contractor-as-drawn_*.svg` and `output/dxf/contractor-as-drawn_*.dxf` (7 plans,
  4 elevations, 2 sections — 26 files of each type), `output/blend/contractor-as-drawn.blend`,
  `output/png/contractor-as-drawn_<view>.png` × 12 plus a `.png.json` sidecar for each,
  `output/gltf/contractor-as-drawn.glb`, `output/viewer/contractor-as-drawn.html`. Never
  hand-edit any of these.
- `designs/contractor-as-drawn.json` (modify, only if TASK-04-03 finds a bad camera): change
  the offending `meta.views[].room_id` and nothing else.
- `src/homedesign/orchestrator.py` (leave alone): the Blender candidate ordering is pinned by
  a test and must not be reordered.
- `src/homedesign/viewer.py` (leave alone): the 8 MiB inlining limit stands.

**Function Signatures**
None — no code interfaces change in this phase.

**Test Specs**
- `homedesign build designs/contractor-as-drawn.json --profile final --gltf` → exit code `0`,
  stdout containing a line matching `blender build: <seconds>s`.
- `ls output/png/contractor-as-drawn_*.png | wc -l` → `12`.
- Freshness (TASK-04-06) → all 12 tuples report `True`.
- Red-render guard (TASK-04-05) → the sampled exterior centre pixel is **not** within ±10 of
  `(194, 34, 53)`.
- Preview pass wall-clock → under 3 minutes; final pass → under 25 minutes. A final pass
  materially longer than that means Cycles was selected instead of EEVEE; re-check the profile
  flag.

**Dependencies**
- PHASE-02 complete (the spec compiles).
- Blender 4.1.1 installed and discoverable, or `BLENDER_CMD` pointing at it.
- `pillow` (already a project dependency) for the pixel check.

**Exit Criteria**
- [ ] 12 PNGs exist under `output/png/` with the `contractor-as-drawn_` prefix.
- [ ] All 12 provenance sidecars match the current `model_hash`.
- [ ] No render is predominantly red.
- [ ] `output/gltf/contractor-as-drawn.glb` and `output/viewer/contractor-as-drawn.html` exist
      and the viewer loads the model in a browser.
- [ ] Every one of the 12 views visibly depicts its intended subject.

**Phase Risks**
- **RISK-04-01:** Blender is not installed or not discoverable, so `build` fails. Mitigation:
  set `BLENDER_CMD` to the 4.1 binary. If Blender is genuinely unavailable in the execution
  environment, stop and report that runtime limitation explicitly rather than substituting a
  different renderer or fabricating output.
- **RISK-04-02:** Interior shots in a 3.95 m-wide house use a very wide lens and show visible
  distortion. This is accepted (DEC-009) and is a ledger note, not a defect to fix. If a shot
  is unusable, swap the `room_id`.
- **RISK-04-03:** Seven levels of geometry may push the scene build or the glTF export past
  the memory available on a 4-core / 7.8 GB machine. Mitigation: if the build fails on memory,
  render in two passes with `homedesign render ... --view <name> --skip-existing`, which reuses
  the saved `.blend` instead of rebuilding the scene.

### PHASE-05 - Publish the Finals

**Goal**
Move the finals out of disposable `output/` into the tracked `deliverables/` tree, matching the
layout contract in `deliverables/README.md`.

**Tasks**
- [ ] TASK-05-01: Create the folder structure, mirroring `deliverables/tubehouse-dream/`:
      ```bash
      mkdir -p deliverables/contractor-as-drawn/png deliverables/contractor-as-drawn/gltf deliverables/contractor-as-drawn/viewer
      ```
- [ ] TASK-05-02: Copy the finals:
      ```bash
      cp output/png/contractor-as-drawn_*.png deliverables/contractor-as-drawn/png/
      cp output/gltf/contractor-as-drawn.glb  deliverables/contractor-as-drawn/gltf/
      cp output/viewer/contractor-as-drawn.html deliverables/contractor-as-drawn/viewer/
      ```
      Do **not** copy the `.png.json` provenance sidecars — `deliverables/tubehouse-dream/png/`
      holds bare PNGs only.
- [ ] TASK-05-03: Confirm nothing copied is git-ignored:
      ```bash
      git check-ignore -v deliverables/contractor-as-drawn 2>&1 || echo "not ignored - good"
      ```
      Expect `not ignored - good`. Only `output/` is ignored (`.gitignore:2`).
- [ ] TASK-05-04: Re-read `designs/contractor-as-drawn.fidelity.md` and add any departure that
      PHASE-04 introduced (RISK-03-01), including the GLB-inlining note if ASM-007 applied.
- [ ] TASK-05-05: Report to the plan's owner: the 12 view names, the total render wall-clock,
      the GLB size in bytes and whether it inlines, and the count of ledger rows. Do not run
      `git commit` or `git push` unless asked.

**File Changes**
- `deliverables/contractor-as-drawn/png/contractor-as-drawn_<view>.png` (create): 12 files.
- `deliverables/contractor-as-drawn/gltf/contractor-as-drawn.glb` (create).
- `deliverables/contractor-as-drawn/viewer/contractor-as-drawn.html` (create).
- `designs/contractor-as-drawn.fidelity.md` (modify): append any PHASE-04 departures.
- `deliverables/README.md` (leave alone): the layout contract is already correct; this design
  simply has no `pdf/` folder because the A3 brief is out of scope.
- `deliverables/tubehouse-dream/**` (leave alone): the brief scheme's finals are untouched.

**Function Signatures**
None — no code interfaces change in this phase.

**Test Specs**
- `ls deliverables/contractor-as-drawn/png/*.png | wc -l` → `12`.
- `ls deliverables/contractor-as-drawn/png/*.json 2>/dev/null | wc -l` → `0` (sidecars excluded).
- `git status --porcelain deliverables/contractor-as-drawn` → lists the new files as untracked
  (`??`), proving they are not git-ignored.

**Dependencies**
- PHASE-03 and PHASE-04 complete.

**Exit Criteria**
- [ ] `deliverables/contractor-as-drawn/` contains `png/` (12 files), `gltf/` (1 file) and
      `viewer/` (1 file).
- [ ] `git status --porcelain deliverables/contractor-as-drawn` shows the files as untracked
      rather than ignored.
- [ ] The fidelity ledger reflects the final state of the model.

**Phase Risks**
- **RISK-05-01:** Copying the `.png.json` sidecars into `deliverables/` diverges from the
  existing `tubehouse-dream` layout and adds noise to the tracked tree. Mitigation: the glob in
  TASK-05-02 matches `*.png` only; the count check in Test Specs catches a slip.

## Gotchas

- **Millimetres on the Python side, metres on the Blender side.** Every number in the spec is
  an integer millimetre. The `/ 1000` conversion happens exactly once, inside
  `src/homedesign/blender/`. Never write metres into the spec.
- **`"additionalProperties": false` is set on every object in the schema.** One stray key —
  a comment, a `note`, a `source` field — fails validation with code `schema_error`. This is
  precisely why the measurements and fidelity files are separate markdown sidecars.
- **`meta.name` must equal the spec filename stem.** Every output filename derives from
  `meta.name`, not from the path, so a mismatch silently writes
  `output/png/<wrong-name>_*.png` and the rest of the plan's commands stop matching.
- **View names become filenames.** `meta.views[].name` produces `<meta.name>_<view name>.png`.
  Keep them ASCII, lower-case, underscore-separated. Vietnamese diacritics belong in the room
  `name` field only.
- **UTF-8 without a BOM.** Windows PowerShell's `Set-Content`/`Out-File` default to the system
  ANSI codepage or add a BOM, either of which corrupts every Vietnamese room name. Write the
  JSON with Python or with `-Encoding utf8NoBOM`.
- **Contractor filenames contain spaces, including one double space** (`MC  A- A-Model.pdf`).
  Always quote them in shell commands.
- **Section A-A is plotted rotated 90°.** Rasterise it with `set_rotation(270)`;
  `set_rotation(90)` produces an upside-down, mirrored image.
- **The sheets are labelled 1:100 but plot at about 1:122.** Scaling off the PDFs with a 1:100
  rule reads ~18% short. Printed dimension strings are authoritative; the `K = 43.0` mm/pt
  calibration is a cross-check only (S-1).
- **The light well must be left untiled, not authored.** There is no `void` room type and no
  floor-void key for an ordinary room. Floor slabs are emitted per-room, so an untiled
  footprint is automatically open. Only `elevator` rooms and stairwells-with-stairs get an
  automatic slab punch.
- **Roof `voids` work only on `"type": "flat"`.** A `gable` or `shed` roof with `voids` raises
  `NotImplementedError` from `src/homedesign/blender/roof.py`.
- **`check_room_support` is an error, not a warning.** Any room more than 20% unsupported by
  the level below fails the compile. Watch rooms that overhang the light well.
- **Shaft rects must match within 1 mm across all seven levels.** Copy the same rect literal
  rather than retyping it per level; a one-digit typo produces `shaft_misaligned`.
- **Do not reorder `orchestrator._CANDIDATES`.** Blender 4.1 first is deliberate, pinned by
  `test_blender_candidates_prefer_legacy_eevee_build`, and 4.2+ EEVEE Next renders every lit
  surface blood red on this machine's GPU.
- **A blood-red render is a renderer bug, not a materials bug.** `materials.py` contains no red
  at all. If surfaces come out red, check which Blender executable ran before touching the
  design.
- **`output/` is git-ignored and one `git clean -xdf` from gone.** That is the whole reason
  PHASE-05 exists.
- **Do not add `pymupdf` to `pyproject.toml`.** It is a one-off measurement tool, not a
  pipeline dependency; adding it would put a PDF library into every install and every CI run.

## Verification Strategy

- **TEST-001:** `python -m pytest tests -q` → all tests pass, including
  `test_contractor_as_drawn_passes_schema_validation`,
  `test_contractor_as_drawn_passes_geometric_validation`, and the automatically-swept
  `tests/test_camera_placement.py` case for the new design.
- **TEST-002:** `ruff check src tests` → `All checks passed!`
- **TEST-003:** `python scripts/sync_skill.py --check` → `ok: skill copies match` (CI runs this;
  the plan changes no skill docs, so it must still pass).
- **TEST-004:** `homedesign compile designs/contractor-as-drawn.json` → exit code `0`, stdout
  is the path `output/compiled/contractor-as-drawn.model.json`, and stderr contains no line
  without a `warning:` prefix.
- **TEST-005:** `ls output/png/contractor-as-drawn_*.png | wc -l` → `12`.
- **TEST-006:**
  ```bash
  python -c "import json,glob,pathlib; m=json.load(open('output/compiled/contractor-as-drawn.model.json'))['model_hash']; bad=[pathlib.Path(p).name for p in sorted(glob.glob('output/png/contractor-as-drawn_*.png.json')) if json.load(open(p))['model_hash']!=m]; print('stale:', bad)"
  ```
  → `stale: []`
- **TEST-007:**
  ```bash
  python -c "from PIL import Image; im=Image.open('output/png/contractor-as-drawn_exterior_front.png').convert('RGB'); w,h=im.size; print(im.getpixel((w//2,h//2)))"
  ```
  → a pixel that is not within ±10 of `(194, 34, 53)`.
- **TEST-008:**
  ```bash
  python -c "import os; n=os.path.getsize('output/gltf/contractor-as-drawn.glb'); print(n, 'inlines' if n<=8*1024*1024 else 'external-ref (ASM-007 applies)')"
  ```
  → prints the size and which branch of ASM-007 applies.
- **TEST-009:** `ls deliverables/contractor-as-drawn/png/*.png | wc -l` → `12`, and
  `ls deliverables/contractor-as-drawn/png/*.json 2>/dev/null | wc -l` → `0`.
- **TEST-010:** `git status --porcelain deliverables/contractor-as-drawn` → the new files listed
  as `??` (untracked), confirming they are not git-ignored.
- **MANUAL-001:** Open all 12 PNGs. Each exterior shot must show the whole building with sky
  above and ground below and neighbouring party-wall massing on both sides; each room shot must
  show a room interior. A shot of a blank wall or a lawn means the camera missed — change the
  `room_id`, do not change camera code.
- **MANUAL-002:** Open `output/viewer/contractor-as-drawn.html` in a browser; the model loads
  and orbits with the mouse.
- **MANUAL-003:** Read `designs/contractor-as-drawn.fidelity.md` end to end and confirm every
  approximation in the model has a row, including the statement that shadows are decorative
  rather than solar.
- **MANUAL-004:** Spot-check three dimensions in `designs/contractor-as-drawn.json` against
  `designs/contractor-as-drawn.measurements.md` and then against the printed chain on the
  corresponding PDF sheet, confirming the trail from spec value to drawing is unbroken.
- **OBS-001:** Record the wall-clock reported by `blender build: <N>s` in the PHASE-05 report.
  A `--profile final` run materially over 25 minutes means the wrong profile or the wrong
  engine ran.

## Risks and Alternatives

- **RISK-001:** The measurement phase is the schedule risk — roughly 40 rooms across seven
  levels, read from outlined glyphs at high zoom. Everything downstream is minutes.
  Mitigation: finish PHASE-01 completely and verify its tiling arithmetic before authoring any
  JSON; a measurement error found in PHASE-02 costs a full re-read of a level.
- **RISK-002:** The model is an approximation of a drawing, and a render is persuasive in a way
  a caveat is not. Someone may take a rendered dimension, a shadow or a rear-yard clearance as
  fact. Mitigation: the fidelity ledger ships with the renders, and shadows are explicitly
  labelled decorative. Setback and height questions remain in
  `reports/2026-08-12-contractor-drawing-set-review.html` and are not restated by the render.
- **RISK-003:** The render depicts the contractor's single-family scheme, which differs from the
  client's brief (no leased floors, no lockable second-floor lobby, glazed rather than open
  light well). Shown without context, the family could read it as the agreed design.
  Mitigation: ASM-008 requires the published page to link the review report in one sentence.
- **RISK-004:** Blender may be unavailable in the execution environment, blocking PHASE-04 and
  PHASE-05. Mitigation: PHASE-01 through PHASE-03 are entirely Blender-free and deliver real
  value on their own (a validated spec, a measurement record and a ledger). If Blender is
  missing, complete those three phases, report the runtime limitation plainly, and stop.
- **ALT-001:** Extend the schema first — a site polygon for the skewed boundary, a glazed
  roof-light construct, and a cutaway view kind. Not chosen: the site polygon touches every
  wall-derivation path in `src/homedesign/compiler.py`, and the render is wanted now. The
  fidelity ledger becomes the backlog for that work rather than its excuse.
- **ALT-002:** Model directly in Blender and skip the spec. Not chosen: it forfeits the check
  registry, the 2D drawing set, the model-hash provenance sidecars and every test. The
  pipeline's value is that the render is downstream of a validated model.
- **ALT-003:** Copy `designs/tubehouse-dream.json` and overwrite only what differs. Not chosen:
  same plot and same core position make it the obvious shortcut and exactly the trap — it would
  inherit the brief's geometry wherever attention lapsed, silently defeating DEC-001.
- **ALT-004:** Wait for the contractor's DWG before modelling. Not chosen: it blocks on someone
  else's reply. The request is already outstanding in the review; if the DWG arrives it becomes
  a verification pass against a model that already exists.
- **ALT-005:** Render a Cycles hero shot for the cover image (~3 minutes for one view, CPU-only).
  Deferred, not rejected — worth doing after the EEVEE gallery has been seen.

## Suggested Next Step

Execute PHASE-01. It needs only `pip install pymupdf` and the five PDFs already in
`contractor/`, it is the schedule-critical path, and its exit criteria — every level tiling
exactly, the core rects identical across all seven levels, and the storey heights summing to
the topmost section tag — are arithmetic checks that either pass or do not. Do not begin
PHASE-02 until they pass.
