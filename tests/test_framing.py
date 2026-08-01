"""Framing assertions against real renders (TEST-008/009). These are slow
(they invoke Blender) and are marked so they can be skipped in CI."""

from pathlib import Path

import pytest

from homedesign import orchestrator

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

    Only the top 55% of the frame is scanned -- the ground plane spans the
    full width below the horizon and would otherwise make the building's
    horizontal occupancy look like 100%.
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


def test_tubehouse_mini_exterior_framed(tmp_path):
    """The exterior render contains the whole building: the non-sky bbox
    occupies >30% and <95% of the frame in each dimension (TEST-008)."""
    out = REPO_ROOT / "output"
    model_path = out / "compiled" / "tubehouse-mini.model.json"
    if not model_path.exists():
        pytest.skip("compiled model not present; run `homedesign build` first")
    png = out / "png" / "tubehouse-mini_exterior.png"
    if not png.exists():
        pytest.skip("render not present; run `homedesign build` first")

    img_w, img_h = __import__("PIL.Image", fromlist=["Image"]).open(png).size
    min_x, min_y, max_x, max_y = _non_sky_bbox(png)
    bw, bh = max_x - min_x, max_y - min_y
    assert bw / img_w > 0.30, f"building too narrow: {bw/img_w:.0%}"
    assert bw / img_w < 0.95
    assert bh / img_h > 0.30, f"building too short: {bh/img_h:.0%}"
    assert bh / img_h < 0.95
