"""Balcony parapet band geometry (RF TASK-03-04). Pure Python, no bpy.

A parapet is drawn on the drawing set and built in the scene from the same
band list, so the slat pattern the contractor sees on `MẶT ĐỨNG CHÍNH` and the
slats in the render can never drift apart.

Bands are returned in millimetres, positioned inside the room rect with their
outer face on the rect edge (the same convention `railings.build_parapet` has
always used), plus a `z_off_mm` giving the band's base above the balcony floor.
"""
from __future__ import annotations

from .constants import PARAPET_HEIGHT_MM, PARAPET_THICKNESS_MM

PATTERNS = ("solid", "slatted")

# A slatted parapet is a stack of horizontal slats with an open gap between
# them — the pattern drawn on the contractor's front elevation. 100 mm slats on
# a 160 mm pitch put seven slats in the 1100 mm parapet with the top slat
# finishing at 1060 mm, so the handrail line still reads at the drawn height.
SLAT_HEIGHT_MM = 100.0
SLAT_GAP_MM = 60.0


def slat_offsets(height_mm: float = PARAPET_HEIGHT_MM) -> list[float]:
    """Base offsets of every slat in a parapet `height_mm` tall."""
    pitch = SLAT_HEIGHT_MM + SLAT_GAP_MM
    offsets = []
    z = 0.0
    while z + SLAT_HEIGHT_MM <= height_mm:
        offsets.append(z)
        z += pitch
    return offsets


def parapet_bands(
    x_mm: float,
    y_mm: float,
    w_mm: float,
    d_mm: float,
    sides,
    pattern: str = "solid",
    height_mm: float = PARAPET_HEIGHT_MM,
    thickness_mm: float = PARAPET_THICKNESS_MM,
) -> list[dict]:
    """Every box making up the parapet on `sides` of a balcony rect.

    Each band carries absolute `x_mm`/`y_mm` plan position, its `w_mm`/`d_mm`
    footprint, a `z_off_mm` base above the balcony floor and its `h_mm` height.
    A `solid` parapet yields one band per side; a `slatted` one yields a band
    per slat per side.
    """
    if pattern not in PATTERNS:
        raise ValueError(f"unknown parapet pattern {pattern!r}; expected one of {PATTERNS}")

    footprints = []
    if "north" in sides:
        footprints.append(("n", x_mm, y_mm, w_mm, thickness_mm))
    if "south" in sides:
        footprints.append(("s", x_mm, y_mm + d_mm - thickness_mm, w_mm, thickness_mm))
    if "west" in sides:
        footprints.append(("w", x_mm, y_mm, thickness_mm, d_mm))
    if "east" in sides:
        footprints.append(("e", x_mm + w_mm - thickness_mm, y_mm, thickness_mm, d_mm))

    offsets = [0.0] if pattern == "solid" else slat_offsets(height_mm)
    band_h = height_mm if pattern == "solid" else SLAT_HEIGHT_MM

    bands: list[dict] = []
    for side, bx, by, bw, bd in footprints:
        for i, z_off in enumerate(offsets):
            bands.append({
                "side": side,
                "index": i,
                "x_mm": bx,
                "y_mm": by,
                "w_mm": bw,
                "d_mm": bd,
                "z_off_mm": z_off,
                "h_mm": band_h,
            })
    return bands


def elevation_bands(length_mm: float, pattern: str = "solid",
                    height_mm: float = PARAPET_HEIGHT_MM) -> list[dict]:
    """The same pattern as a list of `(z_off_mm, h_mm)` bands for a 2D elevation."""
    if pattern not in PATTERNS:
        raise ValueError(f"unknown parapet pattern {pattern!r}; expected one of {PATTERNS}")
    if pattern == "solid":
        return [{"z_off_mm": 0.0, "h_mm": height_mm, "w_mm": length_mm}]
    return [{"z_off_mm": z, "h_mm": SLAT_HEIGHT_MM, "w_mm": length_mm}
            for z in slat_offsets(height_mm)]
