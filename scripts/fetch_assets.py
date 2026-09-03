#!/usr/bin/env python3
"""Populate `assets/cache/` with CC0 textures, HDRIs and furniture meshes.

Run once (PR TASK-02-01 / 02-02 / 03-01). Everything is fetched from Poly Haven,
whose entire library is CC0, and written under `assets/cache/` in the layout
`homedesign.asset_cache` resolves. The renderer never reaches the network
itself (ASM-005) — this script is the only downloader, and a missing entry is a
hard error at render time, not a silent fetch.

    python scripts/fetch_assets.py            # fill in whatever is missing
    python scripts/fetch_assets.py --force    # re-download everything
    python scripts/fetch_assets.py --attribution-only

Furniture arrives as multi-file glTF and is welded into a single `.glb` with
`@gltf-transform/cli` via `npx`, because `asset_library` imports one file per
kind. A kind with no suitable CC0 mesh is left out on purpose; `build_item`
falls back to its procedural builder for those.
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import shutil
import subprocess
import sys
import tempfile
import urllib.request
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent
CACHE = REPO_ROOT / "assets" / "cache"
API = "https://api.polyhaven.com"
UA = {"User-Agent": "homedesign-asset-cache/1.0 (+https://github.com/tah-allotrope/freecad-blender)"}
LICENCE = "CC0 1.0 Universal (Public Domain Dedication)"

# --- what we fetch --------------------------------------------------------

# One Poly Haven texture per finish family. `glass_clear` is deliberately
# absent: Poly Haven has no clear-glazing PBR set, and a dirt/smudge map would
# read as filthy windows on the hero stills. `asset_cache.texture_set` returns
# None for it, so `make_procedural_material` keeps its procedural glass graph.
TEXTURES = {
    "plaster_painted": "painted_plaster_wall",
    "ceramic_tile": "floor_tiles_06",
    "stone_slab": "marble_01",
    "wood_board": "wood_floor_deck",
    "metal_brushed": "metal_plate",
    "concrete_formed": "concrete_wall_008",
}
# Poly Haven map name -> the filename `asset_cache` looks for.
TEXTURE_MAPS = {"Diffuse": "diffuse", "Rough": "rough", "nor_gl": "normal", "AO": "ao"}
TEXTURE_RES = "2k"

HDRIS = {
    # Must be a "puresky" asset: those are sky-only, with no ground plane or
    # scenery baked in. A full-environment HDRI puts its own location behind
    # the building — `hausdorf_clear_sky` rendered a Czech meadow and alpine
    # cottages behind a Saigon tube house. Noon and clear also matches the
    # project's fixed 55 degree sun (DEC-004).
    # The exterior sky is visible behind the building on the hero stills, so it
    # gets the higher resolution; the interior probe only lights and reflects.
    "exterior": ("qwantani_noon_puresky", "2k"),
    "interior": ("brown_photostudio_02", "1k"),
}

# Furniture kind (from procedural_furniture._BUILDERS) -> Poly Haven model.
# `kitchen_run` and `wc` have no CC0 equivalent in the library; they stay
# procedural rather than being faked with a stretched cabinet or crate.
FURNITURE = {
    "bed": "old_bed_frame",
    "sofa": "sofa_03",
    "table": "dining_table",
    "chair": "dining_chair_02",
    "shelving": "wooden_bookshelf_worn",
    "console": "chinese_console_table",
    "desk": "metal_office_desk",
    "wardrobe": "vintage_cabinet_01",
    "car": "covered_car",
    "planter": "planter_box_01",
}
FURNITURE_RES = "1k"

PROCEDURAL_ONLY = {
    "glass_clear": "no CC0 clear-glazing PBR set exists; procedural glass graph retained",
    "kitchen_run": "no CC0 kitchen run in the library; procedural builder retained",
    "wc": "no CC0 sanitaryware in the library; procedural builder retained",
}


# --- plumbing -------------------------------------------------------------

def api(path: str):
    req = urllib.request.Request(f"{API}{path}", headers=UA)
    with urllib.request.urlopen(req, timeout=60) as r:
        return json.load(r)


def download(url: str, dest: Path) -> int:
    dest.parent.mkdir(parents=True, exist_ok=True)
    req = urllib.request.Request(url, headers=UA)
    with urllib.request.urlopen(req, timeout=300) as r, open(dest, "wb") as fh:
        shutil.copyfileobj(r, fh)
    return dest.stat().st_size


def sha256(path: Path) -> str:
    h = hashlib.sha256()
    with open(path, "rb") as fh:
        for chunk in iter(lambda: fh.read(1 << 20), b""):
            h.update(chunk)
    return h.hexdigest()


def asset_page(slug: str) -> str:
    return f"https://polyhaven.com/a/{slug}"


# --- fetchers -------------------------------------------------------------

def fetch_textures(force: bool, records: list[dict]) -> None:
    for family, slug in TEXTURES.items():
        files = api(f"/files/{slug}")
        for ph_name, local_name in TEXTURE_MAPS.items():
            entry = files.get(ph_name, {}).get(TEXTURE_RES, {}).get("jpg")
            if not entry:
                print(f"  {family}: no {ph_name} at {TEXTURE_RES}, skipped")
                continue
            dest = CACHE / "textures" / family / f"{local_name}.jpg"
            if dest.exists() and not force:
                print(f"  {family}/{local_name}.jpg exists")
            else:
                size = download(entry["url"], dest)
                print(f"  {family}/{local_name}.jpg  {size/1e6:.1f} MB")
            records.append({
                "path": dest.relative_to(REPO_ROOT).as_posix(),
                "name": f"{slug} ({ph_name}, {TEXTURE_RES})",
                "source": entry["url"],
                "page": asset_page(slug),
                "sha256": sha256(dest),
                "bytes": dest.stat().st_size,
            })


def fetch_hdris(force: bool, records: list[dict]) -> None:
    for local_name, (slug, res) in HDRIS.items():
        files = api(f"/files/{slug}")
        entry = files["hdri"][res]["hdr"]
        dest = CACHE / "hdri" / f"{local_name}.hdr"
        if dest.exists() and not force:
            print(f"  hdri/{local_name}.hdr exists")
        else:
            size = download(entry["url"], dest)
            print(f"  hdri/{local_name}.hdr  {size/1e6:.1f} MB")
        records.append({
            "path": dest.relative_to(REPO_ROOT).as_posix(),
            "name": f"{slug} ({res} HDRI)",
            "source": entry["url"],
            "page": asset_page(slug),
            "sha256": sha256(dest),
            "bytes": dest.stat().st_size,
        })
        preview = _write_hdri_preview(dest)
        if preview is not None:
            records.append({
                "path": preview.relative_to(REPO_ROOT).as_posix(),
                "name": f"{slug} (tone-mapped 512px preview, derived)",
                "source": entry["url"],
                "page": asset_page(slug),
                "sha256": sha256(preview),
                "bytes": preview.stat().st_size,
            })


def _write_hdri_preview(hdr: Path) -> Path | None:
    """Bake the small LDR equirect JPEG the web viewer inlines.

    Done here, in the system Python, because the viewer is written from inside
    Blender and Blender's bundled Python has neither numpy nor Pillow.
    """
    try:
        sys.path.insert(0, str(REPO_ROOT / "src"))
        from homedesign.hdri import equirect_preview_jpeg

        out = hdr.with_name(f"{hdr.stem}_preview.jpg")
        out.write_bytes(equirect_preview_jpeg(hdr, width=512))
        print(f"  hdri/{out.name}  {out.stat().st_size/1e3:.0f} kB")
        return out
    except Exception as exc:
        print(f"  hdri preview for {hdr.name}: skipped ({exc})")
        return None


def _gltf_to_glb(gltf_path: Path, out: Path) -> None:
    """Weld a multi-file glTF into one self-contained .glb."""
    cmd = ["npx", "--yes", "@gltf-transform/cli", "copy", str(gltf_path), str(out)]
    subprocess.run(cmd, check=True, capture_output=True, timeout=600,
                   shell=(os.name == "nt"))


def fetch_furniture(force: bool, records: list[dict]) -> None:
    for kind, slug in FURNITURE.items():
        dest = CACHE / "furniture" / f"{kind}.glb"
        if dest.exists() and not force:
            print(f"  furniture/{kind}.glb exists")
        else:
            files = api(f"/files/{slug}")
            entry = files["gltf"][FURNITURE_RES]["gltf"]
            with tempfile.TemporaryDirectory() as td:
                tmp = Path(td)
                gltf_name = entry["url"].rsplit("/", 1)[1]
                download(entry["url"], tmp / gltf_name)
                # `include` maps the glTF's own relative URI to the absolute
                # URL it lives at — the .bin sits under a different resolution
                # directory, so the relative path cannot be joined to the glTF.
                for rel, meta in entry.get("include", {}).items():
                    download(meta["url"], tmp / rel)
                dest.parent.mkdir(parents=True, exist_ok=True)
                _gltf_to_glb(tmp / gltf_name, dest)
            print(f"  furniture/{kind}.glb  {dest.stat().st_size/1e6:.1f} MB  ({slug})")
        records.append({
            "path": dest.relative_to(REPO_ROOT).as_posix(),
            "name": f"{slug} ({FURNITURE_RES} glTF, welded to GLB)",
            "source": f"https://dl.polyhaven.org/file/ph-assets/Models/gltf/{FURNITURE_RES}/{slug}/",
            "page": asset_page(slug),
            "sha256": sha256(dest),
            "bytes": dest.stat().st_size,
        })


# --- attribution ----------------------------------------------------------

def write_attribution(records: list[dict]) -> None:
    total = sum(r["bytes"] for r in records)
    lines = [
        "# Asset Attribution",
        "",
        "Every file under `assets/cache/` is CC0 and comes from Poly Haven",
        "(<https://polyhaven.com>), whose entire library is released into the public",
        "domain. Re-fetch or verify with `python scripts/fetch_assets.py`.",
        "",
        f"Licence for all entries: **{LICENCE}**.",
        "",
        f"{len(records)} files, {total/1e6:.1f} MB total.",
        "",
        "| File | Asset | Poly Haven page | Bytes | SHA-256 |",
        "|---|---|---|---:|---|",
    ]
    for r in sorted(records, key=lambda r: r["path"]):
        lines.append(
            f"| `{r['path']}` | {r['name']} | <{r['page']}> | {r['bytes']} | `{r['sha256']}` |"
        )
    lines += [
        "",
        "## Deliberately not cached",
        "",
        "These resolve to `None` in `homedesign.asset_cache` and fall back to the",
        "procedural graph or builder, which is the designed path — not a gap:",
        "",
    ]
    for name, why in PROCEDURAL_ONLY.items():
        lines.append(f"- `{name}` — {why}")
    lines.append("")
    (CACHE / "ATTRIBUTION.md").write_text("\n".join(lines), encoding="utf-8")
    print(f"wrote ATTRIBUTION.md ({len(records)} files, {total/1e6:.1f} MB)")


def collect_existing() -> list[dict]:
    """Attribution records for whatever is already on disk."""
    records: list[dict] = []
    for family, slug in TEXTURES.items():
        for ph_name, local_name in TEXTURE_MAPS.items():
            dest = CACHE / "textures" / family / f"{local_name}.jpg"
            if dest.exists():
                records.append({
                    "path": dest.relative_to(REPO_ROOT).as_posix(),
                    "name": f"{slug} ({ph_name}, {TEXTURE_RES})",
                    "source": "", "page": asset_page(slug),
                    "sha256": sha256(dest), "bytes": dest.stat().st_size,
                })
    for local_name, (slug, res) in HDRIS.items():
        dest = CACHE / "hdri" / f"{local_name}.hdr"
        if dest.exists():
            records.append({
                "path": dest.relative_to(REPO_ROOT).as_posix(),
                "name": f"{slug} ({res} HDRI)", "source": "", "page": asset_page(slug),
                "sha256": sha256(dest), "bytes": dest.stat().st_size,
            })
        preview = CACHE / "hdri" / f"{local_name}_preview.jpg"
        if preview.exists():
            records.append({
                "path": preview.relative_to(REPO_ROOT).as_posix(),
                "name": f"{slug} (tone-mapped 512px preview, derived)",
                "source": "", "page": asset_page(slug),
                "sha256": sha256(preview), "bytes": preview.stat().st_size,
            })
    for kind, slug in FURNITURE.items():
        dest = CACHE / "furniture" / f"{kind}.glb"
        if dest.exists():
            records.append({
                "path": dest.relative_to(REPO_ROOT).as_posix(),
                "name": f"{slug} ({FURNITURE_RES} glTF, welded to GLB)",
                "source": "", "page": asset_page(slug),
                "sha256": sha256(dest), "bytes": dest.stat().st_size,
            })
    return records


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--force", action="store_true", help="re-download files that already exist")
    ap.add_argument("--attribution-only", action="store_true",
                    help="rewrite ATTRIBUTION.md from what is already on disk")
    ap.add_argument("--only", choices=["textures", "hdris", "furniture"],
                    help="fetch just one group")
    args = ap.parse_args(argv)

    CACHE.mkdir(parents=True, exist_ok=True)
    if args.attribution_only:
        write_attribution(collect_existing())
        return 0

    records: list[dict] = []
    if args.only in (None, "textures"):
        print("textures:")
        fetch_textures(args.force, records)
    if args.only in (None, "hdris"):
        print("hdris:")
        fetch_hdris(args.force, records)
    if args.only in (None, "furniture"):
        print("furniture:")
        fetch_furniture(args.force, records)

    if args.only:
        records = collect_existing()
    write_attribution(records)
    return 0


if __name__ == "__main__":
    sys.exit(main())
