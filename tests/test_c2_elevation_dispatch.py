"""C2: elevation writers must be exhaustive and handle outline."""

import json
from pathlib import Path

import pytest

from homedesign.compiler import compile_spec
from homedesign.elevation import build_elevation, build_section, _svg, _dxf


def _model():
    spec = json.loads(Path("designs/contractor-as-drawn.json").read_text(encoding="utf-8"))
    return compile_spec(spec)


def test_elevation_svg_and_dxf_handle_all_kinds():
    model = _model()
    kinds = set()
    for side in ("north", "south", "east", "west"):
        for it in build_elevation(model, side):
            kinds.add(it["kind"])
    for sec in (model.sections or []):
        # build_section uses axis/position
        for it in build_section(model, sec.get("axis", "x"), float(sec.get("position_mm", 0))):
            kinds.add(it["kind"])
    # Also check that writers handle each kind without dropping
    # Collect kinds that each writer explicitly handles (by inspecting source)
    # Instead, exercise the writers with one item of each kind.
    for kind in kinds:
        # Build a minimal item of that kind
        item = {"kind": kind, "x": 0, "z": 0, "w": 100, "h": 100, "label": "test", "type": "door", "points": [(0, 0), (100, 0), (100, 100), (0, 100)]}
        # SVG should not raise for known kinds
        try:
            _svg([item], "test", 1000, 1000)
        except ValueError as e:
            if "unknown primitive" in str(e):
                pytest.fail(f"SVG writer missing kind {kind!r}: {e}")
        # DXF should not raise for known kinds (outline now handled)
        # we test via temp file
        import tempfile
        with tempfile.TemporaryDirectory() as tmp:
            out = Path(tmp) / "out.dxf"
            try:
                _dxf([item], out)
            except ValueError as e:
                if "unknown primitive" in str(e):
                    pytest.fail(f"DXF writer missing kind {kind!r}: {e}")


def test_elevation_unknown_kind_raises():
    import tempfile
    from pathlib import Path
    bad = [{"kind": "not_a_real_kind", "x": 0, "z": 0, "w": 10, "h": 10}]
    with pytest.raises(ValueError, match="unknown primitive"):
        _svg(bad, "test", 100, 100)
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.dxf"
        with pytest.raises(ValueError, match="unknown primitive"):
            _dxf(bad, out)


def test_outline_handled_by_both_writers():
    # outline is the kind that SVG handled but DXF previously dropped
    item = {"kind": "outline", "x": 0, "z": 0, "w": 100, "h": 100}
    _svg([item], "test", 1000, 1000)
    import tempfile
    with tempfile.TemporaryDirectory() as tmp:
        out = Path(tmp) / "out.dxf"
        _dxf([item], out)
        assert out.exists()
