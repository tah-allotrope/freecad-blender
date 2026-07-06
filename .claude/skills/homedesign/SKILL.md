---
name: homedesign
description: Turn a natural-language home idea into validated 2D floor plans and furnished 3D Cycles renders, and apply conversational edits to an existing design. Use when the user says "/homedesign", asks to design/generate a house or floorplan, or asks to edit a home design already produced by this skill (e.g. "make the kitchen bigger").
---

# /homedesign

Turns a plain-language home idea into 2D floor plans (SVG + DXF) and furnished
3D Cycles renders, via a compact high-level spec and a deterministic Python
compiler (`src/homedesign/`). No FreeCAD is involved anywhere in this flow.

## Spec format

Read `spec/homespec.schema.json` for the authoritative schema. Read
`spec/examples/demo-3br-2storey.json` and `spec/examples/tubehouse-mini.json`
as worked examples before writing a new spec — they show the corridor
pattern that keeps room adjacency (and therefore door/window placement)
correct.

Cheat sheet:
- `meta.name` — used as the output file stem everywhere.
- `site.plot_width_mm` / `plot_depth_mm` — the buildable footprint.
- `storeys[]` — each has `level` (0-based), `height_mm`, `rooms[]`,
  `openings[]`, optional `stairs` (`{room, direction}`), optional `roof`
  (`{type: flat|gable|shed, pitch_deg, overhang_mm, rect?, voids?}` — only put
  a roof on the top storey). `rect` overrides the default full-plot span (use
  it for a partial roof, e.g. a rooftop terrace left open); `voids` (array of
  `{x,y,w,d}`, `type: flat` only) punches open-to-sky holes in the roof —
  the standard way to keep a mid-plan light well open at every level, since
  rooms simply aren't tiled over that footprint on any storey.
- `meta.views` (optional) — a named camera gallery: each entry is
  `{name, kind: exterior_front|exterior_aerial|room, room_id?}` (`room_id`
  required when `kind: room`). Renders land at
  `output/png/<slug>_<view name>.png`. Omit `views` entirely to get the old
  2-shot default (one exterior + one auto-picked interior).
- `rooms[]` — each room is either an absolute `rect: {x,y,w,d}` (mm, origin
  at the plot's front-left corner) or a `relative: {adjacent_to, side, w, d}`
  placement solved against an already-placed room. Room `type` includes
  `elevator` for a lift shaft (no furniture is placed in it).
- `openings[]` — `{type: door|window, between: [room_id, room_id_or_"exterior"], width_mm, sill_mm, head_mm, side?}`.
  A door/window can only be placed where two rooms (or a room and
  `"exterior"`) actually share a wall — the compiler derives walls from room
  geometry, so **every room must be reachable via a chain of doors from an
  exterior door**, or the design will look right but not compile as a livable
  home. `side` (`north|south|east|west`; north=min-y, south=max-y, west=min-x,
  east=max-x) disambiguates which exterior face gets the opening when a room
  borders more than one exterior wall (e.g. the street facade on one side and
  a light well on the other) — omit it only when the room has just one
  exterior wall. `opening_no_wall` is raised if the requested side isn't
  actually an exterior wall of that room (e.g. it's shared with another room).
- **Design rule that avoids the #1 mistake**: lay each storey out as stacked
  rows tiling the full plot, with a full-width corridor row (a `hall` room
  spanning the whole plot width) between any row of more than ~2 rooms and
  the row below it. This guarantees every room on both sides of the corridor
  shares a full wall with it, so a door always exists. See the demo spec.

## Workflow

1. **Author or patch the spec.** For a new idea, write
   `output/specs/<slug>.json` from scratch following the schema and the
   corridor pattern above. For an edit request ("make the kitchen bigger",
   "add a bedroom"), load the existing `output/specs/<slug>.json` and make
   the smallest JSON edit that satisfies the request — do not regenerate the
   whole spec. This keeps edits diffable and round-trippable.
2. **Build.** Run:
   ```
   PYTHONPATH=src python -m homedesign build output/specs/<slug>.json
   ```
   This validates the spec (schema + geometric sanity), compiles it,
   generates SVG/DXF plans, and drives a headless Blender build + preview
   render. It prints every artifact path, ending with `blender build: <N>s`.
3. **If the command exits nonzero**, its stderr is a list of
   `[code] path: message` errors (schema errors, room overlap, opening on a
   nonexistent wall, opening too wide for its wall, stairwell too narrow,
   missing stair continuity, etc.). Fix the spec directly from these
   messages — they are precise and machine-generated — and re-run. Do not
   guess at unrelated fixes.
4. **Self-correct visually, bounded to 3 passes.** Once the build succeeds,
   Read the `output/png/<slug>_exterior.png` and `_interior.png` renders and
   the `output/svg/<slug>_f*.svg` plans. Look for: rooms that don't read as
   the requested type, obviously wrong proportions, a roof that doesn't span
   the building, missing furniture in furnished rooms, or a completely dark
   interior render (means the room got no light — should not happen, but if
   it does, check the room actually compiled rather than re-running blindly).
   If something is visibly wrong, patch the spec and rebuild. Stop after 3
   build attempts either way and present the current best result — don't
   loop indefinitely.
5. **Present.** Show the renders and plans, and summarize the design in a
   sentence or two (room count, layout, notable features). Mention that
   `--final` gives a full-quality render (512 samples, 1080p) if the user
   wants a polished still instead of the fast preview.
6. **Conversational edits.** When the user asks for a change, go back to
   step 1 against the *same* spec file and re-run step 2 onward. Summarize
   what changed in the spec (e.g. "widened the kitchen from 4.0m to 4.6m and
   shrank the office by the same amount") rather than re-describing the
   whole house.

## Architect-brief PDF

Once a spec has a final render gallery (`meta.views`, built with `--final`),
assemble an A3-landscape architect brief:
```
PYTHONPATH=src python -m homedesign pdf output/specs/<slug>.json
```
This compiles the spec, regenerates SVG/DXF plans if missing, reads a brief
copy file at `spec/briefs/<slug>.json` (`{title, subtitle, narrative: [...],
requirements: [...]}` — write one per house, no budget content), and prints
`output/pdf/<slug>-brief.html` to `output/pdf/<slug>-brief.pdf` via a headless
Chromium browser (Edge or Chrome, auto-detected; override with
`PDF_BROWSER_CMD`). The PDF has one page each for cover (hero render), design
narrative, room schedule (per-room area + floor totals), one plan page per
storey (inline vector SVG), a render gallery (2 images/page), requirements,
and a handover appendix listing the DXF files and source spec. Pass
`--hero <view name>` to pick the cover image (default: first `meta.views`
entry) and `--brief <path>` to use a brief copy file at a different path.

## Known limitations (by design, not bugs)

- Rectilinear geometry only: axis-aligned walls, flat/gable/shed roofs, no
  curved or diagonal walls, no split levels.
- Roof `voids` (open-to-sky holes) are only implemented for `type: flat`;
  requesting voids on a `gable`/`shed` roof raises `NotImplementedError` at
  Blender-build time.
- Furniture is procedural (parametric boxes), not photoreal asset models —
  there is no bundled CC0 asset library yet. Renders read as furnished but
  stylized, not catalog-photo realistic.
- IFC/BIM export is not wired to this pipeline (`src/ifc_export_utils.py`
  targets the retired low-level spec format and is not part of this flow).
- Preview renders are low-sample Cycles for speed; always available via
  `--final` for a slower, cleaner still.
