"""Locate Blender and drive the headless build+render subprocess legs.

This module runs in system Python. It never imports bpy -- all Blender-side
work happens inside `blender/build_scene.py`, executed via subprocess.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_CANDIDATES = [
    "C:/Users/tukum/Blender/blender-4.1.1-windows-x64/blender.exe",
    "C:/Program Files/Blender Foundation/Blender 4.1/blender.exe",
    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe",
    "C:/Program Files/Blender Foundation/Blender 3.6/blender.exe",
]


def find_blender() -> str:
    env = os.environ.get("BLENDER_CMD")
    if env:
        return env
    on_path = shutil.which("blender") or shutil.which("blender.exe")
    if on_path:
        return on_path
    for candidate in _CANDIDATES:
        if Path(candidate).exists():
            return candidate
    raise FileNotFoundError(
        "Blender not found. Set BLENDER_CMD=/path/to/blender.exe or install it on PATH."
    )


def build_scene(model_path: Path, out_dir: Path, final: bool = False) -> list[Path]:
    blender = find_blender()
    builder_script = Path(__file__).resolve().parent / "blender" / "build_scene.py"
    profile = "final" if final else "preview"

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "blend").mkdir(parents=True, exist_ok=True)
    (out_dir / "png").mkdir(parents=True, exist_ok=True)

    cmd = [
        blender, "--background", "--python", str(builder_script), "--",
        "--model", str(model_path), "--out", str(out_dir), "--profile", profile,
    ]
    result = subprocess.run(cmd, capture_output=True, text=True, cwd=REPO_ROOT)
    sys.stderr.write(result.stderr)
    if result.returncode != 0:
        raise RuntimeError(f"Blender build failed (exit {result.returncode}):\n{result.stdout}\n{result.stderr}")

    name = model_path.stem.replace(".model", "")
    blend_path = out_dir / "blend" / f"{name}.blend"
    png_paths = sorted((out_dir / "png").glob(f"{name}_*.png"))
    return [blend_path] + png_paths
