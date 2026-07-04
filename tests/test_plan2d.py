import json
from pathlib import Path

import ezdxf

from src.homedesign.compiler import compile_spec
from src.homedesign import plan2d

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
    assert len(svgs) == len(model.storeys)
    assert len(dxfs) == len(model.storeys)
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
