"""Parametric door/window objects. Runs inside Blender."""

from .geom import make_box, make_hinged_box
from .materials import get_material

FRAME_DEPTH = 0.06
DOOR_SWING_RAD = 0.0
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
    # Mullion / transom bars when divisions are authored
    divisions = opening_mm.get("divisions")
    if divisions:
        try:
            from homedesign.facade import opening_division_lines
            bars = opening_division_lines(opening_mm["width_mm"], opening_mm["head_mm"] - opening_mm["sill_mm"], divisions)
            bar_depth = GLASS_THICKNESS * 2
            for idx, bar in enumerate(bars):
                # bar offsets are relative to opening bottom-left
                if span_axis == "y":
                    bx = x0 + thickness / 2 - bar_depth / 2
                    by = y0 + FRAME_WIDTH + bar["x_mm"] / 1000
                    bw = bar_depth
                    bd = bar["w_mm"] / 1000
                    bh = bar["h_mm"] / 1000
                    bz = z + FRAME_WIDTH + bar["y_mm"] / 1000
                    # horizontal bars span full width: bar["x_mm"] is 0, so by corrected
                    if bar["x_mm"] == 0.0:
                        by = y0 + FRAME_WIDTH
                        bd = width - 2 * FRAME_WIDTH
                else:
                    bx = x0 + FRAME_WIDTH + bar["x_mm"] / 1000
                    by = y0 + thickness / 2 - bar_depth / 2
                    bw = bar["w_mm"] / 1000
                    bd = bar_depth
                    bh = bar["h_mm"] / 1000
                    bz = z + FRAME_WIDTH + bar["y_mm"] / 1000
                    if bar["x_mm"] == 0.0:
                        bx = x0 + FRAME_WIDTH
                        bw = width - 2 * FRAME_WIDTH
                make_box(f"{name_base}_bar_{idx}", bx, by, bz, bw, bd, bh, collection, frame_mat)
        except Exception:
            pass
    else:
        leaf_mat = get_material(style, "door_leaf")
        leaf_w = width - 2 * FRAME_WIDTH
        # Leaf sits centred within the wall thickness so its plane is inside the
        # frame depth (FRAME_DEPTH=0.06). Hinge edge coincides with the frame's
        # inner jamb face.
        if span_axis == "y":
            hinge_y = y0 + FRAME_WIDTH
            leaf_x = x0 + thickness / 2 - DOOR_LEAF_THICKNESS / 2
            hinge_x = leaf_x
            make_hinged_box(f"{name_base}_leaf", leaf_x, y0 + FRAME_WIDTH, z,
                             DOOR_LEAF_THICKNESS, leaf_w, height, hinge_x, hinge_y, DOOR_SWING_RAD, collection, leaf_mat)
        else:
            hinge_x = x0 + FRAME_WIDTH
            leaf_y = y0 + thickness / 2 - DOOR_LEAF_THICKNESS / 2
            hinge_y = leaf_y
            make_hinged_box(f"{name_base}_leaf", x0 + FRAME_WIDTH, leaf_y, z,
                             leaf_w, DOOR_LEAF_THICKNESS, height, hinge_x, hinge_y, -DOOR_SWING_RAD, collection, leaf_mat)
        # Lever handle on both faces: backplate + horizontal lever near the
        # opening stile (~120mm from the frame edge) at 1000mm above the sill.
        # Same opening size/position — finish-level detail only.
        handle_z = z + 1.0
        if span_axis == "y":
            hx = x0 + thickness / 2
            hy = y0 + width - FRAME_WIDTH - 0.12
            for side in (-1.0, 1.0):
                px = hx + side * (DOOR_LEAF_THICKNESS / 2 + 0.006)
                make_box(f"{name_base}_handle_plate_{int(side)}", px - 0.006, hy - 0.025, handle_z - 0.11,
                         0.012, 0.05, 0.22, collection, frame_mat)
                make_box(f"{name_base}_handle_lever_{int(side)}", px - 0.01, hy - 0.14, handle_z + 0.05,
                         0.02, 0.13, 0.025, collection, frame_mat)
        else:
            hx = x0 + width - FRAME_WIDTH - 0.12
            hy = y0 + thickness / 2
            for side in (-1.0, 1.0):
                py = hy + side * (DOOR_LEAF_THICKNESS / 2 + 0.006)
                make_box(f"{name_base}_handle_plate_{int(side)}", hx - 0.025, py - 0.006, handle_z - 0.11,
                         0.05, 0.012, 0.22, collection, frame_mat)
                make_box(f"{name_base}_handle_lever_{int(side)}", hx - 0.065, py - 0.01, handle_z + 0.05,
                         0.13, 0.02, 0.025, collection, frame_mat)
        # Recessed-look panel mouldings: two stacked rail frames per face in
        # the leaf finish — the shadow lines read as panelled joinery at
        # render distance. Static coordinates assume DOOR_SWING_RAD == 0 (the
        # leaf itself is unrotated); revisit both if a swing is ever enabled.
        inset, rail, proud = 0.14, 0.055, 0.012
        panel_w = leaf_w - inset * 2
        if panel_w > 0.25 and height > 1.6:
            panels = [(z + 0.2, z + 0.95), (z + 1.1, min(z + height - 0.15, z + 1.85))]
            if span_axis == "y":
                for fi, sgn in enumerate((-1.0, 1.0)):
                    fx = leaf_x + (0.0 if sgn < 0 else DOOR_LEAF_THICKNESS)
                    px = fx - proud if sgn < 0 else fx
                    for pi, (pz0, pz1) in enumerate(panels):
                        if pz1 - pz0 <= 0.2:
                            continue
                        ya, yb = y0 + FRAME_WIDTH + inset, y0 + FRAME_WIDTH + leaf_w - inset
                        make_box(f"{name_base}_panel_{fi}_{pi}_a", px, ya, pz0,
                                 proud, rail, pz1 - pz0, collection, leaf_mat)
                        make_box(f"{name_base}_panel_{fi}_{pi}_b", px, yb - rail, pz0,
                                 proud, rail, pz1 - pz0, collection, leaf_mat)
                        make_box(f"{name_base}_panel_{fi}_{pi}_c", px, ya + rail, pz0,
                                 proud, panel_w - rail * 2, rail, collection, leaf_mat)
                        make_box(f"{name_base}_panel_{fi}_{pi}_d", px, ya + rail, pz1 - rail,
                                 proud, panel_w - rail * 2, rail, collection, leaf_mat)
            else:
                for fi, sgn in enumerate((-1.0, 1.0)):
                    fy = leaf_y + (0.0 if sgn < 0 else DOOR_LEAF_THICKNESS)
                    py = fy - proud if sgn < 0 else fy
                    for pi, (pz0, pz1) in enumerate(panels):
                        if pz1 - pz0 <= 0.2:
                            continue
                        xa, xb = x0 + FRAME_WIDTH + inset, x0 + FRAME_WIDTH + leaf_w - inset
                        make_box(f"{name_base}_panel_{fi}_{pi}_a", xa, py, pz0,
                                 rail, proud, pz1 - pz0, collection, leaf_mat)
                        make_box(f"{name_base}_panel_{fi}_{pi}_b", xb - rail, py, pz0,
                                 rail, proud, pz1 - pz0, collection, leaf_mat)
                        make_box(f"{name_base}_panel_{fi}_{pi}_c", xa + rail, py, pz0,
                                 panel_w - rail * 2, proud, rail, collection, leaf_mat)
                        make_box(f"{name_base}_panel_{fi}_{pi}_d", xa + rail, py, pz1 - rail,
                                 panel_w - rail * 2, proud, rail, collection, leaf_mat)
