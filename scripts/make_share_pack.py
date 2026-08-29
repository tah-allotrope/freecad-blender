"""Generate A3 plates and chat share images."""
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

def make_a3_plate(png_path: Path, title: str, source_sheet: str, rendered_at: str, out_path: Path) -> Path:
    # A3 landscape 300dpi 3508x2480
    img = Image.open(png_path).convert("RGB")
    plate = Image.new("RGB", (3508, 2480), "white")
    # scale image to fit within plate with margin
    draw = ImageDraw.Draw(plate)
    # title block
    draw.text((20, 20), f"{title} | {source_sheet} | {rendered_at}", fill="black")
    # paste resized image centered
    img_ratio = img.width / img.height
    plate_ratio = 3400 / 2200
    if img_ratio > plate_ratio:
        new_w = 3400
        new_h = int(3400 / img_ratio)
    else:
        new_h = 2200
        new_w = int(2200 * img_ratio)
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    plate.paste(resized, ((3508 - new_w)//2, 120))
    out_path.parent.mkdir(parents=True, exist_ok=True)
    plate.save(out_path, "PNG")
    # ensure exact size
    assert plate.size == (3508, 2480)
    return out_path

def make_share_image(png_path: Path, caption: str, out_path: Path, long_edge_px: int = 1600, quality: int = 85) -> Path:
    img = Image.open(png_path).convert("RGB")
    w, h = img.size
    if max(w, h) > long_edge_px:
        if w >= h:
            new_w = long_edge_px
            new_h = int(h * long_edge_px / w)
        else:
            new_h = long_edge_px
            new_w = int(w * long_edge_px / h)
        img = img.resize((new_w, new_h), Image.LANCZOS)
    # caption bar
    bar_h = 40
    new_img = Image.new("RGB", (img.width, img.height + bar_h), "white")
    new_img.paste(img, (0, 0))
    draw = ImageDraw.Draw(new_img)
    draw.text((10, img.height + 10), caption, fill="black")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    new_img.save(out_path, "JPEG", quality=quality)
    # ensure under 1MB
    if out_path.stat().st_size > 1048576:
        # recompress lower quality
        new_img.save(out_path, "JPEG", quality=75)
    assert max(new_img.size) == long_edge_px or max(new_img.size) < long_edge_px
    return out_path
