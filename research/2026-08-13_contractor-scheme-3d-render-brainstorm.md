---
title: "3D Render of the Contractor's As-Drawn Scheme"
date: "2026-08-13"
type: "brainstorm"
depth: "standard"
source_request: "the 3d render of this new drawing by contractor given more effective methods learnt previously"
slug: "contractor-scheme-3d-render"
---

# Brainstorm: 3D Render of the Contractor's As-Drawn Scheme

## Problem & Why Now

Five PDF sheets arrived in `contractor/` and were reviewed yesterday
(`reports/2026-08-12-contractor-drawing-set-review.html`, 13 findings). The review is
prose and 2D crops. What nobody has seen is **the building the contractor actually
drew, in three dimensions** — and this is a 3.95 × 25 m seven-level tube house, the
typology where plan and section conceal the most: the light well is a slot you cannot
read from a plan, the core stacks through seven plates, and the roof carries a plant
room nobody has looked at from outside.

Why now: the pipeline is finally capable of this. The methods learnt over the last
fortnight are exactly the ones this task needs —

- **Legacy EEVEE on Blender 4.1 is the only working render path** on this machine, and
  the candidate ordering already enforces it (`orchestrator._CANDIDATES`). The 11.3-hour
  Cycles gallery that made rendering unaffordable is no longer the only route: a
  12-view `final` gallery now costs single-digit minutes.
- **The camera-truth fixes shipped** — `camera_fit.fit_distance` sign, facade anchoring,
  interior cameras constrained inside their rooms. Before that, a render of this set
  would have depicted a lawn.
- **glTF + the self-contained viewer** turn one build into an interactive deliverable,
  which on this hardware is worth more per minute than stills.
- **Model-hash provenance sidecars** mean the gallery cannot silently ship images of an
  older model.
- **PDF forensics from yesterday** — 8–16× rendering, calibrated mm/pt, reading outlined
  glyphs visually — is the technique that gets millimetres out of a text-less drawing set.

The audience is the family. The subject is the contractor's scheme *exactly as drawn* —
not the brief's building — so the render carries evidentiary weight in the conversation
finding C-01 opened.

## Current vs Desired State

- **Current state:** `contractor/` holds five vector PDFs with no extractable text.
  `designs/tubehouse-dream.json` is the *brief's* five-storey scheme, already compiled,
  rendered (9 views), exported to GLB and published. The contractor's seven-level scheme
  exists only as paper. `homedesign` has never ingested a real-world drawing set.
- **Desired state:** `designs/contractor-as-drawn.json` compiles clean, passes the check
  registry, renders a 12-view gallery on legacy EEVEE `final`, exports a GLB and a
  self-contained viewer, and is published as an artifact the family can walk through —
  with a sidecar ledger recording every place the model departs from the sheet.
- **Key repo surfaces:**
  - `spec/homespec.schema.json` — the closed contract (`additionalProperties: false`
    everywhere; 12-value room `type` enum; rectangular `site`)
  - `src/homedesign/compiler.py` — wall derivation, floor voids (`_derive_floor_voids`)
  - `src/homedesign/checks.py` — the five-rule registry
  - `src/homedesign/stairs.py` — Blondel sizing, `straight`/`u_return` only
  - `src/homedesign/blender/build_scene.py` — `_set_engine`, lighting rig, cameras
  - `src/homedesign/camera_fit.py` — all camera placement; you choose the room, not the position
  - `src/homedesign/render_profiles.py`, `orchestrator.py` — profiles, Blender discovery
  - `src/homedesign/viewer.py` — inlines the GLB base64 if ≤ 8 MB
  - `tests/test_validate.py`, `tests/test_camera_placement.py`
  - `designs/tubehouse-dream.json` — the worked example to imitate structurally, **not** to copy from

## Resolved Decisions

**Interviewed**

- **DEC-001:** The render is a **presentable, family-facing visual**, not a coordination
  diagnostic — so the realism items (neighbour massing, parapets, ceilings) matter and
  the `final` profile is justified.
- **DEC-002:** Model the scheme **exactly as drawn** — single-family throughout, no lease
  floors, no F2 lobby door, rooftop plant room present. Deltas from the brief stay in the
  review, not in the geometry. Rendering a building nobody drew would destroy the render's
  evidentiary value.
- **DEC-003:** Where the schema cannot express the drawing, **approximate within today's
  schema and record every departure in a fidelity ledger**. No schema/compiler changes in
  this pass.
- **DEC-004:** **12-shot walkthrough** — two exteriors plus one or more interiors on every
  one of the seven levels, including the stair core / light well looking up.
- **DEC-005:** Deliver **PNG gallery + GLB + self-contained viewer, published as an
  artifact**. The interactive model costs seconds on top of the render.
- **DEC-006:** Punch a **roof `void`** over the light well and ledger the glass cap. A
  glass cap transmits light; a solid slab does not, and the renderer has no glass — so the
  void is the truthful *depiction* even though the solid cap is the literal *geometry*.
  Without it the core shot renders black.
- **DEC-007:** **Accept the wide-lens interiors.** No cutaway view kind — that is a schema
  + camera_fit + wall-suppression + tests project of its own. If a shot reads badly, swap
  the room rather than rewrite the camera.
- **DEC-008:** **`--profile final`, legacy EEVEE, all 12 views.** ~30 s/view → ~6 min
  render plus ~2 min scene build.
- **DEC-009:** **Read the contractor's printed dimension chains at 8–16× zoom** as the
  authoritative source; use vector measurement (calibrated 43.0 mm/pt from two independent
  known dimensions) only to fill gaps and cross-check. The printed figures are correct
  regardless of the sheets' ~1:122 plot scale. This is the bulk of the work.
- **DEC-010:** **Vietnamese-only room names**, exactly the strings on the sheets
  (`P.KHÁCH`, `P.NGỦ 1`, `P.THỜ`, `SÂN THƯỢNG`). Maximum traceability back to the drawing
  set, and the family's own language.

**Self-answered from the repo** (the interview did not need these)

- **DEC-011:** Spec lives at `designs/contractor-as-drawn.json` — repo convention is
  `designs/*.json`, kebab-case, and `tests/test_camera_placement.py` sweeps that directory
  automatically.
- **DEC-012:** Ledger lives at `designs/contractor-as-drawn.fidelity.md`, beside the spec.
  It *cannot* live inside the spec: every schema object sets
  `"additionalProperties": false`, so there is no side-channel for provenance.
- **DEC-013:** **Seven storeys, `level` 0–6.** The `lửng` is level 1 with its own
  `height_mm` — `height_mm` is per-storey and `base_z` accumulates, so a mezzanine needs
  no special construct. It satisfies `check_room_support` because level-0 rooms tile the
  full footprint beneath it.
- **DEC-014:** `SÂN THƯỢNG` is **level 6**: `balcony` rooms for the open terrace (auto
  1100 mm parapets — the review's T1-2 item, already shipped), `storage` for the
  2000 × 1900 lift plant room, plus the stairwell/elevator overrun. The single `roof`
  object goes on level 6, `type: "flat"` — `voids` raise `NotImplementedError` on any
  other roof type (`blender/roof.py:33`), which DEC-006 depends on.
- **DEC-015:** Room-type mapping (12-value closed enum; the Vietnamese name carries the truth):

  | Sheet label | `type` | Note |
  |---|---|---|
  | `P.KHÁCH` | `living` | |
  | `P.NGỦ` | `bedroom` | |
  | `P.SINH HOẠT` | `living` | family room |
  | `P.THỜ` | `living` | no altar-room enum value; habitable, needs daylight |
  | `BẾP` / `ĂN` | `kitchen` / `dining` | |
  | `WC` | `bathroom` | |
  | `KHO` | `storage` | |
  | `NƠI ĐỂ XE` | `garage` | |
  | `HÀNH LANG` | `hall` | |
  | `THANG` | `stairwell` | |
  | `THANG MÁY` | `elevator` | |
  | `LÔ GIA` / `BAN CÔNG` / `SÂN THƯỢNG` | `balcony` | gets auto parapets |
  | `Ô KỸ THUẬT THANG MÁY` | `storage` | rooftop plant room |

- **DEC-016:** Set `site.context: {neighbours: true, street_depth_mm: …}`. A tube house is
  by definition sandwiched; rendering it free-standing in a green field is architecturally
  misleading, and the schema already supports the massing.
- **DEC-017:** Storey heights come from **Section A-A's level tags**, not from re-deriving
  them. Read so far: `+17.200 / +20.600 / +23.800 / +25.800` → 3400 / 3200 / 2000 mm. The
  lower tags must be read in the same pass. The top 2000 mm is presumably the plant room /
  overrun, to be confirmed.
- **DEC-018:** The light well is expressed **by omission** — leave its footprint untiled on
  every level. Floor slabs are emitted per-room (`build_scene.py:87-97`), so an untiled
  footprint is automatically open. This is exactly how `tubehouse-dream` does it.
- **DEC-019:** The ~7.2° skewed boundaries collapse to an **orthogonal plot rectangle**
  (≈3960 × 25000 mm). The tapering rear yard is simply untiled plot. `site` has only
  `plot_width_mm` / `plot_depth_mm` and every downstream path assumes a rectangle. Ledger
  entry; the review's C-03 setback finding is unaffected and stays in the review.
- **DEC-020:** The ~8 winder treads become **`mode: "u_return"`**. The enum is
  `auto|straight|u_return|none`; `stairs.py` emits only those two forms. The measured shaft
  (two 1154 mm flights + 697 mm well ≈ 3005 mm short side) clears `MIN_URETURN_SHORT_MM`
  = 1900, so it fits. Tread count and riser are re-derived per storey height — the model
  will *not* reproduce finding C-07's copy-pasted stair block, which is itself a ledger entry.
- **DEC-021:** The spec must **compile clean**. Where a check fires, adjust the model
  minimally, and record the adjustment in the ledger *and* as a candidate review finding —
  a check failure on an as-drawn model is information about the drawing, not just an
  obstacle.
- **DEC-022:** Add the spec explicitly to `tests/test_validate.py` (which hardcodes only
  the two `spec/examples` files). `tests/test_camera_placement.py` picks up `designs/*.json`
  for free.
- **DEC-023:** Build with
  `homedesign build designs/contractor-as-drawn.json --profile final --gltf`.
  Outputs land in `output/{compiled,svg,dxf,blend,png,gltf,viewer}/`.
- **DEC-024:** **Do not touch `orchestrator._CANDIDATES`.** Blender 4.1 first is deliberate
  and pinned by `test_blender_candidates_prefer_legacy_eevee_build`.

## Assumptions & Constraints

- **ASM-001:** The printed dimension chains are internally consistent enough to tile a
  closed plan on each level. Where a chain does not close, take the room-side figures and
  ledger the residual.
- **ASM-002:** A room edge facing the light well is not shared with another room, so
  `_derive_walls` classifies it `exterior` and a window onto the well is authorable as
  `between: [room, "exterior"]`. This is what makes `check_habitable_daylight` satisfiable
  for interior rooms in a 3.95 m-wide house. **Verify on first compile** — if it fails, the
  daylight rule becomes the first real finding this exercise produces.
- **ASM-003:** Section level tags are structural floor-to-floor, matching `height_mm` semantics.
- **ASM-004:** 12 views × ~30 s + ~2 min build + GLB export ≈ **under 10 minutes** end to end.
- **ASM-005:** All seven levels are covered by the five sheets (trệt+lửng / 2+3+4 / 5+sân
  thượng / mái+elevation / section A-A), so no level has to be inferred.
- **CON-001:** **Blender 4.1 legacy EEVEE only.** EEVEE Next (4.2+) renders every lit
  surface blood red on this machine's Intel UHD 620. Cycles enumerates zero GPU devices, so
  it is CPU-only at ~169 s/view.
- **CON-002:** `additionalProperties: false` throughout the schema — no annotation,
  provenance or drawing reference can live in the spec. Hence DEC-012.
- **CON-003:** Closed 12-value room-type enum: no altar room, plant room, terrace, shop or void.
- **CON-004:** Rectangular plot, axis-aligned walls only, no cantilever beyond 20% of a
  room's area (`check_room_support` is a hard error).
- **CON-005:** One stair per storey (`stairs` is an object, not an array), and it must sit
  in a `stairwell`-typed room.
- **CON-006:** Roof `voids` are valid only on `type: "flat"`.
- **CON-007:** `output/` is gitignored and disposable; finals belong in `deliverables/`.
- **CON-008:** There is no north angle anywhere in the schema, and the contractor's sheets
  have no north point either (finding C-04). The sun rig is fixed (55°/35°), so **shadows in
  this render are decorative, not solar**. Ledger entry, and it must not be presented to the
  family as daylight analysis.

## Approaches Considered

- **Chosen:** Encode the as-drawn scheme as a new `designs/contractor-as-drawn.json` by
  reading the printed dimensions, approximate the inexpressible geometry, ledger every
  departure, render 12 views on legacy EEVEE `final`, export GLB + viewer, publish. — It is
  the only route that produces a family-facing picture *and* leaves an auditable trail from
  every number back to a sheet, without any code change.
- **ALT-001: Extend the schema first** (site polygon, glazed roof-light, cutaway views). —
  Rejected for this pass. The site polygon touches every wall-derivation path, and the
  render is wanted now. The ledger becomes the backlog for this work rather than its excuse.
- **ALT-002: Model directly in Blender**, bypassing the spec. — Rejected: forfeits the check
  registry, the 2D drawing set, model-hash provenance and every test. The pipeline's whole
  value is that the render is downstream of a validated model.
- **ALT-003: Copy `tubehouse-dream.json` and overwrite what differs.** — Rejected by
  DEC-009. Same plot, same core position, and that is exactly the trap: it would inherit the
  brief's geometry wherever attention lapsed, silently defeating "exactly as drawn".
- **ALT-004: Wait for the DWG.** — Rejected: blocks on the contractor's reply. The request is
  already in yesterday's review and can proceed in parallel; if the DWG arrives, it becomes
  a verification pass against a model that already exists.
- **ALT-005: Cycles for the hero shot.** — Deferred. Three extra minutes for real GI on the
  cover image is cheap and may be worth doing after the EEVEE gallery is seen.

## Out of Scope

- Any schema, compiler, checks or Blender code change.
- A brief-restored variant spec (the second building, with lease floors and an open well).
- The A3 PDF brief (`homedesign pdf`) and the `spec/briefs/` entry it needs.
- Revising `research/2026-08-12_tubehouse-lift-comparison.md` for the measured 2.4 m² shaft
  and 7 stops — flagged in §07 of yesterday's review, still owed, still separate.
- Re-rendering or modifying `tubehouse-dream`.
- Structural, MEP or code-compliance interpretation; the setback and height questions stay
  in the review where they belong.
- Any git commit or push.

## Open Questions

1. **Q-001:** Should the published artifact stay purely presentational, or carry yesterday's
   13 findings alongside the renders?
   - **Recommended default:** Purely presentational — a clean walkthrough for the family,
     with one line linking to the review artifact. DEC-005 chose the gallery-and-viewer
     option over the findings-pairing option, so this follows it.
   - **Why this matters:** Decides whether the family's first look at the house is a house or
     an argument.
2. **Q-002:** Where do the finals land — `deliverables/contractor-as-drawn/`?
   - **Recommended default:** Yes. `output/` is disposable and one `git clean -xdf` from
     gone; `deliverables/` exists for exactly this.
   - **Why this matters:** A gallery that costs 10 minutes is cheap to lose, but the GLB the
     family is walking through should not vanish.
3. **Q-003:** If the GLB exceeds 8 MB, `viewer.py` stops inlining it and falls back to a
   relative file reference — which breaks a published artifact, since the CSP blocks every
   external fetch.
   - **Recommended default:** Check the size after export; if over, cut furniture from the
     export rather than dropping the viewer.
   - **Why this matters:** Seven levels is 40% more geometry than `tubehouse-dream`, so this
     is likely, not hypothetical.
4. **Q-004:** When a dimension chain does not close, prefer the drawing's stated figure or
   the sum of its parts?
   - **Recommended default:** The room-side figures, with the residual recorded in the ledger.
   - **Why this matters:** It is the difference between a model that tiles and a model that
     leaves 30 mm slivers throwing `room_overlap` across seven levels.

## Suggested Next Step

Run `/plan contractor-scheme-3d-render` to turn this into a multi-phase implementation plan.
