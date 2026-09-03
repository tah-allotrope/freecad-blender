"""Edge protection for balconies and stair flights. Runs inside Blender.

All geometry is a `make_box` composition (CON-004): parapets are 1100mm high
panels inside the balcony rect (their outer face on the rect edge), and stair
balustrades are per-tread rail panels that follow the flight slope.

The parapet band list comes from `homedesign.parapet`, the same pure module the
elevation writer draws from, so a `slatted` parapet cannot appear in one output
and not the other.
"""
from homedesign.constants import (
    BALUSTRADE_HEIGHT_MM,
    PARAPET_HEIGHT_MM,
    PARAPET_THICKNESS_MM,
    RAIL_THICKNESS_MM,
)
from homedesign.parapet import parapet_bands

from .geom import make_box

PARAPET_HEIGHT_M = PARAPET_HEIGHT_MM / 1000
PARAPET_THICKNESS_M = PARAPET_THICKNESS_MM / 1000
BALUSTRADE_HEIGHT_M = BALUSTRADE_HEIGHT_MM / 1000
RAIL_THICKNESS_M = RAIL_THICKNESS_MM / 1000


def build_parapet(rect_mm, top_z_m, sides, height_m, thickness_m, collection, material,
                  pattern: str = "solid"):
    """Parapet panels along the requested `sides` of a balcony rect (mm).

    Panels sit inside the room rect, their outer face on the rect edge, so they
    never project past the plot regardless of the wall-alignment setting. With
    `pattern="slatted"` each side becomes a stack of horizontal slats separated
    by open gaps, matching the pattern drawn on the front elevation.
    """
    x, y, w, d = rect_mm
    bands = parapet_bands(
        x, y, w, d, sides, pattern,
        height_mm=height_m * 1000, thickness_mm=thickness_m * 1000,
    )
    objs = []
    for band in bands:
        name = f"parapet_{band['side']}" if pattern == "solid" else f"parapet_{band['side']}_{band['index']}"
        objs.append(make_box(
            name,
            band["x_mm"] / 1000, band["y_mm"] / 1000, top_z_m + band["z_off_mm"] / 1000,
            band["w_mm"] / 1000, band["d_mm"] / 1000, band["h_mm"] / 1000,
            collection, material,
        ))
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
