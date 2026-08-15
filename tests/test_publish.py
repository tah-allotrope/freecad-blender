"""Hash-verified publish and brief scaffolding (PHASE-06)."""
import json
from pathlib import Path

import pytest

from homedesign.compiler import compile_spec
from homedesign.model import model_hash, write_render_sidecar
from homedesign.publish import publish, verify_fresh

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "spec" / "examples"
DESIGNS = REPO_ROOT / "designs"


def _mini():
    return compile_spec(json.loads((EXAMPLES / "tubehouse-mini.json").read_text()))


def test_scaffold_brief_has_all_keys():
    from homedesign.brief import scaffold_brief

    spec = json.loads((DESIGNS / "contractor-as-drawn.json").read_text(encoding="utf-8"))
    model = compile_spec(spec)
    brief = scaffold_brief(model)
    assert set(brief) == {"title", "subtitle", "narrative", "requirements"}
    assert "7 storeys" in brief["subtitle"]
    assert "3.96" in brief["subtitle"]
    assert brief["narrative"]
    assert brief["requirements"]


def _write_png(png_dir, name, hash_val):
    png_dir.mkdir(parents=True, exist_ok=True)
    p = png_dir / name
    p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 20)
    if hash_val is not None:
        write_render_sidecar(p, hash_val, "exterior", "final")
    return p


def test_verify_fresh_flags_only_mismatched(tmp_path):
    model = _mini()
    _write_png(tmp_path / "png", f"{model.name}_a.png", model_hash(model))
    _write_png(tmp_path / "png", f"{model.name}_b.png", "deadbeef0000")
    stale = verify_fresh(model, tmp_path)
    assert len(stale) == 1
    assert stale[0][0].name == f"{model.name}_b.png"
    assert stale[0][1] == "deadbeef0000"


def test_verify_fresh_flags_missing_sidecar(tmp_path):
    model = _mini()
    _write_png(tmp_path / "png", f"{model.name}_a.png", None)
    stale = verify_fresh(model, tmp_path)
    assert len(stale) == 1
    assert stale[0][1] is None


def test_publish_refuses_when_stale(tmp_path):
    model = _mini()
    _write_png(tmp_path / "png", f"{model.name}_a.png", "deadbeef0000")
    deliverables = tmp_path / "deliverables"
    with pytest.raises(RuntimeError) as exc:
        publish(model, tmp_path, deliverables)
    assert "stale" in str(exc.value).lower()
    assert not (deliverables / model.name).exists()


def test_publish_force_copies(tmp_path):
    model = _mini()
    _write_png(tmp_path / "png", f"{model.name}_a.png", "deadbeef0000")
    deliverables = tmp_path / "deliverables"
    paths = publish(model, tmp_path, deliverables, force=True)
    assert paths
    assert (deliverables / model.name / "png" / f"{model.name}_a.png").exists()


def test_publish_copies_fresh_gallery(tmp_path):
    model = _mini()
    _write_png(tmp_path / "png", f"{model.name}_a.png", model_hash(model))
    (tmp_path / "gltf").mkdir()
    (tmp_path / "gltf" / f"{model.name}.glb").write_bytes(b"glb")
    deliverables = tmp_path / "deliverables"
    paths = publish(model, tmp_path, deliverables)
    assert (deliverables / model.name / "png" / f"{model.name}_a.png").exists()
    assert (deliverables / model.name / "gltf" / f"{model.name}.glb").exists()
    # png + its render sidecar + glb
    assert len(paths) == 3
