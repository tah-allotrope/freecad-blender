"""Artifact provenance: model hashes, render sidecars, viewer writer (PHASE-06)."""
import json
from pathlib import Path

import pytest

from homedesign.compiler import compile_spec
from homedesign.model import (
    model_hash,
    read_render_sidecar,
    write_render_sidecar,
)
from homedesign.pdf import render_brief_html
from homedesign.viewer import write_viewer

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "spec" / "examples"


def load_example(name):
    return json.loads((EXAMPLES / name).read_text())


def _mini():
    return compile_spec(load_example("tubehouse-mini.json"))


def _brief():
    return {"title": "T", "subtitle": "s", "narrative": ["p"], "requirements": ["r"]}


def test_model_hash_is_stable_12_hex_and_sensitive_to_geometry():
    model = _mini()
    h1 = model_hash(model)
    h2 = model_hash(model)
    assert h1 == h2
    assert len(h1) == 12
    int(h1, 16)  # valid hex
    # A 1mm height change must change the hash.
    model.storeys[0].height_mm += 1.0
    assert model_hash(model) != h1


def test_model_hash_stable_across_recompiles():
    spec = load_example("tubehouse-mini.json")
    a = compile_spec(json.loads(json.dumps(spec)))
    b = compile_spec(json.loads(json.dumps(spec)))
    assert model_hash(a) == model_hash(b)


def test_read_sidecar_missing_returns_none():
    assert read_render_sidecar(Path("does-not-exist.png")) is None


def test_write_and_read_sidecar_roundtrip(tmp_path):
    png = tmp_path / "mini_exterior.png"
    png.write_bytes(b"png")
    sidecar = write_render_sidecar(png, "abc123def456", "exterior", "final")
    assert sidecar.exists()
    data = read_render_sidecar(png)
    assert data["model_hash"] == "abc123def456"
    assert data["view"] == "exterior"
    assert data["profile"] == "final"


def test_write_and_read_glb_sidecar_roundtrip(tmp_path):
    """The export-time GLB sidecar `publish` demands (freshness C5)."""
    glb = tmp_path / "mini.glb"
    glb.write_bytes(b"glb")
    sidecar = write_render_sidecar(glb, "abc123def456", "glb", "final")
    assert sidecar.exists()
    assert sidecar.name == "mini.glb.json"
    assert read_render_sidecar(glb)["model_hash"] == "abc123def456"



def test_pdf_require_fresh_raises_on_stale_render(tmp_path, monkeypatch):
    # Use tmp_path so we never mutate deliverables
    out = tmp_path / "out"
    (out / "png").mkdir(parents=True)
    (out / "svg").mkdir(parents=True)
    model = _mini()
    from homedesign.model import View
    model.views = [View(name="exterior", kind="exterior_front")]
    png = out / "png" / "tubehouse-mini_exterior.png"
    from PIL import Image
    Image.new("RGB", (10, 10), color="white").save(png)
    write_render_sidecar(png, "stale00000000", "exterior", "final")
    # Create all required drawings for the model via catalogue
    from homedesign.artifacts import all_drawing_paths
    for pth in all_drawing_paths(model, out):
        pth.parent.mkdir(parents=True, exist_ok=True)
        pth.write_text("<svg></svg>", encoding="utf-8")
    with pytest.raises(RuntimeError) as exc:
        render_brief_html(model, _brief(), out, EXAMPLES / "tubehouse-mini.json", require_fresh=True)
    assert "stale" in str(exc.value).lower()
    html = render_brief_html(model, _brief(), out, EXAMPLES / "tubehouse-mini.json")
    assert "STALE" in html


def test_write_viewer_inlines_glb(tmp_path):
    """The light phone build stays a single offline file (DEC-006).

    The full build now serves an external GLB instead; that contract is
    covered in tests/test_render_fidelity.py.
    """
    glb = tmp_path / "mini.glb"
    glb.write_bytes(b"\x00\x01GLB")
    html_path = write_viewer("mini", glb, tmp_path, build="light").html
    html = html_path.read_text(encoding="utf-8")
    assert "mini" in html
    assert "atob(" in html  # GLB embedded inline (under the 8MB limit)
    # The GLB must be decoded to an ArrayBuffer before loader.parse: a bare
    # atob() string is treated as glTF-JSON and JSON.parse() fails, leaving
    # the viewer black.
    assert "loader.parse(_buf.buffer" in html
    assert "loader.parse(atob(" not in html
    # No external <script> tags -- the three.js sources are inlined. (The
    # bundled libraries mention fetch()/http:// internally in error paths;
    # the model itself is loaded from the embedded base64, never a request.)
    assert "<script src=" not in html


def test_console_script_registered():
    import tomllib

    pyproject = tomllib.loads((REPO_ROOT / "pyproject.toml").read_text())
    assert pyproject["project"]["scripts"]["homedesign"] == "homedesign.__main__:main"
