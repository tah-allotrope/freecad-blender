"""C4: artefact catalogue owns names and paths, missing drawing is error."""

import json
from pathlib import Path

from homedesign.artifacts import (
    elevation_svg_path,
    plan_svg_path,
    png_path,
    section_svg_path,
    viewer_gltf_relative,
)
from homedesign.compiler import compile_spec


def test_artifact_paths_are_absolute(tmp_path):
    out = tmp_path / "out"
    p = plan_svg_path(out, "demo", 0)
    assert p.is_absolute(), f"plan path not absolute: {p}"
    rel = Path("output")
    p2 = plan_svg_path(rel, "demo", 0)
    assert p2.is_absolute()


def test_relative_link_never_absolute(tmp_path):
    out = tmp_path / "out"
    glb = out / "gltf" / "x.glb"
    glb.parent.mkdir(parents=True)
    glb.write_text("x")
    viewer_dir = out / "viewer"
    viewer_dir.mkdir()
    rel = viewer_gltf_relative(out, "x")
    assert not Path(rel).is_absolute()
    assert rel == "../gltf/x.glb"


def test_missing_drawing_raises(tmp_path):
    """PDF must not substitute paragraph for a missing SVG."""
    spec = json.loads((Path("spec/examples/demo-3br-2storey.json")).read_text(encoding="utf-8"))
    model = compile_spec(spec)
    from homedesign.pdf import _plan_pages

    out = tmp_path / "out"
    svg_dir = out / "svg"
    svg_dir.mkdir(parents=True)
    try:
        _plan_pages(model, svg_dir)
        assert False, "_plan_pages should have raised for missing drawings"
    except FileNotFoundError:
        pass


def test_catalogue_naming_conventions(tmp_path):
    out = tmp_path / "out"
    assert plan_svg_path(out, "house", 2).name == "house_f2.svg"
    assert elevation_svg_path(out, "house", "south").name == "house_elev_south.svg"
    assert section_svg_path(out, "house", "A-A").name == "house_section_A-A.svg"
    assert png_path(out, "house", "exterior").name == "house_exterior.png"
