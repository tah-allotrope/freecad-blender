import json
from pathlib import Path

import pytest

from homedesign.compiler import compile_spec, resolve_opening_offset
from homedesign.errors import SpecValidationError

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "spec" / "examples"


def load_example(name):
    return json.loads((EXAMPLES / name).read_text())


def _spec_with_openings(openings, rooms=None, plot="5000x10000"):
    plot_w, plot_d = map(int, plot.split("x"))
    return {
        "meta": {"name": "t", "style": "modern-minimal", "views": []},
        "site": {"plot_width_mm": plot_w, "plot_depth_mm": plot_d},
        "storeys": [
            {
                "level": 0,
                "name": "G",
                "height_mm": 3000,
                "rooms": rooms or [
                    # Long north wall (5000) so the 3000 door + 1000 window
                    # both fit and the overlap predicate is what's tested.
                    {"id": "a", "type": "living", "rect": {"x": 0, "y": 0, "w": 5000, "d": 3000}},
                    {"id": "b", "type": "bedroom", "rect": {"x": 0, "y": 3000, "w": 5000, "d": 3000}},
                ],
                "openings": openings,
            }
        ],
    }


def test_resolve_opening_offset_center():
    assert resolve_opening_offset(3000, 900, "center", None) == 1050.0


def test_resolve_opening_offset_start():
    assert resolve_opening_offset(3000, 900, "start", None) == 0.0


def test_resolve_opening_offset_end():
    assert resolve_opening_offset(3000, 900, "end", None) == 2100.0


def test_resolve_opening_offset_explicit_wins():
    assert resolve_opening_offset(3000, 900, "center", 250) == 250.0


def test_overlapping_openings_raise():
    # Exact real defect from tubehouse-dream level 0: 3000mm door at offset
    # 500 + 1000mm window at offset 1500 on the same wall.
    openings = [
        {"type": "door", "between": ["a", "exterior"], "side": "north", "width_mm": 3000, "offset_mm": 500},
        {"type": "window", "between": ["a", "exterior"], "side": "north", "width_mm": 1000, "sill_mm": 1800, "head_mm": 2100, "offset_mm": 1500},
    ]
    with pytest.raises(SpecValidationError) as exc:
        compile_spec(_spec_with_openings(openings))
    assert any(e.code == "opening_overlap" for e in exc.value.errors)


def test_moved_window_compiles():
    openings = [
        {"type": "door", "between": ["a", "exterior"], "side": "north", "width_mm": 3000, "offset_mm": 500},
        {"type": "window", "between": ["a", "exterior"], "side": "north", "width_mm": 1000, "sill_mm": 1800, "head_mm": 2100, "offset_mm": 3600},
    ]
    # 3600+1000=4600 > wall span 4000 would be opening_out_of_wall; use a
    # wall long enough so the point being tested is overlap, not fit.
    rooms = [
        {"id": "a", "type": "living", "rect": {"x": 0, "y": 0, "w": 5000, "d": 3000}},
        {"id": "b", "type": "bedroom", "rect": {"x": 0, "y": 3000, "w": 5000, "d": 3000}},
    ]
    model = compile_spec(_spec_with_openings(openings, rooms=rooms, plot="5000x10000"))
    assert model is not None


def test_touching_in_plan_but_not_elevation_compiles():
    # Overlap in plan but only touching in elevation (window sill 2100 == door
    # head 2100) -> the 1mm slack permits it.
    openings = [
        {"type": "door", "between": ["a", "exterior"], "side": "north", "width_mm": 1000, "offset_mm": 500, "head_mm": 2100},
        {"type": "window", "between": ["a", "exterior"], "side": "north", "width_mm": 1000, "sill_mm": 2100, "head_mm": 2400, "offset_mm": 1500},
    ]
    model = compile_spec(_spec_with_openings(openings))
    assert model is not None


def test_opening_out_of_wall():
    # offset 3500 + width 900 = 4400 > 3000 wall span -> opening_out_of_wall.
    rooms = [
        {"id": "a", "type": "living", "rect": {"x": 0, "y": 0, "w": 3000, "d": 3000}},
        {"id": "b", "type": "bedroom", "rect": {"x": 0, "y": 3000, "w": 3000, "d": 3000}},
    ]
    openings = [
        {"type": "window", "between": ["a", "exterior"], "side": "north", "width_mm": 900, "offset_mm": 3500},
    ]
    with pytest.raises(SpecValidationError) as exc:
        compile_spec(_spec_with_openings(openings, rooms=rooms))
    assert any(e.code == "opening_out_of_wall" for e in exc.value.errors)
