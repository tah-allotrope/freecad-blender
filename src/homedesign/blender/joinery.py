"""Parametric door/window objects. Runs inside Blender."""

from .geom import make_box, make_hinged_box
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

    # Head lintel: a FRAME_WIDTH-deep box across the opening head.
    reveal = 0.03
    lintel_depth = thickness + 2 * reveal
    if span_axis == "y":
        make_box(f"{name_base}_lintel", x0 - reveal, y0, z + height - FRAME_WIDTH,
                 lintel_depth, width, FRAME_WIDTH, collection, frame_mat)
    else:
        make_box(f"{name_base}_lintel", x0, y0 - reveal, z + height - FRAME_WIDTH,
                 width, lintel_depth, FRAME_WIDTH, collection, frame_mat)

    if opening_mm["type"] == "window":
        # 25mm-thick sill projecting 30mm past the wall face on the exterior
        # side (modelled on both faces; the joinery does not know which side is
        # exterior, and a belt-course read is correct from either angle).
        sill_thickness = 0.025
        if span_axis == "y":
            make_box(f"{name_base}_sill", x0 - reveal, y0, z - sill_thickness,
                     lintel_depth, width, sill_thickness, collection, frame_mat)
        else:
            make_box(f"{name_base}_sill", x0, y0 - reveal, z - sill_thickness,
                     width, lintel_depth, sill_thickness, collection, frame_mat)

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
        # Leaf hinged open ~20deg for a livelier render: swing it about the
        # near jamb rather than filling the void flat. Rotation is baked into
        # the mesh about that hinge line (see make_hinged_box) -- rotating
        # the object itself would pivot around the world origin instead.
        leaf_w = width - 2 * FRAME_WIDTH
        if span_axis == "y":
            hinge_x, hinge_y = x0 + thickness / 2, y0 + FRAME_WIDTH
            make_hinged_box(f"{name_base}_leaf", x0 + thickness / 2, y0 + FRAME_WIDTH, z,
                             DOOR_LEAF_THICKNESS, leaf_w, height, hinge_x, hinge_y, 0.35, collection, leaf_mat)
        else:
            hinge_x, hinge_y = x0 + FRAME_WIDTH, y0 + thickness / 2
            make_hinged_box(f"{name_base}_leaf", x0 + FRAME_WIDTH, y0 + thickness / 2, z,
                             leaf_w, DOOR_LEAF_THICKNESS, height, hinge_x, hinge_y, -0.35, collection, leaf_mat)
