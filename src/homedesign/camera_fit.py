"""Analytic camera framing (S4): fit an axis-aligned box in frame.

Pure math over plain tuples -- no `bpy` import, so this module is fully
unit-testable outside Blender. The Blender-side camera builders consume it.
"""
from __future__ import annotations

import math
from typing import Iterable

Vec3 = tuple[float, float, float]
BBox = tuple[Vec3, Vec3]  # (min_corner, max_corner)

MARGIN = 1.08  # leave 8% so the subject never touches the frame edge
MIN_DISTANCE = 1.0  # degenerate boxes must not put the camera inside geometry
SENSOR_WIDTH_MM = 36.0


def basis_from_direction(forward: Vec3) -> tuple[Vec3, Vec3]:
    """Orthonormal (right, up) for a forward vector, using world +Z as the up
    reference. Falls back to +Y when forward is parallel to +Z."""
    f = _unit(forward)
    ref = (0.0, 0.0, 1.0) if abs(f[2]) < 0.999 else (0.0, 1.0, 0.0)
    right = _unit(_cross(f, ref))
    up = _cross(right, f)
    return right, up


def corners_of(bbox: BBox) -> list[Vec3]:
    (x1, y1, z1), (x2, y2, z2) = bbox
    return [
        (x1, y1, z1), (x1, y1, z2), (x1, y2, z1), (x1, y2, z2),
        (x2, y1, z1), (x2, y1, z2), (x2, y2, z1), (x2, y2, z2),
    ]


def fit_distance(
    corners: Iterable[Vec3],
    centre: Vec3,
    forward: Vec3,
    right: Vec3,
    up: Vec3,
    lens_mm: float,
    res_x: int,
    res_y: int,
    margin: float = MARGIN,
) -> float:
    """Camera distance from `centre` along `-forward` that fits every corner.

    Per S4: for each corner, the required pull-back is the larger of the
    horizontal and vertical distances needed so the corner's offset onto the
    camera axes stays inside the half-FOV cones. The result is clamped to
    MIN_DISTANCE.
    """
    half_fov_x = math.atan(SENSOR_WIDTH_MM / (2 * lens_mm))
    half_fov_y = math.atan((SENSOR_WIDTH_MM * res_y) / (2 * lens_mm * res_x))
    tan_x, tan_y = math.tan(half_fov_x), math.tan(half_fov_y)

    required = 0.0
    for c in corners:
        v = (c[0] - centre[0], c[1] - centre[1], c[2] - centre[2])
        d_x = abs(_dot(v, right)) / tan_x + _dot(v, forward)
        d_y = abs(_dot(v, up)) / tan_y + _dot(v, forward)
        required = max(required, d_x, d_y)
    return max(MIN_DISTANCE, margin * required)


def building_bbox(model: dict) -> BBox:
    """World-space bounding box of the whole building in metres.

    Plot footprint x total storey height (heights accumulate in level order),
    excluding the ground plane and roof overhang. Used by the aerial camera,
    which wants the full footprint in frame.
    """
    plot_w = model["plot_width_mm"] / 1000
    plot_d = model["plot_depth_mm"] / 1000
    total_h = sum(s["height_mm"] for s in model["storeys"]) / 1000
    return (0.0, 0.0, 0.0), (plot_w, plot_d, total_h)


def facade_bbox(model: dict) -> BBox:
    """Street-facade box: plot width x total height, zero depth.

    The front camera frames this instead of the full footprint -- on a long
    narrow tube house the plot depth would otherwise dominate the required
    distance and leave the facade a small strip in frame (TEST-008 requires
    >30% occupancy per dimension).
    """
    plot_w = model["plot_width_mm"] / 1000
    total_h = sum(s["height_mm"] for s in model["storeys"]) / 1000
    return (0.0, 0.0, 0.0), (plot_w, 0.0, total_h)


def room_subject_bbox(storey: dict, room: dict) -> BBox:
    """Room interior volume (floor to min(storey height, 2.4m)) unioned with
    the world-space footprint of every furniture item placed in it."""
    from .placement import plan_room

    base_z = storey["base_z"] / 1000
    height_m = min(storey["height_mm"] / 1000, 2.4)
    r = room["rect"]
    x, y = r["x"] / 1000, r["y"] / 1000
    w, d = r["w"] / 1000, r["d"] / 1000

    min_x, min_y, min_z = x, y, base_z
    max_x, max_y, max_z = x + w, y + d, base_z + height_m

    for item in plan_room(room["type"], w, d):
        # Room-local -> world. Rotated items swap w/d on the floor.
        iw, id_ = (item.d, item.w) if item.rot_deg in (90, 270) else (item.w, item.d)
        ix, iy = x + item.x, y + item.y
        min_x = min(min_x, ix)
        min_y = min(min_y, iy)
        max_x = max(max_x, ix + iw)
        max_y = max(max_y, iy + id_)
        max_z = max(max_z, base_z + item.h)
    return (min_x, min_y, min_z), (max_x, max_y, max_z)


def _unit(v: Vec3) -> Vec3:
    n = math.sqrt(v[0] * v[0] + v[1] * v[1] + v[2] * v[2])
    return (v[0] / n, v[1] / n, v[2] / n) if n else (0.0, 0.0, 1.0)


def _cross(a: Vec3, b: Vec3) -> Vec3:
    return (
        a[1] * b[2] - a[2] * b[1],
        a[2] * b[0] - a[0] * b[2],
        a[0] * b[1] - a[1] * b[0],
    )


def _dot(a: Vec3, b: Vec3) -> float:
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
