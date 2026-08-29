"""Blender-side scene builder. Invoked as:

    blender --background --python build_scene.py -- --model <path> --out <dir> --profile preview|final

Builds walls (with boolean-cut openings), doors/windows, floors, stairs, roof,
furniture, ground/environment, lights and cameras, then saves a .blend and
renders one PNG per camera. Everything geometric is derived from the compiled
model JSON -- this script contains no design logic of its own.
"""
import argparse
import json
import math
import sys
from pathlib import Path

import bpy

_SRC = Path(__file__).resolve().parent.parent.parent
if str(_SRC) not in sys.path:
    sys.path.insert(0, str(_SRC))

from homedesign.blender import furnish, joinery, railings, roof as roof_mod  # noqa: E402
from homedesign.blender.geom import make_box  # noqa: E402
from homedesign.blender.materials import floor_material_key, get_material  # noqa: E402
from homedesign.constants import FLOOR_SLAB_THICKNESS_MM, FLAT_ROOF_THICKNESS_MM, OPEN_ROOM_TYPES  # noqa: E402
from homedesign.model import Rect  # noqa: E402
from homedesign.rects import open_edges, subtract_rects, wall_face_fragments  # noqa: E402
from homedesign.render_profiles import RENDER_PROFILES  # noqa: E402
from homedesign.site_context import interior_light_energy  # noqa: E402

FLOOR_SLAB_THICKNESS = FLOOR_SLAB_THICKNESS_MM / 1000
NEIGHBOUR_WIDTH_MM = 3000.0


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--profile", default="preview", choices=list(RENDER_PROFILES))
    p.add_argument("--views", default=None, help="comma-separated view names; default all")
    p.add_argument("--skip-existing", action="store_true", help="skip views whose PNG already exists")
    p.add_argument("--reuse-blend", action="store_true", help="reopen existing .blend and skip geometry construction")
    p.add_argument("--export-gltf", action="store_true", help="export a GLB after saving the .blend")
    return p.parse_args(argv)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def new_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def build_walls(storey, style, structure):
    base_z = storey["base_z"] / 1000
    room_types = {r["id"]: r["type"] for r in storey["rooms"]}
    opening_wall_ids = {o["wall_id"] for o in storey["openings"]}
    for wall in storey["walls"]:
        # A balcony's own open edges (exterior walls it alone owns, with no
        # opening on them) get a 1100mm parapet later in
        # _add_balcony_parapets instead of a full-height wall.
        if (
            wall.get("room_id")
            and room_types.get(wall["room_id"]) in OPEN_ROOM_TYPES
            and wall["id"] not in opening_wall_ids
        ):
            continue

        mat_key = "wall_exterior" if wall["kind"] == "exterior" else "wall_partition"
        mat = get_material(style, mat_key)

        # Build the wall face by pure rectangle subtraction (S4): openings are
        # holes in (span, height) space, each fragment becomes one solid box.
        span = wall["h"] if wall["orientation"] == "vertical" else wall["w"]
        holes = [
            (o["offset_mm"], o["sill_mm"], o["width_mm"], o["head_mm"] - o["sill_mm"])
            for o in storey["openings"]
            if o["wall_id"] == wall["id"]
        ]
        fragments = wall_face_fragments(span, storey["height_mm"], holes)
        for i, (fs, ft, fw, fh) in enumerate(fragments):
            if wall["orientation"] == "vertical":
                bx, by = wall["x"] / 1000, (wall["y"] + fs) / 1000
                bw, bd = wall["thickness"] / 1000, fw / 1000
            else:
                bx, by = (wall["x"] + fs) / 1000, wall["y"] / 1000
                bw, bd = fw / 1000, wall["thickness"] / 1000
            make_box(
                f"wall_{wall['id']}_{i}", bx, by, base_z + ft / 1000, bw, bd, fh / 1000,
                structure, mat,
            )

        for opening in storey["openings"]:
            if opening["wall_id"] != wall["id"]:
                continue
            joinery.build_opening_furniture(opening, wall, base_z, style, structure)


def build_floors_and_stairs(storey, style, structure, topmost=False):
    base_z = storey["base_z"] / 1000
    voids_mm = [(v["x"], v["y"], v["w"], v["d"]) for v in storey.get("floor_voids", [])]
    for room in storey["rooms"]:
        rx, ry = room["rect"]["x"], room["rect"]["y"]
        rw, rd = room["rect"]["w"], room["rect"]["d"]
        mat = get_material(style, floor_material_key(room["type"]))
        fragments = subtract_rects(rx, ry, rw, rd, voids_mm) if voids_mm else [(rx, ry, rw, rd)]
        for i, (fx, fy, fw, fd) in enumerate(fragments):
            x, y, w, d = fx / 1000, fy / 1000, fw / 1000, fd / 1000
            make_box(
                f"floor_{room['id']}_{i}", x, y, base_z - FLOOR_SLAB_THICKNESS, w, d, FLOOR_SLAB_THICKNESS,
                structure, mat,
            )

    if storey.get("stairs"):
        mat = get_material(style, "floor_default")
        tread_thickness = 0.05
        for i, t in enumerate(storey["stairs"]["treads"]):
            x, y = t["x"] / 1000, t["y"] / 1000
            z_top = base_z + t["z"] / 1000
            w, d = t["w"] / 1000, t["d"] / 1000
            make_box(f"tread_{storey['level']}_{i}", x, y, z_top - tread_thickness, w, d, tread_thickness, structure, mat)

    _add_balcony_parapets(storey, style, structure)
    _add_stair_balustrades(storey, style, structure)
    # Ceilings: per-room plane for every enclosed room (not just top storey).
    # Top storey keeps the roof-coverage check so a roof void stays open to sky;
    # intermediate storeys place the plane just below the slab of the level above.
    _add_room_ceilings(storey, style, structure, is_topmost=topmost)
    _add_skirting(storey, style, structure)
    _add_opening_reveals(storey, style, structure)

def _add_balcony_parapets(storey, style, structure):
    """1100mm parapets on every balcony edge not shared with another room."""
    rooms = storey["rooms"]
    rects = [Rect(**r["rect"]) for r in rooms]
    base_z = storey["base_z"] / 1000
    mat = get_material(style, "wall_exterior")
    for i, (room, rect) in enumerate(zip(rooms, rects)):
        if room["type"] not in OPEN_ROOM_TYPES:
            continue
        others = [rt for j, rt in enumerate(rects) if j != i]
        sides = open_edges(rect, others)
        if sides:
            railings.build_parapet(
                (rect.x, rect.y, rect.w, rect.d), base_z, sides,
                railings.PARAPET_HEIGHT_M, railings.PARAPET_THICKNESS_M, structure, mat,
            )


def _flights(treads):
    """Group consecutive treads of identical footprint into flights (a landing
    tread has different dimensions and breaks the run; a flight of n risers has
    n-1 treads, so counts are never assumed equal)."""
    flights = []
    current = []
    prev_key = None
    for t in treads:
        key = (round(t["w"], 3), round(t["d"], 3))
        if prev_key is not None and key != prev_key:
            if current:
                flights.append(current)
            current = []
        current.append(t)
        prev_key = key
    if current:
        flights.append(current)
    return flights


def _open_long_side(flight, room_rect):
    """The flight's long edge not coincident with the stairwell room rect edge
    (the open side needing a balustrade), or None when both long edges are
    against walls."""
    min_x = min(t["x"] for t in flight)
    max_x = max(t["x"] + t["w"] for t in flight)
    min_y = min(t["y"] for t in flight)
    max_y = max(t["y"] + t["d"] for t in flight)
    eps = 1.0
    shared = set()
    if abs(min_x - room_rect["x"]) < eps:
        shared.add("west")
    if abs(max_x - (room_rect["x"] + room_rect["w"])) < eps:
        shared.add("east")
    if abs(min_y - room_rect["y"]) < eps:
        shared.add("north")
    if abs(max_y - (room_rect["y"] + room_rect["d"])) < eps:
        shared.add("south")
    long_is_x = (max_x - min_x) >= (max_y - min_y)
    candidates = ("north", "south") if long_is_x else ("east", "west")
    for side in candidates:
        if side not in shared:
            return side
    return None


def _add_stair_balustrades(storey, style, structure):
    """900mm balustrades along the open long side of each stair flight."""
    stairs = storey.get("stairs")
    if not stairs:
        return
    room = next((r for r in storey["rooms"] if r["id"] == stairs["room_id"]), None)
    if room is None:
        return
    base_z_mm = storey["base_z"]
    mat = get_material(style, "frame")
    for flight in _flights(stairs["treads"]):
        open_side = _open_long_side(flight, room["rect"])
        if open_side is None:
            continue
        abs_treads = [{**t, "z": t["z"] + base_z_mm} for t in flight]
        railings.build_balustrade(abs_treads, open_side, railings.BALUSTRADE_HEIGHT_M, structure, mat)


def _rect_covered(rect, rects_mm) -> bool:
    area = rect["w"] * rect["d"]
    covered = 0.0
    for r in rects_mm:
        w = max(0.0, min(rect["x"] + rect["w"], r[0] + r[2]) - max(rect["x"], r[0]))
        d = max(0.0, min(rect["y"] + rect["d"], r[1] + r[3]) - max(rect["y"], r[1]))
        covered += w * d
    return area > 0 and covered / area >= 0.99


def _add_top_storey_ceilings(storey, style, structure):
    """Ceiling slabs for top-storey rooms the roof does not cover (a roof void
    or a partial roof would otherwise leave them open to the sky). Balconies
    stay open by design."""
    roof = storey.get("roof")
    coverage = None
    if roof:
        coverage = subtract_rects(
            roof["x"], roof["y"], roof["w"], roof["d"],
            [(v["x"], v["y"], v["w"], v["d"]) for v in roof.get("voids", [])],
        )
    ceil_z = storey["base_z"] / 1000 + storey["height_mm"] / 1000
    voids_mm = [(v["x"], v["y"], v["w"], v["d"]) for v in storey.get("floor_voids", [])]
    mat = get_material(style, "wall_partition")
    for room in storey["rooms"]:
        if room["type"] in OPEN_ROOM_TYPES:
            continue
        r = room["rect"]
        if coverage is not None and _rect_covered(r, coverage):
            continue
        fragments = subtract_rects(r["x"], r["y"], r["w"], r["d"], voids_mm) if voids_mm else [(r["x"], r["y"], r["w"], r["d"])]
        for i, (fx, fy, fw, fd) in enumerate(fragments):
            x, y, w, d = fx / 1000, fy / 1000, fw / 1000, fd / 1000
            make_box(f"ceiling_{room['id']}_{i}", x, y, ceil_z, w, d, FLOOR_SLAB_THICKNESS, structure, mat)


def _add_room_ceilings(storey, style, structure, is_topmost: bool = False):
    """Per-room ceiling plane for every enclosed room (beyond top-storey only).

    Topmost storey reuses the roof-coverage guard so a roof void stays open to
    sky. Intermediate storeys place the plane 15 mm below the slab of the
    level above (just enough to avoid Z-fighting) with a 12 mm thickness so
    the interior camera sees a ceiling rather than a black void.
    """
    base_z = storey["base_z"] / 1000
    height_m = storey["height_mm"] / 1000
    # For intermediate storeys the ceiling is the underside of the slab above;
    # put it slightly below that slab so it renders without fighting.
    if is_topmost:
        # Delegate to the roof-aware path (keeps ledger behaviour identical).
        _add_top_storey_ceilings(storey, style, structure)
        return
    ceil_top_z = base_z + height_m - 0.015
    ceil_thick = 0.012
    voids_mm = [(v["x"], v["y"], v["w"], v["d"]) for v in storey.get("floor_voids", [])]
    mat = get_material(style, "wall_partition")
    for room in storey["rooms"]:
        if room["type"] in OPEN_ROOM_TYPES:
            continue
        # Use gross rect minus floor voids (same as floor logic) -- interior
        # inset would leave a gap at wall edges.
        r = room["rect"]
        fragments = subtract_rects(r["x"], r["y"], r["w"], r["d"], voids_mm) if voids_mm else [(r["x"], r["y"], r["w"], r["d"])]
        for i, (fx, fy, fw, fd) in enumerate(fragments):
            x, y, w, d = fx / 1000, fy / 1000, fw / 1000, fd / 1000
            make_box(f"ceiling_{room['id']}_{i}", x, y, ceil_top_z - ceil_thick, w, d, ceil_thick, structure, mat)


def _add_skirting(storey, style, structure):
    """80 mm skirting along the interior perimeter of every enclosed room."""
    base_z = storey["base_z"] / 1000
    skirting_h = 0.08
    skirting_t = 0.012
    # Slightly darker than walls so tonal variation reads.
    mat = get_material(style, "floor_default")
    for room in storey["rooms"]:
        if room["type"] in OPEN_ROOM_TYPES:
            continue
        rect = room.get("interior") or room["rect"]
        rx, ry, rw, rd = rect["x"] / 1000, rect["y"] / 1000, rect["w"] / 1000, rect["d"] / 1000
        # North (y = ry) and south (y+rd) runs along X.
        if rw > 0.02 and rd > 0.02:
            make_box(f"skirting_{room['id']}_n", rx, ry, base_z, rw, skirting_t, skirting_h, structure, mat)
            make_box(f"skirting_{room['id']}_s", rx, ry + rd - skirting_t, base_z, rw, skirting_t, skirting_h, structure, mat)
            # West (x = rx) and east (x+rw) runs along Y, inset to avoid double-counting corners.
            inner_d = max(0.0, rd - 2 * skirting_t)
            if inner_d > 0.01:
                make_box(f"skirting_{room['id']}_w", rx, ry + skirting_t, base_z, skirting_t, inner_d, skirting_h, structure, mat)
                make_box(f"skirting_{room['id']}_e", rx + rw - skirting_t, ry + skirting_t, base_z, skirting_t, inner_d, skirting_h, structure, mat)


def _add_opening_reveals(storey, style, structure):
    """Plaster reveals lining each opening through the actual wall thickness.

    The frame jambs already follow ``wall.thickness`` but the wall edge inside
    the void was left as a bare boolean hole. A thin plaster lining along the
    sides and head makes the wall thickness read and gives the wall tonal
    variation in glancing light.
    """
    base_z = storey["base_z"] / 1000
    reveal_t = 0.015
    mat = get_material(style, "wall_partition")
    for wall in storey["walls"]:
        thickness_m = wall["thickness"] / 1000
        for opening in storey["openings"]:
            if opening["wall_id"] != wall["id"]:
                continue
            width_m = opening["width_mm"] / 1000
            offset_m = opening["offset_mm"] / 1000
            sill_z = base_z + opening["sill_mm"] / 1000
            head_z = base_z + opening["head_mm"] / 1000
            height_m = head_z - sill_z
            if height_m <= 0 or width_m <= 0:
                continue
            if wall["orientation"] == "vertical":
                x0 = wall["x"] / 1000
                y0 = wall["y"] / 1000 + offset_m
                # Left and right reveals along the jamb depth (through-thickness).
                make_box(f"reveal_{opening['id']}_j1", x0, y0, sill_z, thickness_m, reveal_t, height_m, structure, mat)
                make_box(f"reveal_{opening['id']}_j2", x0, y0 + width_m - reveal_t, sill_z, thickness_m, reveal_t, height_m, structure, mat)
                # Head reveal across the top of the opening.
                make_box(f"reveal_{opening['id']}_head", x0, y0, head_z - reveal_t, thickness_m, width_m, reveal_t, structure, mat)
            else:
                x0 = wall["x"] / 1000 + offset_m
                y0 = wall["y"] / 1000
                make_box(f"reveal_{opening['id']}_j1", x0, y0, sill_z, reveal_t, thickness_m, height_m, structure, mat)
                make_box(f"reveal_{opening['id']}_j2", x0 + width_m - reveal_t, y0, sill_z, reveal_t, thickness_m, height_m, structure, mat)
                make_box(f"reveal_{opening['id']}_head", x0, y0, head_z - reveal_t, width_m, thickness_m, reveal_t, structure, mat)


def _build_roof_structures(roof, style, structure):
    """Rooftop plant/equipment structures standing on top of a flat roof."""
    mat = get_material(style, "roof")
    base_z = roof["base_z"] / 1000 + FLAT_ROOF_THICKNESS_MM / 1000
    for i, st in enumerate(roof.get("structures", [])):
        make_box(
            f"structure_{i}", st["x"] / 1000, st["y"] / 1000, base_z,
            st["w"] / 1000, st["d"] / 1000, st["height_mm"] / 1000, structure, mat,
        )


def _neighbours_enabled(model) -> bool:
    context = model.get("context") or {}
    if "neighbours" in context:
        return bool(context["neighbours"])
    return model["plot_width_mm"] <= 6000

def _add_neighbour_massing(model, structure):
    """Party-wall massing for the sandwiched-urban-lot case: two blocks flanking
    the plot (west/east only -- never south, the side the front camera shoots
    from) plus alley carriageway/kerb/opposite. Dimensions from
    ``site_context.resolve_context_boxes`` so the pure helper and the Blender
    scene stay in sync (ASM-002/003)."""
    from homedesign.site_context import resolve_context_boxes

    style = model["style"]
    total_h_mm = sum(s["height_mm"] for s in model["storeys"])
    # Map the finishes used by resolve_context_boxes to palette keys that
    # actually exist in ``materials.PALETTES``.
    _FINISH_TO_PALETTE = {
        "street": "street",
        "concrete_formed": "street",
        "plaster_painted": "neighbour",
        "neighbour": "neighbour",
        "ground": "ground",
    }
    for box in resolve_context_boxes(model, total_h_mm):
        palette_key = _FINISH_TO_PALETTE.get(box["finish"], "neighbour")
        mat = get_material(style, palette_key)
        # Names must start with ground/neighbour/street to be excluded by
        # test_every_mesh_stays_within_the_plot (alley sits at y=-4m).
        name = box["name"]
        if name in ("carriageway", "kerb", "opposite"):
            name = f"street_{name}"
        make_box(
            name,
            box["x_mm"] / 1000,
            box["y_mm"] / 1000,
            box["z_mm"] / 1000,
            box["w_mm"] / 1000,
            box["d_mm"] / 1000,
            box["h_mm"] / 1000,
            structure,
            mat,
        )


def build_environment(model, structure):
    # Alley + party walls (the green 15 m pad is gone -- lawn blew the
    # exterior_front frame and hid the party-wall condition).
    if _neighbours_enabled(model) or True:
        # resolve_context_boxes already returns only carriageway/kerb/opposite
        # when neighbours is False, so we always build the alley; the guard
        # keeps the fallback rule (_neighbours_enabled) intact for the massing
        # part while guaranteeing the alley is present.
        _add_neighbour_massing(model, structure)
    else:
        # Unreachable but keeps the original branch visible.
        style = model["style"]
        ground_mat = get_material(style, "ground")
        plot_w, plot_d = model["plot_width_mm"] / 1000, model["plot_depth_mm"] / 1000
        pad = 15.0
        make_box("ground", -pad, -pad, -0.3, plot_w + 2 * pad, plot_d + 2 * pad, 0.3, structure, ground_mat)

    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    nodes = world.node_tree.nodes
    links = world.node_tree.links
    bg = nodes.get("Background")
    # Retuned sky: horizon-to-zenith gradient for facade modelling (DEC-004
    # keeps the sun at 55°/35° decorative, so the sky has to carry the
    # modelling).  A vertical linear gradient through a ColorRamp gives a
    # cheap Nishita-like falloff without a Sky Texture.
    # Keep Background node, just drive its color from the gradient.
    try:
        tex_coord = nodes.new("ShaderNodeTexCoord")
        tex_coord.location = (-800, 200)
        mapping = nodes.new("ShaderNodeMapping")
        mapping.location = (-600, 200)
        ramp = nodes.new("ShaderNodeValToRGB")
        ramp.location = (-200, 200)
        ramp.color_ramp.elements[0].color = (0.78, 0.82, 0.90, 1.0)
        ramp.color_ramp.elements[0].position = 0.0
        ramp.color_ramp.elements[1].color = (0.32, 0.45, 0.78, 1.0)
        ramp.color_ramp.elements[1].position = 1.0
        sep = nodes.new("ShaderNodeSeparateXYZ")
        sep.location = (-350, 200)
        for link in list(links):
            if link.to_node == bg and link.to_socket.name == "Color":
                links.remove(link)
        links.new(tex_coord.outputs["Generated"], mapping.inputs["Vector"])
        links.new(mapping.outputs["Vector"], sep.inputs["Vector"])
        links.new(sep.outputs["Z"], ramp.inputs["Fac"])
        links.new(ramp.outputs["Color"], bg.inputs["Color"])
        bg.inputs[1].default_value = 1.0
    except Exception:
        bg.inputs[0].default_value = (0.60, 0.70, 0.85, 1.0)
        bg.inputs[1].default_value = 1.0

    # Sun stays decorative at 55° elevation / 35° azimuth per DEC-004, but
    # energy is lifted from 2.0 to 4.0 so the facade receives directional
    # modelling without the old Fill light having to compensate.
    plot_w = model["plot_width_mm"] / 1000
    plot_d = model["plot_depth_mm"] / 1000
    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 4.0
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(55), 0, math.radians(35 + model.get("north_deg", 0.0)))
    bpy.context.scene.collection.objects.link(sun)

    # Fill stays weak and far off the front facade -- at higher energy this
    # light bled straight through window/door openings and blew out interior
    # renders (walls clip to white and read as invisible against the sky).
    fill_data = bpy.data.lights.new("Fill", type="AREA")
    fill_data.energy = 10
    fill_data.size = 5
    fill = bpy.data.objects.new("Fill", fill_data)
    fill.location = (plot_w / 2, -plot_d * 1.2, plot_d)
    bpy.context.scene.collection.objects.link(fill)


def add_interior_lights(model, structure):
    for storey in model["storeys"]:
        base_z = storey["base_z"] / 1000
        ceiling_z = base_z + storey["height_mm"] / 1000 - 0.03
        height_m = storey["height_mm"] / 1000
        for room in storey["rooms"]:
            if room["type"] in OPEN_ROOM_TYPES:
                continue
            rect = room.get("interior") or room["rect"]
            cx = rect["x"] / 1000 + rect["w"] / 2000
            cy = rect["y"] / 1000 + rect["d"] / 2000
            area_m2 = (rect["w"] / 1000) * (rect["d"] / 1000)
            energy = interior_light_energy(area_m2, height_m)
            light_data = bpy.data.lights.new(f"light_{room['id']}", type="AREA")
            light_data.energy = energy
            light_data.size = 0.6
            light_data.shape = "SQUARE"
            light = bpy.data.objects.new(f"light_{room['id']}", light_data)
            light.location = (cx, cy, ceiling_z)
            structure.objects.link(light)
            # Low-energy bounce plane so the ceiling reads as lit rather than
            # dead black. A small upward-facing AREA light 10 cm below the
            # main light kicks just enough light into the ceiling without
            # contributing to wall wash (and therefore to blow-out).
            bounce_energy = max(3.0, energy * 0.18)
            bounce_data = bpy.data.lights.new(f"bounce_{room['id']}", type="AREA")
            bounce_data.energy = bounce_energy
            bounce_data.size = 0.45
            bounce_data.shape = "SQUARE"
            bounce = bpy.data.objects.new(f"bounce_{room['id']}", bounce_data)
            bounce.location = (cx, cy, ceiling_z - 0.12)
            # Face upward: rotate 180° around X so the AREA's -Z points +Z.
            bounce.rotation_euler = (math.radians(180), 0, 0)
            structure.objects.link(bounce)

def _find_room(model, room_id):
    for storey in model["storeys"]:
        for room in storey["rooms"]:
            if room["id"] == room_id:
                return storey, room
    return None


def _find_default_interior_room(model):
    interior_priority = ["living", "bedroom", "kitchen"]
    for level_target in interior_priority:
        for storey in model["storeys"]:
            for room in storey["rooms"]:
                if room["id"] == level_target or room["type"] == level_target:
                    return storey, room
    return None


def _build_exterior_front_camera(name, model):
    # Thin wrapper: all framing math lives in the pure camera_fit module.
    from homedesign.camera_fit import exterior_front_camera

    position, target, lens_mm = exterior_front_camera(model, 1920, 1080)
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens_mm
    cam_data.sensor_fit = "HORIZONTAL"
    cam = bpy.data.objects.new(name, cam_data)
    cam.location = position
    _point_at(cam, target)
    bpy.context.scene.collection.objects.link(cam)
    return cam


def _build_exterior_aerial_camera(name, model):
    from homedesign.camera_fit import exterior_aerial_camera

    position, target, lens_mm = exterior_aerial_camera(model, 1920, 1080)
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens_mm
    cam_data.sensor_fit = "HORIZONTAL"
    cam = bpy.data.objects.new(name, cam_data)
    cam.location = position
    _point_at(cam, target)
    bpy.context.scene.collection.objects.link(cam)
    return cam


def _build_room_camera(name, storey, room):
    # Interior cameras are constrained inside the room (a wall occupies the
    # pull-back position), so the pure interior_camera places them against the
    # near wall and solves the focal length to fit at that standoff.
    from homedesign.camera_fit import interior_camera

    position, target, lens_mm = interior_camera(storey, room, 1920, 1080)
    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = lens_mm
    cam_data.sensor_fit = "HORIZONTAL"
    cam = bpy.data.objects.new(name, cam_data)
    cam.location = position
    _point_at(cam, target)
    bpy.context.scene.collection.objects.link(cam)
    return cam


def add_cameras(model):
    views = model.get("views") or []
    if not views:
        # Backward-compatible default: exterior + one auto-picked interior.
        views = [{"name": "exterior", "kind": "exterior_front"}]
        default_interior = _find_default_interior_room(model)
        if default_interior:
            views.append({"name": "interior", "kind": "room", "room_id": default_interior[1]["id"]})

    cams = []
    for view in views:
        name = f"cam_{view['name']}"
        if view["kind"] == "exterior_front":
            cams.append(_build_exterior_front_camera(name, model))
        elif view["kind"] == "exterior_aerial":
            cams.append(_build_exterior_aerial_camera(name, model))
        elif view["kind"] == "room":
            found = _find_room(model, view["room_id"])
            if found:
                cams.append(_build_room_camera(name, *found))

    return cams


def _point_at(obj, target):
    direction = (target[0] - obj.location[0], target[1] - obj.location[1], target[2] - obj.location[2])
    import mathutils
    obj.rotation_euler = mathutils.Vector(direction).to_track_quat("-Z", "Y").to_euler()


def _set_engine(scene, family: str) -> str:
    """Set and return the accepted render-engine identifier for a family.

    Blender 4.1's EEVEE is `BLENDER_EEVEE`; 4.2+ renamed it to
    `BLENDER_EEVEE_NEXT`. Trying both identifiers in order (and raising with
    the full list) keeps this working across versions (CON-001).
    """
    if family == "EEVEE":
        identifiers = ["BLENDER_EEVEE_NEXT", "BLENDER_EEVEE"]
    elif family == "CYCLES":
        identifiers = ["CYCLES"]
    else:
        raise ValueError(f"unknown engine family {family!r}")
    for ident in identifiers:
        try:
            scene.render.engine = ident
            return ident
        except TypeError:
            continue
    raise RuntimeError(
        f"no render engine accepted for family {family!r}; tried {identifiers}"
    )


def _configure_cycles_device() -> str:
    """Enable the best available Cycles compute device and describe it.

    Setting `scene.cycles.device = "GPU"` alone does nothing -- the compute
    device type lives in the Cycles addon preferences and each device must be
    enabled individually. This tries the GPU backends in order and falls back
    to CPU, printing the outcome so the render path is never silently wrong.
    """
    prefs = bpy.context.preferences.addons["cycles"].preferences
    enabled = []
    for backend in ("OPTIX", "CUDA", "HIP", "ONEAPI", "METAL"):
        try:
            prefs.compute_device_type = backend
        except TypeError:
            continue
        devices = [d for d in prefs.devices if d.type == backend]
        for d in devices:
            d.use = True
        if devices:
            enabled.append((backend, len(devices)))
        if enabled:
            break
    scene = bpy.context.scene
    if enabled:
        scene.cycles.device = "GPU"
        backend, count = enabled[0]
        return f"GPU via {backend} ({count} device{'s' if count > 1 else ''})"
    scene.cycles.device = "CPU"
    return "CPU (no GPU backend available)"


def render(model_name, cams, out_dir, profile, views=None, skip_existing=False,
           model_hash=None):
    from homedesign.model import write_render_sidecar

    scene = bpy.context.scene
    profile_cfg = RENDER_PROFILES[profile]
    _set_engine(scene, profile_cfg["engine"])
    if profile_cfg["engine"] == "CYCLES":
        scene.cycles.samples = profile_cfg["samples"]
        scene.cycles.use_adaptive_sampling = True
        scene.cycles.adaptive_threshold = 0.01
        scene.render.use_persistent_data = True
        device_desc = _configure_cycles_device()
        print(f"cycles device: {device_desc}")
        sys.stdout.flush()
    else:
        # EEVEE settings are version-tolerant (CON-001): legacy EEVEE (4.1)
        # and EEVEE Next (4.2+) differ in which properties exist.
        if hasattr(scene.eevee, "taa_render_samples"):
            scene.eevee.taa_render_samples = profile_cfg["samples"]
        if hasattr(scene.eevee, "use_soft_shadows"):
            scene.eevee.use_soft_shadows = True
        # EEVEE Next raytracing (Blender 4.2+) is opt-in per scene; 4.1's
        # legacy EEVEE has no such flag, so the capability is never silently
        # assumed (CON-001).
        if profile_cfg.get("raytracing"):
            try:
                scene.eevee.use_raytracing = True
                print("eevee raytracing: on")
            except AttributeError:
                print("eevee raytracing: unavailable")
            sys.stdout.flush()
    scene.render.resolution_x, scene.render.resolution_y = profile_cfg["res"]
    scene.cycles.use_denoising = True
    # AgX (Blender 4.0+) compresses highlights and colour-grades faithfully;
    # Filmic is the older fallback, and "Standard" hard-clips bright interior
    # walls to white. The accepted transform is printed so a run is never
    # ambiguous about which path produced it.
    accepted_transform = None
    for transform in ("AgX", "Filmic", "Standard"):
        try:
            scene.view_settings.view_transform = transform
            accepted_transform = transform
            break
        except TypeError:
            continue
    print(f"view transform: {accepted_transform}")
    scene.view_settings.exposure = 0.0

    want = set(views) if views else None
    png_dir = Path(out_dir) / "png"
    png_dir.mkdir(parents=True, exist_ok=True)
    rendered: list[Path] = []
    for cam in cams:
        tag = cam.name.replace("cam_", "")
        if want is not None and tag not in want:
            continue
        target = png_dir / f"{model_name}_{tag}.png"
        if skip_existing and target.exists():
            print(f"skip: {target.name} exists")
            sys.stdout.flush()
            continue
        scene.camera = cam
        scene.render.filepath = str(target)
        bpy.ops.render.render(write_still=True)
        if model_hash:
            write_render_sidecar(target, model_hash, tag, profile)
        rendered.append(target)
    return rendered


def main():
    args = parse_args()
    model = json.loads(Path(args.model).read_text())
    style = model["style"]

    out_dir = Path(args.out)
    blend_path = out_dir / "blend" / f"{model['name']}.blend"
    (out_dir / "blend").mkdir(parents=True, exist_ok=True)

    if args.reuse_blend and blend_path.exists():
        # Reopen the saved scene and go straight to rendering (TASK-04-06).
        bpy.ops.wm.open_mainfile(filepath=str(blend_path))
        cams = [o for o in bpy.context.scene.objects if o.type == "CAMERA"]
    else:
        clear_scene()
        structure = new_collection("Structure")
        furniture = new_collection("Furniture")

        for i, storey in enumerate(model["storeys"]):
            build_walls(storey, style, structure)
            build_floors_and_stairs(storey, style, structure, topmost=(i == len(model["storeys"]) - 1))
            if storey.get("roof"):
                roof_mod.build_roof(storey["roof"], style, structure)
                _build_roof_structures(storey["roof"], style, structure)
            furnish.furnish_storey(storey, style, furniture)

        build_environment(model, structure)
        add_interior_lights(model, structure)
        # Lightweight vertex-colour AO: darken lower vertices so the later
        # glTF export carries a COLOR_0 layer that costs bytes proportional
        # to vertex count (not texture resolution) and the shader's AO mix
        # already consumes it.
        try:
            from homedesign.blender.materials import add_vertex_color_ao

            add_vertex_color_ao()
        except Exception as e:
            print(f"vertex AO: skipped ({e})")
            sys.stdout.flush()
        cams = add_cameras(model)

        bpy.ops.wm.save_as_mainfile(filepath=str(blend_path))

    views = args.views.split(",") if args.views else None
    render(model["name"], cams, out_dir, args.profile, views=views, skip_existing=args.skip_existing,
           model_hash=model.get("model_hash"))

    if args.export_gltf:
        gltf_dir = out_dir / "gltf"
        gltf_dir.mkdir(parents=True, exist_ok=True)
        glb_path = gltf_dir / f"{model['name']}.glb"
        # Flatten procedural graphs back to flat base colours so the GLB
        # never carries image textures and stays under 6/25 MiB. The render
        # already consumed the procedural shading, so this is safe post-render.
        try:
            from homedesign.blender.materials import prepare_for_gltf_export

            prepare_for_gltf_export()
            # Re-apply AO after flatten: the Attribute->MixRGB node was kept
            # in the flatten path as a lightweight multiply; re-ensure the
            # colour layer still exists (no-op if it does).
            from homedesign.blender.materials import add_vertex_color_ao as _ao2

            _ao2()
        except Exception as e:
            print(f"prepare_for_gltf_export: skipped ({e})")
            sys.stdout.flush()
        bpy.ops.export_scene.gltf(
            filepath=str(glb_path),
            export_format="GLB",
            use_selection=False,
            export_yup=False,
        )
        print(f"gltf: {glb_path}")
        sys.stdout.flush()
        from homedesign.viewer import optimize_glb, write_floor_viewer, write_viewer
        before = glb_path.stat().st_size
        if optimize_glb(glb_path):
            print(f"glb optimize: {before} -> {glb_path.stat().st_size} bytes")
        else:
            print("glb optimize: skipped (npx not available or gltf-transform failed)")
        sys.stdout.flush()
        write_viewer(model["name"], glb_path, out_dir)
        floors_path = write_floor_viewer(model["name"], glb_path, model["storeys"], out_dir / "svg", out_dir)
        if floors_path is None:
            print("floor viewer: skipped (plan SVGs not found -- run `plan` before `render --export-gltf`)")
        else:
            print(f"floor viewer: {floors_path}")
        sys.stdout.flush()


if __name__ == "__main__":
    main()
    # bpy sometimes hangs on shutdown in --background mode (lingering device
    # threads); force-exit now that the .blend and renders are on disk.
    import os
    os._exit(0)
