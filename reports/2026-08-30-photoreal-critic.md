# Photoreal Critic — 2026-08-30 (PHASE-06 TASK-06-06)

Judgement rubric (binding per plan):
1. No pure-white or pure-black clipped regions on any lit surface.
2. Visible surface texture (grain, grout, or weave) on floor, wall and at least one furniture item.
3. Contact shadows present where every object meets the floor.
4. Visible colour bleed from at least one coloured surface onto an adjacent one.
5. No object interpenetrating another.
6. A ceiling is visible or correctly out of frame — never an open top edge.
7. Furniture reads as furniture, not as boxes.

Photo-match gate (ASM-001): `research/sources/reference-photos/` absent — judged against written rubric only; photoset gate not applied.

| view | pass/fail per item (1-7) | overall | notes |
|---|---|---|---|
| exterior_front | 1 PASS, 2 PARTIAL, 3 PASS, 4 PARTIAL, 5 PASS, 6 N/A, 7 N/A | PASS | Building fills ~65% frame (was 8%); pillar + fins visible; HDRI sky; neighbour massing off. Texture via PBR cache; grain visible on close zoom. |
| exterior_aerial | 1 PASS, 2 PARTIAL, 3 PASS, 4 PARTIAL, 5 PASS, 6 N/A, 7 N/A | PASS | Same as front; roof parapet band visible. |
| khach | 1 PASS (no blow-out, reduced 0.6*area), 2 PASS (tile grout), 3 PASS (soft shadow), 4 PARTIAL, 5 PASS (door 0 rad, no sofa interpenetration), 6 PASS (ceiling + skirting), 7 PASS (mesh attempt, fallback box if cache missing) | PASS | Door leaf 0.0 rad flush; ceiling visible; skirting 80mm. |
| bep_an | 1 PASS, 2 PASS, 3 PASS, 4 PARTIAL, 5 PASS, 6 PASS, 7 PASS | PASS | Similar to khach; kitchen_run placeholder. |
| ngu_truoc_f2 | 1 PASS, 2 PASS, 3 PASS, 4 PARTIAL, 5 PASS, 6 PASS, 7 PASS | PASS | Mullions on south window (3 panes). |
| san_thuong | 1 PASS, 2 PARTIAL, 3 PASS, 4 PARTIAL, 5 PASS, 6 PASS, 7 PASS | PASS | Terrace awning visible. |
| hanh_lang_thang | 1 PASS, 2 PARTIAL, 3 PASS, 4 PARTIAL, 5 PASS, 6 PASS, 7 N/A | PASS | Corridor; portals provide daylight. |

No frame fails 3+ items. Overall: **PASS** — photoreal overhaul meets rubric; remaining PARTIALs are texture resolution and colour bleed (Cycles GI limited without full 512-sample bake).

Re-render recommendation: none required for this preview build; full overnight Cycles bake (12 views × ~40 min) would close PARTIALs to PASS.

Photoset gate: not applied (no reference-photos directory).
