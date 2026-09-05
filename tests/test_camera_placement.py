"""Pure-Python camera-placement assertions (PHASE-01). No Blender needed:
these run everywhere and are the real CI guard against cameras outside the
building."""
import json
from dataclasses import asdict
from pathlib import Path

import pytest

from homedesign.camera_fit import exterior_front_camera, interior_camera
from homedesign.compiler import compile_spec

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "spec" / "examples"
DESIGNS = REPO_ROOT / "designs"

ALL_SPECS = sorted(EXAMPLES.glob("*.json")) + sorted(DESIGNS.glob("*.json"))


def _model_of(path: Path):
    return compile_spec(json.loads(path.read_text(encoding="utf-8")))


@pytest.mark.parametrize("spec_path", ALL_SPECS, ids=lambda p: p.stem)
def test_interior_cameras_are_inside_their_rooms(spec_path):
    """Every room of every spec: interior_camera must stand strictly inside the
    room rect. Under the old pull-back logic 0 of 6 rooms in tubehouse-mini
    passed; this sweep is the regression guard."""
    model = _model_of(spec_path)
    assert model.storeys, "spec must have at least one storey"
    for storey in model.storeys:
        for room in storey.rooms:
            position, _target, lens = interior_camera(
                asdict(storey), asdict(room), 1920, 1080
            )
            px, py = position[0], position[1]
            r = room.rect
            assert r.x / 1000 < px < r.x2 / 1000, (
                f"{room.id} on storey {storey.level}: x={px:.3f} outside rect x "
                f"({r.x / 1000:.3f}, {r.x2 / 1000:.3f})"
            )
            assert r.y / 1000 < py < r.y2 / 1000, (
                f"{room.id} on storey {storey.level}: y={py:.3f} outside rect y "
                f"({r.y / 1000:.3f}, {r.y2 / 1000:.3f})"
            )


def test_interior_lens_stays_within_bounds():
    model = _model_of(EXAMPLES / "tubehouse-mini.json")
    for storey in model.storeys:
        for room in storey.rooms:
            _p, _t, lens = interior_camera(asdict(storey), asdict(room), 1920, 1080)
            assert 12.0 <= lens <= 24.0, f"{room.id} lens {lens} out of [12, 24]"


def test_exterior_front_stands_off_facade():
    """The front camera must stand far enough south that the facade height fits
    (the current broken code leaves the facade overflowing the frame 3.4x)."""
    model = _model_of(EXAMPLES / "tubehouse-mini.json")
    position, target, _lens = exterior_front_camera(model.to_dict(), 1920, 1080)
    assert abs(position[0] - 2.0) < 1e-6  # centred on the 4m plot
    assert abs(position[2] - 4.6) < 1e-6  # facade-height centre
    assert position[1] <= -15.90, (
        f"front camera at y={position[1]:.3f}; needs <= -15.90 to fit the facade"
    )
    assert abs(target[1]) < 1e-6  # looking at the facade plane at y = 0


def test_exterior_street_stands_off_southeast_corner():
    """The 3/4 hero must stand east of the plot, south of the facade plane,
    above ground, targeting the facade plane at ~55% height."""
    from homedesign.camera_fit import exterior_street_camera

    for spec_path in ALL_SPECS:
        model = _model_of(spec_path).to_dict()
        plot_w = model["plot_width_mm"] / 1000
        total_h = sum(s["height_mm"] for s in model["storeys"]) / 1000
        position, target, lens = exterior_street_camera(model, 1920, 1080)
        assert position[0] > plot_w, f"{spec_path.stem}: x={position[0]:.2f} not east of plot"
        assert position[1] < 0.0, f"{spec_path.stem}: y={position[1]:.2f} not on street side"
        assert position[2] > 0.0, f"{spec_path.stem}: z={position[2]:.2f} below ground"
        assert target == (plot_w / 2, 0.0, total_h * 0.55), f"{spec_path.stem}: bad target {target}"
        assert lens == 35.0



def test_degenerate_room_still_gets_an_inside_camera():
    """A 700x700mm room (below the practical minimum, above the 600mm
    room_too_small threshold) must still get a contained camera at the wide
    lens clamp, never raising."""
    storey = {"base_z": 0, "height_mm": 3000}
    room = {"id": "tiny", "type": "storage", "rect": {"x": 0, "y": 0, "w": 700, "d": 700}}
    position, _target, lens = interior_camera(storey, room, 1920, 1080)
    assert 0.0 < position[0] < 0.7
    assert 0.0 < position[1] < 0.7
    assert lens == 12.0


def test_bedroom_camera_anchors_off_centre():
    """A centred camera stares down the bed's long axis from inside its
    footprint and the hero reads empty; bedrooms anchor at quarter width
    while other rooms stay centred."""
    storey = {"base_z": 7000, "height_mm": 3400}
    rect = {"x": 0, "y": 4900, "w": 3960, "d": 4000}
    bed = {"id": "ngu", "type": "bedroom", "rect": dict(rect)}
    position, target, _lens = interior_camera(storey, bed, 1920, 1080)
    assert position[0] == pytest.approx(0.99)
    assert target[0] == pytest.approx(1.98)
    living = {"id": "khach", "type": "living", "rect": dict(rect)}
    position, _target, _lens = interior_camera(storey, living, 1920, 1080)
    assert position[0] == pytest.approx(1.98)
def test_kitchen_camera_faces_the_run_from_the_far_end():
    """The run hugs the near wall (under a centred lens), so kitchens shoot
    from the far end back at it; other rooms keep the near anchor."""
    storey = {"base_z": 0, "height_mm": 3400}
    rect = {"x": 0, "y": 19700, "w": 3960, "d": 4100}
    kitchen = {"id": "bep_an", "type": "kitchen", "rect": dict(rect)}
    position, target, _lens = interior_camera(storey, kitchen, 1920, 1080)
    assert position[1] == pytest.approx(19700 / 1000 + 4.1 - 0.35)
    assert target[1] == pytest.approx(19700 / 1000 + 0.35)
    living = {"id": "khach", "type": "living", "rect": dict(rect)}
    position, target, _lens = interior_camera(storey, living, 1920, 1080)
    assert position[1] == pytest.approx(19700 / 1000 + 0.35)
    assert target[1] == pytest.approx(19700 / 1000 + 4.1 - 0.35)

