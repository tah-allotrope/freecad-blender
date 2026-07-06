import json
from pathlib import Path

from src.homedesign.compiler import compile_spec
from src.homedesign import pdf

REPO_ROOT = Path(__file__).resolve().parent.parent
EXAMPLES = REPO_ROOT / "spec" / "examples"


def load_example(name):
    return json.loads((EXAMPLES / name).read_text())


def _brief():
    return {
        "title": "Test House Brief",
        "subtitle": "A design-intent brief",
        "narrative": ["Paragraph one.", "Paragraph two."],
        "requirements": ["Requirement A", "Requirement B"],
    }


def test_room_schedule_lists_every_room_with_area_and_floor_totals():
    model = compile_spec(load_example("tubehouse-mini.json"))
    schedule = pdf.build_room_schedule(model)
    assert len(schedule) == len(model.storeys)
    ground = schedule[0]
    assert {r["id"] for r in ground["rooms"]} == {"living", "stairwell", "hall", "bedroom"}
    living = next(r for r in ground["rooms"] if r["id"] == "living")
    assert living["area_m2"] == 20.0  # 4m x 5m
    assert ground["total_m2"] == sum(r["area_m2"] for r in ground["rooms"])


def test_render_brief_html_includes_title_narrative_and_requirements():
    model = compile_spec(load_example("tubehouse-mini.json"))
    html = pdf.render_brief_html(model, _brief(), REPO_ROOT / "output", REPO_ROOT / "spec" / "examples" / "tubehouse-mini.json")
    assert "Test House Brief" in html
    assert "Paragraph one." in html
    assert "Requirement A" in html
    assert "@page { size: A3 landscape;" in html


def test_render_brief_html_includes_one_plan_page_per_storey():
    model = compile_spec(load_example("tubehouse-mini.json"))
    html = pdf.render_brief_html(model, _brief(), REPO_ROOT / "output", REPO_ROOT / "spec" / "examples" / "tubehouse-mini.json")
    for storey in model.storeys:
        assert storey.name in html


def test_render_brief_html_lists_handover_files():
    model = compile_spec(load_example("tubehouse-mini.json"))
    spec_path = REPO_ROOT / "spec" / "examples" / "tubehouse-mini.json"
    html = pdf.render_brief_html(model, _brief(), REPO_ROOT / "output", spec_path)
    assert spec_path.name in html
    assert "tubehouse-mini_f0.dxf" in html


def test_gallery_pages_batches_two_images_per_page(tmp_path):
    imgs = []
    for i in range(3):
        p = tmp_path / f"img{i}.png"
        p.write_bytes(b"\x89PNG\r\n\x1a\n" + b"0" * 20)
        imgs.append(p)
    html = pdf._gallery_pages(imgs, per_page=2)
    assert html.count('class="page"') == 2  # 3 images at 2/page -> 2 pages
