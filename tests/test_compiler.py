import json
from pathlib import Path

import pytest

from src.homedesign.compiler import compile_spec
from src.homedesign.errors import SpecValidationError

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
    assert ground.stairs.treads[-1].z < ground.height_mm


def test_roof_only_on_declared_storey():
    model = compile_spec(load_example("demo-3br-2storey.json"))
    assert model.storeys[0].roof is None
    assert model.storeys[1].roof is not None
    assert model.storeys[1].roof.type == "gable"


def test_model_round_trips_through_dict():
    from src.homedesign.model import CompiledModel

    model = compile_spec(load_example("tubehouse-mini.json"))
    data = model.to_dict()
    restored = CompiledModel.from_dict(data)
    assert restored.name == model.name
    assert len(restored.storeys) == len(model.storeys)
    assert restored.storeys[0].walls[0].id == model.storeys[0].walls[0].id
