"""Regenerate output/viewer/*.html from existing artifacts (no Blender run).

Usage: python scripts/regen_viewer.py [model_name] [--out output] [--light]
Falls back to the flagship contractor-as-drawn when no name is given.

Writes the full (external-GLB) viewer, the per-floor viewer, and with --light
also derives the phone build's GLB and its single-file viewer.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from homedesign.viewer import (  # noqa: E402
    derive_light_glb,
    write_floor_viewer,
    write_viewer,
)


def room_labels(model: dict) -> list[dict]:
    """Room name sprites in metres, at head height (RF TASK-05-06)."""
    out = []
    for storey in model["storeys"]:
        base_z = storey["base_z"] / 1000
        head = min(1.6, storey["height_mm"] / 1000 * 0.5)
        for room in storey["rooms"]:
            name = room.get("name") or room.get("id")
            if not name:
                continue
            r = room["rect"]
            out.append({
                "text": str(name),
                "x": (r["x"] + r["w"] / 2) / 1000,
                "y": (r["y"] + r["d"] / 2) / 1000,
                "z": base_z + head,
                "storey": storey["name"],
            })
    return out


def level_tags(model: dict) -> list[dict]:
    return [
        {
            "text": f"{s['name']} {s['base_z'] / 1000:+.3f}",
            "x": 0.0, "y": 0.0, "z": s["base_z"] / 1000, "storey": s["name"],
        }
        for s in model["storeys"]
    ]


def main() -> None:
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    out = ROOT / "output"
    if "--out" in sys.argv:
        out = Path(sys.argv[sys.argv.index("--out") + 1])
    name = args[0] if args else "contractor-as-drawn"
    glb = out / "gltf" / f"{name}.glb"
    if not glb.exists():
        raise SystemExit(f"no GLB at {glb} — run 'homedesign build {name}.json --gltf' first")
    model = json.loads((out / "compiled" / f"{name}.model.json").read_text(encoding="utf-8"))
    storeys = [
        {"name": s["name"], "base_z": s["base_z"], "height_mm": s["height_mm"]}
        for s in model["storeys"]
    ]
    print("storeys:", [(s["name"], s["base_z"]) for s in storeys])

    rooms, levels = room_labels(model), level_tags(model)
    written = write_viewer(name, glb, out, rooms=rooms, levels=levels)
    print("wrote", written.html, "+", written.glb)

    floor_page = write_floor_viewer(name, glb, storeys, out / "svg", out)
    print("wrote", floor_page)

    if "--light" in sys.argv:
        light_glb = glb.with_name(f"{name}-light.glb")
        derive_light_glb(glb, light_glb)
        light = write_viewer(name, light_glb, out, build="light", rooms=rooms, levels=levels)
        print("wrote", light.html, f"({light_glb.stat().st_size} bytes)")


if __name__ == "__main__":
    main()
