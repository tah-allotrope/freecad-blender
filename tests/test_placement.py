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
