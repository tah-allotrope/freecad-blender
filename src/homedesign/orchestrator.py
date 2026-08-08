"""Locate Blender and drive the headless build+render subprocess legs.

This module runs in system Python. It never imports bpy -- all Blender-side
work happens inside `blender/build_scene.py`, executed via subprocess.
"""
from __future__ import annotations

import os
import shutil
import subprocess
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parent.parent.parent

_CANDIDATES = [
    # Blender 4.1 (legacy EEVEE) is preferred over 4.2+ (EEVEE Next).
    #
    # EEVEE Next is a much heavier consumer of the OpenGL driver than legacy
    # EEVEE, and it miscompiles on the Gen9.5 Intel iGPU this tool targets
    # (UHD 620, driver 23.20.16.4849): every lit surface renders blood red.
    # A white 0.92/0.91/0.88 wall comes out (194, 34, 53) -- independent of
    # view transform and of `raytracing` -- while the world background is
    # unaffected, so the corruption is in surface shading, not colour
    # management. Vulkan is not an escape: Blender rejects the device for
    # missing timeline semaphores, buffer device address and
    # VK_EXT_provoking_vertex.
    #
    # Legacy EEVEE renders the same scene correctly (190, 194, 197, matching
    # Cycles' 190, 193, 197) at 29.7s/view vs 169.3s/view for Cycles CPU,
    # which is the only other correct path here (no OPTIX/CUDA/HIP/oneAPI
    # device exists on this machine). `build_scene._set_engine` already falls
    # back to BLENDER_EEVEE, and the `final` profile's `raytracing: True`
    # degrades to a no-op under 4.1.
    #
    # Set BLENDER_CMD to override on a machine with a GPU that EEVEE Next
    # handles correctly.
    "C:/Users/tukum/Blender/blender-4.1.1-windows-x64/blender.exe",
    "C:/Program Files/Blender Foundation/Blender 4.1/blender.exe",
    "C:/Users/tukum/Blender/blender-4.5.1-windows-x64/blender.exe",
    "C:/Program Files/Blender Foundation/Blender 4.2/blender.exe",
    "C:/Program Files/Blender Foundation/Blender 4.0/blender.exe",
    "C:/Program Files/Blender Foundation/Blender 3.6/blender.exe",
    # macOS
    "/Applications/Blender.app/Contents/MacOS/Blender",
    # Linux
    "/usr/bin/blender",
    "/usr/local/bin/blender",
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


def _build_command(model_path: Path, out_dir: Path, profile: str,
                   views: list[str] | None = None, skip_existing: bool = False,
                   reuse_blend: bool = False, gltf: bool = False) -> list[str]:
    blender = find_blender()
    builder_script = Path(__file__).resolve().parent / "blender" / "build_scene.py"
    cmd = [
        blender, "--background", "--python", str(builder_script), "--",
        "--model", str(model_path), "--out", str(out_dir), "--profile", profile,
    ]
    if views:
        cmd += ["--views", ",".join(views)]
    if skip_existing:
        cmd += ["--skip-existing"]
    if reuse_blend:
        cmd += ["--reuse-blend"]
    if gltf:
        cmd += ["--export-gltf"]
    return cmd


def build_scene(model_path: Path, out_dir: Path, final: bool = False,
                profile: str | None = None,
                views: list[str] | None = None, skip_existing: bool = False,
                reuse_blend: bool = False, gltf: bool = False) -> list[Path]:
    # `profile` ("preview"|"final"|"cycles") overrides the legacy `final` flag.
    profile = profile or ("final" if final else "preview")

    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "blend").mkdir(parents=True, exist_ok=True)
    (out_dir / "png").mkdir(parents=True, exist_ok=True)

    cmd = _build_command(model_path, out_dir, profile, views, skip_existing, reuse_blend, gltf)
    proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                            text=True, cwd=REPO_ROOT, encoding="utf-8", errors="replace")
    streamed: list[str] = []
    assert proc.stdout is not None
    for line in proc.stdout:
        streamed.append(line.rstrip())
        sys.stderr.write(line)
    proc.wait()
    if proc.returncode != 0:
        tail = streamed[-50:]
        raise RuntimeError(
            f"Blender build failed (exit {proc.returncode}). Last output:\n"
            + "\n".join(tail)
        )

    name = model_path.stem.replace(".model", "")
    blend_path = out_dir / "blend" / f"{name}.blend"
    png_paths = sorted((out_dir / "png").glob(f"{name}_*.png"))
    return [blend_path] + png_paths


def render_only(model_path: Path, out_dir: Path, profile: str = "preview",
                views: list[str] | None = None, skip_existing: bool = False,
                detach: bool = False, log_path: Path | None = None) -> list[Path] | int:
    """Render views of an already-built model.

    Synchronous mode returns the rendered PNG paths. With `detach=True`,
    launches Blender as a detached process (survives the launching shell),
    redirects output to `log_path`, and returns the PID immediately.
    """
    out_dir.mkdir(parents=True, exist_ok=True)
    (out_dir / "png").mkdir(parents=True, exist_ok=True)

    cmd = _build_command(model_path, out_dir, profile, views, skip_existing, reuse_blend=True)

    if not detach:
        proc = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
                                text=True, cwd=REPO_ROOT, encoding="utf-8", errors="replace")
        streamed: list[str] = []
        assert proc.stdout is not None
        for line in proc.stdout:
            streamed.append(line.rstrip())
            sys.stderr.write(line)
        proc.wait()
        if proc.returncode != 0:
            tail = streamed[-50:]
            raise RuntimeError(
                f"Blender render failed (exit {proc.returncode}). Last output:\n"
                + "\n".join(tail)
            )
        name = model_path.stem.replace(".model", "")
        if views:
            return [out_dir / "png" / f"{name}_{v}.png" for v in views]
        return sorted((out_dir / "png").glob(f"{name}_*.png"))

    # Detached launch: survive a closed terminal.
    log_path = log_path or (out_dir / "logs" / f"render-{int(time.time())}.log")
    log_path.parent.mkdir(parents=True, exist_ok=True)
    logf = open(log_path, "w", encoding="utf-8")
    if os.name == "nt":
        proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT,
                                cwd=REPO_ROOT,
                                creationflags=subprocess.DETACHED_PROCESS
                                | subprocess.CREATE_NEW_PROCESS_GROUP)
    else:
        proc = subprocess.Popen(cmd, stdout=logf, stderr=subprocess.STDOUT,
                                cwd=REPO_ROOT, start_new_session=True)
    print(f"detached render pid: {proc.pid}")
    print(f"log: {log_path}")
    if os.name == "nt":
        print(f"kill: taskkill /PID {proc.pid} /F")
    else:
        print(f"kill: kill {proc.pid}")
    return proc.pid
