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

EYE_HEIGHT_M = 1.5  # interior-camera eye height above the storey floor (ASM-003)
WALL_INSET_M = 0.35  # interior-camera inset from the near wall's interior face (ASM-003)
INTERIOR_LENS_MIN_MM = 12.0  # widest acceptable interior lens (ASM-003)
INTERIOR_LENS_MAX_MM = 24.0  # narrowest acceptable interior lens (ASM-003)
CEILING_CAP_M = 2.4  # visible ceiling height cap so tall storeys do not force absurd lenses (ASM-003)


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

    Per S1: the camera sits at `centre - dist*forward`, so a corner's distance
    from the camera along the view axis is `dist + dot(v, forward)`. The
    constraint `|lateral| <= tan * (dist + dot(v, f))` rearranges to
    `dist >= |lateral|/tan - dot(v, f)` -- the depth term is **subtracted**
    because the binding corner is the *nearest* one. The result is the max over
    all corners of the horizontal and vertical requirements, clamped to
    MIN_DISTANCE and scaled by `margin`.
    """
    half_fov_x = math.atan(SENSOR_WIDTH_MM / (2 * lens_mm))
    half_fov_y = math.atan((SENSOR_WIDTH_MM * res_y) / (2 * lens_mm * res_x))
    tan_x, tan_y = math.tan(half_fov_x), math.tan(half_fov_y)

    required = 0.0
    for c in corners:
        v = (c[0] - centre[0], c[1] - centre[1], c[2] - centre[2])
        d_x = abs(_dot(v, right)) / tan_x - _dot(v, forward)
        d_y = abs(_dot(v, up)) / tan_y - _dot(v, forward)
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


def exterior_front_camera(
    model: dict, res_x: int, res_y: int, lens_mm: float = 35.0
) -> tuple[Vec3, Vec3, float]:
    """`(position, target, lens_mm)` for the street-facade camera, in metres.

    Fits `facade_bbox(model)` using **that box's own centre**
    `(plot_w/2, 0.0, total_h/2)` as both the fit centre and the camera anchor --
    never the plot centroid, whose mid-depth position both hid the old sign
    error and under-framed the facade. The camera stands south of the plot
    (negative y) looking north (+y) at the facade plane at y = 0.
    """
    bbox = building_bbox(model)
    corners = corners_of(bbox)
    centre = (
        model["plot_width_mm"] / 2000,
        0.0,
        sum(s["height_mm"] for s in model["storeys"]) / 2000,
    )
    forward = (0.0, 1.0, 0.0)  # looking north at the street facade
    right, up = basis_from_direction(forward)
    dist = fit_distance(corners, centre, forward, right, up, lens_mm, res_x, res_y)
    position = (centre[0], centre[1] - dist, centre[2])
    return position, centre, lens_mm


def exterior_aerial_camera(
    model: dict, res_x: int, res_y: int, lens_mm: float = 35.0
) -> tuple[Vec3, Vec3, float]:
    """`(position, target, lens_mm)` for the 45-degree south-east aerial camera.

    The fit centre is derived from `building_bbox(model)` so centre and box can
    never diverge again; the camera descends from the south-east toward the
    building's bbox centre.
    """
    bbox = building_bbox(model)
    corners = corners_of(bbox)
    centre = (
        (bbox[0][0] + bbox[1][0]) / 2,
        (bbox[0][1] + bbox[1][1]) / 2,
        (bbox[0][2] + bbox[1][2]) / 2,
    )
    # 45-degree descent from the south-east: +x / -y / above.
    forward = (-0.5, 0.5, -0.7071)
    right, up = basis_from_direction(forward)
    dist = fit_distance(corners, centre, forward, right, up, lens_mm, res_x, res_y)
    position = (
        centre[0] + dist * 0.5,
        centre[1] - dist * 0.5,
        centre[2] + dist * 0.7071,
    )
    return position, centre, lens_mm


def exterior_street_camera(
    model: dict, res_x: int, res_y: int, lens_mm: float = 35.0
) -> tuple[Vec3, Vec3, float]:
    """`(position, target, lens_mm)` for the 3/4 street-level hero, in metres.

    The pro-tubehouse angle: off the south-east street corner, looking
    slightly up at the facade so fins and parapets get raking parallax
    instead of the flat-frontal read. Target is the facade plane (y = 0) at
    ~55% of total height; the whole-building fit sets the distance, which
    lands the camera elevated (~opposite-balcony height, very Saigon) rather
    than cropping the parapet.
    """
    bbox = building_bbox(model)
    corners = corners_of(bbox)
    total_h = sum(s["height_mm"] for s in model["storeys"]) / 1000
    centre = (model["plot_width_mm"] / 2000, 0.0, total_h * 0.55)
    # 35° off the south axis toward the east, +8° up.
    forward = (-0.568, 0.811, 0.139)
    right, up = basis_from_direction(forward)
    dist = fit_distance(corners, centre, forward, right, up, lens_mm, res_x, res_y)
    position = (
        centre[0] - forward[0] * dist,
        centre[1] - forward[1] * dist,
        centre[2] - forward[2] * dist,
    )
    return position, centre, lens_mm


def _tall_item_at(room: dict, px: float, py: float, eye_m: float) -> bool:
    """Whether a furniture item tall enough to swallow the lens stands at (px, py).

    World-space point-in-footprint test against the seeded placement (the same
    rule the 3D scene was furnished with), with a 0.15 m margin. Only items
    reaching the eye height count -- rugs and tables never block a stance.
    """
    from .placement import plan_room

    r = room.get("interior") or room["rect"]
    x, y = r["x"] / 1000, r["y"] / 1000
    w, d = r["w"] / 1000, r["d"] / 1000
    seed = room.get("id", "")
    for item in plan_room(room.get("type", ""), w, d, seed=seed):
        if item.h < eye_m - 0.2:
            continue
        iw = item.d if item.rot_deg in (90, 270) else item.w
        id_ = item.w if item.rot_deg in (90, 270) else item.d
        if x + item.x - 0.15 <= px <= x + item.x + iw + 0.15 and \
           y + item.y - 0.15 <= py <= y + item.y + id_ + 0.15:
            return True
    return False

def interior_camera(
    storey: dict,
    room: dict,
    res_x: int,
    res_y: int,
    eye_height_m: float = EYE_HEIGHT_M,
    wall_inset_m: float = WALL_INSET_M,
    lens_min_mm: float = INTERIOR_LENS_MIN_MM,
    lens_max_mm: float = INTERIOR_LENS_MAX_MM,
) -> tuple[Vec3, Vec3, float]:
    """`(position, target, lens_mm)` for a camera standing **inside** a room (S2).

    Pull-back framing has no solution indoors -- a wall occupies the pull-back
    position -- so the camera is constrained against the near wall and the focal
    length is solved to fit the room at that fixed standoff. `room["interior"]`
    (the net usable rect after wall thickness) is preferred when present;
    otherwise the gross rect is used with the wall-inset standoff. The position
    is guaranteed strictly inside the room rect.
    """
    base_z = storey["base_z"] / 1000
    ceil_z = base_z + min(storey["height_mm"] / 1000, CEILING_CAP_M)
    r = room.get("interior") or room["rect"]
    x, y, w, d = r["x"] / 1000, r["y"] / 1000, r["w"] / 1000, r["d"] / 1000

    long_is_depth = room["rect"]["d"] >= room["rect"]["w"]
    z = min(base_z + eye_height_m, ceil_z - 0.15)
    if room.get("type") == "bedroom":
        # The bed hugs the near wall (y ~ 0.1); a near-wall camera stares away
        # from it and the hero reads as an empty room with doors. Shoot from
        # the far end back at the bed so the hero shows the dressed asset.
        # The stance dodges the seeded far-corner wardrobe variant.
        px = x + w * 0.75
        if _tall_item_at(room, px, y + d - wall_inset_m, eye_height_m):
            px = x + w * 0.25
        position = (px, y + d - wall_inset_m, z)
        target = (x + w / 2, y + wall_inset_m, z - 0.35)
        available = d - 2 * wall_inset_m
        half_w = max(px - x, x + w - px) - wall_inset_m
    elif room.get("type") == "kitchen":
        # Diagonal corner shot: the run spans the full near wall, so an axial
        # view fills the frame with carcase back. From the far corner opposite
        # the tall fridge the run reads with depth, tap, handles and the new
        # dining set behind. The fridge corner is seeded (mirrored layouts put
        # it right), so pick the clear corner -- a stance inside the fridge
        # renders a black frame.
        if _tall_item_at(room, x + w - wall_inset_m, y + d - wall_inset_m, z - base_z):
            position = (x + wall_inset_m, y + d - wall_inset_m, z)
            target = (x + w / 2 + 0.4, y + wall_inset_m, z - 0.35)
        else:
            position = (x + w - wall_inset_m, y + d - wall_inset_m, z)
            target = (x + w / 2 - 0.4, y + wall_inset_m, z - 0.35)
        available = max(w, d) - 2 * wall_inset_m
        half_w = w / 2
    elif long_is_depth:
        # Bedrooms anchor off-centre: a centred camera stares down the bed's
        # long axis from inside its footprint and the hero reads empty.
        px = x + w / 2
        position = (px, y + wall_inset_m, z)
        target = (x + w / 2, y + d - wall_inset_m, z - 0.2)
        available = d - 2 * wall_inset_m
        half_w = max(px - x, x + w - px) - wall_inset_m
    else:
        py = y + d / 2
        position = (x + wall_inset_m, py, z)
        target = (x + w - wall_inset_m, y + d / 2, z - 0.2)
        available = w - 2 * wall_inset_m
        half_w = max(py - y, y + d - py) - wall_inset_m

    available = max(available, 0.5)
    half_w = max(half_w, 0.3)
    half_v = max(z - base_z, ceil_z - z)
    f_x = (SENSOR_WIDTH_MM * available) / (2 * half_w)
    f_y = (SENSOR_WIDTH_MM * res_y * available) / (2 * res_x * half_v)
    lens_mm = min(max(min(f_x, f_y), lens_min_mm), lens_max_mm)
    return position, target, lens_mm


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
