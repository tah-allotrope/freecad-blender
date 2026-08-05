---
title: "homedesign — Second Pass: Camera Truth, Render Economics, and the Deliverables an Architect Actually Asks For"
date: "2026-08-04"
type: "brainstorm"
depth: "deep"
source_request: "Thoroughly analyze this project's current state, codebase, documentation and architecture; brainstorm what improvements, features, refactors, architectural changes or optimizations would take it to the next level."
slug: "homedesign-second-pass"
mode: "unattended (no interview — recommended answers adopted and recorded under Assumptions Adopted)"
supersedes_context: "research/2026-07-30-homedesign-next-level-brainstorm.md (its Sprints 1–3 shipped as plans/2026-07-30-homedesign-correctness-and-delivery-plan.md, 88/88)"
---

# Brainstorm: homedesign — Second Pass

## Problem & Why Now

The last sprint closed 88/88 items across six phases and left the repo in genuinely
good shape: 90 tests pass in 6.5 s, `ruff check src tests` is clean, the skill-mirror
CI gate is green, stairs are Blondel-compliant, floor voids exist, openings can be
positioned and are overlap-checked, a validation rule registry runs on every compile,
EEVEE gives a 17 s preview loop, and the PDF dropped from 27 MB of HTML to 192 KB.

So the obvious defects are gone. That makes this the moment to check the thing the
last pass could not check about itself: **does the tool's output actually depict the
building it compiled?**

It does not. This session rebuilt `spec/examples/tubehouse-mini.json` from current
`HEAD` and looked at the pixels. The "exterior" render is a featureless white wall
with the building cropped off the top and bottom of the frame. The "interior" render
is a photograph of the *outside* of the house, taken from 5.26 m out on the lawn.
Both renders are produced by the analytic camera-fit module that PHASE-05 added
specifically to fix framing — and all 90 tests pass on them, including the dedicated
framing regression test.

That is the theme of this brainstorm: the pipeline is now correct about geometry and
wrong about **depiction** — the renders, the shipped PDF, and the warning channel all
confidently present something other than what the compiler produced. Every claim below
was verified this session against the code, a fresh build, the compiled model JSON, or
arithmetic reproduced in a script.

## Current State

- **~3,640 LOC Python** (`src/homedesign/` 3,364 + orphaned `src/ifc_export_utils.py`
  276), split pure/testable vs. `blender/` bpy-only. The separation held up well
  under six phases of change and is still the repo's best structural asset.
- **Tests**: 12 files, **90 tests, 6.47 s, all green**. Still ~zero coverage of the
  ~800 LOC under `blender/`; the one Blender-touching test (`test_framing.py`) reads
  a PNG produced by a *previous* run and skips if absent.
- **Packaging**: `pyproject.toml` with a `dev` extra, ruff pinned, GitHub Actions
  running lint + tests + skill-sync on every push. No console script.
- **Delivery**: per-storey SVG + DXF (door swings, window symbols, north arrow, scale
  bar, title block), EEVEE preview / Cycles final PNG gallery, 17-page A3 PDF brief
  with room schedule, opening schedule and quantity take-off.
- **Hardware reality, unchanged**: no Cycles GPU backend. The last final gallery cost
  **11.3 h**. Blender is **4.1.1** (build date 2024-04-15) — legacy EEVEE, no EEVEE
  Next raytracing.

### Evidence gathered this session

| Check | Result |
|---|---|
| `python -m pytest tests -q` | **90 passed in 6.47s** |
| `ruff check src tests` / `python scripts/sync_skill.py --check` | clean / `ok: skill copies match` |
| Fresh `homedesign build spec/examples/tubehouse-mini.json` | succeeds, **17.0 s** |
| Visual check of the fresh `tubehouse-mini_exterior.png` | **blank wall, building cropped top and bottom** |
| Visual check of the fresh `tubehouse-mini_interior.png` | **exterior of the house on a lawn** |
| `test_tubehouse_mini_exterior_framed` against that render | **PASSED** |
| Front camera: distance obtained vs. needed | **4.69 m vs. 15.90 m → facade overflows the frame 3.4×** |
| Room cameras inside their own room (`tubehouse-mini`) | **0 of 6** (`living` camera sits at y = −5.26 m; room spans y ∈ [0, 5]) |
| Warnings emitted by `compile`, all four specs | **63 / 24 / 23 / 14 — 100% `wall_outside_plot`, no other code ever fires** |
| `output/pdf/tubehouse-dream-brief.pdf` (Aug 1 16:52) | assembled from Aug-1 plans + **Jul-6 renders** (pre-stairs, pre-void, pre-camera) |
| `src/ifc_export_utils.py` | 276 LOC, zero importers, `ifcopenshell` no longer a dependency → **cannot run** |
| `AGENTS.md` "Start Here" → `plans/home-design-to-architect-workflow.md` | that file's own frontmatter says **`status: superseded`**, describes the deleted FreeCAD pipeline |

---

## Findings, Ranked

### Tier 0 — The renders do not show the building

**T0-1 — `camera_fit.fit_distance` has a sign error on the depth term, and every unit
test is blind to it.**
`camera_fit.py:62-63`:

```python
d_x = abs(_dot(v, right)) / tan_x + _dot(v, forward)
d_y = abs(_dot(v, up))    / tan_y + _dot(v, forward)
```

The camera is placed at `centre - dist * forward`, so the camera-to-corner distance
along the view axis is `dist + dot(v, forward)`. The constraint
`|lateral| <= tan * (dist + dot(v, f))` rearranges to
`dist >= |lateral|/tan - dot(v, f)` — **minus**, not plus. The code pulls back *more*
for corners that are already farther away and *less* for the near corners that
actually bind.

Why no test caught it: all four `fit_distance` tests
(`tests/test_camera_fit.py:10-45`) fit a box centred exactly on the `centre` argument.
For a symmetric box the two signs select different binding corners but return the
*identical* maximum, so the bug is mathematically invisible to every test in the
suite. It only manifests when `centre` is not the box's centre — which is precisely
what `_build_exterior_front_camera` does: it fits `facade_bbox` (a zero-depth box at
`y = 0`) while passing the plot **centroid** (mid-depth) as both the fit centre and
the camera anchor.

Reproduced numerically on `tubehouse-mini` (4 × 12 m plot, 9.2 m tall, 35 mm lens):

```
facade bbox      ((0,0,0), (4.0, 0.0, 9.2))
centre passed    (2.0, 6.0, 4.6)      <-- 6 m behind the facade it is fitting
fit_distance     10.693
camera y         -4.693  -> real camera-to-facade distance 4.69 m
distance needed  15.90 m
=> facade overflows the frame by 3.4x
```

Flipping the sign yields `dist = 23.7 m`, camera at `y = -17.7`, i.e. 17.7 m from the
facade against 15.9 m required — correct with margin to spare. **One character fixes
the exterior camera.** (Passing the centroid instead of the facade centre is then
merely wasteful rather than wrong; it is still worth cleaning up, because it is what
hid the sign error in the first place.)

**T0-2 — Every interior camera is placed outside the building. The math is right; the
strategy is impossible.**
`_build_room_camera` (`build_scene.py:222-254`) computes a correct fit distance and
then places the camera at `min_y - dist` — *outside the near wall*. For a 4 × 5 m
living room at 20 mm, the fit needs 5.26 m of pull-back, so the camera lands 5.26 m
beyond the wall, on the lawn. Measured across `tubehouse-mini`, **0 of 6 room cameras
are inside their room**; the fresh `_interior.png` is the resulting picture of a blank
exterior wall. Note this one is *not* fixed by T0-1 — the room bbox is centred on the
passed centre, so the sign error cancels there.

The real problem is conceptual: "pull back until the subject fits" has no solution
indoors, because there is a wall at the pull-back position. An interior camera must be
*constrained inside the room* (back against the near wall with a small inset, eye
height ~1.5 m, a wide lens, and accepted cropping), which is a different algorithm
from exterior fitting — not a tuning of the same one.

**T0-3 — The framing regression test cannot fail on a cropped render.**
`tests/test_framing.py:50-67` asserts only that the non-sky bounding box occupies
between 30% and 95% of the frame in each dimension, scanning only the top 55% of the
image. A building that *overflows* the frame produces a bbox that starts at row 0 and
runs to the scan limit — comfortably inside 30–95%. It passed on the render above.
The assertion that actually encodes "the whole building is in shot" is the opposite
one: **the non-sky bbox must not touch any frame edge**, and must clear each edge by
roughly the 8% margin `camera_fit.MARGIN` promises. A pure-Python companion assertion
is even cheaper and needs no Blender: *every room camera's position lies inside its
room's rect*.

**T0-4 — The validation warning channel is 100% noise, and the defect it gestures at
is still real.**
Across all four specs in the repo, **every single warning is `wall_outside_plot`** —
63 on `tubehouse-dream`, 24 / 23 / 14 on the fixtures, and no other code has ever
fired. The rule is structurally unfalsifiable and its own docstring
(`checks.py:216-218`) admits why: exterior walls are centred on the room edge, so a
200 mm wall *always* pokes 100 mm past the plot line. It can never be satisfied, so it
can never be acted on, and it buries any warning that would matter (e.g.
`storeys_out_of_order`) under 63 lines of noise.

The underlying fact is a genuine modelling error, not a false alarm: the "4.0 m" tube
house is really **4.2 m** wide. On a sandwiched urban lot that is the difference
between legal and not. The correct fix is in the compiler, not the checker — inset
exterior walls so their *outer face* lands on the plot boundary (room rects then
denote the gross/structural line, which is also the standard architectural
convention). Once walls genuinely respect the plot, the rule flips from a permanent
warning to a real error that can actually catch something.

**T0-5 — The shipped deliverable depicts a different, older building, and nothing in
the pipeline can notice.**
`output/pdf/tubehouse-dream-brief.pdf` (Aug 1 16:52) combines SVG plans regenerated
Aug 1 16:43 from the current model with PNG renders dated **Jul 6** — produced before
buildable stairs, before floor voids, before the opening-overlap fix, before the
camera work. The brief handed to an architect therefore shows ladder-pitch stairs and
a sealed lift shaft next to plans that show neither. `pdf` simply globs
`output/png/<name>_<view>.png` and embeds whatever exists.

This is an architecture gap, not a mistake someone made: **no artifact carries the
identity of the model it came from.** A content hash of the compiled model, written
into a sidecar next to each PNG (and into the `.blend`), lets `pdf` and `render`
refuse — or at minimum loudly warn — when an image predates the model. Given that a
final gallery costs 11 hours, silently shipping a stale one is the most expensive
failure mode the tool has.

### Tier 1 — Highest leverage

**T1-1 — Upgrading Blender is probably worth more than every render optimisation
combined.**
The installed Blender is **4.1.1**, whose EEVEE is the legacy rasteriser: no
ray-traced GI, no screen-space refraction worth the name, no AgX. Blender 4.2+
ships **EEVEE Next**, which does real-time ray tracing and produces interior GI that
is close enough to Cycles for an architect brief. On this machine Cycles will never
have a GPU backend, so the 11.3 h gallery is a permanent tax — and `_set_engine`
already tries `BLENDER_EEVEE_NEXT` before `BLENDER_EEVEE` (CON-001), meaning **the
code is ready and the runtime is not**. Moving to 4.5 LTS and promoting EEVEE Next to
the default `final` profile is a one-evening experiment with an order-of-magnitude
payoff; Cycles becomes an opt-in overnight path for a hero shot rather than the only
route to a presentable image. AgX also replaces the Filmic workaround that exists only
because Standard was clipping interiors to white.

**T1-2 — The things that make a render read as "wrong" are geometric, not textural,
and they are all cheap.**
Before any texture work:
  - **No railings or parapets on `balcony` rooms.** `tubehouse-dream` has a 5-storey
    open roof terrace with no edge protection. An architect sees this instantly.
  - **No balustrade on stairs** — the newly-correct flights are bare treads.
  - **No ceilings.** Rooms get a ceiling only incidentally, from the floor slab of the
    storey above; the top storey has none unless a roof happens to cover it.
  - **No neighbour context.** A Vietnamese tube house rendered free-standing in a
    green field is architecturally misleading — it is by definition sandwiched. Two
    grey party-wall blocks and a strip of street cost ~30 LOC and change the reading
    of every exterior shot.
  - **No window reveals or sills**; `joinery.py` puts two frame jambs and a pane in a
    hole, with no head, no sill, no reveal depth.

**T1-3 — Realism ceiling unchanged, and the asset pipeline is sitting right there
unused.** `materials.py` is still 12 flat Principled BSDFs, no UVs, no maps, no HDRI
world (the sky is a solid colour and a fake 25 W "Fill" light compensates). Meanwhile
BlenderMCP is configured (`.claude/mcp.json`) and its PolyHaven / Sketchfab / Hyper3D
tools are live in this very session — and the pipeline has never touched them. The
right shape is an **offline asset cache** checked into `assets/` (a handful of CC0
HDRIs + 4–6 PBR sets + a small furniture library keyed by `FurnitureItem.kind`), with
the procedural blocks kept as the never-fails fallback, so the build stays
deterministic and network-free.

**T1-4 — No elevations, no sections. This is the biggest remaining deliverable gap.**
Plans alone are not a design package; the next two drawings any architect asks for are
elevations and a long section — and for a 4 × 25 m five-storey tube house, the long
section *is* the design (it is where the light well, the stair core and the storey
stack become legible). Both are fully derivable from `CompiledModel` in pure Python:
an elevation is walls and openings projected onto one facade plane with storey levels;
a section is a cut line through the model with everything behind it in outline.
Notably the **retired FreeCAD pipeline produced `front_facade_elevation.dxf`** (still
sitting in `output/dxf/`) and its replacement never has — this is a capability the
project lost and did not notice.

**T1-5 — The spec still cannot express things people ask for in the first sentence.**
Rooms gained `name`, and openings gained `align`/`offset_mm`. Still missing: per-room
ceiling height; wall thickness override (`EXT_THICKNESS`/`INT_THICKNESS` remain module
constants, so a 150 mm partition or a brick wall is unsayable); floor/wall finishes;
per-room furniture override or suppression; **site orientation** (there is no north
angle anywhere — the north arrow is hardcoded to −y, so "which way does the house
face" cannot be answered and sun angles are fiction); neighbour/context geometry; and
`meta.style` is still an enum with exactly one member.

### Tier 2 — Formats and durability

**T2-1 — `src/ifc_export_utils.py` is now definitively dead and should be resolved.**
276 LOC, no importer anywhere in `src/` or `tests/`, targeting the retired spec format,
and `ifcopenshell` was correctly dropped from `pyproject.toml` — so the file cannot
even be executed. The previous brainstorm recommended "rewire, or delete; leaving it
is the worst option," and it was left. IFC4 from `CompiledModel` (IfcWall / IfcSlab /
IfcDoor / IfcWindow / IfcSpace / IfcStair) remains the one format DXF fundamentally
cannot carry, and the model holds everything needed. **Recommendation: delete the file
now** (it is git history, not documentation) and treat IFC as a clean-sheet feature
scheduled on its own merits.

**T2-2 — glTF + a self-contained web viewer sidesteps the render problem entirely.**
`bpy.ops.export_scene.gltf` from the same headless run costs seconds and produces a
model that a single-file three.js page can walk through in a browser. On hardware that
cannot render 9 stills in under 11 hours, *one interactive model* is both the cheaper
and the better deliverable — and it is directly publishable as an Artifact.

**T2-3 — `output/` is gitignored, so an 11.3-hour asset is one `git clean -xdf` from
gone.** The flagship brief PDF, the final render gallery and the `.blend` are all
untracked. Regenerable in principle; in practice the gallery costs an overnight run and
the current PNGs are the only copies of renders from a model state that no longer
exists. A tracked `deliverables/<slug>/` holding the finals (or, at minimum, an
explicit note in `AGENTS.md` that `output/` is disposable and expensive) closes a real
data-loss path — the same class of issue as the `output/specs/` finding last round.

### Tier 3 — Platform and hygiene

**T3-1 — `AGENTS.md`'s "Start Here" sends the next agent to a superseded document.**
Line 16 recommends `plans/home-design-to-architect-workflow.md` "for the end-to-end
workflow." That file's own frontmatter reads `status: superseded`, and its body
instructs the reader to install FreeCAD, run `run.sh`, and configure `opencode.json`
and `freecad-mcp-guide.md` — none of which exist. An agent reading AGENTS.md in the
order it prescribes lands on instructions for software this repo deliberately deleted.
Either archive it under `docs/archive/` like its siblings, or point "Start Here" at
`.claude/skills/homedesign/SKILL.md`, which is accurate.

**T3-2 — SKILL.md contradicts itself on the render engine.** Step 2 correctly
describes an EEVEE preview; "Known limitations" (line 162) still says "Preview renders
are low-sample Cycles for speed." Small, but this file is the agent-facing contract.

**T3-3 — No console script.** `pyproject.toml` has no `[project.scripts]`, so every
doc still prescribes `PYTHONPATH=src python -m homedesign …` even though `pip install
-e .` already makes the package importable. `homedesign = "homedesign.__main__:main"`
is two lines and removes a papercut from every command in every document.

**T3-4 — Small dead/loaded code.**
  - `compiler.py:368`: `default_head = 2100.0 if o["type"] == "door" else 2100.0` — a
    tautology; either the two defaults should differ (windows typically share a head
    line with doors, so arguably they legitimately match — then drop the branch) or
    the intent was lost.
  - `orchestrator.py:19` still hardcodes `C:/Users/tukum/Blender/...` as the first
    candidate. `BLENDER_CMD` and PATH are checked first, so it is harmless, but it is
    a user-specific path in shared source.
  - `build_scene._find_default_interior_room` searches a priority list containing
    `"master"`, which is not a member of the room-type enum — it can only ever match
    by room *id*, silently.

**T3-5 — Still zero automated coverage of `blender/` (~800 LOC), and this session
shows exactly which assertions matter.** The `bpy` PyPI wheel runs Blender headless as
an importable module, making this CI-able. The highest-value checks are the ones that
had to be done by hand here: every mesh bbox lies inside the plot ± tolerance (the
permanent form of the ad-hoc script that caught 32 flung door leaves); no floor slab
covers a declared floor void; every camera position is inside the volume it claims to
depict; the object count for a fixture model is stable. Plus golden-file tests for
SVG/DXF, which are pure text and cost nothing.

**T3-6 — `output/` still holds FreeCAD-era artifacts** — `freecad_F0..F4.svg`,
`floorplan_F0..F4.dxf`, `front_facade_elevation.dxf`, `tubehouse_scene.blend`,
`floor_1_preview.svg`. Flagged last round, still there. Harmless but confusing when
someone greps the output directory for "what does this tool produce."

---

## Approaches Considered

**(A) Fix the cameras, re-render, ship the brief.** Smallest possible scope: T0-1 to
T0-3 plus one overnight gallery. Gets an honest deliverable within days. Caps the
project where it is.

**(B) Chase photorealism** — HDRI, PBR, asset library, neighbours. Most visible
change, but on 4.1.1 + CPU Cycles it is gated behind render economics, and it makes a
picture of a building whose stairs have no handrail and whose terrace has no parapet.
Wrong order.

**(C) Complete the drawing set** — elevations, sections, IFC, web viewer. Highest
value to the actual audience (an architect), entirely pure-Python for the drawings,
and completely independent of the render bottleneck.

**Adopted: A → (upgrade Blender) → C, with B riding alongside C.** The reasoning is
that A is a precondition for *anything* being trustworthy, the Blender upgrade is a
single cheap experiment that determines whether B is affordable at all, and C is the
only work whose value does not depend on the render path. B's geometric half (railings,
parapets, ceilings, neighbours, reveals — T1-2) is promoted ahead of B's textural half,
because those items change what the drawing *says*, not merely how it looks.

**Rejected:** rewriting camera placement as an iterative solver or letting Blender's
`camera_to_view_selected` do it. The analytic approach is right and is
unit-testable without Blender; it has one wrong character and one impossible
application. Also rejected: hand-authoring the camera positions per view in the spec —
that trades a bug for a permanent authoring burden and would have hidden this defect
forever.

## Suggested Roadmap

**Sprint 1 — "the picture must show the building" (small, sharp, mostly pure Python).**
1. Flip the sign in `fit_distance`; add a unit test with a **deliberately off-centre**
   box that fails under the old sign (the missing test class, not just the missing
   test).
2. Anchor `_build_exterior_front_camera` on the facade box's own centre rather than
   the plot centroid.
3. Replace the room camera with an interior-constrained placement: camera inside the
   room against the near wall, ~1.5 m eye height, wide lens, cropping accepted; add a
   pure-Python test asserting every camera position lies inside its subject room.
4. Strengthen `test_framing.py` to assert the non-sky bbox is **strictly inside** the
   frame with margin on all four edges, and make it build its own render instead of
   skipping when one is absent.
5. Re-render the `tubehouse-dream` gallery and rebuild the brief.
*Exit criterion:* the exterior render shows the whole building with visible sky above
and ground below, and the interior renders show room interiors — asserted by a test
that demonstrably fails on today's images.

**Sprint 2 — "one upgrade, then believable geometry."**
Install Blender 4.5 LTS; measure EEVEE Next against Cycles on one interior and one
exterior; if it holds up, promote it to the `final` profile and demote Cycles to an
opt-in hero path, switch Filmic → AgX, and delete the compensating "Fill" light in
favour of an HDRI world. Then the geometric realism items: parapets/railings on
`balcony`, stair balustrades, top-storey ceilings, window reveals and sills, neighbour
party-wall massing and a street strip.
*Exit criterion:* a full gallery in minutes rather than hours, with no unprotected
five-storey terrace edge in it.

**Sprint 3 — "the rest of the drawing set, and artifacts that know what they are."**
Elevations and long/cross sections from `CompiledModel` into `plan2d` and the PDF;
exterior wall inset + `wall_outside_plot` promoted from permanent warning to real
error; model-hash provenance sidecars so `pdf`/`render` can detect stale images; glTF
export + a self-contained three.js walkthrough page; delete `src/ifc_export_utils.py`;
`[project.scripts]` entry point; the AGENTS.md / SKILL.md accuracy pass; `bpy`-wheel
tests for the Blender half.

Textures and a furniture asset library (T1-3's second half) ride alongside Sprint 3 —
most visible, least depended-upon, and only affordable once Sprint 2 answers the
engine question.

## Assumptions Adopted

Recorded per the unattended-mode instruction; each is the answer I would have
recommended had I been able to ask.

1. **Camera correctness outranks everything.** A tool whose renders do not depict its
   own model is not shippable, regardless of how correct the geometry underneath is.
2. **Interior and exterior cameras need different algorithms**, not shared tuning.
   Pull-back framing is undefined indoors.
3. **Blender 4.5 LTS + EEVEE Next is the render answer on this hardware**, not further
   Cycles tuning and not a GPU that will never exist here. If the 4.2+ upgrade is
   blocked for a reason not visible in the repo, Sprint 2's first half is void and the
   11.3 h constraint stands — the rest of the roadmap is unaffected.
4. **Wall inset is a compiler change, not a checker change.** Room rects become the
   gross/structural line; exterior walls grow inward. This changes every existing
   plan by 100 mm per side, which is correct and is the point.
5. **Delete `ifc_export_utils.py` rather than rewire it.** It is recoverable from git;
   IFC deserves a clean implementation against `CompiledModel` when it is actually
   scheduled.
6. **Backwards compatibility is still required** for every spec in `spec/` and
   `designs/`; schema growth stays additive with preserved defaults. (Exception: the
   wall-inset change alters compiled geometry by design — specs still compile, output
   shifts.)
7. **Deliverables that cost hours should be tracked**; `output/` stays disposable, a
   new `deliverables/` holds finals.
8. This document changes no code. The only mutation made this session was rebuilding
   `spec/examples/tubehouse-mini.json` (regenerating its own `output/` artifacts) to
   gather evidence.

## Out of Scope

Curved or diagonal geometry and split levels; structural or code-compliance
certification; cost estimation; MEP routing; multi-user or cloud service; real-time
collaborative editing; site-survey or photogrammetry import; FreeCAD's return.

## Open Questions

1. **Is a wide-angle interior shot acceptable, or should interiors be cutaway
   exteriors?** Constraining the camera inside a 4 m-wide room means a very wide lens
   and visible distortion. The alternative — a sectional/cutaway camera outside a
   removed wall — reads better and is how architects present interiors, but needs
   per-view wall suppression. Recommendation: constrained-interior first (it is the
   bug fix), cutaway as a Sprint 3 view kind.
2. **Does the wall-inset change need a compatibility flag?** It shifts every wall by
   100 mm. Recommendation: no flag — a versioned spec field would preserve a geometry
   the tool now considers wrong.
3. **Is the audience still "an architect I hand a PDF to," or has it shifted toward
   the interactive model?** This decides whether elevations/sections (T1-4) or the web
   viewer (T2-2) leads Sprint 3.
4. **Should `homedesign` gain a `verify` subcommand** that re-checks artifact
   freshness, camera containment and mesh-in-plot in one call — i.e. promote this
   session's ad-hoc evidence gathering into the tool itself?

## Suggested Next Step

Run `/plan` on **Sprint 1**. It is four small, mostly pure-Python changes plus one
re-render, it is the precondition for trusting any other output the tool produces, and
it is testable to a standard that provably fails on today's artifacts. Suggested plan
title: *"homedesign camera truth: fix the fit sign, anchor the facade, put interior
cameras indoors, and make the framing test able to fail."*
