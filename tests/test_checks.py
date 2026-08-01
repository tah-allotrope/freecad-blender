import json
from pathlib import Path

from homedesign.checks import (
    check_door_reachability,
    check_walls_within_plot,
)
from homedesign.compiler import compile_spec

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "spec" / "examples"


def load_example(name):
    return json.loads((EXAMPLES / name).read_text())


def test_demo_spec_is_fully_reachable():
    model = compile_spec(load_example("demo-3br-2storey.json"))
    errors = check_door_reachability(model)
    assert errors == [], f"demo spec should be reachable: {errors}"


def test_unreachable_room_is_flagged():
    spec = load_example("demo-3br-2storey.json")
    # Remove every door on level 1 so bedroom3 loses its only path.
    for storey in spec["storeys"]:
        if storey["level"] == 1:
            storey["openings"] = [
                o for o in storey["openings"] if o["type"] != "door"
            ]
    model = compile_spec(spec)
    errors = check_door_reachability(model)
    assert any(e.code == "room_unreachable" for e in errors)


def test_wall_outside_plot_is_warning():
    model = compile_spec(load_example("tubehouse-mini.json"))
    errors = check_walls_within_plot(model)
    assert errors
    assert all(e.severity == "warning" for e in errors)


def test_unsupported_room_flagged():
    # Level-1 room sitting entirely over an untiled void on level 0.
    spec = {
        "meta": {"name": "t", "style": "modern-minimal", "views": []},
        "site": {"plot_width_mm": 4000, "plot_depth_mm": 10000},
        "storeys": [
            {
                "level": 0,
                "name": "G",
                "height_mm": 3000,
                "rooms": [
                    # Only tiles the front 4000mm; y 4000-10000 is an untiled void.
                    {"id": "a", "type": "living", "rect": {"x": 0, "y": 0, "w": 4000, "d": 4000}},
                ],
                "openings": [],
            },
            {
                "level": 1,
                "name": "F1",
                "height_mm": 3000,
                "rooms": [
                    # Sits at y 4000-8000: 0% covered by the floor below.
                    {"id": "c", "type": "bedroom", "rect": {"x": 0, "y": 4000, "w": 4000, "d": 4000}},
                ],
                "openings": [],
            },
        ],
    }
    model = compile_spec(spec)
    from homedesign.checks import check_room_support
    errors = check_room_support(model)
    assert any(e.code == "room_unsupported" for e in errors)
