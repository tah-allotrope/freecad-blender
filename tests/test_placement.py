from homedesign.placement import plan_room


def test_bedroom_gets_a_bed_that_fits():
    items = plan_room("bedroom", 4.0, 4.0)
    beds = [i for i in items if i.kind == "bed"]
    assert len(beds) == 1
    bed = beds[0]
    assert bed.x >= 0 and bed.x + bed.w <= 4.0
    assert bed.y >= 0 and bed.y + bed.d <= 4.0


def test_small_bathroom_gets_only_wc():
    items = plan_room("bathroom", 1.2, 1.2)
    kinds = {i.kind for i in items}
    assert "wc" in kinds
    assert "shower" not in kinds


def test_large_bathroom_gets_shower_and_basin():
    items = plan_room("bathroom", 3.0, 2.5)
    kinds = {i.kind for i in items}
    assert {"wc", "basin", "shower"} <= kinds


def test_kitchen_run_never_exceeds_room_width():
    items = plan_room("kitchen", 4.0, 4.0)
    run = next(i for i in items if i.kind == "kitchen_run")
    assert run.x + run.w <= 4.0


def test_living_room_gets_dining_set_when_large_enough():
    items = plan_room("living", 6.0, 4.0)
    kinds = [i.kind for i in items]
    assert "sofa" in kinds
    assert "dining_table" in kinds
    assert kinds.count("chair") == 4


def test_unknown_room_type_gets_no_furniture():
    assert plan_room("garage", 4.0, 4.0) == []


def test_all_items_stay_within_room_bounds():
    for room_type, w, d in [("bedroom", 3.0, 3.5), ("kitchen", 3.5, 3.0), ("living", 5.0, 4.0), ("office", 2.5, 2.5)]:
        for item in plan_room(room_type, w, d):
            assert -0.01 <= item.x
            assert item.x + item.w <= w + 0.01
            assert -0.01 <= item.y
            assert item.y + item.d <= d + 0.01


def test_shallow_bedroom_rotates_bed_90_degrees():
    """A bed too long for a shallow room rotates 90deg: w/d stay semantic and
    the rotation carries the orientation (TASK-03-09)."""
    items = plan_room("bedroom", 4.0, 2.2)
    bed = next(i for i in items if i.kind == "bed")
    assert bed.rot_deg == 90
    assert bed.w == 1.6
    assert bed.d == 2.0
    # Rotated footprint fits the room: d becomes the width direction.
    assert bed.x >= 0 and bed.x + bed.d <= 4.0
    assert bed.y >= 0 and bed.y + bed.w <= 2.2


def test_garage_gets_a_car_when_it_fits():
    items = plan_room("garage", 4.0, 6.0)
    cars = [i for i in items if i.kind == "car"]
    assert len(cars) == 1
    car = cars[0]
    assert car.w <= 4.0 and car.d <= 6.0


def test_garage_too_small_is_empty():
    assert plan_room("garage", 2.0, 2.0) == []


def test_hall_narrow_is_empty():
    assert plan_room("hall", 0.9, 4.0) == []


def test_hall_gets_console():
    items = plan_room("hall", 2.0, 4.0)
    consoles = [i for i in items if i.kind == "console"]
    assert len(consoles) == 1


def test_terrace_gets_two_chairs_and_planter():
    items = plan_room("terrace", 3.0, 3.0)
    kinds = [i.kind for i in items]
    assert kinds.count("chair") == 2
    assert kinds.count("planter") == 1
    assert len(items) == 3


def test_wc_gets_wc_and_basin_no_shower():
    items = plan_room("wc", 1.6, 2.0)
    assert {i.kind for i in items} == {"wc", "basin"}


def test_new_room_types_stay_within_bounds():
    for room_type in ("hall", "storage", "utility", "garage", "balcony", "terrace", "wc"):
        for w, d in [(1.0, 1.0), (2.0, 3.0), (4.0, 6.0), (8.0, 10.0)]:
            for item in plan_room(room_type, w, d):
                assert item.x >= -1e-9 and item.y >= -1e-9
                assert item.x + item.w <= w + 1e-9
                assert item.y + item.d <= d + 1e-9
