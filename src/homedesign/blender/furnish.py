"""Furnish rooms: pure placement math (placement.py) executed as bpy objects
(procedural_furniture.py). No asset library exists yet -- procedural blocks
are the sole furniture source, and the pipeline never fails without one.
"""
import sys
from pathlib import Path

_SRC = Path(__file__).resolve().parent.parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from homedesign.placement import plan_room  # noqa: E402
from . import procedural_furniture as pf


def furnish_storey(storey_mm, style, collection):
    for room in storey_mm["rooms"]:
        w_m = room["rect"]["w"] / 1000
        d_m = room["rect"]["d"] / 1000
        items = plan_room(room["type"], w_m, d_m)
        room_x = room["rect"]["x"] / 1000
        room_y = room["rect"]["y"] / 1000
        base_z = storey_mm["base_z"] / 1000
        for item in items:
            pf.build_item(item, room_x, room_y, base_z, style, collection)
