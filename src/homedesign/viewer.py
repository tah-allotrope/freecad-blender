"""Self-contained offline web viewers for an exported GLB (TASK-06-06).

Writes a single HTML file at `output/viewer/<name>.html` that embeds the GLB
as a base64 data URI plus an inlined copy of three.js, its GLTFLoader and
OrbitControls -- no network requests at all, so the file works from the local
filesystem with the network disconnected. If the GLB exceeds 8 MB the GLB is
kept as a sibling file and referenced relatively instead (RISK-06-01).

`write_floor_viewer` writes a second page, `<name>-floors.html`, that pairs
each storey's 2D plan SVG with a 3D pane isolated to that storey alone --
the whole-building viewer is hard to read room-by-room because every floor
above the one you care about blocks the view.
"""
from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

_ASSETS = Path(__file__).resolve().parent / "assets"
INLINE_GLB_LIMIT_BYTES = 8 * 1024 * 1024


def _read_asset(name: str) -> str:
    return (_ASSETS / name).read_text(encoding="utf-8")


def optimize_glb(glb_path: Path) -> bool:
    """In-place glTF optimization (dedup + weld + quantize) via
    `@gltf-transform/cli`.

    Raises `RuntimeError` naming `npx` when the `npx` executable is not
    available — callers must treat a missing Node toolchain as a hard error,
    not a silent no-op.
    """
    if shutil.which("npx") is None:
        raise RuntimeError("npx not found: gltf-transform requires npx")
    glb_path = Path(glb_path)
    try:
        with tempfile.TemporaryDirectory() as td:
            a, b, c = Path(td) / "a.glb", Path(td) / "b.glb", Path(td) / "c.glb"
            for cmd, src, dst in (
                ("dedup", glb_path, a),
                ("weld", a, b),
                ("quantize", b, c),
            ):
                subprocess.run(
                    ["npx", "--yes", "@gltf-transform/cli", cmd, str(src), str(dst)],
                    check=True, capture_output=True, timeout=180,
                    # npx resolves to npx.CMD on Windows; CreateProcess can't
                    # exec a .CMD directly without going through cmd.exe.
                    shell=(os.name == "nt"),
                )
            shutil.copy2(c, glb_path)
        return True
    except Exception:
        raise RuntimeError("npx not found: gltf-transform requires npx")


_B64_CHUNK_CHARS = 2000


def _load_call(glb: Path, viewer_dir: Path, build: str | None = None) -> str:
    """JS that fetches/decodes the GLB and hands it to `loader.parse`.

    For the `light` build the GLB is always inlined as base64url and the
    function raises instead of silently falling back to a relative `fetch()`
    reference — the light viewer must work offline from a single file.
    """
    # Light build: never fall back to a relative fetch(); inline or raise.
    if build == "light":
        if not glb.exists():
            raise FileNotFoundError(f"GLB not found for light build: {glb}")
        size = glb.stat().st_size
        # Enforce both the user-visible budget (6 MiB) and the technical
        # inline ceiling (8 MiB) — a light GLB that exceeds either must be
        # treated as an error, not a silent fetch().
        assert_within_budget(glb, "light")
        if size > INLINE_GLB_LIMIT_BYTES:
            raise ValueError(
                f"light GLB size {size} exceeds inline limit {INLINE_GLB_LIMIT_BYTES} "
                f"({size/1024/1024:.1f} MiB > {INLINE_GLB_LIMIT_BYTES/1024/1024:.0f} MiB)"
            )
        b64url = base64.urlsafe_b64encode(glb.read_bytes()).decode("ascii")
        chunks = [b64url[i : i + _B64_CHUNK_CHARS] for i in range(0, len(b64url), _B64_CHUNK_CHARS)]
        b64_literal = "[" + ",\n".join(f"'{c}'" for c in chunks) + "].join('')"
        return (
            f"var _b64={b64_literal};"
            "_b64=_b64.replace(/-/g,'+').replace(/_/g,'/');"
            "var _bin=atob(_b64);"
            "var _buf=new Uint8Array(_bin.length);"
            "for(var _i=0;_i<_bin.length;_i++){_buf[_i]=_bin.charCodeAt(_i);}"
            "loader.parse(_buf.buffer, '', onModel, onModelError);"
        )
    if glb.exists() and glb.stat().st_size <= INLINE_GLB_LIMIT_BYTES:
        b64url = base64.urlsafe_b64encode(glb.read_bytes()).decode("ascii")
        chunks = [b64url[i : i + _B64_CHUNK_CHARS] for i in range(0, len(b64url), _B64_CHUNK_CHARS)]
        b64_literal = "[" + ",\\n".join(f"'{c}'" for c in chunks) + "].join('')"
        return (
            f"var _b64={b64_literal};"
            "_b64=_b64.replace(/-/g,'+').replace(/_/g,'/');"
            "var _bin=atob(_b64);"
            "var _buf=new Uint8Array(_bin.length);"
            "for(var _i=0;_i<_bin.length;_i++){_buf[_i]=_bin.charCodeAt(_i);}"
            "loader.parse(_buf.buffer, '', onModel, onModelError);"
        )
    relative = glb.name if viewer_dir == glb.parent else _relative_to(glb, viewer_dir)
    return (
        f"fetch('{relative}').then(function(r){{return r.arrayBuffer();}})"
        ".then(function(b){loader.parse(b, '', onModel, onModelError);});"
    )


def _badge_text(build: str) -> str:
    if build == "light":
        return "PHIÊN BẢN NHẸ — ĐIỆN THOẠI"
    if build == "full":
        return "PHIÊN BẢN ĐẦY ĐỦ — MÁY TÍNH"
    raise ValueError(f"unknown build {build!r}")


def write_viewer(model_name: str, glb_path: Path, out_dir: Path, build: str = "full") -> Path:
    """Write the self-contained whole-building viewer HTML next to the GLB."""
    if build not in ("light", "full"):
        raise ValueError(f"unknown build {build!r}")
    glb = Path(glb_path)
    # Enforce size budget before embedding — light must be ≤6 MiB, full ≤25 MiB.
    # For light this also guarantees the later _load_call inline path succeeds
    # (no silent fallback to fetch()).
    assert_within_budget(glb, build)
    viewer_dir = out_dir / "viewer"
    viewer_dir.mkdir(parents=True, exist_ok=True)
    # Keep backwards compat: write_viewer("mini", ...) -> mini.html (full badge).
    # For dual-build publishing we also need suffixed copies light/full.
    if build == "full":
        html_path = viewer_dir / f"{model_name}.html"
    else:
        html_path = viewer_dir / f"{model_name}-{build}.html"

    template = _read_asset("viewer_template.html")
    template = template.replace("__TITLE__", model_name)
    template = template.replace("__BUILD_BADGE__", _badge_text(build))
    # Legacy placeholder fallback: if template still contains hardcoded badge, keep it.
    template = template.replace("__THREE_JS__", _read_asset("three.min.js"))
    template = template.replace("__GLTF_LOADER__", _read_asset("GLTFLoader.js"))
    template = template.replace("__ORBIT_CONTROLS__", _read_asset("OrbitControls.js"))
    html = template.replace("__LOAD_CALL__", _load_call(glb, viewer_dir, build=build))
    html_path.write_text(html, encoding="utf-8")
    # For full builds also emit the explicit -full.html sibling so docs can link
    # to both light/full names without aliasing, while preserving the historic
    # viewer/<name>.html location used by tests and the single-file publish path.
    if build == "full":
        full_path = viewer_dir / f"{model_name}-full.html"
        if full_path != html_path:
            full_path.write_text(html, encoding="utf-8")
    return html_path


def write_floor_viewer(
    model_name: str, glb_path: Path, storeys: list[dict], svg_dir: Path, out_dir: Path,
    build: str = "full",
) -> Path | None:
    """Write the per-floor viewer HTML (2D plan + floor-isolated 3D pane).

    `storeys` is the compiled model's `storeys` list (each needs `name`,
    `base_z`, `height_mm`); `svg_dir` holds the plan SVGs written by
    `plan2d.write_plans`, named `<model_name>_f<level>.svg`. Returns None
    (writing nothing) if any storey's plan SVG is missing, since the page
    would otherwise silently render blank plan panels.
    """
    if build not in ("light", "full"):
        raise ValueError(f"unknown build {build!r}")
    svgs: list[str] = []
    for level in range(len(storeys)):
        svg_path = Path(svg_dir) / f"{model_name}_f{level}.svg"
        if not svg_path.exists():
            return None
        text = svg_path.read_text(encoding="utf-8")
        # The plan SVGs carry a viewBox but no width/height attributes, so a
        # browser has no intrinsic size to lay out until CSS gives it one --
        # stamping width/height="100%" makes each <svg> a normal responsive
        # replaced element that fills its container and lets the existing
        # preserveAspectRatio="xMidYMid meet" do the letterboxing.
        svgs.append(text.replace("<svg ", '<svg width="100%" height="100%" ', 1))

    viewer_dir = out_dir / "viewer"
    viewer_dir.mkdir(parents=True, exist_ok=True)
    html_path = viewer_dir / f"{model_name}-floors.html"

    tab_parts = []
    for i, s in enumerate(storeys):
        active_attr = ' class="active"' if i == 0 else ""
        pressed = "true" if i == 0 else "false"
        tab_parts.append(
            f'<button type="button" aria-pressed="{pressed}"{active_attr}>{_escape(s["name"])}</button>'
        )
    tabs = "".join(tab_parts)
    plans = "".join(
        f'<div class="plan{" active" if i == 0 else ""}" data-floor="{i}">'
        f'<div class="plan-sheet">{svg}</div></div>'
        for i, svg in enumerate(svgs)
    )
    bands = []
    for i, s in enumerate(storeys):
        z0 = s["base_z"] / 1000.0
        is_last = i == len(storeys) - 1
        z1 = 1.0e9 if is_last else (storeys[i + 1]["base_z"]) / 1000.0
        bands.append({"name": s["name"], "z0": z0, "z1": z1})

    glb = Path(glb_path)
    template = _read_asset("floor_viewer_template.html")
    template = template.replace("__TITLE__", model_name)
    template = template.replace("__BUILD_BADGE__", _badge_text(build))
    template = template.replace("__THREE_JS__", _read_asset("three.min.js"))
    template = template.replace("__GLTF_LOADER__", _read_asset("GLTFLoader.js"))
    template = template.replace("__ORBIT_CONTROLS__", _read_asset("OrbitControls.js"))
    template = template.replace("__FLOOR_TABS__", tabs)
    template = template.replace("__FLOOR_PLANS__", plans)
    template = template.replace("__FLOOR_BANDS_JSON__", json.dumps(bands))
    html = template.replace("__LOAD_CALL__", _load_call(glb, viewer_dir, build=build))
    html_path.write_text(html, encoding="utf-8")
    if build != "light":
        try:
            import shutil
            shutil.copy2(glb_path, out_dir / glb_path.name)
        except Exception:
            pass
    return html_path


def _escape(text: str) -> str:
    return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;").replace('"', "&quot;")


def _relative_to(path: Path, base_dir: Path) -> str:
    try:
        return path.resolve().relative_to(base_dir.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()


def glb_size_budget(build: str) -> int:
    if build == "light":
        return 6 * 1024 * 1024
    if build == "full":
        return 25 * 1024 * 1024
    raise ValueError(f"unknown build {build!r}")


def assert_within_budget(glb_path, build: str) -> None:
    import pathlib

    path = pathlib.Path(glb_path)
    size = path.stat().st_size if path.exists() else 0
    budget = glb_size_budget(build)
    if size > budget:
        raise ValueError(
            f"GLB size {size} exceeds budget {budget} for build {build!r} "
            f"({size/1024/1024:.1f} MiB > {budget/1024/1024:.0f} MiB)"
        )


def room_label_data(model) -> list[dict]:
    out = []
    for storey in model.storeys:
        for room in storey.rooms:
            # center of room rect
            x_m = (room.rect.x + room.rect.w / 2) / 1000
            y_m = (room.rect.y + room.rect.d / 2) / 1000
            z_m = (storey.base_z + (room.level_mm or 0)) / 1000
            level_tag = f"+{storey.base_z/1000:.3f}" if room.level_mm is None else f"+{(storey.base_z + room.level_mm)/1000:.3f}"
            # if level_mm present, make tag from base_z+level_mm else base_z
            if room.level_mm is not None:
                level_tag = f"+{(storey.base_z + room.level_mm)/1000:.3f}"
            out.append({"text": room.name or room.id, "level_tag": level_tag, "x_m": x_m, "y_m": y_m, "z_m": z_m})
    return out
