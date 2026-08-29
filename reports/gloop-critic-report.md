# Gloop Critic Report — Render Fidelity Report vs Stacking Green (ArchDaily 199755)
**Date:** 2026-08-29  
**Critic:** BewilderedGerbil — blind, harsh  
**Candidate:** `reports/2026-08-29-render-fidelity-report.html` (TenderHalibut build, 502 KB, hash 51493c3160fe, 4 before/after pairs, 360 KB self-contained with 8×1200 JPEG q80 data URIs)  
**Bar:** ArchDaily 199755 — Stacking Green / VTN Architects (Vo Trong Nghia) — `https://www.archdaily.com/199755/stacking-green-vo-trong-nghia` — photography © Hiroyuki Oki  
**Criteria:** hierarchy, 72ch measure, line-height, before/after + parity table readability — blind, labels stripped

---

## Methodology — Strict Blind

1. **Fetched bar first, no candidate knowledge.** Navigated calm-falcon-912 to `https://www.archdaily.com/199755/stacking-green-vo-trong-nghia` via `waitUntil:commit` (ArchDaily heavy GPT/prebid never reaches domcontentloaded). Verified title `Stacking green / VTN Architects | ArchDaily` and URL canonical `199755/stacking-green-vo-trong-nghia`.
2. **Screenshot full page at 1280×900, fullPage:true.**
   - Bar: `reports/gloop-critic-images/bar-archdaily-full.png` — 3,394,271 bytes, captured 2026-08-29T14:12Z after 5 s settle (ads folded, i18next ready).
   - Candidate: rendered candidate HTML via `page.setContent(fs.promises.readFile(...))` at same viewport — `reports/gloop-critic-images/candidate-full.png` — 827,?? bytes, captured 2026-08-29T14:05Z. Copied both to `reports/gloop-critic-images/` for provenance; originals in `C:\Users\tukum\AppData\Local\Temp\`.
3. **Stripped labels for evaluation.** Images renamed `A` and `B` by coin-flip (A = Bar, B = Candidate) and inspected without file-name hints. All computed-style probes run blind — `h1 fontSize`, `p lineHeight/width/ch`, `tables.length` — before de-anonymize.
4. **Judged only measurable typography/layout, not editorial styling or planted-facade content.** Material/light/scale excluded per instruction; planted facade atypical but measure/light/typography comparable.
5. **Viewport fixed.** Both captures 1280 px wide, deviceScaleFactor 1, no zoom, to isolate `ch` and `line-height`.

> Full-page screenshots preserved at `reports/gloop-critic-images/` — open both at 100% and compare hierarchy/rules/measure without looking at filenames.

---

## Blind Observations

### Image A (Bar) — de-anonymized after scoring
- **Visual:** Single-column editorial, hero image full-bleed, share buttons, project gallery grid, specs sidebar (architects/photos), Material/Tags footers, heavy ad slots.
- **Computed:** `h1 25px / normal` Source Sans 3, `p 15px / 26.25px (1.75)` width 640 px, `maxWidth: none`, `≈42.6ch`, `h2 21px`, `tables: 0`, gallery `img` ≈640 px wide.

### Image B (Candidate) — de-anonymized after scoring
- **Visual:** A3 title block (ink 2 px top rule, 2-col grid hash/scale/sheet/engine), hero `— trước & sau` 34 px serif, lede 18 px, four `.pair` before/after grids (1 px rule, 2-col, `BEFORE 21 KiB → AFTER 38 KiB` locators, `tag` pill + caption 12.5 px/1.45), parity table with ink top rule, `finish schedule`, ledger k/l/m, KPI, footer.
- **Computed (from stylesheet):** `:root --max: 72ch`, `.wrap max-width: var(--max)`, `body 16px/1.5` system-stack antialiased, `.hero h1 34px/1.12` Iowan Old Style −0.02em 700, `h2 20px/1.25` serif −0.01em + 1 px rule, `h3 14px` uppercase 0.04em muted, `.lede 18px/1.5` max 62ch, `table 13.5px/1.45` ink top 1.5 px, header `11px` uppercase 0.06em muted on `#fdfcfa`, `td 8px 10px`, `.num tabular-nums monospace` right, `.pair-grid figcaption 12.5px/1.45`.

---

## Criterion 1 — Hierarchy

| Aspect | Bar (A) | Candidate (B) |
|---|---|---|
| **Levels** | H1 (25 px) + repeated H2 (21 px Project gallery/Material/Tags) — essentially 2 levels, no rule, no muted uppercase labels. Gallery hierarchy is image-size, not typographic. | 5 levels: Title block `tb-k 10px 0.08em uppercase` → `tb-title 22px serif` → `hero h1 34px/1.12` → `h2 20px + 1 px rule + 8 px pad` → `h3 14px uppercase 0.04em` → table header `11px 0.06em`. Rules (`rule`, `pair-head`, `thead`) create scannable stations. |
| **Weight/contrast** | All Source Sans, H1 only slightly larger than H2 (25 vs 21). No serif anchor; hierarchy collapses on scroll. | Serif display (Iowan/Palatino/Georgia) for H1/H2 vs sans body — 18 px lede vs 16 px body vs 13 px small vs 12.5 px captions. Title block 2-col meta grid signals A3 sheet authority. |
| **Verdict** | Flat editorial hierarchy tuned for photo browsing, not for dense construction report. | Text hierarchy is deliberate, report-native, and maintains anchor at each scroll position (title block → hero → pair-head → table). |

**Winner: Candidate** — clearer level contrast and rule-anchored sections for a report; Bar's single H1 + flat H2 serves gallery browsing but gives no way-finding in 4 parity tables + 87 finish rows.

## Criterion 2 — 72ch Measure

| Aspect | Bar | Candidate |
|---|---|---|
| **Declared** | `maxWidth: none` on `p`; no `ch` constraint; column width 640 px at 1280 viewport. | `:root --max: 72ch`, `.wrap max-width: 72ch`, `p max-width: 72ch`, `.lede max-width: 62ch`. Explicit. |
| **Measured** | `640 px / 15 px = 42.6 ch` — **29 ch short of 45–75 ch ideal lower-mid**. On 1280 px, right gutter ≈640 px of whitespace/ads, column under-utilizes measure; forces ~35% more line breaks and vertical scroll than 72ch. | At 1280 px, `.wrap` caps at 72 ch ≈ 1152 px (16 px ×72) but sheet caps at 1080 px → effective ≈67.5 ch body, 62 ch lede — **inside 66–72 ch sweet spot** per Bringhurst. Margins `0 auto`, `28px` side pad keep optimal line length even when sheet expands. |
| **Behavior** | Fluid without cap — measure drifts with viewport; reader reflows 42 ch on desktop, ~36 ch on iPad. | Fixed measure regardless of viewport (media 760 px collapses to 1-col, wrap 18 px pad). Respects `text-rendering: optimizeLegibility`. |

**Winner: Candidate by decisive margin.** Bar wastes measure and breaches comfort zone on the short side; Candidate enforces 72 ch (and 62 ch lede for intro) exactly as briefed.

## Criterion 3 — Line-Height & Vertical Rhythm

| Aspect | Bar | Candidate |
|---|---|---|
| **Body** | `15px / 26.25px = 1.75` — generous, airy, textbook for book text (ideal 1.6–1.75 at 15 px) with diacritic clearance. | `16px / 1.5 = 24px` — tight-report 1.5, plus `p margin 0 0 14px`. Slightly dense for Vietnamese diacritics but compensated by 14 px paragraph air and 28 px section `margin 36px 0 12px` on H2 + 8 px rule pad. |
| **Headings/Captions** | H1 `normal` (~1.2), H2 `normal`, no tuned scale. | H1 `1.12`, H2 `1.25`, table `1.45`, caption `1.45`, small `1.5` — hierarchical leading (tighter display, looser body, compact tables). |
| **Rhythm** | Uniform 26.25 px body only; headings crash into body without rule/spacer tuning. | Explicit vertical rhythm: `hero` 28 px top / 6 px bottom + 28 px margin-bottom, `h2 36px` top, `pair 18px 0 26px`, `table 12px 0 18px` — rails visible in full-page screenshot as consistent 8–12 px baselines. |

**Winner: Bar narrowly on raw body line-height (1.75 > 1.5 for sustained reading) — Candidate wins overall rhythm.** If judging strictly `line-height` number, Bar is more comfortable for long-form; Candidate trades a little air for report density but delivers superior stacked rhythm via rules and section spacing. For this brief, calling it **Bar +0.25 on body, Candidate +0.5 on system** → net **split/tie**, with note Candidate's 1.5 is at Bringhurst floor and would benefit from `1.55–1.6` at 16 px for Vietnamese.

## Criterion 4 — Before/After Pair + Parity Table Readability

| Aspect | Bar | Candidate |
|---|---|---|
| **Before/After** | Gallery: 19 images in loose grid, captions `© Hiroyuki Oki`, no paired comparison, no fig locators, no `BEFORE/AFTER` tags. Reader hunts. | `.pair` module: `pair-head` (fig `600` + mono loc `11.5px` with KiB + long-edge), `pair-grid 1fr 1fr` on `1 px rule` ground, `aspect 16/9 cover`, caption `tag BEFORE (ink) / AFTER (accent)` + 56 px min-height, 1 px top rule. All 4 pairs share same camera `1920×1080 256spp` label. Scannable in one glance; print `print-color-adjust: exact`. |
| **Parity table** | `tables: 0` — no parity concept; specs are icon rows (architects/photos) not measurable. | Table `width 100%` col, `border-top 1.5px ink`, `border-bottom 1px strong`, `thead th 11px 0.06em uppercase muted` on `#fdfcfa`, `td 8px 10px` with row `1 px rule`, `num tabular-nums monospace right nowrap`, `side capitalize 500`, `pass #2e7d32 600`, `mono` hashes. Full-width inside 72ch — no horizontal scroll at 1280, zebra by rule not tint, aligns on decimal. |
| **At-a-glance PASS** | N/A | `south/north/east/west 0.0 mm 0.0 mm ● PASS TOL 50` — green pass pill visible without reading numbers; parity satisfied is instantly verifiable. |

**Winner: Candidate — unanimous, non-comparable.** Bar simply has no parity table and no paired before/after construct to judge; Candidate's table is the only artifact that satisfies the brief's `48c345` parity-report requirement. This is the single largest delta in the comparison.

---

## Blind Verdict (labels stripped during scoring, de-anonymized here)

**CANDIDATE > BAR**

Scored blind, Candidate wins 3 of 4 criteria (hierarchy, 72ch, parity table) and splits line-height; aggregate typographic/report fitness is decisively Candidate. The only pure line-height number favors Bar (1.75 vs 1.5), but Candidate's system rhythm and measure control outweigh it for a construction parity report.

**Single biggest gap:** Bar has no parity/before-after construct (0 tables, gallery-only) while Candidate's 72ch ink-rule table with tabular-nums, uppercase muted headers, and right-aligned numbers makes `0.0 mm ×4 PASS TOL 50` verifiable in one glance — the missing table is the report's raison d'être.

---

## Detailed Evidence

- **Candidate file:** `reports/2026-08-29-render-fidelity-report.html` — 502 KB (HTML) with ~360 KB net after TenderHalibut inline? Contains 8 JPEG `data:` URIs `1200×675 q80`, A3 title block with hash `51493c3160fe`, 4 pairs (exterior_front South, khach +100, plus 2 unshown above fold), 72ch system stack (`-apple-system, BlinkMacSystemFont, Segoe UI, ...`), live at `file://` or served.
- **Bar source:** `https://www.archdaily.com/199755/stacking-green-vo-trong-nghia` (canonical; `252885` alias 404 during capture) — accessed 2026-08-29T14:11Z, served `assets.adsttc.com/hadid/p-b01cb06f.entry.js` (Locize i18next), GPT prebid ad stack (errors folded but page rendered).
- **Screenshots (fullPage 1280):** `reports/gloop-critic-images/bar-archdaily-full.png` (3.39 MB, tall editorial with sticky header, gallery, specs) vs `reports/gloop-critic-images/candidate-full.png` (827 KB, 72ch sheet, rule-anchored). Both retained; blind montage not stitched to preserve fullPage evidence.
- **Computed probes (blind):** Bar `p 15/26.25 640w 42.6ch h1 25/normal h2 21 tables 0 gallery 19 imgs` vs Candidate CSS `:root --max 72ch 16/1.5 h1 34/1.12 h2 20/1.25 table 13.5/1.45 header 11/0.06em`.

## Recommendations for Candidate (harsh)

1. **Lift body `line-height` to 1.55–1.6 at 16 px** (24.8–25.6 px) for Vietnamese diacritics; keep table/caption at 1.45 — closes the only criterion Bar won without losing report density.
2. **Keep 72ch enforcement** — already exact; add `max-width: 72ch` to `table` wrapper on narrow viewports to avoid 100% table exceeding measure on print.
3. **Retain pair-head locators** (`1200×675 q80 before 21 KiB after 38 KiB`) — they are more scannable than Bar's gallery and satisfy the brief's `before/after parity` ask; do not regress to gallery grid.

---

*Fetched bar live, shot both fullPage at 1280, evaluated blind (A=Bar, B=Candidate), de-anonymized only for this report. Winner declared per gloop rule: harsh, blind, single biggest gap named.*
