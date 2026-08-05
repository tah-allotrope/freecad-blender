import json
from pathlib import Path

import ezdxf

from homedesign.compiler import compile_spec
from homedesign import plan2d

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "spec" / "examples"


def load_model(name):
    spec = json.loads((EXAMPLES / name).read_text())
    return compile_spec(spec)


def test_write_plans_creates_svg_and_dxf_per_storey(tmp_path):
    model = load_model("demo-3br-2storey.json")
    paths = plan2d.write_plans(model, tmp_path)
    svgs = [p for p in paths if p.suffix == ".svg"]
    dxfs = [p for p in paths if p.suffix == ".dxf"]
    # The complete drawing set: one plan per storey + four elevations + two
    # sections, each in SVG and DXF.
    drawing_units = len(model.storeys) + 6
    assert len(svgs) == drawing_units
    assert len(dxfs) == drawing_units
    assert len(paths) == 2 * drawing_units
    for p in paths:
        assert p.exists()


def test_svg_contains_every_room_id(tmp_path):
    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    ground = model.storeys[0]
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text()
    for room in ground.rooms:
        assert room.id in svg_text


def test_svg_marks_doors_and_windows_distinctly(tmp_path):
    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text()
    assert "#c0392b" in svg_text  # door color
    assert "#3a7bd5" in svg_text  # window color


def test_dxf_has_wall_door_window_layers_with_content(tmp_path):
    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    doc = ezdxf.readfile(tmp_path / "dxf" / f"{model.name}_f0.dxf")
    msp = doc.modelspace()
    layers_used = {e.dxf.layer for e in msp}
    assert "WALLS" in layers_used
    assert "DOORS" in layers_used
    assert "WINDOWS" in layers_used
    assert "STAIRS" in layers_used
    wall_entities = [e for e in msp if e.dxf.layer == "WALLS"]
    assert len(wall_entities) == len(model.storeys[0].walls)


def test_dxf_stairs_layer_has_one_polyline_per_tread(tmp_path):
    model = load_model("tubehouse-mini.json")
    plan2d.write_plans(model, tmp_path)
    doc = ezdxf.readfile(tmp_path / "dxf" / f"{model.name}_f0.dxf")
    msp = doc.modelspace()
    stair_entities = [e for e in msp if e.dxf.layer == "STAIRS"]
    assert len(stair_entities) == len(model.storeys[0].stairs.treads)


def test_svg_root_has_viewbox_and_no_fixed_size(tmp_path):
    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text()
    root = svg_text.split(">", 1)[0]
    assert "viewBox=" in root
    assert 'width="' not in root
    assert 'height="' not in root


def test_svg_has_door_swing_arc(tmp_path):
    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text()
    # Door swing arcs appear as path elements with an arc command; the demo
    # ground floor has doors.
    arcs = [p for p in svg_text.splitlines() if "<path" in p and " A " in p]
    assert arcs


def test_svg_has_north_arrow_scale_bar_title_block(tmp_path):
    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text()
    assert ">N</text>" in svg_text
    assert "Scale 1:100 @ A3" in svg_text
    assert ">m</text>" in svg_text  # scale bar unit


def test_dxf_pt_flips_y():
    assert plan2d._dxf_pt(0, 0, 25000) == (0, 25000)
    assert plan2d._dxf_pt(4000, 25000, 25000) == (4000, 0)


def test_dxf_street_wall_has_largest_y_after_flip(tmp_path):
    model = load_model("tubehouse-mini.json")
    plan2d.write_plans(model, tmp_path)
    doc = ezdxf.readfile(tmp_path / "dxf" / f"{model.name}_f0.dxf")
    msp = doc.modelspace()
    # The street boundary is the wall at model y=0; after the flip it must
    # appear at the largest DXF y (plot depth).
    street_wall = next(w for w in model.storeys[0].walls if abs(w.y - 0) < 1)
    flipped = plan2d._dxf_pt(street_wall.x, street_wall.y, model.plot_depth_mm)[1]
    assert flipped == model.plot_depth_mm
    # And its polyline in the DXF carries that flipped y.
    street_pts = []
    for e in msp:
        if e.dxf.layer == "WALLS":
            for v in e.get_points():
                if abs(v[1] - model.plot_depth_mm) < 1:
                    street_pts.append(v)
    assert street_pts


def test_dxf_has_door_arcs(tmp_path):
    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    doc = ezdxf.readfile(tmp_path / "dxf" / f"{model.name}_f0.dxf")
    msp = doc.modelspace()
    arcs = [e for e in msp if e.dxftype() == "ARC"]
    assert arcs
