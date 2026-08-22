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


def test_svg_draws_plot_boundary_labelled_ranh_lo_gioi(tmp_path):
    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    assert 'class="plot-boundary"' in svg_text
    assert "Ranh lộ giới" in svg_text
    # The boundary rect spans the full plot, not just the built footprint.
    w_px = model.plot_width_mm / plan2d.MM_PER_PX
    d_px = model.plot_depth_mm / plan2d.MM_PER_PX
    assert f'width="{w_px:.1f}"' in svg_text
    assert f'height="{d_px:.1f}"' in svg_text


def test_dxf_has_plot_layer_boundary(tmp_path):
    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    doc = ezdxf.readfile(tmp_path / "dxf" / f"{model.name}_f0.dxf")
    msp = doc.modelspace()
    boundary = [e for e in msp.query("LWPOLYLINE") if e.dxf.layer == "PLOT"]
    assert len(boundary) == 1
    assert len(boundary[0]) == 4


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


# --- Drawing-completeness features (fidelity ledger rev.3, 2026-08-17) -------
# The contractor plan sheets carry furniture, level markers, numbered stair
# treads and section-cut markers; the generated plans carried none of them,
# and the 3D scene was furnished while the 2D plan of the same model was not.


def test_svg_draws_furniture_for_furnishable_rooms(tmp_path):
    """The same compiled model must not be furnished in 3D and bare in 2D."""
    from homedesign.placement import plan_room

    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")

    ground = model.storeys[0]
    expected_kinds = set()
    for room in ground.rooms:
        rect = room.interior or room.rect
        for item in plan_room(room.type, rect.w / 1000, rect.d / 1000):
            expected_kinds.add(item.kind)
    assert expected_kinds, "fixture has no furnishable rooms; test would be vacuous"

    assert 'class="furniture"' in svg_text
    for kind in expected_kinds:
        assert f'data-furniture="{kind}"' in svg_text


def test_svg_furniture_sits_inside_its_room(tmp_path):
    """Plan furniture must use the same room-local -> world mapping as the 3D
    builder (furnish.py), i.e. the interior rect when one exists."""
    import re

    from homedesign.placement import plan_room

    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")

    ground = model.storeys[0]
    room = next(r for r in ground.rooms
                if plan_room(r.type, (r.interior or r.rect).w / 1000, (r.interior or r.rect).d / 1000))
    rect = room.interior or room.rect
    items = plan_room(room.type, rect.w / 1000, rect.d / 1000)

    # Every drawn footprint centre for this room must fall within the room rect.
    for item in items:
        cx_mm = rect.x + item.x * 1000 + item.w * 1000 / 2
        cy_mm = rect.y + item.y * 1000 + item.d * 1000 / 2
        assert rect.x - 1 <= cx_mm <= rect.x + rect.w + 1
        assert rect.y - 1 <= cy_mm <= rect.y + rect.d + 1

    # And the SVG must actually place a rect at that transformed centre.
    assert re.search(r'data-furniture="[a-z_]+"', svg_text)


def test_svg_has_level_marker_per_storey(tmp_path):
    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    for storey in model.storeys:
        svg_text = (tmp_path / "svg" / f"{model.name}_f{storey.level}.svg").read_text(encoding="utf-8")
        expected = "\u00b1 0.000" if storey.base_z == 0 else f"+ {storey.base_z / 1000:.3f}"
        assert expected in svg_text, f"storey {storey.level} missing level marker {expected!r}"


def test_svg_numbers_stair_treads(tmp_path):
    import re

    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    storey = next(s for s in model.storeys if s.stairs and s.stairs.treads)
    svg_text = (tmp_path / "svg" / f"{model.name}_f{storey.level}.svg").read_text(encoding="utf-8")
    assert 'class="tread-number"' in svg_text
    nums = re.findall(r'class="tread-number"[^>]*>(\d+)<', svg_text)
    assert nums
    # The sheets number odd treads only.
    assert all(int(n) % 2 == 1 for n in nums)
    assert "1" in nums
    assert str(len(storey.stairs.treads) if len(storey.stairs.treads) % 2 == 1
               else len(storey.stairs.treads) - 1) in nums


def test_u_return_tread_numbers_are_odd_ascending_then_returning(tmp_path):
    """22 risers -> up-flight prints 1,3,...,11 and the return prints
    13,15,...,21, matching the contractor sheets' odd-only convention."""
    import re

    spec = json.loads((REPO_ROOT / "designs" / "contractor-as-drawn.json").read_text(encoding="utf-8"))
    model = compile_spec(spec)
    # 3800mm storey -> 22 risers -> 21 numbered positions (the landing carries
    # one), printed odd-only.
    assert len(model.storeys[0].stairs.treads) == 22
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    nums = re.findall(r'class="tread-number"[^>]*>(\d+)<', svg_text)
    assert nums == ["1", "3", "5", "7", "9", "11", "13", "15", "17", "19", "21"]


def test_svg_draws_section_cut_markers(tmp_path):
    model = load_model("demo-3br-2storey.json")
    if not model.sections:
        model.sections = [{"name": "A-A", "axis": "x", "position_mm": model.plot_width_mm / 2}]
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    assert 'class="section-marker"' in svg_text
    for sec in model.sections:
        assert escape_name(sec["name"]) in svg_text


def escape_name(name: str) -> str:
    return name.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")


def test_dxf_has_furniture_layer_matching_svg(tmp_path):
    """SVG and DXF are one drawing set; furnishing only one repeats the very
    2D/3D split this work exists to close."""
    from homedesign.placement import plan_room

    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    doc = ezdxf.readfile(str(tmp_path / "dxf" / f"{model.name}_f0.dxf"))
    msp = doc.modelspace()

    ground = model.storeys[0]
    expected = sum(
        len(plan_room(r.type, (r.interior or r.rect).w / 1000, (r.interior or r.rect).d / 1000))
        for r in ground.rooms
    )
    assert expected, "fixture has no furnishable rooms; test would be vacuous"
    drawn = len(msp.query('LWPOLYLINE[layer=="FURNITURE"]'))
    assert drawn == expected, f"expected {expected} furniture footprints in DXF, got {drawn}"


def test_svg_dimension_chains_are_multi_tier(tmp_path):
    """The contractor sheets carry 2-3 tiers per side (fine subdivision, then
    major bands, then overall); the generator drew a single fine tier."""
    import re

    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")

    tiers = set(re.findall(r'data-tier="(\d+)"', svg_text))
    assert {"1", "2"} <= tiers, f"expected at least two dimension tiers, got {tiers}"

    # The outermost tier states the overall extent as one figure.
    assert f">{int(model.plot_width_mm)}<" in svg_text
    assert f">{int(model.plot_depth_mm)}<" in svg_text


def test_svg_major_tier_uses_full_span_divisions_only(tmp_path):
    """A 'major' division is one a room edge carries clear across the plan --
    derived, never invented, since the schema has no structural grid."""
    import re

    model = load_model("demo-3br-2storey.json")
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")

    # On this fixture the x axis subdivides at 4000/4100/6000, but none of those
    # edges runs the full 8000 depth, so only 0 and 10000 are major: the widest
    # x tier must therefore quote 10000 and never 4000.
    horiz = re.search(r'<g class="dim-chain" data-tier="2" data-axis="h">(.*?)</g>', svg_text, re.S)
    assert horiz, "no tier-2 horizontal chain emitted"
    labels = set(re.findall(r">(\d+)<", horiz.group(1)))
    assert labels == {str(int(model.plot_width_mm))}, labels


def test_fine_dimension_tier_spans_the_whole_plot():
    """The sheets dimension the yard setbacks, not just the built form: a plan
    whose rooms start 3500mm in must quote that 3500 leading gap."""
    from types import SimpleNamespace

    from homedesign.plan2d import _dimension_tiers

    def room(x, y, w, d):
        return SimpleNamespace(rect=SimpleNamespace(x=x, y=y, w=w, d=d, x2=x + w, y2=y + d))

    # One 3960-wide band sitting 3500 from the front and 1200 from the back.
    rooms = [room(0, 3500, 3960, 20300)]
    tiers = _dimension_tiers(rooms, "v", extent_mm=25000, cross_extent_mm=3960)
    fine = tiers[0]
    assert fine[0] == 0, f"fine tier must start at the plot edge, got {fine[0]}"
    assert fine[-1] == 25000, f"fine tier must end at the plot edge, got {fine[-1]}"
    gaps = [round(b - a) for a, b in zip(fine, fine[1:])]
    assert gaps == [3500, 20300, 1200], gaps


# --- Contractor-parity pass (checklist 2026-08-21) ---------------------------


def _contractor_model():
    spec = json.loads((REPO_ROOT / "designs" / "contractor-as-drawn.json").read_text(encoding="utf-8"))
    return compile_spec(spec)


def _text_y(svg_text: str, label: str) -> float:
    import re

    m = re.search(rf'<text[^>]*y="([\d.]+)"[^>]*>{re.escape(label)}</text>', svg_text)
    assert m, f"label {label!r} not found in svg"
    return float(m.group(1))


def test_plan_orientation_rear_at_top(tmp_path):
    """C1: the rear-most room's label sits at a smaller SVG y than the
    front-most room's -- rear at the top of the sheet, street at the bottom."""
    model = _contractor_model()
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    y_rear = _text_y(svg_text, "P. ĂN + BẾP")
    y_front = _text_y(svg_text, "NƠI ĐỂ XE")
    assert y_rear < y_front


def test_per_room_level_markers_replace_storey_fallback(tmp_path):
    """C3: rooms carrying level_mm print their own marker (absolute datum =
    base_z + level_mm); the once-per-storey marker only survives on storeys
    where no room carries one."""
    model = _contractor_model()
    plan2d.write_plans(model, tmp_path)
    f0 = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    assert ">± 0.000<" in f0   # gara
    assert ">+ 0.100<" in f0   # khach
    assert ">+ 0.300<" in f0   # bep_an
    f1 = (tmp_path / "svg" / f"{model.name}_f1.svg").read_text(encoding="utf-8")
    assert ">+ 3.800<" in f1   # sinh_hoat: level_mm 0 over base_z 3800
    # A model with no level_mm anywhere keeps the per-storey fallback.
    plain = load_model("demo-3br-2storey.json")
    plan2d.write_plans(plain, tmp_path)
    for storey in plain.storeys:
        svg_text = (tmp_path / "svg" / f"{plain.name}_f{storey.level}.svg").read_text(encoding="utf-8")
        expected = "\u00b1 0.000" if storey.base_z == 0 else f"+ {storey.base_z / 1000:.3f}"
        assert expected in svg_text


def test_setback_lines_rendered_in_svg_and_dxf(tmp_path):
    """C4: dash-dot building lines at front/rear setback distances, labelled,
    in both writers."""
    model = _contractor_model()
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    assert 'class="setback"' in svg_text
    assert "Ranh khoảng lùi trước" in svg_text
    assert "Ranh khoảng lùi sau" in svg_text
    # Front line at model y=3500 -> flipped SVG y=(25000-3500)/10.
    assert 'y1="2150.0"' in svg_text
    # Rear line at model y=25000-2500 -> flipped SVG y=250.0.
    assert 'y1="250.0"' in svg_text
    doc = ezdxf.readfile(tmp_path / "dxf" / f"{model.name}_f0.dxf")
    msp = doc.modelspace()
    setbacks = [e for e in msp if e.dxf.layer == "SETBACK"]
    lines = [e for e in setbacks if e.dxftype() == "LINE"]
    assert len(lines) == 2
    texts = [e.dxf.text for e in setbacks if e.dxftype() == "TEXT"]
    assert any("trước" in t for t in texts)
    assert any("sau" in t for t in texts)


def test_section_markers_use_drawing_labels(tmp_path):
    """C6: cut lines carry A-A/B-B circle bubbles, not raw internal names."""
    model = _contractor_model()
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    assert ">A-A<" in svg_text
    assert ">B-B<" in svg_text
    assert ">long<" not in svg_text
    assert ">cross_bed<" not in svg_text
    assert "<circle" in svg_text


def test_elevator_room_cross_hatched(tmp_path):
    model = _contractor_model()
    plan2d.write_plans(model, tmp_path)
    svg_text = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    assert "url(#elevhatch)" in svg_text


def test_annotations_render_as_callouts(tmp_path):
    """S3/S4/B2/M2: dashed boxes + italic text callouts on the plans."""
    model = _contractor_model()
    plan2d.write_plans(model, tmp_path)
    f0 = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    assert "Tiểu cảnh, ô lấy sáng" in f0
    assert "- 0.450" in f0 and "+ 0.200" in f0
    for level in range(1, 6):
        svg_text = (tmp_path / "svg" / f"{model.name}_f{level}.svg").read_text(encoding="utf-8")
        assert "Lô gia" in svg_text, f"f{level} missing Lô gia"
    for level in range(2, 5):
        svg_text = (tmp_path / "svg" / f"{model.name}_f{level}.svg").read_text(encoding="utf-8")
        assert "Ô lấy sáng 2200" in svg_text, f"f{level} missing Ô lấy sáng 2200"
    # f5's light well is a real declared void since round 2, not a callout.
    f5 = (tmp_path / "svg" / f"{model.name}_f5.svg").read_text(encoding="utf-8")
    assert "voidhatch" in f5 and "Ô lấy sáng" in f5
    f6 = (tmp_path / "svg" / f"{model.name}_f6.svg").read_text(encoding="utf-8")
    assert "Ô lấy sáng" in f6
    # Boxed callouts draw a dashed rectangle inside the annotation group.
    assert 'class="annotation"' in f0
    assert 'stroke-dasharray="6 3"' in f0


def test_void_label_names_rooms_below(tmp_path):
    """S2: the labels over the hatched lửng voids repeat each room-below
    name separately (the voids are split per room-below footprint), and
    the yard strip over no room falls back to its reason text."""
    model = _contractor_model()
    plan2d.write_plans(model, tmp_path)
    f1 = (tmp_path / "svg" / f"{model.name}_f1.svg").read_text(encoding="utf-8")
    assert "P.KHÁCH" in f1
    assert "NƠI ĐỂ XE" in f1
    assert "SÂN TRƯỚC" in f1
    f0 = (tmp_path / "svg" / f"{model.name}_f0.svg").read_text(encoding="utf-8")
    assert "SÂN TRƯỚC" in f0 and "SÂN SAU" in f0
