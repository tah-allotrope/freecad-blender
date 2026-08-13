# contractor-as-drawn — fidelity ledger

Every place the compiled model departs from the contractor's issued drawing set.
Read this alongside the renders: a render is persuasive, and the point of this
file is that no approximation is mistaken for the design.

Columns: **what the drawing shows → what the model does → why → does it change
what the render says?**

## Geometric departures

### (a) Skewed ~7.2° boundaries → orthogonal plot rectangle
The front (`ranh lộ giới`) and rear boundaries run at ~7.2° to the party walls,
so both yards taper (front 3000→2500, rear 2500→2000). The schema's `site` accepts
only a rectangle, so both collapse to `plot_width_mm 3960 × plot_depth_mm 25000`
and the tapering yards become untiled plot. **Yes — the render cannot show the
taper or the finding C-03 setback crossing; those stay in the review report.**

### (b) Glazed light-well cap (`ô kính lấy sáng`) → open roof void
The roof plan glazes the 1700 × 1800 opening over the core. The renderer has no
glass: a solid cap would turn the shaft into an unlit slot and render the core
shot black. The model punches a `void` over the light well instead (DEC-004).
**Yes, deliberately — the model is truthful in *depiction* (light reaches the
shaft) though not in literal geometry (glass).**

### (c) ~8 winder treads → `u_return` flight
The 180° turn is drawn with ~8 winders fanning from the newel corners. The schema
has no winder; the stair is emitted as `mode: "u_return"` with treads re-derived
per storey. **Marginal — the stair reads as a U-return but the winder geometry
(C-08) is not depicted.**

### (d) One copy-pasted stair block → risers re-derived per storey
The drawing repeats the same 21-tread block on every plan, but the storeys are
3800 / 3200 / 3400 mm. `stairs.py` sizes each flight from its storey height, so
the model's risers differ per storey — exactly the per-storey setting-out detail
finding C-07 asks the contractor to issue. **No — this *corrects* the drawing
rather than approximating it; recorded because it no longer reproduces the sheet.**

### (e) Stair depth enlarged 3200 → 4000 mm
The drawn 3005 × 3200 stair shaft cannot hold a Blondel U-return at a 3800 mm
storey (S-2 needs 3998 mm run). The shaft is enlarged by the smallest amount that
satisfies the inequality. **Yes — the core is 800 mm deeper than drawn. Flagged
as a candidate review finding: a shaft that cannot hold a compliant flight is a
defect in the drawing, not a modelling inconvenience (RISK-02-01).**

### (f) Light well 2200 × 1300 → 1160 × 1600 mm
The drawn well is 2.86 m²; the model uses 1160 × 1600 (1.86 m²) so the void tiles
the 1600-deep lift band. The 1300 dimension is preserved nowhere in the model —
the well is smaller than drawn. **Yes — the light well reads smaller than the
sheet; noted for the programme discussion (its stack-effect role is C-02).**

### (g) Rooftop plant room 2000 mm high → level-6 storage room at 3200 mm storey height
`ô kỹ thuật thang máy` is 2000 × 1900 mm standing 2000 mm **above the roof slab**
(+23.800 → +25.800). The schema has no construct for a room on top of the roof, so
it is modelled as a `storage` room on level 6 (DEC-014), where its walls rise the
full 3200 mm storey height and sit under the roof slab. **Yes — the plant room
reads as a taller box on the terrace rather than a short box on the roof, and it
is hidden under the roof in the aerial shot.**

### (h) No lift pit or overhead
The section shows neither pit nor top-landing overhead (finding C-06). The schema
has no construct for either. **No — nothing is depicted either way.**

## Enum / type approximations (CON-004)

| label on sheet | model `type` | note |
|---|---|---|
| `P.KHÁCH` | living | |
| `P.NGỦ …` | bedroom | |
| `P.SINH HOẠT` | living | family room |
| `P.THỜ` | living | no altar-room enum value |
| `BẾP` / `P.ĂN` | kitchen | combined into one `bep_an` room |
| `WC` | bathroom | |
| `KHO` | storage | |
| `NƠI ĐỂ XE` | garage | |
| `HÀNH LANG` / `SẢNH` | hall | |
| `THANG` | stairwell | |
| `THANG MÁY` | elevator | |
| `SÂN THƯỢNG` / `LÔ GIA` / `BAN CÔNG` | balcony | auto parapets |
| `Ô KỸ THUẬT THANG MÁY` | storage | plant room |

## Programme reconciliation

The plan's 12-view table annotates `khach`/`bep_an` as "level 2" and `sinh_hoat`
as "level 4". The measured review places the living room and kitchen/dining on
**tầng 1 (level 0)**, the family room on the **lửng (level 1)**, and tầng 2–5 as
bedrooms with `P.THỜ` on tầng 5. The model follows the **measured** programme
(the whole point is "exactly as drawn"), so the views map to:

- `khach` → level 0 living; `bep_an` → level 0 kitchen; `lung` and `sinh_hoat` →
  the level 1 family room's two halves. Levels 2 and 4 carry no dedicated view.

## Shadows are decorative, not solar

The schema has **no north angle**, the sheets carry **no north point** (finding
C-04), and the sun rig is fixed (55°/35°). **Shadows in these renders are
decorative and must not be read as daylight or solar analysis.**

## GLB inlining (ASM-007)

**Resolved: does not apply.** `output/gltf/contractor-as-drawn.glb` is
**1 179 312 bytes (1.12 MiB)**, well under `viewer.py`'s 8 MiB
`INLINE_GLB_LIMIT_BYTES`, so the viewer inlines it base64 and the published
`deliverables/contractor-as-drawn/viewer/contractor-as-drawn.html` is fully
self-contained. Seven levels' massing is compact because walls/slabs are simple
boxes and the furniture is procedural.

## Premise changes for other documents

The drawn lift shaft (~1500 × 1600 mm ≈ 2.4 m², seven stops, rooftop machine room)
supersedes the 1000 × 1400 mm / 1.4 m² / five-stop / machine-room-less premise of
`research/2026-08-12_tubehouse-lift-comparison.md`. That document is **not edited**
here; the revision is still owed separately.

## Provenance

All dimensions in `designs/contractor-as-drawn.json` trace to the five PDFs under
`contractor/` via `designs/contractor-as-drawn.measurements.md`. The schema sets
`additionalProperties: false` on every object, so there is no field for this
provenance — hence these two sidecar files.

## Pipeline change (necessary deviation from "no src changes")

Compiling a spec whose room names carry Vietnamese diacritics exposed a latent
encoding bug: `homedesign.__main__._load_spec` / `_write_model_json` (and the SVG
writers in `plan2d.py`/`elevation.py`, and the render-sidecar helpers in
`model.py`) read/write text with the locale default encoding, which is CP1252 on
Windows and mangles `P.KHÁCH` → `P.KH╚CH` or raises. Fixed by pinning
`encoding="utf-8"` at those I/O sites, matching the documented UTF-8 convention.
No logic changed.
