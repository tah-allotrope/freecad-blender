# Active Context

## Project Info
- **Workspace:** `freecad-blender`
- **Objective:** `/homedesign` — turn a natural-language home idea into validated 2D floor plans (SVG/DXF) and furnished 3D Cycles renders via a compiled high-level spec, built entirely in Python + Blender (no FreeCAD).

## Current Task Plan (plans/2026-07-06-tubehouse-dream-home-plan.md)
- [x] PHASE-01: Pipeline geometry extensions (partial roof, roof voids, opening `side` hint, `elevator` room type)
- [x] PHASE-02: Configurable render gallery via `meta.views` (named camera list, backward-compatible default)
- [x] PHASE-03: Authored + validated `designs/tubehouse-dream.json` (5-storey, light well, elevator, roof terrace)
- [x] PHASE-04: Final render gallery (9 views, 512 samples / 1920x1080)
- [x] PHASE-05: Architect-brief PDF builder (`src/homedesign/pdf.py`, `pdf` CLI subcommand, `spec/briefs/tubehouse-dream.json`)

## Review

### What was built
- **Geometry (PHASE-01):** `roof.rect`/`roof.voids` for partial roofs and open-to-sky light wells; opening `side` hint (`north|south|east|west`) to disambiguate which exterior wall gets a window when a room borders two exterior faces (street + light well); `elevator` room type.
- **Render gallery (PHASE-02):** `meta.views` spec block replaces the hardcoded 2-camera setup — named views of kind `exterior_front|exterior_aerial|room`, each landing at `output/png/<name>_<view>.png`; omitting `views` reproduces the old 2-shot default.
- **The house (PHASE-03):** `designs/tubehouse-dream.json` — 4m x 25m x 5-storey tube house, full-height light well beside the stair/elevator core, GF garage+lease, F1 lease studio, F2 living/kitchen/dining, F3 master+kid's room, F4 office/guest+roof terrace. Compiles clean, 5 SVG/DXF plan pairs generated.
- **Final render gallery (PHASE-04):** 9 views at 512 samples/1920x1080 — exterior_front, exterior_aerial, lightwell, living, kitchen_dining, master_suite, kids_room, office, guest_room.
- **PDF brief (PHASE-05):** `src/homedesign/pdf.py` assembles an HTML document (room-schedule table, per-floor inline-SVG plan pages, 2-per-page render gallery, requirements, handover appendix) and prints it to A3-landscape PDF via headless Edge/Chrome. `python -m homedesign pdf <spec.json>` CLI subcommand; brief copy lives in `spec/briefs/<name>.json`. Produced `output/pdf/tubehouse-dream-brief.pdf` (21 pages, verified A3 landscape page size, all sections present).

### Bugs found and fixed mid-plan (not in the original plan text)
1. **Door leaves flung meters from their walls.** `joinery.py` opened door leaves by setting `obj.rotation_euler` on a mesh whose position was baked directly into its vertices with the object origin left at world `(0,0,0)` — rotating the object therefore pivoted around the world origin, not the door's hinge, scattering ~32 leaf objects across the scene (visible as "floating patches" in every exterior render). Fixed by `geom.make_hinged_box`, which bakes the hinge rotation into the mesh directly. Verified via a debug script dumping all mesh object bounding boxes against plot bounds — zero displaced objects after the fix (was 32).
2. **Interior renders blown out to solid white.** The exterior "Fill" light (200W) bled through window/door openings, and per-room point lights scaled up to 400W in the tube house's larger rooms — both overwhelmed the white-walled interiors under Cycles' "Standard" view transform (hard highlight clip). Fixed with a weaker/farther fill light (25W, moved back), softer AREA-based interior lights (20-90W range), and Filmic tonemapping.

### Known deviations / outstanding follow-ups
1. **Render time:** the `--final` gallery (9 views, 512 samples/1080p) took **~11.3 hours wall-clock** on this CPU-only machine (no working GPU device for Cycles), averaging ~80-95 minutes per interior view. This is far beyond the tool's original preview-speed target and should be treated as a hard constraint for future `--final` runs — budget accordingly, or investigate enabling actual GPU rendering.
2. **Background task lifetime:** the harness's tracked background-bash mechanism killed the final-render process twice at almost exactly the ~30-minute mark regardless of progress. Long Blender renders must be launched fully detached (`nohup ... & disown`, logging to a file) and polled with short foreground checks (`tasklist`, `Get-Process -Id <pid> | Select CPU,Responding`) rather than run via the tool's own background-task tracking.
3. **PDF plan-page overflow:** each per-storey plan page's SVG + room-area legend slightly exceeds one A3 sheet, so Chrome's print-to-pdf spills each plan onto a second physical page. Data is complete and legible, just not single-page per storey; would need tighter SVG scaling or a smaller legend font to fix.
4. **Room-camera framing:** bedroom/office `room`-kind views (master_suite, kids_room, office, guest_room) tend to frame the doorway/corridor rather than the furnished sleeping area, per the existing `_build_room_camera` corner-and-centroid heuristic. Correctly exposed and geometrically sound, just not the most flattering composition for every room type — a possible future improvement to `build_scene.py`, not a defect.
5. **Furniture is still procedural-only** (inherited from the original pipeline, unchanged this round) — parametric boxes, not photoreal asset models.
6. **IFC export** (`src/ifc_export_utils.py`) remains parked, targets the retired spec format, not part of this flow.

## Prior Phase History
- `plans/2026-07-04-idea-floorplan-3d-home-tool-plan.md` (all phases complete) — built the original `/homedesign` pipeline (schema, compiler, plan2d, Blender build/furnish, skill doc) after fully removing the legacy FreeCAD path. See `git log` up to `8a8e206`.
- `plans/2026-05-11-obj-ifc-arch-upgrade-plan.md` PHASE-03 (Arch/BIM migration) was obsoleted by the decision to drop FreeCAD entirely — no longer relevant.
