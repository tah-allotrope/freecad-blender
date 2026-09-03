"""C5: freshness owner handles all gallery staleness on tmp_path."""

import json
from pathlib import Path

from homedesign.compiler import compile_spec
from homedesign.freshness import check_freshness
from homedesign.model import model_hash, write_render_sidecar


def _model():
    spec = json.loads(Path("spec/examples/tubehouse-mini.json").read_text(encoding="utf-8"))
    m = compile_spec(spec)
    if not m.views:
        from homedesign.model import View
        m.views = [View(name="exterior", kind="exterior_front"), View(name="plan", kind="room", room_id=m.storeys[0].rooms[0].id)]
    return m


def _prepare_gallery(out: Path, model, stale=False, missing=False):
    # Create PNGs for each view
    (out / "png").mkdir(parents=True, exist_ok=True)
    for v in model.views:
        p = out / "png" / f"{model.name}_{v.name}.png"
        p.write_bytes(b"\x89PNG\r\n\x1a\n")
        h = "stale00000000" if stale else model_hash(model)
        write_render_sidecar(p, h, v.name, "final")
    if missing:
        # Remove one
        p = out / "png" / f"{model.name}_{model.views[0].name}.png"
        p.unlink(missing_ok=True)
    # GLB
    (out / "gltf").mkdir(parents=True, exist_ok=True)
    glb = out / "gltf" / f"{model.name}.glb"
    glb.write_bytes(b"glb")
    import json as _json
    (glb.with_suffix(glb.suffix + ".json")).write_text(_json.dumps({"model_hash": model_hash(model)}), encoding="utf-8")


def test_missing_sidecar_is_stale(tmp_path):
    model = _model()
    out = tmp_path / "out"
    _prepare_gallery(out, model)
    # Remove sidecar for first view
    p = out / "png" / f"{model.name}_{model.views[0].name}.png"
    (p.with_suffix(p.suffix + ".json")).unlink()
    report = check_freshness(model, out)
    assert not report["is_fresh"]
    assert p.name in report["stale"]


def test_wrong_hash_is_stale(tmp_path):
    model = _model()
    out = tmp_path / "out"
    _prepare_gallery(out, model, stale=True)
    report = check_freshness(model, out)
    assert not report["is_fresh"]
    assert len(report["stale"]) == len(model.views)


def test_view_added_makes_stale(tmp_path):
    model = _model()
    out = tmp_path / "out"
    _prepare_gallery(out, model)
    # Add a view to model but not to disk
    from homedesign.model import View
    model.views.append(View(name="new_view", kind="exterior_front"))
    report = check_freshness(model, out)
    assert "new_view" in "".join(report["missing"])


def test_view_removed_makes_extra_png_irrelevant(tmp_path):
    model = _model()
    out = tmp_path / "out"
    _prepare_gallery(out, model)
    # Create an extra PNG on disk that is not a declared view
    extra = out / "png" / f"{model.name}_extra.png"
    extra.write_bytes(b"\x89PNG")
    write_render_sidecar(extra, model_hash(model), "extra", "final")
    report = check_freshness(model, out)
    # Extra PNG should not be considered, gallery is still fresh
    assert report["is_fresh"]
    assert "extra" not in "".join(report["stale"] + report["missing"])


def test_mixed_gallery(tmp_path):
    model = _model()
    out = tmp_path / "out"
    _prepare_gallery(out, model)
    # Make one stale, one missing, rest fresh
    p0 = out / "png" / f"{model.name}_{model.views[0].name}.png"
    write_render_sidecar(p0, "stale", model.views[0].name, "final")
    if len(model.views) > 1:
        p1 = out / "png" / f"{model.name}_{model.views[1].name}.png"
        p1.unlink()
    report = check_freshness(model, out)
    assert not report["is_fresh"]
    assert len(report["stale"]) >= 1
    assert len(report["missing"]) >= 1


def test_glb_stale_without_sidecar(tmp_path):
    model = _model()
    out = tmp_path / "out"
    _prepare_gallery(out, model)
    # Remove GLB sidecar
    glb = out / "gltf" / f"{model.name}.glb"
    (glb.with_suffix(glb.suffix + ".json")).unlink()
    report = check_freshness(model, out)
    assert glb.name in report["stale"]
