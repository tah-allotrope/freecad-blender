"""Elevation-overlay parity metric (S1). Pure Python, no bpy."""
from __future__ import annotations

from homedesign.elevation import build_elevation

TOLERANCE_MM = 50.0


def silhouette_bounds(rects: list[dict]) -> tuple[float, float, float, float]:
    if not rects:
        raise ValueError("silhouette_bounds: empty rect list")

    def _x(r):
        return r.get("x_mm", r.get("x", 0))

    def _y(r):
        return r.get("y_mm", r.get("z", r.get("y", 0)))

    def _w(r):
        return r.get("w_mm", r.get("w", 0))

    def _h(r):
        return r.get("h_mm", r.get("h", 0))

    min_x = min(_x(r) for r in rects)
    min_y = min(_y(r) for r in rects)
    max_x = max(_x(r) + _w(r) for r in rects)
    max_y = max(_y(r) + _h(r) for r in rects)
    return (float(min_x), float(min_y), float(max_x), float(max_y))


def silhouette_deviation(reference: list[dict], candidate: list[dict]) -> float:
    if not reference or not candidate:
        raise ValueError("silhouette_deviation: empty rect list")
    rb = silhouette_bounds(reference)
    cb = silhouette_bounds(candidate)
    return max(abs(rb[i] - cb[i]) for i in range(4))


def opening_deviation(
    reference: list[dict], candidate: list[dict], exclude: set[str]
) -> tuple[float, list[str]]:
    def _id(r):
        return r.get("id") or r.get("identifier") or f"{r.get('wall_id','')}:{r.get('offset_mm','')}"

    ref_map = {_id(r): r for r in reference if _id(r) not in exclude}
    cand_map = {_id(r): r for r in candidate if _id(r) not in exclude}
    unmatched = []
    for k in list(ref_map.keys()):
        if k not in cand_map:
            unmatched.append(k)
    for k in list(cand_map.keys()):
        if k not in ref_map:
            unmatched.append(k)
    worst = 0.0
    for k in set(ref_map.keys()) & set(cand_map.keys()):
        rr = ref_map[k]
        cr = cand_map[k]

        def _edges(r):
            x = r.get("x_mm", r.get("x", 0))
            y = r.get("y_mm", r.get("z", r.get("y", 0)))
            w = r.get("w_mm", r.get("w", 0))
            h = r.get("h_mm", r.get("h", 0))
            return (x, x + w, y, y + h)

        xl_r, xr_r, ys_r, yh_r = _edges(rr)
        xl_c, xr_c, ys_c, yh_c = _edges(cr)
        dev = max(abs(xl_r - xl_c), abs(xr_r - xr_c), abs(ys_r - ys_c), abs(yh_r - yh_c))
        worst = max(worst, dev)
    return (float(worst), sorted(set(unmatched)))


def _candidate_rects(model, side: str) -> list[dict]:
    rects: list[dict] = []
    for storey in model.storeys:
        for wall in storey.walls:
            from homedesign.elevation import _project_box, _opening_h

            h0, w_h, _depth = _project_box(side, model, wall.x, wall.y, wall.w, wall.h)
            rects.append({
                "x_mm": h0,
                "y_mm": storey.base_z,
                "w_mm": w_h,
                "h_mm": storey.height_mm,
                "kind": "wall",
                "id": f"wall:{wall.id}",
            })
            parallel = (
                (side in ("north", "south") and wall.orientation == "horizontal")
                or (side in ("east", "west") and wall.orientation == "vertical")
            )
            if parallel:
                h0_wall, _, _ = _project_box(side, model, wall.x, wall.y, wall.w, wall.h)
                for op in storey.openings:
                    if op.wall_id != wall.id:
                        continue
                    ox = _opening_h(wall, op, side, h0_wall)
                    rects.append({
                        "x_mm": ox,
                        "y_mm": storey.base_z + op.sill_mm,
                        "w_mm": op.width_mm,
                        "h_mm": op.head_mm - op.sill_mm,
                        "kind": "opening",
                        "id": f"{op.wall_id}:{op.offset_mm}",
                        "wall_id": op.wall_id,
                        "offset_mm": op.offset_mm,
                    })
    return rects


def elevation_parity_report(
    model, side: str, tolerance_mm: float = 50.0, exclude: set[str] | None = None
) -> dict:
    if exclude is None:
        exclude = set()
    ref_items = build_elevation(model, side)
    ref_silhouette = [
        {"x_mm": it["x"], "y_mm": it["z"], "w_mm": it["w"], "h_mm": it["h"]}
        for it in ref_items
        if it["kind"] == "wall" and it["w"] > 0 and it["h"] > 0
    ]
    cand_rects = _candidate_rects(model, side)
    cand_silhouette = [r for r in cand_rects if r["kind"] == "wall"]
    ref_openings2: list[dict] = []
    for storey in model.storeys:
        for wall in storey.walls:
            parallel = (
                (side in ("north", "south") and wall.orientation == "horizontal")
                or (side in ("east", "west") and wall.orientation == "vertical")
            )
            if not parallel:
                continue
            from homedesign.elevation import _project_box, _opening_h

            h0_wall, _, _ = _project_box(side, model, wall.x, wall.y, wall.w, wall.h)
            for op in storey.openings:
                if op.wall_id != wall.id:
                    continue
                ox = _opening_h(wall, op, side, h0_wall)
                ref_openings2.append({
                    "x_mm": ox,
                    "y_mm": storey.base_z + op.sill_mm,
                    "w_mm": op.width_mm,
                    "h_mm": op.head_mm - op.sill_mm,
                    "id": f"{op.wall_id}:{op.offset_mm}",
                })
    if not cand_silhouette:
        raise ValueError(f"elevation_parity_report: empty candidate silhouette for side {side!r}")
    if not ref_silhouette:
        raise ValueError(f"elevation_parity_report: empty reference silhouette for side {side!r}")
    sil_dev = silhouette_deviation(ref_silhouette, cand_silhouette)
    open_dev, unmatched = opening_deviation(
        ref_openings2, [r for r in cand_rects if r["kind"] == "opening"], exclude
    )
    passed = sil_dev <= tolerance_mm and open_dev <= tolerance_mm and len(unmatched) == 0
    return {
        "side": side,
        "silhouette_mm": float(sil_dev),
        "opening_mm": float(open_dev),
        "unmatched": unmatched,
        "passed": bool(passed),
    }
