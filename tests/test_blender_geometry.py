"""Blender-side geometry invariants (PHASE-04, ASM-007).

These tests require the `bpy` PyPI wheel; without it they skip cleanly. CI
deliberately does not install `bpy` (see AGENTS.md), so this file runs only on
a machine with `python -m pip install -e ".[dev,bpy]"`.

Each invariant below is one that was previously verified by hand-written
throwaway scripts and then lost; pinning them here prevents the same regressions.
"""
import json
from pathlib import Path

import pytest

bpy = pytest.importorskip("bpy")

import mathutils  # noqa: E402

from homedesign.blender import build_scene, furnish, materials, roof as roof_mod  # noqa: E402
from homedesign.rects import open_edges  # noqa: E402

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "spec" / "examples"
DESIGNS = REPO_ROOT / "designs"

# The flat roof overhangs the plot by 300mm by default, so the containment
# tolerance must cover that; it is otherwise a generous guard against the
# "origin at world zero" mesh-placement bug.
TOLERANCE_M = 0.6


def _load_compiled(spec_path):
    from homedesign.compiler import compile_spec

    spec = json.loads(Path(spec_path).read_text(encoding="utf-8"))
    return compile_spec(spec).to_dict()


def _build_scene(spec_path):
    build_scene.clear_scene()
    # `read_factory_settings` above removed every material, but the module-level
    # material cache still references them; reset it so `get_material` rebuilds.
    materials._cache.clear()
    structure = build_scene.new_collection("Structure")
    furniture = build_scene.new_collection("Furniture")
    model = _load_compiled(spec_path)
    style = model["style"]
    for i, storey in enumerate(model["storeys"]):
        build_scene.build_walls(storey, style, structure)
        build_scene.build_floors_and_stairs(
            storey, style, structure, topmost=(i == len(model["storeys"]) - 1)
        )
        if storey.get("roof"):
            roof_mod.build_roof(storey["roof"], style, structure)
            build_scene._build_roof_structures(storey["roof"], style, structure)
        furnish.furnish_storey(storey, style, furniture)
    build_scene.build_environment(model, structure)
    build_scene.add_interior_lights(model, structure)
    cams = build_scene.add_cameras(model)
    return model, structure, cams


def _world_bbox(obj):
    return [obj.matrix_world @ mathutils.Vector(c) for c in obj.bound_box]


def test_every_mesh_stays_within_the_plot():
    model, _structure, _cams = _build_scene(EXAMPLES / "tubehouse-mini.json")
    plot_w = model["plot_width_mm"] / 1000
    plot_d = model["plot_depth_mm"] / 1000
    for obj in bpy.context.scene.objects:
        if obj.name.startswith(("ground", "neighbour", "street", "carriageway", "kerb", "opposite", "alley")):
            continue
        if obj.type != "MESH":
            continue
        for corner in _world_bbox(obj):
            assert -TOLERANCE_M <= corner.x <= plot_w + TOLERANCE_M, (obj.name, corner)
            assert -TOLERANCE_M <= corner.y <= plot_d + TOLERANCE_M, (obj.name, corner)


def _overlap_area(a, b):
    w = max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    d = max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    return w * d


def test_no_floor_slab_covers_a_declared_void():
    model, _structure, _cams = _build_scene(EXAMPLES / "courtyard-fixture.json")
    floors = [o for o in bpy.context.scene.objects if o.name.startswith("floor_")]
    for storey in model["storeys"]:
        for void in storey.get("floor_voids", []):
            v = (void["x"], void["y"], void["w"], void["d"])
            v_area = void["w"] * void["d"]
            for obj in floors:
                xs = [c.x * 1000 for c in _world_bbox(obj)]
                ys = [c.y * 1000 for c in _world_bbox(obj)]
                f = (min(xs), min(ys), max(xs) - min(xs), max(ys) - min(ys))
                assert _overlap_area(v, f) <= 0.01 * v_area, (obj.name, void)


def test_every_room_camera_sits_inside_its_room():
    model, _structure, cams = _build_scene(EXAMPLES / "tubehouse-mini.json")
    by_id = {}
    for storey in model["storeys"]:
        for room in storey["rooms"]:
            by_id[room["id"]] = room
    for view in model.get("views") or []:
        if view["kind"] != "room":
            continue
        cam = next((c for c in cams if c.name == f"cam_{view['name']}"), None)
        if cam is None:
            continue
        room = by_id[view["room_id"]]
        rect = room.get("interior") or room["rect"]
        pos = cam.location
        assert rect["x"] / 1000 <= pos.x <= (rect["x"] + rect["w"]) / 1000, view
        assert rect["y"] / 1000 <= pos.y <= (rect["y"] + rect["d"]) / 1000, view


def test_suppressed_open_edge_walls_match_open_edges():
    from homedesign.model import Rect

    model, _structure, _cams = _build_scene(DESIGNS / "tubehouse-dream.json")
    for storey in model["storeys"]:
        room_types = {r["id"]: r["type"] for r in storey["rooms"]}
        opening_wall_ids = {o["wall_id"] for o in storey["openings"]}
        rects = [Rect(**r["rect"]) for r in storey["rooms"]]
        for room, rect in zip(storey["rooms"], rects):
            if room_types[room["id"]] not in build_scene.OPEN_ROOM_TYPES:
                continue
            others = [r for r in rects if (r.x, r.y, r.w, r.d) != (rect.x, rect.y, rect.w, rect.d)]
            open_sides = open_edges(rect, others)
            for wall in storey["walls"]:
                if wall.get("room_id") != room["id"]:
                    continue
                is_suppressed = (
                    wall["id"] not in opening_wall_ids
                    and room_types.get(wall["room_id"]) in build_scene.OPEN_ROOM_TYPES
                )
                if not is_suppressed:
                    continue
                # A suppressed wall must sit on one of the room's open edges.
                side = _wall_side_of(wall, room["rect"])
                assert side in open_sides, (room["id"], wall["id"], side, open_sides)


def _wall_side_of(wall, rect):
    eps = wall["thickness"] / 2 + 1.0
    if wall["orientation"] == "vertical":
        coord = wall["x"] + wall["thickness"] / 2
        if abs(coord - rect["x"]) < eps:
            return "west"
        if abs(coord - (rect["x"] + rect["w"])) < eps:
            return "east"
    else:
        coord = wall["y"] + wall["thickness"] / 2
        if abs(coord - rect["y"]) < eps:
            return "north"
        if abs(coord - (rect["y"] + rect["d"])) < eps:
            return "south"
    return None


def test_furniture_material_key_mapping():
    from homedesign.blender.materials import furniture_material_key

    assert furniture_material_key("bed") == "upholstery"
    assert furniture_material_key("nightstand") == "furniture"
    assert furniture_material_key("wc") == "porcelain"
    assert furniture_material_key("car") == "vehicle"
