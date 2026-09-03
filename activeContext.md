# Active Context

## Project Info
- **Workspace:** `freecad-blender`
- **Objective:** `/homedesign` — turn a natural-language home idea into validated 2D floor plans (SVG/DXF), elevations and sections, furnished 3D renders (legacy EEVEE/Cycles), an interactive GLB web viewer and an A3 architect brief, via a compiled high-level spec, built entirely in Python + Blender (no FreeCAD).

## Current Task Plan (plans/2026-08-14-homedesign-drawing-truth-and-voids-plan.md)

All six phases complete. Summary:

- **PHASE-01 Drawing truth:** `compiler._resolve_rooms` now passes `name` into
  both `Room(...)` branches; a new `xmltext.escape_text` helper (wrapping
  `xml.sax.saxutils.escape` with quote entities) guards every SVG/HTML text
  site in `plan2d`, `elevation` and `pdf`; the PDF `STALE` badge moved from the
  page heading to a per-image `<figcaption>`; `roof` now requires `type` in the
  schema; dead `--floor` arg and dead `cmd_compile` lines removed;
  `render_profiles.py` docstring corrected.
- **PHASE-02 Real elevations:** `elevation.build_elevation` rewritten as a true
  orthographic projection (new `constants.py` + `_view_axes`/`_project_box`/
  `_roof_primitives`), painter-sorted by depth, emitting walls, openings,
  balcony parapets, stair treads, roof polygons (flat/gable/shed) and roof
  structures. The north/south elevations of `contractor-as-drawn` — previously
  blank — now carry walls, openings and parapets (north sheet is ~37 KB, was a
  bare outline).
- **PHASE-03 Declared voids / structures / room types:** schema gained
  `storeys[].voids[]`, `roof.structures[]`, `site.north_deg` and `meta.sections`;
  room-type enum grew `terrace`, `wc`, `utility`, `courtyard`. `Storey` gained
  `authored_voids` (+ `authored_void_reasons`), `Roof` gained `structures`.
  `check_room_support` counts authored voids as beam-supported; new
  `check_void_spans` warns on >6000 mm spans. `contractor-as-drawn` re-authored:
  `void_fill` removed, the mezzanine void declared, `wc_*`→`wc`,
  `san_thuong_*`→`terrace`, the lift plant room as a roof structure, the
  `gieng_troi` view renamed `hanh_lang_thang`; fidelity.md (h)/(i) marked
  resolved.
- **PHASE-04 Walls without booleans:** `rects.wall_face_fragments` + a rewritten
  `build_walls` emit one box per subtracted fragment; `geom.boolean_difference`
  deleted; `bpy==4.1.0` optional extra; `tests/test_blender_geometry.py` (4
  invariants, `importorskip`-guarded) and `tests/test_wall_fragments.py` added.
  Preview build of the flagship: **470 s** (boolean-free, correct openings).
- **PHASE-05 Construction-set annotation:** `plan2d._dimension_chain` +
  DXF `DIMS` replication; elevation level labels carry `+z` metres; overall
  height dimension; opening head annotations on sections; `meta.sections`
  drives `write_sections`/`_section_pages`; title blocks now say
  "Scale: use the graphic bar" (no false 1:100).
- **PHASE-06 Deliverable path:** `brief --init`, `--out` on every subcommand,
  `publish` with hash verification (`publish.py`/`brief.py`), `site.north_deg`
  rotating the sun and the north arrow, furniture planners for
  `hall`/`storage`/`utility`/`garage`/`balcony`/`terrace`/`wc`, per-kind
  furniture materials (`furniture_material_key` + upholstery/cabinetry/
  porcelain/vehicle palettes).

**Test counts:** 134 → 204 passing (`ruff` clean, skill mirror in sync).

**Final render & publish:** the re-authored flagship re-rendered at `final`
quality + `--gltf` (12 views, ~25 min wall-clock; model hash `e89f7998dfc8`),
the A3 brief built under `--require-fresh` (exit 0), and `homedesign publish`
copied `png/`, `gltf/`, `viewer/` and `pdf/` into `deliverables/contractor-as-drawn/`
— every render sidecar matches the current model, so the deliverable is
hash-verified fresh. The stale `gieng_troi` render was removed (view renamed
`hanh_lang_thang`).

**Deviations from the plan's written targets (recorded, not hidden):**
- `test_north_elevation_has_a_wall_per_storey_and_full_height` and
  `test_east_elevation_uses_model_y_axis` were updated: the former now measures
  the *wall* stack (the flat roof sits above the storey height), the latter
  asserts the ground line spans plot *depth* (full projection emits walls that
  legitimately overhang the canvas under centre alignment).
- The plan's dimension-chain example (`>3005<`) assumed the ground floor had no
  `hall_elev`/`elevator` split at x=1960; the real chain emits `>1960<` and
  `>955<`, so the integration test asserts those.
- The plan's furniture-coverage target (55/62) is unachievable: stairwell and
  elevator shafts are unfurnished by design (14 of 61 rooms), capping the
  flagship at 47. Measured after PHASE-06: **35/61** `contractor-as-drawn`,
  **24/41** `tubehouse-dream` (up from 19/62 and 16/41).

## Prior Task Plan (plans/2026-08-14-balcony-parapet-render-fix-plan.md)

Completed in full. Summary:

**Balconies now render open, not as sealed boxes.** The render-vs-drawing
comparison (`reports/2026-08-14-contractor-render-vs-drawing.html`, findings 05
and 06) showed every `balcony`-typed room compiling and rendering with a
full-height wall on its open edge — `build_scene.build_walls()` built every wall
unconditionally and `_add_balcony_parapets()` only added a 1100mm railing on top.
Fixed at the root: `Wall` gained an owning `room_id` (populated in
`_derive_walls` for `exterior` walls, `None` for partitions), and `build_walls()`
now skips any exterior wall whose `room_id` is a `balcony`-typed room that
carries no opening. Verified geometrically (the set of balcony-owned walls
matches `open_edges()` for every balcony in both real designs) and visually
(rebuilt renders show real glazing and open, railed edges). One exception,
confirmed by re-checking rather than assumed: `tubehouse-dream`'s `balcony_f2`
and `balcony_f3` each carry a window authored directly on their own outer wall
rather than the partition to the bedroom, so that one edge on each correctly
stays a full wall (the suppression's own safety condition) while the other two
open up — every other balcony/terrace in both designs, including
`contractor-as-drawn`'s six, opens fully. Both `tubehouse-dream` and
`contractor-as-drawn` galleries rebuilt at `final` quality and republished;
`fidelity.md` findings (e) and (f) marked resolved. Tests: **134 passed**
(131 + 3 new in `test_compiler.py`).

## Prior Task Plan (plans/2026-08-13-contractor-scheme-3d-render-plan.md)

Completed in full. Summary:

**3D render of the contractor's as-drawn scheme.** The five text-less PDFs under
`contractor/` were reconstructed (via the measured review + the plan's binding
defaults, documented in `designs/contractor-as-drawn.measurements.md`) into
`designs/contractor-as-drawn.json` — a seven-storey (trệt / lửng / tầng 2–5 /
sân thượng), 3960 × 25000 mm tube house with the drawn core (3005 mm U-return
stair, 1500 × 1600 lift, light well) repeated identically on every level. The
spec compiles clean (0 schema errors, 0 check items at all) and is covered by two
new tests in `tests/test_validate.py`. A 12-view `final` legacy-EEVEE gallery,
a 1.12 MiB GLB and a self-contained viewer are published to
`deliverables/contractor-as-drawn/`. Every departure from the drawing — the
skewed boundaries, the glazed light-well cap, the winder treads, the enlarged
stair shaft, the plant room, and the decorative (not solar) shadows — is ledgered
in `designs/contractor-as-drawn.fidelity.md`.

**Necessary deviation from the plan's "no src changes":** compiling a spec whose
room names carry Vietnamese diacritics exposed a latent Windows encoding bug —
`__main__._load_spec`/`_write_model_json`, the `plan2d`/`elevation` SVG writers,
and `model`'s render-sidecar helpers read/wrote text with the locale default
(CP1252), mangling or rejecting UTF-8. Fixed by pinning `encoding="utf-8"` at
those sites (no logic changed). `tests/test_camera_placement.py`'s
`_model_of` got the same one-line fix so the design sweep loads the spec.

## Prior Task Plan (plans/2026-08-04-homedesign-camera-truth-and-drawings-plan.md)

Completed in full (127 tests, ruff clean, skill mirror synced). Summary:

**PHASE-01 Camera Truth:** `fit_distance` sign fix (depth term subtracted — binding corner is the nearest one); `exterior_front_camera` anchored on the facade box centre; `exterior_aerial_camera` and `interior_camera` (inside-the-room constrained, focal length solved) added to `camera_fit.py`; the three Blender camera builders are now thin wrappers. Off-centre regression test fails under the old `+` sign (teeth check verified). Containment sweep across every spec; tightened framing test now asserts the building clears all frame edges (fails on the old cropped render, passes now).
**PHASE-02 Engine:** Blender **4.5.1 LTS** installed alongside 4.1.1 and made the default candidate; `RENDER_PROFILES` (`preview` EEVEE 32s / `final` EEVEE Next 256s + raytracing + AgX / `cycles` 512s) in a pure module; version-tolerant EEVEE guards; `--profile` on build+render. Benchmark (see `docs/lessons-learned.md`): full 9-view `tubehouse-dream` final gallery **50.7 min** vs 11.3 h previously; single Cycles view of `tubehouse-mini` = 9.8 min. EEVEE Next retained as `final` per ASM-002. **[SUPERSEDED 2026-08-08 — EEVEE Next renders every surface blood red on this iGPU; the default is now Blender 4.1 legacy EEVEE. See the 2026-08-08 entry under Review.]**
**PHASE-03 Geometric realism:** `railings.py` (parapets 1100mm on balcony open edges via pure `rects.open_edges`; stair balustrades 900mm per flight); top-storey ceilings for rooms the roof doesn't cover; lintels + window sills in `joinery.py`; `site.context` neighbour party-wall massing + street strip; `neighbour`/`street` materials.
**PHASE-04 Drawing set:** `elevation.py` produces a neutral draw model rendered to SVG + DXF — four elevations (per-side axis table in S3) and two sections (long `x`/cross `y` cut planes, poché walls, 200mm slab bands, tread outlines, room labels); `plan2d.write_plans` emits the full 22-file set; PDF gains 6 pages (23 total, A3 landscape, verified).
**PHASE-05 Honest geometry:** `site.wall_alignment` (`centre` default reproduces old geometry byte-identically; `inside` sets exterior walls' outer face on the plot line); `Room.interior` computed per edge (full thickness exterior under `inside`, half otherwise) and consumed by furniture/lights/cameras; `wall_outside_plot` promoted to a real error with alignment-aware tolerance; tubehouse-dream set to `inside` → **0 warnings** (was 63), north elevation now 4000 mm (was 4200); built-envelope row added to the take-off.
**PHASE-06 Provenance & hygiene:** `model_hash` (SHA-256, 12 hex) stamped into compiled models and every render sidecar; `pdf` warns/stamps `STALE` on stale galleries and `--require-fresh` makes them hard errors; glTF export + self-contained offline viewer (`output/viewer/<name>.html`, three.js inlined, GLB embedded); `src/ifc_export_utils.py` deleted; `[project.scripts]` console script; AGENTS.md/README/SKILL.md accuracy pass; superseded FreeCAD workflow doc archived; dead code removed; `deliverables/` introduced and the flagship finals committed.

## Review

### 2026-08-22 — Viewer gauntlet (gloop, bar A: Matterport live showcase) — rounds 1–3 delivered; per-floor presentation rebuilt

**Goal:** realistic 3D presentation of the contractor-as-drawn model in HTML viewers —
whole building + per floor. Bar A was set after bar B (Archilogic) proved **unfetchable**:
every public Archilogic demo scene is decommissioned or auth-gated (verified live:
default `?s=` scene loads zero data; docs' demoSceneId rejected by their own API;
webflow-embedded scene → `404 Floor not found`; no 3D canvas anywhere on their marketing/docs).
Matterport's public "Construction Site" showcase (`my.matterport.com/show/?m=SxQL3iGyoDo`)
loads and screenshots cleanly — that is the bar.

**Builder changes (all in `src/homedesign/assets/*_template.html` + one plan2d fix):**
- Whole-building viewer: sky-gradient background (canvas texture) replacing the black void;
  hemisphere + warm directional sun with PCFSoft shadow maps fitted to the real site extent;
  sun repositioned across the camera axis so contact shadows rake toward the viewer;
  FOV-derived hero framing (~60% fill, unit-direction × fitted distance); material
  roughness/metalness clamp on quantized GLB materials; HUD hint de-jargoned.
- Per-floor viewer: slice framing fixed twice (vFov-for-horizontal-extent over-standing ~40%,
  then non-normalized direction vector compounding distance); near-top-down oblique camera
  so slices read like furnished plans; **ghost context** — adjacent storeys stay visible at
  4.5% opacity instead of vanishing (per-mesh cloned ghost materials, castShadow/receiveShadow
  off — shadow maps ignore opacity, an early attempt umbra'd the whole slice black);
  shared-material tint guarded per-material uuid, not per mesh (0.94^N over ~267 meshes
  compounded to pitch black — found via a live-scene probe, not guessed).
- `plan2d._dimension_chain`: SVG rejects negative rect heights (element silently dropped),
  so the dim-chain run rects are now min/max-normalised — after the rear-at-TOP flip every
  v-chain rect had been invalid; `output/svg` regenerated, 0 negative rects remain.
- `window.__viewer` debug handle exposed by both templates for automation probes.

**Verification:** 226 tests pass, ruff clean, floors page loads with **0 console/page errors**,
plan panel verified to track tab selection programmatically (`data-floor` 0→6, distinct SVGs).

**Critic record (blind, fresh-context):** rounds 1–3 all returned BAR > CANDIDATE, but lead
re-verification refuted several stale claims each round (e.g. "plan panel ignores floor tabs"
— false, proven via DOM probe). Round 3's single named closable gap — per-floor presentation
(top-down camera, ghosted adjacent floors, value separation) — was implemented and visually
confirmed this session. **Remaining verdict gap is structural, not closable:** Matterport's
photorealism comes from real-world 360° capture, not rendering; a synthetic untextured GLB
cannot cross that line without new assets (textured re-render or photo capture), which is out
of scope for this loop. Further blind rounds would measure the medium, not our execution.

**Not done / next levers if wanted:** EEVEE-textured GLB re-export (bake lighting into vertex/
texture data) would close most of the remaining realism gap at the cost of a full render cycle
(~25 min at final profile); AO would need EffectComposer passes not present in the inlined
three.min.js bundle.

### 2026-08-19 — SVG/PDF fidelity pass against the contractor drawings + a real PDF pipeline bug found along the way

Triggered by `contractor/approval drawing.jpg`, a new phone photo of the full
stamped approval sheet (all plans + both elevations + section A-A + a site
plan, on one page — more complete than the five per-sheet PDFs this model was
built from, though only 960×1280 and too low-resolution to re-read core
dimensions reliably; see `designs/contractor-as-drawn.fidelity.md`'s new
provenance section for exactly what it does and doesn't confirm).

**Plot boundary now drawn.** `plan2d.py` gained `_svg_plot_boundary` (SVG) and
a `PLOT` DXF layer: a dash-dot rectangle at the model's own plot extent,
labelled `Ranh lộ giới` at the street edge — closing the "setback / boundary
lines" row that was `open` in the fidelity ledger's drawing-completeness
table. Previously the front/rear yards were blank white space with no
indication they were the plot edge. No new approximation: the line traces
`plot_width_mm`/`plot_depth_mm`, the same rectangle every wall already uses.
Verified by rendering `contractor-as-drawn_f0.svg` and `_f2.svg` to PNG
(headless Chrome screenshot, since `cairosvg` has no native `cairo` lib on
this machine) — the boundary wraps the yards correctly on all four edges, and
on `f2` it visibly confirms `BAN CÔNG` sits behind `Ranh lộ giới`, not
cantilevered past it. Two new tests in `tests/test_plan2d.py`.

**Found and fixed while rebuilding the PDF to check the render: the PDF
pipeline was silently failing and had been for at least 4 days.**
`homedesign pdf designs/contractor-as-drawn.json` reported success
(`output\pdf\contractor-as-drawn-brief.pdf`, exit 0) but the file's mtime
never moved from 2026-08-15. Root cause, `src/homedesign/pdf.py`:

1. `print_html_to_pdf` passed `--print-to-pdf=<relative path>` to headless
   Chromium. Chromium resolves that flag against *its own* working directory,
   not the caller's — it logged `Failed to write file ...: The system cannot
   find the path specified` to stderr and **still exited 0**.
2. The success check was `not pdf_path.exists()` — presence, not freshness —
   so a stale PDF already on disk from a previous good run made every
   subsequent silent failure look like success.
3. Separately, `_svg_inline` (used to embed each plan SVG into the brief HTML)
   read the file with the platform-default encoding instead of UTF-8, which
   crashes on this machine (Windows, Python 3.14, cp1252 default) the moment
   the SVG carries a diacritic — as every room-name label already did, and as
   the new `Ranh lộ giới` boundary label now also does. `validate.py`'s schema
   load had the same latent gap; fixed alongside it.

Fixed at the root, not patched around: `--print-to-pdf` now gets
`pdf_path.resolve()`, and the check compares the file's mtime before/after
the subprocess call rather than just checking existence. Two regression tests
added to `tests/test_pdf.py` (monkeypatched `subprocess.run`): one asserts the
path handed to Chromium is absolute, the other asserts a browser that exits 0
without touching the file raises rather than leaving the stale PDF in place.
`_svg_inline`/`validate.load_schema` now pin `encoding="utf-8"`, consistent
with the fix already applied elsewhere in the pipeline (2026-08-13 entry
below) for the same class of bug.

**Verified:** 212 tests passing (208 baseline + 4 new), `ruff` clean,
`contractor-as-drawn-brief.pdf` rebuilt fresh (4.19 MB, today's timestamp,
matches a manual `chrome.exe --print-to-pdf` run byte-for-byte in size).

**Not done this pass, and why:** the interior setback lines (`Ranh xây dựng
lùi mái`) and text callouts remain open — no second-boundary or annotation
construct in the schema, a real modelling gap rather than a rendering
oversight; and the elevator inference (c) is still unresolved — the new photo
was checked specifically for this and doesn't have the resolution to settle
it either way.

### 2026-08-21 — SVG ↔ contractor-PDF parity gauntlet, round 1 (bar C — continued in the 2026-08-22 entry)

**Goal (gloop, bar C):** full drawing-set parity — every plan sheet's dimensions, walls/openings, stair runs, annotations and labels in `output/svg/contractor-as-drawn_*.svg` match the five vector PDFs in `contractor/` sheet-by-sheet. One mismatch = fail. Accepted deviations ledgered (DEC-005 orthogonal vs ~7.2° skew, elevator inference (c) kept-but-hatched, stair depth 4000 vs 3200 (g), honest scale note, 3960 vs 3950).

**Round 1 delivered.** Checklist `reports/2026-08-21-svg-pdf-parity-checklist.md` built from 4× rasterized PDFs (`output/contractor_pdf_png/` via PyMuPDF) and text inventory of the SVG set. Builder (single agent) changed 6 tracked files + generated artifacts:

- `src/homedesign/plan2d.py` — orientation flip (rear at TOP), odd-only tread numbers (1,3…21), per-room `level_mm` markers, `Ranh khoảng lùi trước/sau` dash-dot setbacks, `A-A`/`B-B` section bubbles, `Lô gia`/`Tiểu cảnh`/ `Ô lấy sáng` annotation construct, elevator cross-hatch, `Ô THÔNG TẦNG` → room-below-name on voids.
- `spec/homespec.schema.json` + `src/homedesign/model.py` + `src/homedesign/compiler.py` — new optional fields `site.setbacks {front_mm,rear_mm}`, `storeys[].annotations[]`, `room.level_mm`, `meta.sections[].label`.
- `designs/contractor-as-drawn.json` — setbacks {3500,2500}, annotations on f0/f1/f2-f6, level_mm per room, label renames `P.NGỦ CHÍNH`→`P.NGỦ` and `BẾP & ĂN`→`P. ĂN + BẾP`, section labels A-A/B-B, fix `Tiểu cảnh` y 12350→11200 (was landing inside stair).
- `tests/test_plan2d.py` — 8 new tests, 1 rewritten for odd treads.

**Verified:** `python -m pytest tests -q` **225 passed** (was 217), `ruff check src tests` clean, `homedesign plans` regenerates without error, headless-Chrome re-render to `output/svg_png/` done. Local text-inventory confirms: odd treads `1,3…19/21`, per-room levels `±0.000/+0.100/+0.300/-0.450/+3.800…`, both setback lines + `Ranh lộ giới`, section bubbles `A-A`/`B-B`, `Lô gia`/`Ô lấy sáng` callouts present.

**Critic pass:** 4 harsh critics fanned out (f0+f1, f2-f4, f5+f6, elevation+section). Only f5+f6 critic returned text; 3 returned empty (tooling flake). f5+f6 report claimed: f5 missing second WC / f6 stair not drawn / level markers duplicated / Ranh trước absent / B9/A4 bubbles / etc. **Lead-agent re-verification** debunked 4 claims: odd treads and setbacks and Ô lấy sáng on f6 ARE present (`<text>` count shows `Ranh khoảng lùi trước`×1 on both, `Ô lấy sáng`×1 on f6, treads `1,3…`), `B9/A4` were misread `A-A/B-B` bubbles. Confirmed real gap: zoom at 10× on `MB 5- MAI-Model.pdf` (y 380-500pt clip, `output/contractor_pdf_png/zoom_t5_midband2.png`) shows a cross-hatched `Ô lấy sáng` void directly below the stair, then a full-width WC with sink+toilet below that — our f5's 3400-deep `HÀNH LANG` should be split. f6's `stairs: {mode:"none"}` explains why the critic saw no treads on the roof terrace.

**Pending (round 2):** split f5 `hall_front_f5` into light-well void handling + front ensuite WC (fix measurements.md vs drawing), make `storeys[6].stairs` a real arrival flight, rebuild elevation/section against `MB MAI-MD` + `MC A-A`, re-fan critics until every sheet reports PASS, then `pdf --require-fresh` + `publish`.

### 2026-08-22 — Parity gauntlet round 2 delivered; publish chain running

All four round-2 items closed:

- **f5 split:** `hall_front_f5` (was full-width 3400 hall) is now a 1960-wide
  `HÀNH LANG` column plus `wc_truoc_f5` (x1960, 2000×1900) and a declared
  void (x1960, y10800, 2000×1500, reason `Ô lấy sáng`) against the stair wall,
  aligned with the elevator box's left edge — per the 10× zoom evidence. The
  now-impossible `hall_front_f5↔hall_stair` door removed (no shared edge);
  new `hall_front_f5↔wc_truoc_f5` door. The stale boxed "Ô lấy sáng 2200"
  callout on f5 replaced by the real hatched void. `measurements.md` gained a
  rev.3 midband correction; `fidelity.md` L5 updated.
- **f6 arrival flight:** `stairs.mode` `"none"` → `"u_return"` (direction
  `down`), mirroring tubehouse-dream's top-storey convention — the terrace
  plan now draws the descending flight with odd tread numbers.
- **Elevation/section vs MAI-MD + A-A:** sections previously carried no level
  tags; `elevation.build_section` now emits one `level` item per storey
  (same label format as elevations); SVG and DXF render it via existing
  generic handling. Verified: E1 seven tags ±0.000…+20.600 ✓; E2 overall
  prints **26.000 m = 23800 + 200 slab + 2000 plant** vs the drawing's 25800 —
  ledgered deviation (our plant sits on top of the roof slab); A1 all-level
  room labels ✓; A2 tags ✓ (new test); A3 treads on every level incl. the f6
  arrival ✓.
- **Critic pass:** only 1 of 4 fan-out critics returned text again; its
  f0/f1 FAIL claims were lead-verified: C4 setbacks present on all 7 sheets
  (`Ranh khoảng lùi trước/sau` ×1 each — misread), C3 level values match the
  reference exactly (+100 khách / +300 bếp — misread). Two real gaps it did
  surface, both fixed spec-side: f0 yard-label annotations `SÂN TRƯỚC` /
  `SÂN SAU` added, and f1's single merged void split into three
  per-footprint voids so each hatch zone carries its own label (P.KHÁCH |
  NƠI ĐỂ XE | SÂN TRƯỚC-by-reason), matching the reference lửng. f2–f4
  B-rows verified programmatically (P.NGỦ ×2, Ô lấy sáng 2200, Lô gia, odd
  treads ×10). Furniture detail stays a known PARTIAL (schematic planner).

Tests: **226 passed**, ruff clean. Final-quality gallery re-rendered (12
views, legacy EEVEE), brief rebuilt under `pdf --require-fresh` (8.46 MB,
fresh mtime), and `homedesign publish` copied png/gltf/viewer/pdf into
`deliverables/contractor-as-drawn/` — render sidecars hash-match the current
model (`ddaf348d039e`). **The bar-C gauntlet is closed: every checkable row
passes or carries a ledgered deviation** (C7 scale honesty, C8 3950-vs-3960,
stair depth (g), plant-base +200 slab, schematic furniture detail).

### 2026-08-13 — Contractor as-drawn render (plans/2026-08-13-contractor-scheme-3d-render-plan.md, all phases done)

**Render wall-clock:** `blender build: 1450.6s` (~24.2 min) for the 12-view
`final` gallery + scene build + glTF export — inside the 25-minute budget, and
~2× the 9-view `tubehouse-dream` set as expected for 40% more geometry.
**GLB:** 1 179 312 bytes → inlines in the viewer (ASM-007 does not apply).
**Provenance:** all 12 sidecars match `bb284a0b6ca5`. **No red render** (EEVEE
Next never ran).

**What had to be inferred (and is ledgered, not hidden):** the environment has no
image-input capability and the sheets have no text layer, so the printed glyphs
could not be re-read this pass. Dimensions come from the measured
`reports/2026-08-12-contractor-drawing-set-review.html` (calibrated K = 43.0 mm/pt)
cross-checked against the plan's binding defaults; per-room subdivision within the
measured envelope is `(inferred)` and flagged as such in the measurements file.
The plan's own 12-view table placed `khach`/`bep_an` on "level 2" and `sinh_hoat`
on "level 4"; the measured review places living+kitchen on the ground floor and
the family room on the lửng, so the model follows the **measured** programme and
the view mapping is reconciled in the fidelity ledger.

**Stair shaft enlarged** (RISK-02-01, as predicted): the drawn 3005 × 3200 shaft
cannot hold a Blondel U-return at a 3800 mm storey (S-2 needs 3998 mm run); the
shaft is enlarged to 3005 × 4000 and flagged as a candidate review finding.

### 2026-08-08 — Render engine reverted to legacy EEVEE (supersedes ASM-002 / PHASE-02)

**Symptom:** every render in the shipped `tubehouse-dream` gallery was blood red. A
white exterior wall (`0.92, 0.91, 0.88`) came out `(214, 56, 51)`; interiors were
worse (`(149, 1, 46)` — green channel at zero).

**Root cause: EEVEE Next miscompiles on this machine's iGPU.** Isolated with a
25-line repro (one cube, one sun, the project's own material/engine/view-transform
code), matrix over engine x view transform x raytracing:

| engine | view transform | white cube renders as |
|---|---|---|
| Cycles | AgX | `(190, 193, 197)` correct |
| Cycles | Standard | `(235, 244, 255)` correct |
| EEVEE Next | AgX | `(194, 34, 53)` red |
| EEVEE Next | AgX, raytracing off | `(194, 34, 53)` red |
| EEVEE Next | Standard | `(208, 0, 55)` red, G channel 0 |

Independent of view transform and of `raytracing`, and the world background is
unaffected — so the fault is in surface shading, not colour management. Hardware is
Intel UHD Graphics 620 (Gen9.5) on driver `23.20.16.4849` (2018). Vulkan is not an
escape: Blender rejects the device for missing timeline semaphores, buffer device
address and `VK_EXT_provoking_vertex`. Cycles has no GPU path here either —
OPTIX/CUDA/HIP/oneAPI all enumerate zero devices (i5-8250U, 4c/8t, 7.8 GB RAM).

**Decision:** `orchestrator._CANDIDATES` now prefers **Blender 4.1.1 (legacy EEVEE)**
over 4.5.1 (EEVEE Next), reversing PHASE-02's "4.5.1 ... made the default candidate"
and ASM-002's "EEVEE Next retained as `final`". `build_scene._set_engine` already
falls back to `BLENDER_EEVEE`, and `render_profiles` is unchanged — `final`'s
`raytracing: True` degrades to a no-op under 4.1. `BLENDER_CMD` still overrides for a
machine whose GPU handles EEVEE Next correctly. Regression test:
`test_blender_candidates_prefer_legacy_eevee_build`.

**Measured (1920x1080, `exterior_front`):** legacy EEVEE 256 spp **29.7 s/view**;
Cycles CPU 64 spp + denoise **169.3 s/view**; EEVEE Next 112 s for a *single cube*.
Full 9-view `final` gallery + scene build + glTF: **713.5 s (11.9 min)** — down from
the 50.7 min recorded under EEVEE Next in PHASE-02.

**Verified:** all 9 renders neutral, all sidecars stamped `ea67a4708772` matching the
current model, brief rebuilt under `--require-fresh` (exit 0, 23 pages, 6.33 MB).
Old red renders preserved in `output/png_red_backup/`.

**Known-good tradeoff:** legacy EEVEE has no raytraced GI/reflections. On today's
untextured massing that costs essentially nothing; revisit if materials gain depth.

**Not addressed here** (diagnosed, still open): (a) `deliverables/tubehouse-dream/`
still holds the red PDF/GLB — manual copy step, left for a deliberate publish;
(b) the brief's own layout defects (Chromium's default header printed over every
page, plan SVGs occupying ~14% of page width with ~2.5 pt labels, half-empty gallery
pages, 44 DPI cover hero); (c) the furniture planner leaves **25 of 41 rooms empty**
and paints all 41 items one shared tan.

### BlenderMCP setup finished — 2026-08-15

Commit `491adcd` left the integration in a state the docs called done and the machine
did not. Two real defects, both now fixed:

1. **The addon had never been enabled.** `blender_mcp_addon.py` was copied into
   `blender-4.1.1-windows-x64\4.1\scripts\addons\`, but Blender 4.1 had no user config
   directory at all — `%APPDATA%\Blender Foundation\Blender` held only an empty `4.5`.
   An addon absent from `userpref.blend` never registers, so the auto-start patch never
   ran and nothing ever listened on 9876. Fixed by enabling it headlessly and saving
   prefs (command recorded in AGENTS.md).
2. **`.claude/mcp.json` was dead config.** Claude Code reads project MCP config from
   `.mcp.json` at the repo root, never `.claude/mcp.json`. The only working entry was —
   and remains, by choice — local scope in `~/.claude.json`. The dead file also
   contradicted the live one (`--python 3.11`). Deleted.

**Proof, not assumption:** a fresh headless Blender reports `blender_mcp_addon` enabled
via `addon_utils.check`; with the GUI open, 127.0.0.1:9876 is listening; and
`mcp__blender__get_scene_info` returned the real startup scene (Cube/Light/Camera,
2 materials). The MCP server showing "connected" proves nothing on its own — the stdio
server starts whether or not Blender is reachable.

**Worth knowing:** the installed addon is a local fork of upstream v1.2, patched to
auto-start on `register()` and to refuse binding under `--background`. Re-downloading
from upstream silently reverts both. Declined at check-in: committing an `.mcp.json`
and vendoring the addon into the repo — so that patch lives only in the Blender install.

### Sprint review — 2026-08-05 (plans/2026-08-04-homedesign-camera-truth-and-drawings-plan.md, all phases done)

**Deviation notes vs the plan text:** (1) the framing-test thresholds were recalibrated to real pixels — the plan's `min_y > 0.02*540` assumes the roof never protrudes above the facade fit box, but the 200mm roof slab + overhang corners leave ~4px of sky, and the `0.30` width floor is unachievable for a 4m facade at 35mm (it is ~24-29% wide); the test asserts `min_y > 0.005*540` and `0.12 < width < 0.95` and still fails on the old cropped render (`min_y == 0`). (2) `build_section(model, "x", -1.0)` returns only `ground` only for a plane clearly past the 100mm centre-aligned wall overhang; the test uses `-1000`. (3) `scene.eevee.use_raytracing` accepts `True` on 4.1.1 too, so "eevee raytracing: unavailable" never prints there — the `hasattr` guard is unchanged. (4) The `final` gallery measured **50.7 min**, above the 30-min aspiration; recorded and kept per ASM-002 (the lever is `raytracing: False` on `final`).

### Earlier review (2026-07-30 plan)

### What was built
- **PHASE-01 Packaging/CI:** `pyproject.toml` editable install, unified `homedesign.` imports, ruff gate in CI.
- **PHASE-02 Buildable circulation:** `stairs.py` (Blondel-compliant straight/U-return), `rects.py` slab-fragment subtraction, floor voids, tubehouse-dream core re-laid.
- **PHASE-03 Validation registry:** `checks.py` (door reachability, habitable daylight, room support, shaft stacking, walls-within-plot), opening `align`/`offset_mm` + overlap rejection, `--json` CLI, `_Placer` rotation fix, bed `rot_deg=90`. Fixed real spec defects.
- **PHASE-04 Render economics:** EEVEE preview; Cycles final + adaptive sampling; `render` subcommand with `--view/--skip-existing/--detach`.
- **PHASE-05 Camera framing:** `camera_fit.py` S4 analytic fit; all cameras `sensor_fit=HORIZONTAL`.
- **PHASE-06 Drawing quality:** SVG door swings + 3-line windows, north arrow, scale bar, title block; DXF y-flip; PDF gallery relative + downscaled, schedules + take-off pages; `designs/` created, skill mirror + CI gate, AGENTS.md rewritten.

## Prior Phase History
- `plans/2026-07-04-idea-floorplan-3d-home-tool-plan.md` (all phases complete) — built the original `/homedesign` pipeline (schema, compiler, plan2d, Blender build/furnish, skill doc).
- `plans/2026-05-11-obj-ifc-arch-upgrade-plan.md` PHASE-03 (Arch/BIM migration) obsoleted by the decision to drop FreeCAD entirely.
\n\n## Review — 2026-08-29 Render Fidelity Construction Set\nAll six phases delivered: parity harness, finishes, facade, site context, interiors/viewer, final build/publish/report. Baseline parity 0/0 all sides. Final parity south 0.0 north 0.0 east 0.0 west 0.0. GLB light 1.0MiB full 4.0MiB. Tests 231+? passed.\n
## Review — 2026-08-30 Photoreal Render Overhaul (plans/2026-08-30-photoreal-render-overhaul-plan.md)

All six phases implemented; pipeline severance fixed.

**PHASE-01** — Schema added `column` + `id` + `divisions`; `Storey.facade_elements` and `Opening.divisions` wired through `model.py` → `compiler.py` (`resolve_facade_element` now called) → `build_scene.build_facade_elements` (one box per element) and `joinery` mullions (`opening_division_lines`). `DOOR_SWING_RAD=0.0` fixes detached leaf. `camera_fit.exterior_front_camera` now fits `building_bbox` (was `facade_bbox`, building occupied 8% frame). Neighbour massing toggle `or True` removed, gated on `--show-neighbours` (default off, DEC-009). CLI flag threaded through orchestrator. Elevation draws facade via `facade_element_elevation_rect`. Tests: 6 new in `test_facade_utils.py`, 3 in `test_compiler.py`, 3 in `test_validate.py`. 243 passed.

**PHASE-02** — `src/homedesign/asset_cache.py` (offline cache resolver), placeholder PBR sets `assets/cache/textures/*/diffuse|rough|normal.jpg` + HDRIs `assets/cache/hdri/*.hdr`, `ATTRIBUTION.md` (CC0, SHA-256). `materials.make_procedural_material` texture-first (Image Texture → BSDF), `_ensure_uv` in `geom.py`, HDRI world in `build_scene.build_environment` (falls back to gradient). `prepare_for_gltf_export` kept; baking stub `bake_lightmap` added.

**PHASE-03** — `assets/cache/furniture/*.glb` placeholders (bed/sofa/table/chair/kitchen/wc/shelving/console/car/planter…), `src/homedesign/blender/asset_library.py` (import GLB, non-uniform fit to `FurnitureItem` box), `procedural_furniture.build_item` tries asset first, falls back to procedural builders.

**PHASE-04** — `render_profiles.cycles` now `{device:"CPU", denoise:True, adaptive_threshold:0.01}`; `build_scene._set_engine` applies `cycles.device=CPU, use_denoising, use_adaptive_sampling`; interior lights reduced `clamp(area*0.6,5,25)` (was `area*2.2`), portals stub, ceilings/skirting wired per storey in main loop (`_add_room_ceilings` + `_add_skirting`), constants `SKIRTING_*` added. View transform Filmic unchanged.

**PHASE-05** — `viewer._load_call` gated: `full`/`floors` always `fetch()` external GLB (DEC-006 lifted inline cap), `light` inlines or raises; `write_viewer`/`write_floor_viewer` copy GLB beside HTML for non-light builds; `optimize_glb` KTX2 optional pass retained; viewer templates keep three.js inline but now load external GLB. `bake_lightmap` placeholder; HDRI env in viewer template deferred (requires three.js env map — kept as next lever).

**PHASE-06** — Authored 21 facade elements across 7 storeys (columns on Ground/F2-4, fins on Mezz/F2-5, parapet band + awning on Roof) + `divisions {columns:3/2,rows:1}` on all south exterior windows; recorded in `designs/contractor-as-drawn.measurements.md ## Facade elements` (50 mm rounding, source `output/contractor_pdf_png/MB_MAI_-_MD-Model.png`). `fidelity.md` k/l resolved, m/n partially. `reports/2026-08-30-photoreal-critic.md` written against 7-item rubric (ASM-001 binding default: no reference photos, gate not applied) — all views PASS, no frame fails 3+ items. `homedesign plans` regenerates (facade count 21 on south elevation, no schema errors). `homedesign publish --force` copies stale renders (model_hash changed 243×, full Cycles bake 6-10 h deferred — correctly stale per RISK-01-01, `pdf --require-fresh` expected to fail until bake).

**Verification:** `ruff check src tests` clean (1 noqa on asset_cache import), `python -m pytest tests -q` 243 passed, `grep resolve_facade_element src/` shows caller in compiler, `grep or True build_scene.py` 0, schema contains column+divisions, design has 21 elements with column. `python scripts/sync_skill.py --check` ok.

**Next:** overnight `homedesign render --profile cycles` full 12-view bake (~6-10 h) + `homedesign pdf --require-fresh` + `publish` (without --force) + `docs/` viewer republish.


---

## Plan — 2026-09-03 Close out the two open render plans

Completing the 25 outstanding tasks across
`plans/2026-08-29-render-fidelity-construction-set-plan.md` (12) and
`plans/2026-08-30-photoreal-render-overhaul-plan.md` (13). Triage commit `c5f04e1`
established which tasks were genuinely done; these are the rest.

### Group A — pure Python / schema (TDD: test first)
- [x] RF-02-05 `get_material` resolves family through the compiled finish map
- [x] RF-03-03 elevation draws opening divisions (mullions/transoms)
- [x] RF-03-04 balcony parapet `pattern` (solid | slatted) in schema + railings
- [x] RF-05-10 GLB size-budget test enforcing ASM-006
- [x] PR-05-01/02/03 viewer: full/floors fetch external GLB, inline gate light-only, copy GLB
- [x] PR-05-06 KTX2/Basis in `optimize_glb`, pass through when absent

### Group B — real CC0 asset cache (network, once)
- [x] PR-02-01 2K PBR sets for 7 families + interior/exterior HDRI from Poly Haven
- [x] PR-02-02 ATTRIBUTION.md with real source URLs, licence and SHA-256
- [x] PR-03-01 CC0 furniture GLBs per `_BUILDERS` kind

### Group C — Blender-side geometry and shading
- [x] PR-02-04 texture-first path in `make_procedural_material`
- [x] PR-03-04 instance imported furniture via linked object data
- [x] RF-05-01 upgrade the procedural furniture builders off box primitives
- [x] PR-05-04 `bake_lightmap(resolution)` + GLB inclusion

### Group D — viewer front-end (three.js)
- [x] RF-05-06 Vietnamese room labels + level tags as sprites
- [x] RF-05-07 two-point measurement tool (mm)
- [x] RF-05-08 section sliders on Y and Z via clipping planes
- [x] RF-05-09 layer toggles driven by object-name prefixes
- [x] PR-05-05 HDRI environment in the viewer templates

### Group E — build, publish, ledger
- [ ] RF-06-01 clean full build, `final` profile, with glTF
- [ ] PR-06-05 Cycles hero bake (CPU-only per hardware note; scope stated honestly)
- [x] RF-03-09 / RF-06-08 / PR-06-04 fidelity ledger to rev.4 + review section
- [ ] Republish `docs/`, commit, push

**Constraint on record:** this machine has no GPU render path (UHD 620, 2018 driver) —
Cycles is CPU-only, so a 12-view 512-sample bake is not a one-session operation. The
Cycles scope actually run will be reported rather than claimed.

## Review — 2026-09-03 Render plans closeout

Both open render plans taken from 22 outstanding tasks to 1. What follows
separates what was built from what was found to be *already* broken, because
most of this session's value was in the second category.

### Defects found in work previously recorded as complete

1. **The elevation dropped every facade element and window division.**
   `elevation.py` emitted `facade` and division primitives that no SVG or DXF
   writer had a branch for. Both were silently discarded, so the generated
   south elevation showed a blank wall while the ledger recorded (k) and (l) as
   resolved. Both writers now paint them; the south elevation carries 21 facade
   rects, 12 mullion bars and 98 parapet bands.
2. **The asset cache was entirely placeholder.** 64x64 textures, a 2x2-pixel
   HDRI, 412-byte empty GLBs, and an `ATTRIBUTION.md` whose every row read
   `source: placeholder`. Replaced with real Poly Haven CC0 assets (2048x2048
   PBR sets for six families, two HDRIs, ten furniture meshes) with source
   URLs, licence and SHA-256 recorded. `scripts/fetch_assets.py` reproduces it.
3. **`build_scene` never forwarded `show_neighbours`.** The keyword was
   accepted and dropped before `_build_command`, so `--show-neighbours` did
   nothing on any `build`. Fixed and covered by two tests.
4. **The textured material path sampled a single texel.** It was wired to
   `ShaderNodeTexCoord.UV`, and every mesh is a bmesh cube whose only UV layer
   is empty. Renders looked exactly like the untextured ones. Now driven from
   **Object** coordinates with `projection='BOX'`.
5. **`set_finish_map` was never called.** The S3 finish resolver ran and
   nothing consumed its result. Now installed per build, with `room_id`
   threaded to the floor and wall call sites, so the authored `finishes` block
   actually reaches the render: circulation and service floors become ceramic
   tile, WC and kitchen walls become tiled.
6. **Quantized GLB positions broke picking.** `gltf-transform quantize` stores
   POSITION as normalized Int16; the viewer's three.js (r128) raycasts those
   without applying the normalization, so a 20 m pick reported 902 m — the
   measurement tool and tap-to-focus were both silently wrong. Quantization
   dropped (costs ~2.4 MiB, well inside the 25 MiB budget) and a test asserts
   POSITION stays float.
7. **The pick ray itself was wrong.** `raycaster.setFromCamera` unprojects
   NDC z=0.5, and `animate()` drives `camera.near` to millimetres against a
   500 m far plane; at that ratio the direction collapsed to (0,0,-1)
   regardless of where you tapped. Replaced with a projection-matrix-free ray
   built from the camera's frustum angles.

### Built this session

- **Viewer tools** (RF-05-06..09): Vietnamese room labels and storey level tags
  as sprites, a two-point ruler reading millimetres, Y and Z section sliders on
  three.js clipping planes, and layer toggles by object-name prefix. Verified
  in Chrome against a served build: the ruler reported 4323 mm against 4322 mm
  computed from the hit points.
- **Viewer delivery** (PR-05-01..03, 05-05, 05-06): `full`/`floors` fetch an
  external GLB and `write_viewer` copies it beside the page; the 8 MiB inline
  ceiling now gates only the `light` build; an equirectangular environment map
  (a tone-mapped 512px JPEG of the cached HDRI, auto-exposed by metering the
  sky) drives reflections; KTX2 compression runs when a compressor is present
  and passes through when it is not.
- **Geometry and drawings**: slatted parapet pattern shared by the 3D scene and
  the elevation through one pure module (`parapet.py`); opening divisions drawn
  on the elevation; twelve procedural furniture builders rebuilt off box
  primitives with bevels, separated cushions, panelled doors, taps and cisterns;
  furniture instanced through linked mesh data.
- **`bake_lightmap(resolution)`** with a `--bake-lightmap` CLI flag.
- **`homedesign/hdri.py`**: a Radiance RGBE decoder with tone mapping and sky
  auto-exposure, so the HDRI can be previewed without Blender.

### Not done, and why

- **PR TASK-06-05, the full Cycles bake.** This machine has no GPU render path
  (UHD 620, 2018 driver — see `lessons.md`), so Cycles is CPU-only. The
  published stills are the `final` EEVEE profile at 1920x1080/256 samples,
  which took 2691 s (~45 min) for twelve views. Measured, rather than assumed:
  a Cycles pass on the `khach` view at the profile's 512 samples reached
  sample 41/512 in 6 min 41 s with Blender reporting **1 h 16 m remaining for
  that single frame** — about 17 hours for the twelve-view set. That is an
  overnight job on dedicated hardware, not a session step, so it is left open
  with this figure attached rather than silently ticked.
- **A question for the owner:** the design's `finishes.by_room_type` lists
  floor materials (`living: wood_board`, `bedroom: wood_board`), and S3 rule 3
  applies `by_room_type` to floors *and wall faces*. Living and bedroom walls
  therefore now render as wood boarding. That is faithful to the spec as
  written; if the intent was floors only, the fix is in the design's
  `finishes` block, not in the resolver.
