"""Hash-verified publish (PHASE-06): copy a model's artifacts into a
deliverable directory only when every render's sidecar matches the model."""
from __future__ import annotations

import shutil
from pathlib import Path

from .model import CompiledModel, read_render_sidecar


def verify_fresh(model: CompiledModel, out_dir: Path) -> list[tuple[Path, str | None]]:
    """Delegates to freshness (C5): declared views, not every PNG on disk."""
    from .freshness import check_freshness
    from pathlib import Path as P
    report = check_freshness(model, P(out_dir), kind="warn")
    stale = []
    for name in report["stale"] + report["missing"]:
        if not name.endswith(".png"):
            continue
        pp = P(out_dir) / "png" / name
        sc = read_render_sidecar(pp)
        stale.append((pp, sc.get("model_hash") if sc else None))
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
    from .freshness import check_freshness
    report = check_freshness(model, Path(out_dir), kind="refuse")
    if not report["is_fresh"] and not force:
        raise RuntimeError(report["message"])

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
