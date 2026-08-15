"""Hash-verified publish (PHASE-06): copy a model's artifacts into a
deliverable directory only when every render's sidecar matches the model."""
from __future__ import annotations

import shutil
from pathlib import Path

from .model import CompiledModel, model_hash, read_render_sidecar


def verify_fresh(model: CompiledModel, out_dir: Path) -> list[tuple[Path, str | None]]:
    """One `(png_path, sidecar_hash_or_None)` tuple for every render of this
    model whose sidecar hash does not equal the current model hash; an empty
    list means the gallery is fully fresh."""
    current = model_hash(model)
    stale: list[tuple[Path, str | None]] = []
    png_dir = Path(out_dir) / "png"
    if not png_dir.exists():
        return stale
    for p in sorted(png_dir.glob(f"{model.name}_*.png")):
        sidecar = read_render_sidecar(p)
        if sidecar is None or sidecar.get("model_hash") != current:
            stale.append((p, sidecar.get("model_hash") if sidecar else None))
    return stale


def publish(
    model: CompiledModel,
    out_dir: Path,
    deliverables_dir: Path,
    force: bool = False,
) -> list[Path]:
    """Copy this model's `png/`, `gltf/`, `viewer/` and `pdf/` artifacts into
    `deliverables_dir / <name> / <subdir>/` and return the written paths.

    Raises `RuntimeError` naming every stale file when the gallery is not fresh
    and `force` is `False`.
    """
    out_dir = Path(out_dir)
    deliverables_dir = Path(deliverables_dir)
    stale = verify_fresh(model, out_dir)
    if stale and not force:
        names = ", ".join(p.name for p, _ in stale)
        raise RuntimeError(f"stale render(s) for model {model_hash(model)}: {names}")

    dest = deliverables_dir / model.name
    written: list[Path] = []
    for sub in ("png", "gltf", "viewer", "pdf"):
        src_dir = out_dir / sub
        if not src_dir.is_dir():
            continue
        dst_dir = dest / sub
        dst_dir.mkdir(parents=True, exist_ok=True)
        for f in src_dir.iterdir():
            # Only this model's files, and never the nested pdf/img gallery
            # (downscaled copies that already exist at full res under png/).
            if f.is_file() and f.name.startswith(f"{model.name}"):
                shutil.copy2(f, dst_dir / f.name)
                written.append(dst_dir / f.name)
    return written
