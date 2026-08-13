"""Elevations and sections (PHASE-04): pure projection of a CompiledModel onto
vertical planes.

Both drawing types produce the same neutral draw model -- a list of typed
primitives with `x`/`z` in millimetres (z grows upward) -- and the SVG and DXF
writers are two renderers over that one source, never two independent
implementations. Elevation `x` uses the model axis defined per side in S3 (the
east/west elevations use model **y** as their horizontal axis).
"""
from __future__ import annotations

from pathlib import Path

import ezdxf

from .model import CompiledModel
from .plan2d import MARGIN_MM, MM_PER_PX, _scale_bar, _title_block
from .rects import subtract_rects

TOL = 1.0  # mm tolerance for a wall's face/centre lying on the elevation plane
SLAB_BAND_MM = 200.0  # structural floor band drawn as cut in sections

# Per side: the plane axis/value the wall's face must sit on, the qualifying
# wall orientation, which face is exterior, and the model axis used as the
# elevation's horizontal axis (S3).
_ELEV = {
    "north": {"plane": "y", "value": 0.0, "orient": "horizontal", "ext": "min", "h_axis": "x", "width_key": "plot_width_mm"},
    "south": {"plane": "y", "value": "plot_depth", "orient": "horizontal", "ext": "max", "h_axis": "x", "width_key": "plot_width_mm"},
    "west": {"plane": "x", "value": 0.0, "orient": "vertical", "ext": "min", "h_axis": "y", "width_key": "plot_depth_mm"},
    "east": {"plane": "x", "value": "plot_width", "orient": "vertical", "ext": "max", "h_axis": "y", "width_key": "plot_depth_mm"},
}


def _plane_value(model: CompiledModel, side: str) -> float:
    spec = _ELEV[side]
    if spec["value"] in ("plot_depth", "plot_width"):
        return model.plot_depth_mm if spec["value"] == "plot_depth" else model.plot_width_mm
    return spec["value"]


def _wall_on_plane(wall, side: str, plane_value: float) -> bool:
    """A wall qualifies for an elevation when its exterior face OR its centre
    line lies on the plane (covers both `centre` and `inside` wall alignment)."""
    spec = _ELEV[side]
    if wall.orientation != spec["orient"]:
        return False
    if spec["plane"] == "y":
        centre = wall.y + wall.h / 2
        face = wall.y if spec["ext"] == "min" else wall.y + wall.h
    else:
        centre = wall.x + wall.w / 2
        face = wall.x if spec["ext"] == "min" else wall.x + wall.w
    return min(abs(centre - plane_value), abs(face - plane_value)) < TOL


def _wall_h_extent(wall, side: str) -> tuple[float, float]:
    if side in ("north", "south"):
        return wall.x, wall.x + wall.w
    return wall.y, wall.y + wall.h


def build_elevation(model: CompiledModel, side: str) -> list[dict]:
    """Draw-model primitives for one elevation (S3)."""
    plane_value = _plane_value(model, side)
    width_mm = model.plot_width_mm if side in ("north", "south") else model.plot_depth_mm
    total_h = sum(s.height_mm for s in model.storeys)

    items: list[dict] = [
        {"kind": "ground", "x": 0.0, "z": 0.0, "w": width_mm, "h": 0.0, "label": None, "type": None},
        {"kind": "outline", "x": 0.0, "z": 0.0, "w": width_mm, "h": total_h, "label": None, "type": None},
    ]
    for storey in model.storeys:
        items.append({
            "kind": "level", "x": 0.0, "z": storey.base_z, "w": width_mm, "h": 0.0,
            "label": storey.name or f"Level {storey.level}", "type": None,
        })
        for wall in storey.walls:
            if not _wall_on_plane(wall, side, plane_value):
                continue
            h0, h1 = _wall_h_extent(wall, side)
            items.append({
                "kind": "wall", "x": h0, "z": storey.base_z, "w": h1 - h0, "h": storey.height_mm,
                "label": None, "type": None,
            })
            for opening in storey.openings:
                if opening.wall_id != wall.id:
                    continue
                items.append({
                    "kind": "opening", "x": h0 + opening.offset_mm,
                    "z": storey.base_z + opening.sill_mm, "w": opening.width_mm,
                    "h": opening.head_mm - opening.sill_mm, "label": None, "type": opening.type,
                })
    return items


def _wall_cut(wall, axis: str, position_mm: float) -> bool:
    if axis == "x":
        return wall.x < position_mm < wall.x + wall.w
    return wall.y < position_mm < wall.y + wall.h


def _rect_contains(rect, axis: str, position_mm: float) -> bool:
    if axis == "x":
        return rect.x < position_mm < rect.x + rect.w
    return rect.y < position_mm < rect.y + rect.d


def build_section(model: CompiledModel, axis: str, position_mm: float) -> list[dict]:
    """Draw-model primitives for a section cut on plane `axis` = `position_mm`
    (S4): cut walls (poché), cut floor bands, stair tread outlines and room
    labels. Everything behind the cut is omitted by design (ALT-002)."""
    width_mm = model.plot_depth_mm if axis == "x" else model.plot_width_mm
    items: list[dict] = [
        {"kind": "ground", "x": 0.0, "z": 0.0, "w": width_mm, "h": 0.0, "label": None, "type": None},
    ]
    for storey in model.storeys:
        base, height = storey.base_z, storey.height_mm
        for wall in storey.walls:
            if not _wall_cut(wall, axis, position_mm):
                continue
            if axis == "x":
                x0, x1 = wall.y, wall.y + wall.h
            else:
                x0, x1 = wall.x, wall.x + wall.w
            items.append({
                "kind": "cut_wall", "x": x0, "z": base, "w": x1 - x0, "h": height,
                "label": None, "type": None,
            })
        for room in storey.rooms:
            if not _rect_contains(room.rect, axis, position_mm):
                continue
            voids = [(v.x, v.y, v.w, v.d) for v in storey.floor_voids]
            fragments = subtract_rects(room.rect.x, room.rect.y, room.rect.w, room.rect.d, voids)
            for fx, fy, fw, fd in fragments:
                if axis == "x":
                    items.append({"kind": "cut_slab", "x": fy, "z": base, "w": fd, "h": SLAB_BAND_MM, "label": None, "type": None})
                else:
                    items.append({"kind": "cut_slab", "x": fx, "z": base, "w": fw, "h": SLAB_BAND_MM, "label": None, "type": None})
            mid = room.rect.y + room.rect.d / 2 if axis == "x" else room.rect.x + room.rect.w / 2
            items.append({
                "kind": "room_label", "x": mid, "z": base + height / 2, "w": 0, "h": 0,
                "label": room.name or room.id, "type": None,
            })
        if storey.stairs:
            stair_room = next((r for r in storey.rooms if r.id == storey.stairs.room_id), None)
            if stair_room is not None and _rect_contains(stair_room.rect, axis, position_mm):
                for t in storey.stairs.treads:
                    if axis == "x":
                        items.append({"kind": "tread", "x": t.y, "z": base + t.z, "w": t.d, "h": 0.0, "label": None, "type": None})
                    else:
                        items.append({"kind": "tread", "x": t.x, "z": base + t.z, "w": t.w, "h": 0.0, "label": None, "type": None})
    return items


def _svg(items: list[dict], title: str, width_mm: float, total_h_mm: float) -> str:
    width_px = (width_mm + MARGIN_MM) / MM_PER_PX
    height_px = (total_h_mm + MARGIN_MM) / MM_PER_PX
    parts = [
        f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width_px:.0f} {height_px:.0f}" '
        f'preserveAspectRatio="xMidYMid meet" font-family="sans-serif">',
        f'<rect x="0" y="0" width="{width_px:.0f}" height="{height_px:.0f}" fill="white"/>',
    ]

    def px_x(v: float) -> float:
        return (v + MARGIN_MM) / MM_PER_PX

    def px_y_top(z: float, h: float) -> float:
        # z grows upward, SVG y grows downward -- this is the one flip point.
        return (MARGIN_MM + total_h_mm - (z + h)) / MM_PER_PX

    for item in items:
        kind = item["kind"]
        x, z, w, h = item["x"], item["z"], item["w"], item["h"]
        sx, sy, sw, sh = px_x(x), px_y_top(z, h), w / MM_PER_PX, h / MM_PER_PX
        if kind in ("wall", "cut_slab"):
            parts.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="#555"/>')
        elif kind == "cut_wall":
            parts.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" '
                         f'fill="#333" stroke="#000" stroke-width="2"/>')
        elif kind == "opening":
            parts.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" '
                         f'fill="white" stroke="#888" stroke-width="0.8"/>')
        elif kind == "outline":
            parts.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" '
                         f'fill="none" stroke="#222" stroke-width="2"/>')
        elif kind == "tread":
            y = px_y_top(z, 0.0)
            parts.append(f'<line x1="{sx:.1f}" y1="{y:.1f}" x2="{sx + sw:.1f}" y2="{y:.1f}" '
                         f'stroke="#888" stroke-width="1.5"/>')
        elif kind == "ground":
            y = px_y_top(z, 0.0)
            parts.append(f'<line x1="{sx:.1f}" y1="{y:.1f}" x2="{sx + sw:.1f}" y2="{y:.1f}" '
                         f'stroke="#000" stroke-width="3"/>')
        elif kind == "level":
            y = px_y_top(z, 0.0)
            parts.append(f'<line x1="{sx:.1f}" y1="{y:.1f}" x2="{sx + sw:.1f}" y2="{y:.1f}" '
                         f'stroke="#999" stroke-width="0.8" stroke-dasharray="6 4"/>')
            parts.append(f'<text x="{sx + 6:.1f}" y="{y - 4:.1f}" font-size="10" fill="#666">{item["label"]}</text>')
        elif kind == "room_label":
            parts.append(f'<text x="{sx:.1f}" y="{sy:.1f}" font-size="12" text-anchor="middle" fill="#222">{item["label"]}</text>')

    parts.append(_scale_bar(height_px))
    parts.append(_title_block(width_px, height_px, [title, "Scale 1:100 @ A3", "homedesign"]))
    parts.append("</svg>")
    return "\n".join(parts)


_DXF_LAYERS = [
    ("WALLS", 7), ("DOORS", 1), ("WINDOWS", 5), ("STAIRS", 3),
    ("TEXT", 2), ("DIMS", 8), ("ELEV", 7), ("SECTION", 3), ("LEVELS", 8),
]


def _dxf(items: list[dict], out_path: Path) -> None:
    doc = ezdxf.new("R2010")
    doc.units = ezdxf.units.MM
    for layer, color in _DXF_LAYERS:
        doc.layers.add(layer, color=color)
    msp = doc.modelspace()

    def poly(item, layer):
        x, z, w, h = item["x"], item["z"], item["w"], item["h"]
        pts = [(x, z), (x + w, z), (x + w, z + h), (x, z + h)]
        msp.add_lwpolyline(pts, close=True, dxfattribs={"layer": layer})

    for item in items:
        kind = item["kind"]
        x, z, w = item["x"], item["z"], item["w"]
        if kind in ("wall", "cut_wall", "cut_slab"):
            poly(item, "ELEV" if kind == "wall" else "SECTION")
        elif kind == "opening":
            poly(item, "DOORS" if item.get("type") == "door" else "WINDOWS")
        elif kind == "tread":
            msp.add_line((x, z), (x + w, z), dxfattribs={"layer": "STAIRS"})
        elif kind == "ground":
            msp.add_line((x, z), (x + w, z), dxfattribs={"layer": "DIMS"})
        elif kind == "level":
            msp.add_line((x, z), (x + w, z), dxfattribs={"layer": "LEVELS"})
            msp.add_text(item["label"] or "", dxfattribs={"layer": "TEXT", "height": 150}).set_placement(
                (x + 100, z + 150), align=ezdxf.enums.TextEntityAlignment.LEFT
            )
        elif kind == "room_label":
            msp.add_text(item["label"] or "", dxfattribs={"layer": "TEXT", "height": 180}).set_placement(
                (x, z), align=ezdxf.enums.TextEntityAlignment.MIDDLE_CENTER
            )
    doc.saveas(out_path)


def write_elevations(model: CompiledModel, out_dir: Path, sides=("north", "south", "east", "west")) -> list[Path]:
    """The SVG and DXF elevation paths, in that order per side."""
    svg_dir = out_dir / "svg"
    dxf_dir = out_dir / "dxf"
    svg_dir.mkdir(parents=True, exist_ok=True)
    dxf_dir.mkdir(parents=True, exist_ok=True)
    total_h = sum(s.height_mm for s in model.storeys)
    paths: list[Path] = []
    for side in sides:
        items = build_elevation(model, side)
        width_mm = model.plot_width_mm if side in ("north", "south") else model.plot_depth_mm
        svg_path = svg_dir / f"{model.name}_elev_{side}.svg"
        svg_path.write_text(_svg(items, f"{model.name} {side.title()} Elevation", width_mm, total_h), encoding="utf-8")
        paths.append(svg_path)
        dxf_path = dxf_dir / f"{model.name}_elev_{side}.dxf"
        _dxf(items, dxf_path)
        paths.append(dxf_path)
    return paths


def write_sections(model: CompiledModel, out_dir: Path) -> list[Path]:
    """The SVG and DXF section paths: long (`x`) and cross (`y`) per ASM-004."""
    svg_dir = out_dir / "svg"
    dxf_dir = out_dir / "dxf"
    svg_dir.mkdir(parents=True, exist_ok=True)
    dxf_dir.mkdir(parents=True, exist_ok=True)
    total_h = sum(s.height_mm for s in model.storeys)
    paths: list[Path] = []
    for axis, position in (("x", model.plot_width_mm / 2), ("y", model.plot_depth_mm / 2)):
        items = build_section(model, axis, position)
        width_mm = model.plot_depth_mm if axis == "x" else model.plot_width_mm
        title = "Long Section" if axis == "x" else "Cross Section"
        svg_path = svg_dir / f"{model.name}_section_{axis}.svg"
        svg_path.write_text(_svg(items, f"{model.name} {title}", width_mm, total_h), encoding="utf-8")
        paths.append(svg_path)
        dxf_path = dxf_dir / f"{model.name}_section_{axis}.dxf"
        _dxf(items, dxf_path)
        paths.append(dxf_path)
    return paths
