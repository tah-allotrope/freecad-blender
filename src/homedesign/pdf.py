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
from pathlib import Path

from .model import CompiledModel

PAGE_CSS = """
@page { size: A3 landscape; margin: 14mm; }
* { box-sizing: border-box; }
body { font-family: "Segoe UI", Arial, sans-serif; color: #1a1a1a; margin: 0; }
.page { page-break-after: always; padding: 10mm; min-height: calc(297mm - 28mm); }
.page:last-child { page-break-after: auto; }
h1 { font-size: 32pt; margin: 0 0 4mm; }
h2 { font-size: 20pt; border-bottom: 2px solid #222; padding-bottom: 2mm; }
.cover { display: flex; flex-direction: column; justify-content: flex-end;
         height: calc(297mm - 28mm); background-size: cover; background-position: center;
         color: white; text-shadow: 0 1px 6px rgba(0,0,0,.7); }
.cover h1 { font-size: 44pt; }
table { border-collapse: collapse; width: 100%; font-size: 11pt; }
th, td { border: 1px solid #ccc; padding: 2mm 3mm; text-align: left; }
th { background: #f0f0f0; }
.plan-page svg { max-width: 100%; max-height: 230mm; }
.gallery { display: grid; grid-template-columns: 1fr 1fr; gap: 6mm; }
.gallery img { width: 100%; height: auto; border: 1px solid #ddd; }
ul.requirements li { margin-bottom: 2mm; }
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


def _svg_inline(path: Path) -> str:
    text = path.read_text()
    if text.startswith("<?xml"):
        text = text.split("?>", 1)[1]
    return text


def _cover_page(brief: dict, hero_path: Path | None) -> str:
    style = f"background-image:url('{_img_data_uri(hero_path)}')" if hero_path else ""
    return (
        f'<section class="page cover" style="{style}">'
        f"<h1>{brief['title']}</h1><p>{brief.get('subtitle', '')}</p>"
        f"</section>"
    )


def _narrative_page(brief: dict) -> str:
    paragraphs = "".join(f"<p>{p}</p>" for p in brief.get("narrative", []))
    return f'<section class="page"><h2>Design Intent</h2>{paragraphs}</section>'


def _schedule_page(schedule: list[dict]) -> str:
    rows = "".join(
        f"<tr><td>{s['name']}</td><td>{r['id']}</td><td>{r['type']}</td><td>{r['area_m2']:.1f}</td></tr>"
        for s in schedule for r in s["rooms"]
    )
    totals = "".join(
        f"<tr><td colspan='3'><b>{s['name']} total</b></td><td><b>{s['total_m2']:.1f}</b></td></tr>"
        for s in schedule
    )
    return (
        '<section class="page"><h2>Room Schedule</h2>'
        "<table><thead><tr><th>Floor</th><th>Room</th><th>Type</th>"
        f"<th>Area (m&#178;)</th></tr></thead><tbody>{rows}</tbody></table>"
        f'<h2>Floor Totals</h2><table><tbody>{totals}</tbody></table></section>'
    )


def _plan_pages(model: CompiledModel, svg_dir: Path) -> str:
    pages = []
    for storey in model.storeys:
        svg_path = svg_dir / f"{model.name}_f{storey.level}.svg"
        body = _svg_inline(svg_path) if svg_path.exists() else "<p>(plan not generated)</p>"
        pages.append(f'<section class="page plan-page"><h2>{storey.name} &mdash; Floor Plan</h2>{body}</section>')
    return "".join(pages)


def _gallery_pages(image_paths: list[Path], per_page: int = 2) -> str:
    existing = [p for p in image_paths if p.exists()]
    pages = []
    for i in range(0, len(existing), per_page):
        chunk = existing[i:i + per_page]
        imgs = "".join(f'<img src="{_img_data_uri(p)}">' for p in chunk)
        pages.append(f'<section class="page"><h2>Renders</h2><div class="gallery">{imgs}</div></section>')
    return "".join(pages)


def _requirements_page(brief: dict) -> str:
    items = "".join(f"<li>{r}</li>" for r in brief.get("requirements", []))
    return f'<section class="page"><h2>Requirements for the Architect</h2><ul class="requirements">{items}</ul></section>'


def _appendix_page(model: CompiledModel, spec_path: Path) -> str:
    items = [f"<li>{spec_path.name} (source spec, JSON)</li>"]
    for storey in model.storeys:
        items.append(f"<li>{model.name}_f{storey.level}.dxf ({storey.name}, CAD/DXF)</li>")
    return (
        '<section class="page"><h2>Handover Files</h2>'
        "<p>The following machine-readable files accompany this brief:</p>"
        f'<ul>{"".join(items)}</ul></section>'
    )


def render_brief_html(model: CompiledModel, brief: dict, out_dir: Path, spec_path: Path,
                       hero_view: str | None = None) -> str:
    svg_dir = out_dir / "svg"
    png_dir = out_dir / "png"

    schedule = build_room_schedule(model)
    view_names = [v.name for v in model.views] or ["exterior", "interior"]
    image_paths = [png_dir / f"{model.name}_{name}.png" for name in view_names]
    hero_name = hero_view or (view_names[0] if view_names else None)
    hero_path = png_dir / f"{model.name}_{hero_name}.png" if hero_name else None
    if hero_path is not None and not hero_path.exists():
        hero_path = None

    body = "".join([
        _cover_page(brief, hero_path),
        _narrative_page(brief),
        _schedule_page(schedule),
        _plan_pages(model, svg_dir),
        _gallery_pages(image_paths),
        _requirements_page(brief),
        _appendix_page(model, spec_path),
    ])

    return (
        "<!doctype html><html><head><meta charset=\"utf-8\">"
        f"<title>{brief['title']}</title><style>{PAGE_CSS}</style>"
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
    browser = _find_browser()
    cmd = [
        browser, "--headless", "--disable-gpu",
        f"--print-to-pdf={pdf_path}", html_path.resolve().as_uri(),
    ]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0 or not pdf_path.exists():
        raise RuntimeError(f"PDF print failed (exit {result.returncode}): {result.stderr}")


def build_brief(model: CompiledModel, brief: dict, out_dir: Path, spec_path: Path,
                 hero_view: str | None = None) -> Path:
    pdf_dir = out_dir / "pdf"
    pdf_dir.mkdir(parents=True, exist_ok=True)
    html = render_brief_html(model, brief, out_dir, spec_path, hero_view=hero_view)
    html_path = pdf_dir / f"{model.name}-brief.html"
    html_path.write_text(html, encoding="utf-8")
    pdf_path = pdf_dir / f"{model.name}-brief.pdf"
    print_html_to_pdf(html_path, pdf_path)
    return pdf_path
