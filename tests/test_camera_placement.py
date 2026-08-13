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
