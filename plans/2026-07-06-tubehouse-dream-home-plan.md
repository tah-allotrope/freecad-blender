---
title: "Tubehouse Dream Home: 5-Storey Spec, Light Well, Render Gallery, Architect-Brief PDF"
date: "2026-07-06"
status: "complete — all five phases delivered (bfdac9d, c9c947f, 05b796e, b29c47f, 0682897): spec/tubehouse-dream.json compiles, 5 SVG/DXF plan pairs, 9 final 1920x1080 renders in output/png/, and output/pdf/tubehouse-dream-brief.pdf via the new `pdf` CLI stage"
request: "tubehouse-dream-home"
plan_type: "multi-phase"
research_inputs:
  - "research/2026-07-06_tubehouse-dream-home-brainstorm.md"
  - "research/2026-07-04_idea-floorplan-3d-home-tool-brainstorm.md"
---

# Plan: Tubehouse Dream Home: 5-Storey Spec, Light Well, Render Gallery, Architect-Brief PDF

## Objective
Design the user's real dream home — a 4m × 25m, 5-storey mixed-use Vietnamese urban tube
house with a full-height mid-tube light well — through the existing `/homedesign`
pipeline, and compile the results (dimensioned per-floor plans, a full 3D render gallery,
design narrative, room schedule, requirements) into one A3-landscape architect-brief PDF.

## Context Snapshot
- **Current state:** `src/homedesign/` compiles a JSON spec into per-storey SVG+DXF plans
  and a Blender Cycles scene with exactly two renders (exterior + one auto-picked
  interior). Verified in-code: room voids already work at the wall level
  (`compiler._derive_walls` marks unshared edges `exterior`, explicitly "handles
  courtyards"), and floor slabs are per-room (`build_scene.build_floors_and_stairs`), so
  a full-height light well is mostly representable today. Remaining gaps: `_derive_roof`
  (compiler.py:325) always spans the whole plot (would cap both the light well and the
  roof terrace); `_walls_between` (compiler.py:226) picks the largest exterior wall for
  `between: [room, "exterior"]` openings, so a room facing both the street and the light
  well cannot say which face gets the window; no `elevator` room type; `add_cameras`
  (build_scene.py:138) is hardcoded to 2 views; no PDF stage exists.
- **Desired state:** `spec/tubehouse-dream.json` compiles cleanly to 5 storeys with light
  well, elevator shaft, balconies, and partial roof; `python -m homedesign build ... --final`
  emits 5 floor-plan SVG/DXF pairs and an 8+-image render gallery; a new `pdf` CLI stage
  produces `output/pdf/tubehouse-dream-brief.pdf` (A3 landscape, via HTML → headless Edge).
- **Key repo surfaces:** `spec/homespec.schema.json`, `src/homedesign/compiler.py`,
  `model.py`, `validate.py`, `plan2d.py`, `orchestrator.py`, `__main__.py`,
  `blender/build_scene.py`, `blender/roof.py`, `blender/materials.py`,
  `spec/examples/tubehouse-mini.json`, `tests/test_compiler.py`, `tests/test_validate.py`,
  `tests/test_plan2d.py`, `tests/test_placement.py`, `.claude/skills/homedesign/SKILL.md`.
- **Out of scope:** curved/cylindrical geometry; construction/permit-grade drawings;
  cost/budget content; IFC export (stays parked); render styles beyond `modern-minimal`.

## Research Inputs
- `research/2026-07-06_tubehouse-dream-home-brainstorm.md` — fixes the entire house
  program (DEC-001…DEC-018) and deliverable shape (DEC-019…DEC-022); its Open Questions
  seed `## Grill Me` below. This plan's phases follow its suggested sequencing.
- `research/2026-07-04_idea-floorplan-3d-home-tool-brainstorm.md` — establishes standing
  constraints (rectilinear-only core, styles limited to `modern-minimal`, PDF previously
  dropped deliberately, IFC parked), which bound what PHASE-01 may change.

## Assumptions and Constraints
- **ASM-001:** Lease spaces are modeled as `office` rooms; the elevator gets a new
  `elevator` room-type enum value (~1.2m × 1.5m shaft stacked on every storey).
- **ASM-002:** Party walls (both sides + rear) carry no openings; windows exist only on
  the street facade (y=0 edge) and onto the light well.
- **ASM-003:** Headless Edge is available at
  `C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe` (or on PATH) and
  supports `--headless --print-to-pdf=<path> <file-url>`.
- **ASM-004:** Blender is discoverable by `orchestrator.py` (hardcoded candidates or
  `BLENDER_CMD`), as it was for the existing tubehouse-mini outputs.
- **CON-001:** Geometry stays rectilinear and axis-aligned; the light well is an untiled
  rect void (~2.0m × 2.0m at ~12m depth beside the stair core), not new geometry kinds.
- **CON-002:** Validator floors: rooms ≥600mm each dimension, stair runs ≥900mm. On a 4m
  tube minus 200mm exterior walls, the interior is ~3.6m wide; core floors must fit
  stair (≥900) + elevator (~1200) + light well (~2000) by distributing them along the
  tube depth, not across its width.
- **CON-003:** Every room must be reachable via a door-chain from an exterior door
  (SKILL.md design rule) — hall/corridor rooms link front and rear zones past the core.
- **CON-004:** 8+ final renders at 512 samples / 1920×1080 will take significant time on
  this machine; iterate at preview quality, run `--final` once, unattended.
- **DEC-001:** House program per brainstorm: GF garage(front)+hall+core+rear lease;
  F1 lease studio+WC; F2 living(front, balcony)+kitchen/dining(rear)+WC; F3 master
  suite + one kid's room + baths; F4 office + guest bed/bath (rear) + front roof
  terrace (~40%); heights GF 4.0m, others 3.4m.
- **DEC-002:** PDF = A3 landscape architect brief: cover hero render → narrative → room
  schedule → one plan page per storey → render gallery → requirements → handover appendix.
- **DEC-003:** PDF built from an HTML template printed by headless Edge (vector SVG
  plans embedded inline); reportlab rejected.

## Phase Summary
| Phase | Goal | Dependencies | Primary outputs |
|---|---|---|---|
| PHASE-01 | Pipeline geometry extensions: partial roof, opening side hint, elevator type | None | Schema + compiler + tests green |
| PHASE-02 | Configurable render gallery (8+ named views) | PHASE-01 | `build_scene.py` camera system + preview renders |
| PHASE-03 | Author + validate the 5-storey tubehouse spec | PHASE-01 | `spec/tubehouse-dream.json`, 5 SVG/DXF plan pairs |
| PHASE-04 | Final-quality render gallery | PHASE-02, PHASE-03 | 8+ PNGs in `output/png/` |
| PHASE-05 | Architect-brief PDF builder + assembly | PHASE-03, PHASE-04 | `src/homedesign/pdf.py`, `output/pdf/tubehouse-dream-brief.pdf` |

## Detailed Phases

### PHASE-01 - Pipeline Geometry Extensions
**Goal**
Make the light well, roof terrace, elevator, and window-side control representable, with
red/green TDD against the existing test suite.

**Tasks**
- [x] TASK-01-01: Write failing tests in `tests/test_compiler.py` for: (a) a roof with an
  explicit sub-rect covering only part of the plot; (b) a roof with a `voids` list whose
  rects are excluded from the roof footprint; (c) an opening
  `between: [room, "exterior"]` carrying a `side: north|south|east|west` hint landing on
  that specific wall; (d) an `elevator` room type compiling like `storage`.
- [x] TASK-01-02: Extend `spec/homespec.schema.json`: add `"elevator"` to the room type
  enum; add optional `rect {x,y,w,d}` and `voids: [rect]` to `roof`; add optional
  `side` enum to openings (valid only when one endpoint is `"exterior"`).
- [x] TASK-01-03: Implement in `src/homedesign/compiler.py`: `_derive_roof` uses
  `roof.rect` when given (else plot span, current behavior) and records `voids` on the
  `Roof` model object; `_walls_between` filters exterior-wall candidates by the `side`
  hint (vertical wall at rect.x=west / rect.x2=east; horizontal at rect.y=front(south) /
  rect.y2=north) before the largest-first sort. Add `voids: list[Rect]` to `Roof` in
  `model.py` (serialize in `to_dict`).
- [x] TASK-01-04: Update `src/homedesign/blender/roof.py` to build the roof from the
  roof rect and boolean-subtract each void (flat roof is sufficient; gable/shed +
  voids may raise a clear NotImplementedError since this design uses flat).
- [x] TASK-01-05: Update `src/homedesign/plan2d.py` and
  `src/homedesign/blender/materials.py` + `furnish.py` so `elevator` rooms get a label,
  fill color, floor material, and no furniture. Draw the top-storey roof outline/voids
  on the top-floor SVG only if trivially cheap; otherwise skip (plans are per-storey
  footprints, roof legibility is optional).
- [x] TASK-01-06: Run `python -m pytest tests/` — all tests green; update
  `.claude/skills/homedesign/SKILL.md` "Known limitations" and spec-format notes for the
  three new spec fields.

**Files / Surfaces**
- `spec/homespec.schema.json` — new enum value + roof rect/voids + opening side.
- `src/homedesign/compiler.py` — `_derive_roof`, `_walls_between`.
- `src/homedesign/model.py` — `Roof.voids`.
- `src/homedesign/blender/roof.py` — void subtraction, sub-rect roof.
- `src/homedesign/plan2d.py`, `blender/materials.py`, `blender/furnish.py` — elevator handling.
- `tests/test_compiler.py` (+ `tests/test_validate.py` if schema tests live there) — new cases first.
- `.claude/skills/homedesign/SKILL.md` — document new capabilities.

**Dependencies**
- None.

**Exit Criteria**
- [ ] `python -m pytest tests/` passes with the new cases, red-then-green.
- [ ] A minimal courtyard fixture spec (untiled 2×2m void, window `side` hint onto it,
  roof void above it) compiles with zero validation errors.

**Phase Risks**
- **RISK-01-01:** Boolean roof subtraction in Blender can produce bad normals/z-fighting.
  Mitigation: build the flat roof as a ring of boxes around each void instead of a
  boolean when the void count is small — deterministic and artifact-free.
- **RISK-01-02:** The `side` hint interacts with `_walls_between`'s fallback ordering.
  Mitigation: when a `side` is given and no wall matches, emit `opening_no_wall` rather
  than silently falling back to another face.

### PHASE-02 - Configurable Render Gallery
**Goal**
Replace the hardcoded 2-camera setup with a named-view gallery: exterior street, exterior
aerial, light-well shot, and one interior per listed room.

**Tasks**
- [x] TASK-02-01: Design a `views` block (either top-level in the spec under `meta` or a
  `--views` JSON sidecar; prefer spec `meta.views` so it round-trips): list of
  `{name, kind: exterior_front|exterior_aerial|room, room_id?, level?}`. Default when
  absent = current two views (backward compatible).
- [x] TASK-02-02: Extend `add_cameras` in `src/homedesign/blender/build_scene.py` to
  build one camera per view: `exterior_front` = current exterior framing;
  `exterior_aerial` = high three-quarter view showing the roof terrace and light-well
  opening; `room` = camera inside the named room aimed at its far corner (reuse the
  existing interior-camera placement logic, parameterized by room id + storey level).
- [x] TASK-02-03: Name outputs `output/png/<name>_<view>.png`; pass views through
  `orchestrator.build_scene` and `model.to_dict()` (compiler copies `meta.views`
  verbatim onto `CompiledModel`).
- [x] TASK-02-04: Preview-quality smoke run against `spec/examples/tubehouse-mini.json`
  with a 4-view block; confirm one PNG per view and sane framing by inspecting outputs.

**Files / Surfaces**
- `spec/homespec.schema.json` — `meta.views` array.
- `src/homedesign/compiler.py`, `model.py` — pass-through of views.
- `src/homedesign/blender/build_scene.py` — `add_cameras`, `render`, `main`.
- `src/homedesign/orchestrator.py` — no interface change expected; inspect only.

**Dependencies**
- PHASE-01 (schema file is shared; land changes sequentially to avoid conflicts).

**Exit Criteria**
- [ ] `python -m homedesign build spec/examples/tubehouse-mini.json` with a views block
  yields one correctly named PNG per view at preview quality.
- [ ] Omitting `meta.views` reproduces today's two-image behavior.

**Phase Risks**
- **RISK-02-01:** Auto-framed room cameras in 4m-wide rooms clip walls or stare into a
  corner. Mitigation: place camera at the room corner farthest from the door, lens
  ~18-20mm, aim at room centroid at 1.4m height; verify per-view in the preview run.

### PHASE-03 - Author and Validate the 5-Storey Spec
**Goal**
Encode the brainstormed house (DEC-001 program) as `spec/tubehouse-dream.json` and
iterate until compiler + validator emit zero errors and the 2D plans read correctly.

**Tasks**
- [x] TASK-03-01: Lay out the shared vertical core, identical on every storey: light
  well (~2000×2000 void, front edge ≈ y=11,500), stairwell (≥900mm-wide straight run
  beside it), elevator shaft (~1200×1500), and hall segments linking front/rear zones
  (CON-002/CON-003). Use absolute `rect` placement for the core; `relative` for infill.
- [x] TASK-03-02: Author all five storeys per DEC-001, heights 4000/3400/3400/3400/3400,
  with balcony rooms at the front of F2 and F3, terrace as balcony-type room on the
  front of F4, roof `{type: flat, rect: <enclosed F4 portion>, voids: [<light well>]}`,
  and stairs `up`/`up_and_down`/`down` continuity across levels.
- [x] TASK-03-03: Place openings: exterior door front at GF garage/hall (`side: "south"`
  or the front-facing value verified in PHASE-01); light-well windows for kitchen/dining
  (F2), kid's room or bath (F3), office (F4) using the `side` hint; front glazing on
  balcony-adjacent rooms; interior doors satisfying the door-chain rule; window head
  heights per floor-to-floor of 3.4m.
- [x] TASK-03-04: Add `meta.views` with 8+ views: exterior_front, exterior_aerial,
  light-well room shot, and interiors for living (F2), kitchen/dining (F2), master (F3),
  kid's room (F3), office (F4), guest room (F4).
- [x] TASK-03-05: Loop `PYTHONPATH=src python -m homedesign compile spec/tubehouse-dream.json`
  until zero `[code]` errors, then `plans` and visually review all five SVGs in
  `output/svg/tubehouse-dream_f{0..4}.svg` against the brainstorm program (room
  positions, areas, door swings, stair placement, light well visible as void).
- [x] TASK-03-06: Preview build (`build`, no `--final`) and review the gallery for
  framing, light-well openness (sky visible down the well in the aerial), and terrace
  exposure.

**Files / Surfaces**
- `spec/tubehouse-dream.json` — new; the house itself.
- `output/svg/`, `output/dxf/`, `output/compiled/`, `output/png/` — generated artifacts.

**Dependencies**
- PHASE-01 (light well roof/side features), PHASE-02 for TASK-03-04/06 (views).

**Exit Criteria**
- [ ] `compile` exits 0 with no validation errors.
- [ ] All five plan SVGs match the brainstormed program on visual review by the user.
- [ ] Preview renders show an open-to-sky light well and front roof terrace.

**Phase Risks**
- **RISK-03-01:** The 3.6m interior width cannot fit corridor + elevator side-by-side
  anywhere; if a layout knot proves unsolvable within validator limits, shrink the light
  well toward 1.5×2.0m before compromising stair width (≥900mm is non-negotiable).
- **RISK-03-02:** Untiled voids may trip unforeseen validator paths (e.g. reachability
  heuristics). Mitigation: the PHASE-01 courtyard fixture is the canary; fix in
  PHASE-01 code, not by distorting the design.

### PHASE-04 - Final Render Gallery
**Goal**
Produce the publication-quality image set for the PDF.

**Tasks**
- [x] TASK-04-01: Run `PYTHONPATH=src python -m homedesign build spec/tubehouse-dream.json --final`
  in the background (512 samples, 1920×1080 per view; expect a long unattended run).
- [x] TASK-04-02: Review every PNG; fix any framing/material issue by editing
  `meta.views` or the spec and re-render only what changed (re-running `--final` is
  acceptable if per-view rendering isn't separable — note actual runtime).
- [x] TASK-04-03: Pick the hero image for the PDF cover (expected: exterior_front or
  exterior_aerial).

**Files / Surfaces**
- `output/png/tubehouse-dream_<view>.png` — final gallery.
- `output/blend/` (or wherever build_scene saves the .blend) — keep for manual re-shots.

**Dependencies**
- PHASE-02, PHASE-03.

**Exit Criteria**
- [ ] 8+ final PNGs exist, each visually approved.

**Phase Risks**
- **RISK-04-01:** Multi-hour render on this machine. Mitigation: run in background,
  confirm GPU is engaged (build_scene enables GPU when available) before the full set.

### PHASE-05 - Architect-Brief PDF Builder
**Goal**
Net-new `pdf` pipeline stage assembling the DEC-002 document via HTML → headless Edge.

**Tasks**
- [x] TASK-05-01: Red/green: add `tests/test_pdf.py` covering the HTML assembly pure
  parts — room-schedule table generation from a `CompiledModel` (per-floor room name,
  type, area m², floor totals), page sequencing, and inline-SVG embedding (read SVG text,
  strip XML prolog, embed). No Edge invocation in unit tests.
- [x] TASK-05-02: Implement `src/homedesign/pdf.py`: `build_brief(model, out_dir, meta)`
  renders a single HTML document with CSS `@page { size: A3 landscape; margin: 12mm }`
  and one `<section class="page">` per: cover (hero PNG full-bleed + title), narrative,
  room schedule, plan page per storey (inline SVG scaled to fit, storey name + area
  total), gallery pages (2 images/page), requirements, handover appendix (lists
  `output/dxf/*.dxf` per floor + `spec/tubehouse-dream.json`). Images referenced via
  relative `file://` paths or base64-embedded (prefer base64 for a self-contained HTML).
- [x] TASK-05-03: Write the brief copy as a data file `spec/briefs/tubehouse-dream.md`
  (or JSON) consumed by `pdf.py`: design-intent narrative (Vietnam urban context,
  hot-humid climate, cross-ventilation via light well), requirements page (family
  elevator spec, light-well glazing/drainage, party-wall structure, services riser at
  the core, tenant/family access separation per Grill-Me answer, orientation note per
  Grill-Me answer), no budget content (brainstorm DEC-018).
- [x] TASK-05-04: Add `pdf` subcommand to `src/homedesign/__main__.py`:
  `python -m homedesign pdf <spec.json>` → compiles, regenerates plans if missing,
  writes `output/pdf/<name>-brief.html`, then invokes Edge:
  `msedge --headless --disable-gpu --print-to-pdf="output/pdf/<name>-brief.pdf" <file-url>`
  (resolve msedge from PATH, then the Program Files candidates; fall back to Chrome;
  clear error if neither found).
- [x] TASK-05-05: Run end-to-end for tubehouse-dream; inspect the PDF page-by-page
  (plan legibility at A3, image quality, no clipped tables); deliver the PDF to the user.
- [x] TASK-05-06: Document the `pdf` stage in `.claude/skills/homedesign/SKILL.md`.

**Files / Surfaces**
- `src/homedesign/pdf.py` — new module.
- `src/homedesign/__main__.py` — new `pdf` subcommand.
- `spec/briefs/tubehouse-dream.md` — brief copy (narrative + requirements), new.
- `tests/test_pdf.py` — new.
- `output/pdf/tubehouse-dream-brief.pdf` — the deliverable.

**Dependencies**
- PHASE-03 (plans + model), PHASE-04 (final images). HTML scaffolding can start earlier
  against tubehouse-mini artifacts.

**Exit Criteria**
- [ ] `python -m homedesign pdf spec/tubehouse-dream.json` produces the PDF with all
  DEC-002 sections, verified by opening it.
- [ ] `python -m pytest tests/` green including `test_pdf.py`.

**Phase Risks**
- **RISK-05-01:** Edge headless print-to-pdf ignores some CSS `@page` size hints in old
  builds. Mitigation: verify output page size first thing with a one-page probe HTML; if
  A3 is not honored, add `--print-to-pdf-no-header` + explicit page CSS, or fall back to
  Chrome headless.
- **RISK-05-02:** Base64-embedding 8 PNGs at 1920×1080 makes a heavy HTML but keeps the
  document self-contained; if Edge chokes, switch to file:// relative references.

## Verification Strategy
- **TEST-001:** `python -m pytest tests/` — extended compiler/schema/pdf suites stay
  green at every phase boundary (red first for PHASE-01 and PHASE-05 per TDD).
- **TEST-002:** PHASE-01 courtyard fixture spec compiles with zero errors — canary for
  light-well support.
- **MANUAL-001:** User visually approves the five plan SVGs (PHASE-03) before final
  renders are spent, and each final PNG (PHASE-04) before PDF assembly.
- **MANUAL-002:** Open `output/pdf/tubehouse-dream-brief.pdf` and check: A3 landscape
  page size, every DEC-002 section present, plans legible at arm's length, hero cover.
- **OBS-001:** Record the `--final` build wall-clock time printed by `__main__.cmd_build`
  to calibrate future re-render decisions.

## Risks and Alternatives
- **RISK-001:** The `4m` width is the binding constraint everywhere; if the program
  cannot satisfy validator minima, resolve by shrinking the light well then the elevator
  — never the stairs — and record the change in the spec commit message.
- **RISK-002:** Schema is shared by PHASE-01 and PHASE-02; land them sequentially
  (PHASE-02 after PHASE-01 merges) to keep `homespec.schema.json` conflict-free.
- **ALT-001:** Model the light well as a `balcony`-type room instead of an untiled void —
  rejected: balconies get floor slabs and read as rooms in plans/schedules; a true void
  is already supported by wall derivation and needs only the roof fix.
- **ALT-002:** reportlab or wkhtmltopdf for the PDF — rejected in brainstorm DEC-022;
  HTML → headless Edge keeps SVG plans vector-crisp with zero new Python dependencies.
- **ALT-003:** Per-floor 3D cutaway renders (roof/upper floors hidden) in the gallery —
  attractive but requires per-view scene mutation in `build_scene.py`; deferred as a
  follow-up, not needed for the brief.

## Grill Me
1. **Q-001:** Which way does the street facade face (plot orientation), and is there a
   real address/site to reference in the brief?
   - **Recommended default:** Keep the model orientation-agnostic; the brief's
     requirements page states "facade orientation TBC — shading strategy for the glazed
     front to be confirmed against actual solar orientation."
   - **Why this matters:** Only the brief copy (PHASE-05 TASK-05-03) changes.
   - **If answered differently:** Add orientation-specific shading/sun notes to the
     narrative and requirements pages; geometry and renders are unaffected.
2. **Q-002:** Do lease tenants need hard access separation from the family (separate
   lobby, lockable stair door, elevator floor lockout)?
   - **Recommended default:** Shared stair/elevator core with a lockable family lobby at
     F2, stated as a requirement line in the brief.
   - **Why this matters:** Decides one requirements-page line and whether the GF hall is
     split into public/private segments in the spec (PHASE-03 TASK-03-01).
   - **If answered differently:** A dedicated tenant lobby room is added at GF and the
     hall layout re-partitioned; plans regenerate, renders unaffected except GF interior.

## Suggested Next Step
Answer the two Grill Me questions (defaults are safe), then begin PHASE-01 with the
failing compiler tests (`tests/test_compiler.py`) per the red/green rule.
