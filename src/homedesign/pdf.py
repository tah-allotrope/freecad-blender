"""Assembles the architect-brief PDF: an HTML document (cover, narrative,
room schedule, per-floor plans, render gallery, requirements, handover
appendix) printed to PDF via a headless Chromium browser (Edge or Chrome).
Runs in system Python -- never imports bpy.
"""
from __future__ import annotations

import base64
import glob
import os
import shutil
import subprocess
import sys
from pathlib import Path

from .model import CompiledModel, model_hash, read_render_sidecar
from .xmltext import escape_text

PAGE_CSS = """
@page { size: A3 landscape; margin: 14mm;
        @bottom-right { content: counter(page) " / " counter(pages); font-size: 9pt; color: #666; }
        @bottom-left { content: "homedesign"; font-size: 9pt; color: #666; } }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, sans-serif; color: #1a1a1a; margin: 0; }
/* Fixed height (not min-height) + overflow:hidden + flex column so every
   section is hard-capped to exactly one physical page: a flex:1 child
   (an svg or a table wrapper) absorbs whatever space is left after the
   heading instead of pushing content onto a second page. */
.page { page-break-after: always; padding: 10mm; height: calc(297mm - 28mm);
        overflow: hidden; display: flex; flex-direction: column; }
.page:last-child { page-break-after: auto; }
h1 { font-size: 32pt; margin: 0 0 4mm; flex: 0 0 auto; }
h2 { font-size: 20pt; border-bottom: 2px solid #222; padding-bottom: 2mm; margin: 0 0 3mm; flex: 0 0 auto; }
.cover { justify-content: flex-end; background-size: cover; background-position: center;
         color: white; text-shadow: 0 1px 6px rgba(0,0,0,.7); }
.cover h1 { font-size: 44pt; }
table { border-collapse: collapse; width: 100%; font-size: 11pt; }
th, td { border: 1px solid #ccc; padding: 2mm 3mm; text-align: left; }
th { background: #f0f0f0; }
.plan-page svg { width: 100%; height: 100%; flex: 1 1 auto; min-height: 0; }
.gallery { display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; flex: 1 1 auto; min-height: 0; }
.gallery img { width: 100%; height: auto; max-height: 100%; object-fit: contain; border: 1px solid #ddd; }
ul.requirements li { margin-bottom: 2mm; }
/* Compact two-column layout for schedules with many rows (room / opening
   counts scale with storey count and would otherwise spill onto extra
   pages). */
.two-col { display: flex; gap: 6mm; flex: 1 1 auto; min-height: 0; }
.two-col > div { flex: 1; overflow: hidden; }
.compact-table th, .compact-table td { padding: 0.6mm 2mm; font-size: 8pt; }
.stale { color: #b00020; font-weight: bold; font-size: 10pt; }
"""


def build_room_schedule(model: CompiledModel) -> list[dict]:
    schedule = []
    for storey in model.storeys:
        rooms = []
        total = 0.0
        for room in storey.rooms:
            area = round((room.rect.w / 1000) * (room.rect.d / 1000), 1)
            rooms.append({"id": room.id, "type": room.type, "area_m2": area})
            total += area
        schedule.append({
            "level": storey.level,
            "name": storey.name,
            "rooms": rooms,
            "total_m2": round(total, 1),
        })
    return schedule


def _img_data_uri(path: Path) -> str:
    data = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:image/png;base64,{data}"


def downscale_png(src: Path, dst: Path, max_width_px: int = 1400) -> Path:
    """Write a copy of `src` scaled to at most `max_width_px` wide (ASM-007).

    Returns `src` unchanged (and warns on stderr) when Pillow is unavailable.
    """
    try:
        from PIL import Image
    except ImportError:
        print(f"warning: Pillow unavailable; {src.name} not downscaled", file=sys.stderr)
        return src
    img = Image.open(src).convert("RGB")
    if img.width > max_width_px:
        ratio = max_width_px / img.width
        new_h = max(int(img.height * ratio), 1)
        img = img.resize((max_width_px, new_h))
    dst.parent.mkdir(parents=True, exist_ok=True)
    img.save(dst, "PNG")
    return dst


def build_opening_schedule(model: CompiledModel) -> list[dict]:
    """One row per opening: id, storey, type, width, sill, head, rooms."""
    rows = []
    for storey in model.storeys:
        rooms_by_id = {r.id: (r.name or r.id) for r in storey.rooms}
        for o in storey.openings:
            wall = next((w for w in storey.walls if w.id == o.wall_id), None)
            rooms = []
            if wall is not None:
                # The wall's two side room ids are not directly stored on the
                # opening in the compiled model; recover them from the wall
                # neighbourhood: the rooms whose rects share that wall edge.
                for r in storey.rooms:
                    rect = r.rect
                    if wall.orientation == "vertical":
                        if abs(rect.x2 - wall.x) < 1 or abs(rect.x - (wall.x + wall.w)) < 1:
                            if rect.y < wall.y + wall.h and rect.y2 > wall.y:
                                rooms.append(r)
                    else:
                        if abs(rect.y2 - wall.y) < 1 or abs(rect.y - (wall.y + wall.h)) < 1:
                            if rect.x < wall.x + wall.w and rect.x2 > wall.x:
                                rooms.append(r)
            room_labels = [rooms_by_id.get(r.id, r.id) for r in rooms[:2]]
            if not room_labels:
                room_labels = ["exterior", "?"]
            rows.append({
                "id": o.id,
                "storey": storey.level,
                "type": o.type,
                "width_mm": o.width_mm,
                "sill_mm": o.sill_mm,
                "head_mm": o.head_mm,
                "rooms": room_labels,
            })
    return rows


def build_takeoff(model: CompiledModel) -> list[dict]:
    """Per-storey quantities: GFA, wall lengths, opening counts, + totals, and
    a built-envelope row disclosing the actual outer building dimensions
    (TASK-05-07: the gross-vs-plot fact is reported on the drawing set)."""
    rows = []
    total_gfa = total_ext = total_part = total_doors = total_windows = 0.0
    for storey in model.storeys:
        gfa = sum((r.rect.w / 1000) * (r.rect.d / 1000) for r in storey.rooms)
        ext = sum(w.h / 1000 for w in storey.walls if w.kind == "exterior")
        part = sum(w.h / 1000 for w in storey.walls if w.kind == "partition")
        doors = sum(1 for o in storey.openings if o.type == "door")
        windows = sum(1 for o in storey.openings if o.type == "window")
        rows.append({
            "level": storey.level, "name": storey.name,
            "gfa_m2": round(gfa, 1), "exterior_wall_m": round(ext, 1),
            "partition_wall_m": round(part, 1),
            "door_count": doors, "window_count": windows,
        })
        total_gfa += gfa
        total_ext += ext
        total_part += part
        total_doors += doors
        total_windows += windows
    all_walls = [w for s in model.storeys for w in s.walls]
    if all_walls:
        env_w = (max(w.x + w.w for w in all_walls) - min(w.x for w in all_walls)) / 1000
        env_d = (max(w.y + w.h for w in all_walls) - min(w.y for w in all_walls)) / 1000
        rows.append({
            "level": None, "name": "Built envelope (W x D m)",
            "gfa_m2": round(env_w, 1), "exterior_wall_m": round(env_d, 1),
            "partition_wall_m": 0.0, "door_count": "", "window_count": "",
        })
    rows.append({
        "level": None, "name": "Total",
        "gfa_m2": round(total_gfa, 1), "exterior_wall_m": round(total_ext, 1),
        "partition_wall_m": round(total_part, 1),
        "door_count": int(total_doors), "window_count": int(total_windows),
    })
    return rows


def _svg_inline(path: Path) -> str:
    text = path.read_text(encoding="utf-8")
    if text.startswith("<?xml"):
        text = text.split("?>", 1)[1]
    return text


def _cover_page(brief: dict, hero_path: Path | None) -> str:
    style = f"background-image:url('{_img_data_uri(hero_path)}')" if hero_path else ""
    return (
        f'<section class="page cover" style="{style}">'
        f"<h1>{escape_text(brief['title'])}</h1><p>{escape_text(brief.get('subtitle', ''))}</p>"
        f"</section>"
    )


def _narrative_page(brief: dict) -> str:
    paragraphs = "".join(f"<p>{escape_text(p)}</p>" for p in brief.get("narrative", []))
    return f'<section class="page"><h2>Design Intent</h2>{paragraphs}</section>'


def _split_rows(rows: list, n: int) -> list[list]:
    """`rows` split into `n` near-equal chunks, earlier chunks taking any remainder."""
    per = -(-len(rows) // n)  # ceil division
    return [rows[i:i + per] for i in range(0, len(rows), per)] or [[]]


def _schedule_page(schedule: list[dict]) -> str:
    all_rooms = [(s["name"], r) for s in schedule for r in s["rooms"]]
    columns = _split_rows(all_rooms, 2)

    def render_col(items):
        rows = "".join(
            f"<tr><td>{escape_text(name)}</td><td>{escape_text(r['id'])}</td><td>{escape_text(r['type'])}</td><td>{r['area_m2']:.1f}</td></tr>"
            for name, r in items
        )
        return (
            "<table class='compact-table'><thead><tr><th>Floor</th><th>Room</th><th>Type</th>"
            f"<th>Area (m&#178;)</th></tr></thead><tbody>{rows}</tbody></table>"
        )

    cols_html = "".join(f"<div>{render_col(c)}</div>" for c in columns)
    totals = "".join(
        f"<tr><td>{escape_text(s['name'])}</td><td><b>{s['total_m2']:.1f} m&#178;</b></td></tr>"
        for s in schedule
    )
    return (
        '<section class="page"><h2>Room Schedule</h2>'
        f'<div class="two-col">{cols_html}</div>'
        '<h2>Floor Totals</h2>'
        f'<table class="compact-table"><tbody>{totals}</tbody></table></section>'
    )


def _plan_pages(model: CompiledModel, svg_dir: Path) -> str:
    pages = []
    for storey in model.storeys:
        svg_path = svg_dir / f"{model.name}_f{storey.level}.svg"
        body = _svg_inline(svg_path) if svg_path.exists() else "<p>(plan not generated)</p>"
        pages.append(f'<section class="page plan-page"><h2>{escape_text(storey.name)} &mdash; Floor Plan</h2>{body}</section>')
    return "".join(pages)


def _elevation_pages(model: CompiledModel, svg_dir: Path) -> str:
    pages = []
    for side in ("north", "south", "east", "west"):
        svg_path = svg_dir / f"{model.name}_elev_{side}.svg"
        body = _svg_inline(svg_path) if svg_path.exists() else "<p>(elevation not generated)</p>"
        pages.append(f'<section class="page plan-page"><h2>{side.title()} Elevation</h2>{body}</section>')
    return "".join(pages)


def _section_pages(model: CompiledModel, svg_dir: Path) -> str:
    cuts = model.sections or [
        {"name": "x", "axis": "x"},
        {"name": "y", "axis": "y"},
    ]
    pages = []
    for cut in cuts:
        label = "Long Section" if cut["axis"] == "x" else "Cross Section"
        svg_path = svg_dir / f"{model.name}_section_{cut['name']}.svg"
        body = _svg_inline(svg_path) if svg_path.exists() else "<p>(section not generated)</p>"
        pages.append(f'<section class="page plan-page"><h2>{escape_text(cut["name"])} &mdash; {label}</h2>{body}</section>')
    return "".join(pages)


def _gallery_pages(image_paths: list[Path], embed_images: bool, img_dir: Path,
                   current_hash: str | None = None) -> str:
    existing = [p for p in image_paths if p.exists()]
    pages = []
    for i in range(0, len(existing), 2):
        chunk = existing[i:i + 2]
        imgs = []
        for p in chunk:
            # TASK-06-03: a render is stale when its sidecar hash differs from
            # the model being briefed (or the sidecar is missing). The badge is
            # drawn on the image itself, so a mixed stale/fresh page still
            # shows it.
            stale = False
            if current_hash is not None:
                sidecar = read_render_sidecar(p)
                if sidecar is None or sidecar.get("model_hash") != current_hash:
                    print(f"warning: stale render {p.name} (sidecar hash {sidecar.get('model_hash') if sidecar else 'missing'} != model {current_hash})",
                          file=sys.stderr)
                    stale = True
            caption = '<figcaption class="stale">STALE</figcaption>' if stale else ""
            if embed_images:
                img = f'<img src="{_img_data_uri(p)}">'
            else:
                # Reference the downscaled copy by relative path so the HTML
                # stays small (ASM-007); cover hero stays a data URI.
                downscale_png(p, img_dir / p.name)
                img = f'<img src="../pdf/img/{p.name}">'
            imgs.append(f"<figure>{img}{caption}</figure>")
        pages.append(f'<section class="page"><h2>Renders</h2><div class="gallery">{"".join(imgs)}</div></section>')
    return "".join(pages)


def _opening_schedule_page(rows: list[dict]) -> str:
    def render_col(items):
        body = "".join(
            f"<tr><td>{r['id']}</td><td>{r['storey']}</td><td>{r['type']}</td>"
            f"<td>{r['width_mm']:.0f}</td><td>{r['sill_mm']:.0f}</td><td>{r['head_mm']:.0f}</td>"
            f"<td>{escape_text(r['rooms'][0])} / {escape_text(r['rooms'][1])}</td></tr>"
            for r in items
        )
        return (
            "<table class='compact-table'><thead><tr><th>ID</th><th>Floor</th><th>Type</th>"
            "<th>Width</th><th>Sill</th><th>Head</th><th>Between</th></tr></thead>"
            f"<tbody>{body}</tbody></table>"
        )

    columns = _split_rows(rows, 2)
    cols_html = "".join(f"<div>{render_col(c)}</div>" for c in columns)
    return (
        '<section class="page"><h2>Door &amp; Window Schedule</h2>'
        f'<div class="two-col">{cols_html}</div></section>'
    )


def _takeoff_page(rows: list[dict]) -> str:
    body = "".join(
        f"<tr><td>{escape_text(r['name'])}</td><td>{r['gfa_m2']:.1f}</td><td>{r['exterior_wall_m']:.1f}</td>"
        f"<td>{r['partition_wall_m']:.1f}</td><td>{r['door_count']}</td><td>{r['window_count']}</td></tr>"
        for r in rows
    )
    return (
        '<section class="page"><h2>Quantity Take-Off</h2>'
        "<table><thead><tr><th>Storey</th><th>GFA (m&#178;)</th><th>Ext. wall (m)</th>"
        "<th>Partition wall (m)</th><th>Doors</th><th>Windows</th></tr></thead>"
        f"<tbody>{body}</tbody></table></section>"
    )


def _requirements_page(brief: dict) -> str:
    items = "".join(f"<li>{escape_text(r)}</li>" for r in brief.get("requirements", []))
    return f'<section class="page"><h2>Requirements for the Architect</h2><ul class="requirements">{items}</ul></section>'


def _appendix_page(model: CompiledModel, spec_path: Path) -> str:
    items = [f"<li>{spec_path.name} (source spec, JSON)</li>"]
    for storey in model.storeys:
        items.append(f"<li>{model.name}_f{storey.level}.dxf ({escape_text(storey.name)}, CAD/DXF)</li>")
    return (
        '<section class="page"><h2>Handover Files</h2>'
        "<p>The following machine-readable files accompany this brief:</p>"
        f'<ul>{"".join(items)}</ul></section>'
    )


def render_brief_html(model: CompiledModel, brief: dict, out_dir: Path, spec_path: Path,
                       hero_view: str | None = None, embed_images: bool = False,
                       require_fresh: bool = False) -> str:
    svg_dir = out_dir / "svg"
    png_dir = out_dir / "png"
    img_dir = out_dir / "pdf" / "img"
    img_dir.mkdir(parents=True, exist_ok=True)

    schedule = build_room_schedule(model)
    openings = build_opening_schedule(model)
    takeoff = build_takeoff(model)
    view_names = [v.name for v in model.views] or ["exterior", "interior"]
    image_paths = [png_dir / f"{model.name}_{name}.png" for name in view_names]
    hero_name = hero_view or (view_names[0] if view_names else None)
    hero_path = png_dir / f"{model.name}_{hero_name}.png" if hero_name else None
    if hero_path is not None and not hero_path.exists():
        hero_path = None

    # TASK-06-03/04: gallery staleness is judged against the model being
    # briefed; `require_fresh` promotes a stale image to a hard error.
    current_hash = model_hash(model)
    if require_fresh:
        stale = []
        for p in image_paths:
            if not p.exists():
                continue
            sidecar = read_render_sidecar(p)
            if sidecar is None or sidecar.get("model_hash") != current_hash:
                stale.append(p.name)
        if stale:
            raise RuntimeError(
                f"stale render(s) for model {current_hash}: {', '.join(sorted(stale))}; "
                "re-render before building the brief"
            )

    # The cover hero is embedded as a data URI, so downscale it hard -- a
    # full-res 1920px render would otherwise add ~2.7MB of base64 to the
    # HTML, blowing the <200KB budget (ASM-007).
    hero_embedded = None
    if hero_path is not None:
        hero_embedded = downscale_png(hero_path, img_dir / f"hero_{hero_path.name}", max_width_px=640)

    body = "".join([
        _cover_page(brief, hero_embedded),
        _narrative_page(brief),
        _schedule_page(schedule),
        _plan_pages(model, svg_dir),
        _elevation_pages(model, svg_dir),
        _section_pages(model, svg_dir),
        _gallery_pages(image_paths, embed_images, img_dir, current_hash=current_hash),
        _requirements_page(brief),
        _opening_schedule_page(openings),
        _takeoff_page(takeoff),
        _appendix_page(model, spec_path),
    ])

    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<title>{escape_text(brief['title'])}</title><style>{PAGE_CSS}</style>"
        f"</head><body>{body}</body></html>"
    )


def _find_browser() -> str:
    env = os.environ.get("PDF_BROWSER_CMD")
    if env:
        return env
    for name in ("msedge", "msedge.exe", "chrome", "chrome.exe", "google-chrome"):
        found = shutil.which(name)
        if found:
            return found
    candidates = (
        glob.glob("C:/Program Files (x86)/Microsoft/EdgeCore/*/msedge.exe")
        + glob.glob("C:/Program Files (x86)/Microsoft/Edge/Application/msedge.exe")
        + glob.glob("C:/Program Files/Microsoft/Edge/Application/msedge.exe")
        + glob.glob("C:/Program Files (x86)/Google/Chrome/Application/chrome.exe")
    )
    if candidates:
        return sorted(candidates)[-1]
    raise FileNotFoundError(
        "No headless-capable browser found. Set PDF_BROWSER_CMD=/path/to/msedge.exe or chrome.exe."
    )


def print_html_to_pdf(html_path: Path, pdf_path: Path) -> None:
    # --print-to-pdf must be absolute: headless Chromium resolves it against
    # its own working directory, not the caller's, and silently logs
    # "cannot find the path specified" to stderr (exit code still 0) rather
    # than failing the process -- so a relative path here leaves a stale PDF
    # in place undetected by an exists()-only check.
    browser = _find_browser()
    pdf_path = pdf_path.resolve()
    before = pdf_path.stat().st_mtime if pdf_path.exists() else None
    cmd = [
        browser, "--headless", "--disable-gpu",
        f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri(),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    after = pdf_path.stat().st_mtime if pdf_path.exists() else None
    if result.returncode != 0 or after is None or after == before:
        raise RuntimeError(f"PDF print failed (exit {result.returncode}): {result.stderr}")


def build_brief(model: CompiledModel, brief: dict, out_dir: Path, spec_path: Path,
                 hero_view: str | None = None, embed_images: bool = False,
                 require_fresh: bool = False) -> Path:
    pdf_dir = out_dir / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    html = render_brief_html(model, brief, out_dir, spec_path, hero_view=hero_view,
                             embed_images=embed_images, require_fresh=require_fresh)
    html_path = pdf_dir / f"{model.name}-brief.html"
    html_path.write_text(html, encoding="utf-8")
    pdf_path = pdf_dir / f"{model.name}-brief.pdf"
    print_html_to_pdf(html_path, pdf_path)
    return pdf_path
