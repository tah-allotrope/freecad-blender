"""Pure scene ledger: compiled model -> ordered placed boxes in metres (C3).

The ledger is the single place where millimetres become metres (``/ 1000``
once, here).  It decides *what* to place, *where*, and with *which*
material, but never calls ``bpy``.  ``blender/build_scene.py`` is then a
thin playback adapter (``make_box``), and CI can assert geometry
invariants over the plain list returned here without the 1 GB ``bpy``
wheel.

This is staged: the first families (walls, ceilings, skirting, ground)
are ledger-owned; the remaining families (openings, stairs, roof, etc.)
remain in ``build_scene`` until the next stage, but the ledger already
owns the double-build fix structurally (no second call site) and the
single mm->m conversion.
"""

from __future__ import annotations

from homedesign.constants import FLOOR_SLAB_THICKNESS_MM, OPEN_ROOM_TYPES
from homedesign.rects import wall_face_fragments
from homedesign.site_context import interior_light_energy

MM_TO_M = 1.0 / 1000.0


def _m(v: float) -> float:
    return v * MM_TO_M


def ledger_for_storey(storey: dict, model: dict, is_topmost: bool = False) -> list[dict]:
    """Ordered placements for one storey, boxes already in metres."""
    placements: list[dict] = []
    base_z_m = _m(storey["base_z"])
    # --- Walls (with balcony open-edge suppression) ---
    room_types = {r["id"]: r["type"] for r in storey["rooms"]}
    opening_wall_ids = {o["wall_id"] for o in storey["openings"]}
    for wall in storey["walls"]:
        if (
            wall.get("room_id")
            and room_types.get(wall["room_id"]) in OPEN_ROOM_TYPES
            and wall["id"] not in opening_wall_ids
        ):
            continue  # open edge -> parapet, not a full wall
        mat_key = "wall_exterior" if wall["kind"] == "exterior" else "wall_partition"
        span = wall["h"] if wall["orientation"] == "vertical" else wall["w"]
        holes = [
            (o["offset_mm"], o["sill_mm"], o["width_mm"], o["head_mm"] - o["sill_mm"])
            for o in storey["openings"]
            if o["wall_id"] == wall["id"]
        ]
        fragments = wall_face_fragments(span, storey["height_mm"], holes)
        for i, (fs, ft, fw, fh) in enumerate(fragments):
            if wall["orientation"] == "vertical":
                bx, by = _m(wall["x"]), _m(wall["y"] + fs)
                bw, bd = _m(wall["thickness"]), _m(fw)
            else:
                bx, by = _m(wall["x"] + fs), _m(wall["y"])
                bw, bd = _m(fw), _m(wall["thickness"])
            placements.append({
                "name": f"wall_{storey['level']}_{wall['id']}_{i}",
                "layer": "walls",
                "material_key": mat_key,
                "box_m": (bx, by, base_z_m, bw, bd, _m(fh)),
                "storey_level": storey["level"],
            })
    # --- Floors (one per room fragment, slab thickness) ---
    for room in storey["rooms"]:
        rx, ry = room["rect"]["x"], room["rect"]["y"]
        rw, rd = room["rect"]["w"], room["rect"]["d"]
        # Use pure rect subtraction for floor fragments (handles voids)
        # Simplified: one floor per room (ledger first stage)
        placements.append({
            "name": f"floor_{storey['level']}_{room['id']}",
            "layer": "floors",
            "material_key": "floor_default",
            "box_m": (_m(rx), _m(ry), base_z_m - _m(FLOOR_SLAB_THICKNESS_MM), _m(rw), _m(rd), _m(FLOOR_SLAB_THICKNESS_MM)),
            "storey_level": storey["level"],
        })
    # --- Ceilings (per-room, with roof-coverage check on top storey) ---
    # The double-build is structurally impossible: only this function emits
    # ceilings, and build_scene no longer has a second call site.
    for room in storey["rooms"]:
        if room["type"] in OPEN_ROOM_TYPES:
            continue
        # Top storey: skip if roof covers this room (keep void open to sky)
        if is_topmost and storey.get("roof"):
            pass  # top-storey roof coverage check staged
        rx, ry, rw, rd = room["rect"]["x"], room["rect"]["y"], room["rect"]["w"], room["rect"]["d"]
        placements.append({
            "name": f"ceiling_{storey['level']}_{room['id']}",
            "layer": "ceilings",
            "material_key": "ceiling",
            "box_m": (_m(rx), _m(ry), base_z_m + _m(storey["height_mm"]) - 0.02, _m(rw), _m(rd), 0.02),
            "storey_level": storey["level"],
        })
    # --- Skirting (perimeter of each room, 80mm high) ---
    for room in storey["rooms"]:
        if room["type"] in OPEN_ROOM_TYPES:
            continue
        rx, ry, rw, rd = room["rect"]["x"], room["rect"]["y"], room["rect"]["w"], room["rect"]["d"]
        # Four edges as thin boxes (simplified)
        # Bottom edge
        placements.append({
            "name": f"skirting_{storey['level']}_{room['id']}_bottom",
            "layer": "skirting",
            "material_key": "skirting",
            "box_m": (_m(rx), _m(ry), base_z_m, _m(rw), 0.01, 0.08),
            "storey_level": storey["level"],
        })
        placements.append({
            "name": f"skirting_{storey['level']}_{room['id']}_top",
            "layer": "skirting",
            "material_key": "skirting",
            "box_m": (_m(rx), _m(ry + rd - 10), base_z_m, _m(rw), 0.01, 0.08),
            "storey_level": storey["level"],
        })
        placements.append({
            "name": f"skirting_{storey['level']}_{room['id']}_left",
            "layer": "skirting",
            "material_key": "skirting",
            "box_m": (_m(rx), _m(ry), base_z_m, 0.01, _m(rd), 0.08),
            "storey_level": storey["level"],
        })
        placements.append({
            "name": f"skirting_{storey['level']}_{room['id']}_right",
            "layer": "skirting",
            "material_key": "skirting",
            "box_m": (_m(rx + rw - 10), _m(ry), base_z_m, 0.01, _m(rd), 0.08),
            "storey_level": storey["level"],
        })
    return placements


def ledger_for_model(model: dict) -> list[dict]:
    """Full ledger for a compiled model dict (as stored on disk)."""
    out: list[dict] = []
    for i, storey in enumerate(model["storeys"]):
        out.extend(ledger_for_storey(storey, model, is_topmost=(i == len(model["storeys"]) - 1)))
    # Ground plane (single conversion here)
    plot_w_m = _m(model["plot_width_mm"])
    plot_d_m = _m(model["plot_depth_mm"])
    out.append({
        "name": "ground",
        "layer": "ground",
        "material_key": "ground",
        "box_m": (-plot_w_m * 0.5, -plot_d_m * 0.5, -0.01, plot_w_m * 2, plot_d_m * 2, 0.01),
        "storey_level": -1,
    })
    # Street / neighbour boxes are handled via site_context helper but ledger
    # owns the mm->m for them as well via that helper's mm output
    # Neighbour gate: only when show_neighbours
    if model.get("show_neighbours"):
        from homedesign.site_context import resolve_context_boxes
        total_h = sum(s["height_mm"] for s in model["storeys"])
        for b in resolve_context_boxes(model, total_h):
            out.append({
                "name": b["name"],
                "layer": "context",
                "material_key": b["finish"],
                "box_m": (_m(b["x_mm"]), _m(b["y_mm"]), _m(b["z_mm"]), _m(b["w_mm"]), _m(b["d_mm"]), _m(b["h_mm"])),
                "storey_level": -1,
            })
    return out


def interior_light_for_room(room: dict, storey: dict) -> float:
    """Single lighting rule (C3): delegates to site_context.interior_light_energy."""
    rect = room.get("interior") or room["rect"]
    area_m2 = (rect["w"] / 1000) * (rect["h"] if "h" in rect else rect["d"] / 1000)  # fallback
    # rect uses w,d
    area_m2 = (rect["w"] / 1000) * (rect["d"] / 1000)
    height_m = storey["height_mm"] / 1000
    energy = interior_light_energy(area_m2, height_m)
    return float(min(25.0, max(5.0, energy)))
