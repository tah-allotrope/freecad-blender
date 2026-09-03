---
title: "Photoreal Render Overhaul"
date: "2026-08-30"
type: "brainstorm"
depth: "standard"
source_request: "idea to improve current 3d render as even the latest version after \"gloop\" skill use seem rudementary for sharing and doesnt resemble drawing (front facing pillar missing, etc) need to leverage gloop, design, blender skills and tools to generate smth looking visually impressive, no past limitation shall be applied this time"
slug: "photoreal-render-overhaul"
---

# Brainstorm: Photoreal Render Overhaul

## Problem & Why Now

The 2026-08-29 render-fidelity pass shipped its **plumbing** and never shipped its
**content**. That is the whole diagnosis, and it is verifiable in one command:

```
storey                facade_elements
0 Ground                    1
1 Mezzanine                 0
2 Floor 2                   0
3 Floor 3                   0
4 Floor 4                   0
5 Floor 5                   0
6 Roof Terrace              0
```

`facade_elements` was added to `spec/homespec.schema.json` (enum `fin|band|panel|awning`),
`build_scene.py` learned to build them, `finishes` was added — and the design carries
**one fin, on the ground storey**. Six storeys of the elevation are bare. The commit
message says "facade"; the model says otherwise. This is why the last gloop loop moved
the harness and not the picture.

Looking at the shipped artifacts before writing this brief:

- `deliverables/contractor-as-drawn/png/contractor-as-drawn_exterior_front.png` — the
  building occupies roughly **8% of the frame**; the neighbour massing blocks stand
  **in front of** the lower five storeys and hide them; every surface is the same
  grey-blue; there is no facade grain of any kind. It is a massing study.
- `deliverables/contractor-as-drawn/png/contractor-as-drawn_khach.png` — a **door leaf
  detached from its frame, clipping through the sofa**; furniture is untextured boxes;
  walls are blown to near-white with no bounce light, no skirting, no reveals, no
  ceiling read.

**The specific defect the user named — "front facing pillar missing" — is a vocabulary
gap, not a modelling oversight.** `facade_elements.kind` has no `column`. There is no
construct in the schema that can express the front pillar on `MẶT ĐỨNG CHÍNH`, so no
amount of authoring would have produced it. Fidelity-ledger items **(k)** facade
articulation, **(l)** undivided openings, **(m)** plain parapet railings and **(n)** no
finish information are all still open, and (k) is described in the ledger's own words as
*"the single biggest visual departure… the reason the 3D reads as massing rather than as
this building."*

Why now: the standing instruction for this pass is that **no past limitation applies**.
Three limits have quietly capped every prior attempt and all three are now lifted by
decision: CPU-only fast-EEVEE rendering, procedural-only assets, and the 8 MiB inline-GLB
viewer budget. None of them was ever a hard constraint — they were caution carried
forward.

## Current vs Desired State

- **Current state:**
  - **Materials:** `finishes` exists in schema and design, mapping element kinds to names
    (`plaster_painted`, `ceramic_tile`, `wood_board`, `aluminium`…), but resolves to flat
    Principled fills in `blender/materials.py`. **No textures, no UVs, no image maps.**
  - **Facade:** vocabulary is `fin|band|panel|awning`; **no `column`**. One fin authored
    in the entire building.
  - **Openings:** `{type, between, side, width_mm, sill_mm, head_mm, align, offset_mm}` —
    a single rectangular hole. **No subdivision field**, so no mullions, transoms or
    panelled door sets. The facade's grain and scale come almost entirely from this.
  - **Railings:** auto-generated solid 1100 mm parapet on open edges; the drawn pattern
    is absent.
  - **Furniture:** 12 procedural kinds, all `make_box` primitives (`geom.py`,
    `procedural_furniture.py`).
  - **Joinery:** `joinery.py::build_opening_furniture` produces the detached-leaf defect.
  - **Lighting:** one decorative sun at 55°/35°, a weak area fill, one area light per
    room sized `clamp(area_m2 * 2.2, 20, 90)`. No GI, no HDRI, no portals.
  - **Render profiles:** `preview` 32 spp / 960×540, `final` 256 spp EEVEE / 1920×1080,
    `cycles` 512 spp CPU — the `cycles` profile exists and is **not used** for the
    shipped set.
  - **Cameras:** `camera_fit.py` is pure and unit-tested; `exterior_front_camera` fits
    `facade_bbox`, which pulls the camera far enough back that the building is a sliver.
  - **Context:** `_add_neighbour_massing` builds freestanding blocks with an
    `or True` short-circuit at `src/homedesign/blender/build_scene.py:408`; the blocks
    occlude the facade.
  - **Viewer:** `INLINE_GLB_LIMIT_BYTES = 8 MiB`, base64url-inlined to dodge the Claude
    Artifacts entropy filter — a filter that **does not apply to the GitHub Pages
    delivery actually in use** (`docs/`). Flat vertex-colour AO look.
  - **Tests:** 226 green; camera math and 2D SVG/DXF text content covered. No render
    tests.
- **Desired state:** a set of interiors and a web viewer that a viewer mistakes for
  photographs of a built Saigon tube house — real bounce light, real PBR surfaces, real
  furniture, and a viewer carrying baked lighting instead of flat ambient — with the
  facade vocabulary extended so the drawn pillar, mullions and railing pattern can be
  expressed at all.
- **Key repo surfaces:**
  - `spec/homespec.schema.json` — `additionalProperties: false` throughout; the
    articulation additions land at `/properties/storeys/items/properties/facade_elements`
    and `…/openings`
  - `src/homedesign/model.py::model_hash` — **any schema addition invalidates every
    render sidecar**; do the migration once
  - `src/homedesign/blender/materials.py` — the palette to replace with a PBR resolver
  - `src/homedesign/blender/build_scene.py` — `_add_neighbour_massing` (:408 `or True`),
    `build_environment`, `add_interior_lights`, `_set_engine`, `render`, `add_cameras`
  - `src/homedesign/blender/joinery.py::build_opening_furniture` — detached-leaf defect
  - `src/homedesign/blender/{railings,furnish,procedural_furniture,geom,roof}.py`
  - `src/homedesign/camera_fit.py::exterior_front_camera` — framing defect
  - `src/homedesign/render_profiles.py` — `cycles` profile to promote to the hero path
  - `src/homedesign/viewer.py` — `INLINE_GLB_LIMIT_BYTES`, `optimize_glb`, `write_viewer`,
    `write_floor_viewer`; templates in `src/homedesign/assets/`
  - `src/homedesign/orchestrator.py::_CANDIDATES` — **Blender 4.1 legacy-EEVEE pin stays**
    (guarded by `test_blender_candidates_prefer_legacy_eevee_build`); Cycles is orthogonal
    to that pin
  - `src/homedesign/publish.py::verify_fresh` — blocks publish on stale hashes
  - `designs/contractor-as-drawn.{json,measurements.md,fidelity.md}` — fidelity items
    (k)(l)(m)(n)
  - `contractor/` + `output/contractor_pdf_png/` — `MẶT ĐỨNG CHÍNH` is the source for the
    pillar, mullions and railing pattern
  - Blender MCP: `search_polyhaven_assets`, `download_polyhaven_asset`,
    `search_sketchfab_models`, `download_sketchfab_model`, `set_texture`

## Resolved Decisions

- **DEC-001:** The bar is **photo-match against real Saigon tube-house photography**, not
  mm-accuracy against the elevation — the previous pass's bar produced an accurate image
  nobody found convincing. Drawing accuracy remains a hard *constraint*: every realism
  gain must be traceable to the sheets, never invented.
- **DEC-002:** Effort concentrates on **interior stills and the GLB web viewer**.
  Exterior hero stills are explicitly *not* the priority surface this pass — but the
  missing front pillar and the 8%-of-frame camera are corrected anyway, as accuracy and
  correctness defects rather than as investment.
- **DEC-003:** **Cycles CPU is unlocked for hero output**, accepting long bakes. This is
  the single largest cause of the "blown-out white box" interior: EEVEE without GI gives
  no bounce, so plaster reads as paper. EEVEE stays the fast iteration loop. The Blender
  4.1 pin is untouched — Cycles does not depend on EEVEE Next, and EEVEE Next is known
  to render red on this GPU.
- **DEC-004:** **PolyHaven HDRIs and PBR texture sets are pulled in** via the Blender MCP
  and cached in-repo so builds stay reproducible offline. `finishes` names already in the
  design (`plaster_painted`, `ceramic_tile`, `wood_board`, `aluminium`, `concrete_formed`,
  `glass_clear`) become the resolver keys — the mapping layer already exists, only the
  resolution target changes.
- **DEC-005:** **Furniture becomes curated real meshes** (Sketchfab/PolyHaven), cached
  under a licensed assets directory, placed from the same spec coordinates the box
  primitives use today. No procedural box will photo-match; interiors are priority #1 and
  the boxes are their most damning defect.
- **DEC-006:** **The 8 MiB inline-GLB cap is lifted.** The viewer serves an external
  `.glb` from `docs/` with KTX2-compressed PBR textures, a baked Cycles lightmap and an
  HDRI environment, so the viewer shows the same lighting as the stills. A reduced inline
  build is retained as an offline/Zalo fallback. The cap only ever existed to dodge the
  Claude Artifacts entropy filter, which does not apply to the GitHub Pages delivery in
  use.
- **DEC-007:** **The full articulation vocabulary is added to the schema in one
  migration:** `column` added to `facade_elements.kind` (this is the user's missing front
  pillar); `divisions` added to openings for mullions/transoms/panelled sets (item l);
  `railing.pattern` (item m); plus reveal, skirting and cornice depth. Done as a single
  change because every schema addition invalidates every `model_hash` sidecar.
- **DEC-008:** **Facade content is authored off `MẶT ĐỨNG CHÍNH`** for all seven storeys,
  not just Ground. The plumbing is not the deliverable; the populated model is.
- **DEC-009:** **Neighbour massing is dropped from hero stills**, kept in the codebase
  behind a render-time toggle defaulting off, rather than deleted. Recorded concern: a
  tube house is by definition wall-to-wall, and isolated-object renders forfeit the street
  context that makes it read as a real VN house. The user's call stands; the toggle
  preserves the option. The `or True` short-circuit at `build_scene.py:408` is removed as
  part of this.
- **DEC-010:** **The exterior framing defect is fixed independently of DEC-009** —
  `exterior_front_camera` fits the building bbox so the facade fills the frame, rather
  than a bbox wide enough to reduce it to 8%.
- **DEC-011:** **No new render-quality tests.** Judging is the gloop blind-critic loop,
  logged to `reports/`. Recorded risk: nothing then prevents a later change from silently
  undoing the result, and this departs from the repo's own 2026-08-21 codify-each-PASS
  pattern. Boundary applied: the existing 226 tests must stay green, and *geometry*
  correctness fixes (the door-leaf-through-sofa interpenetration) still get a test,
  because that is a geometry bug rather than an aesthetic judgement.
- **DEC-012:** **Render budget is an overnight full-set bake, ~6–10 h unattended**, all
  12 views on Cycles CPU at quality samples with denoising, so the set is visually
  consistent. Each gloop round iterates on 2–3 hero frames at preview quality to keep the
  loop fast; only the accepted configuration gets the long bake.

## Assumptions & Constraints

- **ASM-001:** The gloop loop runs against a provisional written rubric until the user's
  reference photos land (see Q-001), then re-judges against the photoset. Build phases do
  not block on the photos; only the final gate does.
- **ASM-002:** `finishes.by_element` / `by_room_type` names are treated as the stable
  public keys of the new PBR resolver, so populated designs do not need re-authoring.
- **ASM-003:** DEC-011's "no new tests" covers render aesthetics only; schema-migration
  and geometry-correctness tests are still written, because the schema is a closed
  contract with `additionalProperties: false` and a malformed addition breaks validation
  for every design.
- **CON-001:** Blender 4.1 legacy-EEVEE candidate pin in `orchestrator.py::_CANDIDATES`
  must not be touched — guarded by an existing test. EEVEE Next renders red on this
  machine's UHD 620.
- **CON-002:** No GPU render path exists; Cycles reports zero GPU devices. All bakes are
  CPU. This is what makes DEC-012's overnight budget necessary rather than optional.
- **CON-003:** Every realism addition must be traceable to the contractor sheets
  (`contractor/`, `output/contractor_pdf_png/`). Invented articulation defeats the entire
  value of a render downstream of a validated model.
- **CON-004:** Any schema change invalidates every render sidecar via `model_hash`, and
  `publish.py::verify_fresh` will block publishing until the full set is rebuilt.
- **CON-005:** Downloaded assets carry licences; they must be cached with attribution and
  the repo must still build offline from the cache.

## Approaches Considered

- **Chosen:** Extend the geometry vocabulary, populate it from the sheets, replace the
  flat palette with PBR + HDRI, swap box furniture for curated meshes, promote Cycles CPU
  to the hero path, and lift the viewer budget to carry baked lighting — judged by a gloop
  blind critic against photographic references. Every one of the four open fidelity items
  (k)(l)(m)(n) closes, and the result generalises to future designs.
- **ALT-001:** *Hand-tune this one scene as a one-off.* Fastest route to one impressive
  image; rejected because the next design starts from massing again and nothing is
  reusable — this is exactly how the pipeline arrived here.
- **ALT-002:** *Stay on EEVEE and buy realism with lighting craft* (irradiance volumes,
  portals, exposure). Cheap and fast; rejected because it caps out short of photoreal and
  re-imposes the limitation the user explicitly lifted.
- **ALT-003:** *Golden-image perceptual diff testing.* Catches every regression exactly;
  rejected under DEC-011 — any lighting tweak reddens the whole suite and committed PNGs
  bloat the repo.
- **ALT-004:** *Cloud/remote GPU rendering.* Would cut the overnight bake to minutes;
  rejected for now because it adds credentials, cost, and a moving part the pipeline
  cannot test. Revisit if the 6–10 h budget proves unworkable.

## Out of Scope

- Exterior hero-still art direction beyond fixing the pillar, the framing defect and the
  context toggle (DEC-002).
- A3 print plate redesign — the plates re-render from whatever the new pipeline produces,
  but their layout is untouched.
- Any change to `orchestrator.py::_CANDIDATES` or the Blender 4.1 pin (CON-001).
- The 2D SVG/DXF drawing set — it is already at parity and this pass does not touch it.
- Re-measuring the building. `designs/contractor-as-drawn.measurements.md` rev.3 is the
  input, not a subject.
- Cloud rendering (ALT-004).

## Open Questions

1. **Q-001:** Which reference photographs should the render be judged against? You chose
   to supply them rather than have me source a set.
   - **Recommended default:** Drop 8–12 images into `research/sources/reference-photos/`
     — a mix of Saigon tube-house interiors (living, kitchen/dining, bedroom) and one or
     two alley-facade shots. Until they land, the loop runs on a provisional written
     rubric (ASM-001) and re-judges once they exist.
   - **Why this matters:** This is the entire pass/fail gate. Without it the critic is
     judging on taste alone, which is the failure mode gloop exists to prevent — and the
     first build phases can proceed regardless, so it blocks the finish line, not the
     start.
2. **Q-002:** Is there a licence constraint on downloaded furniture assets (CC0 only, or
   is CC-BY with attribution acceptable)?
   - **Recommended default:** CC0 only, so the repo carries no attribution obligation and
     the deliverables can be shared with the construction team without conditions.
   - **Why this matters:** CC0-only meaningfully narrows the available furniture and may
     force a procedural fallback for some kinds; it is cheaper to know before curating.

## Suggested Next Step

Run `/plan photoreal-render-overhaul` to turn this into a multi-phase implementation plan.
