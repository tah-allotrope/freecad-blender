---
title: "Idea → 2D Floorplan → 3D Home Model Tool"
date: "2026-07-04"
type: "brainstorm"
depth: "standard"
source_request: "Transform this repo into a super smooth idea → 2D floorplan → 3D home model tool"
slug: "idea-floorplan-3d-home-tool"
---

# Brainstorm: Idea → 2D Floorplan → 3D Home Model Tool

## Problem & Why Now
<!-- seeds /plan ## Objective -->
The repo can turn a hand-authored 3,100-line spec JSON for **one hardcoded building** (a 4×25m tube house) into 2D plans and 3D renders — but only via a fragile two-stage FreeCAD→Blender pipeline with machine-specific paths, no spec validation, no 3D doors/windows, and no automated "idea" stage (today a human edits JSON in a chat session). The owner wants to describe *any* home in natural language to Claude and get validated 2D plans plus furnished 3D renders in one turn, then refine conversationally ("make the kitchen bigger") with correct round-tripping. The pipeline pieces exist and work; the transformation is from "bespoke script collection for one house" to "general, validated, one-command design tool driven by an LLM."

## Current vs Desired State
<!-- seeds /plan ## Context Snapshot -->
- **Current state:** Spec-driven batch pipeline: `spec/floorplan-spec.json` → `run.sh` (freecadcmd + `src/generate_floorplan.py`, Part::Box walls, 2D Draft plans) → `run_blender.sh` (`src/setup_blender_scene.py` OBJ import + materials, `src/render_blender.py` Cycles PNG). Parallel pure-Python IFC4 export (`src/ifc_export_utils.py`, IfcOpenShell — FreeCAD-independent). Exploratory FreeCAD-MCP chat path (`opencode.json`) requiring a live GUI. No jsonschema validation; door/element schemas inconsistent per type; walls are dumb boxes with no openings; PDF export broken (cairosvg); facade SVG fails headless; hardcoded stale paths (`generate_floorplan.py:41`). Tools: FreeCAD 1.0.2, Blender 4.1.1, IfcOpenShell 0.8.5 on Windows via Git Bash.
- **Desired state:** `/homedesign` Claude Code skill: natural-language prompt → Claude authors a compact **high-level design spec** (~100 lines: rooms, adjacency, openings, floors, style) → deterministic Python **compiler** derives walls/openings/geometry → pure-Python 2D output (SVG + DXF via ezdxf) and procedural 3D built directly in Blender (bpy): shell with real wall openings, doors/windows with frames/glass, roof, materials, and **furnished scenes** from a bundled CC0 asset pack with procedural fallback. One command runs compile→validate→preview-render; Claude visually inspects the results, self-corrects (bounded), then presents. FreeCAD is deleted from the flow.
- **Key repo surfaces:** `spec/floorplan-spec.json` (becomes compiled intermediate or is replaced), `src/floorplan_utils.py` + `src/facade_utils.py` (pure, tested — reusable), `src/blender_materials.py` + `spec/blender_materials.json` (material system — reusable), `src/setup_blender_scene.py` + `src/render_blender.py` (scene/render — evolve into the bpy builder), `src/ifc_export_utils.py` (FreeCAD-independent — survives), `src/generate_floorplan.py` + `run.sh` + `src/blender_export_utils.py` + MCP config (deleted once superseded), `docs/lessons-learned.md`, `plans/2026-05-11-obj-ifc-arch-upgrade-plan.md` (PHASE-07 Arch migration is **obsoleted** by this direction).

## Resolved Decisions
<!-- the grilled Q&A; each one keeps /plan's Grill Me empty -->
- **DEC-001:** Primary user is the owner driving Claude — natural language in, full output out; "smooth" = one prompt, one command. — No product UI, no hosting; the agent is the interface.
- **DEC-002:** The deliverable that defines success is **photoreal-ish Cycles renders** (exterior + interior); the 3D model is a means to the image. — 2D plans and IFC are supporting outputs.
- **DEC-003:** Iteration is a **conversational edit loop**: Claude patches the spec incrementally and re-runs. — Requires a diffable, human-legible spec and a fast, idempotent pipeline.
- **DEC-004:** The LLM authors a **new high-level design spec** (rooms/dimensions/adjacency/openings/floors/style, ~100 lines); a deterministic compiler derives walls, openings, and geometry. — LLM-reliable, diffable; the low-level detail becomes machine-generated.
- **DEC-005:** The idea→spec stage is a **`/homedesign` Claude Code skill** in the repo (schema docs + workflow instructions). — No API keys or separate runtime; this session's Claude does the authoring, running, and inspecting.
- **DEC-006:** Scope is **rectilinear any-home**: axis-aligned walls, detached/townhouse/tube-house, 1–N floors, flat or simple pitched roof. — Covers most real ideas; freeform/curved is out.
- **DEC-007:** 3D geometry is built **procedurally in Blender (bpy)** from the compiled spec — walls with boolean-cut openings, parametric doors/windows, roof. FreeCAD exits the 3D path. — One less handoff; kills the OBJ interchange and its quality problems.
- **DEC-008:** 2D plans are **pure Python**: SVG directly + DXF via `ezdxf`, from the same compiled model as the 3D. — FreeCAD removed from the smooth path entirely; single Python+Blender runtime.
- **DEC-009:** The skill includes an **automatic visual self-correction loop**: compile → validate → fast preview render → Claude inspects images/plans → fix spec → repeat (bounded, ~3 passes) → present. — Smoothness over per-turn latency.
- **DEC-010:** Renders are **furnished scenes** — furniture placed per room type, not just an architectural shell. — Best-looking, most judgeable renders; accepted as the largest workstream.
- **DEC-011:** Furniture comes from a **bundled CC0 asset pack** (curated once, e.g. Poly Haven / Kenney / Quaternius) with **procedural bpy fallback** for missing types. — Offline, deterministic, license-clean.
- **DEC-012:** The FreeCAD pipeline (generator, run.sh, OBJ export, MCP config) is **deleted aggressively** once the new path renders acceptably. — Clean repo; DXF/SVG are reimplemented in Python; FCStd output is dropped.
- **DEC-013:** Acceptance demo: `/homedesign "3-bedroom 2-storey house, open kitchen, master with ensuite"` → validated spec → 2D plans + furnished renders in one turn, then one conversational edit ("bigger kitchen") round-trips correctly. — Fresh-prompt generality is the bar, not tube-house parity.
- **DEC-014:** The design spec gets a **formal JSON Schema** plus compiler-level geometric sanity checks (room overlap, unreachable rooms, stairs fit, door/wall consistency). — Today nothing validates the spec; LLM-authored input makes this mandatory. *(inferred from repo gaps, not asked)*
- **DEC-015:** One orchestrator entry point (e.g. `python -m homedesign build <spec> [--final]`) replaces the two bash scripts; preview = low-sample Cycles (safe headless on this GPU setup), final = full Cycles. — Single command is the core of "smooth". *(inferred, not asked)*
- **DEC-016:** The pure-Python IFC exporter survives (it never depended on FreeCAD) as an **optional flag** off the compiled model, out of the smooth path. *(inferred; see Q-001)*

## Assumptions & Constraints
<!-- seeds /plan ## Assumptions and Constraints -->
- **ASM-001:** Blender 4.1.1's Python API (bpy) can express everything needed — boolean wall openings, parametric joinery, asset appending from bundled .blend libraries — headless on this Windows machine.
- **ASM-002:** Claude can reliably author the new high-level spec given a schema + examples in the skill, and can meaningfully judge preview renders visually.
- **ASM-003:** A usable CC0 furniture set (bed, sofa, table, chairs, kitchen block, WC, basin, wardrobe) can be curated at reasonable repo size (or one-time fetch).
- **CON-001:** Windows 11 + Git Bash; Blender at `C:/Users/tukum/Blender/blender-4.1.1-windows-x64/blender.exe` (overridable via `BLENDER_CMD`). No new heavyweight runtimes.
- **CON-002:** Rectilinear geometry only; flat or simple pitched roofs; no curved/diagonal walls, no split levels.
- **CON-003:** The preview loop must be fast enough for ~3 self-correction passes per turn (target: preview render well under a minute).

## Approaches Considered
<!-- seeds /plan ## Risks and Alternatives -->
- **Chosen:** High-level spec → Python compiler → pure-Python 2D (SVG/ezdxf) + procedural bpy 3D with bundled assets, orchestrated by a `/homedesign` skill with a bounded visual self-correction loop. — Single runtime, LLM-friendly authoring surface, fastest path to good furnished renders.
- **ALT-001:** Extend the Part::Box FreeCAD generator with boolean openings + door/window solids. — Keeps a heavyweight, path-fragile dependency and the lossy OBJ handoff for a render-first goal.
- **ALT-002:** Migrate to FreeCAD Arch/BIM workbench (the planned PHASE-07). — Right move for a BIM-first product; wrong for render-first — bigger rewrite, preset-constrained visuals, still two runtimes. This brainstorm obsoletes that plan.
- **ALT-003:** LLM writes the existing low-level spec directly (no compiler). — 3,100 lines of mm-precise, inconsistent-schema JSON is unreliable LLM output and undiffable in conversation.
- **ALT-004:** Standalone CLI calling the Claude API for idea→spec. — Shareable, but needs keys/prompting/its own UX; the Claude Code skill gets the same result for free.
- **ALT-005:** Online asset pulls (BlenderKit) for furniture. — Better variety but network-dependent, account-gated, non-deterministic.

## Out of Scope
- Any end-user UI (web/desktop editor or viewer) — the agent is the interface.
- Freeform geometry: curved/diagonal walls, complex roofs, split levels.
- BIM round-trip editing (Bonsai/Revit workflows); IFC remains a one-way optional export.
- The FreeCAD-MCP live-GUI workflow (deleted with the FreeCAD path).
- Structural/code-compliance engineering of any kind.
- FCStd and PDF outputs (PDF was already broken; drop rather than fix).

## Open Questions
<!-- the few that survived; seed /plan ## Grill Me. Use `None.` when fully resolved. -->
1. **Q-001:** Should IFC export be ported to the new compiled model in the first release, or parked until someone actually needs a BIM file?
   - **Recommended default:** Park it — keep `ifc_export_utils.py` in the repo but don't adapt it until needed; renders are the product.
   - **Why this matters:** Adapting IFC to the new spec is real work (storey/space/wall mapping) that competes with the furniture workstream.
2. **Q-002:** Which CC0 pack(s) to curate, and checked into git vs. one-time fetch script (repo size vs. reproducibility)?
   - **Recommended default:** One-time fetch script with pinned URLs + checksums into `assets/` (gitignored), procedural fallback covering all room types so the pipeline never hard-fails without assets.
   - **Why this matters:** Determines offline behavior, repo weight, and whether a fresh clone renders furnished scenes.

## Suggested Next Step
Run `/plan idea-floorplan-3d-home-tool` to turn this into a multi-phase implementation plan.
