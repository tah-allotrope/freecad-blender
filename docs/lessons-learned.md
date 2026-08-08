# Lessons Learned

Blender-era lessons from the `homedesign` pipeline (pure Python spec →
compiled model → headless Blender scene → Cycles/EEVEE renders).

## Lesson: Blender headless `bpy` gotchas (2026-07-04, homedesign pipeline)

**Hangs after render finishes:** `blender --background --python script.py` can hang
indefinitely after the script's `main()` returns (render written, `.blend` saved),
apparently stuck in shutdown (likely lingering Cycles device threads). Fix: call
`os._exit(0)` explicitly at the end of the script instead of trusting normal
interpreter exit.

**Point lights with `shadow_soft_size > 0` are directly visible to camera rays.**
A point light with nonzero soft size renders as a small emissive sphere; at
interior-room scale with plausible wattage this blows out the whole frame if it's
anywhere near the camera's view. Keep `shadow_soft_size = 0` for point lights meant
to just illuminate a room, not be seen.

**Boolean modifier order matters for opening cuts.** Cut wall-opening voids with a
small padding (~0.02m) beyond the wall thickness/opposing faces to avoid coplanar
face artifacts from the `EXACT` boolean solver.

**Room-adjacency tiling for procedural floor plans:** when rooms are laid out as
stacked rows of different room-counts (e.g. a 3-room row over a 4-room row), a
wall-derivation algorithm that requires *exact* span matches between rooms will
silently misclassify the shared boundary as all-exterior. Use a sweep-line
(breakpoint-based atomic-interval) approach instead — it correctly finds where two
specific rooms share a sub-span even when their row layouts don't align.


## Lesson: EEVEE Next silently miscompiles on Gen9.5 Intel iGPUs (2026-08-08)

**This supersedes the 2026-08-05 lesson below. Do not restore EEVEE Next as the
`final` engine on this machine.**

Every render in the shipped `tubehouse-dream` gallery came out blood red. The
palette in `blender/materials.py` contains no red at all — the fault was the
engine, not the data. Minimal repro (one cube, one sun, the project's own
material/engine/view-transform code):

| engine | view transform | white `0.92/0.91/0.88` cube renders as |
|---|---|---|
| Cycles | AgX | `(190, 193, 197)` correct |
| Cycles | Standard | `(235, 244, 255)` correct |
| EEVEE Next | AgX | `(194, 34, 53)` red |
| EEVEE Next | AgX, raytracing off | `(194, 34, 53)` red |
| EEVEE Next | Standard | `(208, 0, 55)` red, green channel 0 |

Independent of view transform and of `raytracing`; the world background renders
correctly, so colour management is innocent and the fault is in surface shading.
Hardware: Intel UHD Graphics 620 (Gen9.5), driver `23.20.16.4849` (2018).
Vulkan is not an escape — Blender rejects the device for missing timeline
semaphores, buffer device address and `VK_EXT_provoking_vertex`.

**Resolution:** `orchestrator._CANDIDATES` prefers **Blender 4.1.1 (legacy
EEVEE)** over 4.5.1. `build_scene._set_engine` already falls back to
`BLENDER_EEVEE`; `render_profiles` is unchanged. Pinned by
`test_blender_candidates_prefer_legacy_eevee_build`. `BLENDER_CMD` overrides on
a machine whose GPU handles EEVEE Next correctly.

**Measured (1920x1080, `exterior_front`):** legacy EEVEE 256 spp **29.7 s/view**;
Cycles CPU 64 spp + denoise **169.3 s/view**; EEVEE Next **112 s for a single
cube**. Full 9-view `final` gallery + scene build + glTF: **713.5 s (11.9 min)** —
down from the 50.7 min below, so the speed argument for EEVEE Next was wrong too.

**Generalisable rule:** when output colour or geometry contradicts the source
data, stop reading source and bisect the *pipeline* (engine, view transform,
device, version) with a minimal scene. Two tells that the tool is at fault:
unrelated inputs collapsing onto the same wrong output (a white wall and a green
lawn both landing on the same red), and one element rendering correctly while all
others fail. Confirm by rendering the same scene through a second engine.

---

## Lesson (SUPERSEDED 2026-08-08): EEVEE Next vs Cycles on CPU-only hardware (2026-08-05, camera truth + render economics plan)

> **Superseded.** The conclusion below — "EEVEE Next remains the `final`
> profile" — produced a gallery of unusable red renders. The timings are still
> accurate as history; the recommendation is not. See the 2026-08-08 lesson above.

**Blender 4.5.1 LTS + EEVEE Next replaced the 11.3-hour Cycles gallery.** The
9-view `tubehouse-dream` gallery at `--profile final` (EEVEE Next raytracing,
AgX, 256 samples, 1920x1080) completed in **50.7 min** wall clock on this
CPU-only machine (Intel UHD 620 iGPU, no Cycles GPU backend). Per view:
exterior_front 4:50, exterior_aerial 3:02, lightwell 7:06, living 6:04,
kitchen_dining 5:38, master_suite 6:00, kids_room 6:11, office 5:18,
guest_room 6:14. For comparison, a single Cycles view of the smallest fixture
(`tubehouse-mini` exterior, 512 samples) cost **9.8 min** -- a 9-view Cycles
gallery of the flagship house would be ~90-180 min.

**Findings:**
- EEVEE Next on 4.5 pays a large one-time per-process cost (shader compile /
  Vulkan init, ~60-90 s on this iGPU) before the first sample of the first
  view. It is amortised across all views in a single invocation, so always
  render the whole gallery in one Blender run (the `render` subcommand does).
- The first view (exterior_front, 4:50) is the slowest because it includes
  that init; later views settle at 3-7 min each.
- The 50.7 min figure is above the plan's 30-min aspirational target. Per
  ASM-002 this is recorded and the binding default stands: EEVEE Next remains
  the `final` profile and Cycles stays the explicit `--profile cycles` path.
  If a sub-30-min gallery is ever required, the lever is `raytracing: False`
  on the `final` profile (the bulk of the per-sample cost), which trades a
  little GI for a large speedup.
- `scene.eevee.use_raytracing` exists and accepts `True` on BOTH 4.1.1 and
  4.5.1 -- the plan expected 4.1.1 to print "unavailable", but the property is
  present there too. The `hasattr` guard is still the right shape; the
  "eevee raytracing: on" print is informational on 4.1.

**Quality:** EEVEE Next + AgX interiors are bright, tonally graded and close
enough to Cycles for an architect brief; glass and window openings render
differently from Cycles (EEVEE's default transmission), so never chase EEVEE
artifacts in a preview -- validate layout, not lighting.
