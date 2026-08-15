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


def test_wall_outside_plot_clean_under_centre_alignment():
    # A centre-aligned wall legitimately straddles the plot line by half its
    # thickness, so a compliant spec emits nothing (was 24/63 warning lines).
    model = compile_spec(load_example("tubehouse-mini.json"))
    assert model.wall_alignment == "centre"
    assert check_walls_within_plot(model) == []


def test_wall_outside_plot_is_now_an_error():
    # The compiler rejects rooms outside the plot at compile time, so the
    # check is unit-tested on a compiled model whose west wall is shoved 400mm
    # past the plot line -- beyond the centre-alignment tolerance, and the
    # violation is error-severity, not a warning.
    from homedesign.model import CompiledModel, Rect, Room, Storey, Wall

    model = CompiledModel(
        name="t", style="modern-minimal",
        plot_width_mm=4000, plot_depth_mm=5000,
        storeys=[
            Storey(
                level=0, name="G", height_mm=3000, base_z=0,
                rooms=[Room(id="a", type="living", rect=Rect(x=0, y=0, w=4000, d=5000))],
                walls=[
                    Wall(id="F0_W001", x=-400.0, y=0, w=200.0, h=5000.0,
                         thickness=200.0, kind="exterior", storey_level=0, orientation="vertical"),
                ],
            )
        ],
    )
    errors = check_walls_within_plot(model)
    assert errors
    assert any(e.code == "wall_outside_plot" for e in errors)
    assert all(e.severity != "warning" for e in errors)


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


def _void_supported_spec(with_void=True):
    spec = {
        "meta": {"name": "t", "style": "modern-minimal"},
        "site": {"plot_width_mm": 4000, "plot_depth_mm": 8000},
        "storeys": [
            {
                "level": 0, "name": "G", "height_mm": 3000,
                "rooms": [
                    # Only tiles the front 4000mm; y 4000-8000 is a declared void.
                    {"id": "a", "type": "living", "rect": {"x": 0, "y": 0, "w": 4000, "d": 4000}},
                ],
                "openings": [],
            },
            {
                "level": 1, "name": "F1", "height_mm": 3000,
                "rooms": [
                    {"id": "c", "type": "bedroom", "rect": {"x": 0, "y": 4000, "w": 4000, "d": 4000}},
                ],
                "openings": [],
            },
        ],
    }
    if with_void:
        spec["storeys"][0]["voids"] = [{"x": 0, "y": 4000, "w": 4000, "d": 4000}]
    return spec


def test_declared_void_supports_room_above():
    from homedesign.checks import check_room_support

    model = compile_spec(_void_supported_spec(with_void=True))
    assert check_room_support(model) == []


def test_removing_declared_void_flags_unsupported_room():
    from homedesign.checks import check_room_support

    model = compile_spec(_void_supported_spec(with_void=False))
    errors = check_room_support(model)
    assert len([e for e in errors if e.code == "room_unsupported"]) == 1
    assert "0%" in errors[0].message


def test_large_void_span_is_a_warning():
    from homedesign.checks import check_void_spans

    spec = _void_supported_spec(with_void=True)
    spec["storeys"][0]["voids"] = [{"x": 0, "y": 0, "w": 7000, "d": 7000}]
    spec["storeys"][0]["rooms"] = [{"id": "a", "type": "living", "rect": {"x": 0, "y": 0, "w": 8000, "d": 8000}}]
    spec["site"]["plot_width_mm"] = 8000
    spec["site"]["plot_depth_mm"] = 8000
    # The upper room now sits over the (declared) void; give it a supported area
    # so room_support is not the thing under test.
    model = compile_spec(spec)
    errors = check_void_spans(model)
    assert any(e.code == "void_span_large" and e.severity == "warning" for e in errors)


def test_void_dedupes_with_elevator_footprint():
    spec = _void_supported_spec(with_void=True)
    spec["storeys"][0]["rooms"].append(
        {"id": "lift", "type": "elevator", "rect": {"x": 0, "y": 4000, "w": 4000, "d": 4000}}
    )
    model = compile_spec(spec)
    storey = model.storeys[0]
    assert len(storey.authored_voids) == 1
    # The authored void coincides with the elevator footprint, so the merged
    # floor_voids collapses to one rectangle.
    assert len(storey.floor_voids) == 1
