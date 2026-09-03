"""Stylized parametric furniture -- the fallback (and, for now, the only)
furniture source. No external assets are required for a furnished render.
Runs inside Blender.
"""

import math

from .geom import make_box, make_cylinder, make_hinged_box
from .materials import furniture_material_key, get_material

_HAS_ASSET = False
try:
    from . import asset_library
    _HAS_ASSET = True
except Exception:
    _HAS_ASSET = False


# Edge softening for every procedural piece. 3 mm is the smallest radius that
# still catches a highlight at interior render resolutions; below that the edge
# reads as a perfectly sharp CG boundary again.
BEVEL = 0.003


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

    def box(self, name, x, y, z, w, d, h, collection, material=None, bevel: float = 0.0):
        if abs(self.angle_rad) < 1e-9:
            return make_box(name, x, y, z, w, d, h, collection, material, bevel=bevel)
        return make_hinged_box(
            name, x, y, z, w, d, h,
            self.pivot_x, self.pivot_y, self.angle_rad,
            collection, material, bevel=bevel,
        )

    def cylinder(self, name, x, y, z, radius, h, collection, material=None,
                 segments: int = 16, axis: str = "Z"):
        """A cylinder whose base centre is (x, y, z), rotated with the item.

        Rotation is baked into the vertices for the same reason boxes bake it
        (see the class docstring), so the placer rotates the base point about
        the pivot and, for a horizontal cylinder, swaps its axis on a quarter
        turn.
        """
        cx, cy = x, y
        axis_out = axis
        if abs(self.angle_rad) > 1e-9:
            cos_a, sin_a = math.cos(self.angle_rad), math.sin(self.angle_rad)
            dx, dy = x - self.pivot_x, y - self.pivot_y
            cx = self.pivot_x + dx * cos_a - dy * sin_a
            cy = self.pivot_y + dx * sin_a + dy * cos_a
            if axis in ("X", "Y") and abs(cos_a) < 0.5:
                axis_out = "Y" if axis == "X" else "X"
        return make_cylinder(name, cx, cy, z, radius, h, collection, material,
                             segments=segments, axis=axis_out)


def _placer_for(item, x, y):
    """A placer that rotates the item's whole footprint about its centre."""
    return _Placer(x + item.w / 2, y + item.d / 2, math.radians(item.rot_deg))


def build_item(item, room_x, room_y, base_z, style, collection):
    """item is a placement.FurnitureItem (room-local meters); room_x/room_y
    offset it into world space; base_z is the storey floor elevation (m)."""
    if _HAS_ASSET:
        try:
            obj = asset_library.build_from_asset(item, room_x, room_y, base_z, collection)
            if obj is not None:
                return obj
        except Exception:
            pass
    mat = get_material(style, furniture_material_key(item.kind))
    x = room_x + item.x
    y = room_y + item.y
    z = base_z

    builder = _BUILDERS.get(item.kind, _default_block)
    place = _placer_for(item, x, y)
    builder(item, x, y, z, mat, collection, place)


def _default_block(item, x, y, z, mat, collection, place):
    return place.box(f"furn_{item.kind}_{x:.2f}_{y:.2f}", x, y, z, item.w, item.d, item.h,
                     collection, mat, bevel=BEVEL)


def _build_bed(item, x, y, z, mat, collection, place):
    """Plinth, recessed frame rail, mattress with a rolled edge, two pillows,
    and a headboard on the wall side."""
    tag = f"{x:.2f}_{y:.2f}"
    plinth_h, rail_h = 0.08, 0.17
    # A recessed plinth reads as a shadow gap under the bed rather than a slab
    # sitting flat on the floor.
    place.box(f"bed_plinth_{tag}", x + 0.06, y + 0.06, z, item.w - 0.12, item.d - 0.12,
              plinth_h, collection, mat, bevel=BEVEL)
    place.box(f"bed_frame_{tag}", x, y, z + plinth_h, item.w, item.d, rail_h,
              collection, mat, bevel=BEVEL)
    place.box(f"bed_mattress_{tag}", x + 0.03, y + 0.03, z + plinth_h + rail_h,
              item.w - 0.06, item.d - 0.06, 0.2, collection, mat, bevel=0.05)
    top = z + plinth_h + rail_h + 0.2
    pillow_w = item.w * 0.42
    place.box(f"bed_pillow1_{tag}", x + item.w * 0.04, y + 0.06, top,
              pillow_w, 0.32, 0.1, collection, mat, bevel=0.04)
    place.box(f"bed_pillow2_{tag}", x + item.w - pillow_w - item.w * 0.04, y + 0.06, top,
              pillow_w, 0.32, 0.1, collection, mat, bevel=0.04)
    place.box(f"bed_headboard_{tag}", x, y - 0.05, z + plinth_h,
              item.w, 0.05, 0.75, collection, mat, bevel=BEVEL)
    return None


def _build_sofa(item, x, y, z, mat, collection, place):
    """Frame, arms, and separated seat and back cushions with gaps between."""
    tag = f"{x:.2f}_{y:.2f}"
    arm_w = min(0.16, item.w * 0.12)
    back_d = min(0.22, item.d * 0.28)
    seat_h, frame_h = 0.42, 0.30
    inner_w = max(0.2, item.w - arm_w * 2)
    seat_d = max(0.2, item.d - back_d)

    place.box(f"sofa_base_{tag}", x, y, z, item.w, item.d, frame_h, collection, mat, bevel=BEVEL)
    place.box(f"sofa_arm_l_{tag}", x, y, z, arm_w, item.d, 0.62, collection, mat, bevel=0.03)
    place.box(f"sofa_arm_r_{tag}", x + item.w - arm_w, y, z, arm_w, item.d, 0.62,
              collection, mat, bevel=0.03)
    place.box(f"sofa_backframe_{tag}", x + arm_w, y + item.d - back_d, z,
              inner_w, back_d, 0.72, collection, mat, bevel=BEVEL)

    # Two or three cushions with a real gap, which is what separates a sofa
    # from an upholstered box.
    seats = 3 if item.w > 1.9 else 2
    gap = 0.02
    cushion_w = (inner_w - gap * (seats - 1)) / seats
    for i in range(seats):
        cx = x + arm_w + i * (cushion_w + gap)
        place.box(f"sofa_seat_{i}_{tag}", cx, y + 0.04, z + frame_h,
                  cushion_w, seat_d - 0.06, seat_h - frame_h + 0.06,
                  collection, mat, bevel=0.045)
        place.box(f"sofa_back_{i}_{tag}", cx, y + item.d - back_d + 0.03, z + seat_h,
                  cushion_w, back_d - 0.06, 0.30, collection, mat, bevel=0.045)
    return None


def _build_table_with_legs(item, x, y, z, mat, collection, place):
    """Bevelled top over an apron rail, on four turned (cylindrical) legs."""
    tag = f"{x:.2f}_{y:.2f}"
    top_h, apron_h, inset = 0.04, 0.07, 0.09
    leg_r = 0.028
    place.box(f"table_top_{tag}", x, y, z + item.h - top_h, item.w, item.d, top_h,
              collection, mat, bevel=0.012)
    apron_z = z + item.h - top_h - apron_h
    place.box(f"table_apron_n_{tag}", x + inset, y + inset, apron_z,
              item.w - inset * 2, 0.03, apron_h, collection, mat, bevel=BEVEL)
    place.box(f"table_apron_s_{tag}", x + inset, y + item.d - inset - 0.03, apron_z,
              item.w - inset * 2, 0.03, apron_h, collection, mat, bevel=BEVEL)
    for lx, ly in ((x + inset, y + inset),
                   (x + item.w - inset, y + inset),
                   (x + inset, y + item.d - inset),
                   (x + item.w - inset, y + item.d - inset)):
        place.cylinder(f"table_leg_{lx:.2f}_{ly:.2f}", lx, ly, z, leg_r,
                       item.h - top_h, collection, mat)
    return None


def _build_chair(item, x, y, z, mat, collection, place):
    """Bevelled seat pad, a slatted back, and four round legs."""
    tag = f"{x:.2f}_{y:.2f}"
    seat_h = min(0.45, item.h * 0.55)
    seat_z = z + seat_h
    leg_r, inset = 0.018, 0.055
    place.box(f"chair_seat_{tag}", x, y, seat_z, item.w, item.d, 0.055,
              collection, mat, bevel=0.014)
    # Three vertical slats with gaps, rather than one solid back panel.
    back_h = max(0.2, item.h - seat_h - 0.055)
    slat_w = item.w * 0.18
    for i in range(3):
        sx = x + item.w * (0.12 + i * 0.29)
        place.box(f"chair_slat_{i}_{tag}", sx, y + item.d - 0.045, seat_z + 0.055,
                  slat_w, 0.028, back_h, collection, mat, bevel=BEVEL)
    place.box(f"chair_rail_{tag}", x + item.w * 0.10, y + item.d - 0.05,
              seat_z + 0.055 + back_h, item.w * 0.80, 0.035, 0.05,
              collection, mat, bevel=BEVEL)
    for lx, ly in ((x + inset, y + inset),
                   (x + item.w - inset, y + inset),
                   (x + inset, y + item.d - inset),
                   (x + item.w - inset, y + item.d - inset)):
        place.cylinder(f"chair_leg_{lx:.2f}_{ly:.2f}", lx, ly, z, leg_r, seat_h, collection, mat)
    return None


def _build_kitchen_run(item, x, y, z, mat, collection, place):
    """Plinth, carcase, panelled doors with handles, worktop and upstand, a
    sink recess and a tap — no CC0 kitchen run exists, so this one carries the
    whole scene."""
    tag = f"{x:.2f}_{y:.2f}"
    plinth_h = 0.10
    top_h = 0.04
    carcase_h = max(0.3, item.h - plinth_h - top_h)
    place.box(f"kitchen_plinth_{tag}", x + 0.05, y + 0.03, z,
              item.w - 0.1, item.d - 0.06, plinth_h, collection, mat, bevel=BEVEL)
    place.box(f"kitchen_carcase_{tag}", x, y, z + plinth_h, item.w, item.d, carcase_h,
              collection, mat, bevel=BEVEL)

    # One door per ~600 mm module, each with a recessed panel and a bar handle.
    modules = max(1, int(round(item.w / 0.6)))
    door_w = item.w / modules
    for i in range(modules):
        dx = x + i * door_w + 0.006
        w = door_w - 0.012
        place.box(f"kitchen_door_{i}_{tag}", dx, y - 0.018, z + plinth_h + 0.01,
                  w, 0.018, carcase_h - 0.02, collection, mat, bevel=0.006)
        place.box(f"kitchen_panel_{i}_{tag}", dx + 0.06, y - 0.026,
                  z + plinth_h + 0.07, max(0.05, w - 0.12), 0.008,
                  max(0.05, carcase_h - 0.14), collection, mat, bevel=0.004)
        place.cylinder(f"kitchen_handle_{i}_{tag}", dx + w / 2, y - 0.045,
                       z + plinth_h + carcase_h - 0.09, 0.009, w * 0.5,
                       collection, mat, axis="X")

    top_z = z + plinth_h + carcase_h
    place.box(f"kitchen_worktop_{tag}", x - 0.015, y - 0.03, top_z,
              item.w + 0.03, item.d + 0.03, top_h, collection, mat, bevel=0.008)
    place.box(f"kitchen_upstand_{tag}", x, y + item.d - 0.02, top_z + top_h,
              item.w, 0.02, 0.09, collection, mat, bevel=BEVEL)
    # Sink: a shallow recess rim plus a mixer tap and spout.
    sink_w = min(0.5, item.w * 0.35)
    sx = x + item.w * 0.62
    place.box(f"kitchen_sink_{tag}", sx, y + item.d * 0.25, top_z + top_h - 0.008,
              sink_w, item.d * 0.45, 0.01, collection, mat, bevel=0.004)
    tap_x = sx + sink_w / 2
    tap_y = y + item.d * 0.78
    place.cylinder(f"kitchen_tap_{tag}", tap_x, tap_y, top_z + top_h, 0.016, 0.24,
                   collection, mat)
    place.cylinder(f"kitchen_spout_{tag}", tap_x, tap_y - 0.09, top_z + top_h + 0.23,
                   0.011, 0.18, collection, mat, axis="Y")
    return None


def _build_wc(item, x, y, z, mat, collection, place):
    """Pedestal, bowl, seat, lid, cistern and a flush plate."""
    tag = f"{x:.2f}_{y:.2f}"
    bowl_d = item.d * 0.62
    place.box(f"wc_pedestal_{tag}", x + item.w * 0.22, y + bowl_d * 0.15, z,
              item.w * 0.56, bowl_d * 0.6, 0.20, collection, mat, bevel=0.03)
    place.box(f"wc_base_{tag}", x + 0.01, y, z + 0.18, item.w - 0.02, bowl_d, 0.20,
              collection, mat, bevel=0.055)
    place.box(f"wc_seat_{tag}", x, y, z + 0.38, item.w, bowl_d, 0.03,
              collection, mat, bevel=0.014)
    place.box(f"wc_lid_{tag}", x, y + bowl_d * 0.55, z + 0.41, item.w, bowl_d * 0.45, 0.025,
              collection, mat, bevel=0.012)
    tank_d = max(0.10, item.d - bowl_d)
    place.box(f"wc_tank_{tag}", x + 0.015, y + bowl_d, z + 0.34, item.w - 0.03, tank_d, 0.42,
              collection, mat, bevel=0.02)
    place.box(f"wc_flush_{tag}", x + item.w * 0.34, y + bowl_d + tank_d - 0.012,
              z + 0.62, item.w * 0.32, 0.012, 0.07, collection, mat, bevel=0.005)
    return None


def _build_shelving(item, x, y, z, mat, collection, place):
    """Carcase with a back panel and real shelves, not a filled block."""
    tag = f"{x:.2f}_{y:.2f}"
    t = 0.022
    place.box(f"shelving_side_l_{tag}", x, y, z, t, item.d, item.h, collection, mat, bevel=BEVEL)
    place.box(f"shelving_side_r_{tag}", x + item.w - t, y, z, t, item.d, item.h,
              collection, mat, bevel=BEVEL)
    place.box(f"shelving_back_{tag}", x + t, y + item.d - 0.01, z, item.w - t * 2, 0.01, item.h,
              collection, mat, bevel=0.0)
    bays = max(2, int(item.h / 0.36))
    for i in range(bays + 1):
        sz = z + (item.h - t) * i / bays
        place.box(f"shelving_shelf_{i}_{tag}", x + t, y, sz, item.w - t * 2, item.d, t,
                  collection, mat, bevel=0.006)
    return None


def _build_console(item, x, y, z, mat, collection, place):
    """Carcase on legs with two panelled drawers and bar handles."""
    tag = f"{x:.2f}_{y:.2f}"
    leg_h = min(0.16, item.h * 0.28)
    body_h = max(0.12, item.h - leg_h)
    place.box(f"console_body_{tag}", x, y, z + leg_h, item.w, item.d, body_h,
              collection, mat, bevel=BEVEL)
    for i in range(2):
        dz = z + leg_h + 0.012 + i * (body_h / 2)
        dh = body_h / 2 - 0.024
        place.box(f"console_drawer_{i}_{tag}", x + 0.012, y - 0.016, dz,
                  item.w - 0.024, 0.016, dh, collection, mat, bevel=0.006)
        place.cylinder(f"console_handle_{i}_{tag}", x + item.w / 2, y - 0.04,
                       dz + dh / 2, 0.008, item.w * 0.34, collection, mat, axis="X")
    for lx, ly in ((x + 0.05, y + 0.05), (x + item.w - 0.05, y + 0.05),
                   (x + 0.05, y + item.d - 0.05), (x + item.w - 0.05, y + item.d - 0.05)):
        place.cylinder(f"console_leg_{lx:.2f}_{ly:.2f}", lx, ly, z, 0.02, leg_h, collection, mat)
    return None


def _build_car(item, x, y, z, mat, collection, place):
    """Body, cabin and four wheels — a parked car in the garage bay."""
    tag = f"{x:.2f}_{y:.2f}"
    wheel_r = min(0.32, item.h * 0.24)
    body_z = z + wheel_r * 0.75
    body_h = max(0.3, item.h * 0.45)
    place.box(f"car_body_{tag}", x, y + item.d * 0.02, body_z,
              item.w, item.d * 0.96, body_h, collection, mat, bevel=0.09)
    place.box(f"car_cabin_{tag}", x + item.w * 0.06, y + item.d * 0.24, body_z + body_h,
              item.w * 0.88, item.d * 0.46, max(0.25, item.h - body_h - wheel_r),
              collection, mat, bevel=0.07)
    for wx in (x + item.w * 0.06, x + item.w * 0.94):
        for wy in (y + item.d * 0.20, y + item.d * 0.80):
            place.cylinder(f"car_wheel_{wx:.2f}_{wy:.2f}", wx, wy, z + wheel_r,
                           wheel_r, 0.10, collection, mat, axis="X")
    return None


def _build_planter(item, x, y, z, mat, collection, place):
    """Tapered box, a soil surface, and a few foliage masses above it."""
    tag = f"{x:.2f}_{y:.2f}"
    box_h = min(item.h * 0.45, 0.5)
    place.box(f"planter_box_{tag}", x, y, z, item.w, item.d, box_h,
              collection, mat, bevel=0.02)
    place.box(f"planter_rim_{tag}", x - 0.015, y - 0.015, z + box_h - 0.05,
              item.w + 0.03, item.d + 0.03, 0.05, collection, mat, bevel=0.012)
    place.box(f"planter_soil_{tag}", x + 0.03, y + 0.03, z + box_h - 0.06,
              item.w - 0.06, item.d - 0.06, 0.02, collection, mat, bevel=0.0)
    foliage_h = max(0.15, item.h - box_h)
    for i in range(3):
        fx = x + item.w * (0.10 + i * 0.29)
        place.box(f"planter_foliage_{i}_{tag}", fx, y + item.d * 0.18,
                  z + box_h - 0.02 + foliage_h * 0.05 * i,
                  item.w * 0.26, item.d * 0.62, foliage_h * (0.7 + 0.12 * i),
                  collection, mat, bevel=0.06)
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
    "shelving": _build_shelving,
    "console": _build_console,
    "car": _build_car,
    "planter": _build_planter,
}
