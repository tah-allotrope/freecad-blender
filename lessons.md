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

## 2026-09-03 — A primitive in the draw model is not a primitive on the sheet

**Pattern:** `elevation.py` built `facade` primitives for all 21 authored facade
elements and the fidelity ledger recorded (k) as resolved. Neither the SVG nor
the DXF writer had a branch for that `kind`, so every one was silently dropped
and the generated south elevation still showed a blank wall. The same held for
window divisions. Both were "verified" by grepping for the producing code.

**Rule:** For any pipeline with a neutral intermediate model and multiple
renderers, adding a new primitive kind is only half the change — check every
consumer has a branch for it, and assert on the *output* (the SVG/DXF/PNG),
never on the intermediate. A `kind` string that no writer matches fails silently
by construction; prefer an explicit `else: raise` in the writer, or a test that
enumerates the kinds each writer handles against the kinds the builder emits.

## 2026-09-03 — Verify an asset cache by its contents, not its file tree

**Pattern:** `assets/cache/` had the right directory layout, an `ATTRIBUTION.md`
with SHA-256 hashes, and code paths that consumed it — and every texture was a
64×64 placeholder, the HDRIs were 2×2 pixels, and the furniture GLBs were
412-byte empties. Everything downstream "worked"; nothing looked different.

**Rule:** When a task says "download real assets", assert on intrinsic
properties — image dimensions, file size floors, decoded value ranges (an HDRI
must contain values above 1.0), mesh triangle counts — not on file existence.
An attribution row saying `source: placeholder` is a self-report, not evidence.

## 2026-09-03 — Bake the transform, or update the depsgraph; never assume

**Pattern:** New furniture instances were parented to an empty carrying their
placement. `matrix_world` is only recomputed on depsgraph evaluation, so every
consumer reading it in the same pass — the geometry tests, camera fitting, the
exporter — saw the mesh at the template's origin, a metre outside the plot.

**Rule:** In Blender, code that builds and immediately reads geometry must
either assign `matrix_world` on an unparented object (which writes through
straight away) or call `bpy.context.view_layer.update()` before reading. Also:
`clear_scene()` frees the previous file's datablocks, so every module-level
cache holding a material or mesh must be cleared with it, or a later build
silently reuses freed data.

## 2026-09-03 — A keyword the callee accepts but never forwards fails silently

**Pattern:** `orchestrator.build_scene(..., show_neighbours=False)` took the
keyword, documented it, and called `_build_command(model, out, profile, views,
skip_existing, reuse_blend, gltf)` — positionally, without it. Every
`homedesign build --show-neighbours` therefore rendered the plain ground pad.
Nothing errored; the CLI flag existed, the Blender script parsed it, the flag
just never got there. `render_only` forwarded it correctly, which made the
plumbing look complete on inspection.

**Rule:** When threading an option through a call chain, test the *edge*, not
the middle: assert the flag reaches the outermost boundary (here, the argv
handed to the subprocess) for both values. Grep for the parameter name and
check every call site actually passes it — a parameter with a default is
invisible when dropped.

## 2026-09-03 — An image texture with no UVs renders as a flat colour, not an error

**Pattern:** Materials were switched to a texture-first path wired to
`ShaderNodeTexCoord.UV`. Every mesh is a `bmesh` cube with no unwrap, and
`_ensure_uv` only creates an *empty* UV layer, so every face sampled a single
texel. Renders came out flat-coloured and looked exactly like the old
procedural ones — the failure mode of a missing unwrap is a plausible image,
not a crash, so it survived a written "textures now wired" review.

**Rule:** For procedurally generated, axis-aligned geometry, drive image
textures from **Object** coordinates with `projection='BOX'` rather than UVs:
no unwrap needed, the scale stays metric, and the pattern runs continuously
across adjacent boxes. When a visual change is claimed, compare two rendered
frames — the presence of texture nodes in the graph proves nothing.
