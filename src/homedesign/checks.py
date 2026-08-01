"""Validation rule registry: geometric and livability checks over CompiledModel.

Each rule is a `(code, callable)` pair; the callable takes a `CompiledModel`
and returns `list[SpecError]`. `validate.validate_compiled` runs the registry
and concatenates the results, so adding a rule here is all that is needed to
enforce it everywhere (CLI compile, tests, CI).
"""
from __future__ import annotations

from .errors import SpecError
from .model import CompiledModel

HABITABLE_TYPES = {"bedroom", "living", "kitchen", "dining", "office"}


def check_door_reachability(model: CompiledModel) -> list[SpecError]:
    """Every room must be reachable via a chain of door openings from an
    exterior door (level 0) or from a stairwell/elevator room (upper levels)."""
    errors: list[SpecError] = []
    for storey in model.storeys:
        # Build the door graph: room_id <-> room_id (or "exterior") for doors.
        graph: dict[str, set[str]] = {}
        for o in storey.openings:
            if o.type != "door":
                continue
            # Find the two room ids the opening connects via its wall.
            wall = next((w for w in storey.walls if w.id == o.wall_id), None)
            if wall is None:
                continue
            touching = {
                r.id for r in storey.rooms if _wall_touches_room(wall, r.rect)
            }
            if wall.kind == "exterior":
                touching.add("exterior")
            ids = list(touching)
            for a in ids:
                for b in ids:
                    if a != b:
                        graph.setdefault(a, set()).add(b)
                        graph.setdefault(b, set()).add(a)

        reachable: set[str] = set()
        if storey.level == 0:
            if "exterior" not in graph:
                errors.append(
                    SpecError(
                        code="no_entrance",
                        path=f"storeys[{storey.level}]",
                        message=(
                            f"storey {storey.level} has no exterior door; the home has no entrance"
                        ),
                    )
                )
            else:
                reachable = _flood(graph, "exterior")
        else:
            # Upper storey: reachable via stairwell/elevator rooms on this storey.
            vertical_roots = {
                r.id
                for r in storey.rooms
                if r.type in ("stairwell", "elevator") and r.id in graph
            }
            for root in vertical_roots:
                reachable |= _flood(graph, root)

        for room in storey.rooms:
            if room.id not in reachable:
                errors.append(
                    SpecError(
                        code="room_unreachable",
                        path=f"storeys[{storey.level}].rooms[{room.id}]",
                        message=(
                            f"room '{room.id}' on storey {storey.level} is not reachable via a "
                            "chain of doors from an exterior door (ground) or a stair/elevator "
                            "shaft (upper storeys)"
                        ),
                    )
                )
    return errors


def _flood(graph: dict[str, set[str]], start: str) -> set[str]:
    seen: set[str] = set()
    stack = [start]
    while stack:
        node = stack.pop()
        if node in seen:
            continue
        seen.add(node)
        stack.extend(graph.get(node, ()))
    return seen


def check_habitable_daylight(model: CompiledModel) -> list[SpecError]:
    """Habitable rooms must have at least one window on a touching wall."""
    errors: list[SpecError] = []
    for storey in model.storeys:
        for room in storey.rooms:
            if room.type not in HABITABLE_TYPES:
                continue
            has_window = any(
                o.type == "window"
                and any(
                    _wall_touches_room(w, room.rect)
                    for w in storey.walls
                    if w.id == o.wall_id
                )
                for o in storey.openings
            )
            if not has_window:
                errors.append(
                    SpecError(
                        code="room_no_daylight",
                        path=f"storeys[{storey.level}].rooms[{room.id}]",
                        message=(
                            f"habitable room '{room.id}' ({room.type}) has no window on any wall"
                        ),
                    )
                )
    return errors


def check_room_support(model: CompiledModel) -> list[SpecError]:
    """Every room above the lowest level must be >= 80% covered by the union
    of rooms on the level below (no cantilevered floor)."""
    errors: list[SpecError] = []
    levels = sorted({s.level for s in model.storeys})
    by_level = {s.level: s for s in model.storeys}
    for lvl in levels[1:]:
        storey = by_level[lvl]
        below = by_level[levels[levels.index(lvl) - 1]]
        below_rects = [r.rect for r in below.rooms]
        for room in storey.rooms:
            area = room.rect.w * room.rect.d
            if area <= 0:
                continue
            covered = _overlap_area(room.rect, below_rects)
            if covered / area < 0.8:
                errors.append(
                    SpecError(
                        code="room_unsupported",
                        path=f"storeys[{lvl}].rooms[{room.id}]",
                        message=(
                            f"room '{room.id}' on storey {lvl} is only {covered / area:.0%} "
                            "covered by the floor below (< 80%); the floor would be unsupported"
                        ),
                    )
                )
    return errors


def _overlap_area(rect, rects) -> float:
    total = 0.0
    for r in rects:
        w = max(0.0, min(rect.x2, r.x2) - max(rect.x, r.x))
        d = max(0.0, min(rect.y2, r.y2) - max(rect.y, r.y))
        total += w * d
    return total


def check_shaft_stacking(model: CompiledModel) -> list[SpecError]:
    """A stairwell/elevator room must keep the same footprint across levels
    where it appears; a storey with generated stairs needs the shaft on the
    storey above."""
    errors: list[SpecError] = []
    by_level = {s.level: s for s in model.storeys}
    levels = sorted(by_level)
    footprints: dict[str, tuple[float, float, float, float]] = {}
    for lvl in levels:
        storey = by_level[lvl]
        for room in storey.rooms:
            if room.type not in ("stairwell", "elevator"):
                continue
            key = room.id
            rect = (room.rect.x, room.rect.y, room.rect.w, room.rect.d)
            if key in footprints:
                prev = footprints[key]
                if any(abs(a - b) > 1 for a, b in zip(prev, rect)):
                    errors.append(
                        SpecError(
                            code="shaft_misaligned",
                            path=f"storeys[{lvl}].rooms[{key}]",
                            message=(
                                f"shaft '{key}' has footprint {prev} on an earlier storey but "
                                f"{rect} on storey {lvl}; vertical circulation must stack"
                            ),
                        )
                    )
            else:
                footprints[key] = rect
    # Discontinuity: storey with stairs but no shaft above (unless top storey).
    for i, lvl in enumerate(levels):
        storey = by_level[lvl]
        if storey.stairs is None:
            continue
        if i == len(levels) - 1:
            continue
        above = by_level[levels[i + 1]]
        has_shaft_above = any(
            r.type == "stairwell" for r in above.rooms
        )
        if not has_shaft_above:
            errors.append(
                SpecError(
                    code="shaft_discontinuous",
                    path=f"storeys[{lvl}]",
                    message=(
                        f"storey {lvl} generates stairs but storey {levels[i + 1]} has no "
                        "stairwell shaft for them to continue into"
                    ),
                )
            )
    return errors


def check_walls_within_plot(model: CompiledModel) -> list[SpecError]:
    """Walls extending beyond the plot rectangle. Warning, not error: exterior
    walls are centred on the room edge, so a 200mm wall pokes 100mm out."""
    errors: list[SpecError] = []
    for storey in model.storeys:
        for wall in storey.walls:
            x1, y1 = wall.x, wall.y
            x2, y2 = wall.x + wall.w, wall.y + wall.h
            if x1 < -1 or y1 < -1 or x2 > model.plot_width_mm + 1 or y2 > model.plot_depth_mm + 1:
                errors.append(
                    SpecError(
                        code="wall_outside_plot",
                        path=f"storeys[{storey.level}].walls[{wall.id}]",
                        message=(
                            f"wall '{wall.id}' spans x[{x1:.0f},{x2:.0f}] y[{y1:.0f},{y2:.0f}] "
                            f"and extends beyond the {model.plot_width_mm:.0f}x"
                            f"{model.plot_depth_mm:.0f}mm plot"
                        ),
                        severity="warning",
                    )
                )
    return errors


def check_storey_order(spec_levels: list[int]) -> list[SpecError]:
    """Warning when storeys are not authored in ascending level order."""
    if spec_levels == sorted(spec_levels):
        return []
    return [
        SpecError(
            code="storeys_out_of_order",
            path="storeys",
            message=(
                f"storeys authored as {spec_levels}, not ascending; they are sorted by level "
                "before compilation"
            ),
            severity="warning",
        )
    ]


def _wall_touches_room(wall, rect, eps: float = 1.0) -> bool:
    if wall.orientation == "vertical":
        coord = wall.x + wall.thickness / 2
        on_edge = abs(coord - rect.x) < eps or abs(coord - rect.x2) < eps
        overlaps = not (wall.y + wall.h <= rect.y + eps or rect.y2 <= wall.y + eps)
    else:
        coord = wall.y + wall.thickness / 2
        on_edge = abs(coord - rect.y) < eps or abs(coord - rect.y2) < eps
        overlaps = not (wall.x + wall.w <= rect.x + eps or rect.x2 <= wall.x + eps)
    return on_edge and overlaps


# The registry: order matters only for stable error ordering in output.
RULES: list[tuple[str, callable]] = [
    ("door_reachability", check_door_reachability),
    ("habitable_daylight", check_habitable_daylight),
    ("room_support", check_room_support),
    ("shaft_stacking", check_shaft_stacking),
    ("walls_within_plot", check_walls_within_plot),
]
