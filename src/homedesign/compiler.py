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
from .facade import resolve_facade_element
from .finishes import build_finish_map
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
    wall_alignment = spec["site"].get("wall_alignment", "centre")

    # Sort storeys by level so base_z accumulation does not silently depend
    # on list order; warn (later, via the registry) if the authored order
    # differed from the sorted order.
    authored_levels = [s["level"] for s in spec["storeys"]]
    spec["storeys"] = sorted(spec["storeys"], key=lambda s: s["level"])
    sorted_levels = [s["level"] for s in spec["storeys"]]
    if authored_levels != sorted_levels:
        errors.append(
            SpecError(
                code="storeys_out_of_order",
                path="storeys",
                message=(
                    f"storeys authored as levels {authored_levels}, sorted to {sorted_levels}; "
                    "base_z accumulation follows the sorted order"
                ),
                severity="warning",
            )
        )

    storeys: list[Storey] = []
    base_z = 0.0
    for s_idx, s in enumerate(spec["storeys"]):
        height = s.get("height_mm", DEFAULT_STOREY_HEIGHT)
        path = f"storeys[{s_idx}]"

        rooms = _resolve_rooms(s["rooms"], plot_w, plot_d, path, errors)
        walls = _derive_walls(rooms, plot_w, plot_d, s["level"], wall_alignment)
        _derive_interiors(rooms, walls, wall_alignment)
        openings = _place_openings(s.get("openings", []), rooms, walls, s["level"], path, errors)
        stairs = derive_stairs(s.get("stairs"), rooms, height, s["level"], path, errors)
        roof = _derive_roof(s.get("roof"), plot_w, plot_d, s["level"], base_z + height)

        facade_elems = []
        for fe in s.get("facade_elements", []):
            resolved = resolve_facade_element(fe, base_z, plot_w, plot_d)
            # keep original kind/side alongside resolved box
            resolved["kind"] = fe.get("kind")
            resolved["side"] = fe.get("side")
            if "id" in fe:
                resolved["id"] = fe["id"]
            facade_elems.append(resolved)
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
                authored_voids=[Rect(x=v["x"], y=v["y"], w=v["w"], d=v["d"]) for v in s.get("voids", [])],
                authored_void_reasons=[v.get("reason", "") for v in s.get("voids", [])],
                annotations=list(s.get("annotations", [])),
                facade_elements=facade_elems,
            )
        )
        base_z += height

    _derive_floor_voids(storeys)

    all_room_ids = {r.id for s in storeys for r in s.rooms}
    views = _resolve_views(spec["meta"].get("views", []), all_room_ids, errors)

    sections = spec["meta"].get("sections", [])
    for idx, sec in enumerate(sections):
        axis = sec["axis"]
        position = float(sec["position_mm"])
        limit = plot_w if axis == "x" else plot_d
        if position > limit:
            errors.append(
                SpecError(
                    code="section_out_of_plot",
                    path=f"meta.sections[{idx}]",
                    message=(
                        f"section '{sec['name']}' position {position:.0f}mm exceeds the "
                        f"{limit:.0f}mm plot {axis}-extent"
                    ),
                )
            )

    if errors:
        raise SpecValidationError(errors)

    return CompiledModel(
        name=spec["meta"]["name"],
        style=spec["meta"].get("style", "modern-minimal"),
        plot_width_mm=plot_w,
        plot_depth_mm=plot_d,
        storeys=storeys,
        views=views,
        context=spec["site"].get("context", {}),
        wall_alignment=wall_alignment,
        sections=sections,
        north_deg=spec["site"].get("north_deg", 0.0),
        finish_map=build_finish_map(spec),
        setbacks=spec["site"].get("setbacks"),
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
                resolved[r["id"]] = Room(id=r["id"], type=r["type"], rect=Rect(**r["rect"]),
                                         name=r.get("name"), level_mm=r.get("level_mm"),
                                         parapet_pattern=r.get("parapet_pattern", "solid"))
                continue
            rel = r["relative"]
            anchor = resolved.get(rel["adjacent_to"])
            if anchor is None:
                still_pending.append(r)
                continue
            resolved[r["id"]] = Room(
                id=r["id"], type=r["type"], rect=_place_relative(anchor.rect, rel), name=r.get("name"),
                level_mm=r.get("level_mm"), parapet_pattern=r.get("parapet_pattern", "solid"),
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


def _derive_walls(rooms: list[Room], plot_w: float, plot_d: float, level: int,
                  wall_alignment: str = "centre") -> list[Wall]:
    """Derive wall segments from room-rect edges.

    Each room contributes 4 edges. Edges that exactly coincide (same
    orientation, coordinate, and span) between two different rooms merge into
    one partition wall. Any other edge becomes an exterior wall (this also
    naturally covers edges on the plot boundary).

    Per S5, `wall_alignment` selects how an *exterior* wall sits relative to
    the room edge it derives from: `"centre"` (default, today's geometry) spans
    `[coord - t/2, coord + t/2]`; `"inside"` lies wholly on the room side of
    `coord` so its outer face lands on the plot line. Partitions are always
    centred.
    """
    # edge -> list of (start, end, room_id)
    edges: dict[tuple[str, int], list[tuple[float, float, str]]] = {}
    for room in rooms:
        r = room.rect
        edges.setdefault(_edge_key("vertical", r.x), []).append((r.y, r.y2, room.id))
        edges.setdefault(_edge_key("vertical", r.x2), []).append((r.y, r.y2, room.id))
        edges.setdefault(_edge_key("horizontal", r.y), []).append((r.x, r.x2, room.id))
        edges.setdefault(_edge_key("horizontal", r.y2), []).append((r.x, r.x2, room.id))

    rooms_by_id = {r.id: r for r in rooms}
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
            if kind == "partition" or wall_alignment != "inside":
                # Centred: the wall straddles the room-edge coordinate.
                if orientation == "vertical":
                    x = coord - thickness / 2
                    y = start
                    w, h = thickness, end - start
                else:
                    x = start
                    y = coord - thickness / 2
                    w, h = end - start, thickness
            else:
                # Inset: the exterior wall lies wholly on the room side of the
                # edge, its outer face on `coord`. The single covering room
                # decides which side is interior.
                room = rooms_by_id[covering[0]]
                if orientation == "vertical":
                    # Room east of the wall (coord is rect.x) -> wall spans
                    # [coord, coord+t]; room west (coord is rect.x2) -> [coord-t, coord].
                    room_east = abs(coord - room.rect.x) < 1.0
                    x = coord if room_east else coord - thickness
                    y = start
                    w, h = thickness, end - start
                else:
                    # Room south of the wall (coord is rect.y) -> wall spans
                    # [coord, coord+t]; room north (coord is rect.y2) -> [coord-t, coord].
                    room_south = abs(coord - room.rect.y) < 1.0
                    y = coord if room_south else coord - thickness
                    x = start
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
                    room_id=covering[0] if len(covering) == 1 else None,
                )
            )
    return walls


def _edge_inset(wall: Wall, alignment: str) -> float:
    """How far a wall's own face sits inside the room-edge coordinate (S5)."""
    if alignment == "inside" and wall.kind == "exterior":
        return wall.thickness
    return wall.thickness / 2


def _derive_interiors(rooms: list[Room], walls: list[Wall], alignment: str) -> None:
    """Populate each room's net `interior` rect: the gross rect shrunk by the
    thickness of every wall on its boundary (full thickness for exterior walls
    under `"inside"`, half otherwise; partitions always half). Edges with no
    wall are left as-is. The room schedule keeps reporting the gross area."""
    eps = 1.0
    for room in rooms:
        rect = room.rect
        insets = {"north": 0.0, "south": 0.0, "east": 0.0, "west": 0.0}
        for wall in walls:
            if wall.orientation == "vertical":
                centre = wall.x + wall.w / 2
                if abs(centre - rect.x) <= wall.thickness / 2 + eps and _span_overlap(
                    rect.y, rect.y2, wall.y, wall.y + wall.h
                ):
                    insets["west"] = max(insets["west"], _edge_inset(wall, alignment))
                elif abs(centre - rect.x2) <= wall.thickness / 2 + eps and _span_overlap(
                    rect.y, rect.y2, wall.y, wall.y + wall.h
                ):
                    insets["east"] = max(insets["east"], _edge_inset(wall, alignment))
            else:
                centre = wall.y + wall.h / 2
                if abs(centre - rect.y) <= wall.thickness / 2 + eps and _span_overlap(
                    rect.x, rect.x2, wall.x, wall.x + wall.w
                ):
                    insets["north"] = max(insets["north"], _edge_inset(wall, alignment))
                elif abs(centre - rect.y2) <= wall.thickness / 2 + eps and _span_overlap(
                    rect.x, rect.x2, wall.x, wall.x + wall.w
                ):
                    insets["south"] = max(insets["south"], _edge_inset(wall, alignment))
        if any(insets.values()):
            room.interior = Rect(
                x=rect.x + insets["west"],
                y=rect.y + insets["north"],
                w=rect.w - insets["west"] - insets["east"],
                d=rect.d - insets["north"] - insets["south"],
            )


def _span_overlap(a1: float, a2: float, b1: float, b2: float) -> bool:
    return a1 < b2 and b1 < a2


def _wall_side(wall: Wall, rect: Rect, eps: float = 1.0) -> str | None:
    """Which cardinal face of `rect` this wall sits on: north=min-y, south=max-y,
    west=min-x, east=max-x (matches the `relative` placement side convention).

    The tolerance includes half the wall thickness so `"inside"`-aligned walls
    (whose centre sits t/2 inboard of the room edge) are still recognised.
    """
    tol = wall.thickness / 2 + eps
    if wall.orientation == "vertical":
        coord = wall.x + wall.thickness / 2
        if abs(coord - rect.x) < tol:
            return "west"
        if abs(coord - rect.x2) < tol:
            return "east"
    else:
        coord = wall.y + wall.thickness / 2
        if abs(coord - rect.y) < tol:
            return "north"
        if abs(coord - rect.y2) < tol:
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
    from .model import _wall_touches_room_canonical

    return _wall_touches_room_canonical(wall, rect, eps)


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
        offset = resolve_opening_offset(
            span,
            width,
            o.get("align", "center"),
            o.get("offset_mm"),
        )
        if offset < 0 or offset + width > span + 1:
            errors.append(
                SpecError(
                    code="opening_out_of_wall",
                    path=f"{path}.openings[{idx}]",
                    message=(
                        f"opening offset {offset}mm + width {width}mm exceeds wall span {span}mm "
                        f"on wall '{wall.id}'"
                    ),
                )
            )
            continue
        # Doors and windows deliberately share a 2100mm head line (the standard
        # UK door head height; windows align to it for a clean facade).
        default_head = 2100.0
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
                divisions=o.get("divisions"),
                between=(a_id, b_id),
            )
        )
    _check_opening_overlaps(result, path, errors)
    return result


def resolve_opening_offset(
    span_mm: float, width_mm: float, align: str, offset_mm: float | None
) -> float:
    """S3: distance of the opening from the wall segment's start.

    `offset_mm` overrides `align` entirely. `align` defaults to "center"
    (callers always pass it).
    """
    if offset_mm is not None:
        return float(offset_mm)
    if align == "start":
        return 0.0
    if align == "end":
        return span_mm - width_mm
    return (span_mm - width_mm) / 2


def _check_opening_overlaps(openings: list[Opening], path: str, errors: list[SpecError]) -> None:
    """S3: two openings on the same wall overlap when they overlap in both
    plan (offset/width) and elevation (sill/head). 1mm slack permits
    edge-to-edge placement."""
    by_wall: dict[str, list[Opening]] = {}
    for o in openings:
        by_wall.setdefault(o.wall_id, []).append(o)
    for wall_id, ops in by_wall.items():
        for i, a in enumerate(ops):
            for b in ops[i + 1 :]:
                plan_overlap = (
                    min(a.offset_mm + a.width_mm, b.offset_mm + b.width_mm)
                    - max(a.offset_mm, b.offset_mm)
                ) > 1
                elev_overlap = (
                    min(a.head_mm, b.head_mm) - max(a.sill_mm, b.sill_mm)
                ) > 1
                if plan_overlap and elev_overlap:
                    errors.append(
                        SpecError(
                            code="opening_overlap",
                            path=f"{path}.openings",
                            message=(
                                f"openings '{a.id}' and '{b.id}' overlap on wall '{wall_id}' "
                                f"(plan {plan_overlap:.0f}mm, elevation {elev_overlap:.0f}mm)"
                            ),
                        )
                    )


def _derive_floor_voids(storeys: list[Storey]) -> None:
    """S2: for each storey, punch a void from the storey below's stairwell
    (if it generated stairs) and every elevator room on the storey below,
    plus every elevator room on the storey's own level (a lift shaft is
    open at every level it passes through)."""
    by_level = {s.level: s for s in storeys}
    levels = sorted(by_level)
    for idx, level in enumerate(levels):
        storey = by_level[level]
        # Authored voids (S3): a beam-spanned opening declared on this storey,
        # seeded before the derived stairwell/elevator voids.
        rects: list[Rect] = list(storey.authored_voids)
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
        structures=roof_spec.get("structures", []),
    )
