---
title: "Tubehouse Dream Home — 2D Plans + 3D Renders to Architect-Brief PDF"
date: "2026-07-06"
type: "brainstorm"
depth: "deep"
source_request: "tubehouse dream home: goal is 2D floor plans then 3D renders compiled into a PDF"
slug: "tubehouse-dream-home"
---

# Brainstorm: Tubehouse Dream Home — 2D Plans + 3D Renders to Architect-Brief PDF

## Problem & Why Now
<!-- seeds /plan ## Objective -->
The user wants their dream home — a 5-storey mixed-use Vietnamese urban tube house on a
4m × 25m sandwiched lot — turned into a professional design-intent document: dimensioned
2D floor plans per storey, a persuasive gallery of 3D Cycles renders, and a written
requirements narrative, all compiled into a single A3-landscape PDF to hand a real
architect. The repo's `/homedesign` pipeline already produces the raw ingredients
(per-floor SVG/DXF plans, Blender renders) and a tube house is its flagship example, but
two capabilities are missing: a mid-tube open-to-sky light well (the defining
architectural feature of a deep sandwiched tube house) and any PDF compilation at all.

## Current vs Desired State
<!-- seeds /plan ## Context Snapshot -->
- **Current state:** `src/homedesign/` compiles a JSON spec (`spec/homespec.schema.json`)
  into per-storey SVG+DXF plans (`plan2d.py`) and a Blender Cycles scene with exactly two
  renders — one exterior, one auto-picked interior (`blender/build_scene.py`). Geometry is
  strictly rectilinear; only the plot perimeter counts as "exterior" for windows; roofs
  cover the whole top storey; style enum is `modern-minimal` only. A 4×12m 3-storey
  example exists (`spec/examples/tubehouse-mini.json`). No PDF code exists (deliberately
  dropped in the 2026-07-04 rebuild).
- **Desired state:** a spec for the real 4×25m, 5-storey house compiles cleanly with a
  full-height light well and elevator shaft; the renderer produces a full gallery (8+
  views); a new PDF builder assembles cover, narrative, room schedule, per-floor A3 plan
  pages, render gallery, requirements notes, and a machine-readable-files appendix into
  `output/pdf/<name>.pdf` via HTML printed by headless Edge.
- **Key repo surfaces:** `spec/homespec.schema.json`, `src/homedesign/compiler.py`,
  `validate.py`, `plan2d.py`, `orchestrator.py`, `blender/build_scene.py` (+ `roof.py`,
  `geom.py`), `.claude/skills/homedesign/SKILL.md`, `src/homedesign/__main__.py`,
  `spec/examples/tubehouse-mini.json`; prior context in
  `research/2026-07-04_idea-floorplan-3d-home-tool-brainstorm.md` and
  `plans/2026-07-04-idea-floorplan-3d-home-tool-plan.md`.

## Resolved Decisions
<!-- the grilled Q&A; each one keeps /plan's Grill Me empty -->

### The house
- **DEC-001:** "Tubehouse" = long narrow **rectilinear** box, not a cylinder — matches the
  pipeline's native geometry; curved geometry rejected as a core rebuild.
- **DEC-002:** The PDF is an **architect brief** — design intent with dimensioned plans,
  renders, room schedule, and written requirements; the architect redoes technical drawings.
- **DEC-003:** Footprint **4m × 25m** — the repo's original bespoke tube-house proportions.
- **DEC-004:** **5 storeys, mixed-use**: ground = lease + car park, floor 1 = lease,
  floors 2–4 = family. Total ~17.6m tall.
- **DEC-005:** Family program = **3 bedrooms + 3 baths** across floors 2–4.
- **DEC-006:** Lot is **sandwiched** (party walls on both sides and rear; street facade
  only). Ground floor: garage at the front, entry hall + vertical core mid-tube, rear
  lease space (storage/workshop) accessed internally; floor 1 = full lease unit.
- **DEC-007:** **Mid-tube open-to-sky light well** is the daylight strategy — the defining
  feature; worth extending the pipeline rather than only noting it in the brief.
- **DEC-008:** Vertical core = **stair beside the light well** at mid-depth **plus a
  family-size elevator shaft** stacked on every floor (~1.2m × 1.5m).
- **DEC-009:** Floor heights: **ground 4.0m, upper floors 3.4m** — tall commercial ground.
- **DEC-010:** Floor 4 = **partial rooftop terrace**: front ~40% open terrace, flat roof
  over the enclosed rear portion.
- **DEC-011:** Facade: **full-width balconies on floors 2–3 + floor-to-ceiling glazing**,
  terrace parapet on 4 (balcony is a supported room type).
- **DEC-012:** Style **modern-minimal** — the only style the material system implements;
  zero extra work.
- **DEC-013:** Floor 2 (family common): **living at the front** (opens to balcony),
  **kitchen + dining behind the light well**, WC at the core.
- **DEC-014:** Floor 3 = **master suite + one kid's room** (+ baths). Floor 4 = **office
  on the light well + guest bedroom with bath at the rear + front roof terrace** —
  preserves the 3BR total.
- **DEC-015:** Floor 1 lease unit = open-plan studio/office wrapping the core + WC
  (resolved from typology; nothing hinges on it).
- **DEC-016:** Light well default sizing: **~2.0m × 2.0m void adjacent to the stair core
  at mid-depth (~12m from the street), full height from ground to sky**, with circulation
  passing beside it. Architect refines exact proportions.
- **DEC-017:** Site context: **Vietnam, urban** — brief includes hot-humid climate notes,
  cross-ventilation via the light well, and typical VN tube-house code context.
- **DEC-018:** **No budget stated** in the brief; cost discussion deferred to the first
  architect meeting.

### The deliverable & pipeline
- **DEC-019:** PDF contents = **the full set**: cover with hero render → design-intent
  narrative → room schedule table (areas per floor) → one floor-plan page per storey →
  render gallery → requirements/notes for the architect (elevator, light well, structure,
  services) → appendix page listing machine-readable handover files (per-floor DXF, spec
  JSON).
- **DEC-020:** Page format **A3 landscape** — 25m-deep plans stay legible near 1:100;
  renders get full-bleed pages.
- **DEC-021:** Render set = **full gallery (8+ final-quality views)**: exterior street +
  aerial, light-well shot, and interiors of every major room — requires extending the
  two-camera system in `build_scene.py`.
- **DEC-022:** PDF generation via **HTML → headless Edge/Chrome print-to-PDF** — embeds
  the SVG plans as crisp vectors, no native Python deps (cairo etc.) on Windows, easy to
  restyle. reportlab rejected as verbose with lossy SVG handling.

## Assumptions & Constraints
<!-- seeds /plan ## Assumptions and Constraints -->
- **ASM-001:** Lease spaces are modeled with the existing `office` room type — the schema
  enum has no retail/shop type; the brief text explains actual use.
- **ASM-002:** The elevator is modeled as a small stacked shaft room (storage-type or a
  new `elevator` enum value) with the real lift specified in the brief text, not geometry.
- **ASM-003:** Party walls (sides + rear) carry no openings; windows exist only on the
  street facade and onto the light well.
- **ASM-004:** One car + motorbikes/bicycles fit the front garage (~4m × 6m).
- **CON-001:** Geometry core is rectilinear, axis-aligned only (repo DEC-006/CON-002 from
  the 2026-07-04 brainstorm still stand).
- **CON-002:** The compiler currently treats only the plot perimeter as exterior — light
  well support must make void-facing walls window-eligible and cut the roof over the void.
- **CON-003:** Validator requires door-chain reachability from an exterior door and
  ≥900mm stair runs; the 4m width minus light well and core makes corridor widths tight —
  layouts must respect `room_too_small` (<600mm) and stair rules.
- **CON-004:** Renderer today emits exactly 2 cameras; final quality is 512 samples at
  1920×1080 — 8+ finals will take meaningful render time on this machine.
- **CON-005:** Windows host; Blender located via hardcoded candidates or `BLENDER_CMD`;
  PDF printing relies on locally installed Edge/Chrome headless.

## Approaches Considered
<!-- seeds /plan ## Risks and Alternatives -->
- **Chosen:** Extend the existing `/homedesign` pipeline minimally — add light-well/void
  support (schema + compiler + plan2d + Blender roof/walls), an elevator-shaft
  representation, a configurable camera gallery, and a new net-new `pdf.py` stage
  (HTML template → headless Edge) — then author the 5-storey spec and run `build --final`.
- **ALT-001:** True curved/cylindrical tube geometry — rejected: replaces the rect/box
  geometry core; a large engineering project that delays the actual goal.
- **ALT-002:** Skip the light well, note daylight in the brief only — rejected: the light
  well defines the house; plans and renders without it misrepresent the design.
- **ALT-003:** Front/rear setbacks for daylight — rejected: the lot is sandwiched with a
  party wall at the rear; no second facade is available.
- **ALT-004:** reportlab (pure-Python PDF) — rejected: verbose layout code, lossy SVG
  path; HTML→Edge keeps plans vector-crisp with zero native dependencies.

## Out of Scope
- Curved/cylindrical geometry of any kind.
- Construction/permit-grade drawings (dimension chains, sections, structural sizing) —
  the architect produces these.
- Cost estimation or budget statements.
- IFC export (remains parked per the 2026-07-04 plan).
- New render styles beyond `modern-minimal`; material aspirations go in the brief text.

## Open Questions
<!-- the few that survived; seed /plan ## Grill Me. Use `None.` when fully resolved. -->
1. **Q-001:** What is the plot's real orientation and address (which way does the street
   facade face)?
   - **Recommended default:** Model with the facade as "front" generically; note in the
     brief that sun-shading of the glazed facade depends on orientation, to be confirmed.
   - **Why this matters:** Facade shading, light-well sun angles, and climate notes in
     the brief change with orientation.
2. **Q-002:** Do lease tenants need access separation from the family (separate lobby,
   lockable stair door, elevator floor lockout)?
   - **Recommended default:** Shared stair/elevator core with a lockable family lobby at
     floor 2, stated as a requirement in the brief.
   - **Why this matters:** Affects ground-floor hall layout and a line in the
     requirements page, not the modeled geometry.

## Suggested Next Step
Run `/plan tubehouse-dream-home` to turn this into a multi-phase implementation plan
(expected phases: light-well + elevator pipeline support → camera gallery → 5-storey spec
authoring + validation → final renders → HTML→PDF builder → assemble the brief).
