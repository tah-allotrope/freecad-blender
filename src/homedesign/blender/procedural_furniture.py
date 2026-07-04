"""Stylized parametric furniture -- the fallback (and, for now, the only)
furniture source. No external assets are required for a furnished render.
Runs inside Blender.
"""
import bpy

from .geom import make_box
from .materials import get_material


def build_item(item, room_x, room_y, base_z, style, collection):
    """item is a placement.FurnitureItem (room-local meters); room_x/room_y
    offset it into world space; base_z is the storey floor elevation (m)."""
    mat = get_material(style, "furniture")
    x = room_x + item.x
    y = room_y + item.y
    z = base_z

    builder = _BUILDERS.get(item.kind, _default_block)
    obj = builder(item, x, y, z, mat, collection)
    if obj is not None and item.rot_deg:
        import math
        obj.rotation_euler[2] = math.radians(item.rot_deg)


def _default_block(item, x, y, z, mat, collection):
    return make_box(f"furn_{item.kind}_{x:.2f}_{y:.2f}", x, y, z, item.w, item.d, item.h, collection, mat)


def _build_bed(item, x, y, z, mat, collection):
    make_box(f"bed_frame_{x:.2f}_{y:.2f}", x, y, z, item.w, item.d, 0.25, collection, mat)
    make_box(f"bed_mattress_{x:.2f}_{y:.2f}", x + 0.03, y + 0.03, z + 0.25, item.w - 0.06, item.d - 0.06, 0.2, collection, mat)
    make_box(f"bed_pillow1_{x:.2f}_{y:.2f}", x + 0.1, y + 0.05, z + 0.45, item.w * 0.35, 0.3, 0.1, collection, mat)
    make_box(f"bed_pillow2_{x:.2f}_{y:.2f}", x + item.w - item.w * 0.35 - 0.1, y + 0.05, z + 0.45, item.w * 0.35, 0.3, 0.1, collection, mat)
    return None


def _build_sofa(item, x, y, z, mat, collection):
    make_box(f"sofa_base_{x:.2f}_{y:.2f}", x, y, z, item.w, item.d, 0.4, collection, mat)
    make_box(f"sofa_back_{x:.2f}_{y:.2f}", x, y + item.d - 0.2, z + 0.4, item.w, 0.2, 0.4, collection, mat)
    return None


def _build_table_with_legs(item, x, y, z, mat, collection):
    top_h = 0.06
    make_box(f"table_top_{x:.2f}_{y:.2f}", x, y, z + item.h - top_h, item.w, item.d, top_h, collection, mat)
    leg = 0.06
    for lx, ly in ((x + leg / 2, y + leg / 2), (x + item.w - leg * 1.5, y + leg / 2),
                    (x + leg / 2, y + item.d - leg * 1.5), (x + item.w - leg * 1.5, y + item.d - leg * 1.5)):
        make_box(f"table_leg_{lx:.2f}_{ly:.2f}", lx, ly, z, leg, leg, item.h - top_h, collection, mat)
    return None


def _build_chair(item, x, y, z, mat, collection):
    make_box(f"chair_seat_{x:.2f}_{y:.2f}", x, y, z + item.h - 0.45, item.w, item.d, 0.05, collection, mat)
    make_box(f"chair_back_{x:.2f}_{y:.2f}", x, y + item.d - 0.05, z + item.h - 0.45, item.w, 0.05, 0.45, collection, mat)
    leg = 0.04
    for lx, ly in ((x + leg / 2, y + leg / 2), (x + item.w - leg * 1.5, y + leg / 2),
                    (x + leg / 2, y + item.d - leg * 1.5), (x + item.w - leg * 1.5, y + item.d - leg * 1.5)):
        make_box(f"chair_leg_{lx:.2f}_{ly:.2f}", lx, ly, z, leg, leg, item.h - 0.45, collection, mat)
    return None


def _build_kitchen_run(item, x, y, z, mat, collection):
    make_box(f"kitchen_counter_{x:.2f}_{y:.2f}", x, y, z, item.w, item.d, item.h, collection, mat)
    return None


def _build_wc(item, x, y, z, mat, collection):
    make_box(f"wc_base_{x:.2f}_{y:.2f}", x, y, z, item.w, item.d * 0.6, 0.4, collection, mat)
    make_box(f"wc_tank_{x:.2f}_{y:.2f}", x, y + item.d * 0.6, z + 0.35, item.w, item.d * 0.4, 0.45, collection, mat)
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
