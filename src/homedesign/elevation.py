"""Elevations and sections (PHASE-04): pure projection of a CompiledModel onto
vertical planes.

Both drawing types produce the same neutral draw model -- a list of typed
primitives with `x`/`z` in millimetres (z grows upward) -- and the SVG and DXF
writers are two renderers over that one source, never two independent
implementations. Elevation `x` uses the model axis defined per side in S3 (the
east/west elevations use model **y** as their horizontal axis).
"""
from __future__ import annotations

import math
from pathlib import Path

import ezdxf

from .constants import FLAT_ROOF_THICKNESS_MM, OPEN_ROOM_TYPES, PARAPET_THICKNESS_MM, SLAB_BAND_MM
from .model import CompiledModel
from .plan2d import MARGIN_MM, MM_PER_PX, _scale_bar, _title_block
from .rects import open_edges, subtract_rects
from . import facade
from . import parapet as parapet_mod
from .xmltext import escape_text


def _view_axes(side: str, model: CompiledModel) -> tuple[str, float, float]:
    """`(horizontal_model_axis, canvas_width_mm, mirror_flag)` for a side.

    `horizontal_model_axis` is `"x"` for north/south and `"y"` for east/west;
    `mirror_flag` is `1.0` for the two near sides (north/west) and `-1.0` for
    the two far sides (south/east), which draw mirrored so each elevation reads
    as if the viewer stands on that side (ASM-001).
    """
    if side in ("north", "south"):
        return "x", model.plot_width_mm, 1.0 if side == "north" else -1.0
    return "y", model.plot_depth_mm, 1.0 if side == "west" else -1.0


def _project_box(side: str, model: CompiledModel, x: float, y: float, w: float, d: float) -> tuple[float, float, float]:
    """`(h_mm, width_mm, depth_mm)` for a model box on one elevation side.

    `h_mm` is the box's left edge on the drawing, `width_mm` its drawn width,
    and `depth_mm` the sort key where **smaller is nearer to the viewer** (S1).
    """
    if side == "north":
        return x, w, y
    if side == "south":
        return model.plot_width_mm - (x + w), w, -(y + d)
    if side == "west":
        return y, d, x
    return model.plot_depth_mm - (y + d), d, -(x + w)


def _opening_h(wall, opening, side: str, wall_h: float) -> float:
    """The opening's drawn left edge, given its host wall's drawn left edge."""
    span = wall.w if wall.orientation == "horizontal" else wall.h
    if side in ("north", "west"):
        return wall_h + opening.offset_mm
    return wall_h + (span - opening.offset_mm - opening.width_mm)


def _roof_primitives(side: str, model: CompiledModel, roof) -> list[dict]:
    """Projection of one roof into one or more `roof` primitives (S2)."""
    x0, y0, w, d, z0 = roof.x, roof.y, roof.w, roof.d, roof.base_z
    h0, w_h, depth = _project_box(side, model, x0, y0, w, d)
    out: list[dict] = []

    if roof.type == "flat":
        voids = [(v.x, v.y, v.w, v.d) for v in roof.voids] if roof.voids else []
        fragments = subtract_rects(x0, y0, w, d, voids) if voids else [(x0, y0, w, d)]
        for fx, fy, fw, fd in fragments:
            fh0, fw_h, fdepth = _project_box(side, model, fx, fy, fw, fd)
            out.append({
                "kind": "roof", "x": fh0, "z": z0, "w": fw_h, "h": FLAT_ROOF_THICKNESS_MM,
                "label": None, "type": "flat", "depth": fdepth,
                "points": [
                    (fh0, z0), (fh0 + fw_h, z0),
                    (fh0 + fw_h, z0 + FLAT_ROOF_THICKNESS_MM), (fh0, z0 + FLAT_ROOF_THICKNESS_MM),
                ],
            })
        return out

    pitch = math.radians(roof.pitch_deg)
    if roof.type == "gable":
        rise = (w / 2) * math.tan(pitch)
        if side in ("north", "south"):
            h_apex = h0 + w_h / 2
            points = [(h0, z0), (h0 + w_h, z0), (h_apex, z0 + rise)]
        else:
            points = [(h0, z0), (h0 + w_h, z0), (h0 + w_h, z0 + rise), (h0, z0 + rise)]
    else:  # shed
        rise = w * math.tan(pitch)
        if side == "north":
            points = [(h0, z0), (h0 + w_h, z0), (h0 + w_h, z0 + rise), (h0, z0)]
        elif side == "south":
            points = [(h0, z0), (h0 + w_h, z0), (h0 + w_h, z0), (h0, z0 + rise)]
        else:
            points = [(h0, z0), (h0 + w_h, z0), (h0 + w_h, z0 + rise), (h0, z0 + rise)]
    out.append({
        "kind": "roof", "x": h0, "z": z0, "w": w_h, "h": rise,
        "label": None, "type": roof.type, "depth": depth, "points": points,
    })
    return out


def build_elevation(model: CompiledModel, side: str) -> list[dict]:
    """Draw-model primitives for one elevation (S1): a true orthographic
    projection of the building, painter-sorted so nearer geometry overpaints
    farther geometry, with the silhouette derived from the projected primitives
    rather than assumed to be the plot rectangle."""
    _, canvas_width_mm, _ = _view_axes(side, model)
    total_h = sum(s.height_mm for s in model.storeys)

    # Groups of (depth, category, h, [primitives]); a wall and its openings are
    # one group so openings always paint on top of their host wall (S1.2 item 2).
    groups: list[tuple[float, int, float, list[dict]]] = []
    for storey in model.storeys:
        for wall in storey.walls:
            h0, w_h, depth = _project_box(side, model, wall.x, wall.y, wall.w, wall.h)
            group = [{
                "kind": "wall", "x": h0, "z": storey.base_z, "w": w_h, "h": storey.height_mm,
                "label": None, "type": None, "depth": depth,
            }]
            parallel = (
                (side in ("north", "south") and wall.orientation == "horizontal")
                or (side in ("east", "west") and wall.orientation == "vertical")
            )
            if parallel:
                for opening in storey.openings:
                    if opening.wall_id != wall.id:
                        continue
                    o_h = _opening_h(wall, opening, side, h0)
                    o_z = storey.base_z + opening.sill_mm
                    o_w = opening.width_mm
                    o_height = opening.head_mm - opening.sill_mm
                    group.append({
                        "kind": "opening", "x": o_h,
                        "z": o_z, "w": o_w,
                        "h": o_height,
                        "label": None, "type": opening.type, "depth": depth,
                    })
                    # Mullions and transoms ride in the same group as their
                    # host opening so they always overpaint the glass (S1.2).
                    for bar in facade.opening_division_lines(
                        o_w, o_height, getattr(opening, "divisions", None) or {}
                    ):
                        # north/west read left-to-right; south/east are mirrored
                        # by _opening_h, so the bar offsets mirror with them.
                        if side in ("north", "west"):
                            bar_h = o_h + bar["x_mm"]
                        else:
                            bar_h = o_h + (o_w - bar["x_mm"] - bar["w_mm"])
                        group.append({
                            "kind": "mullion", "x": bar_h,
                            "z": o_z + bar["y_mm"], "w": bar["w_mm"],
                            "h": bar["h_mm"],
                            "label": None, "type": opening.type, "depth": depth,
                        })
            groups.append((depth, 0, h0, group))

        for room in storey.rooms:
            if room.type not in OPEN_ROOM_TYPES:
                continue
            others = [r.rect for r in storey.rooms if r.id != room.id]
            sides = open_edges(room.rect, others)
            if not sides:
                continue
            rect = room.rect
            t = PARAPET_THICKNESS_MM
            bands = []
            if "north" in sides:
                bands.append((rect.x, rect.y, rect.w, t))
            if "south" in sides:
                bands.append((rect.x, rect.y + rect.d - t, rect.w, t))
            if "west" in sides:
                bands.append((rect.x, rect.y, t, rect.d))
            if "east" in sides:
                bands.append((rect.x + rect.w - t, rect.y, t, rect.d))
            pattern = getattr(room, "parapet_pattern", "solid") or "solid"
            for bx, by, bw, bd in bands:
                h0, w_h, depth = _project_box(side, model, bx, by, bw, bd)
                # One primitive for a solid parapet; one per slat for a slatted
                # one, from the same band list the 3D scene builds from.
                groups.append((depth, 1, h0, [{
                    "kind": "parapet", "x": h0, "z": storey.base_z + slat["z_off_mm"],
                    "w": w_h, "h": slat["h_mm"],
                    "label": None, "type": pattern, "depth": depth,
                } for slat in parapet_mod.elevation_bands(w_h, pattern)]))

        if storey.stairs:
            for t in storey.stairs.treads:
                h0, w_h, depth = _project_box(side, model, t.x, t.y, t.w, t.d)
                groups.append((depth, 2, h0, [{
                    "kind": "tread", "x": h0, "z": storey.base_z + t.z, "w": w_h,
                    "h": 0.0, "label": None, "type": None, "depth": depth,
                }]))

        for fe in getattr(storey, "facade_elements", []):
            rect = facade.facade_element_elevation_rect(fe, side, storey.base_z)
            if rect is None:
                continue
            h0, w_h, depth = _project_box(side, model, rect["x_mm"], 0, rect["w_mm"], 1)
            # Use rect's y as z, w/h as above; depth from projection
            groups.append((depth, 1, h0, [{
                "kind": "facade", "x": h0, "z": rect["y_mm"], "w": w_h, "h": rect["h_mm"],
                "label": None, "type": fe.get("kind"), "depth": depth,
            }]))
        if storey.roof:
            for prim in _roof_primitives(side, model, storey.roof):
                groups.append((prim["depth"], 3, prim["x"], [prim]))
            for st in storey.roof.structures:
                h0, w_h, depth = _project_box(side, model, st["x"], st["y"], st["w"], st["d"])
                groups.append((depth, 4, h0, [{
                    "kind": "structure", "x": h0, "z": storey.roof.base_z + FLAT_ROOF_THICKNESS_MM,
                    "w": w_h, "h": st["height_mm"], "label": st.get("name"), "type": None, "depth": depth,
                }]))

    groups.sort(key=lambda g: (-g[0], g[1], g[2]))
    projected: list[dict] = [p for _, _, _, group in groups for p in group]

    # Non-projected frame items (S1.3), emitted first so everything overpaints
    # them. The outline is the axis-aligned bounding box of the projected
    # solid geometry (ASM-002), clamped to the canvas.
    items: list[dict] = [
        {"kind": "ground", "x": 0.0, "z": 0.0, "w": canvas_width_mm, "h": 0.0, "label": None, "type": None},
    ]
    solid = [p for p in projected if p["kind"] in ("wall", "roof", "parapet", "structure", "facade")]
    if solid:
        min_h = max(0.0, min(p["x"] for p in solid))
        max_h = min(canvas_width_mm, max(p["x"] + p["w"] for p in solid))
        max_z = max(p["z"] + p["h"] for p in solid)
    else:
        min_h, max_h, max_z = 0.0, canvas_width_mm, total_h
    items.append({
        "kind": "outline", "x": min_h, "z": 0.0, "w": max_h - min_h, "h": max_z,
        "label": None, "type": None,
    })
    for storey in model.storeys:
        items.append({
            "kind": "level", "x": 0.0, "z": storey.base_z, "w": canvas_width_mm, "h": 0.0,
            "label": f"{storey.name}  +{storey.base_z / 1000:.3f}", "type": None,
        })
    items.extend(projected)
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
        # Opening head annotations: a small +x.xxx label at the head of every
        # opening whose host wall the section plane cuts through.
        for opening in storey.openings:
            wall = next((w for w in storey.walls if w.id == opening.wall_id), None)
            if wall is None or not _wall_cut(wall, axis, position_mm):
                continue
            xpos = (wall.y + wall.h / 2) if axis == "x" else (wall.x + wall.w / 2)
            items.append({
                "kind": "head_annotation", "x": xpos, "z": base + opening.head_mm, "w": 0, "h": 0,
                "label": f"+{opening.head_mm / 1000:.3f}", "type": None,
            })
    # Storey level tags down the cut, as MC A-A carries them (checklist A2).
    for storey in model.storeys:
        items.append({
            "kind": "level", "x": 0.0, "z": storey.base_z, "w": width_mm, "h": 0.0,
            "label": f"{storey.name}  +{storey.base_z / 1000:.3f}", "type": None,
        })
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
        elif kind == "parapet":
            # Outlined so a slatted parapet reads as separate bars rather than
            # dissolving into one grey block against the wall behind it.
            parts.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" '
                         f'fill="#8a8a8a" stroke="#1a1a1a" stroke-width="0.8"/>')
        elif kind == "facade":
            # Projecting elements (pillars, fins, bands) sit proud of the wall,
            # so they read lighter, with a crisp outline. The wall field is
            # #555; anything within a few percent of that is invisible.
            parts.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" '
                         f'fill="#9a9a9a" stroke="#111" stroke-width="1.2"/>')
        elif kind == "mullion":
            parts.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" '
                         f'fill="#bbb" stroke="#333" stroke-width="0.5"/>')
        elif kind == "structure":
            parts.append(f'<rect x="{sx:.1f}" y="{sy:.1f}" width="{sw:.1f}" height="{sh:.1f}" fill="#333"/>')
        elif kind == "roof":
            pts = " ".join(f"{px_x(h):.1f},{px_y_top(z, 0.0):.1f}" for h, z in item["points"])
            parts.append(f'<polygon points="{pts}" fill="#444"/>')
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
            parts.append(f'<text x="{sx + 6:.1f}" y="{y - 4:.1f}" font-size="10" fill="#666">{escape_text(item["label"])}</text>')
        elif kind == "room_label":
            parts.append(f'<text x="{sx:.1f}" y="{sy:.1f}" font-size="12" text-anchor="middle" fill="#222">{escape_text(item["label"])}</text>')
        elif kind == "head_annotation":
            parts.append(f'<text x="{sx + 2:.1f}" y="{sy:.1f}" font-size="9" fill="#555">{escape_text(item["label"])}</text>')

    # Overall height dimension on the right, labelled in metres.
    solid = [i for i in items if i["kind"] in ("wall", "roof", "parapet", "structure", "facade")]
    max_z = max((i["z"] + i["h"] for i in solid), default=total_h_mm)
    right_x = px_x(width_mm) + 40.0
    y_top, y_bot = px_y_top(max_z, 0.0), px_y_top(0.0, 0.0)
    parts.append(f'<line x1="{right_x:.1f}" y1="{y_bot:.1f}" x2="{right_x:.1f}" y2="{y_top:.1f}" '
                 f'stroke="#000" stroke-width="0.5"/>')
    parts.append(f'<line x1="{right_x - 3:.1f}" y1="{y_bot:.1f}" x2="{right_x + 3:.1f}" y2="{y_bot:.1f}" stroke="#000" stroke-width="0.5"/>')
    parts.append(f'<line x1="{right_x - 3:.1f}" y1="{y_top:.1f}" x2="{right_x + 3:.1f}" y2="{y_top:.1f}" stroke="#000" stroke-width="0.5"/>')
    parts.append(f'<text x="{right_x - 4:.1f}" y="{(y_top + y_bot) / 2:.1f}" font-size="10" '
                 f'text-anchor="middle" transform="rotate(-90 {right_x - 4:.1f} {(y_top + y_bot) / 2:.1f})">'
                 f'{max_z / 1000:.3f} m</text>')

    parts.append(_scale_bar(height_px))
    parts.append(_title_block(width_px, height_px, [escape_text(title), "Scale: use the graphic bar", "homedesign"]))
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
        elif kind in ("parapet", "structure", "facade"):
            poly(item, "ELEV")
        elif kind == "mullion":
            poly(item, "WINDOWS")
        elif kind == "roof":
            msp.add_lwpolyline(
                [(h, z) for h, z in item["points"]], close=True, dxfattribs={"layer": "ELEV"}
            )
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
        elif kind == "head_annotation":
            msp.add_text(item["label"] or "", dxfattribs={"layer": "TEXT", "height": 120}).set_placement(
                (x + 100, z), align=ezdxf.enums.TextEntityAlignment.LEFT
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
    """The SVG and DXF section paths: one per `meta.sections` entry when the
    spec declares them, else the two legacy centreline sections (ASM-004)."""
    svg_dir = out_dir / "svg"
    dxf_dir = out_dir / "dxf"
    svg_dir.mkdir(parents=True, exist_ok=True)
    dxf_dir.mkdir(parents=True, exist_ok=True)
    total_h = sum(s.height_mm for s in model.storeys)

    cuts = model.sections or [
        {"name": "x", "axis": "x", "position_mm": model.plot_width_mm / 2},
        {"name": "y", "axis": "y", "position_mm": model.plot_depth_mm / 2},
    ]
    paths: list[Path] = []
    for cut in cuts:
        axis, position = cut["axis"], float(cut["position_mm"])
        items = build_section(model, axis, position)
        width_mm = model.plot_depth_mm if axis == "x" else model.plot_width_mm
        title = "Long Section" if axis == "x" else "Cross Section"
        svg_path = svg_dir / f"{model.name}_section_{cut['name']}.svg"
        svg_path.write_text(_svg(items, f"{model.name} {title}", width_mm, total_h), encoding="utf-8")
        paths.append(svg_path)
        dxf_path = dxf_dir / f"{model.name}_section_{cut['name']}.dxf"
        _dxf(items, dxf_path)
        paths.append(dxf_path)
    return paths
