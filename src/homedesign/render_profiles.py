"""Render engine profiles (pure data -- no `bpy` import, unit-testable).

`final` promotes EEVEE Next (ray-traced) as the full-quality path on the CPU
only hardware this tool targets (CON-001); Cycles remains the explicit
`cycles` opt-in for hero shots.
"""
from __future__ import annotations

RENDER_PROFILES = {
    "preview": {"engine": "EEVEE", "samples": 32, "res": (960, 540), "raytracing": False},
    "final": {"engine": "EEVEE", "samples": 256, "res": (1920, 1080), "raytracing": True},
    "cycles": {"engine": "CYCLES", "samples": 512, "res": (1920, 1080), "raytracing": False},
}
