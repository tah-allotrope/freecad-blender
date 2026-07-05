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

from homedesign.blender import furnish, joinery, roof as roof_mod  # noqa: E402
from homedesign.blender.geom import boolean_difference, make_box  # noqa: E402
from homedesign.blender.materials import floor_material_key, get_material  # noqa: E402

FLOOR_SLAB_THICKNESS = 0.05
PREVIEW = {"samples": 24, "res": (640, 360)}
FINAL = {"samples": 512, "res": (1920, 1080)}


def parse_args():
    argv = sys.argv[sys.argv.index("--") + 1:] if "--" in sys.argv else []
    p = argparse.ArgumentParser()
    p.add_argument("--model", required=True)
    p.add_argument("--out", required=True)
    p.add_argument("--profile", default="preview", choices=["preview", "final"])
    return p.parse_args(argv)


def clear_scene():
    bpy.ops.wm.read_factory_settings(use_empty=True)


def new_collection(name):
    col = bpy.data.collections.new(name)
    bpy.context.scene.collection.children.link(col)
    return col


def build_walls(storey, style, structure):
    base_z = storey["base_z"] / 1000
    height = storey["height_mm"] / 1000
    for wall in storey["walls"]:
        x, y = wall["x"] / 1000, wall["y"] / 1000
        w, h = wall["w"] / 1000, wall["h"] / 1000
        mat_key = "wall_exterior" if wall["kind"] == "exterior" else "wall_partition"
        mat = get_material(style, mat_key)
        wall_obj = make_box(f"wall_{wall['id']}", x, y, base_z, w, h, height, structure, mat)

        openings = [o for o in storey["openings"] if o["wall_id"] == wall["id"]]
        for opening in openings:
            sill = opening["sill_mm"] / 1000
            head = opening["head_mm"] / 1000
            width = opening["width_mm"] / 1000
            thickness = wall["thickness"] / 1000
            pad = 0.02
            if wall["orientation"] == "vertical":
                cx, cy = x - pad, y + opening["offset_mm"] / 1000
                cw, cd = thickness + 2 * pad, width
            else:
                cx, cy = x + opening["offset_mm"] / 1000, y - pad
                cw, cd = width, thickness + 2 * pad
            cutter = make_box(f"cut_{opening['id']}", cx, cy, base_z + sill, cw, cd, head - sill, structure)
            boolean_difference(wall_obj, cutter, structure)
            joinery.build_opening_furniture(opening, wall, base_z, style, structure)


def build_floors_and_stairs(storey, style, structure):
    base_z = storey["base_z"] / 1000
    for room in storey["rooms"]:
        x, y = room["rect"]["x"] / 1000, room["rect"]["y"] / 1000
        w, d = room["rect"]["w"] / 1000, room["rect"]["d"] / 1000
        mat = get_material(style, floor_material_key(room["type"]))
        make_box(f"floor_{room['id']}", x, y, base_z - FLOOR_SLAB_THICKNESS, w, d, FLOOR_SLAB_THICKNESS, structure, mat)

    if storey.get("stairs"):
        mat = get_material(style, "floor_default")
        for i, t in enumerate(storey["stairs"]["treads"]):
            x, y, z = t["x"] / 1000, t["y"] / 1000, base_z + t["z"] / 1000
            w, d = t["w"] / 1000, t["d"] / 1000
            make_box(f"tread_{storey['level']}_{i}", x, y, z, w, d, 0.18, structure, mat)


def build_environment(model, structure):
    style = model["style"]
    ground_mat = get_material(style, "ground")
    plot_w, plot_d = model["plot_width_mm"] / 1000, model["plot_depth_mm"] / 1000
    pad = 15.0
    make_box("ground", -pad, -pad, -0.3, plot_w + 2 * pad, plot_d + 2 * pad, 0.3, structure, ground_mat)

    world = bpy.data.worlds.new("World")
    bpy.context.scene.world = world
    world.use_nodes = True
    bg = world.node_tree.nodes.get("Background")
    bg.inputs[0].default_value = (0.6, 0.7, 0.85, 1.0)
    bg.inputs[1].default_value = 1.0

    sun_data = bpy.data.lights.new("Sun", type="SUN")
    sun_data.energy = 3.5
    sun = bpy.data.objects.new("Sun", sun_data)
    sun.rotation_euler = (math.radians(55), 0, math.radians(35))
    bpy.context.scene.collection.objects.link(sun)

    fill_data = bpy.data.lights.new("Fill", type="AREA")
    fill_data.energy = 200
    fill_data.size = 5
    fill = bpy.data.objects.new("Fill", fill_data)
    fill.location = (plot_w / 2, -plot_d * 0.5, plot_d)
    bpy.context.scene.collection.objects.link(fill)


def add_interior_lights(model, structure):
    for storey in model["storeys"]:
        base_z = storey["base_z"] / 1000
        ceiling_z = base_z + storey["height_mm"] / 1000 - 0.3
        for room in storey["rooms"]:
            cx = room["rect"]["x"] / 1000 + room["rect"]["w"] / 2000
            cy = room["rect"]["y"] / 1000 + room["rect"]["d"] / 2000
            area_m2 = (room["rect"]["w"] / 1000) * (room["rect"]["d"] / 1000)
            light_data = bpy.data.lights.new(f"light_{room['id']}", type="POINT")
            light_data.energy = min(400.0, max(60.0, area_m2 * 12.0))
            light_data.shadow_soft_size = 0.4
            light = bpy.data.objects.new(f"light_{room['id']}", light_data)
            light.location = (cx, cy, ceiling_z)
            structure.objects.link(light)


def _find_room(model, room_id):
    for storey in model["storeys"]:
        for room in storey["rooms"]:
            if room["id"] == room_id:
                return storey, room
    return None


def _find_default_interior_room(model):
    interior_priority = ["living", "master", "bedroom", "kitchen"]
    for level_target in interior_priority:
        for storey in model["storeys"]:
            for room in storey["rooms"]:
                if room["id"] == level_target or room["type"] == level_target:
                    return storey, room
    return None


def _build_exterior_front_camera(name, model, plot_w, plot_d, total_height, centroid):
    # Framed off the street frontage (plot_w), not max(plot_w, plot_d) -- on a
    # long narrow tube house the depth would otherwise push the camera far
    # enough back that the blank party-wall side dominates the shot.
    cam_data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cam_data)
    dist = plot_w * 3.0 + total_height * 1.2 + 6
    cam.location = (centroid[0] - plot_w * 0.9, -dist * 0.55, total_height * 0.55 + 1.5)
    _point_at(cam, (centroid[0], plot_d * 0.08, total_height * 0.45))
    bpy.context.scene.collection.objects.link(cam)
    return cam


def _build_exterior_aerial_camera(name, model, plot_w, plot_d, total_height, centroid):
    cam_data = bpy.data.cameras.new(name)
    cam = bpy.data.objects.new(name, cam_data)
    dist = max(plot_w, plot_d) * 1.4 + 5
    cam.location = (centroid[0] + dist * 0.5, centroid[1] - dist * 0.5, total_height * 3.0 + 6)
    _point_at(cam, centroid)
    bpy.context.scene.collection.objects.link(cam)
    return cam


def _build_room_camera(name, storey, room):
    """Place the camera near one short-axis wall, centered on the short axis,
    aimed down the long axis -- a corner-and-centroid heuristic breaks down
    on this tool's elongated tube-house rooms (e.g. 4m x 9.5m), putting the
    camera nearly against a wall."""
    x = room["rect"]["x"] / 1000
    y = room["rect"]["y"] / 1000
    w = room["rect"]["w"] / 1000
    d = room["rect"]["d"] / 1000
    base_z = storey["base_z"] / 1000
    eye_z = base_z + 1.5

    long_is_depth = d >= w
    long_dim = d if long_is_depth else w
    short_dim = w if long_is_depth else d
    clearance = max(0.5, min(short_dim * 0.4, long_dim * 0.15))

    if long_is_depth:
        cam_x, cam_y = x + w / 2, y + clearance
        target = (x + w / 2, y + long_dim * 0.65, eye_z - 0.2)
    else:
        cam_x, cam_y = x + clearance, y + d / 2
        target = (x + long_dim * 0.65, y + d / 2, eye_z - 0.2)

    cam_data = bpy.data.cameras.new(name)
    cam_data.lens = 20
    cam = bpy.data.objects.new(name, cam_data)
    cam.location = (cam_x, cam_y, eye_z)
    _point_at(cam, target)
    bpy.context.scene.collection.objects.link(cam)
    return cam


def add_cameras(model):
    plot_w, plot_d = model["plot_width_mm"] / 1000, model["plot_depth_mm"] / 1000
    total_height = sum(s["height_mm"] for s in model["storeys"]) / 1000
    centroid = (plot_w / 2, plot_d / 2, total_height / 2)

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
            cams.append(_build_exterior_front_camera(name, model, plot_w, plot_d, total_height, centroid))
        elif view["kind"] == "exterior_aerial":
            cams.append(_build_exterior_aerial_camera(name, model, plot_w, plot_d, total_height, centroid))
        elif view["kind"] == "room":
            found = _find_room(model, view["room_id"])
            if found:
                cams.append(_build_room_camera(name, *found))

    return cams


def _point_at(obj, target):
    direction = (target[0] - obj.location[0], target[1] - obj.location[1], target[2] - obj.location[2])
    import mathutils
    obj.rotation_euler = mathutils.Vector(direction).to_track_quat("-Z", "Y").to_euler()


def render(model_name, cams, out_dir, profile):
    scene = bpy.context.scene
    scene.render.engine = "CYCLES"
    profile_cfg = FINAL if profile == "final" else PREVIEW
    scene.cycles.samples = profile_cfg["samples"]
    scene.render.resolution_x, scene.render.resolution_y = profile_cfg["res"]
    scene.cycles.use_denoising = True
    scene.view_settings.view_transform = "Standard"
    scene.view_settings.exposure = 0.2
    try:
        scene.cycles.device = "GPU"
    except Exception:
        pass

    png_dir = Path(out_dir) / "png"
    png_dir.mkdir(parents=True, exist_ok=True)
    for cam in cams:
        scene.camera = cam
        tag = cam.name.replace("cam_", "")
        scene.render.filepath = str(png_dir / f"{model_name}_{tag}.png")
        bpy.ops.render.render(write_still=True)


def main():
    args = parse_args()
    model = json.loads(Path(args.model).read_text())
    style = model["style"]

    clear_scene()
    structure = new_collection("Structure")
    furniture = new_collection("Furniture")

    for storey in model["storeys"]:
        build_walls(storey, style, structure)
        build_floors_and_stairs(storey, style, structure)
        if storey.get("roof"):
            roof_mod.build_roof(storey["roof"], style, structure)
        furnish.furnish_storey(storey, style, furniture)

    build_environment(model, structure)
    add_interior_lights(model, structure)
    cams = add_cameras(model)

    out_dir = Path(args.out)
    (out_dir / "blend").mkdir(parents=True, exist_ok=True)
    bpy.ops.wm.save_as_mainfile(filepath=str(out_dir / "blend" / f"{model['name']}.blend"))

    render(model["name"], cams, out_dir, args.profile)


if __name__ == "__main__":
    main()
    # bpy sometimes hangs on shutdown in --background mode (lingering device
    # threads); force-exit now that the .blend and renders are on disk.
    import os
    os._exit(0)
