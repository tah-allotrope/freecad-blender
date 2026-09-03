"""Single owner for is this render stale? (C5).

One module decides what the gallery is, whether each artifact matches the
model in hand, and what a mismatch means (warn / badge / refuse).  The
gallery is the set of PNGs for the model's declared views; the check is
sidecar is None or sidecar.hash != current, extended to GLB/SVG via
their own sidecars or file hashes.  Tests run on tmp_path without
touching deliverables.
"""

from __future__ import annotations

import json
from pathlib import Path
from typing import Literal

from .artifacts import png_path, viewer_gltf_path, pdf_path
from .model import CompiledModel, model_hash, read_render_sidecar


def gallery_png_paths(model: CompiledModel, out_dir: Path) -> list[Path]:
    """Declared gallery: one PNG per model.view, or every PNG on disk when no views declared."""
    if not model.views:
        # Fallback for tests and legacy models with no declared views
        png_dir = Path(out_dir) / "png"
        if not png_dir.exists():
            return []
        return sorted(png_dir.glob(f"{model.name}_*.png"))
    return [png_path(out_dir, model.name, v.name) for v in model.views]


def gallery_all_paths(model: CompiledModel, out_dir: Path) -> list[Path]:
    """Gallery plus GLB and PDF (the deliverable set)."""
    paths = gallery_png_paths(model, out_dir)
    paths.append(viewer_gltf_path(out_dir, model.name))
    paths.append(pdf_path(out_dir, model.name))
    return paths


def check_freshness(
    model: CompiledModel, out_dir: Path, kind: Literal["warn", "refuse"] = "warn"
) -> dict:
    """Return freshness report for the gallery.

    Report keys: current_hash, missing, stale, fresh, is_fresh, message.
    Stale means sidecar missing or hash mismatch; missing means PNG absent.
    kind controls whether stale is an error (refuse) or warning.
    """
    current = model_hash(model)
    missing: list[str] = []
    stale: list[str] = []
    fresh: list[str] = []
    # PNGs
    for p in gallery_png_paths(model, out_dir):
        if not p.exists():
            missing.append(p.name)
            continue
        sidecar = read_render_sidecar(p)
        if sidecar is None or sidecar.get("model_hash") != current:
            stale.append(p.name)
        else:
            fresh.append(p.name)
    # GLB and PDF are considered stale if absent or hash not matching
    # For GLB we check sidecar via .glb.json if present, else file hash
    glb = viewer_gltf_path(out_dir, model.name)
    if glb.exists():
        sidecar_path = glb.with_suffix(glb.suffix + ".json")
        if sidecar_path.exists():
            try:
                data = json.loads(sidecar_path.read_text(encoding="utf-8"))
                if data.get("model_hash") != current:
                    stale.append(glb.name)
                else:
                    fresh.append(glb.name)
            except (OSError, ValueError):
                stale.append(glb.name)
        else:
            stale.append(glb.name)
    is_fresh = not missing and not stale
    message = ""
    if missing:
        message += f"missing: {', '.join(missing)}; "
    if stale:
        message += f"stale: {', '.join(stale)} (model {current}); "
    if kind == "refuse" and (missing or stale):
        message = f"refuse: {message.strip()}"
    return {
        "current_hash": current,
        "missing": missing,
        "stale": stale,
        "fresh": fresh,
        "is_fresh": is_fresh,
        "message": message.strip(),
    }


def assert_fresh(model: CompiledModel, out_dir: Path) -> None:
    """Raise if gallery is not fresh."""
    report = check_freshness(model, out_dir, kind="refuse")
    if not report["is_fresh"]:
        raise RuntimeError(report["message"])
