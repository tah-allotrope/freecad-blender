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
               # kitchen_run, fridge, wc, basin, shower, desk
    x: float
    y: float
    z: float
    rot_deg: float
    w: float
    d: float
    h: float


def plan_room(room_type: str, w_m: float, d_m: float) -> list[FurnitureItem]:
    """Return furniture placements in room-local coordinates (origin at the
    room's x,y corner, +x along width, +y along depth)."""
    if room_type == "bedroom":
        return _plan_bedroom(w_m, d_m)
    if room_type == "bathroom":
        return _plan_bathroom(w_m, d_m)
    if room_type == "kitchen":
        return _plan_kitchen(w_m, d_m)
    if room_type in ("living", "dining"):
        return _plan_living(w_m, d_m)
    if room_type == "office":
        return _plan_office(w_m, d_m)
    return []


def _plan_bedroom(w: float, d: float) -> list[FurnitureItem]:
    items = []
    bed_w, bed_d, bed_h = min(1.6, w * 0.6), 2.0, 0.55
    if bed_d > d - CLEARANCE_M:
        bed_d, bed_w = bed_w, bed_d  # rotate if the room is shallow
    bed_x = (w - bed_w) / 2
    items.append(FurnitureItem("bed", bed_x, 0.1, 0, 0, bed_w, bed_d, bed_h))
    if w - bed_w > 0.7:
        items.append(FurnitureItem("wardrobe", w - 0.6, 0.0, 0, 0, 0.6, min(1.8, d * 0.4), 2.0))
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
    items = [FurnitureItem("sofa", 0.3, d - 0.9, 0, 0, min(2.2, w * 0.6), 0.9, 0.8)]
    items.append(FurnitureItem("coffee_table", 0.3 + min(2.2, w * 0.6) / 2 - 0.5, d - 1.8, 0, 0, 1.0, 0.6, 0.4))
    if w > 3.0 and d > 3.0:
        table_x, table_w = w - 1.8, 1.6
        items.append(FurnitureItem("dining_table", table_x, 0.3, 0, 0, table_w, 0.9, 0.75))
        chair_w = 0.45
        for cx in (table_x + 0.05, table_x + 0.55, table_x + 1.05, table_x + table_w - chair_w - 0.05):
            items.append(FurnitureItem("chair", cx, 1.4, 0, 0, chair_w, chair_w, 0.9))
    return items


def _plan_office(w: float, d: float) -> list[FurnitureItem]:
    return [FurnitureItem("desk", 0.2, 0.2, 0, 0, min(1.4, w - 0.4), 0.7, 0.75)]
