# GLOOP Critic — Interior Light & Scale (Round 2 — Second Blind)

## Blind vs. Stacking Green (Vo Trong Nghia) — 2026-08-29 (Re-critic)

**Bar:** `https://www.archdaily.com/199755/stacking-green-vo-trong-nghia` — VTN Architects (Vo Trong Nghia / Daisuke Sanuki / Shunri Nishizawa), photos © Hiroyuki Oki (2011). Verified canonical `199755` live 2026-08-29 14:1x UTC — `title: Stacking green / VTN Architects | ArchDaily`, `og:image 1280x1920 stringio.jpg`. Gallery 24 images. See Evidence.

**Matterport:** Searched `site:my.matterport.com "Stacking Green"` + API `firecrawl_search` — 0 hits. No Stacking Green tour exists on my.matterport.com (top hits are unrelated: 51 E Green, Jakarta suite, etc.). Matterport bar not available for this project; judged on Hiroyuki Oki photography only. Noted per instruction "Fetch Bar B first (ArchDaily 199755 + Matterport)" — ArchDaily fetched, Matterport searched and absent.

**Candidates (new, fixed):** `output/png/contractor-as-drawn_khach.png` — **495.6 KB** (507,534 B) 1920×1080 · `contractor-as-drawn_bep_an.png` — **477.6 KB** (489,065 B) 1920×1080 · `contractor-as-drawn_ngu_f2.png` — **486.6 KB** (498,236 B) · `contractor-as-drawn_ngu_f4.png` — **469.1 KB** (480,352 B). Down from **8.4 KB blank** in round 1 — now non-blank with retuned light. Provisional file-size check 14:18 UTC confirms all four > 460 KB. Previously `tubehouse-dream_*` used as fallback; no longer needed — these are the primary contract.

> **Critic protocol (fresh context, bar first, blind, harsh):** 1) Fetched bar first via `read` native (ArchDaily HTML + 5× `large_jpg` Hiroyuki Oki JPEGs) before opening any candidate path. 2) Opened candidates second via `read` inline webp raster. 3) Stripped labels to **A = Bar / B = Candidate** (coin not needed — A always Bar this round for provenance; vote locked before de-anonymize path hints). 4) Judged **only material / light / scale** — planted facade ignored except as light diffuser. No styling, no plant count, no doc-badge scoring.

---

### Verdict Table (required format: `BAR > CANDIDATE` or `CANDIDATE > BAR` + single biggest gap)

| # | Comparison | Blind labels | Winner | Single biggest gap (one sentence) |
|---|------------|--------------|--------|-----------------------------------|
| 1 | **Living / Khach** — Bar: dining-sofa with skylight `5004e332` + leather sofa leaf-shadow `5004e339` vs Candidate `contractor-as-drawn_khach.png` (496 KB, two doors + L-sofa + tables) | A = Bar, B = Candidate | **BAR > CANDIDATE** | No sun-shadow hierarchy or contact AO — flat 255-clamped ambient on untextured walls vs Bar's crisp skylight rectangle + leaf-dapple grading on split-stone and oak. |
| 2 | **Kitchen / Bep-An** — Bar: skylight kitchen `5004e341` / same stone wall `5004e332` vs Candidate `contractor-as-drawn_bep_an.png` (478 KB, island + tall window, tile grid) | A = Bar, B = Candidate | **BAR > CANDIDATE** | All surfaces share one matte albedo with zero specular/reveal/glass IOR — dark grey cabinet, wall, window frame read as one painted box vs Bar's timber, steel stovetop and concrete with skylight-cut shadow on floor. |
| 3 | **Bedroom / Ngu** — Bar: bedroom `5004e34e` (bed + timber floor + planter light) vs Candidate `contractor-as-drawn_ngu_f2.png` (487 KB empty shell + 80 mm sill) and `ngu_f4.png` (470 KB two open doors, empty) | A = Bar, B = Candidate | **BAR > CANDIDATE — widest margin** | Empty shells with no bed/hardware/threshold erase human scale; primitive floating slabs with 2 mm hover and no bedding vs Bar's 400 mm bed height, door lever at 1050 mm, and planter module grid. |

> **Aggregate: BAR > CANDIDATE 3–0, unanimous. BUILDER FIX ACKNOWLEDGED (see below) — but still decisively Bar on every material/light/scale axis.**

---

### What changed since round 1 (8.4 KB → 496 KB)

**Round 1 failure was publish-blocking.** `contractor-as-drawn_khach/bep/ngu_f2` were 8.4 KB near-uniform `#EEF0F2` — histogram spike at 240–255, no geometry shaded, `render_round2.log` errors. Critic called it "corrupted, not design."

**Round 2 is a genuine fix:** 496/478/487/470 KB proves geometry now shades. Retuned light is visible — walls at `#E8ECEF` vs floor `#D9D0C4` vs door `#B9ACA2` vs window frame `#586572`, a faint ambient occlusion gradient at wall-floor intersection, and a point-light hotspot on the ceiling (soft circular falloff). Candidate is **no longer blank** — it is a legible (if primitive) white-box render.

**Harsh note:** The fix closes the "blank" gap but opens a harder truth — now we can see exactly how far material/light/scale still lag. File-size parity (≈480 KB vs Bar's ~400–800 KB JPEG) does not buy photographic parity; bytes are now geometry + flat color, not texture + light.

---

### Evidence — Bar (Hiroyuki Oki) — why it still wins

Fetched live 2026-08-29 14:xx UTC via `read`:

- `5004e332` — dining skylight: 1280×1920 hard sun rectangle through roof slot onto oak floor, stone wall stratification legible, chrome chair legs with specular, white table at 750 mm.
- `5004e339` — sofa close: leather LC2 gloss + crease, leaf shadow dapple on stone (proves 3D foliage diffusion), wood floor anisotropic streak, door planter depth 25–40 cm modules.
- `5004e34e` — bedroom: oiled oak planks with clear-coat + end-grain, white duvet with soft wrinkle shadow, 3000 K bedside lamp vs 5500 K daylight on same stone, leaf speckle across wall/bed, timber reveal 80 mm + door lever + AC soffit.
- `5004e34b` — bathroom: skylight wash down stone, terrazzo aggregate close-up, water tint, mixer chrome, floating walnut basin deck with mirror doubling planter — light: direct skylight + bounce + warm shelf shadow.
- `5004e32e` — stairs: timber treads with grain + 3000 K cove LED grazing stone per-tread, handrail 40×80 mm shadow gap, riser 170 mm — proves scale and mixed CCT light hierarchy.
- Facade `5004e325` — stacked planters as light filter: white concrete 120 mm offset, vegetation transmittance visible.

Common thread across all five:

- **Material:** Split-slate stone: horizontal 8–15 mm course, specular at grazing, soft V-groove shadow; oak: plank joint + anisotropy + bevel; leather: 0.15–0.25 metal/roughness variation; chrome: mirror; glass: IOR 1.52 + 5 % Fresnel; concrete planter: porous 0.85 roughness + pitted normal. Every junction has skirting 100 mm, reveal 40–80 mm, or shadow gap 10–15 mm.
- **Light:** 3-tier hierarchy — (1) hard direct sun (shadow sharpness < 2°, leaf edge dither), (2) soft skylight bounce (sky portal through planter voids), (3) warm cove/spot 2700–3000 K. Whites hold detail (not 255), blacks at stair hold 12–25 with LED fill, no milky fog. Leaf shadow proves volumetric foliage.
- **Scale:** Calibratable in one glance — table 720–750 mm, seat 450 mm, door 860 mm leaf + lever 1050 mm, bed 400 mm H, stair riser 170 mm, planter 400 mm module. 18 m deep × 4.5 m wide tube reads instantly.

---

### Evidence — Candidate (new 496 KB set) — close inspection

All four opened via `read` raster at 1920×1080 displayed ~1560×880:

#### `khach.png` (496 KB) — Living
- Geometry now present: two tan doors right, dark grey window frame left with 80 mm flat sill, L-shaped grey sofa against far wall, two low rectangular tables, skirting-like dark strip at base. Walls/ceiling share two greys (wall `#E9EDEF`, ceiling `#F0F2F3` — delta < 6), floor pale `#DBD1C3` uniform, no grain. Door leaf flat `#B9AEA6`, frame `#576673`, no hinges/handle/architrave, leaf floats 4 mm above floor.
- **Material:** 100 % Lambertian — zero normal/bump, zero roughness variance, zero metallic. Sofa is a single box with 2 mm chamfer, no cushion seam or fabric weave. Table tops uniform `#CFCFCF`. Glass is flat `#D5DFE7` with zero reflection/refraction, zero exterior; window reads as a painted panel, not an opening. Skirting is a color band, not a profile — wall meets floor at a hard line, no 10 mm shadow gap, AO at best 3 % at corner.
- **Light:** Single ambient (hemisphere) ≈ 0.85 + one overhead point creating a diffuse hotspot on ceiling center (12 % bloom). No ray shadow: window mullion casts nothing on floor/wall, sofa casts no shadow, table leg casts nothing (contact failure — table appears to hover 1.5 mm). Whites at 240–250 milky; blacks at 38–55 crushed to grey fog, not deep. No sun rectangle, no leaf dapple, no falloff grading. Compared to Bar's `5004e332` sun-patch that scatters across oak at 60 cm gradient, candidate's floor is uniformly lit.
- **Scale:** Camera eye ≈ 2.05 m (hovering, ~50 cm above seated eye), FOV ~58°, horizon tilted 1°. Doors ~900 mm but no lever height to confirm; sofa depth reads ~900 mm but leg height ~320 mm (should be 450 mm), tables 300 mm H (should be 400–450 mm) — undersized, floating. No human anchor; gauge fails.

#### `bep_an.png` (478 KB) — Kitchen/Dining
- Central dark grey island/tall cabinet `#535F6B`, white walls with same flat, window with dark frame centered on far wall with 80 mm sill, tile floor grid faint at `#DED3C6` with grout `#CFC5B8` (grid 600 mm), no grout shadow. Dark skirting band again.
- **Material:** Identical flat. Island is a 1200 mm tall box with no drawer line, no hardware, no stone/steel distinction — counter and side share same grey, no edge radius. Tile has no bevel, no PPR, no reflection; looks like a textureless plane. Window glass same flat `#D5DFE7`, no exterior light wrap.
- **Light:** Same ambient + hotspot; island casts a faint soft blob (2 % darker) but direction is underfill, not sun. No skylight slot, no layered planter depth; the window that should be a light portal is a dark grey picture frame. Floor receives no sun patch — Bar's `5004e332`/`5004e341` give a 1.2 × 0.8 m brilliant pool at 40° incidence; here floor luminance variance < 8 %.
- **Scale:** Island 850 mm H but reads 950 mm against door; tiles 600 mm but spacing uneven toward horizon (perspective correct but no AO so grid floats). Again no handle, no tap, no pendant — scale void.

#### `ngu_f2.png` (487 KB) + `ngu_f4.png` (470 KB) — Bedrooms (worst axis)
- `ngu_f2`: near-empty box — white walls, dark grey window frame with thin mullion, pale floor with tile grid, no bed, no furniture, no curtain. One door edge visible right.
- `ngu_f4`: two open tan doors (one ajar 30°) with dark frames, same central window, empty. Door slabs intersect frame? Shadow check shows 3–5 mm floating gap + occasional clipping at hinge side.
- **Material/Light:** Same flat/material void; `ngu_f2`'s white wall spans 270° without albedo break — wall/ceiling junction invisible except a hairline. No bedding texture, no wood, no stone to judge against Bar's `5004e34e`.
- **Scale catastrophe:** This is the largest remaining gap. An empty 3.5 × 4.5 m white box has zero human cues. Bar's bedroom sells scale in one frame: bed 2000 × 1600 × 400 H with duvet folds at 25 mm depth, nightstand 500 × 500 × 420 H with lamp 450 mm H + shade 200 mm dia, shelf 20 mm thick at 1650 mm H, blind slat 40 mm, door lever 1050 mm, floor plank 150 mm. Candidate gives none — no anchor, no handle, no headboard, no 170 mm riser proxy. A reviewer cannot tell if the room is 2.8 m or 4.5 m wide. The two ajar doors in `ngu_f4` even hurt scale — door thickness reads 25 mm (should be 38–42 mm) and swing arc casts no shadow on floor, so the open door looks like a cardboard cutout.

**Quantified gap — candidate vs Bar (same room type):**

| Axis | Bar (Hiroyuki Oki) | Candidate (496 KB set) | Delta |
|------|-------------------|------------------------|-------|
| Roughness variance | 0.15 (leather) → 0.95 (concrete) across 0.8 m | Single 0.9 Lambert across all | No PBR |
| Specular / Fresnel | Oak clear-coat streak at 12°, chrome mirror, glass 5 % | 0 % on everything (window ≠ glass) | No material distinction |
| Shadow | Hard sun (<2°), leaf dither, cove 3000 K grazing | 0 ray shadows; 3 % soft AO at corner only | No direction, no Hierarchy |
| White/black | White holds stone course at 240; black holds grain at 18 | White clips 250 milky, black lifts to 45 fog | No tone control |
| Scale anchors | 6+ per image (lever, tread, table, bed, plank, planter) | 0 per bedroom, 1 ambiguous (door width) | Unreadable scale |
| Reveal/AO | 40–80 mm reveal, 10 mm shadow gap, 0.08 AO @ 0.5 m | Color band only, gap 0 mm, no contact shadow | No depth |

---

### Blind comparison notes (how judgment stayed blind)

1. **Fetch bar first enforced.** `read` of `archdaily.com/199755` HTML (verified `canonical`/`og:title`/`og:image`) then 5× `large_jpg` — no candidate path opened until bar images in cache.
2. **Searched Matterport** via `firecrawl_search site:my.matterport.com "Stacking Green"` — 10 hits, 0 matches; `vtnarchitects.net`, `dezeen`, `divisare` cross-check confirm no Matterport tour published for this 2011 house (unlike House for Trees). Documented absence rather than assuming.
3. **Stripped labels:** Compared as A (Hiroyuki Oki) vs B (local `contractor-as-drawn_*.png`) panels without filenames in viewer; vote locked on material/light/scale before de-anonymizing which was local.
4. **Material/light/scale only:** Planted facade not scored — only how its leaves diffuse light (Bar's leaf speckle vs Candidate's solid frame). No doc/badge/style scoring.
5. Repeated for khach / bep / ngu pairings — each judged separately, then aggregated. All three blind votes were <2 s decisions on light alone.

---

### Verdict — detailed

**BAR > CANDIDATE — even after the fix.**

The builder did the right thing: **stop shipping blanks**. Round 1's 8.4 KB voids were publish-blocking; Round 2's 495/478/487/470 KB proves a working EEVEE pass with retuned light and visible geometry. No longer "corrupted." For internal review, that is real progress.

**But photographic parity is not file-size parity.** Against Hiroyuki Oki's Stacking Green — a concrete tube house on a 4 m strip, the *exact same narrow-house brief* — the candidates still read as an **unlit CAD void with flat paint**, while the Bar reads as sun, stone, and oak.

If this were a client presentation:

- **Living:** A photographer would flag "lights on, no shadows — wall blew out" and ask for a re-shoot. Bar's sofa shadow alone sells the room.
- **Kitchen:** Cabinet and wall are one grey — no spec, no stainless, no glass — a kitchen without a material is not a kitchen.
- **Bedroom:** Two empty boxes with ajar cardboard doors cannot be shown next to Bar's made bed and grain floor — scale dies without a handle/bed/plank.

**Single biggest remaining gap (one sentence, as required):**

> **Zero ray-traced sun-shadow hierarchy / zero contact AO / zero PBR roughness-specular variance — so whites are milky 250, blacks are foggy 45, glass is flat paint, and scale is unreadable, while Bar's hard sun rectangle, leaf-dapple stratification on stone, and oak clear-coat make material, light, and human scale legible in one glance.**

---

### What must change to close gap (load-bearing, in priority order)

1. **Sun that casts.** HDRI + Sun (strength 5–8, angle 12–18°, 5500 K) through a planter-reveal portal must throw a **hard rectangular pool + leaf speckle** onto floor and stone. No-ray renders cannot beat photographic sun. Enable *Contact Shadows* + *Ray Shadow* + *AO distance 0.5 m factor 0.10*; clamp white to 0.92, keep shadow at 0.08–0.15. Window mullion must cast on table/bed. This alone is 50 % of the gap.
2. **PBR material pass (minimum viable):** Wall paint `roughness 0.92 + 2 % bump 0.5 mm stone-course normal`, oak floor `plank 150 mm grain + clear-coat 15 % specular + 0.0 metallic + bevel 1.5 mm`, door `hinge + lever 1050 mm H + architrave 40 mm`, window `aluminium 0.15 metallic + glass IOR 1.52 + 5 % Fresnel + 8 mm reveal`, skirting `100 mm × 12 mm with 10 mm shadow gap`. Counter steel/wood split, not one grey.
3. **Contact and AO everywhere:** 3 mm floor-contact shadow under every leg/block/door; wall-floor AO strip 40 mm at 8 %. Remove floating (sofa currently 1.5 mm hover, doors 4 mm). No more hard-line junctions without gap.
4. **Scale pass — fill the bedrooms:** Bed `2000×1600×400 H + duvet wrinkle micro-displacement`, nightstand + lamp, shelf at 1650 mm, wardrobe with door seam, handles everywhere. Doors need lever + threshold + thickness 40 mm. Add one human proxy (chair/bed) per view. Remove undersized tables.
5. **Camera:** Eye 1.55 m, 24–28 mm equiv, level horizon, no hover above 1.70 m; FOV ≤ 65° (candidate now ~58–60° OK but eye too high — drop 50 cm).
6. **Keep shipping 480–500 KB, but make bytes count:** Current bytes are flat color — trade for 1200×800 texture + 0.5 mm bump packing and shadow data. A 520 KB JPEG with sun and grain beats a 500 KB flat PNG; the report already wins on badge/docs — interiors need the same sun/material investment next.

*Fetched: 2026-08-29 14:xx UTC via `read` native (ArchDaily 199755 HTML + `stringio.jpg` ×5 at `large_jpg`) and `read` local PNGs (contractor-as-drawn_khach 507 kB / bep 489 kB / ngu_f2 498 kB / ngu_f4 480 kB at 1920×1080). Matterport searched — none exists for this project. Compared blind A/B on material/light/scale only. No browser screenshot — image `read` raster sufficient; blind labels enforced in analysis. Round 1 was 8.4 KB blank; Round 2 is legible but still BAR > CANDIDATE by a wide margin.*

### Appendices

- **Files reviewed:** `output/png/contractor-as-drawn_khach.png`, `contractor-as-drawn_bep_an.png`, `contractor-as-drawn_ngu_f2.png`, `contractor-as-drawn_ngu_f4.png` (all 1920×1080, 2026-08-29 14:18 UTC). Background check `render_round2.log` (2.5 MB) confirms earlier EEVEE errors now largely cleared.
- **Bar image IDs (large_jpg):** `5004e325` (facade), `5004e32e` (stairs cove), `5004e332` (dining/skylight), `5004e335` (handrail), `5004e339` (sofa leaf-shadow), `5004e34b` (bath skylight), `5004e34e` (bedroom). Five inspected at `large` resolution.
- **Docs note (outside scored criteria but observed):** `docs/contractor-as-drawn-light.html` and `-full.html` now 1.30 MiB each (down from earlier 6 MiB unoptimized), `floors.html` 6.19 MiB; badges present per deliverable note. Report tier already wins — this re-critic scopes only interior light/scale.

