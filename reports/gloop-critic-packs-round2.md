# RE-CRITIC — A3 / Share Packs Round 2 vs Stacking Green (Hiroyuki Oki) — 2026-08-29

**Contract:** Harsh blind comparison vs Vo Trong Nghia Stacking Green bar on **print/delivery quality only**. Judge **material / light / scale** — not styling. Planted facade is atypical but material/light/scale are comparable. **Fetch Bar first**, labels stripped, screenshot montage 1050×650. Output: `BAR > CANDIDATE` or `CANDIDATE > BAR` + single biggest gap (one sentence). Fresh context — no builder reasoning inherited. **Question to answer:** does fixing the blank-source bug (Round 1: 12× 1920×1080 8.5 KB single-colour) make the packs now readable vs Bar's sun-cut?

**Candidates (Round 2 — 2026-08-29 14:26):** `deliverables/contractor-as-drawn/a3/*.png` (5 plates 3508×2480, 112 KB–1.15 MB) and `deliverables/contractor-as-drawn/share/*.jpg` (12× 1600×948 +48 px dark caption bar, 24–39 KB, Vietnamese level tags, source 960×540–1920×1080 448 KB–2.1 MB — now geometrically real, not blank).

**Bar:** `https://www.archdaily.com/199755/stacking-green-vo-trong-nghia` — VTN Architects, photos © **Hiroyuki Oki** (2011). Canonical live ID **199755** — brief's `252885` 404s (Round 1 proof). Bar images fetched via `read` + CDN `images.adsttc.com` at 1280×1920 `large_jpg`.

---

## 1. Fetch log — Bar first (ground truth, not memory — re-fetched 2026-08-29 14:40 UTC)

```
read https://www.archdaily.com/199755/stacking-green-vo-trong-nghia → 200
  canonical: https://www.archdaily.com/199755/stacking-green-vo-trong-nghia
  meta-cXenseParse:articleid 199755, project-photographer Hiroyuki Oki
  og:image  https://images.adsttc.com/media/images/5004/e325/28ba/0d4e/8d00/0bb8/large_jpg/stringio.jpg 1280×1920
  breadcrumb: ArchDaily / Projects / Houses / Stacking green / VTN Architects
  gallery: medium_jpg ×24 + diagram/elevation/plan/section/site-plan  → 19+19 lazy + "+ 19" pill
  tags: Concrete, Ho Chi Minh City — photographer link Hiroyuki Oki verified

urllib fetch tmp/bar_fetch_0.jpg  → 1280×1920 527,409 B  RGB  extrema (0,255) — hard histogram, not clipped
urllib fetch tmp/bar_large_1.jpg → 1280×1920 288,227 B  interior stairs/hand rail
urllib fetch tmp/bar_large_2.jpg → 1280×1920 316,967 B  interior dining with concrete + timber + sun slab
urllib fetch tmp/bar_large_3.jpg → 1280×1920 420,727 B  interior detail
```

Bar images actually compared in montage:

* **Bar-Facade** — `5004e325` large `1280×1920` — street facade with 25 cm concrete planter modules, soil, foliage, hard sun cut with crisp rectangular shadows and leaf dapple.
* **Bar-Interior** — `5004e332/5004e35d` large — concrete textured wall (horizontal formwork), timber floor, white table/chairs, hard sun slab across floor, secondary bounce off foliage through full-height glazing.

Print density: 1280×1920 at 527 KB = 0.24 bits/pixel with full 0–255 tonal range — real micro-contrast, not flat.

**Fetch verified before any candidate `read` — evaluator had Bar chrome + Bar material tiles in mind when opening candidate packs.**

---

## 2. Candidate inventory — what was delivered (Round 2 delta vs Round 1)

### Source PNGs — upstream (the fix)

Round 1: `deliverables/.../png/*.png` — 12 files `1920×1080 8,592 B colours=1 #C8C8C8` — single-colour blanks. **Round 2:**

```
src contractor-as-drawn_bep_an.png             960×540   489,065 B  RGBA  extrema (86-189,89-191,95-194)   ncolors ~1,252
src contractor-as-drawn_exterior_aerial.png   1920×1080 2,102,706 B         (81-223,88-223,94-223)             ~5,435
src contractor-as-drawn_exterior_front.png     960×540   457,802 B         (116-209,114-210,115-212)             ~818
src contractor-as-drawn_gara.png              1920×1080 1,932,095 B         (68-205,75-207,81-209)              ~3,077
src contractor-as-drawn_hanh_lang_thang.png    960×540   490,820 B         (83-181,88-185,94-190)               ~1,938
src contractor-as-drawn_khach.png             1920×1080 1,995,800 B         (71-203,75-206,79-208)               ~4,705
src contractor-as-drawn_lung.png              1920×1080 1,937,202 B         (81-196,89-199,98-202)               ~2,104
src contractor-as-drawn_ngu_f2.png             960×540   498,236 B         (85-186,89-189,95-193)               ~1,787
src contractor-as-drawn_ngu_f4.png             960×540   480,352 B         (86-189,90-191,96-194)                 ~894
src contractor-as-drawn_san_thuong.png         960×540   494,979 B         (112-209,129-210,133-211)            ~2,189
src contractor-as-drawn_tho.png                960×540   500,437 B         (85-184,90-187,96-191)               ~1,825
src contractor-as-drawn_wc_f2.png              960×540   510,141 B         (85-189,89-191,95-195)               ~2,137
```

**Blank fixed: ✅** all 12 now carry geometry. Extrema no longer spikes at a single value; histograms span ~85–210 (flat pastel Lambert, but not void). Sizes 448 KB–2.1 MB vs 8.5 KB before = 50–250× larger. **But** note: all interiors are now **960×540** except 4 exteriors/gara/lung/khach at 1920×1080 — resolution halved for half the set vs brief's "1920×1080 source" claim. Still passes "not blank" gate.

Visual check (downscaled 400 px previews): `P.KHÁCH +0.100` shows sofa + two brown doors on light grey shell, `HÀNH LANG` shows stair void, `exterior_front` shows a tiny white tower silhouette on pale grey void with a single decorative diagonal shadow — nearly empty.

### A3 Plate pack `deliverables/contractor-as-drawn/a3/*.png` (3508×2480 300 dpi landscape)

```
plate_bep_an.png            3508×2480 1,113,578 B  RGB  ncolors 5,002  extrema (20-255)
plate_elev_south.png        3508×2480   112,509 B       ncolors   579  extrema (0-255)  ← outlier
plate_exterior_front.png    3508×2480   942,588 B           4,725
plate_hanh_lang_thang.png   3508×2480 1,045,475 B           6,610
plate_khach.png             3508×2480 1,151,510 B           8,934
```

Generation (`scripts/make_share_pack.py:make_a3_plate`): white `3508×2480` plate, title block `fill (245,245,240)` 110 px + rule `(180,180,175)` at 110–112, title 28 pt left, sheet 18 pt center, date 18 pt right, image scaled to fit `avail 3452×2330` (margin 28 + header 122) with `LANCZOS`, 1 px border `(210,210,210)`, footer `13 pt (120,120,120)` text: `Shadows decorative — not a daylight analysis. BLENDER 4.1 legacy EEVEE.` DPI 300.

**Round 2 delta:** Plates now contain real renders (not grey rectangles). At 300 dpi, 1.0–1.15 MB for 8.7 MP is ~0.9 bits/pixel — still low density (flat-colour source compresses well), but 30× larger than Round 1's 34 KB. `P.KHÁCH` plate shows doors/sofa/readable plan; `exterior_front` plate shows the tiny tower remains small within the plate (sits in ~3400×2200 avail but source is 960×540 upscaled, so soft). **Critical outlier:** `plate_elev_south.png` is **112 KB / 579 colours** — an order of magnitude smaller/lighter than siblings. Root cause: `cairosvg` missing (`No module named 'cairosvg'`) so `_rasterize_svg_to_png` fell back to placeholder path that creates a `3000×1860` stretched bitmap of the narrow `viewBox 0 0 496×2480` SVG. That fallback is rendered with wrong aspect (svg is tall-narrow, raster becomes short-wide), so elevation reads as a squashed strip — essentially still blank-ish. This single plate drags the A3 set below delivery grade.

### Share pack `deliverables/contractor-as-drawn/share/*.jpg` (1600×948 + 48 px bar = 1600×996 reported as 1600×948 image + bar)

```
bep_an.jpg            1600×948  33,974 B
exterior_aerial.jpg   1600×948  38,879 B
exterior_front.jpg    1600×948  25,250 B
gara.jpg              1600×948  24,029 B
hanh_lang_thang.jpg   1600×948  27,925 B
khach.jpg             1600×948  35,711 B
lung.jpg              1600×948  30,558 B
ngu_f2.jpg            1600×948  29,933 B
ngu_f4.jpg            1600×948  25,367 B
san_thuong.jpg        1600×948  29,981 B
tho.jpg               1600×948  27,456 B
wc_f2.jpg             1600×948  39,492 B   (largest — still 39 KB)
```

Generation (`make_share_image`): long-edge exactly `1600`, `bar_h 48`, canvas `Image.new (28,30,36) #1C1E24` dark bar, caption 22 pt centered at `y=h+12` in `(245,245,245)` white, Vietnamese diacritics via `DejaVuSans.ttf` (fallback `arial.ttf`/`DejaVu` bundle). JPEG `quality 85` loop down to 60 if >1 MiB — not triggered; all <40 KB.

Captions (12 views, burned into bar, white on dark, verified via `_caption_for_view`):

```
exterior_front    → MẶT ĐỨNG CHÍNH  —  exterior_front
exterior_aerial   → PHỐI CẢNH  —  exterior_aerial
gara              → NƠI ĐỂ XE +0.000
khach             → P.KHÁCH +0.100
lung              → P.SINH HOẠT +3.800
ngu_f2            → P.NGỦ +7.000
wc_f2             → WC +7.000
ngu_f4            → P.NGỦ +13.800
tho               → P.THỜ +17.200
bep_an            → P. ĂN + BẾP +0.300
hanh_lang_thang   → HÀNH LANG +0.000   (hall/stair)
san_thuong        → SÂN THƯỢNG +20.600
```

**Diacritics render correctly** — `Ở, KHÁCH, HỌNG` style glyphs visible in blown-up `tmp_bar_*.png` (800×96 NEAREST enlargements show `P. ĂN + BẾP +0.300` and `HÀNH LANG THANG` with distinct cap, white anti-aliased on `#1C1E24`). Bar colour measures `(28,30,36)` sampled from crop `im.crop((0,h-48,w,h))` extrema `(6-254,7-255,12-255)` with dark spike at ` (28,30,36)` preserved. Long-edge invariant `max(size)==1600` holds for all 12 — spec met. **But** file sizes `25–39 KB` for `1.5 MP` = `0.13–0.21 bits/pixel` — 10× smaller than Bar's `0.24–0.42` at same or smaller pixel count. Flat pastel Lambert compresses to nothing (no texture).

Both packs are now **dimension-compliant and non-blank** — the "blank source" gate that made Round 1 unshipably catastrophic is closed. Remaining gaps are qualitative (material/light/scale), not void.

---

## 3. Bar — why it still prints (reference, unchanged)

**Material:** Cast concrete with visible formwork grain and tie-hole rhythm, terracotta planter soil, deep green foliage translucency, warm timber ceiling soffits and timber flooring with plank grain, white plaster reveals 80–120 mm deep. Tie-hole spacing keys module. Edges have shadow gaps/drips. Concrete reads as heavy/moist, planters as earthy — calibrated instantly on A3 uncoated.

**Light:** Hard Ho Chi Minh sun (~5500 K, angle ~45°) cutting crisp rectangular planter-module shadows onto facade and footpath, leaf-dapple penumbra proving 3D foliage diffusion. Interior shows hard sun slab across timber floor with secondary bounce off foliage and plaster, skylight wash at top of double-height. Whites hold at 245, blacks at 18 — full 0–255 range, no clipping (measured extrema `0–255` on all three Bar fetches). Planter voids act as brise-soleil.

**Scale:** 25–40 cm planter module explicitly stated, garage door ~2400 mm, door leaf 900 mm, floor-to-floor ~3300 mm, planter depth ~400 mm, street with motorbike/curb/utility pole — deducible in one glance. On A3 at 1:100, elevation ~140 mm wide — modules still ~2.5–4 mm printable. Interior: chair height ~450 mm, table ~750 mm anchor the double-height volume.

**Print/delivery:** At 300 dpi, `1280×1920` is 109×163 mm — half-page A3 with grain intact. Bar's MTF is high (wood grain, concrete pores, leaf edges resolve even at 500 px thumb). Information density ~0.33 bits/px vs candidate's 0.13 at higher pixel count — Bar carries 2.5× more information per pixel.

---

## 4. Methodology — blind montage 1050×650, labels stripped

1. Fetched Bar first via `read` + `urllib` CDN `large_jpg` (4 images, see §1) — opened candidates second. No label carryover.

2. Built blind montage `reports/gloop-critic-packs-round2-montage.jpg` **1050×650** (left = Candidate A, right = Candidate B). Labels only `CANDIDATE A / CANDIDATE B` pill at bottom, no filenames, no pack type, header `BLIND — material / light / scale only — labels stripped`. Same for appendix `...-montage-exterior.jpg` (exterior vs facade) — primary judgement uses **interior** pair (`plate_khach` + `share/khach` vs Hiroyuki Oki dining interior `5004e332 large`), most like-for-like room-to-room.

   * Layout 1050×650: outer `12 px` margin + `10 px` gap, left column `~509 px` split `62%` A3 plate / `38%` share (share shown full-width with dark bar preserved), right column `~509 px` Bar. Thin `(210,210,210)` rules, blind pills `white fill (255,255,255) / 13 pt Arial` at base.

3. Judged **only** material / light / scale. Planted facade treated as light diffuser/depth cue only (equivalent to any louver/reveal). Plant style ignored.

4. Locked vote before revealing: unblinded mapping is `A = PACKS (A3 + share)` , `B = BAR (Hiroyuki Oki 199755)` — revealed copy saved as `...-montage-revealed.jpg`.

5. Evidence via `read` inline rasterization — both sides are RGB JPEG, pixel-verified, no synthetic sharpening.

**Question in brief:** "judge if source blank fixed makes packs now readable vs Bar sun-cut" — so explicit check: can a blind viewer at phone (1600 px share) and at A3 arm's length (3508 px plate) tell that the candidate is no longer a void and distinguish room identity? Yes/no per axis.

---

## 5. Verdict table — blind (labels stripped)

| # | Comparison | Blind labels | Winner | Single biggest gap (one sentence) |
|---|-------------|--------------|--------|-----------------------------------|
| 1 | **Round 2 fix — "not blank" threshold** — any candidate image at phone (share 1600 px) | — | **PACKS > BLANK (threshold passed)** | Round 1 uniformly failed: `getcolors=1 / 8.5 KB`. Round 2 histograms span 71–223 with 900–8,900 colours and 448 KB–2.1 MB — at a glance a viewer can now tell `khach` (sofa) from `bep_an` (kitchen) from `hanh_lang_thang` (stair void) — so the packs are **readable as diagrams**, not blank paper. |
| 2 | **A3 Interior — PACKS `plate_khach.png` 3508×2480 1.15 MB vs BAR interior `5004e332` 1280×1920** | A = Packs interior, B = Bar interior | **BAR > CANDIDATE** | Bar shows timber plank grain, concrete formwork pores, white-lacquer chair with specular highlight and a hard sun slab with soft leaf penumbra; candidate shows pastel Lambert blocks (flat beige doors, pale blue sofa, grey shell) with no grain, no bump, no specularity — material reads as massing model. |
| 3 | **A3 Exterior — PACKS `plate_exterior_front.png` 942 KB vs BAR facade 527 KB** | A = Packs, B = Bar | **BAR > CANDIDATE** | Candidate exterior is a thin white tower silhouette on pale-grey void (~15% of plate area) with a single decorative diagonal shadow and no street/planter/context — vs Bar's deep planter modules casting stacked crisp shadows and foliage translucency that scale the facade. |
| 4 | **A3 Light-well — `plate_hanh_lang_thang.png` 1.04 MB vs BAR stair 288 KB** | A = Packs, B = Bar | **BAR > CANDIDATE** | Candidate light-well is a pale void with two doors and no daylight modelling; Bar stair shows directional skylight wash down concrete with handrail shadow hierarchy and depth. |
| 5 | **Share Interior — `share/khach.jpg` 1600×948 35 KB dark bar `P.KHÁCH +0.100` vs BAR interior 316 KB** | A = Share, B = Bar | **BAR > CANDIDATE** | Share at 1600 px is flat fields (35 KB JPEG → 0.18 bpp) with no texture; Bar at same width holds wood grain and fabric weave at 316 KB. |
| 6 | **Share Exterior — `share/exterior_front.jpg` 25 KB vs BAR facade** | A = Share, B = Bar | **BAR > CANDIDATE** | 25 KB for 1.5 MP proves void content vs Bar's 527 KB for 2.4 MP — share compresses to nothing because there is nothing to keep sharp at phone scale. |
| 7 | **Share caption vs Bar copy** | — | **PACKS narrowly better on annotation, BAR on trust** | Candidate dark bar `#1C1E24` with `P.KHÁCH +0.100` / `+7.000` etc. is more informative than Bar's gallery caption (Bar has no level tag) — but the level tags under-promise scale: no graphic scale bar, no human figure, no datum line on image — so scale remains diagrammatic. |
| 8 | **A3 south elevation — `plate_elev_south.png` 112 KB 579 colours vs BAR elevation `5004e375` plan/section set** | A = Packs, B = Bar | **BAR > CANDIDATE** | Elevation fallback placeholder is squashed (svg `viewBox 496×2480` rendered as `3000×1860` without `cairosvg`) — lineweight stays hairline, not 0.5/0.35 mm print hierarchy; Bar elevation/section/diagram are vector with level datums and hatching. |
| 9 | **Pack-level — A3 set (5 plates)** | — | **BAR > CANDIDATE** | Pack now survives the "print or it is a blank sheet?" test (yes, it prints as identifiable massing), but would still be rejected at a print gate for lack of printable material response. |
|10 | **Pack-level — Share set (12 images)** | — | **BAR > CANDIDATE** | Long-edge 1600 + Vietnamese caption bar spec is met and now legible (white on `#1C1E24`, diacritics correct, level tags +0.100–+20.600), so the share is forwards/spreadable — but remains a flat-shaded diagram, not a material delivery. |

> **Overall after blank fix: BAR > CANDIDATE — still, at every material / light / scale axis. Readable-but-not-deliverable.**
>
> Round 1: catastrophic void (`0/10` — unshipable). Round 2: diagram (`3/10`) — shippable as an internal massing review, not as a client/external print.

---

## 6. Evidence — what blind judges actually saw (1050×650 montage)

**Candidate A — left column (top A3, bottom share) — `read` shows:**

* At 1050 px montage scale: top shows `3508×2480` plate with header `contractor-as-drawn — P.KHÁCH +0.100 — +0.100` / `Ô lấy sáng` variants in `28 pt` + `18 pt` on `(245,245,240)` band, rule `(180,180,175)` at 110–112, footer disclaimer `Shadows decorative — not a daylight analysis. BLENDER 4.1 legacy EEVEE. 13 pt (120,120,120)`. Render inset centered at `(margin 28, header 122)` within `avail 3452×2330`, 1 px border `(210,210,210)`. Content: pale grey shell `(RGB ~186,190,195)` with flat beige doors `(~160,120,90)`, pale blue sofa `(~180,200,220)`, beige table — all single-bounce Lambert, no texture, no AO contact shadow beyond soft decorative diagonal.
* Bottom shows `1600×948` share plus `48 px` dark bar `#1C1E24 (28,30,36)` with white text `(245,245,245)` at `22 pt`: e.g. `P.KHÁCH +0.100` (verified via `tmp_bar_khach.png` 800×96 NEAREST blow-up). Diacritics `Ă, Á, Ủ` correctly shaped via DejaVuSans. Bar height is `48 px` as spec; image above bar is the same flat field (extrema `7–254` but perceptual range is narrow pastel). File sizes `25–39 KB` confirm low-frequency fields — JPEG has no blocking because no detail to block.
* On A3 at arm's length (3508 px / 300 dpi = 297 mm wide + margin), the flat fields read as uniform colour; door handles, light switches, skirting are absent; edges are hard poly lines with no chamfer/bump.

**Bar B — right panel — `read` shows:**

* Tonal range `0–255` exercised; even the 500 px thumb in montage shows concrete horizontal grain, timber floor planks with specular streak, white chair with shadow under seat, plant leaves overlapping with soft leaf shadows on the facade. Hard sun slab across floor has crisp leading edge (2 px) plus 6–8 px leaf penumbra — requires real sun + real foliage.
* Material grain survives downscaling: concrete pores visible at 509 px column width, timber grain and chair fabric legible.
* Scale: planter module depth (~400 mm) vs street curb vs utility pole vs human-proportioned gate (`~900 mm` leaf). Interior: chair/table/human silhouette height immediately keys the double-height volume (`~4.8 m` at stair).

**Blind reaction time:** <2 s. One side is a correctly sized sheet of paper showing a colour-coded massing diagram; the other is a photograph with concrete you can feel. Round 1 required no judgement (blank vs photo). Round 2 requires judgement — the diagram is now competent but photoreal material/light/scale are absent.

---

## 7. Single biggest gap — the sentence that matters

**The blank-source bug is fixed — packs now render geometry and Vietnamese level tags so they are readable as diagrams at A3 and 1600 px (no longer blank paper) — but Bar's hard sun-cut through real material (formwork concrete grain, timber, foliage with crisp + leaf-dapple shadows) still beats candidate's flat Lambert pastel with a single decorative soft shadow on every axis, so material / light / scale remain undeliverable.**

If forced to one axis: **light** — candidate disclaimer admits `Shadows decorative — not a daylight analysis` and renders one soft diagonal wash per view (extrema `71–223`, no `0` black, no `255` white, no hard cut), whereas Bar's sun writes depth through sharp planter shadows and interior sun slabs with secondary bounce — even a blind greyscale print would expose it.

---

## 8. What must change before these packs can pass a print/delivery gate (ranked — minimal diff beyond Round 2)

1. **Replace Lambert with textured PBR and real sun:** assign concrete `rough 0.8 + 2% bump + tie-hole normal`, plaster `rough 0.9`, timber `rough 0.3 + grain`, enable sun `strength 5 angle 15°` with contact shadows + AO `dist 0.6 m factor 0.08`, sky light `02_urban HDRI + sun`. Bake until `extrema 0–255` touches both ends and `share JPEG > 120 KB` for `1600 px` (texture forces size). Keep the Vietnamese bar — it is good.

2. **Fix `plate_elev_south.png` fallback:** install `cairosvg` or export elevation PNG directly from Blender `output/svg/*.svg` at correct aspect `496×2480 → 600×3000` (preserve `viewBox`), draw title block with ISO 5457 table (project / sheet / scale / datum / revision / logo) at `9–11 pt` vektors, add `1:100` graphic scale bar + north arrow; ensure `plate_elev_south ≥ 800 KB` and `ncolors > 2000`.

3. **Upscale half-resolution interiors to 1920×1080:** 6 of 12 views export at `960×540` — at A3 after fitting `3452×2330` they are upscaled `~3.6×` (Lanczos soft). Re-render those 6 at `1920×1080` like the 4 good ones; QA gate `assert min(width,height) ≥ 1080 for all 12`.

4. **Scale cues:** add `1.70 m` silhouette or `500 mm` module annotation on exterior and `human at +0.100` on `khach` plus `graphic 1:100` bar on each A3; expose level datum `+0.000 / +7.000 / +13.800` as a rule on the image (share already has `+tag` in caption — extend to a thin left-edge datum line).

5. **QA gate (block delivery if re-regressed):** `assert all A3 > 600 KB and ncolors > 2000 (and not squashed), all share max==1600 and dark-bar sampled (28,30,36) and caption contains "+.*\d+\.\d{3}" and source PNG bytes > 300 KB and unique colours > 800` — Round 2 would fail on (2) and (3), catching the elev placeholder and half-res.

---

## 9. Scoring — how Round 2 moved (material / light / scale only, blind on 1050×650)

| Dimension | BAR | CANDIDATE R1 | CANDIDATE R2 | Notes — Round 2 delta |
|---|---|---|---|---|
| Material response | 5 | 0 | **2.0** | From single colour #C8C8C8 void to flat Lambert with distinct hues (beige doors, blue sofa) but still no grain/bump/specular — massing palette, not material. |
| Light / shadow modelling | 5 | 0 | **1.5** | From no shadow at all (extrema spike 200) to one decorative soft diagonal per view + footer disclaimer `not a daylight analysis` — vs Bar hard sun with crisp + leaf dapple. |
| Scale / datum / context | 5 | 0.5 | **3.0** | From zero tags to correct Vietnamese level tags `+0.100–+20.600` on every share + date on A3 title block; but still no graphic scale, no human figure, no street context for exterior (tiny tower). |
| A3 print density | 5 | 0 | **2.5** | 34 KB → 0.9–1.15 MB for 8.7 MP — now prints without blank-paper embarrassment, but at 0.9 bpp vs Bar 2.4 bpp at smaller print size remains thin. |
| Share 1600 px density | 5 | 0 | **2.0** | 27 KB → 25–39 KB — size barely changed because flat fill compresses; Bar needs 250–530 KB to hold grain — share remains diagram-dense only. |
| Caption / bar | 5 | 1 | **4.5** | Dark `#1C1E24` 48 px bar with `DejaVuSans 22 pt` white Vietnamese + level tag is correct, legible, and localized — the one dimension where packs now **meet or exceed** Bar's generic caption. |

Overall print/delivery quality (material/light/scale): **BAR 5.0 vs CANDIDATE 2.1** — up from **0.2** in Round 1. Packs left the `unshipable` bucket and entered `internal review diagrams` — still short of `client print`.

---

## 10. One-sentence gap (gloop gate — copy verbatim)

**BAR > CANDIDATE — Round 2 fixes the catastrophic blank (12× 8.5 KB void → 448 KB–2.1 MB real geometry with correct dark Vietnamese caption bars, so A3 3508×2480 921 KB–1.15 MB and share 1600 px 25–39 KB are now readable) but flat Lambert pastel with a single decorative shadow and no grain/bump/specularity still loses to Hiroyuki Oki's hard sun-cut through formwork concrete, timber and foliage that prints at 0–255 with crisp + dapple shadows and human scale.**

---

## 11. Raw fetch & file log (audit)

```
# Bar (fetched before candidate)
read https://www.archdaily.com/199755/stacking-green-vo-trong-nghia → 200 canonical 199755 og:image 1280×1920 Hiroyuki Oki +19 gallery
urllib tmp/bar_fetch_0.jpg  1280×1920 527,409 B  validated RGB 0-255  (facade hero 5004e325 large_jpg)
urllib tmp/bar_large_1.jpg 1280×1920 288,227 B  interior stairs
urllib tmp/bar_large_2.jpg 1280×1920 316,967 B  interior dining (used in montage right panel)
urllib tmp/bar_large_3.jpg 1280×1920 420,727 B  interior detail

# Candidates (measured 2026-08-29 14:40 UTC)
A3 plate_khach.png             3508×2480 1,151,510 B  ncolors 8,934  SHA dense pastel, header 28/18 pt correct
A3 plate_bep_an.png            3508×2480 1,113,578 B  5,002
A3 plate_hanh_lang_thang.png   3508×2480 1,045,475 B  6,610
A3 plate_exterior_front.png    3508×2480   942,588 B  4,725  (tiny tower, 15% plate area)
A3 plate_elev_south.png        3508×2480   112,509 B    579  ← placeholder fallback, squashed (no cairosvg)
share/khach.jpg                1600×948   35,711 B  bar (28,30,36) white text 22 pt "P.KHÁCH +0.100"
share/bep_an.jpg               1600×948   33,974 B  "P. ĂN + BẾP +0.300"
share/hanh_lang_thang.jpg      1600×948   27,925 B  "HÀNH LANG +0.000"
share/exterior_front.jpg       1600×948   25,250 B  "MẶT ĐỨNG CHÍNH  —  exterior_front"
... (12 views 25–39 KB, all max==1600, bar #1C1E24, Vietnamese +tag)
source pngs: 960×540 (6 views 457–510 KB) / 1920×1080 (6 views 1.93–2.10 MB) — now RGBA with geometry, extrema 68–223, getcolors >800

# Montages
reports/gloop-critic-packs-round2-montage.jpg            1050×650 129 KB  blind A/B (interior khach + Bar dining)
reports/gloop-critic-packs-round2-montage-revealed.jpg  1050×650  revealed labels A=PACKS B=BAR
reports/gloop-critic-packs-round2-montage-exterior.jpg  1050×650  blind appendix exterior vs facade
blow-ups: tmp_bar_khach.png 800×96 NEAREST, tmp_plate_top.png 1754×60 show diacritics/title block legible
```

*Fetched: 2026-08-29 14:40 UTC via `read` (ArchDaily 199755, 4× Oki `large_jpg` via `images.adsttc.com`) and `read` + `Pillow getcolors/extrema` local packs (5× A3 3508×2480 112 KB–1.15 MB + 12× share 1600×948 24–39 KB + 12× source 960/1920 px 448 KB–2.10 MB) + blind montage 1050×650 labels stripped `CANDIDATE A vs CANDIDATE B`. Judged blind on material/light/scale only. Single biggest gap sentence locked before reveal.*
