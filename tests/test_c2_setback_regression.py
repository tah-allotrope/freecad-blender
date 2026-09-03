"""C2 regression: front setback line is drawn 18.3 m out.

Verified: front_mm=3500, plot_depth=25000 -> drew SVG y=350.0 should be 2150.0.
The old test passed by matching a dimension tick substring.
"""

import json
import re
from pathlib import Path

import ezdxf

from homedesign.compiler import compile_spec
from homedesign import plan2d

REPO_ROOT = Path(__file__).resolve().parent.parent
SPEC_PATH = REPO_ROOT / "designs" / "contractor-as-drawn.json"


def _model():
    return compile_spec(json.loads(SPEC_PATH.read_text(encoding="utf-8")))


def test_front_setback_svg_y_is_correct_on_setback_elements():
    """Front setback must be at model y=3500 -> SVG y=(25000-3500)/10=2150."""
    model = _model()
    storey = model.storeys[0]
    svg_text = plan2d._render_svg(model, storey)
    # Collect y1 from every setback group (one per line after C2 draw-model refactor)
    groups = re.findall(r'<g class="setback">.*?</g>', svg_text, re.DOTALL)
    assert groups, "no setback group in SVG"
    ys = []
    for g in groups:
        ys.extend(re.findall(r'y1="([0-9.]+)"', g))
    # Fallback for legacy single-group layout
    if len(ys) < 2:
        m = re.search(r'<g class="setback">(.*?)</g>', svg_text, re.DOTALL)
        if m:
            ys = re.findall(r'y1="([0-9.]+)"', m.group(1))
    assert len(ys) == 2, f"expected 2 setback lines, got {ys}"
    by_y = sorted(float(y) for y in ys)
    assert 250.0 in by_y, f"rear setback missing, got {by_y}"
    assert 2150.0 in by_y, f"front setback at wrong y; got {by_y} (bug draws 350.0)"


def test_front_setback_dxf_y_is_correct():
    """Front setback in DXF must land at correct flipped coordinate."""
    model = _model()
    storey = model.storeys[0]
    tmp = Path("/tmp/c2_setback_test.dxf")
    plan2d._render_dxf(model, storey, tmp)
    doc = ezdxf.readfile(tmp)
    msp = doc.modelspace()
    setback_lines = [e for e in msp if e.dxf.layer == "SETBACK" and e.dxftype() == "LINE"]
    assert len(setback_lines) == 2
    ys = sorted(round(e.dxf.start.y) for e in setback_lines)
    assert 2500 in ys, f"rear DXF y wrong: {ys}"
    assert 21500 in ys, f"front DXF y wrong (bug draws 3500): {ys}"
