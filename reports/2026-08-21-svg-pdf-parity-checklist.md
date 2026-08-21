# SVG ↔ contractor-PDF parity checklist (bar C: full drawing-set parity)

Reference: the five vector PDFs in `contractor/` (rasterized to
`output/contractor_pdf_png/` at 4×). Candidate: `output/svg/contractor-as-drawn_*.svg`
(rendered to `output/svg_png/`). Truth source for dimensions:
`designs/contractor-as-drawn.measurements.md` rev.2.

A sheet passes when every checkable row below is present and matching in the
generated SVG for that sheet. One mismatch = fail.

## Conventions on every plan sheet

| # | item | drawing shows | candidate status |
|---|---|---|---|
| C1 | orientation | rear (`SÂN SAU`) at TOP, street at BOTTOM | FAIL — flipped |
| C2 | stair tread numbers | odd only: 1,3,5,7,9 up-flight; 21,19,17,15,13 return | FAIL — 1..22 all |
| C3 | per-room level markers | `±0.000`, `+0.100`, `+0.300`, `+0.200`, `-0.450` … one per room/zone | FAIL — one per storey |
| C4 | setback lines | dash-dot `Ranh khoảng lùi trước` + `Ranh khoảng lùi sau` across plot | FAIL — absent |
| C5 | plot boundary | dash-dot `Ranh lộ giới` at street edge | PASS |
| C6 | section markers | `A-A` circle bubbles both ends of cut line | FAIL — raw names `long`/`cross_bed` |
| C7 | title block scale note | `TL : 1/100` | DELIBERATE DEVIATION — honest graphic-bar note kept (PHASE-05 decision); do not print a false scale |
| C8 | width dim | printed `3950` | DELIBERATE DEVIATION — model is 3960 (DEC-005 orthogonal collapse) |
| C9 | dimension chains | multi-tier, values per measurements.md | PASS (values from orthogonal model; taper segments not printable) |

## Sheet-by-sheet content

### MB 1-LUNG → f0 (Tầng 1) + f1 (Lửng)

| # | item | f0 | f1 |
|---|---|---|---|
| S1 | room labels: NƠI ĐỂ XE, P.KHÁCH, WC, P. ĂN + BẾP, SÂN TRƯỚC, SÂN SAU | FAIL — `BẾP & ĂN` should read `P. ĂN + BẾP` | n/a |
| S2 | lửng labels: P.SINH HOẠT + void zones repeat room-below names (P.KHÁCH, NƠI ĐỂ XE, SÂN TRƯỚC) over X-hatch | n/a | FAIL — prints `Ô THÔNG TẦNG…` instead of room-below names |
| S3 | callout `Tiểu cảnh, ô lấy sáng` dashed box in P.KHÁCH zone | FAIL | FAIL |
| S4 | callout `Lô gia` beside rear WC zone | n/a | FAIL |
| S5 | elevator band: unlabelled walled void w/ X-hatch box | FAIL — labelled THANG MÁY/HÀNH LANG (ledgered inference (c), keep but hatch) | same |
| S6 | furniture: dining set, kitchen counter+sink, sofa group, WC fixtures | PARTIAL | n/a |
| S7 | level markers ±0.000/+0.100/+0.300/+0.200/-0.450 | FAIL (C3) | FAIL (+3.800) |

### MB 2-3-4 → f2/f3/f4

| # | item | status |
|---|---|---|
| B1 | bedroom label `P.NGỦ` (both) — not `P.NGỦ CHÍNH` | FAIL |
| B2 | callout `Ô lấy sáng` + `2200` between stair and front ensuite | FAIL |
| B3 | callout `Lô gia` beside rear WC | FAIL |
| B4 | ensuite WC fixtures drawn | PARTIAL |
| B5 | balcony laundry icons at Ban công | FAIL |
| B6 | chains incl. 1400 balcony, 1950 ensuite width | PASS |

### MB 5-MAI → f5 (Tầng 5) + f6 (Sân thượng)

| # | item | status |
|---|---|---|
| M1 | P.THỜ with altar counter; no ensuite front WC | PASS (label ok; altar counter = furniture) |
| M2 | `Ô lấy sáng` callout | FAIL |
| M3 | `Lô gia` callout | FAIL |
| M4 | roof terrace: two open SÂN THƯỢNG + core; doors from terraces to stair hall | PARTIAL |
| M5 | tread numbering odd-only | FAIL (C2) |

### MB MAI-MD → mái plan (no direct counterpart; f6 is sân thượng) + MẶT ĐỨNG CHÍNH → elev_south

| # | item | status |
|---|---|---|
| R1 | roof plan features (Ô kỹ thuật thang máy, Ô kính lấy sáng, gutters) | OUT OF SCOPE this pass — schema has no second-roof level; ledgered |
| E1 | elevation level tags ±0.000…+25.800 | verify |
| E2 | storey height chain 3800/3200/3400×4/3200/2000, overall 23800 | verify |

### MC A-A → section_long

| # | item | status |
|---|---|---|
| A1 | all-level room labels along cut | verify |
| A2 | level tags ±0.000…+25.800 + chain 3800/3200/3400×4/3200/2000 + 23800 | verify |
| A3 | stair flights drawn per level | verify |

## Accepted deviations (ledgered, do not "fix")

- Orthogonal plot vs ~7.2° skew (DEC-005): taper chain segments (2500/2300/500,
  200) and 3950-vs-3960 are not reproducible.
- Elevator shaft inference (fidelity (c)): labels stay, but band gets the
  drawing's X-hatch treatment.
- Stair depth 4000 vs drawn 3200 (fidelity (g)).
- Title-block scale honesty (C7).
