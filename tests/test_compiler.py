import json
from pathlib import Path

import pytest

from homedesign.compiler import compile_spec
from homedesign.errors import SpecValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "spec" / "examples"


def load_example(name):
    return json.loads((EXAMPLES / name).read_text())


def test_demo_compiles_two_storeys():
    model = compile_spec(load_example("demo-3br-2storey.json"))
    assert model.name == "demo-3br-2storey"
    assert len(model.storeys) == 2
    assert model.storeys[0].base_z == 0
    assert model.storeys[1].base_z == 3000


def test_demo_walls_include_exterior_and_partition():
    model = compile_spec(load_example("demo-3br-2storey.json"))
    ground = model.storeys[0]
    kinds = {w.kind for w in ground.walls}
    assert kinds == {"exterior", "partition"}
    assert len(ground.walls) > 4


def test_asymmetric_row_boundary_becomes_partition_walls():
    """Level 1 has a 3-room top row over a 4-room bottom row; the shared
    boundary line must still resolve into correct 2-room partition walls,
    not fall back to 'exterior' just because spans don't match exactly."""
    model = compile_spec(load_example("demo-3br-2storey.json"))
    upper = model.storeys[1]
    boundary_walls = [w for w in upper.walls if w.orientation == "horizontal" and abs(w.y + w.thickness / 2 - 4000) < 5]
    assert boundary_walls, "expected walls along the y=4000 row boundary"
    assert all(w.kind == "partition" for w in boundary_walls)


def test_openings_placed_on_walls():
    model = compile_spec(load_example("demo-3br-2storey.json"))
    ground = model.storeys[0]
    wall_ids = {w.id for w in ground.walls}
    assert len(ground.openings) == 10
    for o in ground.openings:
        assert o.wall_id in wall_ids


def test_kitchen_living_opening_is_wide():
    model = compile_spec(load_example("demo-3br-2storey.json"))
    ground = model.storeys[0]
    opening = next(o for o in ground.openings if o.width_mm == 3800)
    wall = next(w for w in ground.walls if w.id == opening.wall_id)
    assert wall.kind == "partition"


def test_room_overlap_is_rejected():
    spec = load_example("demo-3br-2storey.json")
    spec["storeys"][0]["rooms"][1]["rect"] = {"x": 3900, "y": 0, "w": 6000, "d": 4000}
    with pytest.raises(SpecValidationError) as exc:
        compile_spec(spec)
    assert any(e.code == "room_overlap" for e in exc.value.errors)


def test_room_outside_plot_is_rejected():
    spec = load_example("demo-3br-2storey.json")
    spec["storeys"][0]["rooms"][0]["rect"] = {"x": 0, "y": 0, "w": 9000, "d": 4000}
    with pytest.raises(SpecValidationError) as exc:
        compile_spec(spec)
    assert any(e.code == "room_overlap" or e.code == "room_outside_plot" for e in exc.value.errors)


def test_opening_between_nonadjacent_rooms_is_rejected():
    spec = load_example("demo-3br-2storey.json")
    spec["storeys"][0]["openings"].append({"type": "door", "between": ["kitchen", "office"], "width_mm": 900})
    with pytest.raises(SpecValidationError) as exc:
        compile_spec(spec)
    assert any(e.code == "opening_no_wall" for e in exc.value.errors)


def test_opening_too_wide_is_rejected():
    spec = load_example("demo-3br-2storey.json")
    spec["storeys"][0]["openings"].append({"type": "door", "between": ["hall", "stairwell"], "width_mm": 9000})
    with pytest.raises(SpecValidationError) as exc:
        compile_spec(spec)
    assert any(e.code == "opening_too_wide" for e in exc.value.errors)


def test_relative_room_placement_resolves():
    spec = {
        "meta": {"name": "relative-test", "style": "modern-minimal"},
        "site": {"plot_width_mm": 8000, "plot_depth_mm": 8000},
        "storeys": [
            {
                "level": 0,
                "name": "Ground",
                "height_mm": 3000,
                "rooms": [
                    {"id": "living", "type": "living", "rect": {"x": 0, "y": 0, "w": 4000, "d": 8000}},
                    {"id": "kitchen", "type": "kitchen", "relative": {"adjacent_to": "living", "side": "east", "w": 4000, "d": 4000}},
                    {"id": "bedroom", "type": "bedroom", "relative": {"adjacent_to": "kitchen", "side": "south", "w": 4000, "d": 4000}},
                ],
            }
        ],
    }
    model = compile_spec(spec)
    kitchen = next(r for r in model.storeys[0].rooms if r.id == "kitchen")
    bedroom = next(r for r in model.storeys[0].rooms if r.id == "bedroom")
    assert (kitchen.rect.x, kitchen.rect.y) == (4000, 0)
    assert (bedroom.rect.x, bedroom.rect.y) == (4000, 4000)


def test_stairs_span_full_storey_height():
    model = compile_spec(load_example("tubehouse-mini.json"))
    ground = model.storeys[0]
    assert ground.stairs is not None
    assert len(ground.stairs.treads) >= 2
    assert ground.stairs.treads[-1].z <= ground.height_mm


def test_roof_only_on_declared_storey():
    model = compile_spec(load_example("demo-3br-2storey.json"))
    assert model.storeys[0].roof is None
    assert model.storeys[1].roof is not None
    assert model.storeys[1].roof.type == "gable"


def test_model_round_trips_through_dict():
    from homedesign.model import CompiledModel

    model = compile_spec(load_example("tubehouse-mini.json"))
    data = model.to_dict()
    restored = CompiledModel.from_dict(data)
    assert restored.name == model.name
    assert len(restored.storeys) == len(model.storeys)
    assert restored.storeys[0].walls[0].id == model.storeys[0].walls[0].id


def _lightwell_spec():
    """A minimal 2-storey plot with an untiled void (light well) at mid-depth,
    a room on each side of it, and a roof that only covers part of the plot
    with the light well punched out as a void."""
    return {
        "meta": {"name": "lightwell-test", "style": "modern-minimal"},
        "site": {"plot_width_mm": 4000, "plot_depth_mm": 10000},
        "storeys": [
            {
                "level": 0,
                "name": "Ground",
                "height_mm": 3400,
                "rooms": [
                    {"id": "front", "type": "living", "rect": {"x": 0, "y": 0, "w": 4000, "d": 4000}},
                    # y: 4000-6000 left as an untiled void (the light well)
                    {"id": "rear", "type": "kitchen", "rect": {"x": 0, "y": 6000, "w": 4000, "d": 4000}},
                ],
                "openings": [
                    {"type": "door", "between": ["front", "exterior"], "width_mm": 1000},
                    {"type": "window", "between": ["rear", "exterior"], "width_mm": 1200, "side": "south"},
                    {"type": "window", "between": ["rear", "exterior"], "width_mm": 900, "side": "north"},
                ],
            },
            {
                "level": 1,
                "name": "Roof Storey",
                "height_mm": 3400,
                "rooms": [
                    {"id": "front2", "type": "bedroom", "rect": {"x": 0, "y": 0, "w": 4000, "d": 4000}},
                    {"id": "rear2", "type": "office", "rect": {"x": 0, "y": 6000, "w": 4000, "d": 4000}},
                ],
                "roof": {
                    "type": "flat",
                    "rect": {"x": 0, "y": 6000, "w": 4000, "d": 4000},
                    "voids": [{"x": 500, "y": 6500, "w": 1000, "d": 1000}],
                },
            },
        ],
    }


def test_roof_rect_overrides_plot_span():
    model = compile_spec(_lightwell_spec())
    roof = model.storeys[1].roof
    assert roof is not None
    # overhang (default 300mm) still expands outward from the given rect, not the plot
    assert roof.x == -300
    assert roof.y == 6000 - 300
    assert roof.w == 4000 + 600
    assert roof.d == 4000 + 600


def test_roof_voids_are_recorded_and_excluded_from_footprint():
    model = compile_spec(_lightwell_spec())
    roof = model.storeys[1].roof
    assert len(roof.voids) == 1
    void = roof.voids[0]
    assert (void.x, void.y, void.w, void.d) == (500, 6500, 1000, 1000)


def test_opening_side_hint_selects_matching_exterior_wall():
    model = compile_spec(_lightwell_spec())
    ground = model.storeys[0]
    rear = next(r for r in ground.rooms if r.id == "rear")
    south_window = next(o for o in ground.openings if o.width_mm == 1200)
    north_window = next(o for o in ground.openings if o.width_mm == 900)
    south_wall = next(w for w in ground.walls if w.id == south_window.wall_id)
    north_wall = next(w for w in ground.walls if w.id == north_window.wall_id)
    # south = higher-y edge (rect.y2), north = lower-y edge (rect.y)
    assert abs((south_wall.y + south_wall.thickness / 2) - rear.rect.y2) < 1
    assert abs((north_wall.y + north_wall.thickness / 2) - rear.rect.y) < 1
    assert south_wall.id != north_wall.id


def test_opening_side_hint_with_no_matching_wall_is_rejected():
    """front_a and front_b sit side by side sharing a partition wall on
    front_a's east edge; there is no *exterior* wall on that side, so a
    side='east' hint against 'exterior' must fail rather than silently
    falling back to a different face."""
    spec = {
        "meta": {"name": "side-hint-reject-test", "style": "modern-minimal"},
        "site": {"plot_width_mm": 4000, "plot_depth_mm": 4000},
        "storeys": [
            {
                "level": 0,
                "name": "Ground",
                "height_mm": 3000,
                "rooms": [
                    {"id": "front_a", "type": "living", "rect": {"x": 0, "y": 0, "w": 2000, "d": 4000}},
                    {"id": "front_b", "type": "kitchen", "rect": {"x": 2000, "y": 0, "w": 2000, "d": 4000}},
                ],
                "openings": [
                    {"type": "window", "between": ["front_a", "exterior"], "width_mm": 900, "side": "east"},
                ],
            }
        ],
    }
    with pytest.raises(SpecValidationError) as exc:
        compile_spec(spec)
    assert any(e.code == "opening_no_wall" for e in exc.value.errors)


def test_views_resolve_and_default_to_empty():
    model = compile_spec(load_example("tubehouse-mini.json"))
    assert model.views == []


def test_views_resolve_room_kind_against_actual_rooms():
    spec = _lightwell_spec()
    spec["meta"]["views"] = [
        {"name": "street", "kind": "exterior_front"},
        {"name": "aerial", "kind": "exterior_aerial"},
        {"name": "kitchen_shot", "kind": "room", "room_id": "rear"},
    ]
    model = compile_spec(spec)
    assert [v.name for v in model.views] == ["street", "aerial", "kitchen_shot"]
    assert model.views[2].room_id == "rear"


def test_views_reject_unknown_room_id():
    spec = _lightwell_spec()
    spec["meta"]["views"] = [{"name": "bad", "kind": "room", "room_id": "does_not_exist"}]
    with pytest.raises(SpecValidationError) as exc:
        compile_spec(spec)
    assert any(e.code == "view_room_not_found" for e in exc.value.errors)


def test_elevator_room_type_compiles_like_any_other_room():
    spec = _lightwell_spec()
    spec["storeys"][0]["rooms"].append(
        {"id": "lift", "type": "elevator", "rect": {"x": 4000, "y": 0, "w": 0, "d": 0}}
    )
    # give it real, valid dimensions instead of the placeholder above
    spec["storeys"][0]["rooms"][-1]["rect"] = {"x": 0, "y": 4200, "w": 1200, "d": 1500}
    model = compile_spec(spec)
    lift = next(r for r in model.storeys[0].rooms if r.id == "lift")
    assert lift.type == "elevator"


def _single_room_spec(alignment=None):
    spec = {
        "meta": {"name": "wall-align", "style": "modern-minimal"},
        "site": {"plot_width_mm": 4000, "plot_depth_mm": 5000},
        "storeys": [
            {
                "level": 0, "name": "G", "height_mm": 3000,
                "rooms": [{"id": "a", "type": "living", "rect": {"x": 0, "y": 0, "w": 4000, "d": 5000}}],
                "openings": [],
            }
        ],
    }
    if alignment:
        spec["site"]["wall_alignment"] = alignment
    return spec


def test_wall_alignment_centre_straddles_edge():
    model = compile_spec(_single_room_spec())
    west = next(w for w in model.storeys[0].walls if w.orientation == "vertical" and w.x < 0)
    assert abs(west.x - (-100)) < 1e-6
    assert abs(west.w - 200) < 1e-6


def test_wall_alignment_inside_lies_on_room_side():
    model = compile_spec(_single_room_spec("inside"))
    west = next(w for w in model.storeys[0].walls if w.orientation == "vertical" and abs(w.x) < 1e-6)
    assert abs(west.x - 0.0) < 1e-6
    assert abs(west.w - 200) < 1e-6


def test_default_alignment_preserves_legacy_geometry():
    # The byte-identity guarantee of DEC-003: no wall_alignment key compiles to
    # the same centred geometry as before the change.
    model = compile_spec(_single_room_spec())
    assert model.wall_alignment == "centre"
    west = next(w for w in model.storeys[0].walls if w.orientation == "vertical" and w.x < 0)
    assert abs(west.x + west.thickness / 2 - 0.0) < 1e-6


def test_interior_inside_alignment_full_exterior_walls():
    model = compile_spec(_single_room_spec("inside"))
    room = model.storeys[0].rooms[0]
    assert room.interior is not None
    i = room.interior
    assert (i.x, i.y, i.w, i.d) == (200.0, 200.0, 3600.0, 4600.0)


def test_interior_centre_partition_bounded_inset_half():
    # A room with a partition on its east edge is inset by half INT_THICKNESS
    # (50mm) on that edge only, leaving other edges unshrunk.
    spec = {
        "meta": {"name": "part", "style": "modern-minimal"},
        "site": {"plot_width_mm": 8000, "plot_depth_mm": 4000},
        "storeys": [
            {
                "level": 0, "name": "G", "height_mm": 3000,
                "rooms": [
                    {"id": "a", "type": "living", "rect": {"x": 0, "y": 0, "w": 4000, "d": 4000}},
                    {"id": "b", "type": "bedroom", "rect": {"x": 4000, "y": 0, "w": 4000, "d": 4000}},
                ],
                "openings": [],
            }
        ],
    }
    model = compile_spec(spec)
    a = next(r for r in model.storeys[0].rooms if r.id == "a")
    assert a.interior is not None
    i = a.interior
    # East edge (shared partition) inset 50mm; west/north/south (exterior,
    # centre) inset 100mm each.
    assert i.x == 100.0
    assert i.y == 100.0
    assert i.w == 4000.0 - 100.0 - 50.0
    assert i.d == 4000.0 - 100.0 - 100.0
