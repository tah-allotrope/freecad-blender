"""Deterministic compiler: high-level home spec -> fully-derived CompiledModel.

Resolution order per storey:
1. Resolve every room to an absolute Rect (direct `rect`, or `relative` placement
   solved against an already-resolved room).
2. Derive walls from room-rect edges: edges on the plot boundary become
   `exterior` walls; edges that exactly coincide between two rooms become a
   single `partition` wall; any other edge is treated as `exterior` (handles
   courtyards / non-fully-tiled layouts).
3. Place openings on the wall connecting the two referenced rooms (or a room
   and the plot boundary, via the sentinel id `"exterior"`).
4. Derive a straight-run staircase inside the stairwell room, if any.
5. Derive a roof volume spanning the plot, for storeys that declare one.
"""
from __future__ import annotations

from .errors import SpecError, SpecValidationError
from .model import CompiledModel, Opening, Rect, Room, Roof, Storey, View, Wall
from .stairs import derive_stairs

EXT_THICKNESS = 200.0
INT_THICKNESS = 100.0
DEFAULT_STOREY_HEIGHT = 3000.0

_SIDE_OPPOSITE = {"north": "south", "south": "north", "east": "west", "west": "east"}


def compile_spec(spec: dict) -> CompiledModel:
    errors: list[SpecError] = []
    plot_w = spec["site"]["plot_width_mm"]
    plot_d = spec["site"]["plot_depth_mm"]

    storeys: list[Storey] = []
    base_z = 0.0
    for s_idx, s in enumerate(spec["storeys"]):
        height = s.get("height_mm", DEFAULT_STOREY_HEIGHT)
        path = f"storeys[{s_idx}]"

        rooms = _resolve_rooms(s["rooms"], plot_w, plot_d, path, errors)
        walls = _derive_walls(rooms, plot_w, plot_d, s["level"])
        openings = _place_openings(s.get("openings", []), rooms, walls, s["level"], path, errors)
        stairs = derive_stairs(s.get("stairs"), rooms, height, s["level"], path, errors)
        roof = _derive_roof(s.get("roof"), plot_w, plot_d, s["level"], base_z + height)

        storeys.append(
            Storey(
                level=s["level"],
                name=s.get("name", f"Storey {s['level']}"),
                height_mm=height,
                base_z=base_z,
                rooms=rooms,
                walls=walls,
                openings=openings,
                stairs=stairs,
                roof=roof,
            )
        )
        base_z += height

    _derive_floor_voids(storeys)

    all_room_ids = {r.id for s in storeys for r in s.rooms}
    views = _resolve_views(spec["meta"].get("views", []), all_room_ids, errors)

    if errors:
        raise SpecValidationError(errors)

    return CompiledModel(
        name=spec["meta"]["name"],
        style=spec["meta"].get("style", "modern-minimal"),
        plot_width_mm=plot_w,
        plot_depth_mm=plot_d,
        storeys=storeys,
        views=views,
    )


def _resolve_views(view_specs, room_ids: set[str], errors) -> list[View]:
    views = []
    for idx, v in enumerate(view_specs):
        room_id = v.get("room_id")
        if v["kind"] == "room" and room_id not in room_ids:
            errors.append(
                SpecError(
                    code="view_room_not_found",
                    path=f"meta.views[{idx}]",
                    message=f"view '{v['name']}' references room_id '{room_id}' which does not exist",
                )
            )
            continue
        views.append(View(name=v["name"], kind=v["kind"], room_id=room_id))
    return views


def _resolve_rooms(room_specs, plot_w, plot_d, path, errors) -> list[Room]:
    resolved: dict[str, Room] = {}
    pending = list(room_specs)
    # Iterate until all `relative` rooms resolve or nothing changes (cycle/missing ref).
    for _ in range(len(pending) + 1):
        if not pending:
            break
        still_pending = []
        for r in pending:
            if "rect" in r:
                resolved[r["id"]] = Room(id=r["id"], type=r["type"], rect=Rect(**r["rect"]))
                continue
            rel = r["relative"]
            anchor = resolved.get(rel["adjacent_to"])
            if anchor is None:
                still_pending.append(r)
                continue
            resolved[r["id"]] = Room(
                id=r["id"], type=r["type"], rect=_place_relative(anchor.rect, rel)
            )
        pending = still_pending

    for r in pending:
        errors.append(
            SpecError(
                code="unresolved_relative_room",
                path=f"{path}.rooms[{r['id']}]",
                message=f"could not resolve relative placement (adjacent_to='{r['relative']['adjacent_to']}' not found or cyclic)",
            )
        )

    ordered = [resolved[r["id"]] for r in room_specs if r["id"] in resolved]

    # Geometric sanity: overlap and plot-bounds checks.
    for i, a in enumerate(ordered):
        if a.rect.x < 0 or a.rect.y < 0 or a.rect.x2 > plot_w or a.rect.y2 > plot_d:
            errors.append(
                SpecError(
                    code="room_outside_plot",
                    path=f"{path}.rooms[{a.id}]",
                    message=f"room '{a.id}' rect extends outside the {plot_w}x{plot_d}mm plot",
                )
            )
        for b in ordered[i + 1 :]:
            if _rects_overlap(a.rect, b.rect):
                errors.append(
                    SpecError(
                        code="room_overlap",
                        path=f"{path}.rooms",
                        message=f"rooms '{a.id}' and '{b.id}' overlap",
                    )
                )
    return ordered


def _place_relative(anchor: Rect, rel: dict) -> Rect:
    w, d = rel["w"], rel["d"]
    side = rel["side"]
    if side == "east":
        return Rect(x=anchor.x2, y=anchor.y, w=w, d=d)
    if side == "west":
        return Rect(x=anchor.x - w, y=anchor.y, w=w, d=d)
    if side == "south":
        return Rect(x=anchor.x, y=anchor.y2, w=w, d=d)
    if side == "north":
        return Rect(x=anchor.x, y=anchor.y - d, w=w, d=d)
    raise ValueError(f"unknown side {side!r}")


def _rects_overlap(a: Rect, b: Rect, eps: float = 1.0) -> bool:
    return not (
        a.x2 - eps <= b.x
        or b.x2 - eps <= a.x
        or a.y2 - eps <= b.y
        or b.y2 - eps <= a.y
    )


def _edge_key(orientation: str, coord: float) -> tuple[str, int]:
    return (orientation, round(coord))


def _derive_walls(rooms: list[Room], plot_w: float, plot_d: float, level: int) -> list[Wall]:
    """Derive wall segments from room-rect edges.

    Each room contributes 4 edges. Edges that exactly coincide (same
    orientation, coordinate, and span) between two different rooms merge into
    one partition wall. Any other edge becomes an exterior wall (this also
    naturally covers edges on the plot boundary).
    """
    # edge -> list of (start, end, room_id)
    edges: dict[tuple[str, int], list[tuple[float, float, str]]] = {}
    for room in rooms:
        r = room.rect
        edges.setdefault(_edge_key("vertical", r.x), []).append((r.y, r.y2, room.id))
        edges.setdefault(_edge_key("vertical", r.x2), []).append((r.y, r.y2, room.id))
        edges.setdefault(_edge_key("horizontal", r.y), []).append((r.x, r.x2, room.id))
        edges.setdefault(_edge_key("horizontal", r.y2), []).append((r.x, r.x2, room.id))

    walls: list[Wall] = []
    wall_idx = 0
    for (orientation, coord), spans in edges.items():
        # Sweep-line: split this edge line into atomic sub-intervals at every
        # breakpoint, then classify each by how many distinct rooms cover it
        # (1 room -> exterior/boundary wall, 2+ rooms -> shared partition wall).
        # This correctly handles rows of rooms with different widths on each
        # side of the line (e.g. a 2-room row above a 4-room row).
        breakpoints = sorted({p for start, end, _ in spans for p in (start, end)})
        pieces: list[tuple[float, float, tuple[str, ...]]] = []
        for p, q in zip(breakpoints, breakpoints[1:]):
            mid = (p + q) / 2
            covering = tuple(sorted({rid for start, end, rid in spans if start < mid < end}))
            if covering:
                pieces.append((p, q, covering))

        # Merge consecutive pieces with identical coverage into one wall.
        merged: list[tuple[float, float, tuple[str, ...]]] = []
        for p, q, covering in pieces:
            if merged and merged[-1][2] == covering and merged[-1][1] == p:
                mp, _, mc = merged[-1]
                merged[-1] = (mp, q, mc)
            else:
                merged.append((p, q, covering))

        for start, end, covering in merged:
            kind = "partition" if len(covering) >= 2 else "exterior"
            thickness = INT_THICKNESS if kind == "partition" else EXT_THICKNESS
            wall_idx += 1
            wid = f"F{level}_W{wall_idx:03d}"
            if orientation == "vertical":
                x = coord - thickness / 2
                y = start
                w, h = thickness, end - start
            else:
                x = start
                y = coord - thickness / 2
                w, h = end - start, thickness
            walls.append(
                Wall(
                    id=wid,
                    x=x,
                    y=y,
                    w=w,
                    h=h,
                    thickness=thickness,
                    kind=kind,
                    storey_level=level,
                    orientation=orientation,
                )
            )
    return walls


def _wall_side(wall: Wall, rect: Rect, eps: float = 1.0) -> str | None:
    """Which cardinal face of `rect` this wall sits on: north=min-y, south=max-y,
    west=min-x, east=max-x (matches the `relative` placement side convention)."""
    if wall.orientation == "vertical":
        coord = wall.x + wall.thickness / 2
        if abs(coord - rect.x) < eps:
            return "west"
        if abs(coord - rect.x2) < eps:
            return "east"
    else:
        coord = wall.y + wall.thickness / 2
        if abs(coord - rect.y) < eps:
            return "north"
        if abs(coord - rect.y2) < eps:
            return "south"
    return None


def _walls_between(rooms_by_id: dict[str, Room], walls: list[Wall], a_id: str, b_id: str, side: str | None = None) -> list[Wall]:
    """Find every wall segment separating room a_id from b_id (b_id may be 'exterior'),
    largest span first, so callers can pick the first one an opening actually fits."""
    a = rooms_by_id.get(a_id)
    if a is None:
        return []
    if b_id == "exterior":
        candidates = [w for w in walls if w.kind == "exterior" and _wall_touches_room(w, a.rect)]
        if side is not None:
            candidates = [w for w in candidates if _wall_side(w, a.rect) == side]
    else:
        b = rooms_by_id.get(b_id)
        if b is None:
            return []
        candidates = [
            w for w in walls
            if w.kind == "partition" and _wall_touches_room(w, a.rect) and _wall_touches_room(w, b.rect)
        ]
    candidates.sort(key=lambda w: (w.h if w.orientation == "vertical" else w.w), reverse=True)
    return candidates


def _wall_touches_room(wall: Wall, rect: Rect, eps: float = 1.0) -> bool:
    if wall.orientation == "vertical":
        coord = wall.x + wall.thickness / 2
        on_edge = abs(coord - rect.x) < eps or abs(coord - rect.x2) < eps
        overlaps = not (wall.y + wall.h <= rect.y + eps or rect.y2 <= wall.y + eps)
    else:
        coord = wall.y + wall.thickness / 2
        on_edge = abs(coord - rect.y) < eps or abs(coord - rect.y2) < eps
        overlaps = not (wall.x + wall.w <= rect.x + eps or rect.x2 <= wall.x + eps)
    return on_edge and overlaps


def _place_openings(opening_specs, rooms, walls, level, path, errors) -> list[Opening]:
    rooms_by_id = {r.id: r for r in rooms}
    result = []
    for idx, o in enumerate(opening_specs):
        a_id, b_id = o["between"]
        side = o.get("side")
        candidates = _walls_between(rooms_by_id, walls, a_id, b_id, side) or _walls_between(rooms_by_id, walls, b_id, a_id, side)
        if not candidates:
            errors.append(
                SpecError(
                    code="opening_no_wall",
                    path=f"{path}.openings[{idx}]",
                    message=f"no wall found between '{a_id}' and '{b_id}'",
                )
            )
            continue
        width = o.get("width_mm", 900.0)
        wall = next(
            (w for w in candidates if width <= (w.h if w.orientation == "vertical" else w.w)),
            candidates[0],
        )
        span = wall.h if wall.orientation == "vertical" else wall.w
        if width > span:
            errors.append(
                SpecError(
                    code="opening_too_wide",
                    path=f"{path}.openings[{idx}]",
                    message=f"opening width {width}mm exceeds wall span {span}mm on wall '{wall.id}'",
                )
            )
            continue
        offset = (span - width) / 2
        default_head = 2100.0 if o["type"] == "door" else 2100.0
        result.append(
            Opening(
                id=f"F{level}_O{idx:03d}",
                type=o["type"],
                wall_id=wall.id,
                storey_level=level,
                offset_mm=offset,
                width_mm=width,
                sill_mm=0.0 if o["type"] == "door" else o.get("sill_mm", 900.0),
                head_mm=o.get("head_mm", default_head),
            )
        )
    return result


def _derive_floor_voids(storeys: list[Storey]) -> None:
    """S2: for each storey, punch a void from the storey below's stairwell
    (if it generated stairs) and every elevator room on the storey below,
    plus every elevator room on the storey's own level (a lift shaft is
    open at every level it passes through)."""
    by_level = {s.level: s for s in storeys}
    levels = sorted(by_level)
    for idx, level in enumerate(levels):
        storey = by_level[level]
        rects: list[Rect] = []
        if idx > 0:
            prev = by_level[levels[idx - 1]]
            prev_has_stairs = prev.stairs is not None
            for room in prev.rooms:
                if room.type == "elevator":
                    rects.append(room.rect)
                elif room.type == "stairwell" and prev_has_stairs:
                    rects.append(room.rect)
        for room in storey.rooms:
            if room.type == "elevator":
                rects.append(room.rect)

        deduped: list[Rect] = []
        for r in rects:
            if not any(
                abs(r.x - d.x) <= 1 and abs(r.y - d.y) <= 1 and abs(r.w - d.w) <= 1 and abs(r.d - d.d) <= 1
                for d in deduped
            ):
                deduped.append(r)
        storey.floor_voids = deduped


def _derive_roof(roof_spec, plot_w, plot_d, level, base_z) -> Roof | None:
    if not roof_spec:
        return None
    overhang = roof_spec.get("overhang_mm", 300.0)
    base_rect = roof_spec.get("rect", {"x": 0, "y": 0, "w": plot_w, "d": plot_d})
    voids = [Rect(**v) for v in roof_spec.get("voids", [])]
    return Roof(
        storey_level=level,
        type=roof_spec["type"],
        pitch_deg=roof_spec.get("pitch_deg", 20.0),
        overhang_mm=overhang,
        x=base_rect["x"] - overhang,
        y=base_rect["y"] - overhang,
        w=base_rect["w"] + 2 * overhang,
        d=base_rect["d"] + 2 * overhang,
        base_z=base_z,
        voids=voids,
    )
