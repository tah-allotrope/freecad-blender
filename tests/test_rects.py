from homedesign.model import Rect
from homedesign.rects import open_edges, subtract_rects


def test_subtract_rects_center_hole_area_conserved():
    fragments = subtract_rects(0, 0, 4000, 4000, [(1000, 1000, 1000, 1000)])
    assert len(fragments) == 4
    area = sum(w * d for _x, _y, w, d in fragments)
    assert area == 4000 * 4000 - 1000 * 1000


def test_subtract_rects_no_holes():
    assert subtract_rects(0, 0, 4000, 4000, []) == [(0, 0, 4000, 4000)]


def test_subtract_rects_non_intersecting_hole():
    assert subtract_rects(0, 0, 1000, 1000, [(5000, 5000, 100, 100)]) == [(0, 0, 1000, 1000)]


def test_open_edges_shared_south():
    a = Rect(x=0, y=0, w=4000, d=3000)
    b = Rect(x=0, y=3000, w=4000, d=2000)
    assert open_edges(a, [b]) == {"north", "east", "west"}


def test_open_edges_none_shared():
    a = Rect(x=0, y=0, w=4000, d=3000)
    assert open_edges(a, []) == {"north", "south", "east", "west"}


def test_open_edges_one_mm_gap_is_open():
    # A 1mm gap sits outside the 1mm coincidence tolerance (eps is strict <).
    a = Rect(x=0, y=0, w=4000, d=3000)
    b = Rect(x=0, y=3001, w=4000, d=2000)
    assert open_edges(a, [b]) == {"north", "south", "east", "west"}
