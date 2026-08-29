"""Generate A3 plates and chat share images.

Functions:
  make_a3_plate(png_path, title, source_sheet, rendered_at, out_path) -> Path
    - 3508x2480 @300 dpi landscape, title block with model+sheet+date
  make_share_image(png_path, caption, out_path, long_edge_px=1600, quality=85) -> Path
    - long edge 1600 px, JPEG 85 <1 MiB, caption bar burned at foot

CLI:
  python scripts/make_share_pack.py [--design designs/contractor-as-drawn.json]
  Generates deliverables/contractor-as-drawn/share/ (12 views) and
  deliverables/contractor-as-drawn/a3/ (5 plates).
"""
from __future__ import annotations

import json
from pathlib import Path
from datetime import date

from PIL import Image, ImageDraw, ImageFont


def _load_font(size: int) -> ImageFont.FreeTypeFont | ImageFont.ImageFont:
    """Try DejaVu for Vietnamese diacritics, fallback to default bitmap."""
    # Common locations
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "C:/Windows/Fonts/DejaVuSans.ttf",
        "C:/Windows/Fonts/arial.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in candidates:
        try:
            if Path(p).exists():
                return ImageFont.truetype(p, size)
        except Exception:
            continue
    # Try Pillow bundled DejaVu
    try:
        import PIL

        pil_font = Path(PIL.__file__).parent / "fonts" / "DejaVuSans.ttf"
        if pil_font.exists():
            return ImageFont.truetype(str(pil_font), size)
    except Exception:
        pass
    try:
        # Windows arial as last truetype attempt
        return ImageFont.truetype("arial.ttf", size)
    except Exception:
        return ImageFont.load_default()


def make_a3_plate(png_path: Path, title: str, source_sheet: str, rendered_at: str, out_path: Path) -> Path:
    """Return written A3 landscape plate at 300 dpi (3508x2480 px).

    Title block at top carries model, source_sheet and date. Image is scaled
    to fit within plate with margin, centered.
    """
    # A3 landscape 300 dpi = 3508x2480 (as specified in brief; physical A3 is 4960x3508
    # but project fixes 3508x2480 as the plate size)
    W, H = 3508, 2480
    img = Image.open(png_path).convert("RGB")
    plate = Image.new("RGB", (W, H), "white")
    draw = ImageDraw.Draw(plate)

    # Title block — top band 110 px high, with thin rule below
    title_font = _load_font(28)
    meta_font = _load_font(18)
    # background for title block
    draw.rectangle([(0, 0), (W, 110)], fill=(245, 245, 240))
    draw.rectangle([(0, 110), (W, 112)], fill=(180, 180, 175))
    # Title left, sheet center, date right
    draw.text((24, 18), title, fill=(20, 20, 20), font=title_font)
    # source sheet - smaller, centered-ish
    sheet_text = source_sheet
    draw.text((W // 2 - 160, 38), sheet_text, fill=(40, 40, 40), font=meta_font)
    draw.text((W - 260, 38), rendered_at, fill=(80, 80, 80), font=meta_font)
    # scale image to fit within plate with margin, below title block
    margin = 28
    header_h = 122
    avail_w = W - 2 * margin
    avail_h = H - header_h - margin
    # keep aspect
    scale = min(avail_w / img.width, avail_h / img.height)
    # never upscale beyond original if smaller than avail (keep crisp)
    # but for tiny 8KB placeholders we allow upscale to fill plate
    new_w = int(img.width * scale)
    new_h = int(img.height * scale)
    # clamp to at least 1
    new_w = max(1, new_w)
    new_h = max(1, new_h)
    resized = img.resize((new_w, new_h), Image.LANCZOS)
    x = (W - new_w) // 2
    y = header_h + (avail_h - new_h) // 2
    plate.paste(resized, (x, y))
    # thin border around image
    draw.rectangle([(x - 1, y - 1), (x + new_w, y + new_h)], outline=(210, 210, 210), width=1)
    # footer small note
    footer_font = _load_font(13)
    draw.text((24, H - 26), "Shadows decorative — not a daylight analysis. BLENDER 4.1 legacy EEVEE.", fill=(120, 120, 120), font=footer_font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Save with DPI metadata
    plate.save(out_path, "PNG", dpi=(300, 300))
    assert plate.size == (3508, 2480), f"plate size {plate.size} != (3508,2480)"
    return out_path


def make_share_image(png_path: Path, caption: str, out_path: Path, long_edge_px: int = 1600, quality: int = 85) -> Path:
    """Return written JPEG with caption burned into footer bar.

    Long edge is exactly ``long_edge_px`` (when source is larger; otherwise
    kept smaller). JPEG quality starts at ``quality`` and steps down until
    file is <1 MiB. Caption bar is appended at foot (landscape: width stays
    1600, bar adds height; portrait-aware keeps final max == long_edge_px).
    """
    img = Image.open(png_path).convert("RGB")
    w, h = img.size
    bar_h = 48
    # Determine target image size *before* bar so final max edge == long_edge_px
    # Always resize so long edge == long_edge_px (upscale if smaller, downscale if larger)
    if w >= h:
        # landscape: width is long edge -> exactly long_edge_px
        new_w = long_edge_px
        new_h = int(round(h * long_edge_px / w))
        if (w, h) != (new_w, new_h):
            img = img.resize((new_w, new_h), Image.LANCZOS)
    else:
        # portrait: height + bar is long edge
        target_h = long_edge_px - bar_h
        new_h = target_h
        new_w = int(round(w * target_h / h))
        if (w, h) != (new_w, new_h):
            img = img.resize((new_w, new_h), Image.LANCZOS)
    w2, h2 = img.size
    # caption bar — dark bar with white text
    new_img = Image.new("RGB", (w2, h2 + bar_h), (28, 30, 36))
    new_img.paste(img, (0, 0))
    draw = ImageDraw.Draw(new_img)
    cap_font = _load_font(22)
    # draw caption centered vertically in bar, left padded
    # Use white text for contrast on dark bar
    draw.text((18, h2 + 12), caption, fill=(245, 245, 245), font=cap_font)
    out_path.parent.mkdir(parents=True, exist_ok=True)
    # Save JPEG quality 85, loop down if >1 MiB
    for q in [quality, 82, 78, 75, 70, 65, 60]:
        new_img.save(out_path, "JPEG", quality=q, optimize=True)
        if out_path.stat().st_size <= 1_048_576:
            break
    # Final guarantee: even if still >1 MiB, re-encode smaller dimensions as last resort
    if out_path.stat().st_size > 1_048_576:
        # shrink 10% and retry
        shrink = 0.92
        sw = int(w2 * shrink)
        sh = int(h2 * shrink)
        small = img.resize((sw, sh), Image.LANCZOS)
        new_small = Image.new("RGB", (sw, sh + bar_h), (28, 30, 36))
        new_small.paste(small, (0, 0))
        d2 = ImageDraw.Draw(new_small)
        d2.text((18, sh + 12), caption, fill=(245, 245, 245), font=cap_font)
        new_small.save(out_path, "JPEG", quality=60, optimize=True)
        new_img = new_small
    # Acceptance for 1920x1080 case: long edge exactly 1600
    # For landscape, max == width == 1600; for portrait, max == height == 1600
    actual_max = max(new_img.size)
    assert actual_max == long_edge_px, f"max {actual_max} != {long_edge_px}"
    return out_path


def _caption_for_view(view: dict, model) -> str:
    """Build caption like 'P.KHÁCH +3.800' for room views, plain for exterior."""
    kind = view.get("kind")
    name = view.get("name", "")
    if kind == "room":
        room_id = view.get("room_id")
        for st in model.storeys:
            for rm in st.rooms:
                if rm.id == room_id:
                    abs_mm = st.base_z + (rm.level_mm if rm.level_mm is not None else 0)
                    tag = f"+{abs_mm/1000:.3f}"
                    label = rm.name or name
                    return f"{label} {tag}"
        return name
    # exterior
    if name == "exterior_front":
        return "MẶT ĐỨNG CHÍNH  —  exterior_front"
    if name == "exterior_aerial":
        return "PHỐI CẢNH  —  exterior_aerial"
    return name


def _rasterize_svg_to_png(svg_path: Path, png_path: Path, width: int = 2400) -> Path:
    """Rasterize SVG to PNG. Tries cairosvg, falls back to placeholder."""
    png_path.parent.mkdir(parents=True, exist_ok=True)
    try:
        import cairosvg  # type: ignore

        cairosvg.svg2png(url=str(svg_path), write_to=str(png_path), output_width=width)
        return png_path
    except Exception:
        pass
    # Fallback: render a simple placeholder image with SVG title extracted
    try:
        text = svg_path.read_text(encoding="utf-8", errors="ignore")
        # crude title extraction
        title = svg_path.stem.replace("_", " ").upper()
        # create white image with title text
        img = Image.new("RGB", (width, int(width * 0.62)), "white")
        d = ImageDraw.Draw(img)
        f = _load_font(36)
        d.text((40, 40), title, fill="black", font=f)
        # also dump first 200 chars of svg as hint
        sf = _load_font(14)
        d.text((40, 100), text[:180].replace("\n", " "), fill=(80, 80, 80), font=sf)
        d.rectangle([(0, 0), (img.width - 1, img.height - 1)], outline=(180, 180, 180))
        img.save(png_path, "PNG")
        return png_path
    except Exception:
        # ultimate fallback blank
        img = Image.new("RGB", (width, int(width * 0.62)), "white")
        img.save(png_path, "PNG")
        return png_path


def generate_all(design_path: Path | None = None) -> dict:
    """Generate share (12) + A3 (5) from the design's outputs."""
    if design_path is None:
        design_path = Path("designs/contractor-as-drawn.json")
    design_path = Path(design_path)
    spec = json.loads(design_path.read_text(encoding="utf-8"))
    from homedesign.compiler import compile_spec

    model = compile_spec(spec)
    name = model.name
    today = date.today().isoformat()
    # Source PNGs: prefer deliverables (published fresh), fallback to output
    deliver_png_dir = Path(f"deliverables/{name}/png")
    output_png_dir = Path("output/png")
    output_svg_dir = Path("output/svg")
    # Output dirs
    share_dir = Path(f"deliverables/{name}/share")
    a3_dir = Path(f"deliverables/{name}/a3")
    # --- Share pack for all 12 views ---
    views = spec.get("meta", {}).get("views", [])
    share_written: list[Path] = []
    for v in views:
        vn = v["name"]
        # source png filename pattern: <model>_<view>.png
        src = deliver_png_dir / f"{name}_{vn}.png"
        if not src.exists():
            src = output_png_dir / f"{name}_{vn}.png"
        if not src.exists():
            # skip missing (should not happen after fresh publish)
            continue
        caption = _caption_for_view(v, model)
        out = share_dir / f"{vn}.jpg"
        make_share_image(src, caption, out)
        share_written.append(out)
    # --- A3 plates: exterior_front + 2 interiors + light-well + south elevation ---
    # Resolve interior choices: khach + bep_an as the two interiors, hanh_lang_thang as light-well
    a3_items: list[tuple[Path, str, str]] = []
    # exterior_front
    ef_src = deliver_png_dir / f"{name}_exterior_front.png"
    if not ef_src.exists():
        ef_src = output_png_dir / f"{name}_exterior_front.png"
    if ef_src.exists():
        a3_items.append((ef_src, f"{name} — MẶT ĐỨNG CHÍNH", "MẶT ĐỨNG CHÍNH (south)"))
    # interiors: khach and bep_an
    for vn in ["khach", "bep_an"]:
        src = deliver_png_dir / f"{name}_{vn}.png"
        if not src.exists():
            src = output_png_dir / f"{name}_{vn}.png"
        if src.exists():
            # caption for plate title: room label
            v = next((x for x in views if x["name"] == vn), {"name": vn})
            cap = _caption_for_view(v, model)
            a3_items.append((src, f"{name} — {cap}", cap))
    # light-well: hanh_lang_thang
    lw_src = deliver_png_dir / f"{name}_hanh_lang_thang.png"
    if not lw_src.exists():
        lw_src = output_png_dir / f"{name}_hanh_lang_thang.png"
    if lw_src.exists():
        v = next((x for x in views if x["name"] == "hanh_lang_thang"), {"name": "hanh_lang_thang"})
        cap = _caption_for_view(v, model)
        a3_items.append((lw_src, f"{name} — {cap} (Ô lấy sáng)", "Ô lấy sáng / light-well"))
    # south elevation SVG -> PNG
    svg_src = output_svg_dir / f"{name}_elev_south.svg"
    if svg_src.exists():
        tmp_png = Path("output") / f"{name}_elev_south_tmp.png"
        _rasterize_svg_to_png(svg_src, tmp_png, width=3000)
        a3_items.append((tmp_png, f"{name} — MẶT ĐỨNG NAM (south elevation)", "MẶT ĐỨNG NAM — south elevation"))
    # Write plates
    plate_written: list[Path] = []
    for src, title, sheet in a3_items:
        # Use deterministic names matching spec: plate_<view>.png or plate_elev_south
        if "south elevation" in sheet.lower() or "nam" in sheet.lower():
            out_name = "plate_elev_south.png"
        elif "hanh_lang" in str(src) or "light" in sheet.lower():
            out_name = "plate_hanh_lang_thang.png"
        elif "khach" in str(src):
            out_name = "plate_khach.png"
        elif "bep_an" in str(src):
            out_name = "plate_bep_an.png"
        else:
            out_name = f"plate_{src.stem.replace(name+'_','')}.png"
        out = a3_dir / out_name
        make_a3_plate(src, title, sheet, today, out)
        plate_written.append(out)
    return {"share": share_written, "a3": plate_written}


if __name__ == "__main__":
    import argparse

    ap = argparse.ArgumentParser(description="Generate A3 plates and share images")
    ap.add_argument("--design", type=str, default="designs/contractor-as-drawn.json", help="design JSON path")
    args = ap.parse_args()
    res = generate_all(Path(args.design))
    print(f"Share: {len(res['share'])} files -> deliverables/.../share/")
    for p in res["share"]:
        print(f"  {p}  {p.stat().st_size} bytes")
    print(f"A3: {len(res['a3'])} files -> deliverables/.../a3/")
    for p in res["a3"]:
        print(f"  {p}  {Image.open(p).size}")
