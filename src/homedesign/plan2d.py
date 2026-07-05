"""Pure-Python 2D floor plans: SVG (viewing) + DXF (CAD) from a CompiledModel.

Both writers walk the same compiled model directly -- there is no
FreeCAD/Draft dependency anywhere in this module.
"""
from __future__ import annotations

import math
from pathlib import Path

import ezdxf

from .model import CompiledModel, Storey

MM_PER_PX = 10.0  # SVG viewport scale: 1px = 10mm
MARGIN_MM = 1000.0

ROOM_FILL = {
    "bedroom": "#e8d9c3", "bathroom": "#cfe3e8", "kitchen": "#e8cfc3",
    "living": "#e3e8cf", "dining": "#e3e8cf", "hall": "#eeeeee",
    "stairwell": "#d9d9d9", "garage": "#c9c9c9", "balcony": "#d9e8d0",
    "office": "#e0e0d0", "storage": "#dcdcdc", "elevator": "#c9c9d9",
}


def write_plans(model: CompiledModel, out_dir: Path) -> list[Path]:
    svg_dir = out_dir / "svg"
    dxf_dir = out_dir / "dxf"
    svg_dir.mkdir(parents=True, exist_ok=True)
    dxf_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for storey in model.storeys:
        svg_path = svg_dir / f"{model.name}_f{storey.level}.svg"
        svg_path.write_text(_render_svg(model, storey))
        paths.append(svg_path)

        dxf_path = dxf_dir / f"{model.name}_f{storey.level}.dxf"
        _render_dxf(model, storey, dxf_path)
        paths.append(dxf_path)
    return paths


def _mm_to_px(v: float) -> float:
    return (v + MARGIN_MM) / MM_PER_PX


def _render_svg(model: CompiledModel, storey: Storey) -> str:
    width_px = _mm_to_px(model.plot_width_mm) + MARGIN_MM / MM_PER_PX
    depth_px = _mm_to_px(model.plot_depth_mm) + MARGIN_MM / MM_PER_PX

    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" width="{width_px:.0f}" height="{depth_px:.0f}" '
             f'viewBox="0 0 {width_px:.0f} {depth_px:.0f}" font-family="sans-serif">']
    parts.append(f'<rect x="0" y="0" width="{width_px:.0f}" height="{depth_px:.0f}" fill="white"/>')

    for room in storey.rooms:
        fill = ROOM_FILL.get(room.type, "#f0f0f0")
        x, y = _mm_to_px(room.rect.x), _mm_to_px(room.rect.y)
        w, d = room.rect.w / MM_PER_PX, room.rect.d / MM_PER_PX
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{d:.1f}" '
                     f'fill="{fill}" stroke="none"/>')
        cx, cy = x + w / 2, y + d / 2
        area_sqm = (room.rect.w / 1000) * (room.rect.d / 1000)
        parts.append(f'<text x="{cx:.1f}" y="{cy:.1f}" font-size="12" text-anchor="middle" fill="#333">'
                      f'{room.id}</text>')
        parts.append(f'<text x="{cx:.1f}" y="{cy + 14:.1f}" font-size="10" text-anchor="middle" fill="#666">'
                      f'{area_sqm:.1f} m&#178;</text>')

    for wall in storey.walls:
        x, y = _mm_to_px(wall.x), _mm_to_px(wall.y)
        w, h = wall.w / MM_PER_PX, wall.h / MM_PER_PX
        stroke = "#222" if wall.kind == "exterior" else "#888"
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{stroke}"/>')

    for opening in storey.openings:
        wall = next((w for w in storey.walls if w.id == opening.wall_id), None)
        if wall is None:
            continue
        parts.append(_svg_opening(wall, opening))

    if storey.stairs:
        for t in storey.stairs.treads:
            x, y = _mm_to_px(t.x), _mm_to_px(t.y)
            w, d = t.w / MM_PER_PX, t.d / MM_PER_PX
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{d:.1f}" '
                         f'fill="none" stroke="#555" stroke-width="1"/>')

    # Plot dimension lines.
    parts.append(_dim_line(MARGIN_MM / MM_PER_PX - 40, _mm_to_px(0), MARGIN_MM / MM_PER_PX - 40,
                            _mm_to_px(model.plot_depth_mm), f"{model.plot_depth_mm/1000:.1f} m", vertical=True))
    parts.append(_dim_line(_mm_to_px(0), depth_px - 20, _mm_to_px(model.plot_width_mm), depth_px - 20,
                            f"{model.plot_width_mm/1000:.1f} m", vertical=False))

    parts.append("</svg>")
    return "\n".join(parts)


def _svg_opening(wall, opening) -> str:
    off = opening.offset_mm / MM_PER_PX
    width = opening.width_mm / MM_PER_PX
    if wall.orientation == "vertical":
        x = _mm_to_px(wall.x + wall.thickness / 2)
        y = _mm_to_px(wall.y) + off
        color = "#3a7bd5" if opening.type == "window" else "#c0392b"
        return f'<rect x="{x-2:.1f}" y="{y:.1f}" width="4" height="{width:.1f}" fill="{color}"/>'
    x = _mm_to_px(wall.x) + off
    y = _mm_to_px(wall.y + wall.thickness / 2)
    color = "#3a7bd5" if opening.type == "window" else "#c0392b"
    return f'<rect x="{x:.1f}" y="{y-2:.1f}" width="{width:.1f}" height="4" fill="{color}"/>'


def _dim_line(x1, y1, x2, y2, label, vertical) -> str:
    line = f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#000" stroke-width="0.5"/>'
    if vertical:
        text = f'<text x="{x1-4:.1f}" y="{(y1+y2)/2:.1f}" font-size="10" text-anchor="middle" ' \
               f'transform="rotate(-90 {x1-4:.1f} {(y1+y2)/2:.1f})">{label}</text>'
    else:
        text = f'<text x="{(x1+x2)/2:.1f}" y="{y1-4:.1f}" font-size="10" text-anchor="middle">{label}</text>'
    return line + text


def _render_dxf(model: CompiledModel, storey: Storey, out_path: Path) -> None:
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    for layer, color in [("WALLS", 7), ("DOORS", 1), ("WINDOWS", 5), ("STAIRS", 3), ("TEXT", 2), ("DIMS", 8)]:
        doc.layers.add(layer, color=color)
    msp = doc.modelspace()

    for wall in storey.walls:
        pts = [(wall.x, wall.y), (wall.x + wall.w, wall.y),
                (wall.x + wall.w, wall.y + wall.h), (wall.x, wall.y + wall.h)]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "WALLS"})

    for opening in storey.openings:
        wall = next((w for w in storey.walls if w.id == opening.wall_id), None)
        if wall is None:
            continue
        layer = "DOORS" if opening.type == "door" else "WINDOWS"
        if wall.orientation == "vertical":
            x = wall.x + wall.thickness / 2
            y0 = wall.y + opening.offset_mm
            y1 = y0 + opening.width_mm
            msp.add_line((x, y0), (x, y1), dxfattribs={"layer": layer})
        else:
            y = wall.y + wall.thickness / 2
            x0 = wall.x + opening.offset_mm
            x1 = x0 + opening.width_mm
            msp.add_line((x0, y), (x1, y), dxfattribs={"layer": layer})

    for room in storey.rooms:
        cx = room.rect.x + room.rect.w / 2
        cy = room.rect.y + room.rect.d / 2
        msp.add_text(room.id, dxfattribs={"layer": "TEXT", "height": 150}).set_placement((cx, cy))

    if storey.stairs:
        for t in storey.stairs.treads:
            pts = [(t.x, t.y), (t.x + t.w, t.y), (t.x + t.w, t.y + t.d), (t.x, t.y + t.d)]
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "STAIRS"})

    doc.saveas(out_path)
