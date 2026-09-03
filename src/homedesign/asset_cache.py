"""Pure cache resolver (ASM-005): no network, hard error on missing."""
from __future__ import annotations
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent
CACHE_ROOT = REPO_ROOT / "assets" / "cache"

def cache_root() -> Path:
    return CACHE_ROOT

def texture_set(family: str) -> dict[str, Path] | None:
    base = CACHE_ROOT / "textures" / family
    if not base.exists():
        return None
    diffuse = base / "diffuse.jpg"
    if not diffuse.exists():
        return None
    out = {"diffuse": diffuse}
    for key in ("rough", "normal", "ao"):
        p = base / f"{key}.jpg"
        if p.exists():
            out[key] = p
    return out

def hdri(name: str) -> Path:
    p = CACHE_ROOT / "hdri" / f"{name}.hdr"
    if not p.exists():
        raise FileNotFoundError(f"HDRI {name!r} not found at {p}")
    return p

def hdri_preview(name: str) -> Path | None:
    """The small LDR equirect JPEG beside an HDRI, or None if not generated.

    Written once by `scripts/fetch_assets.py`, because generating it needs
    numpy and Pillow and the viewer is written from inside Blender, whose
    bundled Python has neither.
    """
    p = CACHE_ROOT / "hdri" / f"{name}_preview.jpg"
    return p if p.exists() else None


def furniture(kind: str) -> Path | None:
    p = CACHE_ROOT / "furniture" / f"{kind}.glb"
    return p if p.exists() else None
