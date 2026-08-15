"""Pure unit tests for wall-face rectangle subtraction (PHASE-04, S4)."""
import json
from pathlib import Path

from homedesign.compiler import compile_spec
from homedesign.rects import wall_face_fragments

REPO_ROOT = Path(__file__).resolve().parent.parent


def _area(fragments):
    return sum(w * h for _, _, w, h in fragments)


def test_empty_openings_return_full_face():
    assert wall_face_fragments(4000, 3000, []) == [(0.0, 0.0, 4000.0, 3000.0)]


def test_single_centered_window_produces_four_fragments():
    fragments = wall_face_fragments(4000, 3000, [(1000, 900, 1200, 1200)])
    assert len(fragments) == 4
    assert abs(_area(fragments) - (4000 * 3000 - 1200 * 1200)) < 1.0
    under = [f for f in fragments if f[1] == 0.0 and abs(f[3] - 900.0) < 1e-6]
    over = [f for f in fragments if abs(f[1] - 2100.0) < 1e-6 and abs(f[3] - 900.0) < 1e-6]
    assert any(abs(f[2] - 4000.0) < 1e-6 for f in under)
    assert any(abs(f[2] - 4000.0) < 1e-6 for f in over)


def test_door_at_floor_has_no_full_width_under_sill_band():
    fragments = wall_face_fragments(4000, 3000, [(1000, 0, 900, 2100)])
    assert not any(f[1] == 0.0 and abs(f[2] - 4000.0) < 1e-6 for f in fragments)
    assert abs(_area(fragments) - (4000 * 3000 - 900 * 2100)) < 1.0


def test_full_height_full_width_opening_empties_wall():
    assert wall_face_fragments(4000, 3000, [(0, 0, 4000, 3000)]) == []


def test_two_windows_have_correct_area_and_positive_fragments():
    fragments = wall_face_fragments(6000, 3000, [(500, 900, 1000, 1200), (3000, 900, 1000, 1200)])
    assert abs(_area(fragments) - (6000 * 3000 - 2 * (1000 * 1200))) < 1.0
    assert all(w > 0 and h > 0 for _, _, w, h in fragments)


def _overlap(a, b):
    w = max(0.0, min(a[0] + a[2], b[0] + b[2]) - max(a[0], b[0]))
    h = max(0.0, min(a[1] + a[3], b[1] + b[3]) - max(a[1], b[1]))
    return w * h


def _design_walls():
    for name in ("contractor-as-drawn.json", "tubehouse-dream.json"):
        spec = json.loads((REPO_ROOT / "designs" / name).read_text(encoding="utf-8"))
        model = compile_spec(spec)
        for storey in model.storeys:
            for wall in storey.walls:
                span = wall.h if wall.orientation == "vertical" else wall.w
                holes = [
                    (o.offset_mm, o.sill_mm, o.width_mm, o.head_mm - o.sill_mm)
                    for o in storey.openings if o.wall_id == wall.id
                ]
                yield name, storey, wall, span, holes


def test_area_identity_over_shipped_designs():
    for name, storey, wall, span, holes in _design_walls():
        fragments = wall_face_fragments(span, storey.height_mm, holes)
        expected = span * storey.height_mm - sum(w * h for _, _, w, h in holes)
        assert abs(_area(fragments) - expected) < 1.0, f"{name} wall {wall.id}"


def test_no_fragments_overlap():
    for name, storey, wall, span, holes in _design_walls():
        fragments = wall_face_fragments(span, storey.height_mm, holes)
        for i, a in enumerate(fragments):
            for b in fragments[i + 1:]:
                assert _overlap(a, b) <= 1.0, f"{name} wall {wall.id} fragments overlap"
