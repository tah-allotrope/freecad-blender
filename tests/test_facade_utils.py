import pytest
from homedesign.facade import opening_division_lines, resolve_facade_element

def test_division_three_columns():
    bars = opening_division_lines(2000, 1400, {"columns": 3, "rows": 1, "mullion_mm": 50, "transom_mm": 50})
    assert len(bars) == 2
    # glass_w = (2000-100)/3 = 633.333
    assert bars[0]["x_mm"] == pytest.approx(633.333, abs=0.01)
    assert bars[0]["w_mm"] == 50.0
    assert bars[0]["y_mm"] == 0.0
    assert bars[0]["h_mm"] == 1400
    assert bars[1]["x_mm"] == pytest.approx(1316.667, abs=0.01)

def test_division_one_by_one_empty():
    assert opening_division_lines(2000, 1400, {"columns": 1, "rows": 1}) == []

def test_division_two_by_two():
    bars = opening_division_lines(1200, 2400, {"columns": 2, "rows": 2, "mullion_mm": 60, "transom_mm": 40})
    assert len(bars) == 2
    # find vertical and horizontal
    vert = [b for b in bars if b["w_mm"] == 60.0][0]
    horiz = [b for b in bars if b["h_mm"] == 40.0][0]
    assert vert["x_mm"] == pytest.approx(570.0)
    assert vert["h_mm"] == 2400
    assert horiz["y_mm"] == pytest.approx(1180.0)
    assert horiz["w_mm"] == 1200
    assert horiz["x_mm"] == 0.0

def test_resolve_column_south_proud():
    el = {"kind": "column", "side": "south", "x_mm": 500, "z_mm": 0, "w_mm": 300, "h_mm": 3400, "projection_mm": 300, "storey_level": 0}
    r = resolve_facade_element(el, 0.0, 4000.0, 20000.0)
    assert r["x_mm"] == 500
    assert r["y_mm"] == 20000
    assert r["z_mm"] == 0.0
    assert r["w_mm"] == 300
    assert r["d_mm"] == 300
    assert r["h_mm"] == 3400
    assert r["finish"] == "facade_trim"

def test_resolve_panel_recessed_south():
    el = {"kind": "panel", "side": "south", "x_mm": 0, "z_mm": 100, "w_mm": 1000, "h_mm": 500, "projection_mm": -80, "storey_level": 2}
    r = resolve_facade_element(el, 7200.0, 4000.0, 20000.0)
    assert r["y_mm"] == 19920
    assert r["d_mm"] == 80
    assert r["z_mm"] == 7300.0
    assert r["finish"] == "facade_field"

def test_resolve_zero_projection_min_depth():
    el = {"kind": "fin", "side": "south", "x_mm": 0, "z_mm": 0, "w_mm": 100, "h_mm": 1000, "projection_mm": 0}
    r = resolve_facade_element(el, 0, 4000, 20000)
    assert r["d_mm"] == 10
