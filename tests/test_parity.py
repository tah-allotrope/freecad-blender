import json
import pathlib
import pytest

from homedesign.compiler import compile_spec
from homedesign.parity import (
    TOLERANCE_MM,
    elevation_parity_report,
    opening_deviation,
    silhouette_bounds,
    silhouette_deviation,
)


def test_silhouette_bounds_single():
    assert silhouette_bounds([{"x_mm": 0, "y_mm": 0, "w_mm": 3960, "h_mm": 23800}]) == (
        0.0,
        0.0,
        3960.0,
        23800.0,
    )


def test_silhouette_deviation_identity():
    r = [{"x_mm": 0, "y_mm": 0, "w_mm": 1000, "h_mm": 1000}]
    assert silhouette_deviation(r, r) == 0.0


def test_silhouette_deviation_40():
    a = [{"x_mm": 0, "y_mm": 0, "w_mm": 1000, "h_mm": 1000}]
    b = [{"x_mm": 0, "y_mm": 0, "w_mm": 1040, "h_mm": 1000}]
    assert silhouette_deviation(a, b) == 40.0


def test_empty_candidate_raises():
    spec = json.loads(pathlib.Path("designs/contractor-as-drawn.json").read_text(encoding="utf-8"))
    model = compile_spec(spec)
    from homedesign import parity

    orig = parity._candidate_rects
    parity._candidate_rects = lambda m, s: []
    try:
        with pytest.raises(ValueError, match="south"):
            parity.elevation_parity_report(model, "south")
    finally:
        parity._candidate_rects = orig

def test_unmatched_opening_fails():
    ref = [{"x_mm": 0, "y_mm": 0, "w_mm": 100, "h_mm": 100, "id": "a:0"}]
    cand: list[dict] = []
    dev, unmatched = opening_deviation(ref, cand, set())
    assert dev == 0.0
    assert "a:0" in unmatched


def test_elevation_parity_contractor_south():
    spec = json.loads(pathlib.Path("designs/contractor-as-drawn.json").read_text(encoding="utf-8"))
    model = compile_spec(spec)
    # three deliberate deviations excluded by name (ledger a,c,g) - use empty here but test must pass with empty exclude
    # actual excluded ids would be named, but passing without them should still pass because current model is faithful within tolerance
    report = elevation_parity_report(model, "south", tolerance_mm=TOLERANCE_MM, exclude=set())
    assert report["passed"] is True
    assert report["silhouette_mm"] <= 50.0
    assert report["opening_mm"] <= 50.0
    assert report["unmatched"] == []


def test_elevation_parity_exclude():
    ref = [
        {"x_mm": 0, "y_mm": 0, "w_mm": 100, "h_mm": 100, "id": "a:0"},
        {"x_mm": 200, "y_mm": 0, "w_mm": 100, "h_mm": 100, "id": "b:0"},
    ]
    cand = [{"x_mm": 0, "y_mm": 0, "w_mm": 100, "h_mm": 100, "id": "a:0"}]
    dev, unmatched = opening_deviation(ref, cand, exclude={"b:0"})
    assert unmatched == []
    assert dev == 0.0
