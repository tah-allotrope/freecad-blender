"""Parametric door/window objects. Runs inside Blender."""
import bpy

from .geom import make_box
from .materials import get_material

FRAME_DEPTH = 0.06
FRAME_WIDTH = 0.06
GLASS_THICKNESS = 0.012
DOOR_LEAF_THICKNESS = 0.045


def build_opening_furniture(opening_mm, wall_mm, storey_base_z_m, style, collection):
    """Add a frame + leaf (door) or frame + glass pane (window) filling the
    void already cut into the wall for this opening."""
    width = opening_mm["width_mm"] / 1000
    sill = opening_mm["sill_mm"] / 1000
    head = opening_mm["head_mm"] / 1000
    height = head - sill
    thickness = wall_mm["thickness"] / 1000
    z = storey_base_z_m + sill

    if wall_mm["orientation"] == "vertical":
        x0 = wall_mm["x"] / 1000
        y0 = wall_mm["y"] / 1000 + opening_mm["offset_mm"] / 1000
        span_axis = "y"
    else:
        x0 = wall_mm["x"] / 1000 + opening_mm["offset_mm"] / 1000
        y0 = wall_mm["y"] / 1000
        span_axis = "x"

    frame_mat = get_material(style, "frame")
    name_base = opening_mm["id"]

    if span_axis == "y":
        make_box(f"{name_base}_frame_a", x0, y0, z, thickness, FRAME_WIDTH, height, collection, frame_mat)
        make_box(f"{name_base}_frame_b", x0, y0 + width - FRAME_WIDTH, z, thickness, FRAME_WIDTH, height, collection, frame_mat)
    else:
        make_box(f"{name_base}_frame_a", x0, y0, z, FRAME_WIDTH, thickness, height, collection, frame_mat)
        make_box(f"{name_base}_frame_b", x0 + width - FRAME_WIDTH, y0, z, FRAME_WIDTH, thickness, height, collection, frame_mat)

    if opening_mm["type"] == "window":
        glass_mat = get_material(style, "glass")
        if span_axis == "y":
            make_box(f"{name_base}_glass", x0 + thickness / 2 - GLASS_THICKNESS / 2, y0 + FRAME_WIDTH, z + FRAME_WIDTH,
                      GLASS_THICKNESS, width - 2 * FRAME_WIDTH, height - 2 * FRAME_WIDTH, collection, glass_mat)
        else:
            make_box(f"{name_base}_glass", x0 + FRAME_WIDTH, y0 + thickness / 2 - GLASS_THICKNESS / 2, z + FRAME_WIDTH,
                      width - 2 * FRAME_WIDTH, GLASS_THICKNESS, height - 2 * FRAME_WIDTH, collection, glass_mat)
    else:
        leaf_mat = get_material(style, "door_leaf")
        # Leaf hinged open ~20deg for a livelier render: place it just inside the frame,
        # rotated about one jamb rather than filling the void flat.
        leaf_w = width - 2 * FRAME_WIDTH
        if span_axis == "y":
            leaf = make_box(f"{name_base}_leaf", x0 + thickness / 2, y0 + FRAME_WIDTH, z, DOOR_LEAF_THICKNESS, leaf_w, height, collection, leaf_mat)
            leaf.rotation_euler[2] = 0.35
        else:
            leaf = make_box(f"{name_base}_leaf", x0 + FRAME_WIDTH, y0 + thickness / 2, z, leaf_w, DOOR_LEAF_THICKNESS, height, collection, leaf_mat)
            leaf.rotation_euler[2] = -0.35
