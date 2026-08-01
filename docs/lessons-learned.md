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
