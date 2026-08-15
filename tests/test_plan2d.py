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
    assert "Scale: use the graphic bar" in svg_text
    assert ">m</text>" in svg_text  # scale bar unit


def test_dimension_chain_segments_and_ticks():
    frag = plan2d._dimension_chain([0.0, 3005.0, 3960.0], "h", 40.0, 3960.0)
    assert ">3005<" in frag
    assert ">955<" in frag
    assert frag.count("<line") == 3


def test_dimension_chain_empty_degenerate():
    frag = plan2d._dimension_chain([], "h", 40.0, 3960.0)
    assert ">3960<" in frag
    assert frag.count("<line") == 0


def test_contractor_plan_dimensions_in_svg_and_dxf(tmp_path):
    spec = json.loads((REPO_ROOT / "designs" / "contractor-as-drawn.json").read_text(encoding="utf-8"))
    model = compile_spec(spec)
    plan2d.write_plans(model, tmp_path)
    f0 = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    # Millimetre dimension labels for real room widths: the 955mm stair
    # corridor and the 1960mm lift lobby.
    assert ">955<" in f0
    assert ">1960<" in f0
    doc = ezdxf.readfile(tmp_path / "dxf" / f"{model.name}_f0.dxf")
    dims = [e for e in doc.modelspace() if e.dxf.layer == "DIMS"]
    assert len(dims) >= 4


def test_plans_do_not_print_false_scale(tmp_path):
    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    for svg in (tmp_path / "svg").glob("*.svg"):
        assert "Scale 1:100" not in svg.read_text(encoding="utf-8")


def test_north_arrow_rotates_with_north_deg(tmp_path):
    spec = json.loads((EXAMPLES / "demo-3br-2storey.json").read_text())
    spec["site"]["north_deg"] = 90
    model = compile_spec(spec)
    plan2d.write_plans(model, tmp_path)
    svg = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    assert "rotate(90" in svg


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


def _named_model():
    spec = {
        "meta": {"name": "named-rooms", "style": "modern-minimal"},
        "site": {"plot_width_mm": 4000, "plot_depth_mm": 4000},
        "storeys": [
            {
                "level": 0, "name": "Ground", "height_mm": 3000,
                "rooms": [
                    {"id": "a", "type": "living", "name": "A & B <x>", "rect": {"x": 0, "y": 0, "w": 4000, "d": 4000}},
                ],
            }
        ],
    }
    return compile_spec(spec)


def test_escape_text_helper():
    from homedesign.xmltext import escape_text

    assert escape_text("BẾP & ĂN") == "BẾP &amp; ĂN"
    assert escape_text(None) == ""
    assert escape_text('a<b>"c"') == "a&lt;b&gt;&quot;c&quot;"


def test_svg_with_special_char_names_still_parses(tmp_path):
    import xml.etree.ElementTree as ET

    model = _named_model()
    plan2d.write_plans(model, tmp_path)
    for svg in (tmp_path / "svg").glob("*.svg"):
        ET.fromstring(svg.read_text(encoding="utf-8"))
    ground = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    assert "A &amp; B &lt;x&gt;" in ground


def test_room_names_reach_svg_and_dxf_text(tmp_path):
    spec = json.loads((EXAMPLES / "demo-3br-2storey.json").read_text())
    for storey in spec["storeys"]:
        for room in storey["rooms"]:
            room["name"] = f"Room {room['id']}"
    model = compile_spec(spec)
    plan2d.write_plans(model, tmp_path)
    ground = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    for room in model.storeys[0].rooms:
        assert f"Room {room.id}" in ground
    doc = ezdxf.readfile(tmp_path / "dxf" / f"{model.name}_f0.dxf")
    texts = [e.dxf.text for e in doc.modelspace() if e.dxftype() == "TEXT"]
    for room in model.storeys[0].rooms:
        assert f"Room {room.id}" in texts


def test_declared_void_hatches_svg_and_dxf(tmp_path):
    spec = json.loads((EXAMPLES / "courtyard-fixture.json").read_text())
    model = compile_spec(spec)
    plan2d.write_plans(model, tmp_path)
    ground = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    assert "url(#voidhatch)" in ground
    doc = ezdxf.readfile(tmp_path / "dxf" / f"{model.name}_f0.dxf")
    assert "VOIDS" in doc.layers
    assert any(e.dxf.layer == "VOIDS" for e in doc.modelspace())
