"""Edge protection for balconies and stair flights. Runs inside Blender.

All geometry is a `make_box` composition (CON-004): parapets are 1100mm high
panels inside the balcony rect (their outer face on the rect edge), and stair
balustrades are per-tread rail panels that follow the flight slope.
"""
from .geom import make_box

PARAPET_HEIGHT_M = 1.1
PARAPET_THICKNESS_M = 0.1
BALUSTRADE_HEIGHT_M = 0.9
RAIL_THICKNESS_M = 0.06


def build_parapet(rect_mm, top_z_m, sides, height_m, thickness_m, collection, material):
    """Parapet panels along the requested `sides` of a balcony rect (mm).

    Panels sit inside the room rect, their outer face on the rect edge, so they
    never project past the plot regardless of the wall-alignment setting.
    """
    x, y, w, d = rect_mm
    xm, ym, wm, dm = x / 1000, y / 1000, w / 1000, d / 1000
    objs = []
    if "north" in sides:
        objs.append(make_box("parapet_n", xm, ym, top_z_m, wm, thickness_m, height_m, collection, material))
    if "south" in sides:
        objs.append(make_box("parapet_s", xm, ym + dm - thickness_m, top_z_m, wm, thickness_m, height_m, collection, material))
    if "west" in sides:
        objs.append(make_box("parapet_w", xm, ym, top_z_m, thickness_m, dm, height_m, collection, material))
    if "east" in sides:
        objs.append(make_box("parapet_e", xm + wm - thickness_m, ym, top_z_m, thickness_m, dm, height_m, collection, material))
    return objs


def build_balustrade(treads, open_side, height_m, collection, material):
    """Rail panels along the open long side of a stair flight.

    `treads` carries the flight's tread rects with absolute `z` in millimetres;
    one panel per tread follows the slope (a flight of n risers has n-1 treads,
    so the count here never assumes they are equal). The open side is the long
    edge not coincident with the stairwell room's rect edge.
    """
    objs = []
    for i, t in enumerate(treads):
        x, y, w, d = t["x"] / 1000, t["y"] / 1000, t["w"] / 1000, t["d"] / 1000
        z = t["z"] / 1000
        if open_side == "north":
            objs.append(make_box(f"rail_{i}", x, y, z, w, RAIL_THICKNESS_M, height_m, collection, material))
        elif open_side == "south":
            objs.append(make_box(f"rail_{i}", x, y + d - RAIL_THICKNESS_M, z, w, RAIL_THICKNESS_M, height_m, collection, material))
        elif open_side == "west":
            objs.append(make_box(f"rail_{i}", x, y, z, RAIL_THICKNESS_M, d, height_m, collection, material))
        else:  # east
            objs.append(make_box(f"rail_{i}", x + w - RAIL_THICKNESS_M, y, z, RAIL_THICKNESS_M, d, height_m, collection, material))
    return objs
