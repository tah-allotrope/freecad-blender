from homedesign.camera_fit import (
    basis_from_direction,
    building_bbox,
    corners_of,
    fit_distance,
    room_subject_bbox,
)


def test_fit_distance_2m_cube_margin_1():
    corners = corners_of(((-1, -1, -1), (1, 1, 1)))
    d = fit_distance(corners, (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1),
                     lens_mm=50, res_x=1920, res_y=1080, margin=1.0)
    # S4 formula, vertical constraint: at 1080p with HORIZONTAL sensor fit the
    # vertical half-FOV (atan(36*1080/(2*50*1920)) = 0.1998 rad) is narrower
    # than the horizontal, so the 1m half-height binds:
    #   1/tan(0.1998) + 1 = 5.9383
    assert abs(d - 5.93827160493827) < 1e-3


def test_fit_distance_margin_108():
    corners = corners_of(((-1, -1, -1), (1, 1, 1)))
    d = fit_distance(corners, (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1),
                     lens_mm=50, res_x=1920, res_y=1080, margin=1.08)
    assert abs(d - 5.93827160493827 * 1.08) < 1e-3


def test_square_frame_vertical_equals_horizontal():
    # At a square frame the vertical half-FOV equals the horizontal, so the
    # required distance is smaller than at 1080p where vertical binds:
    #   1/tan(atan(36/100)) + 1 = 3.7778
    corners = corners_of(((-1, -1, -1), (1, 1, 1)))
    d_wide = fit_distance(corners, (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1),
                          lens_mm=50, res_x=1920, res_y=1080, margin=1.0)
    d_square = fit_distance(corners, (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1),
                            lens_mm=50, res_x=1920, res_y=1920, margin=1.0)
    assert abs(d_square - 3.7777777777777777) < 1e-3
    assert d_wide > d_square


def test_degenerate_box_clamps_to_one():
    corners = corners_of(((0, 0, 0), (0, 0, 0)))
    d = fit_distance(corners, (0, 0, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1),
                     lens_mm=50, res_x=1920, res_y=1080)
    assert d == 1.0


def test_fit_distance_off_centre_near_corner_binds():
    # The regression test the symmetric-box suite was blind to: the depth term
    # must be SUBTRACTED (the near corner binds). The box spans y in [-1, 1]
    # while the centre sits at y = -3, so corner depths along forward=(0,1,0)
    # are 2 (near face, y=-1) and 4 (far face, y=1). tan_y = 36*1080/(2*50*1920)
    # = 0.2025, so 1/tan_y = 4.93827...; the corrected formula binds on the near
    # corner: 4.93827... - 2 = 2.93827...
    corners = corners_of(((-1, -1, -1), (1, 1, 1)))
    d = fit_distance(corners, (0, -3, 0), (0, 1, 0), (1, 0, 0), (0, 0, 1),
                     lens_mm=50, res_x=1920, res_y=1080, margin=1.0)
    # Under the old `+` sign the far corner binds and this returns 8.93827...
    assert abs(d - 2.938271604938272) < 1e-3


def test_building_bbox_tubehouse_dream():
    model = {
        "plot_width_mm": 4000, "plot_depth_mm": 25000,
        "storeys": [
            {"height_mm": 4000},
            {"height_mm": 3400},
            {"height_mm": 3400},
            {"height_mm": 3400},
            {"height_mm": 3400},
        ],
    }
    bbox = building_bbox(model)
    assert bbox[0] == (0.0, 0.0, 0.0)
    assert abs(bbox[1][0] - 4.0) < 1e-6
    assert abs(bbox[1][1] - 25.0) < 1e-6
    assert abs(bbox[1][2] - 17.6) < 1e-6  # 4.0 + 4*3.4


def test_basis_orthonormal():
    right, up = basis_from_direction((0, 1, 0))
    assert abs(_dot(right, right) - 1) < 1e-9
    assert abs(_dot(up, up) - 1) < 1e-9
    assert abs(_dot(right, up)) < 1e-9
    assert abs(_dot(right, (0, 1, 0))) < 1e-9
    assert abs(_dot(up, (0, 1, 0))) < 1e-9


def test_room_subject_bbox_includes_furniture():
    storey = {"base_z": 3200, "height_mm": 3400}
    room = {"id": "living", "type": "living", "rect": {"x": 0, "y": 0, "w": 4000, "d": 4000}}
    bbox = room_subject_bbox(storey, room)
    # Room interior extent in metres, z capped at 2.4
    assert bbox[0][0] == 0.0 and bbox[0][1] == 0.0
    assert bbox[1][0] >= 4.0 and bbox[1][1] >= 4.0
    assert abs(bbox[1][2] - (3.2 + 2.4)) < 1e-9


def _dot(a, b):
    return a[0] * b[0] + a[1] * b[1] + a[2] * b[2]
