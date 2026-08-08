# Lessons

Patterns from user corrections, and the rule that prevents each from recurring.

## 2026-08-08 — Answer the artifact the user is actually looking at

**Pattern:** Asked why "the recent pdf looks like ass", I diagnosed the PDF
*assembly* layer (page CSS, Chromium print flags, SVG fit math). The user meant the
*content* — the 3D house was rendered blood red with bare interiors. Both analyses
were correct; only the second was wanted, so the first was a wasted round-trip.

**Rule:** When a complaint targets a container (PDF, report, deck, dashboard), open
the rendered artifact and look at it *before* deciding which layer is at fault. Rank
what a reader would notice first — a red building outranks a misaligned footer.
Ask which layer they mean when a single glance can't settle it.

## 2026-08-08 — A "design looks wrong" bug may be a renderer bug; bisect with a repro, not by reading source

**Pattern:** Every surface in the gallery rendered blood red. The palette in
`materials.py` contains no red at all. Reading more source would never have found it:
the fault was EEVEE Next miscompiling on a 2018 Intel iGPU driver.

**Rule:** When output colour/geometry contradicts the source data, stop reading and
build the smallest scene that reproduces it, then bisect the *pipeline* — engine,
view transform, device, version — not the project code. Two signals that the tool is
at fault, not the data: unrelated inputs collapsing to the same wrong output (a white
wall and a green lawn both landing on the same red), and one element rendering
correctly while all others fail (the world background was fine, so colour management
was innocent).

**Corollary:** Prove the data is good by rendering it through a second engine. One
Cycles render settled it in minutes and produced the before/after the user needed.

## 2026-08-08 — Record the hardware a rendering/compute default assumes

**Pattern:** PHASE-02 made EEVEE Next the `final` profile and Blender 4.5.1 the
default, benchmarked on a machine where it silently produced corrupt output. The
decision was documented; the hardware assumption behind it was not, so nothing
flagged the mismatch.

**Rule:** When choosing a render engine, compute device, or driver-dependent default,
write down the GPU/CPU it was validated on and keep an override path
(`BLENDER_CMD` here). Add a regression test that pins the ordering with the *reason*
in its docstring, so a future "upgrade to the newest version" doesn't silently undo
it.
