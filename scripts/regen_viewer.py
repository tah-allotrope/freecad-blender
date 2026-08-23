"""Regenerate output/viewer/*.html from existing artifacts (no Blender run).

Usage: python scripts/regen_viewer.py [model_name] [--out output]
Falls back to the flagship contractor-as-drawn when no name is given.
"""
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))

from homedesign.viewer import write_viewer, write_floor_viewer


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
    print("wrote", write_viewer(name, glb, out))
    floor_page = write_floor_viewer(name, glb, storeys, out / "svg", out)
    print("wrote", floor_page)


if __name__ == "__main__":
    main()
