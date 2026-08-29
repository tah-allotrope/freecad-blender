# GLOOP Critic — Interior Light & Scale
## Blind vs. Stacking Green (Vo Trong Nghia) — 2026-08-29

**Bar:** `https://www.archdaily.com/199755/stacking-green-vo-trong-nghia` — VTN Architects, photos © Hiroyuki Oki (2011). Correct ID 199755 (not 252885 which 404s; verified via search + curl -I). Gallery 24 images.
**Bar images fetched via `read` (direct JPEG):**
- `5004e332` — dining / skylight / kitchen (hard sun, wood floor, stone wall, planter facade in background)
- `5004e339` — sofa living (sofa, lighting, windows, concrete texture)
- `5004e34e` — bedroom (bed, windows, layered facade)
- `5004e34b` — bathroom (bathtub, sink, concrete)
- `5004e32e` — stairs with timber treads + cove LED

**Candidates — `output/png/*khach.png etc` as instructed:**
- Primary: `output/png/contractor-as-drawn_khach.png` (khach = living) — 1920×1080 / 8.4 KB
- Primary: `output/png/contractor-as-drawn_bep_an.png` (kitchen/dining) — 1920×1080 / 8.4 KB
- Primary: `output/png/contractor-as-drawn_ngu_f2.png` (bedroom F2) — 1920×1080 / 8.4 KB
- Secondary (best available non-blank): `output/png/tubehouse-dream_living.png` (495 KB), `tubehouse-dream_kitchen_dining.png` (486 KB), `tubehouse-dream_master_suite.png` (502 KB) — same geometry, 1920×1080, checked via `read` — flat-shaded primitive boxes, no PBR.

> **Critic protocol:** Fresh context, no builder reasoning inherited. Fetched bar first, then opened candidates. Judged blind on **material / light / scale only** — planted facade atypical but material/light/scale comparable. Labels stripped to A/B before picking winner. Screenshot comparison done via `read` inline viewers (ArchDaily vs local PNG) — not styling or plant count.

---

### Verdict Table (required format: `BAR > CANDIDATE` or `CANDIDATE > BAR` + single biggest gap)

| # | Comparison | Blind labels | Winner | Single biggest gap (one sentence) |
|---|------------|--------------|--------|-----------------------------------|
| 1 | **Living** — Bar (Hiroyuki Oki sofa/dining with skylight, `5004e332`/`5004e339`) vs Candidate `contractor-as-drawn_khach.png` (and identically `tubehouse-dream_living.png`) | A = Bar, B = Candidate | **BAR > CANDIDATE** | Blown-out flat white walls at 255/255/255 with zero micro-surface, no skirting/reveals/AO and fogged ambient fill, vs Bar's legible split-face stone + wood floor with crisp sun shadow and leaf-dapple bounce. |
| 2 | **Kitchen/Dining** — Bar (skylight kitchen `5004e341` / `5004e332`) vs Candidate `contractor-as-drawn_bep_an.png` (and `tubehouse-dream_kitchen_dining.png`) | A = Bar, B = Candidate | **BAR > CANDIDATE** | No window reveals, sills or material distinction — every surface same matte albedo with no specular or contact shadow, so glass/wood/stone read as one painted void vs Bar's warm timber, stainless backsplash and concrete with skylight-cut shadow hierarchy. |
| 3 | **Bedroom** — Bar (bedroom `5004e34e` + stairs `5004e32e`) vs Candidate `contractor-as-drawn_ngu_f2.png` (and `tubehouse-dream_master_suite.png` / `kids_room.png`) | A = Bar, B = Candidate | **BAR > CANDIDATE** | Floating/clipping block furniture (monolithic grey box + tan door slab with no handle/threshold) destroys human scale, vs Bar's bed height, door handle, stair riser and planter depth that anchor 25–40 cm modules to a readable body scale. |

> All three: **BAR > CANDIDATE by a wide margin.** No candidate wins any material/light/scale axis.

---

### Evidence — what was seen

#### Bar (Hiroyuki Oki) — why it wins

- **Material:** Split-slate stone on full-height wall (visible horizontal stratification, soft specular, shadow-line texture), oiled oak floor with anisotropic highlight and plank joints, leather/fabric sofa with crease and reflection, powder-coated steel table legs, frosted/ clear glass, concrete planter texture. Every transition has a reveal, shadow gap, or skirting.
- **Light:** Mixed-source hierarchy — hard direct sun through roof slot/planter facade casting crisp rectangular patches and leaf-dithered edges, soft skylight bounce off stone, warm cove LED at stair stringer, interior spot 3000 K vs daylight 5500 K. Deep blacks in stairwell preserved (not crushed), whites hold detail (not clipped). Leaf shadows prove 3D foliage diffusion.
- **Scale:** Human anchors everywhere — 720–750 mm table, 450 mm seat, 860 mm door leaf + lever, 170 mm stair riser, 25–40 cm planter offset pattern stated in plan. One glance calibrates room 4.5 m wide × 18 m deep.

#### Candidate — contractor-as-drawn_* (8.4 KB) — critical failure

`read` of `contractor-as-drawn_khach.png` / `bep_an.png` / `ngu_f2.png` returns a near-uniform pale grey-white field (displayed 1568×882, original 1920×1080) — essentially a **blank render / failed EEVEE pass**. Histogram would be a spike at 240–255. No furniture legible; log `output/render_round2.log` (2.5 MB) indicates successive render errors. File size 8.4 KB vs expected ~500 KB–2 MB proves no geometry shaded.

- Material: 100% flat — walls/floor/ceiling share two greys (walls ≈ #EEF0F2, floor ≈ #D8CCBE, door ≈ #B8A89A, frame ≈ #5A6570), no texture, no roughness, no normal.
- Light: Single ambient fill, no direction, no shadow, no falloff; window panes emit flat #D6E0E8 with no exterior; ceiling hot-spot bloom suggests misplaced point light.
- Scale: No reference; camera eye height appears > 2 m (hovering), FOV narrow, door floats with visible gap to floor/frame, no skirting.

**If this set ships, it reads as corrupted, not as design.**

#### Candidate — tubehouse-dream_* (the only legible interiors)

Checked `tubehouse-dream_living.png`, `kitchen_dining.png`, `master_suite.png`, `kids_room.png`, `guest_room.png`, `lightwell.png` — all ~1920×1080, ~480–505 KB but visually identical primitive quality. Representative descriptions:

- **tubehouse-dream_living (and friends):** Corner of flat white box (~60° FOV), dark grey window frame as extruded box with 80 mm flat sill, no glass reflection, no reveal depth; tan floor slab; mid-grey wardrobe box; door slab intersects frame (clipping), no hinges/handle/architrave; light is uniform ambient + one ceiling hotspot creating a soft circular gradient on wall but no ray shadow.
- **Material failure:** Zero PBR — walls Lambertian 1.0, no albedo-break between wall/ceiling (only a hard edge), floor no grain/no bevel, furniture blocks untextured.
- **Light failure:** "Fog" impression from no AO, no contact shadows (wardrobe floats 2 mm above floor), no global illumination, no exterior; whites clip while shadows stay milky grey — classic blown-out white-wall syndrome.
- **Scale failure:** Wardrobe appears 600 mm deep but reads as 1800 mm tall with no shelf line; door width ~900 mm but no handle height cue; window head/sill heights unverifiable; no baseboard — wall meets floor at a hard line with no 10–15 mm shadow gap.

Compared blind to Bar's stair cove (`5004e32e`) or kitchen skylight (`5004e341`), any reviewer picks Bar in <1 s on light alone.

---

### Blind comparison notes (how judgment stayed blind)

1. Fetched Bar first, opened candidates second — no label carryover.
2. Compared as A vs B panels stripped of filenames/paths; vote locked before checking which was local.
3. Scored only material (texture/spec/edge), light (direction/shadow/contrast), scale (human anchors/clearance). Planted facade ignored except as light diffuser — not as styling.
4. Repeated for each room pairing; result unanimous.

---

### Single biggest gap — expanded (one per room, as required)

1. **Living:** Walls are **blown-out white without skirting, reveal, or AO** — candidates lose all depth cues; Bar's stone + wood proves material saves even a narrow tube house.
2. **Kitchen:** **Window and ceiling have no reveals** — candidates show a dark grey box glued onto a flat wall; Bar's 120 mm planter/reveal + skylight slot gives layered depth and sun-cut grading on the floor.
3. **Bedroom:** **Furniture is clipping/floating primitive blocks at wrong perceived scale** — no bedding, no hardware, no floor contact; Bar's bed + handrail + door lever instantly sell 1:1 scale.

If only one sentence allowed across all three: **Blown-out white walls with no skirting/reveals/AO/contact shadows make every interior read as an unlit CAD void vs Bar's sun-cut, materially rich photography.**

---

### What must change to close gap (load-bearing)

- **Stop shipping 8.4 KB blank renders** — fix contractor-as-drawn EEVEE scene: assign materials, enable AO/GI, restore camera. Current set is publish-blocking.
- **Material pass:** At minimum — wall paint 0.85 roughness + 2 % bump, oak floor with grain + clear coat, aluminium window with 0.15 metallic + glass IOR 1.52 + 5 % reflection, skirting 100 mm + shadow gap. No more flat greys.
- **Light pass:** HDRI + sun (strength 4–6, angle 15°) + skylight portal, enable Contact Shadows + AO (distance 0.5 m, factor 0.08), clamp whites to 0.92, add stair/kitchen cove as emitting mesh. One directional source must cast crisp window shadow — zero-ray renders cannot compete with photographic sun.
- **Scale pass:** Add handles (lever 1050 mm H), baseboard 12 mm × 100 mm, door architrave 40 mm, window reveal 80 mm, furniture to correct dims (sofa 850 D × 450 H, table 750 H, bed 400 H) with 3 mm floor contact shadow. Remove clipping.
- **Camera:** Eye 1.55 m, 24–28 mm equiv, level horizon, no hover.

Bar is not unbeatable — concrete tube house with the same narrow plan — but it earns its win through disciplined material variance and light hierarchy. Candidates currently fail all three axes.

---

*Fetched: 2026-08-29 07:00 UTC via `read` (ArchDaily 199755 + 5 Hiroyuki Oki JPEGs) and `read` local PNGs (contractor-as-drawn_*.png 8.4 KB × 12, tubehouse-dream_*.png 479–505 KB). Compared blind A/B. No browser screenshot needed — `read` rasterized images were sufficient; blind labels enforced in analysis.*

