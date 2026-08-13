"""Self-contained offline web viewer for an exported GLB (TASK-06-06).

Writes a single HTML file at `output/viewer/<name>.html` that embeds the GLB
as a base64 data URI plus an inlined copy of three.js, its GLTFLoader and
OrbitControls -- no network requests at all, so the file works from the local
filesystem with the network disconnected. If the GLB exceeds 8 MB the GLB is
kept as a sibling file and referenced relatively instead (RISK-06-01).
"""
from __future__ import annotations

import base64
from pathlib import Path

_ASSETS = Path(__file__).resolve().parent / "assets"
INLINE_GLB_LIMIT_BYTES = 8 * 1024 * 1024


def _read_asset(name: str) -> str:
    return (_ASSETS / name).read_text(encoding="utf-8")


def write_viewer(model_name: str, glb_path: Path, out_dir: Path) -> Path:
    """Write the self-contained viewer HTML next to the GLB."""
    viewer_dir = out_dir / "viewer"
    viewer_dir.mkdir(parents=True, exist_ok=True)
    html_path = viewer_dir / f"{model_name}.html"

    glb = Path(glb_path)
    template = _read_asset("viewer_template.html")
    template = template.replace("__TITLE__", model_name)
    template = template.replace("__THREE_JS__", _read_asset("three.min.js"))
    template = template.replace("__GLTF_LOADER__", _read_asset("GLTFLoader.js"))
    template = template.replace("__ORBIT_CONTROLS__", _read_asset("OrbitControls.js"))

    if glb.exists() and glb.stat().st_size <= INLINE_GLB_LIMIT_BYTES:
        b64 = base64.b64encode(glb.read_bytes()).decode("ascii")
        # Decode to an ArrayBuffer, not a string: GLTFLoader.parse treats a JS
        # string as glTF-JSON text, so passing atob()'s binary string made it
        # JSON.parse("glTF…") and fail — the viewer rendered nothing.
        load_call = (
            f"var _b64='{b64}';"
            "var _bin=atob(_b64);"
            "var _buf=new Uint8Array(_bin.length);"
            "for(var _i=0;_i<_bin.length;_i++){_buf[_i]=_bin.charCodeAt(_i);}"
            "loader.parse(_buf.buffer, '', onModel, onModelError);"
        )
        html = template.replace("__LOAD_CALL__", load_call)
    else:
        # Large model: reference the GLB relatively so the HTML stays small.
        relative = glb.name if viewer_dir == glb.parent else _relative_to(glb, viewer_dir)
        load_call = (
            f"fetch('{relative}').then(function(r){{return r.arrayBuffer();}})"
            ".then(function(b){loader.parse(b, '', onModel, onModelError);});"
        )
        html = template.replace("__LOAD_CALL__", load_call)
    html_path.write_text(html, encoding="utf-8")
    return html_path


def _relative_to(path: Path, base_dir: Path) -> str:
    try:
        return path.resolve().relative_to(base_dir.resolve()).as_posix()
    except ValueError:
        return path.resolve().as_posix()
