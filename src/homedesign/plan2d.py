"""Pure-Python 2D floor plans: SVG (viewing) + DXF (CAD) from a CompiledModel.

Both writers walk the same compiled model directly -- there is no
FreeCAD/Draft dependency anywhere in this module.
"""
from __future__ import annotations

from pathlib import Path

import ezdxf

from .model import CompiledModel, Storey
from .xmltext import escape_text

MM_PER_PX = 10.0  # SVG viewport scale: 1px = 10mm
MARGIN_MM = 1000.0

ROOM_FILL = {
    "bedroom": "#e8d9c3", "bathroom": "#cfe3e8", "kitchen": "#e8cfc3",
    "living": "#e3e8cf", "dining": "#e3e8cf", "hall": "#eeeeee",
    "stairwell": "#d9d9d9", "garage": "#c9c9c9", "balcony": "#d9e8d0",
    "office": "#e0e0d0", "storage": "#dcdcdc", "elevator": "#c9c9d9",
    "terrace": "#d9e8d0", "wc": "#cfe3e8", "utility": "#dcdcdc", "courtyard": "#e8f0e0",
}


def write_plans(model: CompiledModel, out_dir: Path) -> list[Path]:
    svg_dir = out_dir / "svg"
    dxf_dir = out_dir / "dxf"
    svg_dir.mkdir(parents=True, exist_ok=True)
    dxf_dir.mkdir(parents=True, exist_ok=True)

    paths = []
    for storey in model.storeys:
        svg_path = svg_dir / f"{model.name}_f{storey.level}.svg"
        svg_path.write_text(_render_svg(model, storey), encoding="utf-8")
        paths.append(svg_path)

        dxf_path = dxf_dir / f"{model.name}_f{storey.level}.dxf"
        _render_dxf(model, storey, dxf_path)
        paths.append(dxf_path)

    # The complete drawing set: four elevations and two sections alongside the
    # per-storey plans (lazy import avoids a module cycle).
    from .elevation import write_elevations, write_sections
    paths.extend(write_elevations(model, out_dir))
    paths.extend(write_sections(model, out_dir))
    return paths


def _mm_to_px(v: float) -> float:
    return (v + MARGIN_MM) / MM_PER_PX


def _render_svg(model: CompiledModel, storey: Storey) -> str:
    width_px = _mm_to_px(model.plot_width_mm) + MARGIN_MM / MM_PER_PX
    depth_px = _mm_to_px(model.plot_depth_mm) + MARGIN_MM / MM_PER_PX

    # viewBox only (no fixed width/height) so the PDF's per-storey plan pages
    # scale to fit one A3 sheet (TASK-06-02).
    parts = [f'<svg xmlns="http://www.w3.org/2000/svg" '
             f'viewBox="0 0 {width_px:.0f} {depth_px:.0f}" '
             f'preserveAspectRatio="xMidYMid meet" font-family="sans-serif">']
    parts.append(f'<rect x="0" y="0" width="{width_px:.0f}" height="{depth_px:.0f}" fill="white"/>')
    parts.append(
        '<defs><pattern id="voidhatch" width="8" height="8" patternTransform="rotate(45)" '
        'patternUnits="userSpaceOnUse">'
        '<line x1="0" y1="0" x2="0" y2="8" stroke="#888" stroke-width="1.5"/></pattern></defs>'
    )

    for room in storey.rooms:
        fill = ROOM_FILL.get(room.type, "#f0f0f0")
        x, y = _mm_to_px(room.rect.x), _mm_to_px(room.rect.y)
        w, d = room.rect.w / MM_PER_PX, room.rect.d / MM_PER_PX
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{d:.1f}" '
                     f'fill="{fill}" stroke="none"/>')
        cx, cy = x + w / 2, y + d / 2
        area_sqm = (room.rect.w / 1000) * (room.rect.d / 1000)
        label = escape_text(room.name or room.id)
        parts.append(f'<text x="{cx:.1f}" y="{cy:.1f}" font-size="12" text-anchor="middle" fill="#333">'
                     f'{label}</text>')
        parts.append(f'<text x="{cx:.1f}" y="{cy + 14:.1f}" font-size="10" text-anchor="middle" fill="#666">'
                     f'{escape_text(f"{area_sqm:.1f} m")}&#178;</text>')

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

    # Declared floor voids: diagonal-hatched with an optional reason label.
    for void, reason in zip(storey.authored_voids, storey.authored_void_reasons):
        x, y = _mm_to_px(void.x), _mm_to_px(void.y)
        w, d = void.w / MM_PER_PX, void.d / MM_PER_PX
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{d:.1f}" '
                     f'fill="url(#voidhatch)" stroke="#888" stroke-width="0.8"/>')
        if reason:
            cx, cy = x + w / 2, y + d / 2
            parts.append(f'<text x="{cx:.1f}" y="{cy:.1f}" font-size="10" text-anchor="middle" '
                         f'fill="#555">{escape_text(reason)}</text>')

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

    # Per-storey dimension chains: one above the plan and one to its left, at
    # every distinct room-boundary coordinate (room edges = where walls sit).
    h_coords = sorted({c for r in storey.rooms for c in (r.rect.x, r.rect.x2)})
    v_coords = sorted({c for r in storey.rooms for c in (r.rect.y, r.rect.y2)})
    parts.append(_dimension_chain(h_coords, "h", 40.0, model.plot_width_mm))
    parts.append(_dimension_chain(v_coords, "v", 40.0, model.plot_depth_mm))

    # Graphic furniture of the drawing (TASK-06-04): north arrow top-left,
    # scale bar bottom-left, title block bottom-right.
    parts.append(_north_arrow(model.north_deg))
    parts.append(_scale_bar(depth_px))
    parts.append(_title_block(width_px, depth_px, [
        model.name,
        storey.name or f"Storey {storey.level}",
        f"Plot {model.plot_width_mm / 1000:.1f} m x {model.plot_depth_mm / 1000:.1f} m",
        "Scale: use the graphic bar",
    ]))

    parts.append("</svg>")
    return "\n".join(parts)


def _svg_opening(wall, opening) -> str:
    off = opening.offset_mm / MM_PER_PX
    width = opening.width_mm / MM_PER_PX
    if wall.orientation == "vertical":
        x = _mm_to_px(wall.x + wall.thickness / 2)
        y = _mm_to_px(wall.y) + off
        color = "#3a7bd5" if opening.type == "window" else "#c0392b"
        if opening.type == "window":
            # Three-line window symbol: centre line + two frame lines.
            return (
                f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y + width:.1f}" stroke="{color}" stroke-width="3"/>'
                f'<line x1="{x - 3:.1f}" y1="{y:.1f}" x2="{x - 3:.1f}" y2="{y + width:.1f}" stroke="{color}" stroke-width="0.8"/>'
                f'<line x1="{x + 3:.1f}" y1="{y:.1f}" x2="{x + 3:.1f}" y2="{y + width:.1f}" stroke="{color}" stroke-width="0.8"/>'
            )
        # Door: leaf line plus swing arc quarter-circle from the hinge jamb.
        return _svg_door_vertical(x, y, width)
    x = _mm_to_px(wall.x) + off
    y = _mm_to_px(wall.y + wall.thickness / 2)
    color = "#3a7bd5" if opening.type == "window" else "#c0392b"
    if opening.type == "window":
        return (
            f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + width:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="3"/>'
            f'<line x1="{x:.1f}" y1="{y - 3:.1f}" x2="{x + width:.1f}" y2="{y - 3:.1f}" stroke="{color}" stroke-width="0.8"/>'
            f'<line x1="{x:.1f}" y1="{y + 3:.1f}" x2="{x + width:.1f}" y2="{y + 3:.1f}" stroke="{color}" stroke-width="0.8"/>'
        )
    return _svg_door_horizontal(x, y, width)


def _svg_door_vertical(x, y, width):
    """Door on a vertical wall (runs along y). Hinge at the top jamb (y),
    leaf swings to the east (increasing x, away from the wall centreline).
    Quarter-circle arc: A rx ry 0 0 1 dx dy."""
    color = "#c0392b"
    leaf = f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x + width:.1f}" y2="{y:.1f}" stroke="{color}" stroke-width="1.2"/>'
    arc = f'<path d="M {x:.1f} {y:.1f} A {width:.1f} {width:.1f} 0 0 1 {x:.1f} {y + width:.1f}" ' \
          f'fill="none" stroke="{color}" stroke-width="0.8"/>'
    return leaf + arc


def _svg_door_horizontal(x, y, width):
    """Door on a horizontal wall (runs along x). Hinge at the left jamb (x),
    leaf swings south (increasing y, away from the wall centreline)."""
    color = "#c0392b"
    leaf = f'<line x1="{x:.1f}" y1="{y:.1f}" x2="{x:.1f}" y2="{y + width:.1f}" stroke="{color}" stroke-width="1.2"/>'
    arc = f'<path d="M {x:.1f} {y:.1f} A {width:.1f} {width:.1f} 0 0 1 {x + width:.1f} {y:.1f}" ' \
          f'fill="none" stroke="{color}" stroke-width="0.8"/>'
    return leaf + arc


def _north_arrow(north_deg: float = 0.0) -> str:
    """North points toward -y (up-screen) by default; rotated by the declared
    `site.north_deg` compass bearing."""
    cx, cy = 70.0, 60.0
    rot = f" rotate({north_deg:.1f})" if north_deg else ""
    return (
        f'<g transform="translate({cx},{cy}){rot}">'
        f'<path d="M 0 26 L -9 -8 L 0 -2 L 9 -8 Z" fill="#222"/>'
        f'<text x="0" y="-14" font-size="12" text-anchor="middle" fill="#222" font-weight="bold">N</text>'
        f'</g>'
    )


def _scale_bar(height_px: float) -> str:
    """Graphic scale bar in metres: 5 segments of 1m each (5m total).
    Placed bottom-left, clear of the dimension line on the left edge.
    Shared by plan and elevation/section drawings."""
    seg = 100.0  # px per metre at 10 mm/px
    x0 = 70.0
    y0 = height_px - 60.0
    parts = [f'<g transform="translate({x0},{y0})">']
    for i in range(5):
        fill = "#222" if i % 2 == 0 else "#fff"
        parts.append(f'<rect x="{i * seg:.1f}" y="0" width="{seg:.1f}" height="14" fill="{fill}" stroke="#222" stroke-width="0.8"/>')
        if i < 5:
            parts.append(f'<text x="{i * seg + seg / 2:.1f}" y="26" font-size="10" text-anchor="middle" fill="#222">{i + 1}</text>')
    parts.append('<text x="-6" y="26" font-size="10" text-anchor="end" fill="#222">0</text>')
    parts.append('<text x="250.0" y="42" font-size="10" text-anchor="middle" fill="#666">m</text>')
    parts.append("</g>")
    return "\n".join(parts)


def _title_block(width_px: float, height_px: float, lines: list[str]) -> str:
    """Title block in the lower-right corner. Shared by plan and
    elevation/section drawings; `lines` carries the drawing title."""
    bw, bh = 360.0, 100.0
    x0 = width_px - bw - 40.0
    y0 = height_px - bh - 40.0
    parts = [f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{bw:.1f}" height="{bh:.1f}" fill="white" stroke="#222" stroke-width="1.2"/>']
    for i, line in enumerate(lines):
        parts.append(f'<text x="{x0 + 12:.1f}" y="{y0 + 22 + i * 20:.1f}" font-size="11" fill="#222">{escape_text(line)}</text>')
    return "\n".join(parts)


def _dim_line(x1, y1, x2, y2, label, vertical) -> str:
    line = f'<line x1="{x1:.1f}" y1="{y1:.1f}" x2="{x2:.1f}" y2="{y2:.1f}" stroke="#000" stroke-width="0.5"/>'
    label = escape_text(label)
    if vertical:
        text = f'<text x="{x1-4:.1f}" y="{(y1+y2)/2:.1f}" font-size="10" text-anchor="middle" ' \
               f'transform="rotate(-90 {x1-4:.1f} {(y1+y2)/2:.1f})">{label}</text>'
    else:
        text = f'<text x="{(x1+x2)/2:.1f}" y="{y1-4:.1f}" font-size="10" text-anchor="middle">{label}</text>'
    return line + text


def _dxf_pt(x_mm: float, y_mm: float, plot_depth_mm: float) -> tuple[float, float]:
    """Model point (mm) -> DXF/CAD point with the y axis flipped.

    SVG y grows downward, DXF/CAD y grows upward; this single helper is the
    only place the flip happens (TASK-06-05).
    """
    return (x_mm, plot_depth_mm - y_mm)


def _dimension_chain(coords_mm: list[float], axis: str, offset_px: float, extent_mm: float) -> str:
    """SVG fragment for one dimension chain: a run line, a tick at each
    coordinate, and a millimetre integer label centred between consecutive
    coordinates. `axis` is `"h"` (drawn above the plan) or `"v"` (drawn to its
    left); `offset_px` is the distance from the plan edge; `extent_mm` is the
    overall plot dimension along that axis (used for the degenerate empty case).
    """
    margin_px = MARGIN_MM / MM_PER_PX

    def to_px(v: float) -> float:
        return (v + MARGIN_MM) / MM_PER_PX

    parts: list[str] = []
    if len(coords_mm) < 2:
        # Degenerate input: only the overall dimension, no ticks.
        if axis == "h":
            y = margin_px - offset_px
            parts.append(f'<text x="{to_px(extent_mm / 2):.1f}" y="{y - 4:.1f}" '
                         f'font-size="10" text-anchor="middle">{int(round(extent_mm))}</text>')
        else:
            x = margin_px - offset_px
            parts.append(f'<text x="{x - 4:.1f}" y="{to_px(extent_mm / 2):.1f}" font-size="10" '
                         f'text-anchor="middle" transform="rotate(-90 {x - 4:.1f} {to_px(extent_mm / 2):.1f})">'
                         f'{int(round(extent_mm))}</text>')
        return "\n".join(parts)

    start, end = coords_mm[0], coords_mm[-1]
    if axis == "h":
        y = margin_px - offset_px
        parts.append(f'<rect x="{to_px(start):.1f}" y="{y - 0.25:.1f}" '
                     f'width="{to_px(end) - to_px(start):.1f}" height="0.5" fill="#000"/>')
        for v in coords_mm:
            parts.append(f'<line x1="{to_px(v):.1f}" y1="{y - 3:.1f}" x2="{to_px(v):.1f}" '
                         f'y2="{y + 3:.1f}" stroke="#000" stroke-width="0.5"/>')
        for a, b in zip(coords_mm, coords_mm[1:]):
            mid = (a + b) / 2
            parts.append(f'<text x="{to_px(mid):.1f}" y="{y - 6:.1f}" font-size="10" '
                         f'text-anchor="middle">{int(round(b - a))}</text>')
    else:
        x = margin_px - offset_px
        parts.append(f'<rect x="{x - 0.25:.1f}" y="{to_px(start):.1f}" '
                     f'width="0.5" height="{to_px(end) - to_px(start):.1f}" fill="#000"/>')
        for v in coords_mm:
            parts.append(f'<line x1="{x - 3:.1f}" y1="{to_px(v):.1f}" x2="{x + 3:.1f}" '
                         f'y2="{to_px(v):.1f}" stroke="#000" stroke-width="0.5"/>')
        for a, b in zip(coords_mm, coords_mm[1:]):
            mid = (a + b) / 2
            parts.append(f'<text x="{x - 6:.1f}" y="{to_px(mid):.1f}" font-size="10" '
                         f'text-anchor="middle" transform="rotate(-90 {x - 6:.1f} {to_px(mid):.1f})">'
                         f'{int(round(b - a))}</text>')
    return "\n".join(parts)


def _dxf_dimension_chain(msp, coords, axis, offset_mm, plot_depth):
    """Replicate one dimension chain onto the DXF `DIMS` layer."""
    if len(coords) < 2:
        return
    if axis == "h":
        y = -offset_mm
        msp.add_line(_dxf_pt(coords[0], y, plot_depth), _dxf_pt(coords[-1], y, plot_depth),
                     dxfattribs={"layer": "DIMS"})
        for v in coords:
            msp.add_line(_dxf_pt(v, 0.0, plot_depth), _dxf_pt(v, y, plot_depth),
                         dxfattribs={"layer": "DIMS"})
        for a, b in zip(coords, coords[1:]):
            mid = (a + b) / 2
            mx, my = _dxf_pt(mid, y, plot_depth)
            msp.add_text(str(int(round(b - a))), dxfattribs={"layer": "DIMS", "height": 150}).set_placement(
                (mx, my + 150), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER
            )
    else:
        x = -offset_mm
        msp.add_line(_dxf_pt(x, coords[0], plot_depth), _dxf_pt(x, coords[-1], plot_depth),
                     dxfattribs={"layer": "DIMS"})
        for v in coords:
            msp.add_line(_dxf_pt(0.0, v, plot_depth), _dxf_pt(x, v, plot_depth),
                         dxfattribs={"layer": "DIMS"})
        for a, b in zip(coords, coords[1:]):
            mid = (a + b) / 2
            mx, my = _dxf_pt(x, mid, plot_depth)
            msp.add_text(str(int(round(b - a))), dxfattribs={"layer": "DIMS", "height": 150}).set_placement(
                (mx - 150, my), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER
            )


def _render_dxf(model: CompiledModel, storey: Storey, out_path: Path) -> None:
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    for layer, color in [("WALLS", 7), ("DOORS", 1), ("WINDOWS", 5), ("STAIRS", 3), ("TEXT", 2), ("DIMS", 8), ("VOIDS", 4)]:
        doc.layers.add(layer, color=color)
    msp = doc.modelspace()
    plot_depth = model.plot_depth_mm

    for wall in storey.walls:
        pts = [_dxf_pt(wall.x, wall.y, plot_depth),
               _dxf_pt(wall.x + wall.w, wall.y, plot_depth),
               _dxf_pt(wall.x + wall.w, wall.y + wall.h, plot_depth),
               _dxf_pt(wall.x, wall.y + wall.h, plot_depth)]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "WALLS"})

    for opening in storey.openings:
        wall = next((w for w in storey.walls if w.id == opening.wall_id), None)
        if wall is None:
            continue
        layer = "DOORS" if opening.type == "door" else "WINDOWS"
        wmm = opening.width_mm
        if wall.orientation == "vertical":
            x = wall.x + wall.thickness / 2
            y0 = wall.y + opening.offset_mm
            y1 = y0 + opening.width_mm
            x_f, y0_f = _dxf_pt(x, y0, plot_depth)
            _, y1_f = _dxf_pt(x, y1, plot_depth)
            if opening.type == "door":
                # Leaf line + swing arc from the hinge jamb (top, i.e. larger
                # DXF y after the flip). Arc sweeps toward the interior side.
                msp.add_line((x_f, y0_f), (x_f + wmm, y0_f), dxfattribs={"layer": layer})
                msp.add_arc((x_f, y0_f), radius=wmm, start_angle=0, end_angle=90,
                            dxfattribs={"layer": layer})
            else:
                # Three-line window symbol on the wall centreline.
                msp.add_line((x_f - 3, y0_f), (x_f - 3, y1_f), dxfattribs={"layer": layer})
                msp.add_line((x_f, y0_f), (x_f, y1_f), dxfattribs={"layer": layer})
                msp.add_line((x_f + 3, y0_f), (x_f + 3, y1_f), dxfattribs={"layer": layer})
        else:
            y = wall.y + wall.thickness / 2
            x0 = wall.x + opening.offset_mm
            x1 = x0 + opening.width_mm
            y_f, x0_f = _dxf_pt(x0, y, plot_depth)
            x1_f, _ = _dxf_pt(x1, y, plot_depth)
            if opening.type == "door":
                msp.add_line((x0_f, y_f), (x0_f, y_f + wmm), dxfattribs={"layer": layer})
                msp.add_arc((x0_f, y_f), radius=wmm, start_angle=90, end_angle=180,
                            dxfattribs={"layer": layer})
            else:
                msp.add_line((x0_f, y_f - 3), (x1_f, y_f - 3), dxfattribs={"layer": layer})
                msp.add_line((x0_f, y_f), (x1_f, y_f), dxfattribs={"layer": layer})
                msp.add_line((x0_f, y_f + 3), (x1_f, y_f + 3), dxfattribs={"layer": layer})

    for room in storey.rooms:
        cx = room.rect.x + room.rect.w / 2
        cy = room.rect.y + room.rect.d / 2
        cx_f, cy_f = _dxf_pt(cx, cy, plot_depth)
        label = room.name or room.id
        msp.add_text(label, dxfattribs={"layer": "TEXT", "height": 150}).set_placement(
            (cx_f, cy_f), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

    for void in storey.authored_voids:
        pts = [_dxf_pt(void.x, void.y, plot_depth),
               _dxf_pt(void.x + void.w, void.y, plot_depth),
               _dxf_pt(void.x + void.w, void.y + void.d, plot_depth),
               _dxf_pt(void.x, void.y + void.d, plot_depth)]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "VOIDS"})

    h_coords = sorted({c for r in storey.rooms for c in (r.rect.x, r.rect.x2)})
    v_coords = sorted({c for r in storey.rooms for c in (r.rect.y, r.rect.y2)})
    _dxf_dimension_chain(msp, h_coords, "h", 500.0, plot_depth)
    _dxf_dimension_chain(msp, v_coords, "v", 500.0, plot_depth)

    if storey.stairs:
        for t in storey.stairs.treads:
            pts = [_dxf_pt(t.x, t.y, plot_depth),
                   _dxf_pt(t.x + t.w, t.y, plot_depth),
                   _dxf_pt(t.x + t.w, t.y + t.d, plot_depth),
                   _dxf_pt(t.x, t.y + t.d, plot_depth)]
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "STAIRS"})

    doc.saveas(out_path)
