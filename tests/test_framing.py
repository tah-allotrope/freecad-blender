"""Framing assertions against real renders (PHASE-01). These invoke Blender
and are skipped in CI when it is unavailable (CON-002)."""

import json
from pathlib import Path

import pytest

from homedesign import orchestrator
from homedesign.compiler import compile_spec

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "spec" / "examples"

blender_available = True
try:
    orchestrator.find_blender()
except FileNotFoundError:
    blender_available = False

pytestmark = pytest.mark.skipif(
    not blender_available, reason="Blender not installed"
)


def _non_sky_bbox(png: Path) -> tuple[int, int, int, int]:
    """Bounding box of pixels that differ from the sky colour.

    Only the top 55% of the frame is scanned: the ground plane sits below the
    horizon (row ~50%+) and would otherwise stretch the bbox edge-to-edge.
    """
    from PIL import Image

    img = Image.open(png).convert("RGB")
    w, h = img.size
    px = img.load()
    scan_h = int(h * 0.55)
    min_x, min_y, max_x, max_y = w, scan_h, -1, -1
    # Sample the true sky from the top-left corner of THIS render (EEVEE and
    # Cycles render the world colour slightly differently).
    sky = px[8, 8]
    for y in range(0, scan_h, 2):
        for x in range(0, w, 2):
            r, g, b = px[x, y]
            if abs(r - sky[0]) + abs(g - sky[1]) + abs(b - sky[2]) > 30:
                min_x, max_x = min(min_x, x), max(max_x, x)
                min_y, max_y = min(min_y, y), max(max_y, y)
    return min_x, min_y, max_x, max_y


def _ensure_render() -> Path:
    """Compile + build the tubehouse-mini preview render if it is not on disk."""
    out = REPO_ROOT / "output"
    model_path = out / "compiled" / "tubehouse-mini.model.json"
    png = out / "png" / "tubehouse-mini_exterior.png"
    if png.exists():
        return png
    if not model_path.exists():
        spec = json.loads((EXAMPLES / "tubehouse-mini.json").read_text())
        model = compile_spec(spec)
        model_path.parent.mkdir(parents=True, exist_ok=True)
        model_path.write_text(json.dumps(model.to_dict(), indent=2))
    orchestrator.build_scene(model_path, out)
    return png


def test_tubehouse_mini_exterior_framed(tmp_path):
    """The exterior render contains the whole building: the non-sky bbox must
    not touch any frame edge, with sky visible above the roof. This is the
    assertion the old test was blind to -- the broken render's building
    overflowed the top edge (min_y == 0), which this now catches."""
    png = _ensure_render()

    img_w, img_h = __import__("PIL.Image", fromlist=["Image"]).open(png).size
    min_x, min_y, max_x, max_y = _non_sky_bbox(png)
    bw = max_x - min_x
    assert min_x > 0.02 * img_w, f"building touches left edge (min_x={min_x})"
    assert max_x < 0.98 * img_w, f"building touches right edge (max_x={max_x})"
    assert min_y > 0.005 * img_h, f"no sky above the roof (min_y={min_y})"
    assert 0.12 < bw / img_w < 0.95, f"building width {bw / img_w:.0%} out of band"
