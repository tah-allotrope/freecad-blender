"""Tests for the render-fidelity and photoreal plan closeout.

Covers the pure-Python surfaces of RF TASK-02-05 / 03-03 / 03-04 / 05-10 and
PR TASK-05-01..03 / 05-06. Nothing here imports `bpy`.
"""
import json
from pathlib import Path

import pytest

from homedesign.compiler import compile_spec
from homedesign.elevation import build_elevation
from homedesign.finishes import family_for_palette_key
from homedesign.parapet import parapet_bands
from homedesign.viewer import glb_size_budget

REPO_ROOT = Path(__file__).resolve().parent.parent
DESIGNS = REPO_ROOT / "designs"
EXAMPLES = REPO_ROOT / "spec" / "examples"


def load_design(name):
    return json.loads((DESIGNS / name).read_text(encoding="utf-8"))


# --- RF TASK-02-05: get_material resolves through the finish map ------------

def test_palette_key_falls_back_to_static_family_without_a_finish_map():
    assert family_for_palette_key("floor_bathroom", {}) == "ceramic_tile"


def test_finish_map_overrides_the_static_family_for_an_element_kind():
    finish_map = {"element:floor": "stone_slab"}
    assert family_for_palette_key("floor_bathroom", finish_map) == "stone_slab"


def test_room_scoped_finish_beats_the_element_default():
    finish_map = {"element:floor": "stone_slab", "room:khach:floor": "wood_board"}
    assert family_for_palette_key("floor_default", finish_map, room_id="khach") == "wood_board"


def test_unknown_finish_family_in_the_map_is_ignored_rather_than_crashing():
    assert family_for_palette_key("frame", {"element:frame": "unobtanium"}) == "metal_brushed"


# --- RF TASK-03-03: elevation draws opening divisions ----------------------

def test_elevation_draws_a_mullion_for_a_divided_opening():
    model = compile_spec(load_design("contractor-as-drawn.json"))
    items = build_elevation(model, "south")
    mullions = [i for i in items if i["kind"] == "mullion"]
    assert mullions, "a south window with divisions must project mullion bars"


def test_every_mullion_sits_inside_its_host_opening():
    model = compile_spec(load_design("contractor-as-drawn.json"))
    items = build_elevation(model, "south")
    openings = [i for i in items if i["kind"] == "opening"]
    for m in [i for i in items if i["kind"] == "mullion"]:
        host = [
            o for o in openings
            if o["x"] - 1 <= m["x"] and m["x"] + m["w"] <= o["x"] + o["w"] + 1
            and o["z"] - 1 <= m["z"] and m["z"] + m["h"] <= o["z"] + o["h"] + 1
        ]
        assert host, f"mullion {m} escapes every opening"


# --- RF TASK-03-04: balcony parapet pattern -------------------------------

def test_a_solid_parapet_is_one_band_per_side():
    bands = parapet_bands(0, 0, 4000, 2000, ["south"], "solid")
    assert len(bands) == 1
    assert bands[0]["w_mm"] == pytest.approx(4000)


def test_a_slatted_parapet_splits_into_gapped_slats():
    bands = parapet_bands(0, 0, 4000, 2000, ["south"], "slatted")
    assert len(bands) > 1, "slatted must emit multiple slats"
    assert all(b["h_mm"] < 1100 for b in bands), "slats are shorter than the full parapet"
    tops = sorted({round(b["z_off_mm"], 3) for b in bands})
    assert len(tops) == len(bands), "slats stack at distinct heights"


def test_slats_never_leave_the_parapet_envelope():
    bands = parapet_bands(0, 0, 4000, 2000, ["south"], "slatted")
    for b in bands:
        assert b["z_off_mm"] >= -0.001
        assert b["z_off_mm"] + b["h_mm"] <= 1100.001


def test_the_schema_accepts_a_parapet_pattern():
    from homedesign.validate import validate_schema
    spec = json.loads((EXAMPLES / "tubehouse-mini.json").read_text(encoding="utf-8"))
    touched = False
    for storey in spec["storeys"]:
        for room in storey.get("rooms", []):
            room["parapet_pattern"] = "slatted"
            touched = True
    assert touched
    assert validate_schema(spec) == []


def test_the_schema_rejects_an_unknown_parapet_pattern():
    from homedesign.validate import validate_schema
    spec = json.loads((EXAMPLES / "tubehouse-mini.json").read_text(encoding="utf-8"))
    spec["storeys"][0]["rooms"][0]["parapet_pattern"] = "wobbly"
    assert validate_schema(spec) != []


# --- RF TASK-05-10: GLB size budget (ASM-006) -----------------------------

def test_the_light_build_budget_is_six_mebibytes():
    assert glb_size_budget("light") == 6 * 1024 * 1024


def test_the_full_build_budget_is_twenty_five_mebibytes():
    assert glb_size_budget("full") == 25 * 1024 * 1024


def test_an_unknown_build_has_no_budget():
    with pytest.raises(ValueError):
        glb_size_budget("enormous")


def test_the_published_glbs_are_inside_their_budgets():
    gltf = REPO_ROOT / "deliverables" / "contractor-as-drawn" / "gltf"
    # The full build is published under the bare name; `-light` is the phone
    # build derived from it.
    for name, build in (
        ("contractor-as-drawn-light.glb", "light"),
        ("contractor-as-drawn.glb", "full"),
    ):
        path = gltf / name
        if not path.exists():
            pytest.skip(f"{name} not published yet")
        assert path.stat().st_size <= glb_size_budget(build), (
            f"{name} is {path.stat().st_size} bytes, over the {build} budget"
        )


# --- PR TASK-05-01/02/03: the full viewer loads an external GLB ------------

def _tiny_glb(path: Path) -> Path:
    path.write_bytes(b"glTF\x02\x00\x00\x00" + b"\x00" * 40)
    return path


def test_the_full_build_fetches_the_glb_instead_of_inlining_it(tmp_path):
    glb = _tiny_glb(tmp_path / "mini.glb")
    from homedesign.viewer import write_viewer

    html = write_viewer("mini", glb, tmp_path, build="full").html.read_text(encoding="utf-8")
    assert "fetch('mini.glb')" in html
    # No inlined payload. (`atob(` alone is not the tell — the bundled
    # GLTFLoader carries one for data: URIs — but our base64 chunk literal and
    # its decode loop are unmistakable.)
    assert "var _b64=" not in html
    assert "loader.parse(_buf.buffer" not in html


def test_the_full_build_copies_the_glb_next_to_its_html(tmp_path):
    glb = _tiny_glb(tmp_path / "mini.glb")
    from homedesign.viewer import write_viewer

    written = write_viewer("mini", glb, tmp_path, build="full")
    assert written.glb is not None
    assert written.glb.exists()
    assert written.glb.parent == written.html.parent
    assert written.glb.read_bytes() == glb.read_bytes()


def test_the_light_build_still_inlines_and_ships_no_sibling_glb(tmp_path):
    glb = _tiny_glb(tmp_path / "mini.glb")
    from homedesign.viewer import write_viewer

    written = write_viewer("mini", glb, tmp_path, build="light")
    html = written.html.read_text(encoding="utf-8")
    assert "atob(" in html
    assert "loader.parse(_buf.buffer" in html
    assert written.glb is None


def test_a_full_build_over_the_inline_limit_is_still_served(tmp_path, monkeypatch):
    """The 8 MiB inline ceiling constrains only the light build (TASK-05-02)."""
    from homedesign import viewer as viewer_mod

    # Shrink the limit rather than writing megabytes to disk: the branch under
    # test is a size comparison, not an I/O path.
    monkeypatch.setattr(viewer_mod, "INLINE_GLB_LIMIT_BYTES", 16)
    glb = tmp_path / "mini.glb"
    glb.write_bytes(b"glTF\x02\x00\x00\x00" + b"\x00" * 512)
    html = viewer_mod.write_viewer("mini", glb, tmp_path, build="full").html.read_text(encoding="utf-8")
    assert "fetch('mini.glb')" in html


def test_a_light_build_over_its_budget_is_an_error(tmp_path):
    from homedesign import viewer as viewer_mod

    glb = tmp_path / "mini.glb"
    glb.write_bytes(b"glTF\x02\x00\x00\x00" + b"\x00" * (viewer_mod.glb_size_budget("light") + 16))
    with pytest.raises((ValueError, RuntimeError)):
        viewer_mod.write_viewer("mini", glb, tmp_path, build="light")


# --- RF TASK-05-06..09 + PR TASK-05-05: viewer construction tools ---------

def _viewer_html(tmp_path, **kw):
    from homedesign.viewer import write_viewer

    glb = _tiny_glb(tmp_path / "mini.glb")
    return write_viewer("mini", glb, tmp_path, build="full", **kw).html.read_text(encoding="utf-8")


def test_the_viewer_embeds_room_labels_and_level_tags(tmp_path):
    html = _viewer_html(
        tmp_path,
        rooms=[{"text": "Phòng khách", "x": 1.0, "y": 2.0, "z": 1.6}],
        levels=[{"text": "Lửng +3.400", "x": 0.0, "y": 0.0, "z": 3.4}],
    )
    assert "Phòng khách" in html
    assert "Lửng +3.400" in html
    assert "var ROOM_LABELS = [" in html
    assert "__ROOM_LABELS__" not in html


def test_the_viewer_ships_a_measurement_tool_reporting_millimetres(tmp_path):
    html = _viewer_html(tmp_path)
    assert "__handleMeasureTap" in html
    assert "Math.round(a.distanceTo(b) * 1000)" in html
    assert "' mm'" in html


def test_the_viewer_ships_section_planes_on_both_axes(tmp_path):
    html = _viewer_html(tmp_path)
    assert "localClippingEnabled = true" in html
    assert "wireCutSlider('cut-y'" in html
    assert "wireCutSlider('cut-z'" in html
    assert 'id="cut-y"' in html and 'id="cut-z"' in html


def test_the_viewer_ships_layer_toggles_for_the_four_groups(tmp_path):
    html = _viewer_html(tmp_path)
    assert "LAYER_PREFIXES" in html
    for layer in ("structure", "walls", "openings", "furniture"):
        assert f'data-layer="{layer}"' in html


def test_the_viewer_carries_an_environment_map(tmp_path):
    html = _viewer_html(tmp_path)
    assert "EquirectangularReflectionMapping" in html
    assert "__ENV_MAP__" not in html
    # The cached HDRI is present in this repo, so a real preview must be inlined.
    assert "data:image/jpeg;base64," in html


def test_no_placeholder_survives_into_a_written_viewer(tmp_path):
    html = _viewer_html(tmp_path, rooms=[], levels=[])
    for placeholder in ("__TITLE__", "__BUILD_BADGE__", "__LOAD_CALL__",
                        "__THREE_JS__", "__GLTF_LOADER__", "__ORBIT_CONTROLS__",
                        "__ROOM_LABELS__", "__LEVEL_TAGS__", "__ENV_MAP__"):
        assert placeholder not in html, f"{placeholder} was never substituted"


# --- the HDRI decoder behind that environment map -------------------------

def test_the_cached_exterior_hdri_decodes_to_a_sane_float_image():
    from homedesign import asset_cache
    from homedesign.hdri import read_hdr

    pixels = read_hdr(asset_cache.hdri("exterior"))
    assert pixels.ndim == 3 and pixels.shape[2] == 3
    assert pixels.shape[1] == pixels.shape[0] * 2, "an equirectangular map is 2:1"
    assert pixels.min() >= 0.0
    assert pixels.max() > 10.0, "an HDRI must carry values above display white"


def test_the_environment_preview_is_small_enough_to_inline():
    from homedesign import asset_cache
    from homedesign.hdri import equirect_preview_jpeg

    jpeg = equirect_preview_jpeg(asset_cache.hdri("exterior"), width=512)
    assert jpeg[:2] == b"\xff\xd8", "not a JPEG"
    assert len(jpeg) < 120_000, f"{len(jpeg)} bytes is too fat to inline"


def test_tone_mapping_never_leaves_the_display_range():
    import numpy as np

    from homedesign.hdri import tone_map

    wild = np.array([[[0.0, 1.0, 1e6]]], dtype=np.float32)
    out = tone_map(wild)
    assert out.dtype.name == "uint8"
    assert out.min() >= 0 and out.max() <= 255


# --- the viewer's GLB must stay raycastable -------------------------------

def _glb_json(path: Path) -> dict:
    """The JSON chunk of a binary glTF."""
    import struct

    raw = path.read_bytes()
    magic, _version, _length = struct.unpack_from("<4sII", raw, 0)
    assert magic == b"glTF", f"{path} is not a GLB"
    chunk_len, chunk_type = struct.unpack_from("<II", raw, 12)
    assert chunk_type == 0x4E4F534A, "first chunk is not JSON"
    return json.loads(raw[20:20 + chunk_len].decode("utf-8"))


def test_published_glb_positions_are_float_not_quantized():
    """Quantized POSITION breaks picking in the viewer's three.js (r128).

    r128 raycasts normalized integer attributes without applying the
    normalization, so every hit lands far past the surface and both the
    measurement tool and tap-to-focus silently misreport. Position
    quantization saved 0.2% of a texture-dominated file, so it is off.
    """
    glb = REPO_ROOT / "deliverables" / "contractor-as-drawn" / "gltf" / "contractor-as-drawn.glb"
    if not glb.exists():
        pytest.skip("contractor GLB not published yet")
    doc = _glb_json(glb)
    float_component = 5126
    for mesh in doc.get("meshes", []):
        for prim in mesh.get("primitives", []):
            index = prim.get("attributes", {}).get("POSITION")
            if index is None:
                continue
            accessor = doc["accessors"][index]
            assert accessor["componentType"] == float_component, (
                f"POSITION accessor {index} is componentType "
                f"{accessor['componentType']}, not float — the GLB was quantized"
            )
            assert not accessor.get("normalized", False)


# --- every build_* option must actually reach the Blender command ---------

def test_build_scene_forwards_show_neighbours_to_blender(monkeypatch, tmp_path):
    """`show_neighbours` was accepted and silently dropped for every `build`.

    `build_scene` took the keyword but called `_build_command` positionally
    without it, so `homedesign build --show-neighbours` rendered the plain
    15 m ground pad instead of the alley and party walls — with no error
    anywhere. `render_only` forwarded it correctly, which is what made the
    gap hard to see.
    """
    from homedesign import orchestrator

    captured = {}

    def fake_build_command(*args, **kwargs):
        captured["kwargs"] = kwargs
        captured["args"] = args
        return ["echo", "noop"]

    class FakeProc:
        stdout = iter(())
        returncode = 0

        def wait(self):
            return 0

    monkeypatch.setattr(orchestrator, "_build_command", fake_build_command)
    monkeypatch.setattr(orchestrator.subprocess, "Popen", lambda *a, **k: FakeProc())
    orchestrator.build_scene(tmp_path / "m.model.json", tmp_path, profile="final",
                             show_neighbours=True)
    assert captured["kwargs"].get("show_neighbours") is True, (
        "build_scene dropped show_neighbours before the Blender command"
    )


def test_build_command_emits_the_show_neighbours_flag(monkeypatch):
    from homedesign import orchestrator

    monkeypatch.setattr(orchestrator, "find_blender", lambda: "blender")
    on = orchestrator._build_command(Path("m.json"), Path("out"), "final", show_neighbours=True)
    off = orchestrator._build_command(Path("m.json"), Path("out"), "final", show_neighbours=False)
    assert "--show-neighbours" in on
    assert "--show-neighbours" not in off


# --- a published page must never reference a local filesystem path ---------

def test_relative_to_resolves_a_sibling_directory():
    """`Path.relative_to` only walks downward; a sibling needs `os.path.relpath`.

    The floors viewer sits in `<out>/viewer/` and its GLB in `<out>/gltf/`, so
    the downward-only form raised and the except branch fell back to
    `path.resolve()` — baking `C:/Users/.../output/gltf/x.glb` into a page
    published to GitHub Pages, where it fails for every visitor.
    """
    from homedesign.viewer import _relative_to

    out = Path("/tmp/out")
    assert _relative_to(out / "gltf" / "x.glb", out / "viewer") == "../gltf/x.glb"


def test_relative_to_never_returns_an_absolute_path(tmp_path):
    from homedesign.viewer import _relative_to

    elsewhere = tmp_path / "somewhere" / "deep" / "model.glb"
    elsewhere.parent.mkdir(parents=True)
    elsewhere.write_bytes(b"x")
    rel = _relative_to(elsewhere, tmp_path / "viewer")
    assert not Path(rel).is_absolute(), rel
    assert ":" not in rel, f"{rel} looks like a Windows drive path"


def _floors_fixture(tmp_path):
    """A minimal model plus the plan SVGs the floors viewer requires."""
    glb = _tiny_glb(tmp_path / "gltf" / "mini.glb") if (tmp_path / "gltf").exists() else None
    (tmp_path / "gltf").mkdir(exist_ok=True)
    glb = _tiny_glb(tmp_path / "gltf" / "mini.glb")
    svg_dir = tmp_path / "svg"
    svg_dir.mkdir(exist_ok=True)
    storeys = [{"name": "Ground", "base_z": 0.0, "height_mm": 3400.0},
               {"name": "F1", "base_z": 3400.0, "height_mm": 3400.0}]
    for level in range(len(storeys)):
        (svg_dir / f"mini_f{level}.svg").write_text(
            '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 100 100"></svg>',
            encoding="utf-8")
    return glb, storeys, svg_dir


def test_floor_viewer_copies_its_glb_and_loads_it_by_name(tmp_path):
    from homedesign.viewer import write_floor_viewer

    glb, storeys, svg_dir = _floors_fixture(tmp_path)
    written = write_floor_viewer("mini", glb, storeys, svg_dir, tmp_path)
    assert written is not None
    html_path = getattr(written, "html", written)
    html = html_path.read_text(encoding="utf-8")
    assert "fetch('mini.glb')" in html, "floors page must load a sibling GLB by bare name"
    assert (html_path.parent / "mini.glb").exists(), "the GLB was not copied beside the page"


def test_no_emitted_viewer_embeds_a_filesystem_path(tmp_path):
    """Guard for every build: nothing published may name a local directory."""
    from homedesign.viewer import write_floor_viewer, write_viewer

    glb, storeys, svg_dir = _floors_fixture(tmp_path)
    pages = [write_viewer("mini", glb, tmp_path, build="full").html,
             write_viewer("mini", glb, tmp_path, build="light").html]
    floors = write_floor_viewer("mini", glb, storeys, svg_dir, tmp_path)
    pages.append(getattr(floors, "html", floors))

    needle = tmp_path.resolve().as_posix()
    for page in pages:
        text = page.read_text(encoding="utf-8")
        assert needle not in text, f"{page.name} embeds the absolute path {needle}"
