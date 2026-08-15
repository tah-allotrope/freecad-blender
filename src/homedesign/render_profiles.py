"""Render engine profiles (pure data -- no `bpy` import, unit-testable).

`final` is a 256-sample legacy-EEVEE render at 1920x1080; its `raytracing: True`
flag degrades to a harmless no-op under Blender 4.1's legacy EEVEE (which has no
such toggle). `cycles` remains an explicit CPU-only opt-in for hero shots
(CON-001).
"""
from __future__ import annotations

RENDER_PROFILES = {
    "preview": {"engine": "EEVEE", "samples": 32, "res": (960, 540), "raytracing": False},
    "final": {"engine": "EEVEE", "samples": 256, "res": (1920, 1080), "raytracing": True},
    "cycles": {"engine": "CYCLES", "samples": 512, "res": (1920, 1080), "raytracing": False},
}
