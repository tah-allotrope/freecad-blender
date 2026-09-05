---
name: homedesign
description: Turn a natural-language home idea into validated 2D floor plans, elevations and sections (SVG/DXF), and furnished 3D renders (EEVEE preview, EEVEE final, or Cycles), plus an interactive GLB web viewer and an A3 architect brief. Use when the user says "/homedesign", asks to design/generate a house or floorplan, or asks to edit a home design already produced by this skill (e.g. "make the kitchen bigger").
---

# /homedesign

Turns a plain-language home idea into 2D floor plans, elevations and sections
(SVG + DXF) and furnished 3D renders, via a compact high-level spec and a
deterministic Python compiler (`src/homedesign/`). No FreeCAD is involved
anywhere in this flow.

## Spec format

Read `spec/homespec.schema.json` for the authoritative schema. Read
`spec/examples/demo-3br-2storey.json` and `spec/examples/tubehouse-mini.json`
as worked examples before writing a new spec — they show the corridor
pattern that keeps room adjacency (and therefore door/window placement)
correct.

Cheat sheet:
- `meta.name` — used as the output file stem everywhere.
- `site.plot_width_mm` / `plot_depth_mm` — the buildable footprint.
- `site.wall_alignment` (optional, `centre|inside`, default `centre`) — how
  exterior walls sit relative to the room edge. `inside` moves their outer
  face onto the plot line (the honest built width), which is what
  `designs/tubehouse-dream.json` uses. The room schedule always reports the
  gross area regardless.
- `site.context` (optional) — `{neighbours: bool, street_depth_mm: number}`.
  When absent, neighbouring party-wall massing is built only when
  `plot_width_mm <= 6000` (the sandwiched-urban-lot case); the front camera
  shoots from the street side, which never gets a neighbour block.
- `site.north_deg` (optional, `0..360`, default `0`) — the compass bearing of
  north, clockwise from model `-y` toward `+x`. It rotates the sun rig in
  renders and the north arrow on plans, so shadows and orientation reflect a
  real bearing instead of the model default.
- `storeys[]` — each has `level` (0-based), `height_mm`, `rooms[]`,
  `openings[]`, optional `stairs` (`{room, direction, mode?}`), optional `roof`
  (`{type: flat|gable|shed, pitch_deg, overhang_mm, rect?, voids?,
  structures?}` — only put a roof on the top storey), and optional `voids`
  (array of `{x,y,w,d, reason?}`) declaring a beam-spanned opening in that
  storey's floor slab. `rect` overrides the roof's default full-plot span (use
  it for a partial roof, e.g. a rooftop terrace left open); roof `voids`
  (array of `{x,y,w,d}`, `type: flat` only) punches open-to-sky holes in the
  roof; `structures` (array of `{x,y,w,d,height_mm,name?}`) places a box on
  top of the roof slab (e.g. a lift plant room).
- **Declare floor voids, don't leave footprints untiled.** A light well, a
  double-height mezzanine opening, or any open shaft is authored as a
  `storeys[].voids[]` rectangle on each storey it passes through — this models
  the open floor slabs, lets `check_room_support` treat the span as
  beam-supported instead of unsupported, and hatches it on the plan. Leaving a
  footprint merely untiled forfeits the wall/floor/section geometry around the
  shaft.
- `meta.views` (optional) — a named camera gallery: each entry is
  `{name, kind: exterior_front|exterior_aerial|exterior_street|room, room_id?}` (`room_id`
  required when `kind: room`; `exterior_street` is the 3/4 street-corner hero).
  Renders land at `output/png/<slug>_<view name>.png`. Omit `views` entirely to get the old
  2-shot default (one exterior + one auto-picked interior).
- `rooms[]` — each room is either an absolute `rect: {x,y,w,d}` (mm, origin
  at the plot's front-left corner) or a `relative: {adjacent_to, side, w, d}`
  placement solved against an already-placed room. Room `type` includes
  `elevator` for a lift shaft (no furniture is placed in it), plus the newer
  `terrace` (open roof terrace, like `balcony` but with a `floor_default`
  finish), `wc` (water closet — a `bathroom` without the shower), `utility`
  and `courtyard` (open to the sky). The optional
  `name` string is the human-readable label: it now appears on the plan SVGs,
  the section room labels, the DXF TEXT entities and the PDF room schedule
  (falling back to the room `id` when absent).
- `stairs` — `{room, direction, mode?}` where `mode` is one of
  `auto|straight|u_return|none` (default `auto`). The generator sizes treads
  from the storey height (Blondel relation: `600 <= 2R + G <= 640`, going
  `>= 250` mm, riser `<= 190` mm) and selects straight vs U-return from the
  shaft's aspect ratio. **An undersized shaft is now a hard compile error**
  (`stair_shaft_too_small`) that names the required size, e.g.
  `a straight flight needs 900x4500mm and a U-return needs 1900x3150mm at a
  3400mm storey height`. A `stairwell` shaft must therefore be at least
  `1900 x 2900` mm for a U-return (two 900 mm flights + 100 mm well) unless
  `mode: none` is set deliberately. Stair and elevator shafts are punched
  out of the floor slab above automatically (floor voids).
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
   `designs/<slug>.json` from scratch following the schema and the
   corridor pattern above. For an edit request ("make the kitchen bigger",
   "add a bedroom"), load the existing `designs/<slug>.json` and make
   the smallest JSON edit that satisfies the request — do not regenerate the
   whole spec. This keeps edits diffable and round-trippable.
2. **Build.** Run:
   ```
   homedesign build designs/<slug>.json
   ```
   This validates the spec (schema + geometric sanity), compiles it,
   generates SVG/DXF plans plus four elevations and two sections, and drives
   a headless Blender build + EEVEE preview render (960x540, ~seconds per
   view — previews check layout, not lighting; the engines differ on glass
   and window openings, so never chase EEVEE artifacts). It prints every
   artifact path, ending with `blender build: <N>s`.

   Plans carry furniture footprints, numbered stair treads, the storey's
   finished-floor level and any declared section cut lines. Furniture comes
   from the same `placement.plan_room` rules the Blender furnisher uses, so
   the plan and the 3D scene cannot disagree about what is in a room.

   The four elevations are true orthographic projections of the whole
   building — every wall, opening, balcony parapet, stair tread and roof is
   projected and painter-sorted front-to-back — not just the walls touching
   the plot boundary, so a set-back facade still reads correctly.
2b. **Re-render without rebuilding.** Once a `.blend` exists, iterate on
   views without redoing geometry:
   ```
   homedesign render designs/<slug>.json \
       --view exterior --view interior [--profile final] [--skip-existing]
   ```
   `render` reuses the saved `.blend` (`--reuse-blend` is implicit). Add
   `--skip-existing` to skip views whose PNG already exists.
2c. **Render profiles.** Three are available everywhere `--profile` is
   accepted: `preview` (EEVEE, 32 samples, 960x540 — the default), `final`
   (EEVEE + AgX, 256 samples, 1920x1080 — ~12 min for a 9-view gallery, not
   the ~11 h Cycles used to cost), and `cycles` (512 samples — an explicit
   opt-in hero-shot path, ~3 min/view on CPU). The engine line is always
   printed (`eevee raytracing: on|unavailable` or `cycles device: ...`) so a
   run is never ambiguous about which path produced it.

   **Renders must come from Blender 4.1's legacy EEVEE.**
   `orchestrator._CANDIDATES` selects 4.1 ahead of 4.5 for this reason, so the
   default is already correct — do not "upgrade" it. EEVEE **Next** (Blender
   4.2+) miscompiles on this project's target iGPU and renders every lit
   surface blood red: a white `0.92/0.91/0.88` wall comes out `(194, 34, 53)`,
   independent of view transform and of `raytracing`, while the world
   background stays correct. Under 4.1 the `final` profile's
   `raytracing: True` degrades to a harmless no-op. If a gallery comes out
   red or otherwise miscoloured, **check which Blender ran before you suspect
   the design** — re-render one view with `--profile cycles` to confirm the
   scene data is fine. Full diagnosis: the 2026-08-08 entry in
   `activeContext.md` and `docs/lessons-learned.md`.
2d. **Interactive model.** Add `--gltf` to `build` to also export a GLB and
   write a self-contained offline web viewer:
   ```
   homedesign build designs/<slug>.json --gltf
   # writes output/gltf/<slug>.glb and output/viewer/<slug>.html
   ```
   The viewer HTML embeds three.js and the GLB (no network requests); open it
   directly in a browser to orbit the model.
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
   `--profile final` gives a full-quality render (EEVEE, 256 samples, 1080p)
   in minutes if the user wants a polished still instead of the fast preview.
6. **Conversational edits.** When the user asks for a change, go back to
   step 1 against the *same* spec file and re-run step 2 onward. Summarize
   what changed in the spec (e.g. "widened the kitchen from 4.0m to 4.6m and
   shrank the office by the same amount") rather than re-describing the
   whole house.

## Architect-brief PDF

Once a spec has a final render gallery (`meta.views`, built with
`--profile final`), assemble an A3-landscape architect brief:
```
homedesign pdf designs/<slug>.json
```
This compiles the spec, regenerates SVG/DXF plans + elevations/sections if
missing, reads a brief copy file at `spec/briefs/<slug>.json` (`{title,
subtitle, narrative: [...], requirements: [...]}` — write one per house, no
budget content), and prints `output/pdf/<slug>-brief.html` to
`output/pdf/<slug>-brief.pdf` via a headless Chromium browser (Edge or Chrome,
auto-detected; override with `PDF_BROWSER_CMD`). The PDF has one page each for
cover (hero render), design narrative, room schedule (per-room area + floor
totals), one plan page per storey, four elevation pages and two section pages
(all inline vector SVG), a render gallery (2 images/page), requirements, and a
handover appendix listing the DXF files and source spec. Pass `--hero <view
name>` to pick the cover image and `--brief <path>` for a different copy file.

Every render carries a sidecar naming the model that produced it; `pdf` warns
(`stale render: <view>`) and stamps `STALE` in the caption when a gallery image
predates the model. Pass `--require-fresh` to make a stale image a hard error
instead — always use it before handing a brief to anyone.

**Scaffold the brief copy** with `homedesign brief --init designs/<slug>.json`
(writes `spec/briefs/<slug>.json` with title/subtitle derived from the model
plus placeholder narrative/requirements; add `--force` to overwrite). **Every
subcommand accepts `--out <dir>`** to target a different output directory than
`output/`. **Publish** a hash-verified deliverable with
`homedesign publish designs/<slug>.json` — it compiles, verifies every render's
sidecar matches the current model hash, and copies `png/`, `gltf/`, `viewer/`
and `pdf/` into `deliverables/<slug>/` (fails on any stale file; `--force`
overrides).

## Known limitations (by design, not bugs)

- Rectilinear geometry only: axis-aligned walls, flat/gable/shed roofs, no
  curved or diagonal walls, no split levels.
- Roof `voids` (open-to-sky holes) are only implemented for `type: flat`;
  requesting voids on a `gable`/`shed` roof raises `NotImplementedError` at
  Blender-build time.
- Furniture is procedural (parametric boxes), not photoreal asset models —
  there is no bundled CC0 asset library yet. Renders read as furnished but
  stylized, not catalog-photo realistic.
- Previews are fast EEVEE renders; `--profile final` upgrades the gallery to
  256-sample EEVEE with AgX colour, and `--profile cycles` remains as an
  explicit (much slower) opt-in path. There is no raytraced GI or reflection
  path on this hardware: EEVEE Next is unusable (see the engine note under
  "Render profiles") and Cycles has no GPU device, so `cycles` runs on CPU.
