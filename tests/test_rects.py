from homedesign.rects import subtract_rects


def test_subtract_rects_center_hole_area_conserved():
    fragments = subtract_rects(0, 0, 4000, 4000, [(1000, 1000, 1000, 1000)])
    assert len(fragments) == 4
    area = sum(w * d for _x, _y, w, d in fragments)
    assert area == 4000 * 4000 - 1000 * 1000


def test_subtract_rects_no_holes():
    assert subtract_rects(0, 0, 4000, 4000, []) == [(0, 0, 4000, 4000)]


def test_subtract_rects_non_intersecting_hole():
    assert subtract_rects(0, 0, 1000, 1000, [(5000, 5000, 100, 100)]) == [(0, 0, 1000, 1000)]
