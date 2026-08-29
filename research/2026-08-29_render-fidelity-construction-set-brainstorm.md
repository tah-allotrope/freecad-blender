---
title: "Render Fidelity for the Construction Set"
date: "2026-08-29"
type: "brainstorm"
depth: "standard"
source_request: "a plan to further enhancement to 3d render for best accuracy and visual fidelity against contractor drawing for sharing with construction team making use of \"gloop\" skill during implementation"
slug: "render-fidelity-construction-set"
---

# Brainstorm: Render Fidelity for the Construction Set

## Problem & Why Now

The `contractor-as-drawn` model is measured, ledgered, validated and published — and the
picture it produces is not convincing. Looking at the shipped artifacts before writing a
word of this brief:

- `deliverables/contractor-as-drawn/png/contractor-as-drawn_exterior_front.png` is a
  **white massing tower standing alone on a green lawn**. No street, no neighbours, no
  facade articulation, flat untextured surfaces, the building occupying roughly 8% of the
  frame. A tube house is by definition wall-to-wall; this image depicts a building that
  cannot exist on that plot.
- `deliverables/contractor-as-drawn/png/contractor-as-drawn_khach.png` shows a **door leaf
  detached from its frame and clipping through the sofa**, box furniture, no skirting, no
  reveals, no ceiling, and walls blown out to white.

The fidelity ledger already says why, in its own words: facade articulation is absent and
it is *"the single biggest visual departure… the reason the 3D reads as massing rather than
as this building."* (`designs/contractor-as-drawn.fidelity.md` items k, l, m, n.)

Why now: the audience has changed. This model is no longer a family walkthrough — it goes
to the **construction team**, on their phones in the alley, as images pasted into Zalo, and
as A3 plates taped up beside the contractor's own sheets. In that setting an unconvincing
render is not merely ugly; it forfeits the authority the measurement work bought. The whole
value of this pipeline is that the render is downstream of a validated model, and nobody
extends that trust to an image that looks like a massing study.

The second reason now: the repo has **no 2D↔3D parity test and no render-fidelity test at
all**. 226 tests check SVG/DXF text content and camera math; the 3D output is untested
territory. The 2026-08-21 parity gauntlet proved the pattern — checklist, gloop loop,
codify each PASS as pytest — and it stopped at the 2D boundary. This project carries it
across.

## Current vs Desired State

- **Current state:**
  - One shared spec → one compiled model → four consumers (`plan2d`, `elevation`, `pdf`,
    `blender/build_scene`). Parity between 2D and 3D is guaranteed structurally, and
    verified only on the 2D side.
  - **Materials do not exist in the schema.** A repo-wide grep for
    `material|finish|texture|colour` in `spec/homespec.schema.json` returns one unrelated
    comment. All appearance comes from a single hardcoded 20-entry flat-Principled palette,
    `PALETTES["modern-minimal"]` in `blender/materials.py`, keyed by element kind. No
    textures, no UVs, no image maps, no per-design override.
  - **Everything is a box.** `blender/geom.py::make_box` / `make_hinged_box` build walls,
    floors, openings, furniture. Twelve procedural furniture kinds, all box primitives.
  - **Openings are undivided rectangles** — no mullions, transoms or panelling. Balcony
    railings are a plain 1100 mm solid parapet, not the drawn pattern.
  - **Lighting is one fixed sun** at 55°/35° (decorative, not solar; `north_deg` unset
    because the approval photo's compass glyph is unreadable), one weak area fill, and one
    area light per room sized `clamp(area_m2 * 2.2, 20, 90)`.
  - `_add_neighbour_massing` exists and is gated on `site.context.neighbours` — and no
    neighbours appear in the shipped render.
  - Viewer: orbit, pinch, tap-to-focus, reset, floor tabs with a synced plan pane and 4.5%
    ghosting of adjacent storeys. **No measure tool, no room labels in 3D, no level tags,
    no layer toggles, no clipping plane, no markup.**
  - Publishing is manual file copies into `docs/`. CI is ruff + pytest + `sync_skill.py`;
    **there is no Pages deploy workflow.**
- **Desired state:** a construction-grade set that survives being put next to the
  contractor's own elevation *and* next to a photograph of a real Saigon tube house:
  articulated facade read off the MD sheet, subdivided openings, real party walls and alley,
  a finish schedule the crew can read, furnished credible interiors, and a viewer that
  measures, labels, sections and isolates — delivered to phone, Zalo and A3 from one final
  build.
- **Key repo surfaces:**
  - `spec/homespec.schema.json` — closed contract, `additionalProperties: false` everywhere;
    `meta.style` is a one-value enum (`modern-minimal`); no material vocabulary
  - `src/homedesign/model.py` — `CompiledModel`, `model_hash` (any schema addition
    invalidates every render sidecar)
  - `src/homedesign/blender/build_scene.py` (~628 lines) — `build_walls`,
    `build_floors_and_stairs`, `_add_balcony_parapets`, `_add_stair_balustrades`,
    `_add_top_storey_ceilings`, `_build_roof_structures`, `_add_neighbour_massing`,
    `build_environment`, `add_interior_lights`, `add_cameras`, `_set_engine`, `render`
  - `src/homedesign/blender/materials.py` — the hardcoded palette
  - `src/homedesign/blender/joinery.py::build_opening_furniture` — frame/glass/leaf; source
    of the detached-leaf defect
  - `src/homedesign/blender/railings.py`, `roof.py`, `furnish.py`,
    `procedural_furniture.py`, `geom.py`
  - `src/homedesign/camera_fit.py` — all camera maths, pure, already unit-tested
  - `src/homedesign/render_profiles.py` — `preview` / `final` / `cycles`
  - `src/homedesign/orchestrator.py::_CANDIDATES` — **Blender 4.1 legacy EEVEE pinned; do
    not touch** (`test_blender_candidates_prefer_legacy_eevee_build`)
  - `src/homedesign/plan2d.py`, `elevation.py` — the 2D consumers that must stay in step
  - `src/homedesign/viewer.py` — `optimize_glb`, `write_viewer`, `write_floor_viewer`,
    `_load_call`, `INLINE_GLB_LIMIT_BYTES = 8 MiB` (base64url, to dodge the Artifacts
    entropy filter)
  - `src/homedesign/assets/viewer_template.html`, `floor_viewer_template.html`
  - `src/homedesign/publish.py::verify_fresh` — blocks publish on stale sidecar hashes
  - `designs/contractor-as-drawn.json`, `.measurements.md` (rev.3), `.fidelity.md` (rev.3)
  - `contractor/` — five vector PDFs + `approval drawing.jpg`;
    `output/contractor_pdf_png/` holds the rasterisations
  - `tests/test_plan2d.py:451+` — the codified 2026-08-21 parity block, the pattern to copy
  - `reports/2026-08-21-svg-pdf-parity-checklist.md` — the gauntlet format to reuse

## Resolved Decisions

**Interviewed**

- **DEC-001:** The driving problem is **visual credibility**, not a suspected drawing
  error. The render currently reads as a massing study and that is what disqualifies it.
  Accuracy is therefore the *constraint* on this work, not its goal — every realism gain
  must be traceable to the sheets rather than invented.
- **DEC-002:** Three delivery channels, all of them: **phone/tablet GLB viewer on site**,
  **images pasted into Zalo**, and **printed A3 plates beside the contractor's PDFs**. Each
  imposes a different fidelity surface — viewer UX, self-explanatory burned-in labelling,
  and print legibility respectively.
- **DEC-003:** **Dual bar.** Geometric half: our render overlaid on the contractor's own
  `MẶT ĐỨNG CHÍNH` elevation at identical scale, tolerance stated in millimetres —
  in-repo, unfakeable, and it makes "accurate" a number. Visual half: a named photoset. This
  is exactly gloop's "taste plus a number beats taste alone".
- **DEC-004:** The named visual bar is **Vo Trong Nghia's "Stacking Green", Ho Chi Minh
  City, ArchDaily photoset**. Same typology, same ~4 m width, same light-well problem,
  professionally photographed inside and out, freely fetchable. Its planted facade is
  atypical on purpose — the critic judges **material, light and scale**, not styling.
- **DEC-005:** **Full scope: Blender layer, schema/compiler, and the spec data itself.** The
  fidelity ledger is now the backlog, not the excuse. This explicitly reverses last pass's
  DEC-003 ("no schema/compiler changes").
- **DEC-006:** Finishes enter through a **`finishes` block in the schema driven by
  procedural PBR node groups** — tile grids, plaster noise, wood grain, brushed aluminium.
  No image assets, so the GLB stays small and the base64 inline path survives. Bonus: the
  same block prints as a **finish schedule the crew can read**, which the render alone can
  never be (ledger item n: "renders must not be read as a finish schedule").
- **DEC-007:** Facade work splits into **two independently judged gauntlet pieces**:
  *"openings read as real windows"* (mullions, transoms, panelling, patterned railings —
  ledger l and m) and *"the facade reads as this building"* (fins, cornice/coping bands,
  framed panels, awnings — ledger k). Each gets its own critic pass against the MD
  elevation. Bundling them is how a gauntlet exits early on the weaker half.
- **DEC-008:** Facade elements become a **first-class `facade_elements[]` construct**
  authored from the contractor's elevation, not a per-design Blender hook. Closing the
  visual gap and closing the accuracy gap are then the same act, and `elevation.py` gets
  something to draw so 2D/3D parity holds.
- **DEC-009:** **The sun stays decorative — light it better.** No solar model, no
  latitude/date rig. Re-tune sun angle and energy, and rebuild the interior fill so rooms
  stop blowing out to white and the facade gets modelling. Renders must continue to carry
  the ledger's disclaimer that shadows are not a daylight analysis.
- **DEC-010:** **Build the party walls and the alley.** Fix/enable neighbour massing so both
  flanks are hard against party walls; replace the green lawn with a real alley section —
  road width, kerb, opposite-side massing. This single change converts the image from model
  to building, and party-wall contact is a construction fact the crew needs to see. No
  entourage (no motorbikes, cables, signage) — invented content that reads as promises.
- **DEC-011:** **Full interior realism, furniture included.** Not just the shell: credible
  furniture geometry replacing the twelve box primitives. Accepted knowingly — it dresses a
  set the contractor is not building and it inflates the GLB, which DEC-012 pays for.
- **DEC-012:** **Two viewer builds.** A decimated, light GLB inlined for the phone-on-4G
  channel; a full-detail build for the meeting-room laptop. This removes the 8 MiB ceiling
  as a design constraint at the cost of a doubled export path. **Mitigation required:** the
  two builds must be unmistakably labelled in the viewer chrome, or the crew will read the
  wrong one.
- **DEC-013:** **Crew tools in the viewer: all four.** Vietnamese room labels + level tags
  floating in 3D, a two-point measure/dimension readout, a section/clipping plane slider,
  and layer toggles (structure / walls / openings / furniture). The measure tool in
  particular raises the stakes on the accuracy work — the crew can now test it, which is
  the point.
- **DEC-014:** **The measurable exit is elevation-overlay parity in millimetres.** Project
  the 3D through an orthographic front camera and assert its silhouette and opening
  positions match `elevation.py`'s SVG — and thereby the MD sheet — within a stated
  tolerance. This closes the repo's biggest test hole and gives the gloop critic a number
  it cannot argue with.
- **DEC-015:** **Seven gauntlet pieces**, each with its own half of the dual bar and its own
  codified pytest as the exit gate:
  1. interior joinery / clipping defects
  2. materials + finish schedule
  3. opening subdivision
  4. facade elements
  5. party walls + alley context
  6. interior realism + furniture
  7. viewer crew tools

  Pieces 1–4 are sequential (each builds on the last's geometry); 5–7 can run in parallel.
- **DEC-016:** **EEVEE only, all the way.** No Cycles hero pass. Fidelity investment goes
  into geometry, materials and light *placement* rather than the integrator, and everything
  the crew sees comes from one engine — no explaining why the cover image looks different
  from the gallery. Keeps every gauntlet round at ~6–10 minutes, and a fast loop is a loop
  that actually iterates.
- **DEC-017:** **One re-render + re-publish at the end**, plus the missing **GitHub Actions
  Pages deploy workflow**. Accept stale `deliverables/` during the loop; land a single
  `build --profile final` + `publish` + docs sync when the gauntlet exits, and generate the
  A3 plates and a Zalo-sized image pack from that same run.

**Self-answered from the repo** (the interview did not need these)

- **DEC-018:** **Do not touch `orchestrator._CANDIDATES`.** Blender 4.1 legacy EEVEE is
  first deliberately; EEVEE Next renders every lit surface blood red on this machine's Intel
  UHD 620 (white wall → RGB 194,34,53), and the ordering is pinned by
  `test_blender_candidates_prefer_legacy_eevee_build` and documented in `AGENTS.md`,
  `docs/lessons-learned.md` (2026-08-08) and `lessons.md`. "Higher fidelity" here can never
  mean "newer engine".
- **DEC-019:** New render logic lands as **pure functions in `src/homedesign/`, tested
  there; only the `bpy` binding goes in `src/homedesign/blender/`.** This is the established
  pattern (`camera_fit.py` + `tests/test_camera_fit.py`), and it is the only way any of this
  is testable in CI, which never installs `bpy`.
- **DEC-020:** Any new geometry shared by 2D and 3D goes through a **pure helper both
  consumers call**, as `plan2d._svg_furniture` and `blender/furnish` already share
  `placement.plan_room`. Diverging here re-opens the 2D/3D split the ledger closed on
  2026-08-17.
- **DEC-021:** `meta.style` is a **one-value enum**. A `finishes` block (DEC-006) either
  extends that enum or sits beside it; it cannot be smuggled in as a style variant.
- **DEC-022:** The gauntlet checklist follows the 2026-08-21 format and lands in
  `reports/2026-08-29-render-fidelity-checklist.md` — rows with PASS / FAIL /
  DELIBERATE-DEVIATION, each PASS codified into `tests/`.
- **DEC-023:** Every deviation this pass introduces or resolves updates
  `designs/contractor-as-drawn.fidelity.md` to rev.4. Items k, l, m, n should close; items
  a (orthogonal plot collapse), c (inferred lift shaft) and g (stair depth 4000 vs drawn
  3200) stay open and are **not** to be "fixed" by rendering.
- **DEC-024:** Room names stay **Vietnamese exactly as printed on the sheets** (last pass's
  DEC-010). For a construction-team audience this matters more, not less — the 3D labels of
  DEC-013 are only traceable if they are the sheet's own strings.
- **DEC-025:** `gltf-transform` (dedup / prune / quantize / draco) is already wired in
  `viewer.optimize_glb` and silently skips when `npx` is absent. The light build of DEC-012
  depends on it, so its availability must become an explicit, checked precondition rather
  than a silent no-op.

## Assumptions & Constraints

- **ASM-001:** The `MẶT ĐỨNG CHÍNH` elevation sheet carries enough resolvable facade detail
  — fin positions, band heights, panel divisions, railing pattern — to author
  `facade_elements[]` without invention. If it does not, the residual becomes ledger
  entries, not guesses. **Verify at the start of piece 4.**
- **ASM-002:** The alley width and opposite-side massing (DEC-010) are readable from the
  site plan on the sheets. If not, they become a stated, labelled approximation.
- **ASM-003:** Procedural node-group materials (DEC-006) survive glTF export well enough to
  reach the viewer. glTF has no procedural node support, so they must bake to small textures
  or vertex colours on export. **This is the load-bearing assumption behind DEC-006's
  "the GLB stays small" claim and must be tested in piece 2, not at the end.**
- **ASM-004:** The door-leaf-detached-from-frame defect visible in `khach.png` originates in
  `blender/joinery.py::build_opening_furniture`, and furniture interpenetration in
  `placement.plan_room` / `procedural_furniture.build_item`. Both are correctness bugs with
  bounded fixes, which is why they are piece 1.
- **ASM-005:** Twelve views on EEVEE `final` stay under ~10 minutes end to end even after
  party walls, facade elements and furnished interiors are added.
- **CON-001:** **Blender 4.1 legacy EEVEE only.** No EEVEE Next, no raytracing, no
  screen-space GI, no GPU Cycles (zero devices enumerated). CPU Cycles is ~169 s/view
  against ~30 s/view for EEVEE.
- **CON-002:** `additionalProperties: false` on **every** schema object. Nothing can be
  annotated, provenanced or referenced back to a sheet from inside the spec — hence the
  `.measurements.md` and `.fidelity.md` sidecars.
- **CON-003:** **Any schema addition changes `model_hash`**, which makes every existing
  render sidecar stale and causes `publish.verify_fresh` to block. A full re-render and
  re-publish is not optional; it is a scheduled phase (DEC-017).
- **CON-004:** `viewer._load_call` inlines base64url only up to `INLINE_GLB_LIMIT_BYTES`
  = 8 MiB, then silently falls back to a relative file reference that breaks in published
  artifacts. Silent is the dangerous part — the size budget needs a test (see Open
  Questions), regardless of DEC-012.
- **CON-005:** CI never installs `bpy`; `tests/test_blender_geometry.py` opens with
  `pytest.importorskip("bpy")`. Every fidelity assertion that must run in CI has to be
  expressible against the compiled model or the SVG, not against a rendered scene.
- **CON-006:** `docs/` is the GitHub Pages root and is synced **by hand** (commit `254dccf`).
  The deploy workflow of DEC-017 is unclaimed work being adopted by this project.
- **CON-007:** `output/` is gitignored and disposable; finals belong in `deliverables/`.
- **CON-008:** Closed 16-value room-type enum, rectangular plot, axis-aligned walls,
  `check_room_support` cantilever limit, one stair per storey, roof `voids` only on
  `type: "flat"`.

## Approaches Considered

- **Chosen:** A **seven-piece gauntlet** (DEC-015) run with `gloop`, each piece looping a
  builder against a separate harsh critic until the critic picks ours blind against its half
  of the dual bar, and each piece exiting on a codified pytest — with the millimetre
  elevation-overlay test (DEC-014) as the spine. It is the only approach where "more
  convincing" and "more accurate" are measured by the same instrument, and it inherits a
  workflow this repo has already proven on the 2D side.
- **ALT-001: Two passes, accuracy first then beauty.** — Rejected. Cleanly separated, but it
  leaves the exterior ugly for a long time while the stated problem (DEC-001) *is* that it
  looks unconvincing.
- **ALT-002: Three fat pieces — exterior, interior, viewer.** — Rejected. Less orchestration
  overhead, but the critic then judges a bundle, which is precisely how a gauntlet exits
  early on a piece that is still weak.
- **ALT-003: Poly Haven image textures via the Blender MCP.** — Rejected for the main path
  by DEC-006. A far higher photoreal ceiling, but it costs UVs and texture memory on the
  UHD 620 and would blow the inline ceiling for the phone build. Reconsider only if
  procedural materials lose the blind comparison against Stacking Green.
- **ALT-004: Better hardcoded palette, no schema change.** — Rejected. Zero blast radius and
  no re-hash, but the render still cannot say what any surface *is*, and a finish schedule
  is exactly what a construction team asks for next.
- **ALT-005: Cycles hero shots for the A3 plates.** — Rejected by DEC-016. Real GI on two or
  three views costs ~10 minutes and would genuinely show — but two engines in one deliverable
  means explaining why the cover image looks unlike the gallery.
- **ALT-006: Baked-lighting GLB re-export** (`activeContext.md` 2026-08-22, "not done"). —
  Deferred, not rejected. It is the lever that targets the phone-on-site channel
  specifically, and DEC-016's EEVEE-only decision does not resolve the viewer's flatness.
  See Q-004.
- **ALT-007: Ship the GLB as a sibling file on Pages.** — Rejected in favour of DEC-012's
  two builds. It removes the ceiling entirely and works on Pages, but forfeits the Claude
  Artifacts path and still needs the deploy workflow.

## Out of Scope

- Upgrading Blender or reaching for EEVEE Next / GPU Cycles in any form.
- A solar/daylight analysis, sun-path study, or resolving `north_deg` (DEC-009).
- Re-rendering or modifying `tubehouse-dream`.
- Street entourage: motorbikes, power lines, signage, planting (DEC-010).
- Re-opening ledger items a (orthogonal plot collapse), c (inferred lift shaft) and g
  (stair depth vs drawn) — they are drawing findings, not render defects.
- Structural, MEP or code-compliance interpretation; setback and height questions stay in
  `reports/2026-08-12-contractor-drawing-set-review.html`.
- The brief-restored variant spec (the second building, with lease floors).
- Any git commit or push without explicit instruction.

## Open Questions

1. **Q-001:** What is the plot's address, or which way does the front face? It unlocks
   Google Street View of the actual alley as a *third*, strongest context bar for piece 5,
   and gives real alley width and opposite-side massing.
   - **Recommended default:** Derive the alley section from the sheets' site plan, keep
     `north_deg` unset per DEC-009, and run piece 5 against Stacking Green's street
     photography alone.
   - **Why this matters:** Decides whether the party-wall/alley piece is verified against
     the real street or against a generic Saigon alley — the difference between "belongs
     there" and "looks plausible".
2. **Q-002:** How is DEC-011's credible furniture sourced — upgraded procedural geometry, or
   Sketchfab/Poly Haven imports via the Blender MCP?
   - **Recommended default:** Upgraded procedural geometry for everything that ships in the
     light phone build; a handful of imported hero pieces in the heavy desktop build only.
     Keeps licensing, file size and determinism on the channel that matters most on site.
   - **Why this matters:** Imported assets carry licence terms, arbitrary polycounts and
     image textures — all three of which DEC-006 and DEC-012 were arranged to avoid.
3. **Q-003:** What tolerance does the elevation-overlay parity test assert (DEC-014)?
   - **Recommended default:** ±50 mm on silhouette and opening edges at sheet scale, with
     any deliberate deviation listed by name in the test rather than widened into the
     tolerance.
   - **Why this matters:** Too tight and the test fails on the plot's known orthogonal
     collapse (ledger item a); too loose and the critic's "number" means nothing.
4. **Q-004:** Given DEC-016 (EEVEE only), does the *viewer* still get baked lighting, or
   does it stay flat while only the stills improve?
   - **Recommended default:** Add baked lighting as an eighth, optional gauntlet piece run
     after the seven — ~25 minutes of render, and it is the only lever that makes the
     phone-on-site channel look like the gallery.
   - **Why this matters:** DEC-016 settled the *render engine*; it did not settle the
     viewer, and the viewer is the primary channel per DEC-002.
5. **Q-005:** Should the GLB size budget become a hard failing test even though DEC-012
   removed the 8 MiB constraint by splitting the builds?
   - **Recommended default:** Yes — a per-build budget test (light build well under 8 MiB,
     heavy build bounded by patience). CON-004's failure mode is *silent*, and a silent
     break in the published Pages copy is the worst possible outcome for an on-site link.
   - **Why this matters:** Splitting the builds relieved the pressure but removed the
     forcing function; nothing then stops the light build drifting over the line.

## Suggested Next Step

Run `/plan render-fidelity-construction-set` to turn this into a multi-phase implementation
plan. The plan should emit, per gauntlet piece, a paste-ready `gloop` prompt naming that
piece's half of the dual bar and its codified pytest exit gate.
