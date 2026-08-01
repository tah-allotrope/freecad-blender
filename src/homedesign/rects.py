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
