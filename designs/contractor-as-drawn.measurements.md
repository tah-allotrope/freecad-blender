# contractor-as-drawn — measurement record (rev. 2)

Traceable table of every dimension behind `designs/contractor-as-drawn.json`, read
directly from the five vector PDFs under `contractor/` at 8–24× zoom (PyMuPDF
raster crops; the sheets carry no extractable text, so every figure below is a
visual read of the printed dimension strings, cross-checked against the vector
line geometry at K = 43.0 mm/pt where noted).

## Revision note

The first pass of this file (committed in `cca5274`) stated plainly that it could
not read the sheets and reconstructed the layout from the 2026-08-12 prose review
plus invented subdivisions. That was wrong in ways that mattered: rooms were on
the wrong side of the core, the mezzanine void was filled in, no balconies/loggias
were modelled, the roof covered the whole footprint instead of just the core, and
a fabricated 1500×1600mm "measured" elevator was invented from nothing. This
revision replaces it with a direct read of all five sheets.

## Coordinate convention (unchanged, ASM-001)

- `x = 0` west party wall, `x = plot_width_mm` east party wall.
- `y = 0` street / `ranh lộ giới` (front), `y` increasing toward the rear (`sân sau`).
- Plot is the orthogonal collapse of the drawn ~7.2°-skewed rectangle (DEC-005).

## Plot

| field | value | source |
|---|---|---|
| `plot_width_mm` | 3960 | frontage printed 3950 on every sheet; +10mm orthogonal margin, unchanged from rev.1 |
| `plot_depth_mm` | 25000 | `MB 1-LUNG` outer chain, printed directly: `25000` |

## Storey heights (Section A-A + front elevation level tags — unchanged from rev.1, confirmed again this pass)

| level | name | height_mm | from tags |
|---|---|---|---|
| 0 | Trệt | 3800 | ±0.000 → +3.800 |
| 1 | Lửng | 3200 | +3.800 → +7.000 |
| 2 | Tầng 2 | 3400 | +7.000 → +10.400 |
| 3 | Tầng 3 | 3400 | +10.400 → +13.800 |
| 4 | Tầng 4 | 3400 | +13.800 → +17.200 |
| 5 | Tầng 5 | 3400 | +17.200 → +20.600 |
| 6 | Sân thượng | 3200 | +20.600 → +23.800 |

Sum = 23800mm (+23.800, the roof/mái slab level). The plant room rises a further
2000mm to +25.800 above the roof slab — a rooftop structure, not a storey.

## Ground floor (`MB 1-LUNG-Model.pdf`, "MẶT BẰNG TẦNG 1") — direct read

Rear-to-front dimension chain, printed directly on the west-wall side:
`2500(taper) / 200 / 1600 / 4100 / 1800 / 3200 / 4800 / 4000 / 3000 / 500(taper)`.
East-wall side chain: `2000 / 5700 / 1800 / 3200[=19500 bracket] / 4800 / 4000 /
3500`. The two sides differ because the front/rear boundaries taper (~7.2°,
DEC-005); the numbers used below are the room-defining values common to both
reads, reconciled to the printed `19500` and `25000` brackets.

Front (street) to rear, as modelled (y = 0 at `ranh lộ giới`):

| y range | depth | zone | source |
|---|---|---|---|
| 0–3500 | 3500 | SÂN TRƯỚC (untiled yard) | "3000" room chain + "500" taper gap, printed |
| 3500–7500 | 4000 | NƠI ĐỂ XE | printed "4000", directly labelled |
| 7500–12300 | 4800 | P.KHÁCH | printed "4800", directly labelled — **note: this is BEFORE the stair, not behind it as rev.1 modelled** |
| 12300–16300 | 4000 | stair core | printed **3200**, enlarged to 4000 (S-2 minimum, see fidelity ledger — same defect rev.1 found, now correctly positioned) |
| 16300–18100 | 1800 | elevator/technical band | printed "1800"; no per-floor label (see Core note below) |
| 18100–19700 | 1600 | WC | printed "1600", directly labelled |
| 19700–23800 | 4100 | BẾP & ĂN (P. ĂN + BẾP) | printed "4100", directly labelled |
| 23800–25000 | 1200 | SÂN SAU (untiled yard) | printed "2000", **compressed by 800mm to absorb the stair enlargement** — see Discrepancies |

Sum: 3500+4000+4800+4000+1800+1600+4100+1200 = 25000mm. Exact.

## Core note — no elevator is labelled on any residential floor plan

Every one of `MB 1-LUNG`, `MB 2-3-4`, `MB 5-MAI` shows the stair block (21-tread
U-return, numbered treads 1..21) followed by an unlabelled walled void, then
"Ô lấy sáng 2200" (an open light well), then WC. **No sheet prints "THANG MÁY"
next to a shaft on any floor plan.** The label appears exactly once, on
`MB MAI - MD-Model.pdf`, as "Ô KỸ THUẬT THANG MÁY" (lift plant/technical room),
1950×2000mm, positioned in the same rear-to-front band as the floor plans'
unlabelled void (roof chain: SÂN THƯỢNG rear 5700 / gutter 1000 / **[1950+2000
tech band, depth ~1900]** / skylight zone / gutter 1000 / SÂN THƯỢNG front 4000 —
this lines up with the floor plans' 1800mm void band between the stair and the
WC/kitchen zone).

**This model infers a lift shaft stacking through all 7 levels, positioned in
that band, sized 2000×1800mm (east portion of the band) from the roof plant
room's printed dimensions — an inference from the roof plan, not a direct
per-floor read, because no floor plan labels a shaft.** This is weaker
provenance than every other room in this file and is the single largest
remaining uncertainty; it should be confirmed against the DWG or by asking the
contractor directly. See `fidelity.md`.

## Core (byte-identical on all seven levels)

| room | id | x | y | w | d | source |
|---|---|---|---|---|---|---|
| stairwell | `stairwell` | 0 | 12300 | 3005 | 4000 | flight 2×1154 + well 697 = 3005 (vector-measured, rev.1, unchanged); depth 4000 is the S-2 U-return minimum at H=3800, enlarged from drawn 3200 |
| hall (beside stair) | `hall_stair` | 3005 | 12300 | 955 | 4000 | circulation, inferred (remainder of stair band) |
| elevator | `elevator` | 1960 | 16300 | 2000 | 1800 | **inferred from roof plant room dims** (Core note above), not a direct floor-plan read |
| hall (beside elevator) | `hall_elev` | 0 | 16300 | 1960 | 1800 | circulation, inferred (remainder of elevator band) |

The light well is **not authored as a room** — the roof punches a `void` over
the stairwell's own footprint (DEC-004: the drawing's "Ô kính lấy sáng" glazed
skylight sits directly over the stair per the roof plan's chain alignment, not
over a separate feature).

## Mezzanine (L1, `MẶT BẰNG LỬNG`, right-hand plan on `MB 1-LUNG-Model.pdf`)

The rear zone (WC+bếp slot on L0) is replaced by one open room, **P. SINH HOẠT**,
labelled directly, spanning y 18100–23800 (5700mm, matching the combined
WC+BẾP footprint below — the printed "+3.800" datum confirms this is the
mezzanine floor level).

**The front zone (y 0–12300, over NƠI ĐỂ XE + P.KHÁCH) is drawn with a diagonal
hatch (×) and is explicitly NOT floored** — it is a double-height void open down
to the garage and living room below. This is read directly off the sheet, not
inferred: the hatch pattern is the drawing's own convention for "no slab", used
identically for the SÂN THƯỢNG zones on the roof-level sheets.

This model leaves y 0–12300 on level 1 completely untiled (no rooms authored),
matching the drawing exactly. Only the stair, elevator, hall and P. SINH HOẠT
are built at this level.

## Tầng 2, 3, 4 (`MB 2-3-4-Model.pdf` — identical layout, different height datum only)

Front (street) to rear:

| y range | depth | room | source |
|---|---|---|---|
| 3500–4900 | 1400 | Ban công (balcony) | printed "1400", directly labelled, recessed within the building line (not cantilevered — see fidelity ledger) |
| 4900–8900 | 4000 | P. NGỦ (front bedroom) | printed "4000" |
| 8900–10500 | 1600 | WC (front bedroom ensuite) | printed "1950"(width)/"1600"(depth pattern, matching the rear WC) |
| 8900–10500 | (x1950–3960) | hall beside ensuite | inferred, remainder of the WC's own depth band |
| 10500–12300 | 1800 | hall (full width, to stair) | inferred, remainder of the 4800 slot after the 1600 WC |
| [core, see above] | | | |
| 18100–19700 | 1600 | WC (rear bedroom ensuite) | printed "1600", directly labelled, same pattern as L0 |
| 19700–23800 | 4100 | P. NGỦ (rear bedroom) | printed "4100" |

Only **one bedroom front, one bedroom rear** — two total per floor, each with its
own ensuite. Rev.1 invented a third bedroom in the WC/storage slot; no third
bedroom is drawn on any sheet.

## Tầng 5 (`MB 5- MAI-Model.pdf`, "MẶT BẰNG TẦNG 5")

Same rear zone as tầng 2–4 (WC 1600 + P. NGỦ 4100, one bedroom). Front zone
differs: **P. THỜ** (altar room), 4000mm, printed directly, with an altar
counter/table against its rear wall (drawn, not a WC). Ban công (1400) at the
front, same as tầng 2–4.

**Midband (rev.3 correction, 2026-08-21 round 2).** Rev.2 called the whole
stair→P.THỜ slot "open circulation with a serving counter — no ensuite WC on
this floor's front zone". The 10× zoom (`output/contractor_pdf_png/
zoom_t5_midband2.png`, clip of `MB 5- MAI-Model.pdf`) disproves the "no WC"
half: directly below the stair sits an X-hatched **Ô lấy sáng** light well
(right half, printed chain "1500" deep), and directly below that a **WC with
sink + toilet**, entered by a door from the open hall on its left. The model
therefore splits the 3400mm midband as: HÀNH LANG column x0–1960 full depth;
WC x1960–3960 × 1900; void (the well) x1960–3960 × 1500 against the stair
wall — aligned with the elevator box's left edge, mirroring tầng 2–4's
1950-wide front WC pattern. The serving-counter reading survives only in the
open hall column.

## Roof (`MB 5- MAI-Model.pdf` right-hand plan "MẶT BẰNG SÂN THƯỢNG", and `MB MAI - MD-Model.pdf` left-hand plan "MẶT BẰNG MÁI")

Two sheets show the roof level: the "sân thượng" plan (walkable terrace, at
+20.600, i.e. level 6's own floor) and the "mái" plan (the roof/coping at
+23.800, one storey above). Reconciling both against the floor-plan bands:

- Front SÂN THƯỢNG: y 3500–12300 (8800mm, = Ban công + P.NGỦ/P.THỜ + hall bands
  merged into one open terrace) — printed "SÂN THƯỢNG" with X-hatch (open, no roof).
- Stair + elevator bands: covered by the roof slab (the "mái" plan's technical +
  skylight zone). The stairwell's own footprint is left as a `void` in the roof
  (glazed skylight per the drawing, DEC-004). The elevator band is fully roofed,
  becoming the enclosed "Ô KỸ THUẬT THANG MÁY" plant room — printed 1950×2000mm,
  standing 2000mm above the roof slab (+23.800 → +25.800), modelled as a
  `storage` room on level 6 since the schema has no rooftop-structure construct
  (DEC-014 unchanged from rev.1).
- Rear SÂN THƯỢNG: y 18100–23800 (5700mm), printed "SÂN THƯỢNG" with X-hatch
  (open, no roof) — matches the WC+BẾP/P.NGỦ footprint below exactly.

## Tiling checks

- Plot area = 3960 × 25000 = 99,000,000 mm².
- L0: 3500(yard)+4000+4800+4000+1800+1600+4100+1200(yard) = 25000mm depth, full
  width 3960mm throughout except where explicitly split (core bands) — tiles
  exactly, no residual.
- L1: stair+elevator+hall bands (12300–18100, 5800mm) + P. SINH HOẠT
  (18100–23800, 5700mm) are the only authored rooms; y0–12300 and y23800–25000
  are deliberately untiled (void / yard), matching the drawing.
- L2–L5: 3500(void, matches L0 yard)+1400+4000+1600+1800+[core 5800]+1600+4100+1200(void)
  = 3500+1400=4900;+4000=8900;+1600=10500;+1800=12300;+4000(stair)=16300;+1800(elev)=18100;+1600=19700;+4100=23800;+1200=25000. Exact.
- L6: front terrace(8800)+core bands(5800)+rear terrace(5700)+yards(3500+1200
  matching L0's untiled bands, i.e. terrace doesn't extend into the yard
  footprint any more than the building below does) = 8800+5800+5700=20300,
  +3500+1200(untiled, unchanged)=25000. Exact.
- Core rects (stairwell, elevator) are byte-identical across levels 0–6 by
  construction (same literal x/y/w/d on every level).

## Discrepancies (all carried into `fidelity.md`)

- **Stair depth enlarged 3200 → 4000mm.** Confirmed again this pass: at
  H=3800mm, `stairs.py` needs n=22 risers, r=172.7mm (≤190 OK), g=254.6mm; a
  U-return with short=3005mm needs run ≥ 3998.5mm (S-2). The drawn 3200mm does
  not fit. The extra 800mm is taken from the rear yard (SÂN SAU, compressed
  2000→1200mm) so the plot still tiles to exactly 25000mm; this is different
  from rev.1's approach (which grew the plot depth) — the plot dimension itself
  is unchanged, only the untiled yard shrinks.
- **Elevator is inferred, not read.** See Core note above. This is the weakest
  piece of provenance in this file.
- **Ensuite WC widths (1950/2010 split) are a reasonable reconstruction**, not a
  pixel-perfect read — the printed "1950" label is a width dimension on the
  sheet; the exact depth split between WC and hall is this model's own tiling
  choice, consistent with the identical rear-WC pattern that IS fully dimensioned.
