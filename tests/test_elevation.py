"""Elevation and section draw-model + writer tests (PHASE-04). Pure Python."""
import json
from pathlib import Path

import ezdxf

from homedesign.compiler import compile_spec
from homedesign.elevation import (
    build_elevation,
    build_section,
    write_elevations,
    write_sections,
)

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "spec" / "examples"
DESIGNS = REPO_ROOT / "designs"


def load_example(name):
    return json.loads((EXAMPLES / name).read_text())


def load_design(name):
    return json.loads((DESIGNS / name).read_text(encoding="utf-8"))


def _mini():
    return compile_spec(load_example("tubehouse-mini.json"))


def _demo():
    return compile_spec(load_example("demo-3br-2storey.json"))


def test_north_elevation_has_a_wall_per_storey_and_full_height():
    model = _mini()
    items = build_elevation(model, "north")
    walls = [i for i in items if i["kind"] == "wall"]
    assert len(walls) >= len(model.storeys)
    total_h = sum(s.height_mm for s in model.storeys)
    # The wall stack reaches the full storey height; the flat roof (a separate
    # primitive) sits above it.
    assert max(i["z"] + i["h"] for i in walls) == total_h


def test_elevation_openings_sit_within_their_walls():
    # tubehouse-mini's exterior openings sit on the west (x=0) facade, which is
    # the longest exterior wall the opening placer prefers.
    model = _mini()
    items = build_elevation(model, "west")
    openings = [i for i in items if i["kind"] == "opening"]
    assert openings
    for o in openings:
        storey = next(s for s in model.storeys if o["z"] >= s.base_z and o["z"] < s.base_z + s.height_mm)
        assert storey.base_z <= o["z"] and o["z"] + o["h"] <= storey.base_z + storey.height_mm


def test_east_elevation_uses_model_y_axis():
    model = _mini()
    items = build_elevation(model, "east")
    depth = model.plot_depth_mm
    # The ground line spans the full canvas: plot *depth* (model y), not width.
    ground = next(i for i in items if i["kind"] == "ground")
    assert ground["w"] == depth
    # The facade walls (nearest depth) tile the full plot depth along the
    # model-y axis.
    walls = [i for i in items if i["kind"] == "wall"]
    nearest_depth = min(w["depth"] for w in walls)
    facade = [w for w in walls if w["depth"] == nearest_depth]
    assert min(w["x"] for w in facade) <= 1.0
    assert max(w["x"] + w["w"] for w in facade) >= depth - 1.0


def test_section_cuts_every_storey_slab_and_only_cut_walls():
    model = _demo()
    items = build_section(model, "x", 5000.0)
    slabs = [i for i in items if i["kind"] == "cut_slab"]
    assert len(slabs) >= len(model.storeys)
    walls = [w for s in model.storeys for w in s.walls]
    for w in (i for i in items if i["kind"] == "cut_wall"):
        matched = [
            ww for ww in walls
            if ww.y == w["x"] and ww.h == w["w"] and ww.x < 5000.0 < ww.x + ww.w
        ]
        assert matched, f"cut wall at x={w['x']} w={w['w']} has no backing wall containing x=5000"


def test_section_outside_plot_returns_only_ground():
    # A plane clearly outside the plot (far past the 100mm centre-aligned wall
    # overhang) cuts nothing.
    model = _demo()
    items = build_section(model, "x", -1000.0)
    assert [i["kind"] for i in items] == ["ground"]


def test_write_elevations_and_sections_produce_valid_files(tmp_path):
    model = _mini()
    elev_paths = write_elevations(model, tmp_path)
    assert len(elev_paths) == 8  # 4 SVG + 4 DXF
    for p in elev_paths:
        assert p.exists()
        if p.suffix == ".svg":
            import xml.etree.ElementTree as ET
            ET.parse(p)  # must be well-formed XML
        else:
            ezdxf.readfile(p)
    sect_paths = write_sections(model, tmp_path)
    assert len(sect_paths) == 4  # 2 SVG + 2 DXF
    for p in sect_paths:
        assert p.exists()


def _contractor():
    return compile_spec(load_design("contractor-as-drawn.json"))


def test_contractor_north_elevation_is_not_blank():
    model = _contractor()
    items = build_elevation(model, "north")
    kinds = [i["kind"] for i in items]
    assert "wall" in kinds
    assert "opening" in kinds


def test_contractor_all_four_elevations_have_walls():
    model = _contractor()
    for side in ("north", "south", "east", "west"):
        items = build_elevation(model, side)
        assert any(i["kind"] == "wall" for i in items), side


def test_contractor_openings_appear_across_elevations():
    model = _contractor()
    total = sum(
        sum(1 for i in build_elevation(model, side) if i["kind"] == "opening")
        for side in ("north", "south", "east", "west")
    )
    assert total >= 101


def test_tubehouse_mini_south_elevation_has_openings():
    model = _mini()
    items = build_elevation(model, "south")
    assert any(i["kind"] == "opening" for i in items)


def test_walls_are_painter_sorted_farthest_first():
    model = _contractor()
    walls = [i for i in build_elevation(model, "north") if i["kind"] == "wall"]
    depths = [w["depth"] for w in walls]
    for a, b in zip(depths, depths[1:]):
        assert a >= b - 1.0


def test_elevation_horizontal_mirroring_north_vs_south():
    model = _demo()
    north = build_elevation(model, "north")
    south = build_elevation(model, "south")
    target = next(
        w for s in model.storeys for w in s.walls
        if w.orientation == "vertical" and 3900 < w.x + w.w / 2 < 4100
    )
    n = [i for i in north if i["kind"] == "wall" and abs(i["x"] - target.x) < 1]
    s = [i for i in south if i["kind"] == "wall"
         and abs(i["x"] - (model.plot_width_mm - target.x - target.w)) < 1]
    assert n, "partition wall missing from north elevation"
    assert s, "mirrored partition wall missing from south elevation"
    for item in n:
        assert abs(item["x"] - target.x) < 1
    for item in s:
        assert abs(item["x"] + target.x + target.w - model.plot_width_mm) < 1


def test_openings_stay_inside_their_host_wall():
    model = _contractor()
    for side in ("north", "south", "east", "west"):
        items = build_elevation(model, side)
        walls = [i for i in items if i["kind"] == "wall"]
        for o in (i for i in items if i["kind"] == "opening"):
            assert any(
                w["x"] <= o["x"] and o["x"] + o["w"] <= w["x"] + w["w"] + 1
                for w in walls
            ), f"{side}: opening {o['x']},{o['w']} not within any wall"


def test_gable_roof_projects_as_triangle_on_gable_end():
    import math

    model = _demo()
    items = build_elevation(model, "north")
    roofs = [i for i in items if i["kind"] == "roof"]
    assert len(roofs) == 1
    roof = roofs[0]
    assert len(roof["points"]) == 3
    model_roof = model.storeys[1].roof
    rise = (model_roof.w / 2) * math.tan(math.radians(model_roof.pitch_deg))
    assert max(z for _, z in roof["points"]) == model_roof.base_z + rise


def test_gable_roof_projects_as_rectangle_on_eave_side():
    model = _demo()
    items = build_elevation(model, "east")
    roofs = [i for i in items if i["kind"] == "roof"]
    assert len(roofs) == 1
    assert len(roofs[0]["points"]) == 4


def test_tubehouse_dream_north_elevation_has_parapets():
    model = compile_spec(load_design("tubehouse-dream.json"))
    items = build_elevation(model, "north")
    parapets = [i for i in items if i["kind"] == "parapet"]
    assert parapets
    assert any(i["h"] == 1100.0 for i in parapets)


def test_all_example_elevations_produce_valid_files(tmp_path):
    import xml.etree.ElementTree as ET

    for name in ("courtyard-fixture.json", "demo-3br-2storey.json", "tubehouse-mini.json"):
        model = compile_spec(load_example(name))
        paths = write_elevations(model, tmp_path)
        for p in paths:
            if p.suffix == ".svg":
                ET.parse(p)
            else:
                ezdxf.readfile(p)


def test_outline_within_canvas_for_all_sides_and_specs():
    specs = (
        [load_example(n) for n in ("courtyard-fixture.json", "demo-3br-2storey.json", "tubehouse-mini.json")]
        + [load_design(n) for n in ("tubehouse-dream.json", "contractor-as-drawn.json")]
    )
    for spec in specs:
        model = compile_spec(spec)
        for side in ("north", "south", "east", "west"):
            items = build_elevation(model, side)
            outline = next(i for i in items if i["kind"] == "outline")
            canvas = model.plot_width_mm if side in ("north", "south") else model.plot_depth_mm
            assert outline["x"] >= 0
            assert outline["x"] + outline["w"] <= canvas + 1


def test_contractor_roof_structure_appears_on_west_elevation():
    model = _contractor()
    items = build_elevation(model, "west")
    structures = [i for i in items if i["kind"] == "structure"]
    assert len(structures) == 1
    assert structures[0]["h"] == 2000.0


def test_level_labels_include_metres():
    import re

    model = _contractor()
    items = build_elevation(model, "north")
    levels = [i for i in items if i["kind"] == "level"]
    assert levels
    for lvl in levels:
        assert re.search(r".+\s\+\d+\.\d{3}$", lvl["label"]), lvl["label"]
    assert any(lvl["label"].endswith("+3.800") for lvl in levels)


def test_named_sections_produce_named_files(tmp_path):
    model = _contractor()
    paths = write_sections(model, tmp_path)
    names = {p.name for p in paths}
    assert "contractor-as-drawn_section_long.svg" in names
    assert "contractor-as-drawn_section_cross_bed.svg" in names
    assert len(paths) == 4


def test_no_sections_keep_legacy_names(tmp_path):
    model = _mini()
    paths = write_sections(model, tmp_path)
    names = {p.name for p in paths}
    assert "tubehouse-mini_section_x.svg" in names
    assert "tubehouse-mini_section_y.svg" in names
    assert len(paths) == 4
