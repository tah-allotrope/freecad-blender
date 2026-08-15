"""Pure axis-aligned rectangle subtraction. No imports beyond typing -- safe
to use from both the compiler and any bpy-importing module."""
from __future__ import annotations


def subtract_rect(
    box: tuple[float, float, float, float], hole: tuple[float, float, float, float]
) -> list[tuple[float, float, float, float]]:
    """Split axis-aligned `box` (x,y,w,d) around `hole` (x,y,w,d) into up to
    four boxes (north/south/east/west strips), assuming `hole` sits fully
    inside `box`. No booleans -- deterministic, artifact-free geometry."""
    bx, by, bw, bd = box
    hx, hy, hw, hd = hole
    bx2, by2 = bx + bw, by + bd
    hx2, hy2 = hx + hw, hy + hd
    if hx2 <= bx or hx >= bx2 or hy2 <= by or hy >= by2:
        return [box]

    hx, hx2 = max(hx, bx), min(hx2, bx2)
    hy, hy2 = max(hy, by), min(hy2, by2)

    pieces = []
    if hy > by:
        pieces.append((bx, by, bw, hy - by))  # north strip (full width)
    if hy2 < by2:
        pieces.append((bx, hy2, bw, by2 - hy2))  # south strip (full width)
    if hx > bx:
        pieces.append((bx, hy, hx - bx, hy2 - hy))  # west strip (middle band)
    if hx2 < bx2:
        pieces.append((hx2, hy, bx2 - hx2, hy2 - hy))  # east strip (middle band)
    return pieces


def subtract_rects(
    x: float, y: float, w: float, d: float, holes: list[tuple[float, float, float, float]]
) -> list[tuple[float, float, float, float]]:
    """The fragments of one rectangle after removing every hole in turn."""
    boxes = [(x, y, w, d)]
    for hole in holes:
        next_boxes = []
        for box in boxes:
            next_boxes.extend(subtract_rect(box, hole))
        boxes = next_boxes
    return boxes


def open_edges(rect, others, eps: float = 1.0) -> set[str]:
    """Which of `{"north", "south", "east", "west"}` of `rect` are not shared
    with an edge of any rect in `others` (coincident within `eps` millimetres).

    `rect` and the entries of `others` expose `.x/.y/.w/.d`. An edge is shared
    when another rect's facing edge lies on it (within `eps`) and their spans
    overlap. Used to decide where a balcony needs a parapet: an edge is open
    when no neighbouring room on the same storey shares it.
    """
    x, y, w, d = rect.x, rect.y, rect.w, rect.d
    shared = set()
    for o in others:
        ox, oy, ow, od = o.x, o.y, o.w, o.d
        if abs(oy + od - y) < eps and _span_overlap(x, x + w, ox, ox + ow):
            shared.add("north")
        if abs(oy - (y + d)) < eps and _span_overlap(x, x + w, ox, ox + ow):
            shared.add("south")
        if abs(ox + ow - x) < eps and _span_overlap(y, y + d, oy, oy + od):
            shared.add("west")
        if abs(ox - (x + w)) < eps and _span_overlap(y, y + d, oy, oy + od):
            shared.add("east")
    return {"north", "south", "east", "west"} - shared


def _span_overlap(a: float, b: float, c: float, d: float) -> bool:
    return a < d and c < b


def wall_face_fragments(
    span_mm: float,
    height_mm: float,
    openings: list[tuple[float, float, float, float]],
) -> list[tuple[float, float, float, float]]:
    """The solid fragments of a wall face (S4), as `(offset_mm, z_mm, width_mm,
    height_mm)` tuples in face coordinates, where the first axis runs along the
    wall span and the second is vertical. Each opening is given as
    `(offset_mm, sill_mm, width_mm, head_minus_sill_mm)`.

    This is exactly `subtract_rects` over the wall's 2D face, so a wall with
    openings becomes up to four boxes per opening (under-sill band, over-head
    band and the two jamb piers) -- deterministic, artifact-free, no booleans.
    """
    if not openings:
        return [(0.0, 0.0, span_mm, height_mm)]
    return subtract_rects(0.0, 0.0, span_mm, height_mm, list(openings))
