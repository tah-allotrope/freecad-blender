# contractor-as-drawn — measurement record

Traceable table of every dimension behind `designs/contractor-as-drawn.json`,
sourced from the five vector PDFs under `contractor/` as read for
`reports/2026-08-12-contractor-drawing-set-review.html`. All units are integer
millimetres.

## Provenance note (read honestly)

The five sheets carry **no extractable text** (each returns `get_text()` length 0;
the labels and dimension figures are outlined glyphs). This execution environment
has **no image-input capability**, so the printed glyphs could not be re-read
visually in this pass. The figures below therefore come from two already-verified
sources, cross-checked against one another:

1. **`reports/2026-08-12-contractor-drawing-set-review.html`** — a measured review
   of the same sheets, calibrated two independent ways (plot width 3950 mm ≈ 91.8 pt
   and building depth 20 900 mm ≈ 485.6 pt, both → **K = 43.0 mm/pt**).
2. The binding defaults in `plans/2026-08-13-contractor-scheme-3d-render-plan.md`
   (ASM-002…ASM-008), themselves derived from the same review.

Rows marked **`(measured)`** are review-measured facts; rows marked
**`(inferred)`** are this plan's subdivision of the measured envelope into rooms,
derived from the review's programme description rather than read off a sheet. This
split is deliberate and is the point of the `fidelity.md` ledger alongside.

## Coordinate convention (ASM-001)

- `x = 0` west party wall, `x = plot_width_mm` east party wall.
- `y = 0` street (front), `y` increasing toward the rear.
- Plot is the orthogonal collapse of the drawn ~7.2°-skewed rectangle.

## Plot (ASM-002)

| field | value | source |
|---|---|---|
| `plot_width_mm` | 3960 | frontage measured 3950–3960 (tapering); orthogonal collapse |
| `plot_depth_mm` | 25000 | head of drawn chain 25000 / 22500 / 19500 |
| front yard | 3000 | y 0…3000 (drawn 3000 → 2500 taper, DEC-005) |
| building envelope | 20000 | y 3000…23000 |
| rear yard | 2000 | y 23000…25000 (drawn 2500 → 2000 taper) |

## Storey heights (from Section A-A level tags)

| level | name | height_mm | from tags |
|---|---|---|---|
| 0 | Trệt | 3800 | ±0.000 → +3.800 |
| 1 | Lửng | 3200 | +3.800 → +7.000 |
| 2 | Tầng 2 | 3400 | +7.000 → +10.400 |
| 3 | Tầng 3 | 3400 | +10.400 → +13.800 |
| 4 | Tầng 4 | 3400 | +13.800 → +17.200 |
| 5 | Tầng 5 | 3400 | +17.200 → +20.600 |
| 6 | Sân thượng | 3200 | +20.600 → +23.800 |

**Sum = 23 800 mm = +23.800** (the roof slab). The plant room rises a further
2000 mm to **+25.800**; it is a rooftop structure, not a storey (ASM-003/ASM-004),
and is modelled as a `storage` room on level 6.

## Core (byte-identical on all seven levels)

| room | id | x | y | w | d | source |
|---|---|---|---|---|---|---|
| stairwell | `stairwell` | 0 | 6000 | 3005 | 4000 | flight 2×1154 + well 697 = 3005 `(measured)`; depth **4000** is the S-2 minimum for a U-return at H=3800, enlarged from the drawn 3200 `(RISK-02-01)` |
| hall | `hall` | 3005 | 6000 | 955 | 4000 | `(inferred)` circulation beside stair |
| elevator | `elevator` | 0 | 10000 | 1500 | 1600 | `(measured)` ~1500 × 1600 |
| hall (rear) | `hall_rear` | 1500 | 10000 | 1300 | 1600 | `(inferred)` circulation beside lift |
| light well | — (void) | 2800 | 10000 | 1160 | 1600 | drawn 2200 × 1300 `(measured)`; modelled 1160 × 1600 to tile the 1600-deep lift band `(ledger)` |

The light well is **not authored** — its footprint is left untiled on every level
(DEC-003) and punched as a roof `void` (DEC-004).

## Rooms per level (all full-width 3960 unless noted)

Front zone y 3000…6000 (3000 deep); rear zone y 11600…23000 (11 400 deep), split as
`[light-well room 6800] + [wc/kho strip 1800] + [rear room 2800]`.

| level | id | name | x | y | w | d | type | source |
|---|---|---|---|---|---|---|---|---|
| 0 | `gara` | NƠI ĐỂ XE | 0 | 3000 | 3960 | 3000 | garage | programme `(measured)` |
| 0 | `khach` | P.KHÁCH | 0 | 11600 | 3960 | 6800 | living | programme `(measured)` |
| 0 | `wc_gf` | WC | 0 | 18400 | 2000 | 1800 | bathroom | `(inferred)` |
| 0 | `kho_gf` | KHO | 2000 | 18400 | 1960 | 1800 | storage | `(inferred)` |
| 0 | `bep_an` | BẾP & ĂN | 0 | 20200 | 3960 | 2800 | kitchen | programme `(measured)` |
| 1 | `sinh_hoat` | P.SINH HOẠT | 0 | 3000 | 3960 | 3000 | living | lửng family room `(measured)` |
| 1 | `sinh_hoat_rear` | P.SINH HOẠT | 0 | 11600 | 3960 | 6800 | living | `(inferred)` |
| 1 | `wc_lung` / `kho_lung` | WC / KHO | — | 18400 | — | 1800 | bathroom / storage | `(inferred)` |
| 1 | `ngu_lung` | P.NGỦ | 0 | 20200 | 3960 | 2800 | bedroom | `(inferred)` |
| 2–4 | `ngu_chinh_f{n}` | P.NGỦ CHÍNH | 0 | 3000 | 3960 | 3000 | bedroom | tầng 2–5 bedrooms `(measured)` |
| 2–4 | `ngu_2_f{n}` | P.NGỦ 2 | 0 | 11600 | 3960 | 6800 | bedroom | `(inferred)` |
| 2–4 | `wc_f{n}` / `kho_f{n}` | WC / KHO | — | 18400 | — | 1800 | bathroom / storage | `(inferred)` |
| 2–4 | `ngu_3_f{n}` | P.NGỦ 3 | 0 | 20200 | 3960 | 2800 | bedroom | `(inferred)` |
| 5 | `tho_f5` | P.THỜ | 0 | 3000 | 3960 | 3000 | living | P.THỜ on tầng 5 `(measured)` |
| 5 | `ngu_2_f5` / `ngu_3_f5` | P.NGỦ 2 / 3 | — | 11600 / 20200 | 3960 | 6800 / 2800 | bedroom | `(inferred)` |
| 6 | `san_thuong` | SÂN THƯỢNG | 0 | 3000 | 3960 | 3000 | balcony | `(measured)` |
| 6 | `oki_thuat` | Ô KỸ THUẬT THANG MÁY | 0 | 11600 | 2000 | 1900 | storage | 2000 × 1900 plant room `(measured)` |
| 6 | `san_thuong_mid` / `san_thuong_rear` | SÂN THƯỢNG | — | 11600 / 13500 | — | — | balcony | `(inferred)` |

## Tiling checks

- Plot area = 3960 × 25000 = 99 000 000 mm².
- Per level, rooms + light well tile the full building envelope (y 3000…23000):
  front 3000 + core 5600 + rear 11400 = 20 000, all × 3960, minus the
  1160 × 1600 light well. Every level sums exactly — no residual, no sliver
  (ASM-006 never had to absorb a residual).
- Core rects are byte-identical across levels 0–6 (`shaft_misaligned` absent).

## Discrepancies

- **Storey-height sum.** The plan's PHASE-01 test text says "sum → +25.800", but the
  2000 mm above +23.800 is the plant room, not a storey. The seven storeys sum to
  +23.800; the plant room is modelled as a level-6 `storage` room. Recorded rather
  than treated as an error.
- **Light well size.** Drawn 2200 × 1300 (2.86 m²) → modelled 1160 × 1600 (1.86 m²)
  so it tiles the 1600-deep lift band. See `fidelity.md`.
- **Stair depth.** Drawn 3200 → modelled 4000 (S-2 U-return minimum at H=3800).
  See `fidelity.md` (RISK-02-01).
- **Skewed boundaries.** Both ~7.2° boundaries collapse to the orthogonal plot
  rectangle; the tapering yards become untiled plot (DEC-005).
