"""Stair sizing, feasibility and tread generation per plan S1 (Blondel relation).

Pure Python -- no `bpy` import, so it is unit-testable outside Blender.

NOTE on a documented plan discrepancy: S1's worked example for a straight
flight at H=3400mm states `treads[-1].z == 3400.0`, but its own formula
(`z = (i + 1) * R` for `i` in `0 .. treads-1`, `treads = n - 1`) can only
reach `(n - 1) * R`, which is 3221.05mm for this input, not `n * R` =
3400mm. The plan's own "Gotchas" section is explicit that a flight of `n`
risers has `n - 1` treads because the top riser lands on the floor above
and needs no tread object. This module follows that formula (the
self-consistent, explicitly-justified rule) rather than the arithmetically
impossible worked number; `treads[-1].z` for a straight flight is
therefore `(n - 1) * R`.
"""
from __future__ import annotations

import math

from .errors import SpecError
from .model import Room, Stairs, Tread

MIN_FLIGHT_WIDTH_MM = 900.0
MIN_URETURN_SHORT_MM = 1900.0
URETURN_WELL_MM = 100.0
TARGET_RISER_MM = 175.0


def stair_sizing(storey_height_mm: float) -> tuple[int, float, float]:
    """`(n_risers, riser_mm, going_mm)` per S1."""
    n = max(2, round(storey_height_mm / TARGET_RISER_MM))
    r = storey_height_mm / n
    g = max(250.0, 600.0 - 2 * r)
    return n, r, g


def straight_minimum(storey_height_mm: float) -> tuple[float, float]:
    """`(min_width_mm, min_depth_mm)` for a straight flight."""
    n, _r, g = stair_sizing(storey_height_mm)
    treads = n - 1
    return MIN_FLIGHT_WIDTH_MM, treads * g


def u_return_minimum(storey_height_mm: float, short_mm: float = MIN_URETURN_SHORT_MM) -> tuple[float, float]:
    """`(min_width_mm, min_depth_mm)` for a U-return."""
    n, _r, g = stair_sizing(storey_height_mm)
    flight_w = (short_mm - URETURN_WELL_MM) / 2
    n_a = math.ceil(n / 2)
    treads_a = n_a - 1
    treads_b = n - n_a - 1
    landing_depth = max(MIN_FLIGHT_WIDTH_MM, flight_w)
    run_required = max(treads_a, treads_b) * g + landing_depth
    return short_mm, run_required


def _straight_fits(long_mm: float, short_mm: float, n: int, g: float) -> bool:
    treads = n - 1
    run_required = treads * g
    return long_mm >= run_required and short_mm >= MIN_FLIGHT_WIDTH_MM


def _u_return_fits(long_mm: float, short_mm: float, n: int, g: float) -> bool:
    if short_mm < MIN_URETURN_SHORT_MM:
        return False
    flight_w = (short_mm - URETURN_WELL_MM) / 2
    n_a = math.ceil(n / 2)
    treads_a = n_a - 1
    treads_b = n - n_a - 1
    landing_depth = max(MIN_FLIGHT_WIDTH_MM, flight_w)
    run_required = max(treads_a, treads_b) * g + landing_depth
    return long_mm >= run_required


def derive_stairs(
    stairs_spec: dict | None,
    rooms: list[Room],
    storey_height_mm: float,
    level: int,
    path: str,
    errors: list[SpecError],
) -> Stairs | None:
    if not stairs_spec:
        return None
    room = next((r for r in rooms if r.id == stairs_spec["room"]), None)
    if room is None:
        return None

    mode = stairs_spec.get("mode", "auto")
    direction = stairs_spec.get("direction", "up")
    if mode == "none":
        return None

    n, r, g = stair_sizing(storey_height_mm)
    if r > 190.0:
        errors.append(
            SpecError(
                code="stair_riser_too_tall",
                path=f"{path}.stairs",
                message=f"storey height {storey_height_mm}mm needs a {r:.1f}mm riser, which exceeds the 190mm maximum",
            )
        )
        return None

    rect = room.rect
    w, d = rect.w, rect.d
    long_mm = max(w, d)
    short_mm = min(w, d)
    long_is_depth = d >= w

    straight_fits = _straight_fits(long_mm, short_mm, n, g)
    u_return_fits = _u_return_fits(long_mm, short_mm, n, g)

    if mode == "auto":
        chosen = "straight" if straight_fits else ("u_return" if u_return_fits else None)
    elif mode == "straight":
        chosen = "straight" if straight_fits else None
    elif mode == "u_return":
        chosen = "u_return" if u_return_fits else None
    else:
        chosen = None

    if chosen is None:
        sw, sd = straight_minimum(storey_height_mm)
        uw, ud = u_return_minimum(storey_height_mm)
        errors.append(
            SpecError(
                code="stair_shaft_too_small",
                path=f"{path}.stairs",
                message=(
                    f"stair shaft '{room.id}' is {w:g}x{d:g}mm; a straight flight needs "
                    f"{sw:g}x{sd:g}mm and a U-return needs {uw:g}x{ud:g}mm at a "
                    f"{storey_height_mm:g}mm storey height"
                ),
            )
        )
        return None

    if chosen == "straight":
        treads = _emit_straight(rect, short_mm, g, r, n, long_is_depth)
    else:
        treads = _emit_u_return(rect, short_mm, long_mm, g, r, n, long_is_depth)

    return Stairs(room_id=room.id, storey_level=level, direction=direction, treads=treads)


def _emit_straight(rect, short_mm: float, g: float, r: float, n: int, long_is_depth: bool) -> list[Tread]:
    treads_count = n - 1
    out = []
    for i in range(treads_count):
        z = (i + 1) * r
        if long_is_depth:
            out.append(Tread(x=rect.x, y=rect.y + i * g, w=short_mm, d=g, z=z))
        else:
            out.append(Tread(x=rect.x + i * g, y=rect.y, w=g, d=short_mm, z=z))
    return out


def _emit_u_return(rect, short_mm: float, long_mm: float, g: float, r: float, n: int, long_is_depth: bool) -> list[Tread]:
    flight_w = (short_mm - URETURN_WELL_MM) / 2
    n_a = math.ceil(n / 2)
    treads_a = n_a - 1
    treads_b = n - n_a
    landing_depth = long_mm - treads_a * g

    out: list[Tread] = []
    if long_is_depth:
        for i in range(treads_a):
            out.append(Tread(x=rect.x, y=rect.y + i * g, w=flight_w, d=g, z=(i + 1) * r))
        landing_y = rect.y + treads_a * g
        out.append(Tread(x=rect.x, y=landing_y, w=short_mm, d=landing_depth, z=n_a * r))
        for j in range(treads_b):
            out.append(
                Tread(
                    x=rect.x + flight_w + URETURN_WELL_MM,
                    y=landing_y - (j + 1) * g,
                    w=flight_w,
                    d=g,
                    z=(n_a + j + 1) * r,
                )
            )
    else:
        for i in range(treads_a):
            out.append(Tread(x=rect.x + i * g, y=rect.y, w=g, d=flight_w, z=(i + 1) * r))
        landing_x = rect.x + treads_a * g
        out.append(Tread(x=landing_x, y=rect.y, w=landing_depth, d=short_mm, z=n_a * r))
        for j in range(treads_b):
            out.append(
                Tread(
                    x=landing_x - (j + 1) * g,
                    y=rect.y + flight_w + URETURN_WELL_MM,
                    w=g,
                    d=flight_w,
                    z=(n_a + j + 1) * r,
                )
            )
    return out
