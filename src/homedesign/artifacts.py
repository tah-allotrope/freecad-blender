"""Single catalogue for where a design's artifacts live and what they are called (C4).

A deep module: every path, name, and relative link is asked, not restated.
Writers register, readers ask. Absolute resolution happens here, before any
subprocess boundary.
"""

from __future__ import annotations

from pathlib import Path


def _out_root(out_dir: Path | str) -> Path:
    return Path(out_dir).resolve()


def plan_svg_path(out_dir: Path, model_name: str, level: int) -> Path:
    return _out_root(out_dir) / "svg" / f"{model_name}_f{level}.svg"


def plan_dxf_path(out_dir: Path, model_name: str, level: int) -> Path:
    return _out_root(out_dir) / "dxf" / f"{model_name}_f{level}.dxf"


def elevation_svg_path(out_dir: Path, model_name: str, side: str) -> Path:
    return _out_root(out_dir) / "svg" / f"{model_name}_elev_{side}.svg"


def elevation_dxf_path(out_dir: Path, model_name: str, side: str) -> Path:
    return _out_root(out_dir) / "dxf" / f"{model_name}_elev_{side}.dxf"


def section_svg_path(out_dir: Path, model_name: str, name: str) -> Path:
    return _out_root(out_dir) / "svg" / f"{model_name}_section_{name}.svg"


def section_dxf_path(out_dir: Path, model_name: str, name: str) -> Path:
    return _out_root(out_dir) / "dxf" / f"{model_name}_section_{name}.dxf"


def png_path(out_dir: Path, model_name: str, view: str) -> Path:
    return _out_root(out_dir) / "png" / f"{model_name}_{view}.png"


def png_sidecar_path(out_dir: Path, model_name: str, view: str) -> Path:
    return png_path(out_dir, model_name, view).with_suffix(".png.json")


def viewer_path(out_dir: Path, model_name: str) -> Path:
    return _out_root(out_dir) / "viewer" / f"{model_name}.html"


def viewer_gltf_path(out_dir: Path, model_name: str) -> Path:
    return _out_root(out_dir) / "gltf" / f"{model_name}.glb"


def pdf_path(out_dir: Path, model_name: str) -> Path:
    return _out_root(out_dir) / "pdf" / f"{model_name}-brief.pdf"


def pdf_html_path(out_dir: Path, model_name: str) -> Path:
    return _out_root(out_dir) / "pdf" / f"{model_name}-brief.html"


def blend_path(out_dir: Path, model_name: str) -> Path:
    return _out_root(out_dir) / "blend" / f"{model_name}.blend"


def compiled_path(out_dir: Path, model_name: str) -> Path:
    return _out_root(out_dir) / "compiled" / f"{model_name}.json"


def all_plan_paths(model, out_dir: Path) -> list[Path]:
    """All SVG+DXF plan paths for a model."""
    out = _out_root(out_dir)
    paths = []
    for s in model.storeys:
        paths.append(plan_svg_path(out, model.name, s.level))
        paths.append(plan_dxf_path(out, model.name, s.level))
    return paths


def all_elevation_paths(model, out_dir: Path, sides=("north", "south", "east", "west")) -> list[Path]:
    out = _out_root(out_dir)
    paths = []
    for side in sides:
        paths.append(elevation_svg_path(out, model.name, side))
        paths.append(elevation_dxf_path(out, model.name, side))
    return paths


def all_section_paths(model, out_dir: Path) -> list[Path]:
    out = _out_root(out_dir)
    paths = []
    for sec in (model.sections or []):
        name = sec.get("name", "section")
        paths.append(section_svg_path(out, model.name, name))
        paths.append(section_dxf_path(out, model.name, name))
    # Fallback for models without declared sections (legacy)
    if not paths:
        for name in ("long", "cross_bed"):
            paths.append(section_svg_path(out, model.name, name))
            paths.append(section_dxf_path(out, model.name, name))
    return paths


def all_drawing_paths(model, out_dir: Path) -> list[Path]:
    """Every SVG/DXF that the PDF embeds (plans + elevations + sections)."""
    return all_plan_paths(model, out_dir) + all_elevation_paths(model, out_dir) + all_section_paths(model, out_dir)


def relative_to(src: Path, dst_dir: Path) -> str:
    """Relative link from dst_dir to src (never absolute)."""
    src = Path(src).resolve()
    dst = Path(dst_dir).resolve()
    # Use os.path.relpath for sibling handling, not Path.relative_to which only walks down
    import os

    rel = os.path.relpath(src, dst)
    return rel.replace(os.sep, "/")


def viewer_gltf_relative(out_dir: Path, model_name: str) -> str:
    """Viewer HTML -> GLB link."""
    glb = viewer_gltf_path(out_dir, model_name)
    viewer_dir = _out_root(out_dir) / "viewer"
    return relative_to(glb, viewer_dir)
