import json
from pathlib import Path

import pytest

from homedesign.compiler import compile_spec
from homedesign import pdf

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
    html = pdf._gallery_pages(imgs, embed_images=True, img_dir=tmp_path)
    assert html.count('class="page"') == 2  # 3 images at 2/page -> 2 pages


def test_opening_schedule_covers_all_openings():
    model = compile_spec(load_example("tubehouse-mini.json"))
    rows = pdf.build_opening_schedule(model)
    total_openings = sum(len(s.openings) for s in model.storeys)
    assert len(rows) == total_openings
    assert all(len(r["rooms"]) == 2 for r in rows)


def test_takeoff_totals_row_matches_sum():
    model = compile_spec(load_example("tubehouse-mini.json"))
    rows = pdf.build_takeoff(model)
    assert rows[-1]["level"] is None
    per_storey = sum(r["gfa_m2"] for r in rows[:-1])
    assert abs(rows[-1]["gfa_m2"] - per_storey) < 0.1


def test_render_brief_html_uses_relative_images_not_data_uris(tmp_path):
    model = compile_spec(load_example("tubehouse-mini.json"))
    out = REPO_ROOT / "output"
    hero = out / "png" / "tubehouse-mini_exterior.png"
    if not hero.exists():
        pytest.skip("no renders present")
    html = pdf.render_brief_html(model, _brief(), out, EXAMPLES / "tubehouse-mini.json")
    # Gallery images referenced by relative path; the single cover-hero data
    # URI is the only base64 occurrence allowed.
    assert html.count("data:image/png;base64") == 1
    assert 'src="../pdf/img/' in html


def test_render_brief_html_embed_images_embeds_all(tmp_path):
    model = compile_spec(load_example("tubehouse-mini.json"))
    out = REPO_ROOT / "output"
    hero = out / "png" / "tubehouse-mini_exterior.png"
    if not hero.exists():
        pytest.skip("no renders present")
    html = pdf.render_brief_html(model, _brief(), out, EXAMPLES / "tubehouse-mini.json",
                                 embed_images=True)
    n_views = len(model.views) or 2
    assert html.count("data:image/png;base64") == n_views + 1  # gallery + hero
