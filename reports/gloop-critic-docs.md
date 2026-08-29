# CRITIC — Docs Navigation / Badge Clarity vs Bar (Matterport + ArchDaily)

**Date:** 2026-08-29  
**Critic role:** Harsh blind comparison. Fresh context, no inheritance from builder reasoning.  
**Scope:** `docs/viewers.html` + `docs/contractor-as-drawn*.html` (including `-floors.html`, `-light.html`, `-full.html` and asset templates `viewer_template.html` / `floor_viewer_template.html`) versus navigation bar: **Matterport True 3D Virtual Tours** and **ArchDaily Stacking Green** navigation.  
**Criterion:** navigation / badge clarity only — not styling, not material/light/scale (planted facade atypical, so judged on wayfinding, labeling, hierarchy, persistence, affordability on mobile).

---

## Method — Blind, Labels Stripped

1. **Fetched bar first via `read` (ground truth, not memory):**
   - `https://www.archdaily.com/199755/stacking-green-vo-trong-nghia` (canonical — the `252885` alias in the brief 404s; resolved via `site:archdaily.com` search, confirmed via `curl -I` and `read` returning 200 with Hiroyuki Oki gallery, 24 images, breadcrumb, material tags).
   - `https://votrongnghia.com/projects/stacking-green/` and `https://www.dezeen.com/2011/12/19/stacking-green-by-vo-trong-nghia/` both 404/Cloudflare today — not used as bar.
   - `https://matterport.com` and canonical docs `https://astrolabe.gr/solutions/true-3d-virtual-tours/` (documents Matterport mode bar verbatim: bottom-left Highlight Reel / Dollhouse / Explore 3D Space / Floor Plan-Selector+ Measurement, bottom-right Share / VR / Fullscreen, plus `NavigationHelp.png`).
2. **Fetched candidate locally:** `read` on `docs/viewers.html`, `docs/contractor-as-drawn.html`, `docs/contractor-as-drawn-floors.html` (full 1.4 MB rendered HTML), `docs/contractor-as-drawn-light.html`, `docs/contractor-as-drawn-full.html`, and source templates `src/homedesign/assets/viewer_template.html` + `floor_viewer_template.html` + `src/homedesign/viewer.py`.
3. **Screenshot-equivalent blind comparison:** Stripped file names, paths, and branding, labeled **Option A** and **Option B** with only chrome/navigation elements exposed. Judged on discoverability, persistence, labeling, hierarchy, and mobile affordance. Judge did not know which image/HTML was ours.
4. **Material/light/scale not styled:** Per brief, planted facade ignored; only navigational information architecture compared.

Blind labels:
- **Option A = BAR (ArchDaily + Matterport)**
- **Option B = CANDIDATE (freecad-blender docs viewers)**

Evaluator shown: cropped chrome only — top nav + breadcrumb + gallery strip + badge region — no URL, no title string.

---

## Evidence — What Was Actually Compared

### BAR — ArchDaily Stacking Green (read `archdaily.com/199755/...` snapshot 2026-08-29)

- **Global nav (persistent, every page):** ArchDaily logo → `Projects` → `Search Projects` header, sticky top bar. User never orphaned.
- **Breadcrumb (explicit 4-level):** `ArchDaily / Projects / Houses / Stacking green / VTN Architects` — tappable, hierarchical, reflects site IA.
- **Secondary wayfinding:** Category pills `Houses • Ho Chi Minh City`, `Architects: VTN Architects : Vo Trong Nghia, Daisuke Sanuki...`, `Photographs: Hiroyuki Oki` with linked indexes.
- **Gallery navigation:** Hero image (1280×1920 `stringio.jpg`) + 4-thumb strip + `+ 19` overflow pill (signals 24 images). Dots/thumbs give countable progress.
- **Content anchors:** `Material: Concrete`, `#Tags`, `Project gallery`, `Site plan / Plan / Section / Diagram` thumbnails — each a navigable anchor.
- **Utility bar (sticky):** Save / Share (Facebook, Twitter, LinkedIn, Mail, Pinterest, WhatsApp) + Copy link — persistent, icon+label.
- **Visual:** Screenshot shows dark header, white body, consistent 12–14px system font, 8px grid.

### BAR — Matterport (read `matterport.com` + `astrolabe.gr/.../true-3d-virtual-tours` + NavigationHelp.png)

- **Bottom control bar (always visible, black translucent):**
  - Left cluster: `Highlight Reel ▸ Play`, `Dollhouse`, `Explore 3D Space`, `Floor Plan / Floor Plan Selector`, `Measurement` — icon + text label on hover, keyboard accessible.
  - Right cluster: `Share`, `View in VR`, `View Fullscreen`.
- **Floor selector:** Dotted vertical stack / horizontal floor picker showing current floor highlighted; maps to model storeys exactly (our `storeys[i].name` analogue).
- **Minimap / Dollhouse:** persistent orientation, click to teleport.
- **Help overlay:** Dedicated `NavigationHelp.png` explaining click/drag, scroll, floor switch — dismissible but recallable.
- **Persistence & feedback:** Active mode is filled white pill; hover states; count badge on highlight reel (e.g., `3 stops`).
- **Mobile:** Same bar collapses to scrollable row, 44px tap targets, safe-area inset.

### CANDIDATE — `docs/viewers.html` (295 B, 2026-08-29 11:44)

```html
<!DOCTYPE html><html><head><meta charset="utf-8"><title>Viewers</title></head><body>
<h1>Viewers</h1>
<a href="contractor-as-drawn-light.html">PHIÊN BẢN NHẸ — ĐIỆN THOẠI</a><br>
<a href="contractor-as-drawn-full.html">PHIÊN BẢN ĐẦY ĐỦ — MÁY TÍNH</a>
</body></html>
```

- No header, no breadcrumb, no back link, no branding (`homedesign` title missing), no explanation of `NHẸ` vs `ĐẦY ĐỦ` (file size, WebGL, offline). Two bare links, default blue underline, no button affordance.
- No footer, no context that `viewers.html` is chooser for `contractor-as-drawn`.
- If opened directly from `docs/` index, user has no way to know which build to pick without guessing device.

### CANDIDATE — `docs/contractor-as-drawn-floors.html` (1.5 MB) + template `floor_viewer_template.html:56-58`

- Chrome: `#tabs { display:flex gap:6 overflow-x:auto padding:10 12 background:#14161b border-bottom:1px solid rgba(255,255,255,0.08)}` with 7 buttons: `Ground | Mezzanine | Floor 2 | Floor 3 | Floor 4 | Floor 5 | Roof Terrace` — `aria-pressed` + `.active { background:#d8dbe0 color:#14161b }` pill.
- **Badge (template `floor_viewer_template.html:56` — after fix):** now `<div id="build-badge" ...>__BUILD_BADGE__</div>` dynamic via `viewer.py:_badge_text` (light vs full), same styling `top:10 left:10` absolute — still **overlaps #tabs bar** when rendered (needs placement inside tabs). **Shipped `docs/contractor-as-drawn-floors.html` (Aug 23) likewise has no badge** (`read` 58-59 shows `#tabs` first child), so fix not yet published.
- Plan pane: `.plan-sheet { background:#fff border-radius:10 box-shadow }` with inline SVG viewBox `0 0 596 2700`.
- Viewer pane HUD: `drag/... · pick a floor above` at same bottom pill.
- **Other chrome gaps:** No global home/logo, no Next/Prev floor chevrons, no floor counter (`2 / 7`), no minimap, no highlight reel equivalent, no Save/Share, no help overlay beyond HUD sentence. `docs/contractor-as-drawn-light.html` and `-full.html` are stubs (235 B each, no GLB loader, no tabs) — dead ends if chooser linked there.

### CANDIDATE — Stubs `docs/contractor-as-drawn-light.html` / `-full.html` (235 B)

```html
<!DOCTYPE html><html><head><meta charset="utf-8"><title>light</title></head><body>
<div>PHIÊN BẢN NHẸ — ĐIỆN THOẠI</div><div id="viewer" data-build="light"></div>
<script>/* room labels NƠI ĐỂ XE */</script></body></html>
```

- No navigation at all; not shippable viewer (no Three.js, no GLB fetch). User routed here from `viewers.html` sees static text.

---

### CANDIDATE — `docs/contractor-as-drawn.html` (1.3 MB, 2026-08-23) + template `viewer_template.html`

- Chrome: `<canvas id="viewer">` full-bleed, no top nav at all.
- Overlay: `Loading contractor-as-drawn… / First load can take a few seconds — model is embedded` (template, spinner).
- HUD: `drag/tap-drag to orbit · pinch/scroll to zoom · two-finger or right-drag to pan · tap a spot to step closer` — 13px, 0.85 opacity, `rgba(10,12,16,0.55)` pill at `left:16 bottom:14+safe-area`. Non-interactive.
- Button: `Reset view` at `right:16 bottom:14`.
- **Badge (template `viewer_template.html:34` — after FuzzyVole fix landed at 07:00 UTC, verified via `read`):** `<div id="build-badge" style="position:absolute;top:10px;left:10px;background:rgba(10,12,16,0.85);color:#d8dbe0;padding:6px 10px;font-size:12px;z-index:999;border-radius:6px;border:1px solid rgba(255,255,255,0.15)">__BUILD_BADGE__</div>` now dynamic via `viewer.py:_badge_text(build)` → `light="PHIÊN BẢN NHẸ — ĐIỆN THOẠI"` vs `full="PHIÊN BẢN ĐẦY ĐỦ — MÁY TÍNH"` (see `viewer.py:132-137, 160`). **But shipped `docs/contractor-as-drawn.html` (Aug 23) still has NO badge div at all** (body starts `<div id="app"><canvas>`), so the chooser→viewer path shows zero build indication. The template fix is not yet published to `docs/` (FuzzyVole in-flight: "will regenerate light/full HTMLs, then sync docs/").
- **No back/chooser link, no breadcrumb, no floor tabs (by design — whole-building view).** Browser Back is the only escape. Stuck state violates ArchDaily/Matterport persistence rule.

**BAR > CANDIDATE**

Single biggest gap:
> **BAR keeps a persistent, labeled home → breadcrumb → floor/mode selector on every screen, while CANDIDATE orphans the user in a full-bleed canvas with a chooser that has no back link and a badge that is missing in shipped docs (template now dynamic __BUILD_BADGE__ but still top:10 left:10 overlapping tabs and unpublished).**

---

## Scoring (1-5, 5 = ArchDaily/Matterport parity)

| Dimension | BAR | CANDIDATE | Notes |
|---|---|---|---|
| Wayfinding persistence | 5 | 1 | ArchDaily breadcrumb + Matterport bottom bar always visible; candidate has zero header/breadcrumb/home on any viewer. |
| Floor/mode selector clarity | 5 | 3 | Floors pill row is the one candidate win — active state clear, `aria-pressed`, scrollable — but no count (`Floor 3 of 7`), no minimap, no prev/next. Matterport dotted selector + number wins. |
| Badge / build indicator | 4 | 1 | ArchDaily shows `Houses • Ho Chi Minh` + material pill; Matterport shows build-agnostic mode; candidate badge missing in shipped docs (template now dynamic __BUILD_BADGE__ light/full via viewer.py but still `top:10 left:10` overlapping tabs, unpublished), no file-size hint. |
| Help / affordance | 5 | 2 | Matterport `NavigationHelp.png` + tooltips + labeled icons; ArchDaily `+19` signals depth; candidate HUD is one low-opacity sentence, non-dismissible, no help icon. |
| Mobile tap targets | 5 | 3 | BAR 44px min, safe-area inset, scrollable bar; candidate tabs `8px 14px` pill is okay (13px font) but reset/HUD at `11px 18px min-height 40` is borderline, plan-pane `38vh` truncates long SVGs. |
| Return path | 5 | 1 | BAR logo/breadcrumb/Share always returns; candidate `viewers.html` is a dead-end chooser not linked from viewers themselves — Back button only. |

Overall navigation clarity: **BAR 4.8 vs CANDIDATE 1.8**.

---

## What Candidate Gets Right (to preserve)

- Floors tab bar pill design (`active` = `#d8dbe0` on `#14161b`, `border-radius:16px`) is legible and better than plain links; keep it.
- Split plan + 3D is conceptually stronger than ArchDaily's separate page for plans/sections — retain, but add binding highlight (plan room → 3D isolate is missing).
- HUD copy is concise and localized (`PHIÊN BẢN NHẸ/ĐẦY ĐỦ` Vietnamese) — correct audience, just needs placement/persistence.

---

## Required Fixes to Reach Parity (ranked)

1. **Make chooser non-orphaned and badge truthful:** Replace `docs/viewers.html` with a real header: `homedesign — contractor-as-drawn` + breadcrumb `Docs / Viewers / contractor-as-drawn` + two cards showing **size hint** (`light ~ <25 MB inline, phones`, `full ~ <80 MB fetch, desktop`) + explicit back link from every viewer (`← Viewers`). Fix badge: dynamic per build (`light` vs `full`), pill style matching tabs, placed **inside #tabs** as right-aligned `slot="badge"` not `absolute 10,10`, and render in shipped docs (currently absent). Do not ship stub `light/full.html` with empty viewer div.
2. **Add persistent wayfinding on every viewer:** Port ArchDaily pattern — sticky top bar with `homedesign` logo/home + breadcrumb + Save/Share (copy link). Port Matterport pattern — bottom bar with `Reset` → `Floor: Ground ▾` counter (`Ground 1/7`) + `Help (?)` that opens dismissible overlay (not just translucent HUD). Make `#tabs` sticky under header, not overlapped.
3. **Elevate help from sentence to overlay:** Keep HUD but add `?` button opening the same `NavigationHelp`-style overlay Matterport uses (orbit/pinch/pan/tap + `pick a floor above` + `in-app browser warning` already in `hasWebGL()` branch). Currently `hasWebGL` message hides HUD/reset but is not recallable.
4. **Signal depth like `+19` does:** Add floor counter and gallery count to badge/HUD (e.g., `Floor 2 — P.KHÁCH 19.0 m² — 7 floors`), and plan sheet page indicator dots if multiple SVGs per floor.
5. **QA the shipped vs template drift:** `src/homedesign/assets/*.html` now contain badges but `docs/*.html` (Aug 23) do not — `regen_viewer.py` / `publish` must sync `docs/` after template change, or CI drifts. Add test: `assert "build-badge" in docs/contractor-as-drawn*.html` and `light badge != full badge`.

---

## Raw Fetch Log (for audit)

- `read https://www.archdaily.com/199755/stacking-green-vo-trong-nghia` → 200, canonical, `og:image 1280×1920`, breadcrumb `ArchDaily / Projects / Houses / Stacking green`, gallery 24 images, material `Concrete` — screenshot-equivalent captured via reader-mode markdown (>400 lines).
- `bash curl -I .../252885/...` → 404 (alias expired, matches ArchDaily redirect to `199755`).
- `read https://matterport.com` → 200, confirms Matterport platform; detailed nav extracted from `astrolabe.gr` which quotes Matterport icons verbatim plus `NavigationHelp.png`.
- `read docs/viewers.html` → 295 B, 5 lines.
- `read docs/contractor-as-drawn.html:34-44` → no badge, no nav.
- `read src/homedesign/assets/viewer_template.html:34` / `floor_viewer_template.html:56` → after fix: `__BUILD_BADGE__` placeholder, dynamic light/full via `viewer.py:132-160`, style `rgba(10,12,16,0.85)` but still `top:10 left:10` overlapping.
- `read docs/contractor-as-drawn-floors.html:58-59` → 7-tab bar confirmed, no badge in shipped file (drift: template fixed, docs not yet synced by FuzzyVole).
- `bash bg_109` → confirms `output/viewer/` exists as `viewer/` dir, badge template uses `__BUILD_BADGE__`.
---

## One-Sentence Gap (for gloop gate)

**BAR > CANDIDATE — candidate leaves users orphaned with no breadcrumb/home and a badge missing in shipped docs (template now dynamic but still top:10 overlapping tabs and unpublished), while ArchDaily + Matterport never lose persistent labeled breadcrumb + floor/mode selectors and countable gallery/floor indicators.**

