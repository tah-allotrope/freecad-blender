"""Shared magic dimensions and room-type sets, in millimetres.

Pure data, no imports. The Blender side derives its metre values from these by
dividing by 1000 at the point of use, preserving the single-conversion-point
rule (AGENTS.md): millimetres everywhere on the pure-Python side, metres only
inside `src/homedesign/blender/`.
"""
from __future__ import annotations

PARAPET_HEIGHT_MM = 1100.0
PARAPET_THICKNESS_MM = 100.0
BALUSTRADE_HEIGHT_MM = 900.0
RAIL_THICKNESS_MM = 60.0
FLOOR_SLAB_THICKNESS_MM = 50.0
FLAT_ROOF_THICKNESS_MM = 200.0
SLAB_BAND_MM = 200.0

# Room types whose plan footprint is open to the sky on unshared edges (they
# get parapets, not full-height walls, on those edges).
OPEN_ROOM_TYPES = {"balcony", "terrace", "courtyard"}

# Room types that require a window for the daylight check.
HABITABLE_TYPES = {"bedroom", "living", "kitchen", "dining", "office"}

# Room types that are wet-service rooms (floor finish grouping).
WET_ROOM_TYPES = {"bathroom", "wc"}
