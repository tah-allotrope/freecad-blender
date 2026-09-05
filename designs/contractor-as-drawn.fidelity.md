# contractor-as-drawn — fidelity ledger (rev. 4)

Every place the compiled model departs from the contractor's issued drawing set.
Read this alongside the renders: a render is persuasive, and the point of this
file is that no approximation is mistaken for the design.

## Revision note

The first pass of this ledger (`cca5274`) was written against a spec that had
already been reconstructed from a prose review rather than the drawings
(`measurements.md` rev.1 said so explicitly). Several of its entries described
departures that turn out not to be real — because the underlying model was
wrong in more basic ways first (rooms on the wrong side of the core, no
balconies, the mezzanine filled in, the roof covering the whole footprint).
This revision reflects the corrected, sheet-sourced model in
`designs/contractor-as-drawn.json` and `measurements.md` rev.2.

**rev.3 (2026-08-17)** adds two sections that rev.2 omitted entirely:
*Architectural detail the schema cannot express at all* ((k)–(n)) and
*Drawing content not reproduced in the generated 2D set*. Rev.2 listed only
departures on features the model does represent, which made the set look far
more complete than it is — a reader comparing `MẶT ĐỨNG CHÍNH` against
`exterior_front.png` sees the difference immediately, and this file did not
account for it. Nothing in (a)–(j) changed; the omission was one of scope.

**rev.4 (2026-09-03)** closes (k)–(n) and, more importantly, corrects rev.3's
account of (k) and (l). Rev.3 recorded them as resolved because the facade
elements and opening divisions reached the *draw model*. They did not reach any
output: `elevation.py` built `facade` and division primitives that neither the
SVG nor the DXF writer had a branch for, so both were silently dropped on the
floor. A reader comparing `MẶT ĐỨNG CHÍNH` with the generated south elevation
still saw a blank wall. Both writers now paint them, and a test asserts every
mullion lands inside its host opening. The lesson is recorded in `lessons.md`:
a primitive in the draw model is not a primitive on the sheet.

Columns: **what the drawing shows → what the model does → why → does it change
what the render says?**

## Geometric departures

### (a) Skewed ~7.2° boundaries → orthogonal plot rectangle
Unchanged from rev.1: the front and rear boundaries run at ~7.2° to the party
walls; the schema's `site` accepts only a rectangle, so both collapse to
`plot_width_mm 3960 × plot_depth_mm 25000`. **Yes — the render cannot show the
taper or the rear-setback crossing flagged in the 2026-08-12 drawing review;
that finding stands and is not re-litigated here.**

### (b) Glazed light-well cap (`ô kính lấy sáng`) → open roof void over the stair
The roof plan glazes an opening directly above the stair (confirmed this pass
by reading the roof plan's own chain: the skylight zone sits in the same
rear-to-front band as the stair, not beside it as rev.1 assumed). The renderer
has no glass: a solid cap would turn the stair into an unlit shaft. The model
punches a `roof.voids` entry over the stairwell's own footprint (3005×4000mm).
**Yes, deliberately — light reaches the stair in the render; the drawing's
narrower ~1700mm glazed insert within a larger unglazed roof is not reproduced,
so the render shows more open sky above the stair than the drawing's glazing
would let through.**

The `meta.views` entry formerly named `gieng_troi` ("light well") actually
pointed at `hall_stair` — a 955mm corridor with a floor slab on every level,
not a light well. **No light well is modelled, and no floor plate is cut**:
the view is renamed `hanh_lang_thang` ("stair corridor") so no artifact claims
a light well exists.

### (c) No lift shaft is labelled on any floor plan — this model infers one
**This is the largest change from rev.1 and the most important thing to read
in this file.** All three residential floor-plan sheets (`MB 1-LUNG`,
`MB 2-3-4`, `MB 5-MAI`) show the stair block followed by an unlabelled walled
void, then a light well, then WC — never a shaft marked "THANG MÁY". The label
"Ô KỸ THUẬT THANG MÁY" (lift plant/technical room) appears exactly once, on
the roof sheet, sized 1950×2000mm, standing 2000mm above the roof slab.

This model infers a 2000×1800mm shaft (`elevator` room, byte-identical on all
7 levels) positioned in the band between the stair and the rear WC, sized from
the roof plant room's printed dimensions rather than from any per-floor
measurement. **This is an inference, not a read.** Two readings were
considered and both are plausible: (1) the shaft genuinely runs the full
height and the floor-plan sheets simply omit the label on repeats — normal
Vietnamese drafting shorthand; (2) there is no passenger lift at all below
roof level, and "Ô KỸ THUẬT THANG MÁY" describes a future/reserved
installation. **This should be confirmed against the DWG or with the
contractor before the elevator's size or existence is treated as fact in any
document derived from this model** — including the 2026-08-12 lift-comparison
research, which already assumed a shaft exists.

### (d) Ensuite WC subdivision (floors 2–5) is a reasonable reconstruction, not a direct read
The rear WC (1600mm deep, full width) is printed and dimensioned identically
to the ground-floor WC. The front bedroom's ensuite is dimensioned only by a
"1950" width label; this model splits the 3400mm zone between the bedroom and
the stair into WC (1950×1600) + hall (2010×1600) + hall (3960×1800) to make it
tile exactly. The real subdivision may differ. **Minor — affects only where an
interior partition sits, not the building's overall reading.**

### (e) Balcony/terrace rooms render as fully enclosed volumes, not open railings
This is a **pipeline limitation, not a modelling choice**, confirmed by
reading `src/homedesign/blender/build_scene.py`: `build_walls()` builds a
full-height wall on every room edge not shared with another room, including
balcony edges; `_add_balcony_parapets()` (the auto-parapet feature) only adds
a 1100mm railing on top of/alongside that wall — it does not suppress it. So
every `balcony`/terrace room in this model (front and rear `ban_công`, both
`sân thượng` zones) compiles and renders as a solid-walled room rather than an
open, railed terrace. **This is not specific to this design** — the same
limitation applies to every balcony in `designs/tubehouse-dream.json`. It is
out of scope for this pass (`src/homedesign/blender/` changes were explicitly
excluded) and is recorded here because it is the reason the exterior_front and
exterior_aerial renders show a solid massing block with almost no glazing or
recesses, even though the spec authors real balcony rooms and real windows
onto them (see (f) below). **Yes — visibly changes the exterior renders.**

> **Resolved (2026-08-14, `plans/2026-08-14-balcony-parapet-render-fix-plan.md`).**
> Root cause fixed, not worked around: `Wall` now carries an owning `room_id`
> (populated during `_derive_walls`; `None` for partition walls), and
> `build_scene.py::build_walls()` skips any exterior wall whose `room_id` is a
> `balcony`-typed room and that carries no opening — `_add_balcony_parapets()`
> then places the 1100mm parapet on exactly those edges. Verified two ways:
> geometrically (the set of balcony-owned walls matches `open_edges()` for
> every balcony in both real designs) and visually (the rebuilt renders —
> `output/png/contractor-as-drawn_exterior_front.png`,
> `_san_thuong.png` — show real glazing and an open, railed edge with sky
> above, not a sealed room). **One correction to how this was first recorded:**
> in `designs/contractor-as-drawn.json` all six balcony/terrace instances have
> zero openings on their own owned walls, so all three free edges of each open
> up. In `designs/tubehouse-dream.json`, `balcony_f2` and `balcony_f3` each
> carry a window authored directly on their own exterior wall
> (`F2_W023`, `F3_W025`) rather than on the partition wall to the bedroom
> behind — the suppression check correctly leaves that one edge as a full wall
> (its safety condition, "no opening on this wall," is false there) and only
> the other two edges of those two balconies get a parapet.
> `tubehouse-dream`'s `terrace_f4` has no such opening and opens fully, like
> every contractor-as-drawn balcony. This is the fix's safety guard working as
> designed, not a defect — but the two balconies are partially, not fully,
> open, which an earlier version of this note overstated.

### (f) Front-facing daylight is modelled as bedroom-to-balcony glazing, not street-facing windows
Each front bedroom/altar room (`ngu_truoc_*`, `tho_f5`) gets a door + a 1400mm
window on the wall shared with its balcony, representing a sliding glass door
— both for `check_habitable_daylight` and because it is the architecturally
real condition (a balcony door is where daylight actually enters). Because of
(e), this glazing is not visible from outside in the current renderer, even
though it is correctly modelled in the spec (verifiable in
`output/svg/contractor-as-drawn_f2.svg` or the compiled model JSON). Interior
rooms without a balcony (`P.KHÁCH`, `P.SINH HOẠT`, rear bedrooms) get a window
on whichever party-wall edge is free — a known pre-existing schema limitation
(the compiler cannot distinguish a real exterior wall from a shared-with-
neighbour party wall; both classify as "exterior" once nothing else is
tiled against them).

> **Resolved (2026-08-14, same fix as (e)).** With the balcony's own open edges
> no longer built as full-height walls, the bedroom-to-balcony door + window on
> the shared partition wall is now visible from the exterior camera on every
> storey — the blocking cause ((e)) is gone, so the front facade shows real
> glazing rather than a solid massing block.

### (g) Stair depth enlarged 3200 → 4000mm (confirmed again this pass)
At the ground-floor storey height (3800mm), `stairs.py`'s Blondel sizing needs
22 risers at 172.7mm (≤190mm, passes) and a 254.6mm going; a U-return with a
3005mm short dimension needs ≥3998.5mm of run. The drawn 3200mm does not fit
under this pipeline's stair rule. The extra 800mm is taken from the rear yard
(`sân sau`, compressed from the drawn 2000mm to 1200mm) rather than growing
the plot, so `plot_depth_mm` stays exactly 25000mm as drawn. **Yes — the core
is 800mm deeper than drawn. This was flagged as a candidate review finding in
the original review and remains one: a shaft that cannot hold a Blondel-
compliant flight at the drawn storeys is a real defect in the issued
dimensions, not a modelling inconvenience.**

### (h) Mezzanine void, floors above it, and the schema's support check
The lửng (level 1) plan shows the zone over the garage and living room
(y 3500–12300) with a diagonal hatch — the drawing's own convention for "no
slab", used identically for the open sân thượng zones on the roof sheets.
This model leaves that footprint untiled on level 1, matching the drawing.

**Resolved (2026-08-14).** The spec now declares the double-height opening
directly: `storeys[1].voids = [{x:0, y:3500, w:3960, d:8800, reason:"Ô THÔNG
TẦNG (double-height void per drawing)"}]`. `checks.check_room_support` counts an
authored void on the storey below as supported-by-design (a beam-spanned
opening), so the former `SÀN GIẢ` placeholder room is gone and the mezzanine
floor slab is genuinely open here rather than an enclosed room. The render now
shows the light-filled double-height space the drawing exists to communicate.

### (i) Rooftop plant room modelled as an enclosed shaft continuation, not a separate structure
`Ô KỸ THUẬT THANG MÁY` stands 2000mm above the roof slab (+23.800 → +25.800) —
a structure on top of the roof, which the schema could not previously represent
(there is no level above the topmost roof).

**Resolved (2026-08-14).** The spec now declares it as
`storeys[6].roof.structures = [{x:1960, y:16300, w:2000, d:1800,
height_mm:2000, name:"Ô KỸ THUẬT THANG MÁY"}]`, a box standing on the roof slab
and rendered with the roof material in both the 3D scene and the elevations.

### (j) No lift pit or overhead
Unchanged from rev.1: the section shows neither, and the schema has no
construct for either. **No — nothing is depicted either way.**

## Architectural detail the schema cannot express at all (added 2026-08-17)

Entries (a)–(j) each describe a *specific* departure on a feature the model does
represent. This section exists because rev.2 of this ledger created a false
impression of completeness by only listing those: the largest gap between the
issued set and the renders is a whole class of content the schema has no
vocabulary for, and which therefore never appears anywhere in the output. A
reader comparing `MẶT ĐỨNG CHÍNH` to `exterior_front.png` sees this immediately;
this ledger did not say it, and should have.

The schema's entire geometric vocabulary is: rooms as axis-aligned rectangles
(`id`/`name`/`type`/`rect`), openings as `type` + `between` + `width_mm`, plus
`stairs`, `roof`, `voids` and `roof.structures`. Consequences:

### (k) Facade articulation is absent — the front elevation is flat massing
> **Resolved (rev.4, 2026-09-03).** `facade_elements` (column, fin, band, panel, awning) are authored across all 7 storeys (21 elements), built as boxes by `build_facade_elements`, and — new in rev.4 — actually drawn on the elevation: `elevation.py` emitted a `facade` primitive that no SVG or DXF branch consumed, so rev.3's claim that it reached the south elevation was wrong. Both writers now paint it (`fill=#5f5f5f` in SVG, layer `ELEV` in DXF) and the silhouette bounding box counts facade elements, so a projecting pillar no longer falls outside the outline. Remaining gap: the cornice is a rectangular band, not a moulded profile.
`MẶT ĐỨNG CHÍNH` carries vertical fins/pilasters running the height of the
middle storeys, a cornice/coping band at the parapet, and framed panel
treatments around the openings. **None of it is modelled**, because there is no
facade-element construct in the schema (`grep -i 'pilaster|fin|mullion|cornice'`
over `src/` matches only camera-fitting code). The renders show a flat white
box with rectangular voids. **Yes — this is the single biggest visual departure
in the set, and the reason the 3D reads as massing rather than as this building.**

### (l) Openings are undivided rectangles — no mullions, transoms or panelling
> **Resolved (rev.4, 2026-09-03).** Street-facing windows carry `divisions {columns: 3/2, rows: 1}`; `joinery.py` emits mullion bars in 3D via `opening_division_lines`, and the elevation now emits a `mullion` primitive from the same function, mirrored correctly on the south/east sides where `_opening_h` flips the drawing axis. `tests/test_render_fidelity.py` asserts a divided window produces bars and that every bar lies inside its host opening. Rev.3 claimed the bars were visible in the south elevation; they were not — the primitive had no writer branch.
Every window on the sheets is subdivided (multi-pane, with transoms; the ground
floor entrance is a panelled door set). An opening in the model is one
`width_mm` and renders as a single rectangular hole with a lintel and sill.
**Yes — the facade's grain and scale come almost entirely from this
subdivision, and none of it survives.**

### (m) Balcony railings are a plain parapet, not the drawn pattern
> **Resolved (rev.4, 2026-09-03).** `parapet_pattern` (`solid` | `slatted`) is a schema property on a room; `homedesign/parapet.py` turns it into a band list — 100 mm slats on a 160 mm pitch, seven within the 1100 mm height — and *both* consumers read that one function: `blender/railings.py` builds the slats and `elevation.py` draws them. All four `BAN CÔNG` (Floors 2–5) are authored `slatted`; the roof terraces keep the solid coping band the sheets draw. Remaining gap: the slat profile is rectangular, and the drawn railing's end posts are not modelled.
The elevations show a patterned railing/balustrade to each `BAN CÔNG`; the model
auto-generates an unarticulated 1100mm solid parapet on open edges (see (e)).
**Yes — visible on every balcony in every exterior view.**

### (n) No material, finish or colour information
> **Resolved for render purposes (rev.4, 2026-09-03); still not a finish schedule.** `assets/cache/` now holds real CC0 2048×2048 PBR sets (diffuse/rough/normal/AO) for six finish families and two HDRIs, all from Poly Haven with source URLs, licence and SHA-256 recorded in `assets/cache/ATTRIBUTION.md`; rev.3's cache was 64×64 placeholder JPEGs and a 2×2-pixel HDRI, so its claim of image-based materials was not true in substance. `make_procedural_material` takes a texture-first path when a family resolves, and `get_material` picks the family through the compiled finish map (`finishes.family_for_palette_key`) rather than a static table, so an authored `finishes` block now changes what renders. Ten furniture kinds are real CC0 meshes, instanced by linked mesh data. **Still true: this is not a finish schedule.** `glass_clear`, `kitchen_run` and `wc` have no CC0 source and stay procedural, and nothing here maps to the sheets' `NỀN GẠCH / VÁCH GẠCH` notation.
The sheets note `KẾT CẤU: MÓNG - CỘT - SÀN BTCT, NỀN GẠCH, VÁCH GẠCH, MÁI BTCT`
and imply finish zones on the elevation. The model carries a single `style`
palette applied by element kind. **Partly — the renders are legible as form but
must not be read as a finish schedule.**

## Drawing content not reproduced in the generated 2D set (added 2026-08-17)

`plan2d.py` emits: room fills, walls, openings with door swings, stair treads,
one dimension chain per axis, north arrow, scale bar and title block. The
contractor's plan sheets additionally carry the following, none of which is
generated. This is recorded as a *drawing-completeness* gap distinct from the
geometric ones above — the underlying model has the data for several of these.

| on the contractor plan | in the generated SVG/DXF | status |
|---|---|---|
| furniture symbols (beds, sofas, dining sets, kitchen fittings, WC fixtures) | drawn in SVG + DXF `FURNITURE` layer | **closed 2026-08-17** |
| level markers (`± 0.000`, `+ 0.200`, `+ 0.300`, `+ 3.800` …) | one per storey, from `storey.base_z` | **closed 2026-08-17** |
| section cut markers (`MC A-A`) | cut line + end labels, from `meta.sections` | **closed 2026-08-17** |
| stair tread numbering (1, 3, 5 … 21, 19, 17) | every tread numbered | **closed 2026-08-17** |
| multi-tier dimension chains (2–3 tiers per side) | fine + full-span bands + overall | **closed 2026-08-17** |
| property boundary (`Ranh lộ giới`) | dash-dot rectangle at the plot extent, labelled at the street edge, in SVG + a `PLOT` DXF layer | **closed 2026-08-19** |
| interior setback lines (`Ranh xây dựng lùi mái`, `ranh khoảng lùi xây dựng`) | absent | **open** — these mark a *building* line distinct from the plot line, e.g. an upper-storey stepback; the schema has no second boundary construct, only the one plot rectangle |
| text callouts (`Tiểu cảnh, ô lấy sáng`, `Lô gia`, `Hành lang thương mại`) | only where they are room names | **open** — no annotation construct in the schema |

The furniture row was a generator defect rather than an approximation: the same
compiled model produced a furnished 3D scene and an unfurnished 2D plan.
`placement.plan_room` was already pure (no `bpy`), so the SVG and DXF writers
now call it directly and the three views cannot disagree.

The dimension tiers are derived, never invented: the middle tier quotes only
coordinates where a room edge runs clear across the plan, because the schema
has no structural grid or column line to quote instead. The fine tier spans
plot edge to plot edge so the front and rear yard setbacks are dimensioned.

**Still true after this work:** the plans are more complete, the elevations and
the 3D are not — (k)–(n) are untouched, and a reader comparing `MẶT ĐỨNG CHÍNH`
to `exterior_front.png` sees the same flat massing as before.

The property-boundary row is drawn from the model's own `plot_width_mm` /
`plot_depth_mm` — the same orthogonal rectangle every wall and room already
uses (DEC-005) — so it adds no new approximation, it just makes the existing
one visible. Confirmed against the ground-floor plan render: the boundary
correctly wraps the untiled front (`SÂN TRƯỚC`) and rear (`SÂN SAU`) yards
that were previously blank white space with no indication they were the plot
edge, and on `f2`–`f5` it shows the `BAN CÔNG` sitting well back of `Ranh lộ
giới` — a rendered check, not just an assertion, that (e)'s recessed-not-
cantilevered reading is drawn consistently.

## Provenance addition: `contractor/approval drawing.jpg` (2026-08-19)

A phone photo of the full stamped/signed approval sheet (all plans, both
elevations, section A-A and the site plan on one physical page) was added to
`contractor/`. It is genuinely new information — the five per-sheet PDFs this
model was built from carry no site plan and no visible north indicator at
all — but its usable resolution is low (960×1280, a folded-paper phone photo,
not a scan), so this pass treats it as **corroboration, not a new primary
source**: nothing in `designs/contractor-as-drawn.json` was changed on the
strength of it alone. What it does confirm at readable resolution:

- **A north-arrow (compass) glyph is printed on the ground-floor and mezzanine
  plan sheets and the site plan**, contradicting this ledger's prior "the
  sheets carry no north point (finding C-04)" — a glyph exists, but at this
  resolution its bearing cannot be read reliably enough to assign
  `site.north_deg` a real value. **The "shadows are decorative, not solar"
  note below is unchanged**; upgrading it needs a proper scan of that glyph,
  not this photo.
- The site plan (`TỔNG MẶT BẰNG`, 1/200) confirms the plot tapers, matches
  (a), and adds real-world context absent from the five sheets: project
  location "thửa 1 phần BC 1281 ... nay là phường Minh Phụng, TP.HCM" and a
  per-storey built-footprint area table. The table's own figures were
  attempted as a cross-check and abandoned: at this resolution individual
  digits in a multi-term formula (e.g. subtraction terms suggesting upper
  floors project further toward the street than the ground floor) cannot be
  read with enough confidence to either confirm or contradict (e), and
  guessing digits from a blurry photo would be a worse error than the gap it
  claims to close.
- Zooming further into the core (stair/elevator/WC band) on any floor-plan
  column, the room-label text becomes illegible before it becomes readable —
  the source photo has already hit its real information ceiling there.
  **(c), the elevator inference, is still open**; this photo does not resolve
  it, and does not raise or lower confidence in either of the two readings
  already on record.

## Enum / type approximations (CON-004, room-type enum grown to 16 values 2026-08-14)

The enum gained `terrace`, `wc`, `utility` and `courtyard` on 2026-08-14 to
reduce the approximation below; the altar room (`P.THỜ`) and combined
kitchen+dining remain `living` and `kitchen` respectively by design.

| label on sheet | model `type` | note |
|---|---|---|
| `P.KHÁCH` | living | |
| `P.NGỦ` / `P.NGỦ CHÍNH` | bedroom | |
| `P.SINH HOẠT` | living | mezzanine family room |
| `P.THỜ` | living | no altar-room enum value |
| `BẾP` + `P.ĂN` (labelled as one room, "P. ĂN + BẾP") | kitchen | combined kitchen+dining, single room, matching the sheet's own single label |
| `WC` | wc | was `bathroom`; retyped 2026-08-14 when the enum grew a `wc` value |
| `NƠI ĐỂ XE` | garage | |
| `HÀNH LANG` (unlabelled circulation, this model's own subdivision) | hall | |
| `THANG` | stairwell | |
| `THANG MÁY` (inferred, see (c)) | elevator | |
| `BAN CÔNG` | balcony | auto parapets, see (e) |
| `SÂN THƯỢNG` | terrace | retyped 2026-08-14 when the enum grew a `terrace` value; open edge with parapet, floor_default |
| `Ô KỸ THUẬT THANG MÁY` | (roof `structures[]` entry — see (i)) | |

## Programme summary (corrected)

Per-floor programme, confirmed room-by-room against the sheets this pass:

- **L0 (Trệt):** garage → P.KHÁCH → [core] → WC → BẾP+ĂN. One living room, one
  kitchen/dining, both before the stair reads garage-first (rev.1 had this
  reversed).
- **L1 (Lửng):** void over garage+khách (untiled, see (h)) + P.SINH HOẠT at
  the rear. Rev.1 filled the whole floor and invented a bedroom here; neither
  is drawn.
- **L2–L4 (Tầng 2–4):** identical — one bedroom front (with ensuite +
  balcony), one bedroom rear (with ensuite). **Two bedrooms per floor, not
  three** — rev.1 invented a third bedroom in a slot that is actually the WC.
- **L5 (Tầng 5):** P.THỜ (altar room) front with a balcony, a front ensuite
  WC under the `Ô lấy sáng` light well beside the stair, and one bedroom rear.
  Rev.1 gave this floor two bedrooms and no altar room. Rev.2 dropped the
  front WC entirely ("no toilet/sink icons in that zone") — disproved by the
  10× zoom of `MB 5- MAI-Model.pdf` (2026-08-21 round 2), which shows the
  X-hatched well plus a sink-and-toilet WC directly below it; the model now
  carries both (`wc_truoc_f5`, void 2000×1500 over the hall).
- **L6 (Sân thượng):** open terrace front and rear, core roofed over.

## Shadows are decorative, not solar

Unchanged from rev.1: the schema has **no north angle**, the sheets carry **no
north point** (finding C-04 in the 2026-08-12 review), and the sun rig is
fixed (55°/35°). **Shadows in these renders are decorative and must not be
read as daylight or solar analysis.**

## GLB inlining (ASM-007)

To be confirmed against the rebuilt export — see the render/publish log. The
rev.1 export was 1.12MiB (well under the 8MiB inline limit); this revision has
more rooms and more openings, so the size should be re-checked rather than
assumed.

## Premise changes for other documents

Unchanged in substance from rev.1, but the provenance is now weaker, not
stronger: `research/2026-08-12_tubehouse-lift-comparison.md` assumed a
1000×1400mm (1.4m², five-stop, machine-room-less) lift. This model's shaft is
2000×1800mm (3.6m², seven stops, with a rooftop plant room) — **but per (c)
above, that shaft's existence and size are this model's own inference from a
single roof-plan label, not a confirmed measurement.** Both the original
1.4m² premise and this model's 3.6m² figure should be treated as provisional
until the contractor confirms whether a passenger lift is being built at all.
That document is **not edited** here; the revision is still owed separately,
and should wait for that confirmation rather than simply substituting one
unverified number for another.

## Provenance

All dimensions in `designs/contractor-as-drawn.json` trace to the five PDFs
under `contractor/` via `designs/contractor-as-drawn.measurements.md` (rev.2),
which was produced by rendering each sheet at 8–24× zoom and reading the
printed dimension strings directly — not reconstructed from the prose review,
unlike the first pass of this file. The schema sets `additionalProperties:
false` on every object, so there is no field for this provenance — hence
these two sidecar files.

## Pipeline change carried over from rev.1 (unchanged, still necessary)

Compiling a spec whose room names carry Vietnamese diacritics exposed a latent
encoding bug: `homedesign.__main__._load_spec` / `_write_model_json` (and the
SVG writers in `plan2d.py`/`elevation.py`, and the render-sidecar helpers in
`model.py`) read/write text with the locale default encoding, which is CP1252
on Windows and mangles `P.KHÁCH` → `P.KH╚CH` or raises. Fixed by pinning
`encoding="utf-8"` at those I/O sites (commit `eb6e6bf`), matching the
documented UTF-8 convention. No logic changed. This fix is still in effect and
was re-verified this pass (`python -c "...json.load(...,encoding='utf-8')..."`
prints every room name with correct diacritics).
\n\n## Rev.4 — 2026-08-29 Render Fidelity\nClosed k,l,m. Added finishes, facade_elements, alley, neighbours. Ledger items a,c,g remain excluded.\n
## Rev.5 — 2026-09-04 Fidelity push (3D only; no geometry moved)

No room rect, opening, stair, void or roof was moved, resized or re-typed.
All changes are finish routing, light rig, or Blender-side detail:

- **Walls render as plaster, not timber.** `by_room_type` (`living=wood_board`)
  leaked into the wall channel via `resolve_finish`, so every living/bedroom
  wall rendered as deck-boards. `by_room_type` now scopes to `floor` only
  (`src/homedesign/finishes.py`); `room:khach:wall` resolves `plaster_painted`
  while `room:khach:floor` stays `wood_board`.
- **Frames render as satin aluminium, not diamond plate.** Spec authors
  `frame=aluminium`, which had no procedural family and silently degraded to
  `metal_brushed` → cached `metal_plate` PBR. `aluminium` is now a real family
  (procedural satin graph, offline-safe); `frame` maps to it.
- **Facade articulation moved to the street face.** All 21 `facade_elements`
  were authored `side:south` (rear plane) while the hero camera and
  `SÂN TRƯỚC` face north — the front render was correctly empty. Flipped
  south→north; north elevation now carries 21 facade items (was 0). Added
  `facade_trim`/`facade_field`/`metal_sheet` palette entries so fins read as
  concrete trim, not wall-white camouflage.
- **Interior light rig: one warm omni per room + per-view isolation.**
  Cool-white ceiling AREAs left camera-side party walls near-black under AgX.
  Each enclosed room now gets one warm `(1.0, 0.83, 0.64)` POINT scaled by
  floor area (`area_m2 * 10`, 20–250 W, C3 rule kept as floor), unshadowed
  (56 cube-shadow maps exhausted the iGPU atlas — proven by OOM crash), and
  each view renders with only its own room's fill alive (`render(...,
  view_rooms)`). Spot-check pixels (sRGB): khach W160/E112, ngu_f2 W167/E111,
  bep_an W160/E99, gara W161/E97 — shaded side reads as warm plaster, no blue
  cast anywhere. Lesson recorded the hard way: verify against pixels
  (`PIL`), never eyeballed previews.
- **Doors read as doors.** Leaves were flat zero-swing slabs; each leaf now
  carries a lever handle (backplate + lever, both faces, frame material) at
  1000 mm above the sill. Same opening size/position.
- **Skirting follows the room floor.** `_add_skirting` used the generic
  `element:floor` (ceramic checker in timber rooms); now scoped by `room_id`.
- **Furniture hits the cache.** `coffee_table`/`dining_table` never matched
  `table.glb` (exact-kind lookup) and always fell back to boxes; aliased to
  the cached dining-table mesh.

Known gaps (unchanged, finish-level only): flat door leaves (no recessed
panels), no textiles (rug/curtains/throws), no pendant/cove fixtures or wall
art, head-on fins sub-pixel at 40 m standoff (a 3/4 aerial would show them),
hero stills omit neighbour massing by DEC-009 toggle (assess street feel via
`homedesign build ... --show-neighbours --out <dir>`).

## Rev.6 — 2026-09-04 Detail pass (rugs + panelled doors; no geometry moved)

- **Rugs.** `living` gains a 1.6×1.1 m rug under the coffee table, `bedroom`
  a runner across the foot of the bed (`placement._plan_living/_plan_bedroom`;
  kind `rug`, h 20 mm, procedural bordered builder, `upholstery` fabric
  material). Rugs are collision-exempt in `resolve_collisions` (clamped only)
  and flow to plans and DXF through the same `plan_room` source — footprint
  verified on `contractor-as-drawn_f0/f2.svg` (`data-furniture="rug"`).
  Preview-visibility note: 20 mm pile at 3–4 m is ~3 px at 960×540, so the
  hero stills barely move; the payoff is in the orbited GLB viewer and any
  `--profile final` plates.
- **Panelled doors.** Every leaf keeps its size/position but gains two
  stacked rail frames per face plus the earlier lever handle (`joinery.py`;
  static coords, valid while `DOOR_SWING_RAD == 0`). Same honest limitation
  as rugs: shadow-line detail for close/final views, subtle at preview range.

## Rev.7 — 2026-09-04 Furnishing pass (floor lamp + nightstands; no geometry moved)

- **Floor lamp** (`living`, rooms >3×3 m): weighted base + slim pole + drum
  shade in porcelain white at the far corner — the bright vertical accent the
  hero stills were missing, and a direct probe of the east-wall wash.
  Verified in `cam_khach` frame and by blend query (`lamp_shade_3.31_11.60`).
- **Nightstands** (`bedroom`): cabinet + proud top + drawer + knob on each
  fitting side of the headboard. Verified in blend (`nightstand_body_*`);
  `ngu_f2` re-render pixel-checked (bed-grey dominant lower half).
- Process lesson (tooling, not design): the image-read path served stale
  bytes for freshly overwritten PNGs more than once this session (including
  one fully crossed pair), sending two diagnoses down wrong paths. Ground
  truth is `PIL` pixel sampling and `blender --background` probes of
  `output/blend/` — never a re-read of a just-written render.

## Rev.8 — 2026-09-04 Street hero view (new camera kind; no geometry moved)

- **New `exterior_street` view kind** (schema + `View` literal + skill doc +
  mirror synced): 3/4 hero from the south-east street corner, +8° up at the
  facade plane's 55% height — the angle pro VN tubehouse renders actually use.
  Pure `camera_fit.exterior_street_camera` (whole-box fit, 35 mm), thin Blender
  wrapper, per-view light isolation treats it as exterior (sun only).
  Framing test sweeps every spec (SE of plot, street side, above ground,
  facade-plane target). Added as 13th view `street` on the flagship.
- Measured on the render: 39% building mass, 76% vertical fill, zero cropped
  edges. Balcony slabs + slatted parapets + bedroom glazing read on every
  level; pilotis + entrance + roof plant room all present. The 120 mm fins
  stay subtle even at parallax (3% of facade width — drawn dimension, kept
  honestly). Heros with `--show-neighbours` remain a separate assessment
  (`output_streetscape/`): the 14 m party block swallows the lower storeys,
  which is authentic siting and useless facade assessment — hence DEC-009
  default stands.

## Rev.9 — 2026-09-04 Pendant sources (new kind; no geometry moved)

- **Pendants** over dining tables, coffee zones and room centres
  (`placement` + `_build_pendant`: canopy, drop cord, drum shade, bulb, all
  in dark-bronze `frame` — porcelain-white drums proved camouflaged against
  the plaster ceiling, the third instance of the material-camouflage class).
  Ceiling height threads `furnish_storey → build_item → _Placer.ceiling_z`
  so drops land at dining height (~1.6–1.8 m, inside the interior frame, not
  above it); pendants are collision-exempt like rugs. Drops were tuned by
  pixel measurement, not eyeballing (a 2.2 m drop clears the 12–24 mm
  interior frame entirely).
- Scale note: each pendant is 4 small objects; ~20 new objects per full
  build, negligible next to 2500+.

## Rev.10 — 2026-09-05 Print handover (pipeline fix; no geometry moved)

- **Final gallery + brief + publish.** 13-view `final` gallery (1920×1080,
  legacy EEVEE 256spp), A3 brief under `--require-fresh` (18.6 MB), and a
  hash-verified `deliverables/contractor-as-drawn/` (png + gltf + viewer +
  pdf). No plan/spec/model change in this pass.
- **Pipeline fix this handover exposed:** the GLB export never wrote the
  `.glb.json` sidecar `freshness.check_freshness` demands, so `publish`
  refused every model-changed GLB without `--force` (prior publishes must
  have forced past it). The export now writes one via the same
  `write_render_sidecar` helper as PNGs (`build_scene.py`, after optimize);
  covered by a pure round-trip test. The current GLB's sidecar was backfilled
  with the verified current hash (`a34fd59b479a`) — recorded here, not hidden.

## Rev.11 — 2026-09-05 Phone GLB back inside budget (LOD, no geometry moved)

- **Failure:** `test_the_published_glbs_are_inside_their_budgets` went red —
  `contractor-as-drawn-light.glb` 8.87 MB vs the 6 MiB phone budget. The old
  committed file was 5.84 MB (97% of budget); the furnishing pushes added
  ~3 MB. GLB inspection (`gltf-transform inspect`) attributed it exactly:
  curated asset meshes 6.07 MB (a draped mattress alone is 1.9 MB), new
  ornament (panels/handles/knobs/rug fields) ~1.4 MB.
- **Fix, two halves, desktop untouched:** (1) meshes over 20k polys are
  collapsed once at asset import (ratio 0.4 — smooth upholstery, UVs kept);
  (2) the light source is exported with sub-15 cm ornament hidden
  (`viewer.LIGHT_EXCLUDE_FRAGMENTS`, substring match — joinery names carry
  the opening id first) and derived normally. Along the way: `hide_render`
  alone does NOT exclude objects from the glTF exporter; `use_visible=True`
  plus `hide_viewport` is required (verified: decor stayed in without it).
- **Measured:** light 8.87 → 5.54 MB (dry-run proven before committing to a
  full rebuild), main 20.1 → 18.3 MB. Full suite 309 passed, publish clean.

## Rev.12 — 2026-09-05 Calm teak doors (finish-only; no geometry moved)

- **Door leaves muted past the deck texture.** The cached `wood_floor_deck`
  PBR set rendered every leaf as high-contrast orange striping that shouted
  over the muted room (fresh-eyes audit of the final khach). Leaves now skip
  the image-texture path (`use_textures=False` on `door_leaf`) and render the
  procedural wood graph in a deep teak base, whose contrast is tuned for
  joinery — safe because no other `wood_board` user reaches that branch (all
  hit the cache first). Measured on the hero: stripe-contrast stdev 1.7 with
  R-B spread 39 (was high-contrast banding) at a muted mid-brown mean.

## Rev.13 — 2026-09-05 Asphalt carriageway readout (finish-only; no geometry moved)

- **Street section reads.** The authored carriageway + kerb boxes were built
  but invisible: the `street` finish resolves to the `concrete_formed` family
  whose cached PBR set renders near-identical to the ground plane (fourth
  instance of the material-camouflage class). The `street` key now skips
  image textures like `door_leaf`, rendering the procedural concrete graph in
  its dark authored base — asphalt against beige ground, kerb edge between.
  Finish-map families unchanged, so the model hash and all sidecars stand.

## Rev.14 — 2026-09-05 Bedroom camera off bed axis (framing-only; no geometry moved)

- **Bedrooms no longer render empty.** The interior camera stood centred on
  the near wall — dead on the bed's long axis, inside its footprint — so the
  mattress filled only the below-frame blind zone and the hero showed bare
  walls. Bedroom cameras now anchor at quarter width with an asymmetric
  half-width fit (other room types bit-identical by construction).
  `ngu_f2` went from 0% to 51% bed-grey in-frame; nightstand + runner +
  pendant join the composition with foreground depth. No clipping introduced
  (0.00% pure white at frame bottom).

## Rev.15 — 2026-09-05 Kitchen camera faces the run (framing-only; no geometry moved)

- **Kitchen hero shows the kitchen.** The run hugs the near wall (under and
  behind a centred lens), so the old view showed window + fridge + floor but
  never a counter. Kitchen cameras now shoot from the far end back at the run
  (mirrored for wide rooms); all other types bit-identical. The run reads as
  dark timber with tap and panelled door behind it — honest: `kitchen_run`
  resolves through the `cabinetry → wood_board` family like it always has.

## Rev.16 — 2026-09-05 Corridor wall wash (light rule; no geometry moved)

- **Narrow rooms get a light floor of 120 W.** Area-scaled omnis left the
  0.955 m stair corridors' far wall at (48,53,62) — blue-tinted black. A
  150 W isolation test proved the response linear (neutral grey, no blowout
  elsewhere), so rooms under 1.5 m in either dimension now floor at 120 W.
  Production reads (72,71,75) against (155,151,153): shaded side, no cast.
  WC (1.6 m min) and shafts are untouched by the threshold.
- Also reverted: hall pendants, which loomed balloon-like 2 m from the
  corridor lens. Narrow halls stay bare; wide halls keep pendant + console.

## Rev.17 — 2026-09-05 Planted terrace (finish routing; no geometry moved)

- **Planter reads planted, not empty.** The cached `planter_box_01` mesh
  ships as an empty concrete box + soil (verified in-blend: only
  `furn_planter_*` objects, no foliage), so the terrace showed a black pit.
  `PROCEDURAL_FIRST = {"planter"}` routes planters to the procedural builder,
  which now grows two overlapping rounded mounds in a new `foliage` finish
  (flat-fallback `plant_green` family — no cached green texture exists
  offline): pit-zone pixels moved black → sunlit leaf (130,154,117).
- Process note: the image-read path served the previous mint-slab bytes for
  this file three times running; the verdict comes from PIL sampling the
  file, per the standing rule.

## Rev.18 — 2026-09-05 Plaster ceilings un-entombed (3 mm offset; no geometry moved)

- **Intermediate ceilings render plaster, not slab soffit.** The ceiling
  plane sat 15 mm below the storey top — inside the 50 mm slab above — so
  every intermediate room showed the upstairs floor finish overhead (timber
  planks over the mezzanine living room). Planes now hang 3 mm under the
  slab underside; void cut-outs behave exactly as before. Measured in `lung`:
  ceiling zone went 100% wood-tone to 0.0%, mean (127,121,120) shaded plaster.

## Rev.19 — 2026-09-05 Smooth drum shades (tessellation; no geometry moved)

- **Pendant/floor-lamp drums at 32 segments.** 16-segment drums showed flat
  facets on 0.38 m shades at hero distance; verified in-blend (64 verts =
  32 segments with shared cap rims, not 16) and by pixel steppiness across
  the drum. Everyday cylinders (legs, cords, knobs) stay at 16.

## Rev.20 — 2026-09-05 Horizon haze (environment only; no geometry moved)

- **No more studio void.** The PureSky HDRI goes near-black below the
  horizon, so aerials showed the ground plane as a beige paper sheet
  floating in navy nothing. The HDRI path now blends to a warm concrete
  haze wherever the look direction dips below the horizon (Z < 0.02 on the
  Generated vector); sun position and sky above are untouched, as is the
  gradient fallback. Frame corners went navy to seamless beige (172,169,164)
  with no visible plane edge.

## Rev.21 — 2026-09-05 Viewer GLB brought current (provenance gap; no geometry moved)

- **Interactive model lagged eight turns.** `model_hash` covers the spec, so
  material-route, ceiling-offset, tessellation and drop-height work never
  invalidated the GLB — the published viewer showed orange doors and
  entombed ceilings long after the stills moved on. Rebuilt `--gltf` from
  current code and republished; the hash contract is blind to Blender-side
  code by design, so rebuilt-on-change discipline (not the hash) is what
  keeps the viewer honest.
