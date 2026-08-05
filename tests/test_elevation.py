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


def load_example(name):
    return json.loads((EXAMPLES / name).read_text())


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
    assert max(i["z"] + i["h"] for i in items) == total_h


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
    for i in items:
        assert 0.0 <= i["x"] <= depth, f"east elevation item x={i['x']} outside plot depth"
        assert 0.0 <= i["x"] + i["w"] <= depth + 1e-6


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
