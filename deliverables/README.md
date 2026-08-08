# deliverables/

Finals worth keeping live here, one folder per design:

```
deliverables/<slug>/pdf/<slug>-brief.pdf
deliverables/<slug>/png/*.png
deliverables/<slug>/gltf/<slug>.glb
deliverables/<slug>/viewer/<slug>.html
```

## Why this directory exists

Everything in `output/` is git-ignored and disposable — a full-quality render
gallery is regenerated from `designs/<slug>.json` with:

```bash
homedesign build designs/<slug>.json          # EEVEE preview
homedesign render designs/<slug>.json --profile final   # full gallery
homedesign pdf designs/<slug>.json --require-fresh      # architect brief
```

A `--profile final` gallery is fast enough (~12 min for the 9-view
`tubehouse-dream` set, legacy EEVEE on Blender 4.1) that nothing in `output/`
is precious, but the brief PDF is the thing you actually hand to an architect.
Copy the finished files here and commit them so the deliverables survive
`git clean -xdf` (which deletes all of `output/`).

Renders must come from **Blender 4.1's legacy EEVEE**, which
`orchestrator._CANDIDATES` selects by default. EEVEE Next (4.2+) miscompiles on
this project's target iGPU and renders every lit surface blood red — see the
2026-08-08 entry in `activeContext.md`. If a gallery looks wrong, check which
Blender ran before you check the design.

The interactive viewer (`--gltf` on `build`, or a small GLB in
`deliverables/<slug>/viewer/`) works offline from the local filesystem — no
network requests — and is the cheapest way to share a model with someone who
does not run Blender.
