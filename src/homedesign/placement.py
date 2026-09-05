"""Pure furniture-placement rules: room type + rect (meters) -> furniture items.

No bpy import here so this is unit-testable outside Blender. The Blender-side
`blender/furnish.py` executes the plans this module produces; it never
computes layout math itself.
"""
from __future__ import annotations

from dataclasses import dataclass

CLEARANCE_M = 0.6  # minimum walkway clearance kept clear of furniture


@dataclass
class FurnitureItem:
    kind: str  # bed, wardrobe, nightstand, sofa, coffee_table, dining_table, chair,
               # kitchen_run, fridge, wc, basin, shower, desk, rug (floor covering,
               # collision-exempt: lies flat under furniture), floor_lamp,
               # pendant (ceiling-hung, collision-exempt)
    x: float
    y: float
    z: float
    rot_deg: float
    w: float
    d: float
    h: float


def _footprint(item: FurnitureItem) -> tuple[float, float, float, float]:
    """Axis-aligned footprint (x,y,w,d) accounting for rot_deg 90."""
    if item.rot_deg == 90:
        return (item.x, item.y, item.d, item.w)
    return (item.x, item.y, item.w, item.d)


def _overlaps(a: tuple[float, float, float, float], b: tuple[float, float, float, float]) -> bool:
    ax, ay, aw, ad = a
    bx, by, bw, bd = b
    return not (ax + aw <= bx or bx + bw <= ax or ay + ad <= by or by + bd <= ay)


def resolve_collisions(
    items: list[FurnitureItem], room_w_m: float, room_d_m: float, door_swings: list[tuple[float, float, float, float]] | None = None
) -> list[FurnitureItem]:
    """Shift overlapping footprints apart, preserving order and length.
    Door swings are (x,y,w,d) rectangles to avoid."""
    if door_swings is None:
        door_swings = []
    # Work on mutable copies
    result = [FurnitureItem(i.kind, i.x, i.y, i.z, i.rot_deg, i.w, i.d, i.h) for i in items]
    for idx in range(len(result)):
        # Clamp inside room
        fx, fy, fw, fd = _footprint(result[idx])
        # ensure within room bounds
        nx = max(0.0, min(fx, room_w_m - fw))
        ny = max(0.0, min(fy, room_d_m - fd))
        result[idx].x, result[idx].y = nx, ny
        if result[idx].kind in ("rug", "pendant"):
            # Floor covering / ceiling-hung: never moves and never
            # displaces anything.
            continue
        # Resolve overlaps with earlier items
        for j in range(idx):
            if result[j].kind in ("rug", "pendant"):
                continue
            for _attempt in range(10):
                a = _footprint(result[idx])
                b = _footprint(result[j])
                if not _overlaps(a, b) and not any(_overlaps(a, s) for s in door_swings):
                    break
                # shift along y then x to separate
                # try moving idx item away by small step
                # Move to not overlap: push idx beyond j's footprint
                ax, ay, aw, ad = a
                bx, by, bw, bd = b
                # push in y direction if possible, else x
                try_y = by + bd + 0.05
                if try_y + ad <= room_d_m:
                    result[idx].y = try_y
                else:
                    try_x = bx + bw + 0.05
                    if try_x + aw <= room_w_m:
                        result[idx].x = try_x
                    else:
                        # cannot separate without leaving room: touch but not overlap
                        result[idx].y = max(0.0, by - ad - 0.01)
                        break
            # after attempts, if still overlapping, nudge to edge
        # also check door swings after pairwise
        for s in door_swings:
            a = _footprint(result[idx])
            if _overlaps(a, s):
                ax, ay, aw, ad = a
                sx, sy, sw, sd = s
                try_y = sy + sd + 0.05
                if try_y + ad <= room_d_m:
                    result[idx].y = try_y
                else:
                    result[idx].x = max(0.0, min(ax, room_w_m - aw))
    return result


def plan_room(room_type: str, w_m: float, d_m: float) -> list[FurnitureItem]:
    """Return furniture placements in room-local coordinates (origin at the
    room's x,y corner, +x along width, +y along depth)."""
    if room_type == "bedroom":
        items = _plan_bedroom(w_m, d_m)
    elif room_type == "bathroom":
        items = _plan_bathroom(w_m, d_m)
    elif room_type == "wc":
        items = _plan_wc(w_m, d_m)
    elif room_type == "kitchen":
        items = _plan_kitchen(w_m, d_m)
    elif room_type in ("living", "dining"):
        items = _plan_living(w_m, d_m)
    elif room_type == "office":
        items = _plan_office(w_m, d_m)
    elif room_type == "hall":
        items = _plan_hall(w_m, d_m)
    elif room_type in ("storage", "utility"):
        items = _plan_shelving(w_m, d_m)
    elif room_type == "garage":
        items = _plan_garage(w_m, d_m)
    elif room_type in ("balcony", "terrace"):
        items = _plan_outdoor(w_m, d_m)
    else:
        items = []
    return resolve_collisions(items, w_m, d_m, [])

def _plan_bedroom(w: float, d: float) -> list[FurnitureItem]:
    items = []
    bed_w, bed_d, bed_h = min(1.6, w * 0.6), 2.0, 0.55
    rot = 0
    if bed_d > d - CLEARANCE_M:
        # Room is shallow: rotate the bed 90deg instead of swapping its
        # dimensions, so w/d stay semantic (w = headboard width, d = length)
        # and the rotation carries the orientation. The fit check must use
        # the rotated footprint.
        if bed_w <= d - CLEARANCE_M and bed_d <= w:
            rot = 90
        else:
            bed_d, bed_w = bed_w, bed_d  # legacy fallback: swap dimensions
    fit_w, fit_d = (bed_d, bed_w) if rot else (bed_w, bed_d)
    bed_x = (w - fit_w) / 2
    items.append(FurnitureItem("bed", bed_x, 0.1, 0, rot, bed_w, bed_d, bed_h))
    if w - fit_w > 0.7:
        items.append(FurnitureItem("wardrobe", w - 0.6, 0.0, 0, 0, 0.6, min(1.8, d * 0.4), 2.0))
    if d - 0.1 - fit_d > 1.0:
        # Runner across the foot of the bed; collision-exempt (lies flat).
        items.append(FurnitureItem("rug", bed_x, 0.1 + fit_d + 0.1, 0, 0, fit_w, 0.8, 0.02))
    if bed_x > 0.55:
        items.append(FurnitureItem("nightstand", bed_x - 0.5, 0.05, 0, 0, 0.45, 0.4, 0.5))
    if bed_x + fit_w + 0.5 < w:
        items.append(FurnitureItem("nightstand", bed_x + fit_w + 0.05, 0.05, 0, 0, 0.45, 0.4, 0.5))
    # Pendant at room centre (deep enough in frame to read; hangs clear).
    items.append(FurnitureItem("pendant", w / 2 - 0.15, d / 2 - 0.15,
                               0, 0, 0.3, 0.3, 0.0))
    return items


def _plan_bathroom(w: float, d: float) -> list[FurnitureItem]:
    items = [FurnitureItem("wc", 0.2, d - 0.4, 0, 0, 0.4, 0.6, 0.4)]
    if w > 1.5:
        items.append(FurnitureItem("basin", w - 0.6, 0.1, 0, 0, 0.5, 0.4, 0.85))
    if w > 2.0 and d > 2.0:
        items.append(FurnitureItem("shower", w - 0.9, d - 0.9, 0, 0, 0.9, 0.9, 2.0))
    return items


def _plan_kitchen(w: float, d: float) -> list[FurnitureItem]:
    run_len = min(w - 0.4, w * 0.9)
    items = [FurnitureItem("kitchen_run", 0.2, 0.0, 0, 0, run_len, 0.6, 0.9)]
    if d > 1.8:
        items.append(FurnitureItem("fridge", 0.2, d - 0.7, 0, 0, 0.7, 0.7, 1.8))
    return items


def _plan_living(w: float, d: float) -> list[FurnitureItem]:
    sofa_w = min(2.2, w * 0.6)
    items = [FurnitureItem("sofa", 0.3, d - 0.9, 0, 0, sofa_w, 0.9, 0.8)]
    coffee_x = 0.3 + sofa_w / 2 - 0.5
    items.append(FurnitureItem("coffee_table", coffee_x, d - 1.8, 0, 0, 1.0, 0.6, 0.4))
    # Rug centred under the coffee table; collision-exempt (lies flat).
    items.append(FurnitureItem("rug", coffee_x - 0.3, d - 2.55, 0, 0, 1.6, 1.1, 0.02))
    if w > 3.0 and d > 3.0:
        table_x, table_w = w - 1.8, 1.6
        items.append(FurnitureItem("dining_table", table_x, 0.3, 0, 0, table_w, 0.9, 0.75))
        chair_w = 0.45
        for cx in (table_x + 0.05, table_x + 0.55, table_x + 1.05, table_x + table_w - chair_w - 0.05):
            items.append(FurnitureItem("chair", cx, 1.4, 0, 0, chair_w, chair_w, 0.9))
        # Pendant over the dining table (correct dressing; near the camera so
        # rarely in frame) plus one over the coffee zone (the hero-visible
        # source in this room's rendered view). Both collision-exempt.
        items.append(FurnitureItem("pendant", table_x + 0.65, 0.6, 0, 0, 0.3, 0.3, 0.0))
        items.append(FurnitureItem("pendant", coffee_x + 0.35, d - 1.65, 0, 0, 0.3, 0.3, 0.0))
        # Floor lamp in the far corner: bright vertical accent that also
        # proves the wall wash on the camera-side party wall.
        items.append(FurnitureItem("floor_lamp", w - 0.45, d - 0.65, 0, 0, 0.35, 0.35, 1.6))
    else:
        # Pendant over the coffee table (collision-exempt, hangs above it).
        items.append(FurnitureItem("pendant", coffee_x + 0.35, d - 1.65, 0, 0, 0.3, 0.3, 0.0))
    return items


def _plan_office(w: float, d: float) -> list[FurnitureItem]:
    return [FurnitureItem("desk", 0.2, 0.2, 0, 0, min(1.4, w - 0.4), 0.7, 0.75)]


def _plan_wc(w: float, d: float) -> list[FurnitureItem]:
    """A `wc` room: the bathroom's WC and basin, without the shower."""
    wc_d = min(0.6, d)
    items = [FurnitureItem("wc", 0.2, d - wc_d, 0, 0, 0.4, wc_d, 0.4)]
    if w > 1.5:
        items.append(FurnitureItem("basin", w - 0.6, 0.1, 0, 0, 0.5, 0.4, 0.85))
    return items


def _plan_hall(w: float, d: float) -> list[FurnitureItem]:
    # Narrow stair corridors stay bare: a 0.38 m drum 2 m from the lens
    # reads as a balloon, not a light (verified in hanh_lang_thang).
    if w < 1.2:
        return []
    if d >= w:
        return [FurnitureItem("pendant", w / 2 - 0.15, d / 2 - 0.15, 0, 0, 0.3, 0.3, 0.0),
                FurnitureItem("console", 0.1, 0.1, 0, 0, 0.35, max(0.5, d - 0.2), 0.85)]
    return [FurnitureItem("pendant", w / 2 - 0.15, d / 2 - 0.15, 0, 0, 0.3, 0.3, 0.0),
            FurnitureItem("console", 0.1, 0.1, 0, 0, max(0.5, w - 0.2), 0.35, 0.85)]

def _plan_shelving(w: float, d: float) -> list[FurnitureItem]:
    if d >= w:
        return [FurnitureItem("shelving", 0.1, 0.1, 0, 0, 0.6, max(0.5, d - 0.2), 2.0)]
    return [FurnitureItem("shelving", 0.1, 0.1, 0, 0, max(0.5, w - 0.2), 0.6, 2.0)]


def _plan_garage(w: float, d: float) -> list[FurnitureItem]:
    car_l, car_w, car_h = 4.5, 1.8, 1.4
    if max(w, d) < car_l or min(w, d) < car_w:
        # No car fits (the tubehouse case): two motorbikes instead — the
        # honest vehicle for a 4 m Saigon garage bay.
        if max(w, d) >= 2.0 and min(w, d) >= 1.6:
            return [FurnitureItem("motorbike", w / 2 - 0.75, (d - 2.0) / 2, 0, 0, 0.7, 2.0, 1.1),
                    FurnitureItem("motorbike", w / 2 + 0.05, (d - 2.0) / 2, 0, 0, 0.7, 2.0, 1.1)]
        return []
    if d >= w:
        return [FurnitureItem("car", (w - car_w) / 2, (d - car_l) / 2, 0, 0, car_w, car_l, car_h)]
    return [FurnitureItem("car", (w - car_l) / 2, (d - car_w) / 2, 0, 0, car_l, car_w, car_h)]


def _plan_outdoor(w: float, d: float) -> list[FurnitureItem]:
    if w < 1.5 or d < 1.5:
        return []
    return [
        FurnitureItem("chair", 0.2, 0.2, 0, 0, 0.45, 0.45, 0.9),
        FurnitureItem("chair", w - 0.65, d - 0.65, 0, 0, 0.45, 0.45, 0.9),
        FurnitureItem("planter", (w - 0.5) / 2, (d - 0.5) / 2, 0, 0, 0.5, 0.5, 0.5),
    ]
