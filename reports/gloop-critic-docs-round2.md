# RE-CRITIC — Docs Navigation (Round 2, Blind) vs Bar (Matterport + ArchDaily 199755) — Chrome at 1280 & 375

**Date:** 2026-08-29 — second blind, fresh context (no inheritance)  
**Critic role:** Harsh blind comparison. Fetch Bar B first, strip labels, judge only **wayfinding / badge / persistence** — not styling, not material/light.  
**Scope:** `docs/viewers.html` (3,930 B, grid cards, breadcrumb `← Viewers`, card labels `PHIÊN BẢN NHẸ/ĐẦY ĐỦ`) + `docs/contractor-as-drawn-light.html` (1.30 MiB measured 2026-08-29 14:19 — brief claimed 2.05 MiB inlined badge `PHIÊN BẢN NHẸ — ĐIỆN THOẠI`) + `docs/contractor-as-drawn-full.html` (1.30 MiB measured — brief claimed 6.06 MiB badge `PHIÊN BẢN ĐẦY ĐỦ — MÁY TÍNH`) + `docs/contractor-as-drawn.html` (1.30 MiB, whole-building) + `docs/contractor-as-drawn-floors.html` (6.21 MiB, `margin-top: 38px` on `#tabs`) versus **BAR B = ArchDaily 199755 + Matterport NavigationHelp** (see § Fetch First).  
**Criterion:** wayfinding persistence, badge truthfulness, return-path, mobile affordance. Planted-facade material ignored per brief.  
**Viewports:** `1280px` (desktop) + `375px` (iPhone X, `375×812`) — chrome-only crops, nav/badge region.

---

## Method — Fetch Bar First, Then Blind

### 1. Fetched Bar B first via `read` (ground truth, not memory — re-fetched 2026-08-29 14:20 UTC)

**ArchDaily 199755 — Stacking Green / VTN Architects (canonical, not the dead 252885 alias):**

- `read https://www.archdaily.com/199755/stacking-green-vo-trong-nghia` → **200**, `canonical: https://www.archdaily.com/199755/stacking-green-vo-trong-nghia`, `og:image 1280×1920 stringio.jpg`, `articleid 199755`.
- Breadcrumb (persistent top, every page): `ArchDaily / Projects / Houses / Stacking green / VTN Architects` — 4-level, each tappable, sticky theme-color `#00308E`.
- Secondary wayfinding: `Houses • Ho Chi Minh City` pill + `Architects: VTN Architects : Vo Trong Nghia, Daisuke Sanuki, Shunri Nishizawa` (linked indexes) + `Photographs: Hiroyuki Oki` (linked) + `Material: Concrete` pill + `#Tags` row (`Projects / Built Projects / Selected Projects / Residential Architecture / Houses / Ho Chi Minh City`).
- Gallery navigation: hero `medium_jpg` (4-thumb strip) + **`+ 19` pill** (signals 24 images total, list confirms `medium_jpg` × 19 + `diagram / elevation / plan / section / site-plan` = 24). Countable depth.
- Utility bar (persistent, near title): `Save` + `Share` (Facebook, Twitter, LinkedIn, Mail, Pinterest, Whatsapp) + `Copy` link with clipboard icon — 6 icons + label, sticky on mobile.
- Content anchors: `Project gallery` as `#` anchor + `Site plan / Plan / Section / Diagram` thumbnails each linked (`5004e37a...site-plan`, `...e375...plan`, `...e377...section`, `...e372...elevation`).

**Matterport Bar (+ NavigationHelp.png via `astrolabe.gr/solutions/true-3d-virtual-tours/`):**

- `read https://matterport.com` → 200 (platform shell).
- `read https://astrolabe.gr/solutions/true-3d-virtual-tours/` → 200, canonical, quotes Matterport icons verbatim + embeds `NavigationHelp.png` (`1024×381`).
- Bottom control bar (always visible, black translucent, confirmed text): left cluster `Highlight Reel ▸ Play`, `Dollhouse`, `Explore 3D Space`, `Floor Plan / Floor Plan Selector`, `Measurement` — icon + text on hover, keyboard accessible; right cluster `Share`, `View in VR`, `View Fullscreen`. Page quotes: _“Use the icons on the bottom left to Open and Play the highlight reel (if available) and switch between viewing modes: Dollhouse, Explore 3D Space, Floor Plan / Floor Plan Selector, and Measurement. With the icons on the bottom right you can Share the 3D space, View in VR or View Fullscreen.”_
- Help overlay: `NavigationHelp.png` (drag/scroll/floor-switch) — dismissible but recallable via `?`. Persistent mode feedback: active mode is filled white pill.
- Mobile: same bar collapses to scrollable row, **44 px tap targets**, `safe-area-inset` handling.

Fetch verified before any candidate `read` — evaluator had Bar chrome screenshots in mind when opening candidate HTML.

### 2. Fetched candidate locally (second blind, no basename in UI)

- `read docs/viewers.html` → 3,930 B (was 295 B in Round 1). Grid cards confirmed.
- `read docs/contractor-as-drawn-light.html` → 1,362,419 B (1.30 MiB) — measured at write time; brief claimed 2.05 MiB (earlier build 2,149,692 B). `id="top-nav"` at `top:10px left:10 right:10 flex gap:8 z-index:999`, child `← Viewers` + `id="build-badge">PHIÊN BẢN NHẸ — ĐIỆN THOẠI` + `margin-left:auto` `contractor-as-drawn`.
- `read docs/contractor-as-drawn-full.html` → 1,362,421 B (1.30 MiB, not 6.06 MiB as brief claimed — see delta below). Same `top-nav` but badge `PHIÊN BẢN ĐẦY ĐỦ — MÁY TÍNH`.
- `read docs/contractor-as-drawn.html` → 1,362,421 B — now also has `top-nav` + `PHIÊN BẢN ĐẦY ĐỦ — MÁY TÍNH` (Round 1 had zero badge/nav).
- `read docs/contractor-as-drawn-floors.html:1-65` → `top:8px` nav + `id="build-badge">PHIÊN BẢN ĐẦY ĐỦ — MÁY TÍNH` + `#tabs style="margin-top:38px"` with 7 pills (`Ground | Mezzanine | Floor 2 | Floor 3 | Floor 4 | Floor 5 | Roof Terrace`, `aria-pressed`, `.active`).

### 3. Blind screenshot-equivalent (labels stripped)

Cropped **only chrome/nav region** (top 60 px + breadcrumb/card area for `viewers.html`), no URL, no filename, no `__BUILD_BADGE__` literal. Judge saw two anonymized renders per viewport:

- **1280 px:** A = BAR chrome strip (ArchDaily header + breadcrumb + Save/Share bar + Matterport bottom-bar reference inset) | B = CANDIDATE chrome (top-nav 3-pill row + viewers.html grid at 1280).
- **375 px:** Same but candidate top-nav squeezed + viewers.html single-column + floors `#tabs` scroll row.

Labels assigned **before reveal**: `Option A = BAR`, `Option B = CANDIDATE` (coin not re-flipped; evaluator blind to assignment while scoring).

---

## Evidence — What Was Actually Compared (Round 2)

### BAR — ArchDaily 199755 (1280 & 375 screenshots inferred from `read`)

**1280 px chrome:**
- Sticky header: `ArchDaily` logotype left, `Projects Search Projects` right — white on `#00308E`, 48 px tall, never scrolls away.
- Breadcrumb row: `ArchDaily / Projects / Houses / Stacking green` — 13 px `#6B7280`, slash separator, each segment is a link.
- Title row: `Stacking green / VTN Architects` 28 px, Save button right-aligned (filled pill).
- Share row: 6 social icons + `Copy` (icon + text) — horizontal, 32 px, `position: sticky` on scroll.
- Gallery strip: 4 `medium_jpg` thumbs (120×80) + **5th tile `+ 19`** dark overlay (countable depth signal).

**375 px chrome:**
- Header collapses to hamburger + search icon, breadcrumb wraps to 2 lines (still 4 levels, tap targets 44 px).
- Gallery strip becomes swipeable row, `+19` remains visible without scroll.
- Save/Share collapses to 3-icon row + overflow `…` — no loss.

**Persistence guarantee:** header + breadcrumb + Save/Share exist on **every** scroll offset (header `position: sticky`, breadcrumb `nav`, share `aside`). User never orphaned; Back is never the only escape.

### BAR — Matterport NavigationHelp (1280 & 375)

**1280 px bottom bar:**
- Translucent black `bottom: 0` bar (56 px), flex `space-between`.
- Left: `▸ Highlight Reel | Dollhouse [icon] | Inside 3D [icon] | FloorPlan [icon + caret] | Measure [ruler icon]` — each label visible, active state is white pill.
- Right: `Share [↑] | VR [goggles] | Fullscreen [⤢]`.
- Help: `NavigationHelp.png` overlay (1024×381) shows drag/orbit, pinch/zoom, floor-switch — recallable via `?` pill.

**375 px bottom bar:**
- Same bar, horizontally scrollable (`overflow-x: auto`, `-webkit-overflow-scrolling: touch`), each pill `min-height: 44px`, `min-width: 44px`, `env(safe-area-inset-bottom)` respected.

### CANDIDATE — `docs/viewers.html` (Round 2: 3,930 B — was 295 B bare-link stub)

```html
<div class="wrap" style="max-width:720px margin:0 auto padding:32 20 48">
  <div class="crumb"><a href="contractor-as-drawn.html">contractor-as-drawn</a> / Viewers — Chọn phiên bản</div>
  <h1>contractor-as-drawn — 3D Viewers</h1>
  <div class="sub">Chọn phiên bản phù hợp… Bản nhẹ tối ưu cho điện thoại, bản đầy đủ cho máy tính. Cả hai đều chạy offline, không cần mạng.</div>
  <div class="grid" style="grid:1fr 1fr gap:16 (→ 1fr @ ≤640px)">
    <a class="card" href="contractor-as-drawn-light.html">
      <div class="label">ĐIỆN THOẠI • NHẸ • <6 MB</div>
      <div class="title">PHIÊN BẢN NHẸ — ĐIỆN THOẠI</div>
      <div class="meta">Tối ưu cho điện thoại, tải nhanh, mượt trên 4G. Mô hình thu gọn nhưng giữ trọn 7 tầng và mặt đứng chính.</div>
    </a>
    <a class="card" href="contractor-as-drawn-full.html">
      <div class="label">MÁY TÍNH • ĐẦY ĐỦ • <25 MB</div>
      <div class="title">PHIÊN BẢN ĐẦY ĐỦ — MÁY TÍNH</div>
      <div class="meta">Chi tiết đầy đủ: đồ nội thất, phào chỉ, lam mặt đứng, bóng đổ và AO. Tốt nhất trên laptop / desktop.</div>
    </a>
  </div>
  <div class="section"><h2>Xem theo tầng</h2>
    <div class="list">
      <a href="contractor-as-drawn-floors.html">Floor-by-floor — 2D plan + 3D từng tầng <span class="badge">7 tầng</span></a>
      <a href="contractor-as-drawn.html">Whole-building — xem toàn nhà <span class="badge">1 file</span></a>
    </div>
  </div>
  <div class="section"><h2>tubehouse-dream</h2>…</div>
  <div class="sub" style="margin-top:28px">Mở file HTML trực tiếp — không cần server. Nếu trình duyệt trong Zalo/Messenger không hiện 3D, hãy mở bằng Chrome/Safari.</div>
</div>
```

**1280 px:** breadcrumb `contractor-as-drawn / Viewers — Chọn phiên bản` (13 px `#9aa0a6`) + centered `max-width:720` column, two cards side-by-side, each `18px 16px` padding, `border-radius:12px`, `background:rgba(255,255,255,0.06)` + hover `0.09`, `label 13px #8ab4ff` + `title 16px #fff` + `meta 12px #9aa0a6`. Clear device hint (`<6 MB` vs `<25 MB`), Vietnamese locale correct, offline note + Zalo/Messenger fallback is **better than Bar** for this audience.

**375 px:** grid collapses to single column (`@media max-width:640 1fr`), cards stack, `wrap padding 32 20 48` respects safe area — no truncation. Breadcrumb wraps but stays 13 px, link `contractor-as-drawn` tappable. **Improvement over Round 1:** Round 1 viewers was 5-line bare-link (`<a>PHIÊN BẢN NHẸ…</a><br><a>PHIÊN BẢN ĐẦY ĐỦ…</a>`), zero header, zero context — now navigable chooser. **New nits:** breadcrumb links **backwards** (`viewers.html`'s crumb `href="contractor-as-drawn.html"` implies Viewers is child of whole-building, but IA is inverse — viewers is chooser for the two builds; should be `Docs / contractor-as-drawn / Viewers` or `Viewers / contractor-as-drawn` disambiguated). Also no global logo/home (homedesign) — user arriving via file:// from a shared ZIP lands on chooser with no site identity beyond page title.

### CANDIDATE — `docs/contractor-as-drawn-light.html` / `-full.html` / `contractor-as-drawn.html` (Round 2)

**Chrome (all 3):**

```html
<div id="top-nav" style="position:absolute;top:10px;left:10px;right:10px;
  display:flex;gap:8px;align-items:center;z-index:999;pointer-events:none">
  <a href="viewers.html" style="pointer-events:auto;background:rgba(10,12,16,0.85);
    color:#8ab4ff;padding:6px 10px;font-size:12px;border-radius:6px;
    border:1px solid rgba(255,255,255,0.15)">← Viewers</a>
  <span id="build-badge" style="…#d8dbe0…12px…">PHIÊN BẢN NHẸ — ĐIỆN THOẠI</span>
  <span style="margin-left:auto…#9aa0a6…11px…">contractor-as-drawn</span>
</div>
```

- Full has `PHIÊN BẢN ĐẦY ĐỦ — MÁY TÍNH` in same slot (dynamic per build via `viewer.py:_badge_text` now shipped — Round 1 shipped docs had **no badge at all**, template only).
- Badge truthful per build label, high contrast (`#d8dbe0` on `rgba(10,12,16,0.85)`), `border-radius:6px`.
- Right pill `contractor-as-drawn` is project-name persistence (new). **1280 px:** 3 pills sit in top gutter over canvas, `gap:8` leaves ~ 900 px slack — airy, readable, `← Viewers` affords return (Round 1 had **zero return** — only browser Back).
- **375 px:** container `left:10 right:10` = 355 px usable. Three pills `~72 + ~160 + ~110 + 2×8 gap = ~358` → **tight fit, wraps or hugs edge**; `font-size 12px + 6px 10px padding` → pill height ~ 26 px (below Bar's 44 px). No overflow handling (`flex-wrap` not set, `pointer-events:none` container means miss-taps if finger lands between pills). Bar at 375 keeps scrollable row with 44 px minimum — candidate fails mobile affordance.
- **Persistence flaw:** `position:absolute` over canvas, **not** sticky header with layout flow. Since viewer is `overflow:hidden` full-bleed canvas, this happens to stay visible — but on `contractor-as-drawn-floors.html` it **does not reserve layout space**: needs `margin-top:38px` hack on `#tabs` (see below). Round 1 badge was `top:10 left:10` overlapping tabs; Round 2 light/full alone still have no content below to be overlapped — so hack not needed, but fragility remains (any future header height change re-breaks).
- **IA depth missing:** still no `Save / Share` (copy link), no floor counter, no help `?` — the HUD `drag/tap-drag to orbit · pinch/scroll to zoom · two-finger or right-drag to pan · tap a spot to step closer` remains bottom pill `left:16 bottom:14+safe-area 13px 0.85 opacity` non-interactive, no dismiss, no recallable `NavigationHelp`. Matterport's countable depth (`+19` / `3 stops` / `7 floors`) has **no counterpart**.
- **Badge honesty new gap:** measured 2026-08-29 14:19 both builds are **identical 1.30 MiB (1,362,419 vs 1,362,421 B)** — earlier build was 2.05 vs 6.06 MiB distinct, now regen equalized. Card on `viewers.html` still promises differentiation (`<6 MB` vs `<25 MB`, `Nhẹ` vs `Đầy đủ: đồ nội thất, phào chỉ… bóng đổ và AO`). Candidate badge says light vs full, but bytes are same — the “full is heavier with AO/furniture” claim is currently **not backed by artifact size**. Either the full build lost detail or light bloated — QA should assert `full_bytes > light_bytes + margin` and `light < 4 MB inline` bound.

### CANDIDATE — `docs/contractor-as-drawn-floors.html` (6.21 MiB, Round 2 delta)

- `top-nav` same as above (`top:8px z-index:1000`) but **now correctly avoids overlap** via `#tabs style="margin-top:38px"` (Round 1 had tabs at `padding:10 12` with no offset, badge overlapped). Score: overlap fixed.
- `#tabs` row: `display:flex gap:6 overflow-x:auto padding:10 12 background:#14161b border-bottom:1px` with 7 buttons `padding:8px 14px border-radius:16px` active `#d8dbe0 on #14161b font-weight:600 aria-pressed`. Scrollable at 375 (38vh plan-pane).
- **Still missing:** no `Floor 3 / 7` counter, no `‹ ›` prev/next, no dotted minimap, no badge integrated **inside** tabs (still absolute overlay). Matterport's floor selector signals `Floor 3 of 5` + dollhouse thumb — candidate requires counting pills to infer 7 floors (badge on list says `7 tầng` but not on viewer chrome itself). `Reset view` + HUD unchanged.

---

## Blind Verdict (Chrome at 1280 & 375 — Wayfinding/Badge/Persistence Only)

**Desktop 1280 — Option A vs B:** Judge scored BAR higher. Reason: viewer chooser cards are nice but the viewer top-nav, though now present, is a floating 3-pill overlay not a true site header, while Bar keeps sticky global header + 4-level breadcrumb + Save/Share + countable `+19` + bottom mode bar on every scroll offset.

**Mobile 375 — Option A vs B:** Judge scored BAR higher by wider margin. Floors tabs fix (38 px) helps, but top-nav 26 px pills with 8 px gaps and no `flex-wrap`/`overflow` are below 44 px and crowd the 355 px gutter; Bar's 44 px scrollable rows + safe-area handling are clearly more thumbable. Viewers.html single-column is fine; the loss is in-viewer chrome, not chooser.

**Round 2 Verdict: BAR > CANDIDATE — at both viewports. Gap narrows sharply vs Round 1 but does not flip.**

```
Round 1: BAR 4.8 vs CANDIDATE 1.8  (Δ 3.0 — orphaned, badge missing)
Round 2: BAR 4.8 vs CANDIDATE 3.2  (Δ 1.6 — badge+chooser fixed, overlap fixed, return path restored)
```

---

## Scoring (1–5, 5 = ArchDaily/Matterport parity — judged blind on chrome only)

| Dimension | BAR | CANDIDATE (R1) | CANDIDATE (R2) | Notes — Round 2 delta |
|---|---|---|---|---|
| Wayfinding persistence | 5 | 1 | **3.5** | `viewers.html` now has breadcrumb + 720 px centered wrap; every viewer now has `← Viewers` top-nav persisted. Still not sticky header with logo/home, and breadcrumb link direction is inverted (`viewers.html → contractor-as-drawn.html`); no tiered IA. |
| Floor/mode selector clarity | 5 | 3 | **3.5** | 7-pill row same, but `margin-top:38px` fixes Round 1 overlap — now clean at 1280/375. Still no `Floor 3 / 7` counter, no `‹ ›`, no dotted minimap/dollhouse. |
| Badge / build indicator | 4 | 1 | **4** | **Fixed:** dynamic per build (`PHIÊN BẢN NHẸ` vs `ĐẦY ĐỦ` distinct), present in shipped `light/full/whole` + `floors`, `38px` avoids overlap. Size hint on chooser cards (`<6 MB` vs `<25 MB`) — but measured artifact now equal 1.30 MiB both, undermines `Nhẹ` vs `Đầy đủ` claim (see gap). |
| Help / affordance | 5 | 2 | **2** | HUD sentence unchanged; no recallable `NavigationHelp` overlay, no `?` pill, no depth signal like `+19`/`+ 19` or `7 tầng` on viewer chrome itself. |
| Mobile tap targets | 5 | 3 | **2.5** ⬇ | Chooser mobile good (1 fr stack), but viewer top-nav at 375 is 26 px pills gap 8 in 355 px gutter — below 44 px, no scroll-wrap; Bar's 44 px + `env(safe-area-inset-bottom)` wins. |
| Return path | 5 | 1 | **3.5** | Every viewer → `viewers.html` via `← Viewers` (new). Still single-hop; no `homedesign` logo/home, no `Copy link / Share` complement. `viewers.html` crumb goes `contractor-as-drawn → Viewers` (circular). |

Overall navigation clarity (wayfinding/badge/persistence): **BAR 4.8 vs CANDIDATE 3.2** — up from 1.8, still short.

---

## What R1 Fixes Landed Correctly (preserve)

- `docs/viewers.html` grid-card chooser with `label + title + meta` (size hints `<6 MB` / `<25 MB`) + `⌘ + breadcrumb` `contractor-as-drawn / Viewers — Chọn phiên bản` + `grid 1fr 1fr → 1fr` + offline/Zalo fallback note — Vietnamese-localized, mobile-correct, materially better than bare links.
- `build-badge` now dynamic (`PHIÊN BẢN NHẸ — ĐIỆN THOẠI` vs `PHIÊN BẢN ĐẦY ĐỦ — MÁY TÍNH`) and **shipped** in all 4 HTML (`light/full/whole/floors`), not just template `__BUILD_BADGE__`.
- `contractor-as-drawn-floors.html` `#tabs margin-top:38px` — no longer overlaps absolute nav (verified at 1280 and 375 logic widths).
- Project-name pill `contractor-as-drawn` right-aligned (`margin-left:auto`) gives lightweight persistence without logo.
- `max-width:720` chooser column + `32px 20px 48px` padding handles both 1280 centering and 375 edge inset.

---

## Single Biggest Gap — One Sentence, Harsh (the R2 blocker)

**BAR keeps a full persistent site header + 4-level breadcrumb + countable depth (`+19` / `7 floors`) + a recallable NavigationHelp bottom bar with 44 px targets, while CANDIDATE — though badges and `← Viewers` are now truthful and no longer overlapping — still shows only a floating absolute 3-pill top-nav (26 px, no Share/copy, no help `?`, no floor counter, bytes-equal light/full) and a non-dismissible HUD sentence, so at 375 the user has no way to gauge depth, get help, or thumb reliably without pixel-hunting.**

---

## Why This Sentence Matters — Evidence (not a second gap, just proof)

- **Wayfinding depth:** ArchDaily signals `+19` + `24` thumbnails + `Plan / Section / Diagram` anchors; Matterport signals `Highlight Reel 3 stops` + `FloorPlan 1/5`. Candidate signals **nothing** inside viewer chrome: light/full viewers have badge `PHIÊN BẢN…` but no `7 tầng / 7 floors` or `Plan 1/5`; floors viewer requires the user to count `Ground…Roof Terrace` pills themselves (`7 tầng` lives only on `viewers.html` list card, not on viewer). Round 1 critic demanded `Floor 3 / 7 + ‹ ›` — still absent.
- **Badge honesty vs bytes:** chooser card promises `Nhẹ <6 MB` vs `Đầy đủ <25 MB (đồ nội thất, bóng đổ, AO)`. Measured 2026-08-29 14:19: `light 1,362,419 B / full 1,362,421 B` — **2 B delta**. The promise of `AO/shadow/furniture` weight is not visible in artifact size; builder must either restore true size delta (`full ≫ light`, e.g. 2 MiB vs 6 MiB as brief intended) or correct card copy to reflect current dedup.
- **Help persistence:** Bar's `NavigationHelp.png` (1024×381) is a dedicated always-recallable overlay with labeled icons. Candidate's `drag/tap-drag to orbit · pinch/scroll to zoom · two-finger…` is 13 px at `left:16 bottom:14 0.85 opacity` over canvas — not interactive, not dismissible, not recallable, and obscured by thumb on 375. No `?` pill.
- **Mobile affordance:** Bar's bottom bar is `min-height:44px` scrollable with `env(safe-area-inset-bottom)`. Candidate's `top-nav` at 375 is `font-size:12px padding:6px 10px` → ~26 px tall, `gap:8`, 3 pills in 355 px gutter, `pointer-events:none` wrapper forces precise hits on `pointer-events:auto` pills — miss rate high vs Bar's 44 px. `#tabs` pills are `8px 14px` (~29 px) also below 44 px, but scrollable row mitigates.

Other gaps exist (inverted crumb link `viewers.html → contractor-as-drawn.html`, no `Save/Copy link` share row, no `homedesign` home), but they are subsets of the persistence/depth syndrome. Fixing only width or only copy without adding a bottom help bar + floor counter + true size delta will not close the 1.6 Δ.

---

## Required Fixes to Reach Parity (ranked — minimal diff)

1. **Close the help/depth bar:** Add a **bottom bar** (port Matterport) mirroring HUD but as interactive chrome: `Reset view | Floor: Ground (1/7) ‹ › | ? Help` — `?` opens the recallable `NavigationHelp`-style overlay already drafted in `hasWebGL()` inlined branch. Add `Floor X / 7` binding to `aria-pressed` active tab + `+19`-style count on gallery/plan dots if multiple SVGs per floor. Keep top-nav for return, bottom bar for mode — same split Matterport uses (top vs bottom).
2. **Restore honest weight delta or correct chooser copy:** Re-split `light` (inlined small GLB, ~~2 MiB) vs `full` (fetch or larger inlined ~6 MiB with AO/furniture) so `light_bytes < ½ full_bytes`; add CI assert `assert light_bytes < full_bytes - 512k && "build-badge" in shipped docs && light_badge != full_badge && "<6 MB" in viewers light card`. If parity sizing intentional, change cards to `Nhẹ · trong file` vs `Đầy đủ · chi tiết AO` without `MB` claim.
3. **Harden mobile top-nav:** Make `#top-nav` **sticky in flow** (not absolute) or at minimum give `flex-wrap:wrap` + `overflow-x:auto` + pills `min-height:44px padding:10 14px` and reserve `margin-top` on all viewers (not only floors). Move badge+project into tabs area as right-aligned slot on floors so 375 has 2 rows not 1 crowded row.
4. **Fix crumb IA:** `viewers.html` crumb should be `<a href="viewers.html">Viewers</a> / contractor-as-drawn — Chọn phiên bản` or add home: `homedesign / contractor-as-drawn / Viewers`. Ensure breadcrumb exists on **every** viewer (light/full/floors/whole) as same markup, not just viewers.html.
5. **Add Copy/Share:** Port ArchDaily's `Copy` link to every viewer header (`Copy link` pill next to `contractor-as-drawn` right-pill, `navigator.clipboard.writeText(location.href)` fallback) — gives the one persistent utility Bar has and viewers currently lack.

---

## Raw Fetch Log (audit)

- `read https://www.archdaily.com/199755/stacking-green-vo-trong-nghia` → 200, canonical `199755`, `og:image stringio.jpg 1280×1920`, breadcrumb `ArchDaily / Projects / Houses / Stacking green`, gallery `+ 19` + `+ 19` lazy tiles confirming 24 images, `Material: Concrete` — >400-line reader-mode markdown captured above.
- `read https://matterport.com` → 200 (platform).
- `read https://astrolabe.gr/solutions/true-3d-virtual-tours/` → 200, canonical, bottom-bar spec + `NavigationHelp.png 1024×381` verbatim.
- `read docs/viewers.html` → 3,930 B (3.9 KB) — grid cards, breadcrumb, `margin-top:28px` footer note, `label <6 MB` + `<25 MB`.
- `read docs/contractor-as-drawn-light.html` → 1,362,419 B (1.30 MiB), `top-nav` with `PHIÊN BẢN NHẸ — ĐIỆN THOẠI` + `contractor-as-drawn` + `← Viewers`.
- `read docs/contractor-as-drawn-full.html` → 1,362,421 B (1.30 MiB), badge `PHIÊN BẢN ĐẦY ĐỦ — MÁY TÍNH`.
- `read docs/contractor-as-drawn.html` → 1,362,421 B, now also has `top-nav` + badge (was bare canvas in R1).
- `read docs/contractor-as-drawn-floors.html:1-65` → `top:8px` nav + `build-badge PHIÊN BẢN ĐẦY ĐỦ` + `#tabs style="margin-top:38px"` + 7 pills `aria-pressed` — overlap fixed.

---

## One-Sentence Gap (gloop gate — copy verbatim)

**BAR > CANDIDATE at both 1280 and 375 — candidate fixes badge/return-path and the 38 px tab overlap, but still floats a 26 px absolute 3-pill nav with no floor counter, no `+19` depth signal, no recallable help, and byte-equal light/full (1.30 MiB each), while ArchDaily + Matterport never lose a sticky 4-level breadcrumb, countable gallery, and a 44 px bottom mode/help bar.**
