"""Place cached CC0 furniture meshes (PR TASK-03-02 / 03-04). Runs in Blender.

A kind's GLB is imported **once** per session into a template list of mesh
datablocks. Every placement then creates new objects that *link* those same
datablocks, so a dining room with twelve chairs holds one chair mesh in memory
and one in the exported GLB, not twelve.

Each placement is fitted non-uniformly to the `FurnitureItem`'s w/d/h box —
the footprint the collision-resolved placement already reserved — rotated
about the footprint centre by `rot_deg`, and named `furn_<kind>_*` so the
viewer's layer toggles can find it.
"""
from __future__ import annotations

import math
from pathlib import Path

try:
    from homedesign import asset_cache
    _HAS_CACHE = True
except Exception:  # pragma: no cover
    asset_cache = None
    _HAS_CACHE = False

# Phone-build LOD: curated CC0 meshes arrive dense (a draped mattress is
# ~2 MB of vertices). Meshes over this polygon count are collapsed once at
# import so both builds share one deterministic LOD; smooth upholstery loses
# nothing visible at room scale, and the phone GLB sheds ~1.7 MB.
LOD_POLY_THRESHOLD = 20000
LOD_DECIMATE_RATIO = 0.4

 # kind -> cached GLB to reuse when the exact kind has no mesh (offline-safe;
# at placement scale; procedural fallback remains for everything else).
KIND_ALIASES = {"coffee_table": "table", "dining_table": "table"}

# kind -> (list of mesh datablocks, local bbox min, local bbox max) or None
_templates: dict[str, tuple | None] = {}


def _apply_phone_lod(obj) -> None:
    """Collapse an over-dense imported mesh once, deterministically.

    Never fails the import: skinned/shape-keyed meshes are skipped and any
    operator error falls back to the original mesh.
    """
    import bpy

    try:
        data = obj.data
        if data is None or getattr(data, "shape_keys", None):
            return
        if len(data.polygons) < LOD_POLY_THRESHOLD:
            return
        mod = obj.modifiers.new("phone_lod", "DECIMATE")
        mod.ratio = LOD_DECIMATE_RATIO
        prev_active = bpy.context.view_layer.objects.active
        bpy.context.view_layer.objects.active = obj
        try:
            bpy.ops.object.modifier_apply(modifier=mod.name)
        finally:
            bpy.context.view_layer.objects.active = prev_active
    except Exception as exc:
        print(f"phone LOD skipped for {getattr(obj, 'name', '?')}: {exc}")

def _import_template(kind: str, path: Path):
    """Import a kind's GLB once and keep its mesh datablocks.

    The imported objects are removed from the scene afterwards; only their mesh
    data survives, which is what later placements link to.
    """
    import bpy

    before = set(bpy.data.objects.keys())
    bpy.ops.import_scene.gltf(filepath=str(path))
    new_names = [n for n in bpy.data.objects.keys() if n not in before]
    meshes: list[tuple] = []
    for name in new_names:
        obj = bpy.data.objects[name]
        if obj.type != "MESH" or obj.data is None:
            continue
        _apply_phone_lod(obj)
    lo = [float("inf")] * 3
    hi = [float("-inf")] * 3
    for name in new_names:
        obj = bpy.data.objects[name]
        if obj.type != "MESH" or obj.data is None:
            continue
        matrix = obj.matrix_world.copy()
        meshes.append((obj.data, matrix))
        for corner in obj.bound_box:
            world = matrix @ __import__("mathutils").Vector(corner)
            for axis in range(3):
                lo[axis] = min(lo[axis], world[axis])
                hi[axis] = max(hi[axis], world[axis])

    # Drop the imported objects; the mesh datablocks stay alive because the
    # template holds references to them.
    for name in new_names:
        obj = bpy.data.objects.get(name)
        if obj is not None:
            bpy.data.objects.remove(obj, do_unlink=True)

    if not meshes or lo[0] == float("inf"):
        return None
    return (meshes, tuple(lo), tuple(hi))


def _template(kind: str):
    if kind in _templates:
        return _templates[kind]
    result = None
    if _HAS_CACHE and asset_cache is not None:
        for candidate in (kind, KIND_ALIASES.get(kind, "")):
            if not candidate:
                continue
            try:
                path = asset_cache.furniture(candidate)
            except Exception:
                path = None
            if path and Path(path).exists():
                try:
                    result = _import_template(kind, Path(path))
                except Exception as exc:
                    print(f"asset import failed for {kind}: {exc}")
                    result = None
                if result is not None:
                    break
    _templates[kind] = result
    return result


def clear_cache() -> None:
    """Forget every imported template (used between builds in one process)."""
    _templates.clear()


def build_from_asset(item, room_x: float, room_y: float, base_z: float, collection):
    """Instance the cached mesh for `item.kind`, or return None to fall back.

    Returns the first instanced object so the caller can treat it like any
    other built object; every part is linked into `collection`.
    """
    import bpy
    import mathutils

    kind = getattr(item, "kind", "")
    template = _template(kind)
    if template is None:
        return None
    meshes, lo, hi = template

    src = [hi[axis] - lo[axis] for axis in range(3)]
    if min(src) <= 1e-9:
        return None

    # The item's footprint is (x, y) corner + (w, d); rot_deg turns it about
    # the footprint centre, exactly as the procedural placer does.
    w, d, h = float(item.w), float(item.d), float(item.h)
    angle = math.radians(float(getattr(item, "rot_deg", 0.0) or 0.0))
    cx = room_x + float(item.x) + w / 2
    cy = room_y + float(item.y) + d / 2

    # A 90-degree rotation swaps which source axis spans the item's width.
    if abs(math.cos(angle)) < 0.5:
        scale = (d / src[0], w / src[1], h / src[2])
    else:
        scale = (w / src[0], d / src[1], h / src[2])

    # Centre the mesh group on the footprint centre in X/Y and sit it on the
    # floor in Z, in the template's own units, before scaling.
    offset = mathutils.Vector((
        -(lo[0] + hi[0]) / 2,
        -(lo[1] + hi[1]) / 2,
        -lo[2],
    ))
    # The full transform is baked into each instance's own matrix rather than
    # applied through a parent empty. Parented transforms are only correct
    # after a depsgraph update, so anything reading `matrix_world` in the same
    # pass that built the scene — the geometry tests, the camera fit, the
    # exporter — would see the mesh sitting at the template's origin.
    place = (
        mathutils.Matrix.Translation((cx, cy, base_z))
        @ mathutils.Matrix.Rotation(angle, 4, "Z")
        @ mathutils.Matrix.Diagonal((scale[0], scale[1], scale[2], 1.0))
        @ mathutils.Matrix.Translation(offset)
    )

    first = None
    for index, (mesh, matrix) in enumerate(meshes):
        obj = bpy.data.objects.new(f"furn_{kind}_{cx:.2f}_{cy:.2f}_{index}", mesh)
        collection.objects.link(obj)
        # `matrix_world` (not `matrix_basis`) is the write that takes effect
        # without a depsgraph evaluation: on an unparented object Blender
        # applies it straight through to the object's local transform.
        obj.matrix_world = place @ matrix
        if first is None:
            first = obj
    return first
