"""Stylized parametric furniture -- the fallback (and, for now, the only)
furniture source. No external assets are required for a furnished render.
Runs inside Blender.
"""

import math

from .geom import make_box, make_hinged_box
from .materials import get_material


class _Placer:
    """Bakes an item's rotation into its mesh vertices about a real pivot.

    Every mesh in this codebase bakes its world position into its vertices and
    leaves the object origin at (0, 0, 0), so rotating via the object's euler
    rotation pivots around the world origin and flings the mesh away (this
    shipped once as 32 scattered door leaves). All rotation therefore goes
    through `geom.make_hinged_box`, which rotates the vertices about an
    explicit pivot line before the object is created.
    """

    def __init__(self, pivot_x: float, pivot_y: float, angle_rad: float):
        self.pivot_x = pivot_x
        self.pivot_y = pivot_y
        self.angle_rad = angle_rad

    def box(self, name, x, y, z, w, d, h, collection, material=None):
        if abs(self.angle_rad) < 1e-9:
            return make_box(name, x, y, z, w, d, h, collection, material)
        return make_hinged_box(
            name, x, y, z, w, d, h,
            self.pivot_x, self.pivot_y, self.angle_rad,
            collection, material,
        )


def _placer_for(item, x, y):
    """A placer that rotates the item's whole footprint about its centre."""
    return _Placer(x + item.w / 2, y + item.d / 2, math.radians(item.rot_deg))


def build_item(item, room_x, room_y, base_z, style, collection):
    """item is a placement.FurnitureItem (room-local meters); room_x/room_y
    offset it into world space; base_z is the storey floor elevation (m)."""
    mat = get_material(style, "furniture")
    x = room_x + item.x
    y = room_y + item.y
    z = base_z

    builder = _BUILDERS.get(item.kind, _default_block)
    place = _placer_for(item, x, y)
    builder(item, x, y, z, mat, collection, place)


def _default_block(item, x, y, z, mat, collection, place):
    return place.box(f"furn_{item.kind}_{x:.2f}_{y:.2f}", x, y, z, item.w, item.d, item.h, collection, mat)


def _build_bed(item, x, y, z, mat, collection, place):
    place.box(f"bed_frame_{x:.2f}_{y:.2f}", x, y, z, item.w, item.d, 0.25, collection, mat)
    place.box(f"bed_mattress_{x:.2f}_{y:.2f}", x + 0.03, y + 0.03, z + 0.25, item.w - 0.06, item.d - 0.06, 0.2, collection, mat)
    place.box(f"bed_pillow1_{x:.2f}_{y:.2f}", x + 0.1, y + 0.05, z + 0.45, item.w * 0.35, 0.3, 0.1, collection, mat)
    place.box(f"bed_pillow2_{x:.2f}_{y:.2f}", x + item.w - item.w * 0.35 - 0.1, y + 0.05, z + 0.45, item.w * 0.35, 0.3, 0.1, collection, mat)
    return None


def _build_sofa(item, x, y, z, mat, collection, place):
    place.box(f"sofa_base_{x:.2f}_{y:.2f}", x, y, z, item.w, item.d, 0.4, collection, mat)
    place.box(f"sofa_back_{x:.2f}_{y:.2f}", x, y + item.d - 0.2, z + 0.4, item.w, 0.2, 0.4, collection, mat)
    return None


def _build_table_with_legs(item, x, y, z, mat, collection, place):
    top_h = 0.06
    place.box(f"table_top_{x:.2f}_{y:.2f}", x, y, z + item.h - top_h, item.w, item.d, top_h, collection, mat)
    leg = 0.06
    for lx, ly in ((x + leg / 2, y + leg / 2), (x + item.w - leg * 1.5, y + leg / 2),
                    (x + leg / 2, y + item.d - leg * 1.5), (x + item.w - leg * 1.5, y + item.d - leg * 1.5)):
        place.box(f"table_leg_{lx:.2f}_{ly:.2f}", lx, ly, z, leg, leg, item.h - top_h, collection, mat)
    return None


def _build_chair(item, x, y, z, mat, collection, place):
    place.box(f"chair_seat_{x:.2f}_{y:.2f}", x, y, z + item.h - 0.45, item.w, item.d, 0.05, collection, mat)
    place.box(f"chair_back_{x:.2f}_{y:.2f}", x, y + item.d - 0.05, z + item.h - 0.45, item.w, 0.05, 0.45, collection, mat)
    leg = 0.04
    for lx, ly in ((x + leg / 2, y + leg / 2), (x + item.w - leg * 1.5, y + leg / 2),
                    (x + leg / 2, y + item.d - leg * 1.5), (x + item.w - leg * 1.5, y + item.d - leg * 1.5)):
        place.box(f"chair_leg_{lx:.2f}_{ly:.2f}", lx, ly, z, leg, leg, item.h - 0.45, collection, mat)
    return None


def _build_kitchen_run(item, x, y, z, mat, collection, place):
    place.box(f"kitchen_counter_{x:.2f}_{y:.2f}", x, y, z, item.w, item.d, item.h, collection, mat)
    return None


def _build_wc(item, x, y, z, mat, collection, place):
    place.box(f"wc_base_{x:.2f}_{y:.2f}", x, y, z, item.w, item.d * 0.6, 0.4, collection, mat)
    place.box(f"wc_tank_{x:.2f}_{y:.2f}", x, y + item.d * 0.6, z + 0.35, item.w, item.d * 0.4, 0.45, collection, mat)
    return None


_BUILDERS = {
    "bed": _build_bed,
    "sofa": _build_sofa,
    "dining_table": _build_table_with_legs,
    "coffee_table": _build_table_with_legs,
    "desk": _build_table_with_legs,
    "chair": _build_chair,
    "kitchen_run": _build_kitchen_run,
    "wc": _build_wc,
}
