# contractor-as-drawn — fidelity ledger (rev. 2)

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
- **L5 (Tầng 5):** P.THỜ (altar room, no ensuite) front with a balcony, one
  bedroom rear. Rev.1 gave this floor two bedrooms and no altar room.
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
