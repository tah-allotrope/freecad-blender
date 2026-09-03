"""Read a Radiance `.hdr` and tone-map it to a small LDR preview.

The web viewer wants an environment map so glass and metal have something to
reflect (PR TASK-05-05), but it has no RGBELoader — the three.js bundle inlined
into the page is deliberately minimal, and adding a loader for a 6 MB float
image would blow the page budget for a reflection nobody inspects pixel-wise.

So the cached HDRI is decoded here, tone-mapped, and shrunk to a small
equirectangular JPEG that inlines as a data URI in a few tens of kilobytes.
`THREE.TextureLoader` reads that with no extra code, and with
`EquirectangularReflectionMapping` it drives both the background and the
reflections.

Pure Python plus numpy and Pillow — no bpy, so it is importable and testable
outside Blender.
"""
from __future__ import annotations

import base64
import io
from pathlib import Path

import numpy as np
from PIL import Image


def read_hdr(path: Path) -> np.ndarray:
    """Decode a Radiance RGBE file to a float32 `(height, width, 3)` array.

    Handles the adaptive-RLE scanline format that every modern writer emits,
    and falls back to flat RGBE for the old format.
    """
    data = Path(path).read_bytes()
    pos = 0

    # --- header: lines until a blank one, then the resolution line ---------
    def readline() -> str:
        nonlocal pos
        end = data.index(b"\n", pos)
        line = data[pos:end].decode("latin-1")
        pos = end + 1
        return line

    magic = readline()
    if not magic.startswith("#?"):
        raise ValueError(f"{path}: not a Radiance file (magic {magic!r})")
    while True:
        line = readline()
        if line.strip() == "":
            break
    res = readline().split()
    if len(res) != 4 or res[0] != "-Y" or res[2] != "+X":
        raise ValueError(f"{path}: unsupported resolution line {res!r}")
    height, width = int(res[1]), int(res[3])

    rgbe = np.zeros((height, width, 4), dtype=np.uint8)
    buf = np.frombuffer(data, dtype=np.uint8)

    for y in range(height):
        if pos + 4 > len(buf):
            raise ValueError(f"{path}: truncated at scanline {y}")
        header = buf[pos:pos + 4]
        is_rle = (
            width >= 8 and width < 32768
            and header[0] == 2 and header[1] == 2
            and (int(header[2]) << 8 | int(header[3])) == width
        )
        if not is_rle:
            # Flat RGBE: width * 4 bytes, no run-length coding.
            row = buf[pos:pos + width * 4]
            if row.size < width * 4:
                raise ValueError(f"{path}: truncated flat scanline {y}")
            rgbe[y] = row.reshape(width, 4)
            pos += width * 4
            continue
        pos += 4
        for channel in range(4):
            x = 0
            while x < width:
                count = int(buf[pos])
                pos += 1
                if count > 128:  # a run of one repeated value
                    run = count - 128
                    rgbe[y, x:x + run, channel] = buf[pos]
                    pos += 1
                    x += run
                else:  # a literal span
                    rgbe[y, x:x + count, channel] = buf[pos:pos + count]
                    pos += count
                    x += count

    exponent = rgbe[:, :, 3].astype(np.int32)
    scale = np.where(exponent == 0, 0.0, np.ldexp(1.0, exponent - (128 + 8)))
    return (rgbe[:, :, :3].astype(np.float32) + 0.5) * scale[:, :, None].astype(np.float32)


def tone_map(linear: np.ndarray, exposure: float = 1.0) -> np.ndarray:
    """Reinhard tone-map plus sRGB transfer, to uint8."""
    x = np.clip(linear * exposure, 0.0, None)
    mapped = x / (1.0 + x)
    srgb = np.where(mapped <= 0.0031308, mapped * 12.92,
                    1.055 * np.power(np.clip(mapped, 1e-8, None), 1 / 2.4) - 0.055)
    return (np.clip(srgb, 0.0, 1.0) * 255.0 + 0.5).astype(np.uint8)


def auto_exposure(linear: np.ndarray, target_srgb: float = 0.65) -> float:
    """Exposure that maps the sky's median luminance to `target_srgb`.

    A clear-sky HDRI is dominated by its sun disc — 135680 against a sky median
    of 0.125 on the noon sky used here — so a fixed exposure of 1.0 renders the
    sky itself as near-black. Metering on the median of the upper third of the
    dome (sky, excluding the ground half and robust to the sun) gives a preview
    that reads as daylight on any HDRI.
    """
    sky = linear[: max(1, linear.shape[0] // 3)]
    median = float(np.median(sky.mean(axis=2)))
    if median <= 1e-6:
        return 1.0
    # Invert the Reinhard + sRGB transfer for the target, then solve for gain.
    linear_target = ((target_srgb + 0.055) / 1.055) ** 2.4
    mapped = min(linear_target, 0.999)
    return float((mapped / (1.0 - mapped)) / median)


def equirect_preview_jpeg(hdr_path: Path, width: int = 512, quality: int = 80,
                          exposure: float | None = None) -> bytes:
    """A small tone-mapped equirectangular JPEG of a cached HDRI.

    `exposure` defaults to metering the sky (see `auto_exposure`).
    """
    linear = read_hdr(hdr_path)
    if exposure is None:
        exposure = auto_exposure(linear)
    img = Image.fromarray(tone_map(linear, exposure), mode="RGB")
    height = max(1, width // 2)
    img = img.resize((width, height), Image.LANCZOS)
    out = io.BytesIO()
    img.save(out, format="JPEG", quality=quality, optimize=True)
    return out.getvalue()


def equirect_data_uri(hdr_path: Path, width: int = 512, quality: int = 80,
                      exposure: float | None = None) -> str:
    """The same preview, ready to drop into `THREE.TextureLoader().load(...)`."""
    payload = equirect_preview_jpeg(hdr_path, width, quality, exposure)
    return "data:image/jpeg;base64," + base64.b64encode(payload).decode("ascii")
