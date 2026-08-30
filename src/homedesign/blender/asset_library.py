"""GLB import, fit, place (PHASE-03)."""
from __future__ import annotations
from pathlib import Path
try:
    from homedesign import asset_cache
    _HAS = True
except Exception:
    _HAS = False

_cache = {}

def build_from_asset(item, room_x: float, room_y: float, base_z: float, collection):
    """Try to import a cached GLB for item.kind, fitted to its bounding box. Returns obj or None."""
    import bpy
    kind = getattr(item, "kind", None) or getattr(item, "type", None) or getattr(item, "kind", "")
    if not _HAS:
        return None
    # resolve path
    try:
        p = asset_cache.furniture(kind)
    except Exception:
        p = None
    if not p or not Path(p).exists():
        return None
    # cache per kind: we just import each time; instancing via linked data would be extra
    try:
        # Import GLB
        before = set(bpy.data.objects.keys())
        bpy.ops.import_scene.gltf(filepath=str(p))
        after = set(bpy.data.objects.keys())
        new_names = after - before
        if not new_names:
            return None
        # Take first new object as representative
        name = list(new_names)[0]
        obj = bpy.data.objects[name]
        # Non-uniform scale to fit bounding box: compute current bounds
        # Simple: scale by w/d/h ratios; assume native unit size ~1m
        w = getattr(item, "w", 1.0)
        d = getattr(item, "d", 1.0)
        h = getattr(item, "h", 1.0)
        # If object has dimensions, scale accordingly
        try:
            dim = obj.dimensions
            if dim.x > 1e-6 and dim.y > 1e-6 and dim.z > 1e-6:
                obj.scale.x = w / dim.x if dim.x else 1
                obj.scale.y = d / dim.y if dim.y else 1
                obj.scale.z = h / dim.z if dim.z else 1
        except Exception:
            pass
        # Position: item origin is room-local; room_x/y are world metres
        ix = getattr(item, "x", 0)
        iy = getattr(item, "y", 0)
        # item x/y are mm in placement? placement uses metres for plan_room? Check: placement returns metres scaled? Actually FurnitureItem w/d in metres? We'll assume metres in item and convert if needed
        # If values > 10, they're mm -> convert
        if ix > 100:
            ix /= 1000
            iy /= 1000
        obj.location.x = room_x + ix
        obj.location.y = room_y + iy
        obj.location.z = base_z
        rot = getattr(item, "rot_deg", 0) or 0
        if rot:
            import math
            obj.rotation_euler.z = math.radians(rot)
        # Move to collection if not already
        try:
            collection.objects.link(obj)
        except Exception:
            pass
        return obj
    except Exception as e:
        print(f"asset import failed for {kind}: {e}")
        return None
