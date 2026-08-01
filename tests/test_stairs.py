import pytest

from homedesign.errors import SpecError
from homedesign.model import Rect, Room
from homedesign.stairs import derive_stairs, stair_sizing, straight_minimum, u_return_minimum


def test_stair_sizing_3400():
    n, r, g = stair_sizing(3400)
    assert n == 19
    assert r == pytest.approx(178.94736842105263)
    assert g == pytest.approx(250.0)
    assert 600 <= 2 * r + g <= 640


def test_stair_sizing_4000():
    n, r, g = stair_sizing(4000)
    assert n == 23
    assert r == pytest.approx(173.91304347826087)
    assert g == pytest.approx(252.17391304347825)
    assert (2 * r + g) == pytest.approx(600.0, abs=1e-6)


def test_straight_and_u_return_minimums():
    assert straight_minimum(3400) == pytest.approx((900.0, 4500.0))
    assert u_return_minimum(3400) == pytest.approx((1900.0, 3150.0))
    w, d = u_return_minimum(4000)
    assert w == pytest.approx(1900.0)
    assert d == pytest.approx(3674.0, abs=0.5)


def _room(shaft_w, shaft_d, room_id="stair"):
    return Room(id=room_id, type="stairwell", rect=Rect(x=0, y=0, w=shaft_w, d=shaft_d))


def test_shaft_too_small_error_names_both_minimums():
    errors: list[SpecError] = []
    result = derive_stairs(
        {"room": "stair", "mode": "auto"}, [_room(1100, 1300)], 3400, 0, "storeys[0]", errors
    )
    assert result is None
    assert len(errors) == 1
    assert errors[0].code == "stair_shaft_too_small"
    assert "900x4500" in errors[0].message
    assert "1900x3150" in errors[0].message


def test_straight_flight_generation():
    errors: list[SpecError] = []
    n, r, _g = stair_sizing(3400)
    result = derive_stairs(
        {"room": "stair", "mode": "auto"}, [_room(900, 4600)], 3400, 0, "storeys[0]", errors
    )
    assert errors == []
    assert result is not None
    assert len(result.treads) == 18
    assert result.treads[0].z == pytest.approx(r)
    assert result.treads[-1].z == pytest.approx((n - 1) * r, abs=1e-6)
    for t in result.treads:
        assert t.d == pytest.approx(250.0)
        assert t.w == pytest.approx(900.0)


def test_u_return_generation():
    errors: list[SpecError] = []
    result = derive_stairs(
        {"room": "stair", "mode": "auto"}, [_room(1900, 3200)], 3400, 0, "storeys[0]", errors
    )
    assert errors == []
    assert result is not None
    assert len(result.treads) == 19
    lower = result.treads[:9]
    landing = result.treads[9]
    upper = result.treads[9:]
    assert landing.w == pytest.approx(1900.0)
    assert landing.d == pytest.approx(950.0)
    for t in lower:
        assert t.x == pytest.approx(0.0)
        assert t.w == pytest.approx(900.0)
    for t in upper[1:]:
        assert t.x == pytest.approx(1000.0)
        assert t.w == pytest.approx(900.0)
    assert result.treads[-1].z == pytest.approx(3400.0, abs=1e-6)


def test_mode_none_returns_none_no_error():
    errors: list[SpecError] = []
    result = derive_stairs(
        {"room": "stair", "mode": "none"}, [_room(1100, 1300)], 3400, 0, "storeys[0]", errors
    )
    assert result is None
    assert errors == []


def test_explicit_mode_does_not_fall_back():
    errors: list[SpecError] = []
    result = derive_stairs(
        {"room": "stair", "mode": "straight"}, [_room(1900, 3200)], 3400, 0, "storeys[0]", errors
    )
    assert result is None
    assert len(errors) == 1
    assert errors[0].code == "stair_shaft_too_small"
