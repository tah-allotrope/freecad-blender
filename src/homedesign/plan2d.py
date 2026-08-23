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


def _y(v: float, depth_mm: float) -> float:
    """Model y (mm; 0 = street, plot_depth_mm = rear) -> SVG y with the REAR
    at the TOP of the sheet, the way the contractor plans are drawn (C1).
    The single place the plan orientation flip happens for SVG."""
    return (depth_mm - v) / MM_PER_PX


def _level_text(level_mm: float) -> str:
    """A finished-floor level in the sheets' own notation: ± 0.000 / + 0.100."""
    if level_mm == 0:
        return "± 0.000"
    sign = "+" if level_mm > 0 else "-"
    return f"{sign} {abs(level_mm) / 1000:.3f}"


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
    parts.append(
        '<defs><pattern id="elevhatch" width="8" height="8" patternUnits="userSpaceOnUse">'
        '<line x1="0" y1="0" x2="8" y2="8" stroke="#888" stroke-width="1"/>'
        '<line x1="8" y1="0" x2="0" y2="8" stroke="#888" stroke-width="1"/></pattern></defs>'
    )

    depth = model.plot_depth_mm
    for room in storey.rooms:
        if room.type == "elevator":
            fill = "url(#elevhatch)"
        else:
            fill = ROOM_FILL.get(room.type, "#f0f0f0")
        x, y = _mm_to_px(room.rect.x), _y(room.rect.y2, depth)
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
        if room.level_mm is not None:
            datum = _level_text(storey.base_z + room.level_mm)
            parts.append(f'<text class="level-marker" x="{cx:.1f}" y="{cy + 28:.1f}" font-size="10" '
                         f'text-anchor="middle" fill="#222">{escape_text(datum)}</text>')

    for wall in storey.walls:
        x, y = _mm_to_px(wall.x), _y(wall.y + wall.h, depth)
        w, h = wall.w / MM_PER_PX, wall.h / MM_PER_PX
        stroke = "#222" if wall.kind == "exterior" else "#888"
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{h:.1f}" fill="{stroke}"/>')

    for opening in storey.openings:
        wall = next((w for w in storey.walls if w.id == opening.wall_id), None)
        if wall is None:
            continue
        parts.append(_svg_opening(wall, opening, depth))

    # Declared floor voids: diagonal-hatched; the primary label repeats the
    # name(s) of the room(s) on the storey below (largest overlap first), as
    # the drawing does over its hatched lửng zones.
    for void, reason in zip(storey.authored_voids, storey.authored_void_reasons):
        x, y = _mm_to_px(void.x), _y(void.y + void.d, depth)
        w, d = void.w / MM_PER_PX, void.d / MM_PER_PX
        parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{d:.1f}" '
                     f'fill="url(#voidhatch)" stroke="#888" stroke-width="0.8"/>')
        cx, cy = x + w / 2, y + d / 2
        below_names = _void_below_names(model, storey, void)
        if below_names:
            parts.append(f'<text x="{cx:.1f}" y="{cy:.1f}" font-size="12" text-anchor="middle" '
                         f'fill="#333">{escape_text(below_names)}</text>')
        if reason:
            dy = 14 if below_names else 0
            parts.append(f'<text x="{cx:.1f}" y="{cy + dy:.1f}" font-size="10" text-anchor="middle" '
                         f'fill="#555">{escape_text(reason)}</text>')

    # Furniture, drawn from the same pure placement rules the Blender builder
    # uses (placement.plan_room), so a furnished 3D scene and its plan can no
    # longer disagree -- they did until 2026-08-17, see the fidelity ledger.
    parts.append(_svg_furniture(storey, depth))

    if storey.stairs:
        for i, t in enumerate(storey.stairs.treads, start=1):
            x, y = _mm_to_px(t.x), _y(t.y + t.d, depth)
            w, d = t.w / MM_PER_PX, t.d / MM_PER_PX
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{d:.1f}" '
                         f'fill="none" stroke="#555" stroke-width="1"/>')
            # Tread numbering, as the contractor sheets number the run: odd
            # tread numbers only (the riser each tread leads to), so a 22-riser
            # flight reads 1,3,...,21 up and 21,...,13 on the return.
            if i % 2 == 1:
                parts.append(f'<text class="tread-number" x="{x + w / 2:.1f}" y="{y + d / 2 + 3:.1f}" '
                             f'font-size="7" text-anchor="middle" fill="#555">{i}</text>')

    # Dimension stacks, inner to outer: fine room subdivision, then full-span
    # band divisions, then the overall figure -- the 2-3 tiers per side the
    # contractor sheets carry. The overall extent is the outermost tier here,
    # so the old separate metre-labelled plot line would now duplicate it.
    for tier, coords in enumerate(
            _dimension_tiers(storey.rooms, "h", model.plot_width_mm, model.plot_depth_mm), start=1):
        parts.append(_dimension_chain(coords, "h", 40.0 * tier, model.plot_width_mm, tier=tier))
    for tier, coords in enumerate(
            _dimension_tiers(storey.rooms, "v", model.plot_depth_mm, model.plot_width_mm), start=1):
        parts.append(_dimension_chain(coords, "v", 40.0 * tier, model.plot_depth_mm,
                                      tier=tier, plot_depth_mm=depth))

    # Section cut lines, and the storey's finished-floor level (per-room
    # markers win; the storey datum is the fallback when no room carries one).
    parts.append(_svg_section_markers(model, storey))
    if not any(r.level_mm is not None for r in storey.rooms):
        parts.append(_svg_level_marker(storey))

    # Text callouts (dashed box + italic label); never geometry.
    parts.append(_svg_annotations(storey, depth))

    # Legal plot perimeter, dash-dot per drawing convention, drawn last so it
    # reads over any room fill it happens to coincide with at the plot edge.
    parts.append(_svg_plot_boundary(model))
    parts.append(_svg_setbacks(model))

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


def _svg_furniture(storey, depth: float) -> str:
    """Plan footprints for every furnishable room on this storey.

    Deliberately calls the same `placement.plan_room` the Blender furnisher
    calls, with the same interior-rect preference and the same room-local ->
    world mapping, so the two views cannot drift apart. `FurnitureItem.x/.y`
    is the footprint's min corner in room-local metres and `rot_deg` turns it
    about the footprint centre (see `procedural_furniture._placer_for`).
    """
    from .placement import plan_room

    parts = ['<g class="furniture" fill="none" stroke="#8a8375" stroke-width="0.8">']
    for room in storey.rooms:
        rect = room.interior or room.rect
        for item in plan_room(room.type, rect.w / 1000, rect.d / 1000):
            x_mm = rect.x + item.x * 1000
            y_mm = rect.y + item.y * 1000
            w_px, d_px = item.w * 1000 / MM_PER_PX, item.d * 1000 / MM_PER_PX
            x_px, y_px = _mm_to_px(x_mm), _y(y_mm + item.d * 1000, depth)
            cx, cy = x_px + w_px / 2, y_px + d_px / 2
            # SVG's y axis runs down while the model's runs north, so the plan
            # is mirrored and a model-space CCW rotation reads as CW here.
            transform = (f' transform="rotate({-item.rot_deg:.1f} {cx:.1f} {cy:.1f})"'
                         if item.rot_deg else "")
            parts.append(f'<rect data-furniture="{item.kind}" x="{x_px:.1f}" y="{y_px:.1f}" '
                         f'width="{w_px:.1f}" height="{d_px:.1f}"{transform}/>')
    parts.append("</g>")
    return "\n".join(parts)


def _void_below_names(model: CompiledModel, storey: Storey, void) -> str:
    """Names of the rooms on the storey below whose rects overlap this void,
    largest overlap first -- the drawing repeats those names over its hatched
    double-height zones."""
    prev = next((s for s in model.storeys if s.level == storey.level - 1), None)
    if prev is None:
        return ""
    overlaps: list[tuple[float, str]] = []
    for room in prev.rooms:
        ox = min(void.x + void.w, room.rect.x2) - max(void.x, room.rect.x)
        oy = min(void.y + void.d, room.rect.y2) - max(void.y, room.rect.y)
        if ox > 0 and oy > 0:
            overlaps.append((ox * oy, room.name or room.id))
    overlaps.sort(key=lambda t: -t[0])
    return " / ".join(name for _, name in overlaps)


def _svg_level_marker(storey) -> str:
    """The storey's finished-floor level, in the sheets' own notation."""
    level = "± 0.000" if storey.base_z == 0 else f"+ {storey.base_z / 1000:.3f}"
    x, y = MARGIN_MM / MM_PER_PX, MARGIN_MM / MM_PER_PX - 14
    return (f'<g class="level-marker">'
            f'<text x="{x:.1f}" y="{y:.1f}" font-size="12" fill="#222">{escape_text(level)}</text>'
            f'</g>')


def _svg_section_markers(model, storey) -> str:
    """Cut lines for every declared section, in circle bubbles at both ends,
    labelled with the section's drawing label (fallback: uppercased name)."""
    if not model.sections:
        return ""
    depth = model.plot_depth_mm
    parts = ['<g class="section-marker">']
    for sec in model.sections:
        name = escape_text(str(sec.get("label") or sec.get("name", "")).upper())
        pos = float(sec.get("position_mm", 0.0))
        if sec.get("axis") == "x":
            # Cut plane perpendicular to x: a vertical line down the plan.
            px = _mm_to_px(pos)
            y0, y1 = _y(depth, depth) - 30, _y(0, depth) + 30
            parts.append(f'<line x1="{px:.1f}" y1="{y0:.1f}" x2="{px:.1f}" y2="{y1:.1f}" '
                         f'stroke="#c0392b" stroke-width="1" stroke-dasharray="12 4 3 4"/>')
            for cy in (y0, y1):
                parts.append(f'<circle cx="{px:.1f}" cy="{cy:.1f}" r="11" fill="white" '
                             f'stroke="#c0392b" stroke-width="1"/>')
                parts.append(f'<text x="{px:.1f}" y="{cy + 3.5:.1f}" font-size="9" '
                             f'text-anchor="middle" fill="#c0392b">{name}</text>')
        else:
            py = _y(pos, depth)
            x0, x1 = _mm_to_px(0) - 30, _mm_to_px(model.plot_width_mm) + 30
            parts.append(f'<line x1="{x0:.1f}" y1="{py:.1f}" x2="{x1:.1f}" y2="{py:.1f}" '
                         f'stroke="#c0392b" stroke-width="1" stroke-dasharray="12 4 3 4"/>')
            for cx in (x0, x1):
                parts.append(f'<circle cx="{cx:.1f}" cy="{py:.1f}" r="11" fill="white" '
                             f'stroke="#c0392b" stroke-width="1"/>')
                parts.append(f'<text x="{cx:.1f}" y="{py + 3.5:.1f}" font-size="9" '
                             f'text-anchor="middle" fill="#c0392b">{name}</text>')
    parts.append("</g>")
    return "\n".join(parts)


def _svg_plot_boundary(model) -> str:
    """The legal plot perimeter -- "ranh dat" on the contractor sheets, with
    the street-facing edge (y=0, ASM-001) called out as "Ranh lo gioi" the
    way every issued plan sheet labels it. Drawn as the schema's own
    orthogonal collapse of the plot (DEC-005): real boundaries taper, this
    line does not, matching the same simplification already baked into
    every room/wall in the model rather than adding a new one."""
    x0, y0 = _mm_to_px(0), _y(model.plot_depth_mm, model.plot_depth_mm)
    w = model.plot_width_mm / MM_PER_PX
    d = model.plot_depth_mm / MM_PER_PX
    return (
        f'<g class="plot-boundary">'
        f'<rect x="{x0:.1f}" y="{y0:.1f}" width="{w:.1f}" height="{d:.1f}" '
        f'fill="none" stroke="#555" stroke-width="1" stroke-dasharray="14 3 2 3"/>'
        f'<text x="{x0 + w / 2:.1f}" y="{y0 + d + 14:.1f}" font-size="10" text-anchor="middle" '
        f'fill="#555">Ranh lộ giới</text>'
        f'</g>'
    )


def _svg_setbacks(model) -> str:
    """The building lines ("ranh khoảng lùi"): dash-dot rules spanning the
    full plot width at the declared front/rear setback distances, labelled
    like the sheets label them. Absent when the site declares none."""
    setbacks = model.setbacks
    if not setbacks:
        return ""
    depth = model.plot_depth_mm
    x0 = _mm_to_px(0)
    x1 = _mm_to_px(model.plot_width_mm)
    parts = ['<g class="setback">']
    for key, dist, label in (
        ("front_mm", float(setbacks.get("front_mm", 0.0)), "Ranh khoảng lùi trước"),
        ("rear_mm", float(setbacks.get("rear_mm", 0.0)), "Ranh khoảng lùi sau"),
    ):
        if not setbacks.get(key):
            continue
        y = _y(depth - dist, depth)
        parts.append(f'<line x1="{x0:.1f}" y1="{y:.1f}" x2="{x1:.1f}" y2="{y:.1f}" '
                     f'stroke="#555" stroke-width="1" stroke-dasharray="14 3 2 3"/>')
        lx = x0 + 10
        parts.append(f'<text x="{lx:.1f}" y="{y - 4:.1f}" font-size="10" fill="#555" '
                     f'transform="rotate(-90 {lx:.1f} {y - 4:.1f})">{escape_text(label)}</text>')
    parts.append("</g>")
    return "\n".join(parts)


def _svg_annotations(storey: Storey, depth: float) -> str:
    """Text callouts: a dashed rectangle when `boxed`, italic centred text.
    Callouts only -- they never affect checks, tiling or furniture."""
    if not storey.annotations:
        return ""
    parts = ['<g class="annotation">']
    for ann in storey.annotations:
        x, y = _mm_to_px(float(ann["x"])), _y(float(ann["y"]) + float(ann["d"]), depth)
        w, d = float(ann["w"]) / MM_PER_PX, float(ann["d"]) / MM_PER_PX
        cx, cy = x + w / 2, y + d / 2
        if ann.get("boxed"):
            parts.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{w:.1f}" height="{d:.1f}" '
                         f'fill="none" stroke="#888" stroke-width="0.8" stroke-dasharray="6 3"/>')
        parts.append(f'<text x="{cx:.1f}" y="{cy + 3.5:.1f}" font-size="10" text-anchor="middle" '
                     f'fill="#444" font-style="italic">{escape_text(str(ann["text"]))}</text>')
    parts.append("</g>")
    return "\n".join(parts)


def _svg_opening(wall, opening, depth: float) -> str:
    off = opening.offset_mm / MM_PER_PX
    width = opening.width_mm / MM_PER_PX
    if wall.orientation == "vertical":
        x = _mm_to_px(wall.x + wall.thickness / 2)
        y = _y(wall.y + opening.offset_mm + opening.width_mm, depth)
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
    y = _y(wall.y + wall.thickness / 2, depth)
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


def _dxf_furniture(msp, storey, plot_depth: float) -> None:
    """Furniture footprints on their own layer, from the same placement rules
    the SVG and the Blender builder use."""
    import math

    from .placement import plan_room

    for room in storey.rooms:
        rect = room.interior or room.rect
        for item in plan_room(room.type, rect.w / 1000, rect.d / 1000):
            x_mm = rect.x + item.x * 1000
            y_mm = rect.y + item.y * 1000
            w_mm, d_mm = item.w * 1000, item.d * 1000
            cx, cy = x_mm + w_mm / 2, y_mm + d_mm / 2
            theta = math.radians(item.rot_deg)
            cos_t, sin_t = math.cos(theta), math.sin(theta)
            corners = []
            for dx, dy in ((-w_mm / 2, -d_mm / 2), (w_mm / 2, -d_mm / 2),
                           (w_mm / 2, d_mm / 2), (-w_mm / 2, d_mm / 2)):
                # Rotate about the footprint centre in model space, then flip
                # into DXF's y-up frame (DXF keeps model orientation, unlike
                # the mirrored SVG, so no sign change on the angle here).
                rx = cx + dx * cos_t - dy * sin_t
                ry = cy + dx * sin_t + dy * cos_t
                corners.append(_dxf_pt(rx, ry, plot_depth))
            msp.add_lwpolyline(corners, close=True, dxfattribs={"layer": "FURNITURE"})


def _dxf_pt(x_mm: float, y_mm: float, plot_depth_mm: float) -> tuple[float, float]:
    """Model point (mm) -> DXF/CAD point with the y axis flipped.

    SVG y grows downward, DXF/CAD y grows upward; this single helper is the
    only place the flip happens (TASK-06-05).
    """
    return (x_mm, plot_depth_mm - y_mm)


def _covers(intervals: list[tuple[float, float]], extent_mm: float, tol: float = 1.0) -> bool:
    """True if `intervals` tile [0, extent_mm] with no gap wider than `tol`."""
    reach = 0.0
    for lo, hi in sorted(intervals):
        if lo > reach + tol:
            return False
        reach = max(reach, hi)
    return reach >= extent_mm - tol


def _major_coords(rooms, axis: str, extent_mm: float, cross_extent_mm: float) -> list[float]:
    """Coordinates where a room edge runs clear across the plan.

    These are the plan's real band divisions, and the only honest source for a
    middle dimension tier: the schema has no structural grid or column line, so
    anything else would be invented. `axis` is `"h"` (x coordinates, tested for
    full-depth spans) or `"v"` (y coordinates, tested for full-width spans).
    """
    if axis == "h":
        def near(r):
            return (r.rect.x, r.rect.x2), (r.rect.y, r.rect.y2)
    else:
        def near(r):
            return (r.rect.y, r.rect.y2), (r.rect.x, r.rect.x2)

    candidates = sorted({c for r in rooms for c in near(r)[0]})
    major = []
    for value in candidates:
        spans = [near(r)[1] for r in rooms if abs(near(r)[0][0] - value) < 1e-6
                 or abs(near(r)[0][1] - value) < 1e-6]
        if _covers(spans, cross_extent_mm):
            major.append(value)
    return major


def _dimension_tiers(rooms, axis: str, extent_mm: float, cross_extent_mm: float) -> list[list[float]]:
    """Ordered inner-to-outer coordinate sets for one side's dimension stack:
    fine room subdivision, then full-span band divisions, then the overall
    figure. Consecutive duplicates are dropped so an undivided plan does not
    draw the same chain three times."""
    # Plot edges are part of the fine tier so the yard setbacks in front of and
    # behind the built form get dimensioned, as they are on the sheets.
    fine = sorted({0.0, extent_mm} | {c for r in rooms
                   for c in ((r.rect.x, r.rect.x2) if axis == "h" else (r.rect.y, r.rect.y2))})
    major = _major_coords(rooms, axis, extent_mm, cross_extent_mm)
    overall = [0.0, extent_mm]

    tiers: list[list[float]] = []
    for candidate in (fine, major, overall):
        if len(candidate) < 2:
            continue
        if tiers and _same_coords(tiers[-1], candidate):
            continue
        tiers.append(candidate)
    return tiers


def _same_coords(a: list[float], b: list[float], tol: float = 1e-6) -> bool:
    return len(a) == len(b) and all(abs(x - y) < tol for x, y in zip(a, b))


def _dimension_chain(coords_mm: list[float], axis: str, offset_px: float, extent_mm: float,
                     tier: int = 1, plot_depth_mm: float | None = None) -> str:
    """SVG fragment for one dimension chain: a run line, a tick at each
    coordinate, and a millimetre integer label centred between consecutive
    coordinates. `axis` is `"h"` (drawn above the plan) or `"v"` (drawn to its
    left); `offset_px` is the distance from the plan edge; `extent_mm` is the
    overall plot dimension along that axis (used for the degenerate empty case).
    Vertical chains read model y through `_y` so they flip with the plan (C1).
    """
    margin_px = MARGIN_MM / MM_PER_PX

    def to_px(v: float) -> float:
        return (v + MARGIN_MM) / MM_PER_PX

    def to_py(v: float) -> float:
        if plot_depth_mm is None:
            return to_px(v)
        return _y(v, plot_depth_mm)

    parts: list[str] = [f'<g class="dim-chain" data-tier="{tier}" data-axis="{axis}">']
    if len(coords_mm) < 2:
        # Degenerate input: only the overall dimension, no ticks.
        if axis == "h":
            y = margin_px - offset_px
            parts.append(f'<text x="{to_px(extent_mm / 2):.1f}" y="{y - 4:.1f}" '
                         f'font-size="10" text-anchor="middle">{int(round(extent_mm))}</text>')
        else:
            x = margin_px - offset_px
            parts.append(f'<text x="{x - 4:.1f}" y="{to_py(extent_mm / 2):.1f}" font-size="10" '
                         f'text-anchor="middle" transform="rotate(-90 {x - 4:.1f} {to_py(extent_mm / 2):.1f})">'
                         f'{int(round(extent_mm))}</text>')
        parts.append("</g>")
        return "\n".join(parts)

    start, end = coords_mm[0], coords_mm[-1]
    # SVG rejects negative rect dimensions (the whole element is dropped, not
    # just flipped), so normalise the run's pixel extent explicitly -- after
    # the rear-at-TOP orientation flip, end < start is normal for v-chains.
    if axis == "h":
        y = margin_px - offset_px
        rx, rw = sorted((to_px(start), to_px(end)))
        parts.append(f'<rect x="{rx:.1f}" y="{y - 0.25:.1f}" '
                     f'width="{rw - rx:.1f}" height="0.5" fill="#000"/>')
        for v in coords_mm:
            parts.append(f'<line x1="{to_px(v):.1f}" y1="{y - 3:.1f}" x2="{to_px(v):.1f}" '
                         f'y2="{y + 3:.1f}" stroke="#000" stroke-width="0.5"/>')
        for a, b in zip(coords_mm, coords_mm[1:]):
            mid = (a + b) / 2
            parts.append(f'<text x="{to_px(mid):.1f}" y="{y - 6:.1f}" font-size="10" '
                         f'text-anchor="middle">{int(round(b - a))}</text>')
    else:
        x = margin_px - offset_px
        ry, rh = sorted((to_py(start), to_py(end)))
        parts.append(f'<rect x="{x - 0.25:.1f}" y="{ry:.1f}" '
                     f'width="0.5" height="{rh - ry:.1f}" fill="#000"/>')
        for v in coords_mm:
            parts.append(f'<line x1="{x - 3:.1f}" y1="{to_py(v):.1f}" x2="{x + 3:.1f}" '
                         f'y2="{to_py(v):.1f}" stroke="#000" stroke-width="0.5"/>')
        for a, b in zip(coords_mm, coords_mm[1:]):
            mid = (a + b) / 2
            parts.append(f'<text x="{x - 6:.1f}" y="{to_py(mid):.1f}" font-size="10" '
                         f'text-anchor="middle" transform="rotate(-90 {x - 6:.1f} {to_py(mid):.1f})">'
                         f'{int(round(b - a))}</text>')
    parts.append("</g>")
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
    for layer, color in [("WALLS", 7), ("DOORS", 1), ("WINDOWS", 5), ("STAIRS", 3), ("TEXT", 2),
                         ("DIMS", 8), ("VOIDS", 4), ("FURNITURE", 9), ("PLOT", 6),
                         ("SETBACK", 5), ("ANNOT", 2)]:
        doc.layers.add(layer, color=color)
    msp = doc.modelspace()
    plot_depth = model.plot_depth_mm

    boundary = [_dxf_pt(0.0, 0.0, plot_depth), _dxf_pt(model.plot_width_mm, 0.0, plot_depth),
                _dxf_pt(model.plot_width_mm, plot_depth, plot_depth), _dxf_pt(0.0, plot_depth, plot_depth)]
    msp.add_lwpolyline(boundary, close=True, dxfattribs={"layer": "PLOT"})

    for wall in storey.walls:
        pts = [_dxf_pt(wall.x, wall.y, plot_depth),
               _dxf_pt(wall.x + wall.w, wall.y, plot_depth),
               _dxf_pt(wall.x + wall.w, wall.y + wall.h, plot_depth),
               _dxf_pt(wall.x, wall.y + wall.h, plot_depth)]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "WALLS"})

    _dxf_furniture(msp, storey, plot_depth)

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

    for void, reason in zip(storey.authored_voids, storey.authored_void_reasons):
        pts = [_dxf_pt(void.x, void.y, plot_depth),
               _dxf_pt(void.x + void.w, void.y, plot_depth),
               _dxf_pt(void.x + void.w, void.y + void.d, plot_depth),
               _dxf_pt(void.x, void.y + void.d, plot_depth)]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "VOIDS"})
        cx = void.x + void.w / 2
        cy = void.y + void.d / 2
        below_names = _void_below_names(model, storey, void)
        if below_names:
            msp.add_text(below_names, dxfattribs={"layer": "VOIDS", "height": 150}).set_placement(
                _dxf_pt(cx, cy, plot_depth), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)
        if reason:
            msp.add_text(reason, dxfattribs={"layer": "VOIDS", "height": 100}).set_placement(
                _dxf_pt(cx, cy - 200, plot_depth), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

    setbacks = model.setbacks or {}
    for key, dist, label in (
        ("front_mm", float(setbacks.get("front_mm", 0.0)), "Ranh khoảng lùi trước"),
        ("rear_mm", float(setbacks.get("rear_mm", 0.0)), "Ranh khoảng lùi sau"),
    ):
        if not setbacks.get(key):
            continue
        y = plot_depth - dist
        msp.add_line(_dxf_pt(0.0, y, plot_depth), _dxf_pt(model.plot_width_mm, y, plot_depth),
                     dxfattribs={"layer": "SETBACK"})
        tx, ty = _dxf_pt(100.0, y - 100.0, plot_depth)
        msp.add_text(label, dxfattribs={"layer": "SETBACK", "height": 120, "rotation": 90}).set_placement(
            (tx, ty), align=ezdxf.enums.TextEntityAlignment.MIDDLE_LEFT)

    for ann in storey.annotations:
        ax, ay = float(ann["x"]), float(ann["y"])
        aw, ad = float(ann["w"]), float(ann["d"])
        if ann.get("boxed"):
            pts = [_dxf_pt(ax, ay, plot_depth), _dxf_pt(ax + aw, ay, plot_depth),
                   _dxf_pt(ax + aw, ay + ad, plot_depth), _dxf_pt(ax, ay + ad, plot_depth)]
            msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": "ANNOT"})
        cx_f, cy_f = _dxf_pt(ax + aw / 2, ay + ad / 2, plot_depth)
        msp.add_text(str(ann["text"]), dxfattribs={"layer": "ANNOT", "height": 120}).set_placement(
            (cx_f, cy_f), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER)

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
